# %% [markdown]
# ## Brief generation (`brief.json`, `brief.md`)
#
# **Choice:** the brief is *assembled from the reconciled, verified records*, never re-written by a model. Each signal shows the primary finding, every other document's finding,
# citations as `[doc_id, section, PDF page (printed page)]` with the short verbatim quote and its verification label, and any conflict side by side. Five (document, signal) pairs are drawn at random (fixed,
# recorded seed) into a **spot-check list** for a human to compare against the PDFs.
#
# **Alternative rejected:** a fluent narrative summary. It would hide which sentence came from which page and would be the one part of the pipeline nobody could verify.
# **Limit:** the brief inherits every weakness of the proxy industry described in the gaps.

# %%
SPOT_SEED = 20260919

def fmt_value(v, depth=0):
    """Compact one-line rendering of a signal value for the markdown/PDF brief."""
    if isinstance(v, dict) and "competitors" in v:
        def one(c):
            share = f"{c['share_pct']}%" if c.get("share_pct") is not None else (f"band {c['share_range']}%" if c.get("share_range") else "no share given")
            return f"{c['name']} {share}" + (f" (revenue ${c['revenue_usd_bn']}bn)" if c.get("revenue_usd_bn") is not None else "")
        bases = list(dict.fromkeys(c["share_basis"] for c in v["competitors"]))
        return "; ".join(one(c) for c in v["competitors"]) + " | share basis: " + " / ".join(bases)
    if isinstance(v, dict) and isinstance(v.get("segments"), list) and v["segments"]:
        rest = {k: x for k, x in v.items() if k != "segments"}
        return "; ".join(f"{s['segment']} {s['share_pct']}%" for s in v["segments"]) + (" | " + fmt_value(rest, 1) if fmt_value(rest, 1) else "")
    if v is None: return "none"
    if isinstance(v, (int, float, str)): return str(v)
    if isinstance(v, list):
        return "; ".join(fmt_value(x, depth + 1) for x in v) if all(not isinstance(x, (dict, list)) for x in v) else " | ".join(fmt_value(x, depth + 1) for x in v)
    if isinstance(v, dict):
        parts = []
        for k, x in v.items():
            if x is None or x == [] or k in ("why_chosen", "scope_note", "internal_conflict", "concentration_note"): continue
            parts.append(f"{k.replace('_', ' ')}: {fmt_value(x, depth + 1)}")
        return ("; " if depth == 0 else ", ").join(parts)
    return str(v)

def best_citation(x):
    """The citation that carries the most of the signal's numbers (a human can check a number fastest); else the first."""
    want = {round(n, 6) for _, n in numeric_leaves(x["value"])}
    score = lambda c: len(want & {round(n, 6) for n in numbers_in(c["quote"])})
    return max(x["citations"], key=score)

def spot_check(records, seed=SPOT_SEED, k=5):
    cands = [(sid, x) for sid, r in records.items() for x in ([r["primary"]] if r["primary"] else []) + r["other_documents"] if x["citations"]]
    picks = random.Random(seed).sample(cands, min(k, len(cands)))
    out = []
    for sid, x in picks:
        c = best_citation(x)
        out.append({"signal_id": sid, "name": SIGNAL_META[sid][0], "doc_id": x["doc_id"], "pdf_page": c["pdf_page"], "printed_page": c["printed_page"], "quote": c["quote"]})
    return out

def build_brief(company, description, docs, naics_choice, extractions, records, gaps, summ, extractor_note, scope_table, verify_mode, family):
    signals = []
    for sid, r in records.items():
        p = r["primary"]
        signals.append({"signal_id": sid, "name": r["name"], "status": p["status"] if p else "NOT_FOUND",
                        "force_tag": p["force_tag"] if p else SIGNAL_META[sid][1], "primary": p, "other_documents": r["other_documents"],
                        "not_supported_by": r["not_supported_by"], "conflicts": r["conflicts"],
                        "quotes_verified": sum(len(x["citations"]) for x in ([p] if p else []) + r["other_documents"])})
    for sg in signals:
        for x in ([sg["primary"]] if sg["primary"] else []) + sg["other_documents"]:
            x["value_text"] = fmt_value(x["value"])
    return {
        "meta": {"company": company, "description": description, "generated": datetime.datetime.now().isoformat(timespec="seconds"),
                 "extractor": extractor_note, "extraction_done_by": "Claude Code (an LLM agent) in the build session; verification, reconciliation, gaps and this brief are code.",
                 "gemini_backend_status": GEMINI_TEST_STATUS, "verification_mode": verify_mode, "primary_rule": PRIMARY_RULE,
                 "proxy_industry_warning": f"Fractional CFO has no industry code. Every figure describes a proxy industry (chosen NAICS {naics_choice['chosen_code']}) or the accounting neighbor; see gaps.",
                 "hand_checked_line": "Hand-checked by me: [ ] of [ ] citations. (left blank on purpose; to be filled in by the student)"},
        "naics": naics_choice, "report_scope": scope_table,
        "sources": [{**{k: docs[d].get(k) for k in ("doc_id", "title", "publisher", "publication_date", "stated_industry_code", "how_to_find", "n_pages", "code_note")},
                     "industry_family": family[d], "naics_2022_listed": extractions[d]["report_scope"]["naics_2022_listed"]} for d in docs],
        "verification_summary": summ, "signals": signals, "gaps": gaps,
        "spot_check": {"seed": SPOT_SEED, "how": "random.Random(seed).sample over (signal, document) findings that have verified citations", "items": spot_check(records)},
    }

