# %% [markdown]
# ## Stage 8: write `five_forces.json` and `five_forces.md`
#
# Every citation carries its document title, publisher and date, the section, the PDF page (with the printed page where there is one) or URL,
# the quote, and its verification result. `build_five_forces_pdf.py` reads `five_forces.json` and `reflection_five_forces.md` to build the
# submission PDF.

# %%
REPORT_META = {s["doc_id"]: s for s in brief["sources"]}

def cite_out(c):
    if c.get("doc_id"):
        m = REPORT_META[c["doc_id"]]
        return {"source": f"{m['publisher']}, \"{m['title']}\" ({m['publication_date']})", "doc_id": c["doc_id"], "type": "paywalled report",
                "section": c["section"], "pdf_page": c["pdf_page"], "printed_page": c.get("printed_page"), "url": None,
                "quote": c["quote"], "verification": c["verification"]}
    m = src_index[c["source_id"]]
    return {"source": f"{m['publisher']}, \"{m['title']}\"", "doc_id": c["source_id"], "type": f"public ({m['kind']})",
            "section": c["section"], "pdf_page": c.get("pdf_page"), "printed_page": None, "url": m["url"], "accessed": m["accessed"],
            "quote": c["quote"], "verification": c["verification"]}

METHOD = {
    "scale": "1-5, whole numbers only. 5 = the force is strong and squeezes industry profits hard; 1 = the force is weak (written-assignment convention).",
    "polarity_conflict": ("The course reference spreadsheet (self-storage example) scores each force for attractiveness to incumbents: "
        "5 = most attractive (weak force), 1 = least attractive (strong force). The written assignment says the opposite: 5 = the force is "
        "strong and squeezes profits, 1 = weak. This tool follows the written assignment. A 4 here is a strong, profit-squeezing force; "
        "on the spreadsheet's scale the same force would be about a 2."),
    "granularity_conflict": ("The spreadsheet averages dozens of weighted sub-components into decimal force scores (its example's rivalry "
        "is 2.4167) and then averages the five forces with equal 0.2 weights into one overall score (3.39). The assignment requires whole numbers "
        "and naming the dominant forces instead of averaging. This tool uses the spreadsheet's sub-dimension categories only as a checklist to "
        "make sure each force's facts cover different points. It outputs one whole-number score per force and no sub-scores, and it never averages "
        "across forces. Where the judgment was torn between two numbers, the rationale says so."),
    "spreadsheet_used_for": "Only the standard of evidence depth: each force backed by several specific, cited facts.",
    "evidence_rules": ("Each fact has at least one citation with a verbatim quote of 25 words or fewer. A fact counts only if every quote "
        "verifies in code against cached source text; unverified facts are dropped. Each force needs at least 3 verified facts across at "
        "least 2 sub-dimensions, and its rationale must cite them by ID."),
    "who_did_what": ("Facts, claims, quotes, scores and rationales were written by Claude Code (an LLM agent) as judgment. Code fetched the "
        "public sources, mapped signals, checked coverage, verified every quote, enforced the scoring rules, and wrote these files. No code "
        "checks that a fact means what its claim says; that needs a human reader."),
}
LIMITS = [
    "Proxy industry: fractional CFO has no NAICS code. Report figures describe management consulting (54161, a superset of the chosen 541611) or accounting (54121c, the rejected neighbor), not the niche.",
    "Dated and mixed-vintage sources: IBISWorld May and August 2026, First Research July 2025 (one profitability figure is from 2023), while AI finance tools change monthly.",
    "IBISWorld 54121c contradicts itself on market size and growth ($158.4bn/1.4% vs $157.4bn/1.3%); neither figure drives a score.",
    "First Research is thin: no competitor market shares (PARTIAL/low confidence on S2), no stated industry code.",
    "No source measures buyer concentration, switching, or substitution for $2M-$20M firms specifically; the buyer and substitute scores extrapolate from industry-wide or all-business data.",
    "Vendor pages (Pilot, Intuit) are marketing claims, cited as claims, not as independent evidence of performance.",
    "Two public facts are secondary or archived: the AICPA 2025 Trends figures come via CFO Dive coverage; the BLS page was fetched from its Internet Archive snapshot because bls.gov blocks scripts.",
    "Verification proves each quote exists in its cited source; it does not prove the claim drawn from it. Scores are an LLM agent's judgment under stated rules.",
]

out_forces = []
for k, r in RESULT.items():
    fs = [f for f in FACTS if f["force"] == k]
    order = {item: i for i, (item, _) in enumerate(CHECKLIST[k])}
    fs.sort(key=lambda f: (order[f["checklist_item"]], f["fact_id"]))
    out_forces.append({
        "key": k, "name": r["name"], "score": r["score"], "rationale": r["rationale"],
        "tally_sanity_check": r["tally"], "subdimensions_covered": sorted({f["checklist_item"] for f in fs}, key=order.get),
        "facts": [{"fact_id": f["fact_id"], "label": f["checklist_item"], "subdimension_detail": f["subdimension"], "direction": f["direction"],
                   "claim": f["claim"], "origin": f["origin"], "cited_in_rationale": f["fact_id"] in r["cited_fact_ids"],
                   "citations": [cite_out(c) for c in f["citations"]]} for f in fs]})

