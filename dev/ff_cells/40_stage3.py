# %% [markdown]
# ## Stage 3: enrichment from public sources, then verify every fact's quotes
#
# `fetch_public.py` fetched each source once with plain HTTP requests (no API key, nothing paid) and cached its text. Each source is listed
# below with its URL and access date.
#
# * **Government documents** (BLS, SEC EDGAR, SBA) are public records, and their full text is committed in `public_sources/`.
#   BLS blocks scripted requests, so its page was fetched from the Internet Archive snapshot of the same URL (26 Sep 2026). The citation
#   still names BLS and the bls.gov URL.
# * **Commercial pages** (vendor marketing, trade press) are someone else's copyrighted text. Only the paragraphs around each cited quote
#   are committed (`public_sources/<id>.txt`). The full text stays local in the git-ignored `cache/public_full/`, and its sha256 is recorded.
#
# Then every citation of every fact is verified with the **same `check_quote` used in the first project**: normalized exact match on the
# cited page, then an adjacent page, then a guarded fuzzy match that requires every word and digit of the quote to appear. A fact counts only
# if **all** of its quotes verify. Facts marked `origin: brief` must also really appear in `brief.json` under the signal and document they name.

# %%
src_index = json.load(open(os.path.join(PUBLIC_DIR, "index.json")))
print(f"{len(src_index)} public sources:")
for sid, s in src_index.items():
    print(f"  {sid:26} {s['kind']:10} accessed {s['accessed']}  committed: {s['committed_text']}\n      {s['publisher']}: {s['title']}\n      {s['url']}")

FETCH_IF_MISSING = True
missing_src = [sid for sid in src_index
               if not os.path.exists(os.path.join(PUBLIC_FULL, sid + ".txt")) and not os.path.exists(os.path.join(PUBLIC_DIR, sid + ".txt"))]
if missing_src and FETCH_IF_MISSING:
    import fetch_public; fetch_public.main()
print("\nsources with no cached text:", missing_src or "none")

def excerpt_for(full_text, quotes, pad=3):
    """Committed excerpt of a commercial page: the lines that carry each quote, plus `pad` lines either side."""
    lines = [l for l in full_text.split("\n")]
    nl = [normalize(l) for l in lines]
    keep = set()
    for q in quotes:
        w = normalize(q).split()
        anchors = [" ".join(w[:5]), " ".join(w[-5:])]
        for i, l in enumerate(nl):
            if any(a and a in l for a in anchors) or (len(w) <= 5 and normalize(q) in l):
                keep.update(range(max(0, i - pad), min(len(lines), i + pad + 1)))
        # quotes broken across short lines (hyperlinks): fall back to a sliding window
        if not any(normalize(q) in normalize("\n".join(lines[a:a + 8])) for a in sorted(keep)):
            for i in range(len(lines)):
                if normalize(q) in normalize("\n".join(lines[i:i + 8])):
                    keep.update(range(max(0, i - pad), min(len(lines), i + 8 + pad))); break
    out, prev = [], None
    for i in sorted(keep):
        if prev is not None and i != prev + 1: out.append("[...]")
        out.append(lines[i]); prev = i
    return "\n".join(out)

quotes_by_source = defaultdict(list)
for f in facts:
    for c in f["citations"]:
        if c.get("source_id"): quotes_by_source[c["source_id"]].append(c["quote"])
for sid, s in src_index.items():
    fp = os.path.join(PUBLIC_FULL, sid + ".txt")
    if s["kind"] == "commercial" and os.path.exists(fp):
        ex = excerpt_for(open(fp).read(), quotes_by_source[sid])
        header = (f"EXCERPTS ONLY (paragraphs around cited quotes) of: {s['title']}\n{s['publisher']} | {s['url']} | accessed {s['accessed']}\n"
                  f"sha256 of full fetched text: {s['sha256_full_text']}\n\n")
        open(os.path.join(PUBLIC_DIR, sid + ".txt"), "w").write(header + ex + "\n")
        print(f"wrote excerpt public_sources/{sid}.txt: {len(ex):,} of {s['chars_full_text']:,} chars")

