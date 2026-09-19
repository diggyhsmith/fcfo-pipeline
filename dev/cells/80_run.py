# %% [markdown]
# ## `run_pipeline(company, description, reports_dir, extractor)`: the whole thing in one call
#
# **Choice:** one function chains the same stage functions used above, so a reader can run it on a new industry by editing the config cell, adding PDFs to `reports/`, and either supplying
# `extractions/*.json` (the default, `claude_code_files`) or setting `extractor="gemini"` with a free key. The cell below calls it and then checks that it reproduces the brief the step-by-step cells built.
#
# **Alternative rejected:** hiding the stages inside the function. The stages are visible above so each choice can be inspected; the function only sequences them.
# **Limit:** the NAICS choice and the extraction files are industry-specific. Changing the industry means re-doing those two human/agent steps; the other stages will re-run unchanged.

# %%
def run_pipeline(company, description, reports_dir, extractor="claude_code_files", write_files=True):
    """Stage 0 ingest (if PDFs present) -> 1 NAICS fetch+validate -> 2 extract -> 3 verify -> 4 reconcile -> 5 gaps -> brief. Returns the brief dict."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is set; this pipeline is zero-cost and never calls a paid API. Unset it.")
    if glob.glob(os.path.join(reports_dir, "*.pdf")):
        pages, docs, _ = stage0_ingest(reports_dir)
    else:
        pages, docs = [], (json.load(open("sources.json")) if os.path.exists("sources.json") else {})
    naics = stage1_fetch()
    choice = stage1_choose(naics)
    extractions, note = run_extractor(extractor, pages, docs)
    items, numrows, struct, log, mode = stage3_verify(extractions)
    summ = summarize(items, numrows, struct)
    r1 = {tuple(k) for k in (log.get("rounds") or [{"failed_keys": []}])[0]["failed_keys"]}
    summ["corrected_in_retry"] = len(r1 & {(i["doc_id"], i["signal_id"], i["evidence_index"]) for i in items if i["result"] != "FAILED"})
    summ["rounds_run"] = len(log.get("rounds", []))
    verified = apply_verification(extractions, items, numrows)
    records, family = stage4_reconcile(extractions, verified, items, docs)
    gaps = stage5_gaps(extractions, verified, records, docs, naics=naics, chosen=choice["chosen_code"])
    brief = build_brief(company, description, docs, choice, extractions, records, gaps, summ, note, report_scope_table(extractions, docs, choice["chosen_code"]), mode, family)
    if write_files:
        json.dump(brief, open("brief.json", "w"), indent=1, ensure_ascii=False)
        open("brief.md", "w").write(render_brief_md(brief))
    return brief

BRIEF2 = run_pipeline(COMPANY, DESCRIPTION, REPORTS_DIR, EXTRACTOR)
_strip = lambda b: json.dumps({k: v for k, v in b.items() if k != "meta"}, sort_keys=True)
assert _strip(BRIEF2) == _strip(BRIEF), "run_pipeline() must reproduce the step-by-step brief"
print("run_pipeline() reproduced the step-by-step brief exactly (everything except the timestamp).\n")
print("FINAL SUMMARY")
print("  company        :", BRIEF2["meta"]["company"])
print("  NAICS          :", BRIEF2["naics"]["chosen_code"], BRIEF2["naics"]["chosen_title"])
print("  extractor      :", BRIEF2["meta"]["extractor"])
print("  gemini backend :", BRIEF2["meta"]["gemini_backend_status"])
print("  verification   :", BRIEF2["meta"]["verification_mode"])
_s = BRIEF2["verification_summary"]
print(f"  quotes         : {_s['quotes_checked']} checked, {_s['passed']} passed, {_s['failed']} failed, {_s['corrected_in_retry']} corrected in retry; numbers {_s['numbers_checked']} checked, {_s['numbers_unmatched']} unmatched")
print("  signal status  :", {s['signal_id']: s['status'] for s in BRIEF2['signals']})
print("  conflicts      :", sum(len(s['conflicts']) for s in BRIEF2['signals']), "| gaps:", len(BRIEF2['gaps']))
