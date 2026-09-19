# %% [markdown]
# ## Stage 0: Ingest (PDF to page-level text cache)
#
# **Choice:** extract text *per PDF page* with `pdfplumber`, and cache `doc_id`, `pdf_page`, printed page label and text in
# `cache/pages.jsonl`. Two text variants are cached per page: `text` (column-aware: two-column IBISWorld pages are
# re-ordered so a sentence is contiguous) and `text_raw` (pdfplumber's default reading order).
#
# **Alternative rejected:** `pypdf` alone, or one text blob per document. `pypdf` merges columns and drops spacing more often;
# one blob loses the page number, and a citation without a page is not findable. Whole-document OCR was also rejected
# (nothing here is scanned; the code flags near-empty pages and would try OCR if `pytesseract` were installed).
#
# **Why two variants:** IBISWorld reports are two-column. Default extraction interleaves the columns line by line, which breaks
# verbatim quotes that wrap across lines. The verifier accepts a quote if it appears in *either* variant of the cited page.
# **Limit:** tables and charts extract poorly in both variants; numbers taken from them are checked against the page text only.

# %%
import pdfplumber

PRINTED_LABEL_PATTERNS = [
    re.compile(r"^(\d{1,3})\s+www\.ibisworld\.com\b"),   # IBISWorld footer: "17 www.ibisworld.com May 2026"
    re.compile(r"(\d{1,3})/\d{1,3}\s*$"),                # browser-printout footer: "10/26"
]

def _cluster_lines(words, tol=3):
    lines, cur, cur_top = [], [], None
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if cur_top is None or abs(w["top"] - cur_top) <= tol:
            cur.append(w); cur_top = w["top"] if cur_top is None else cur_top
        else:
            lines.append(cur); cur, cur_top = [w], w["top"]
    if cur: lines.append(cur)
    return [sorted(l, key=lambda w: w["x0"]) for l in lines]

def column_aware_text(page, band=0.05):
    """Re-order a page so two-column blocks read left column then right column. Header/footer bands are dropped."""
    H, mid = float(page.height), float(page.width) / 2
    words = [w for w in page.extract_words() if H * band <= w["top"] <= H * (1 - band)]
    out, L, R = [], [], []
    def flush():
        out.extend(L); out.extend(R); L.clear(); R.clear()
    for line in _cluster_lines(words):
        crossing = any(w["x0"] < mid - 2 and w["x1"] > mid + 2 for w in line)
        left  = [w for w in line if (w["x0"] + w["x1"]) / 2 <  mid]
        right = [w for w in line if (w["x0"] + w["x1"]) / 2 >= mid]
        if crossing or (left and right and right[0]["x0"] - left[-1]["x1"] < 8):
            flush(); out.append(" ".join(w["text"] for w in line))          # full-width line
        else:
            if left:  L.append(" ".join(w["text"] for w in left))
            if right: R.append(" ".join(w["text"] for w in right))
    flush()
    return "\n".join(out)

def printed_label(raw_text):
    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
    for l in lines[-3:][::-1]:
        for pat in PRINTED_LABEL_PATTERNS:
            m = pat.search(l)
            if m: return m.group(1)
    return None

def detect_doc_meta(pages, filename):
    """Title, publisher, publication date and stated industry code, from the front pages (and, for First Research, the code page)."""
    front = "\n".join(p["text_raw"] for p in pages[:2])
    whole = "\n".join(p["text_raw"] for p in pages)
    meta = {"filename": filename, "n_pages": len(pages)}
    if "ibisworld" in front.lower():
        meta["publisher"] = "IBISWorld"
        m = re.search(r"Services\s*•\s*([0-9]{5}[a-z]?)", front)
        meta["stated_industry_code"] = m.group(1) if m else None
        lines = [l.strip() for l in pages[0]["text_raw"].split("\n") if l.strip()]
        meta["title"] = " ".join(lines[1:3]).replace("the US Accounts", "the US") if len(lines) > 2 else filename
        m = re.search(r"Published:\s*([A-Za-z]+ \d{4})", front)
        meta["publication_date"] = m.group(1) if m else None
        meta["sector_header"] = lines[0]
        meta["how_to_find"] = "BYU Library > Business databases > IBISWorld > search the report title (US industry reports)."
    elif "first research" in front.lower() or "hoovers.dnb.com" in whole.lower():
        meta["publisher"] = "First Research (Dun & Bradstreet), accessed via D&B Hoovers"
        t = pages[0]["text_raw"]
        m = re.search(r"Powered by\s*\n?\s*([A-Z][A-Za-z &,\-]+)", t)
        meta["title"] = "First Research Industry Profile: " + (m.group(1).strip() if m else "Accounting Services")
        m = re.search(r"Published:\s*([A-Za-z]+ \d{4})", front)
        meta["publication_date"] = m.group(1) if m else None
        code_page = next((p for p in pages if "Associated Industry Codes" in p["text_raw"]), None)
        m = re.search(r"NAICS[^\n]{0,20}?(\d{5,6})", code_page["text_raw"]) if code_page else None
        meta["stated_industry_code"] = m.group(1) if m else None
        meta["code_note"] = ("The 'Associated Industry Codes' section (PDF p.%s) is empty in the printout; no NAICS/SIC code is stated. "
                             "Scope is inferred from the title only." % (code_page["pdf_page"] if code_page else "?")) if not m else None
        meta["how_to_find"] = "BYU Library > Business databases > D&B Hoovers > Industries > First Research > 'Accounting Services' (Industry Overview)."
    else:
        meta.update(publisher="unknown", title=filename, publication_date=None, stated_industry_code=None, how_to_find="unknown")
    return meta