# %%
def public_pages():
    pages, used = [], {}
    for sid in src_index:
        full, committed = os.path.join(PUBLIC_FULL, sid + ".txt"), os.path.join(PUBLIC_DIR, sid + ".txt")
        path = full if os.path.exists(full) else committed
        used[sid] = "full text (local cache)" if path == full else "committed text"
        text = open(path).read()
        parts = re.split(r"\[page (\d+)\]\n", text)
        if len(parts) > 1:                                   # PDF: one entry per page
            for i in range(1, len(parts), 2):
                pages.append({"doc_id": sid, "pdf_page": int(parts[i]), "text": parts[i + 1]})
        else:                                                # web page: the whole page is "page 1"
            pages.append({"doc_id": sid, "pdf_page": 1, "text": text})
    return pages, used

pub_pages, pub_used = public_pages()
pages = pub_pages + ([json.loads(l) for l in open(REPORT_CACHE)] if REPORTS_AVAILABLE else [])
IDX = build_page_index(pages)
replay = {} if REPORTS_AVAILABLE else {(it["fact_id"], it["quote"]): it for it in json.load(open(FF_LOG))["items"]}

brief_quotes = defaultdict(set)
for f in findings:
    for c in f["citations"]:
        brief_quotes[(f["signal_id"], f["doc_id"])].add(normalize(c["quote"]))

def verify_citation(fact, c):
    doc = c.get("doc_id") or c.get("source_id")
    page = c.get("pdf_page") or 1
    if c.get("doc_id") and not REPORTS_AVAILABLE:
        old = replay.get((fact["fact_id"], c["quote"]))
        if old is None:
            return {"result": "FAILED", "method": None, "reason": "no live cache and no logged result", "mode": "replay"}
        return {**{k: old[k] for k in ("result", "method", "score", "matched_page", "reason")}, "mode": "replay"}
    r = check_quote(IDX, doc, page, c["quote"])
    r["mode"] = "live"
    return r

ver_items = []
for f in facts:
    ok_all = True
    for c in f["citations"]:
        r = verify_citation(f, c)
        c["verification"] = r["result"]
        ok_all &= r["result"] in ("verified", "verified_adjacent_page")
        ver_items.append({"fact_id": f["fact_id"], "force": f["force"], "origin": f["origin"]["type"],
                          "doc": c.get("doc_id") or c.get("source_id"), "pdf_page": c.get("pdf_page"), "quote": c["quote"],
                          "words": len(c["quote"].split()), **{k: r.get(k) for k in ("result", "method", "score", "matched_page", "reason", "mode")}})
    if f["origin"]["type"] == "brief":
        key = (f["origin"]["signal_id"], f["origin"]["doc_id"])
        in_brief = all(normalize(c["quote"]) in brief_quotes[key] for c in f["citations"])
        f["in_brief"] = in_brief
        ok_all &= in_brief
        if not in_brief: print(f"  {f['fact_id']}: quote not found in brief.json under {key}")
    f["verified"] = ok_all

dropped = [f["fact_id"] for f in facts if not f["verified"]]
FACTS = [f for f in facts if f["verified"]]
print(f"{len(ver_items)} citations checked across {len(facts)} facts: "
      f"{sum(1 for i in ver_items if i['result'] != 'FAILED')} verified, {sum(1 for i in ver_items if i['result'] == 'FAILED')} failed")
print("public text used for verification:", pub_used)
print("facts DROPPED (unverified quote or not really in brief.json):", dropped or "none")
for it in ver_items:
    if it["result"] == "FAILED":
        print(f"  FAILED {it['fact_id']} {it['doc']} p.{it['pdf_page']}: {it['reason']}\n     {it['quote'][:100]}")

# %%
print("Evidence after enrichment (verified facts only):\n")
LOW_EVIDENCE = []
for k, name in FORCES.items():
    fs = [f for f in FACTS if f["force"] == k]
    hit = coverage(fs, k)
    orig = Counter(f["origin"]["type"] for f in fs)
    ok = len(fs) >= MIN_FACTS and len(hit) >= MIN_SUBDIMS
    if not ok: LOW_EVIDENCE.append(k)
    print(f"{name}: {len(fs)} facts ({dict(orig)}), {len(hit)}/{len(CHECKLIST[k])} sub-dimensions -> {'OK' if ok else 'BELOW MINIMUM: confidence must be lowered'}")
    for item, _ in CHECKLIST[k]:
        ids_ = [f["fact_id"] for f in fs if f["checklist_item"] == item]
        print(f"    [{'x' if ids_ else ' '}] {item:46} {' '.join(ids_)}")
print("\nForces below the 3-fact / 2-sub-dimension minimum:", LOW_EVIDENCE or "none")
