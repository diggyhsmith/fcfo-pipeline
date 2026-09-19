# %% [markdown]
# ## Stage 1: NAICS selection from the official 2022 NAICS Manual
#
# **Problem:** fractional CFO is not its own NAICS industry, so every number in every report describes a *proxy* industry.
# The choice of proxy should come from the classification system's own definitions, not from what sounds right.
#
# **Choice:** fetch the official *2022 NAICS Manual* PDF from census.gov, parse the entry for each candidate code (title,
# description, illustrative examples, cross-references), save the text with URL and access date to `naics/`, and pick one code
# by comparing the manual's own language. The justification sentence below quotes the manual, and the code **asserts that each quoted phrase
# appears in the fetched entry**; a mis-quote fails the notebook.
#
# **Alternatives rejected:** (1) the census.gov/naics search page (returns 403 to scripted requests, so it cannot be a reproducible
# source), (2) choosing the code from the report titles (that would let the available data pick the industry), (3) inventing definitions from memory.
# If the fetch fails, the code stops and prints what to paste instead of fabricating text.

# %%
import requests
from pypdf import PdfReader

NAICS_DIR = "naics"
_FURNITURE = re.compile(r"^(PROFESSIONAL, SCIENTIFIC, AND TECHNICAL SERVICES \d+|\d+ NORTH AMERICAN INDUSTRY CLASSIFICATION SYSTEM|"
                        r"T.Canadian, Mexican, and United States industries are comparable\.|census\.gov/naics|\d{3})\s*$")

def fetch_naics_manual(cache_dir=CACHE_DIR):
    path = os.path.join(cache_dir, "2022_NAICS_Manual.pdf")
    if not os.path.exists(path) or os.path.getsize(path) < 1_000_000:
        os.makedirs(cache_dir, exist_ok=True)
        r = requests.get(NAICS_MANUAL_URL, headers={"User-Agent": "Mozilla/5.0 (class project; academic use)"}, timeout=120)
        if r.status_code != 200 or not r.content.startswith(b"%PDF"):
            raise RuntimeError(f"Could not fetch the NAICS manual ({r.status_code}). Open {NAICS_LANDING}, search each candidate code, "
                               f"and paste the title, description and cross-references into naics/manual_paste.txt instead of relying on memory.")
        Path(path).write_bytes(r.content)
    accessed = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
    return path, accessed

def manual_entries(path, codes, page_range=(430, 520)):
    """Return {code: entry_text} by locating the 6-digit heading and reading to the next code heading."""
    reader = PdfReader(path)
    def scan(lo, hi):
        lines = []
        for i in range(lo - 1, min(hi, len(reader.pages))):
            for l in (reader.pages[i].extract_text() or "").split("\n"):
                l = l.rstrip()
                if l.strip() and not _FURNITURE.match(l.strip()): lines.append((i + 1, l))
        return lines
    for rng in (page_range, (1, len(reader.pages))):          # narrow scan first, whole manual as fallback
        lines = scan(*rng)
        out, head = {}, re.compile(r"^(\d{2,6})\s+([A-Z][^\n]*?)T?\s*$")
        idx = [(n, i, head.match(l)) for i, (n, l) in enumerate(lines)]
        idx = [(n, i, m) for n, i, m in idx if m]
        for c in codes:
            for k, (n, i, m) in enumerate(idx):
                if m.group(1) == c:
                    end = idx[k + 1][1] if k + 1 < len(idx) else len(lines)
                    body = "\n".join(l for _, l in lines[i + 1:end])
                    out[c] = {"code": c, "title": m.group(2).strip(), "pdf_page": n, "text": re.sub(r"[ \t]+", " ", body).strip()}
                    break
        if len(out) == len(codes): return out
    return out

def stage1_fetch(codes=NAICS_CANDIDATES):
    path, accessed = fetch_naics_manual()
    entries = manual_entries(path, codes)
    missing = [c for c in codes if c not in entries]
    if missing:
        raise RuntimeError(f"Codes not found in manual text: {missing}. Paste their definitions from {NAICS_LANDING} into naics/manual_paste.txt.")
    os.makedirs(NAICS_DIR, exist_ok=True)
    record = {"source": "2022 NAICS Manual (U.S. Census Bureau / Executive Office of the President, OMB)", "url": NAICS_MANUAL_URL,
              "landing_page": NAICS_LANDING, "accessed": accessed, "entries": entries}
    json.dump(record, open(os.path.join(NAICS_DIR, "naics_2022_candidates.json"), "w"), indent=2)
    with open(os.path.join(NAICS_DIR, "naics_2022_candidates.md"), "w") as fh:
        fh.write(f"# NAICS 2022 candidate definitions\n\nSource: {NAICS_MANUAL_URL}\nAccessed: {accessed}\n\n")
        for c in codes:
            e = entries[c]; fh.write(f"## {c} {e['title']} (manual PDF page {e['pdf_page']})\n\n{e['text']}\n\n")
    return record