def cite_str(c):
    printed = f" (printed {c['printed_page']})" if c.get("printed_page") else ""
    return f"[{c['doc_id']}, {c['section_heading'] or 'no heading detected'}, PDF p.{c['pdf_page']}{printed}]"

def render_brief_md(b):
    L = [f"# Industry brief: {b['meta']['company']}", "", f"*{b['meta']['description']}*", "",
         f"**Extraction:** {b['meta']['extraction_done_by']}", f"**Verification mode this run:** {b['meta']['verification_mode']}", "",
         f"> {b['meta']['proxy_industry_warning']}", "", "## NAICS selected", "",
         f"**{b['naics']['chosen_code']} {b['naics']['chosen_title']}** (2022 NAICS Manual: {b['naics']['manual_url']}, accessed {b['naics']['accessed']}).", "",
         b["naics"]["justification"], "", "## Verification summary", ""]
    s = b["verification_summary"]
    L += [f"Quotes checked {s['quotes_checked']}; passed {s['passed']} (exact {s['passed_exact']}, adjacent page {s['passed_adjacent_page']}, fuzzy {s['passed_fuzzy']}); failed {s['failed']}; "
          f"corrected in retry {s['corrected_in_retry']}; numbers checked {s['numbers_checked']}, unmatched {s['numbers_unmatched']}.", "", "## Signals", ""]
    for sg in b["signals"]:
        L += [f"### {sg['signal_id']} {sg['name']}", f"*force: {sg['force_tag']} | status: {sg['status']} (for the proxy industry, not the fractional niche) | quotes verified: {sg['quotes_verified']}*", ""]
        for i, x in enumerate(([sg["primary"]] if sg["primary"] else []) + sg["other_documents"]):
            L += [f"**{'Primary' if i == 0 else 'Also'}: {x['doc_id']} ({x['status']}, confidence {x['confidence']['level']})**", f"- Value: {x['value_text']}", f"- Summary: {x['summary']}"]
            L += [f"- Cite {cite_str(c)} \"{c['quote']}\" ({c['verification']})" for c in x["citations"]]
            L += [f"- Note: {x['notes']}", ""]
        for c in sg["conflicts"]:
            L += [f"**Conflict ({c['kind']}): {c['metric']}**"] + [f"- {t['doc_id']}: {t['value']} ({t['period_or_year']})" + (f" {cite_str(t['citation'])} \"{t['citation']['quote']}\"" if t["citation"] else "") for t in c["sides"]] + [f"- Why they may differ: {c['why_they_may_differ']}", ""]
    L += ["## Sources", ""] + [f"- **{x['title']}**, {x['publisher']}, {x['publication_date']}, code: {x['stated_industry_code'] or 'not stated'}. Find it: {x['how_to_find']}" for x in b["sources"]]
    L += ["", "## Gaps", ""] + [f"- **{g['why']}**" + (f" ({g['signal_id']}, {g['doc_id']})" if g["doc_id"] else "") + f": {g['what_is_missing']} *To find it:* {g['what_would_find_it']}" for g in b["gaps"]]
    L += ["", "## Spot-check list (5 random findings, seed %d)" % b["spot_check"]["seed"], ""] + \
         [f"- {x['signal_id']} {x['name']}: {x['doc_id']}, PDF p.{x['pdf_page']} (printed {x['printed_page']}): \"{x['quote']}\"" for x in b["spot_check"]["items"]]
    L += ["", b["meta"]["hand_checked_line"], ""]
    return "\n".join(L)

BRIEF = build_brief(COMPANY, DESCRIPTION, DOCS, NAICS_CHOICE, EXTRACTIONS, RECORDS, GAPS, SUMM, EXTRACTOR_NOTE, SCOPE_TABLE, VERIFY_MODE, FAMILY)
json.dump(BRIEF, open("brief.json", "w"), indent=1, ensure_ascii=False)
open("brief.md", "w").write(render_brief_md(BRIEF))
print("Wrote brief.json and brief.md")
print("Signals:", {s["signal_id"]: s["status"] for s in BRIEF["signals"]})
print("\nSpot-check list (compare these 5 against the PDFs):")
for x in BRIEF["spot_check"]["items"]:
    print(f"  {x['signal_id']} | {x['doc_id']} | PDF p.{x['pdf_page']} (printed {x['printed_page']}) | \"{x['quote'][:80]}\"")
print("\n--- brief.md, first lines ---")
print("\n".join(open("brief.md").read().split("\n")[:22]))
