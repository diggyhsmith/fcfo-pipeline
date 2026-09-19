#!/usr/bin/env python3
"""Stage 3 - verification, in code, of every quote the LLM agent wrote.

What this proves:   each evidence quote appears (after normalisation) on the page it cites, or on an adjacent page.
What it cannot prove: that the quote means what the extraction says it means. That still needs a human.

Rules implemented (see the notebook's Stage 3 cell for the reasoning):
  * normalise whitespace, case, hyphens (joined), smart quotes, dashes;
  * exact containment on the cited page (checked against BOTH text variants cached at ingest);
  * else exact containment on page-1 / page+1  -> "verified_adjacent_page";
  * else fuzzy match (rapidfuzz partial_ratio >= 90) on the cited page, accepted ONLY if every digit run AND every
    word of the quote also appears in the matched window. So '$157.4' can never fuzzy-match '$158.4', and 'grew' can
    never fuzzy-match 'shrank': fuzzy matching is there for extraction glitches, not for paraphrase.
  * quotes over 25 words, empty quotes and unknown pages FAIL;
  * every number in a signal's value must appear in that signal's verified quotes.

CLI:  python verify.py            run one verification round and append it to verification_log.json (max 2 rounds)
      python verify.py --reset    start the log over (round 1)
"""
import json, re, glob, os, sys, unicodedata, datetime, hashlib
from rapidfuzz import fuzz

FUZZY_MIN = 90
MAX_WORDS = 25
MAX_ROUNDS = 2
STATUSES = {"FOUND", "PARTIAL", "NOT_FOUND"}

# --------------------------------------------------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------------------------------------------------
_SMART = {"‘": "'", "’": "'", "‚": "'", "‛": "'", "“": '"', "”": '"', "„": '"',
          "–": "-", "—": "-", "−": "-", " ": " ", "‑": "-"}

def normalize(s):
    """Lower-case; smart quotes/dashes to ASCII; hyphens joined (so 'well-\\nqualified' == 'well-qualified'); whitespace collapsed."""
    s = unicodedata.normalize("NFKC", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Co")   # private-use icon glyphs that IBISWorld PDFs embed in tables
    for a, b in _SMART.items():
        s = s.replace(a, b)
    s = re.sub(r"-\s*", "", s)          # drop hyphens and any line-break whitespace after them
    return re.sub(r"\s+", " ", s).strip().lower()

def numbers_in(text):
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text or "")
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]

# --------------------------------------------------------------------------------------------------------------------
# page index
# --------------------------------------------------------------------------------------------------------------------
def build_page_index(pages):
    """pages: list of dicts with doc_id, pdf_page, printed_page, text, text_raw -> {(doc, page): {'variants': [...], 'printed': x}}"""
    idx = {}
    for p in pages:
        variants = [normalize(p.get("text", "")), normalize(p.get("text_raw", ""))]
        idx[(p["doc_id"], p["pdf_page"])] = {"variants": [v for v in variants if v], "printed": p.get("printed_page")}
    return idx

def _same_tokens(nq, window):
    """Guard for fuzzy matches: digit runs must agree exactly, and every word of the quote must occur in the window."""
    if sorted(re.findall(r"\d+", nq)) != sorted(re.findall(r"\d+", window)):
        return False
    have = set(re.findall(r"[a-z0-9$%.]+", window))
    return all(t in have for t in re.findall(r"[a-z0-9$%.]+", nq))

def _contains(variants, nq):
    return any(nq in v for v in variants)

def _fuzzy(variants, nq):
    best_score, best_window = 0.0, ""
    for v in variants:
        al = fuzz.partial_ratio_alignment(nq, v)
        if al is not None and al.score > best_score:
            best_score, best_window = al.score, v[al.dest_start:al.dest_end]
    return best_score, best_window

def check_quote(idx, doc_id, page, quote):
    """Return dict(result, method, score, matched_page, printed_page, reason)."""
    out = {"result": "FAILED", "method": None, "score": None, "matched_page": None, "printed_page": None, "reason": None}
    here = idx.get((doc_id, page))
    if here is None:
        out["reason"] = "cited page does not exist in the cache"; return out
    out["printed_page"] = here["printed"]
    words = len((quote or "").split())
    if not (quote or "").strip():
        out["reason"] = "empty quote"; return out
    if words > MAX_WORDS:
        out["reason"] = f"quote has {words} words (limit {MAX_WORDS})"; return out
    nq = normalize(quote)
    if _contains(here["variants"], nq):
        out.update(result="verified", method="exact", score=100.0, matched_page=page); return out
    for adj in (page - 1, page + 1):
        other = idx.get((doc_id, adj))
        if other and _contains(other["variants"], nq):
            out.update(result="verified_adjacent_page", method="exact", score=100.0, matched_page=adj,
                       reason=f"quote is on PDF p.{adj}, not the cited p.{page}"); return out
    score, window = _fuzzy(here["variants"], nq)
    out["score"] = round(score, 1)
    if score >= FUZZY_MIN and _same_tokens(nq, window):
        out.update(result="verified", method="fuzzy", matched_page=page); return out
    for adj in (page - 1, page + 1):
        other = idx.get((doc_id, adj))
        if other:
            s2, w2 = _fuzzy(other["variants"], nq)
            if s2 >= FUZZY_MIN and _same_tokens(nq, w2):
                out.update(result="verified_adjacent_page", method="fuzzy", score=round(s2, 1), matched_page=adj,
                           reason=f"fuzzy match on PDF p.{adj}"); return out
    out["reason"] = f"not found on p.{page} or adjacent pages (best fuzzy score {out['score']})"
    return out