NAICS = stage1_fetch()
print(f"Fetched {len(NAICS['entries'])} candidate entries from the 2022 NAICS Manual (accessed {NAICS['accessed']}):")
for c, e in NAICS["entries"].items():
    n_cross = len(re.findall(r"^[•]", e["text"], re.M))
    print(f"  {c}  {e['title']:<62} manual PDF p.{e['pdf_page']}  ({len(e['text'])} chars, {n_cross} cross-reference bullets)")

# %% [markdown]
# **Choice made:** **541611 Administrative Management and General Management Consulting Services.**
#
# **Closest neighbor rejected:** 541219 *Other Accounting Services* (541211 *Offices of Certified Public Accountants* is the other close
# neighbor: it requires accountants "certified to audit the accounting records", i.e. attest work, which a fractional CFO does not sell).
#
# **Honest limit:** this is a *classification argument*, not a market-data argument. Only one of the three downloaded reports covers
# management consulting; the two accounting reports describe the neighbor we rejected. The mismatch table below shows this.

# %%
_norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()

def stage1_choose(naics, chosen=None, neighbor=None, quotes=None, justification=None):
    """Validate the configured choice against the fetched manual text and return the record used by the brief."""
    chosen, neighbor = chosen or CHOSEN_CODE, neighbor or NEIGHBOR_CODE
    quotes, justification = quotes or JUSTIFICATION_QUOTES, justification or NAICS_JUSTIFICATION
    assert chosen in naics["entries"] and neighbor in naics["entries"], "chosen/neighbor code must be among the fetched candidates"
    for code, qs in quotes.items():
        for q in qs:
            assert _norm(q) in _norm(naics["entries"][code]["text"]), f"Justification quote not found in {code}: {q!r}"
    return {"chosen_code": chosen, "chosen_title": naics["entries"][chosen]["title"], "neighbor_code": neighbor,
            "neighbor_title": naics["entries"][neighbor]["title"], "justification": justification, "manual_url": naics["url"],
            "landing_page": naics["landing_page"], "accessed": naics["accessed"],
            "candidates": [{"code": c, "title": e["title"], "manual_pdf_page": e["pdf_page"]} for c, e in naics["entries"].items()],
            "quotes_verified": sum(len(v) for v in quotes.values())}

NAICS_CHOICE = stage1_choose(NAICS)
print("Chosen NAICS:", NAICS_CHOICE["chosen_code"], "-", NAICS_CHOICE["chosen_title"])
print("\nWhy this and not", NAICS_CHOICE["neighbor_code"] + ":\n" + textwrap.fill(NAICS_CHOICE["justification"], 118))
print("\nAll", NAICS_CHOICE["quotes_verified"], "quoted phrases verified against the fetched manual text.")
print("\nManual's own cross-reference on the neighbor (541219):")
print(textwrap.indent(textwrap.fill(NAICS["entries"]["541219"]["text"].split("Cross-References.")[-1].replace("\n", " ")[:420], 110), "   "))

# %% [markdown]
# **Which code does each downloaded report cover?** Read from the extraction files (the agent recorded each report's own stated code and scope, and code verifies those quotes in Stage 3).
# The result is a mismatch table, not a footnote: only one of three reports sits on our chosen code.

# %%
def report_scope_table(extractions, docs, chosen):
    rows = []
    for d, e in extractions.items():
        sc = e["report_scope"]
        rows.append({"doc_id": d, "title": docs[d]["title"], "stated_code": sc["stated_industry_code"], "naics_2022_listed": sc["naics_2022_listed"],
                     "covers_chosen_code": chosen in sc["naics_2022_listed"], "relation": sc["relation_to_chosen_naics"]})
    return rows

# (printed after Stage 2 has loaded the extractions; see the cell after Stage 2)