used_sources = sorted({c.get("doc_id") or c.get("source_id") for f in FACTS for c in f["citations"]})
SOURCES = [{"id": d, "type": "paywalled report", "title": REPORT_META[d]["title"], "publisher": REPORT_META[d]["publisher"],
            "date": REPORT_META[d]["publication_date"], "how_to_find": REPORT_META[d]["how_to_find"]} if d in REPORT_META else
           {"id": d, "type": f"public ({src_index[d]['kind']})", "title": src_index[d]["title"], "publisher": src_index[d]["publisher"],
            "url": src_index[d]["url"], "accessed": src_index[d]["accessed"], "fetched_via": src_index[d].get("fetch_url")} for d in used_sources]

FF = {
    "meta": {"company": brief["meta"]["company"], "segment": "US small and mid-sized businesses, roughly $2M-$20M revenue",
             "naics": f"{brief['naics']['chosen_code']} {brief['naics']['chosen_title']} (proxy; fractional CFO has no code)",
             "generated": datetime.datetime.now().isoformat(timespec="seconds"), "input": BRIEF,
             "notebook": "five_forces.ipynb", "verification_mode": VERIFICATION_SUMMARY["report_quote_mode"]},
    "method": METHOD, "limits": LIMITS, "forces": out_forces,
    "overall_read": {"dominant_forces": [FORCES[d] for d in ov["dominant_forces"]], "text": ov["text"],
                     "scores_listed_not_averaged": {RESULT[k]["name"]: RESULT[k]["score"] for k in FORCES}},
    "least_confident": {"force": FORCES[lc["force"]], "score": RESULT[lc["force"]]["score"], "why": lc["why"],
                        "what_would_settle_it": lc["what_would_settle_it"]},
    "stage1_mapping": [{"signal_id": s, "doc_id": d, "forces": v[0], "why": v[1]} for (s, d), v in STAGE1_MAP.items()],
    "thin_before_enrichment": [FORCES[k] for k in THIN], "verification_summary": VERIFICATION_SUMMARY, "sources": SOURCES,
}
json.dump(FF, open(OUT_JSON, "w"), indent=1, ensure_ascii=False)

def md_cite(c):
    where = f"p.{c['pdf_page']}" + (f" (printed {c['printed_page']})" if c.get("printed_page") else "") if c.get("pdf_page") else ""
    loc = "; ".join(x for x in [c["section"], where, c.get("url") or ""] if x)
    return f"    - \"{c['quote']}\" ({c['source']}; {loc}) [{c['verification']}]"

L = [f"# Porter's Five Forces: {FF['meta']['company']}", "",
     f"Segment: {FF['meta']['segment']}. Industry code: {FF['meta']['naics']}. Generated {FF['meta']['generated']} by `five_forces.ipynb` from `brief.json`.", "",
     f"**Scale:** {METHOD['scale']}", "", "| Force | Score |", "|---|---|"]
L += [f"| {f['name']} | {f['score']} |" for f in out_forces]
L += ["", "## Overall read", "", f"Dominant forces: **{', '.join(FF['overall_read']['dominant_forces'])}**.", "", ov["text"], ""]
for f in out_forces:
    L += [f"## {f['name']}: {f['score']} / 5", "", f["rationale"], "",
          f"Sub-dimensions covered: {', '.join(f['subdimensions_covered'])}. Direction tally (sanity check only): "
          f"+{f['tally_sanity_check']['+']} / -{f['tally_sanity_check']['-']} / mixed {f['tally_sanity_check']['mixed']}.", ""]
    for x in f["facts"]:
        L.append(f"- **{x['fact_id']}** [{x['label']}] ({x['direction']}) {x['claim']}")
        L += [md_cite(c) for c in x["citations"]]
    L.append("")
L += ["## Least-confident force", "", f"**{FF['least_confident']['force']}** (score {FF['least_confident']['score']}). {lc['why']}", "",
      f"**What would settle it:** {lc['what_would_settle_it']}", "",
      "## Method: the two conflicts with the course spreadsheet", "", f"- **Scale polarity.** {METHOD['polarity_conflict']}",
      f"- **Granularity.** {METHOD['granularity_conflict']}", f"- **Evidence rules.** {METHOD['evidence_rules']}",
      f"- **Who did what.** {METHOD['who_did_what']}", "", "## Limits", ""] + [f"- {x}" for x in LIMITS] + [
      "", "## Verification", "",
      f"- Five Forces quotes: {VERIFICATION_SUMMARY['five_forces_quotes_checked']} checked, {VERIFICATION_SUMMARY['five_forces_quotes_passed']} passed "
      f"(report quotes: {VERIFICATION_SUMMARY['report_quote_mode']}; public quotes: live).",
      f"- First-project quotes (brief.json signals + report scope): {VERIFICATION_SUMMARY['brief_json_quotes_checked']} checked, {VERIFICATION_SUMMARY['brief_json_quotes_passed']} passed ({brief_mode}).",
      f"- Negative controls: {VERIFICATION_SUMMARY['negative_controls_rejected']} of {VERIFICATION_SUMMARY['negative_controls_run']} corrupted quotes rejected.",
      "", "## Sources", ""]
L += [f"- `{s['id']}`: {s['publisher']}, \"{s['title']}\"" + (f" ({s['date']})" if s.get("date") else f", {s['url']} (accessed {s['accessed']})") for s in SOURCES]
open(OUT_MD, "w").write("\n".join(L) + "\n")
print(f"wrote {OUT_JSON} ({os.path.getsize(OUT_JSON):,} bytes) and {OUT_MD} ({os.path.getsize(OUT_MD):,} bytes)")
print(f"{len(FACTS)} verified facts across 5 forces; {len(SOURCES)} sources; scores:",
      {f['name']: f['score'] for f in out_forces})