# --------------------------------------------------------------------------------------------------------------------
# structure + number checks
# --------------------------------------------------------------------------------------------------------------------
def schema_errors(ext, schema_path="extraction_schema.json"):
    errs = []
    try:
        import jsonschema
        schema = json.load(open(schema_path))
        v = jsonschema.Draft7Validator(schema)
        errs += [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message[:140]}" for e in v.iter_errors(ext)]
    except ImportError:
        for k in ("doc_id", "extracted_by", "report_scope", "signals"):
            if k not in ext: errs.append(f"missing key {k}")
    ids = [s.get("signal_id") for s in ext.get("signals", [])]
    if sorted(ids) != [f"S{i}" for i in range(1, 8)]:
        errs.append(f"signals must be exactly S1..S7, got {ids}")
    for s in ext.get("signals", []):
        for e in s.get("evidence", []):
            if e.get("doc_id") != ext.get("doc_id"):
                errs.append(f"{s.get('signal_id')}: evidence doc_id {e.get('doc_id')} differs from file doc_id")
    return errs

def numeric_leaves(value, path=""):
    """Numbers to be matched against quotes: numeric leaves, plus every number inside strings under keys ending '_range'."""
    found = []
    if isinstance(value, bool) or value is None:
        return found
    if isinstance(value, (int, float)):
        return [(path, float(value))]
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, str) and k.endswith("_range"):
                found += [(f"{path}/{k}", n) for n in numbers_in(v)]
            else:
                found += numeric_leaves(v, f"{path}/{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found += numeric_leaves(v, f"{path}[{i}]")
    return found

def check_numbers(signal, verified_quotes):
    """Every numeric leaf of the value must appear in the union of the signal's VERIFIED quotes."""
    have = set()
    for q in verified_quotes:
        have.update(round(n, 6) for n in numbers_in(q))
    rows = []
    for path, n in numeric_leaves(signal.get("value")):
        rows.append({"path": path, "number": n, "in_quote": round(n, 6) in have})
    return rows

# --------------------------------------------------------------------------------------------------------------------
# verification driver
# --------------------------------------------------------------------------------------------------------------------
def load_extractions(extract_dir="extractions"):
    out = {}
    for f in sorted(glob.glob(os.path.join(extract_dir, "*.json"))):
        ext = json.load(open(f))
        out[ext.get("doc_id", os.path.basename(f)[:-5])] = ext
    return out

def verify_all(extractions, idx):
    """Check every evidence quote (signals + report_scope). Returns (items, number_rows, structure_errors)."""
    items, number_rows, struct = [], [], {}
    for doc_id, ext in extractions.items():
        struct[doc_id] = schema_errors(ext)
        groups = [("SCOPE", ext["report_scope"].get("evidence", []))] + [(s["signal_id"], s.get("evidence", [])) for s in ext["signals"]]
        for sid, evs in groups:
            for i, ev in enumerate(evs):
                r = check_quote(idx, ev.get("doc_id", doc_id), ev.get("pdf_page", -1), ev.get("quote", ""))
                items.append({"doc_id": doc_id, "signal_id": sid, "evidence_index": i, "pdf_page": ev.get("pdf_page"),
                              "section_heading": ev.get("section_heading"), "quote": ev.get("quote"), **r})
        for s in ext["signals"]:
            if s["status"] == "NOT_FOUND":
                continue
            good = [it["quote"] for it in items if it["doc_id"] == doc_id and it["signal_id"] == s["signal_id"]
                    and it["result"] in ("verified", "verified_adjacent_page")]
            for row in check_numbers(s, good):
                number_rows.append({"doc_id": doc_id, "signal_id": s["signal_id"], **row})
    return items, number_rows, struct

def summarize(items, number_rows, struct):
    n = len(items)
    passed = sum(1 for it in items if it["result"] in ("verified", "verified_adjacent_page"))
    return {"quotes_checked": n, "passed": passed, "failed": n - passed,
            "passed_exact": sum(1 for it in items if it["result"] == "verified" and it["method"] == "exact"),
            "passed_fuzzy": sum(1 for it in items if it["method"] == "fuzzy" and it["result"] != "FAILED"),
            "passed_adjacent_page": sum(1 for it in items if it["result"] == "verified_adjacent_page"),
            "numbers_checked": len(number_rows), "numbers_unmatched": sum(1 for r in number_rows if not r["in_quote"]),
            "structure_errors": sum(len(v) for v in struct.values())}

def apply_verification(extractions, items, number_rows):
    """Return per-signal verified view. Failed evidence is dropped from support; a FOUND/PARTIAL signal left with no verified
    evidence becomes UNVERIFIED (and is reported as a gap). Unmatched numbers are flagged, not silently kept."""
    view = {}
    for doc_id, ext in extractions.items():
        sigs = {}
        for s in ext["signals"]:
            mine = [it for it in items if it["doc_id"] == doc_id and it["signal_id"] == s["signal_id"]]
            keep = [it for it in mine if it["result"] in ("verified", "verified_adjacent_page")]
            dropped = [it for it in mine if it["result"] == "FAILED"]
            bad_nums = [r for r in number_rows if r["doc_id"] == doc_id and r["signal_id"] == s["signal_id"] and not r["in_quote"]]
            status = s["status"]
            if status in ("FOUND", "PARTIAL") and not keep:
                status = "UNVERIFIED"
            sigs[s["signal_id"]] = {"status_final": status, "status_claimed": s["status"], "verified_evidence": keep,
                                    "dropped_evidence": dropped, "numbers_unmatched": bad_nums}
        view[doc_id] = sigs
    return view

def load_log(path="verification_log.json"):
    return json.load(open(path)) if os.path.exists(path) else None

def write_log(path, items, number_rows, struct, rounds, generated=None):
    log = {"generated": generated or datetime.datetime.now().isoformat(timespec="seconds"),
           "note": "Quotes are <=25 words each. No full page text is stored here. 'verified' means the quote exists on the cited page; it does not mean the interpretation is right.",
           "rounds": rounds, "summary": summarize(items, number_rows, struct), "structure_errors": struct,
           "items": items, "number_checks": number_rows}
    json.dump(log, open(path, "w"), indent=1, ensure_ascii=False)
    return log

def corrected_in_retry(rounds_items):
    """Evidence that FAILED in an earlier round and passes in the last one, matched by (doc, signal, evidence_index)."""
    if len(rounds_items) < 2: return 0
    key = lambda it: (it["doc_id"], it["signal_id"], it["evidence_index"])
    ok = lambda it: it["result"] in ("verified", "verified_adjacent_page")
    first_failed = {key(it) for it in rounds_items[0] if not ok(it)}
    last_ok = {key(it) for it in rounds_items[-1] if ok(it)}
    return len(first_failed & last_ok)

# --- CLI ---
def _pages_from_cache(cache="cache/pages.jsonl"):
    with open(cache) as fh:
        return [json.loads(l) for l in fh]

def main():
    reset = "--reset" in sys.argv
    if not os.path.exists("cache/pages.jsonl"):
        sys.exit("cache/pages.jsonl not found: run Stage 0 (the notebook) with the PDFs in ./reports first.")
    prev = None if reset else load_log()
    rounds = (prev or {}).get("rounds", [])
    if len(rounds) >= MAX_ROUNDS:
        sys.exit(f"Already ran {MAX_ROUNDS} rounds. Use --reset to start over; the brief allows at most {MAX_ROUNDS} fix-and-retry rounds.")
    idx = build_page_index(_pages_from_cache())
    items, number_rows, struct = verify_all(load_extractions(), idx)
    summ = summarize(items, number_rows, struct)
    rounds.append({"round": len(rounds) + 1, "date": datetime.datetime.now().isoformat(timespec="seconds"),
                   "quotes_checked": summ["quotes_checked"], "passed": summ["passed"], "failed": summ["failed"],
                   "numbers_unmatched": summ["numbers_unmatched"], "structure_errors": summ["structure_errors"],
                   "failed_keys": [[it["doc_id"], it["signal_id"], it["evidence_index"]] for it in items if it["result"] == "FAILED"]})
    write_log("verification_log.json", items, number_rows, struct, rounds)
    print(f"Round {rounds[-1]['round']}: {summ['quotes_checked']} quotes checked | passed {summ['passed']} "
          f"(exact {summ['passed_exact']}, adjacent page {summ['passed_adjacent_page']}, fuzzy {summ['passed_fuzzy']}) | failed {summ['failed']}")
    print(f"Numbers in signal values: {summ['numbers_checked']} checked, {summ['numbers_unmatched']} not found in their quotes | schema/structure errors: {summ['structure_errors']}")
    for it in items:
        if it["result"] == "FAILED":
            print(f"  FAILED {it['doc_id']} {it['signal_id']}[{it['evidence_index']}] p.{it['pdf_page']}: {it['reason']}\n         quote: {it['quote'][:110]}")
    for r in number_rows:
        if not r["in_quote"]:
            print(f"  NUMBER NOT IN QUOTE {r['doc_id']} {r['signal_id']} {r['path']} = {r['number']}")
    for d, errs in struct.items():
        for e in errs:
            print(f"  STRUCTURE {d}: {e}")

if __name__ == "__main__":
    main()