def slug_doc_id(meta):
    pub = "firstresearch" if "first research" in meta["publisher"].lower() else re.sub(r"[^a-z]", "", meta["publisher"].lower().split()[0])
    code = (meta.get("stated_industry_code") or "").lower()
    if not code:   # no code stated: fall back to the title after the colon
        code = re.sub(r"[^a-z0-9]+", "-", meta["title"].split(":")[-1].lower()).strip("-")
    return f"{pub}_{code}"

def stage0_ingest(reports_dir=REPORTS_DIR, cache_dir=CACHE_DIR):
    """Extract per-page text for every PDF. Writes cache/pages.jsonl and returns (pages, docs). Flags near-empty pages."""
    os.makedirs(cache_dir, exist_ok=True)
    pages, docs, flags = [], {}, []
    for f in sorted(glob.glob(os.path.join(reports_dir, "*.pdf"))):
        with pdfplumber.open(f) as pdf:
            doc_pages = []
            for i, pg in enumerate(pdf.pages, start=1):
                raw = pg.extract_text() or ""
                doc_pages.append({"pdf_page": i, "printed_page": printed_label(raw), "text": column_aware_text(pg), "text_raw": raw})
        meta = detect_doc_meta(doc_pages, os.path.basename(f))
        doc_id = slug_doc_id(meta)
        meta["doc_id"] = doc_id
        meta["sha256"] = hashlib.sha256(Path(f).read_bytes()).hexdigest()[:16]
        near_empty = [p["pdf_page"] for p in doc_pages if len(p["text_raw"].strip()) < 50]
        meta["near_empty_pages"] = near_empty
        if near_empty:
            flags.append((doc_id, near_empty))
            try:
                import pytesseract  # noqa: F401
                meta["ocr"] = "pytesseract available but OCR path not exercised in this run"
            except ImportError:
                meta["ocr"] = "no OCR engine installed; these pages have no text"
        for p in doc_pages: p["doc_id"] = doc_id
        docs[doc_id] = meta
        pages.extend(doc_pages)
    with open(os.path.join(cache_dir, "pages.jsonl"), "w") as fh:
        for p in pages:
            fh.write(json.dumps({k: p[k] for k in ("doc_id", "pdf_page", "printed_page", "text", "text_raw")}) + "\n")
    # Metadata only (no report text) is safe to commit and feeds the source list.
    with open("sources.json", "w") as fh:
        json.dump(docs, fh, indent=2)
    return pages, docs, flags

def load_pages_cache(cache_dir=CACHE_DIR):
    with open(os.path.join(cache_dir, "pages.jsonl")) as fh:
        return [json.loads(l) for l in fh]

# %%
if glob.glob(f"{REPORTS_DIR}/*.pdf"):
    PAGES, DOCS, FLAGS = stage0_ingest()
    print(f"Ingested {len(DOCS)} PDFs, {len(PAGES)} pages -> {CACHE_DIR}/pages.jsonl (gitignored)")
    for d, m in DOCS.items():
        print(f"\n[{d}] {m['title']}\n   publisher: {m['publisher']}\n   published: {m['publication_date']} | stated industry code: {m['stated_industry_code']} | pages: {m['n_pages']}"
              f" | printed-page labels found on {sum(1 for p in PAGES if p['doc_id']==d and p['printed_page'])} pages")
        if m.get("code_note"): print("   NOTE:", m["code_note"])
    print("\nNear-empty (possibly scanned) pages:", FLAGS or "none")
else:
    PAGES, DOCS, FLAGS = [], json.load(open("sources.json")) if os.path.exists("sources.json") else {}, []
    print("No PDFs in", REPORTS_DIR, "- Stage 0 skipped; using committed sources.json (metadata only).")
