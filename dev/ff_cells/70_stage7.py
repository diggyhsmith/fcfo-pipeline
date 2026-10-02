# %% [markdown]
# ## Stage 7: verification report (old and new quotes)
#
# Three parts:
# 1. **All 79 quotes from the first project** (the 71 behind `brief.json` signals plus 8 report-scope quotes) are re-checked against the report page cache. Without the cache (fresh clone), the committed
#    `verification_log.json` from the first project is replayed, and the output says so.
# 2. **Every quote behind a Five Forces fact** (Stage 3 results), counted by origin: brief, new report-page extraction, public source.
# 3. **Negative controls.** Corrupted copies of real quotes (a changed number, a reversed word, the wrong page, the wrong source) must
#    **fail**. This shows the verifier can reject a bad quote, not only accept good ones. The verifier's source is printed so the matching rule
#    is visible here and not only in `verify.py`.

# %%
print(inspect.getsource(verify.normalize)); print(inspect.getsource(verify._same_tokens)); print(inspect.getsource(verify.check_quote))

# %%
# 1. brief.json quotes
brief_items = []
if REPORTS_AVAILABLE:          # same driver as pipeline.ipynb: every quote in extractions/*.json (signals + report scope)
    items_, _, _ = verify.verify_all(verify.load_extractions(), IDX)
    brief_items = [{"signal_id": it["signal_id"], "doc_id": it["doc_id"], "result": it["result"], "method": it["method"]} for it in items_]
    brief_mode = "LIVE re-check against cache/pages.jsonl"
else:
    old = json.load(open("verification_log.json"))
    brief_items = [{"signal_id": it["signal_id"], "doc_id": it["doc_id"], "result": it["result"], "method": it["method"]}
                   for it in old["items"]]
    brief_mode = "REPLAYED from verification_log.json (paywalled PDFs/cache not in this clone)"
b_pass = sum(1 for i in brief_items if i["result"] != "FAILED")
print(f"first-project quotes (brief.json signals + report scope): {len(brief_items)} checked, {b_pass} pass, {len(brief_items) - b_pass} fail   [{brief_mode}]")

# 2. Five Forces evidence quotes
by_origin = defaultdict(Counter)
for it in ver_items:
    by_origin[it["origin"]]["pass" if it["result"] != "FAILED" else "fail"] += 1
    by_origin[it["origin"]][it["mode"]] += 1
print("\nFive Forces evidence quotes, by origin:")
for o in ("brief", "report_page", "public"):
    c = by_origin[o]
    print(f"  {o:12} checked {c['pass'] + c['fail']:3}  pass {c['pass']:3}  fail {c['fail']}   (live {c['live']}, replayed {c['replay']})")
methods = Counter((it["result"], it["method"]) for it in ver_items)
print("  match methods:", dict(methods))
over = [it for it in ver_items if it["words"] > 25]
print("  quotes over 25 words:", len(over))

# 3. Negative controls
def corrupt_number(q):
    return re.sub(r"\d", lambda m: str((int(m.group()) + 1) % 10), q, count=1)
controls = []
pub = [it for it in ver_items if it["origin"] == "public" and re.search(r"\d", it["quote"])]
rep = [it for it in ver_items if it["origin"] != "public"]
cases = [("changed number (public)", pub[0]["doc"], 1, corrupt_number(pub[0]["quote"])),
         ("reversed meaning (public)", "cfodive_aicpa_trends_2025", 1,
          "The number of U.S. students who graduated with a bachelor's or a master's degree in accounting rose 6.6%"),
         ("right quote, wrong source", "pilot_cfo_services", 1, "The professional services industry is highly fragmented and competitive."),
         ("over 25 words", "sec_cbiz_10k_fy2025", 1, " ".join(["word"] * 26))]
if REPORTS_AVAILABLE:
    cases += [("changed number (report)", "ibisworld_54161", 34, "Deloitte ($22.4bn) 6.3% Other Companies ($397.9bn) 94.7%"),
              ("reversed meaning (report)", "ibisworld_54121c", 30, "the accounting services space has high switching costs"),
              ("wrong page (report, 5 pages off)", "ibisworld_54161", 24, "Wages represent the industry's most significant expense category.")]
for label, doc, page, q in cases:
    r = check_quote(IDX, doc, page, q)
    controls.append({"control": label, "doc": doc, "pdf_page": page, "quote": q[:120], "result": r["result"], "reason": r["reason"]})
    print(f"  control '{label}': {r['result']}" + ("   <-- PROBLEM: corrupted quote passed" if r["result"] != "FAILED" else ""))
assert all(c["result"] == "FAILED" for c in controls), "a negative control passed"
if not REPORTS_AVAILABLE:
    print("  (report-page controls skipped: no page cache in this clone)")

total = len(ver_items); passed = sum(1 for it in ver_items if it["result"] != "FAILED")
VERIFICATION_SUMMARY = {
    "five_forces_quotes_checked": total, "five_forces_quotes_passed": passed, "five_forces_quotes_failed": total - passed,
    "by_origin": {o: {"checked": by_origin[o]["pass"] + by_origin[o]["fail"], "passed": by_origin[o]["pass"]} for o in ("brief", "report_page", "public")},
    "report_quote_mode": "live" if REPORTS_AVAILABLE else "replayed from five_forces_verification_log.json",
    "public_quote_mode": "live", "facts_total": len(facts), "facts_kept": len(FACTS), "facts_dropped": dropped,
    "brief_json_quotes_checked": len(brief_items), "brief_json_quotes_passed": b_pass, "brief_json_mode": brief_mode,
    "negative_controls_run": len(controls), "negative_controls_rejected": sum(1 for c in controls if c["result"] == "FAILED"),
}
print("\nSUMMARY:", json.dumps(VERIFICATION_SUMMARY, indent=1))

if REPORTS_AVAILABLE:          # only a live run may (re)write the log that fresh clones replay
    json.dump({"generated": datetime.datetime.now().isoformat(timespec="seconds"),
               "note": "Quotes <= 25 words; no page text stored. 'verified' = quote exists on the cited page/source, not that its interpretation is right.",
               "summary": VERIFICATION_SUMMARY, "items": ver_items, "negative_controls": controls},
              open(FF_LOG, "w"), indent=1, ensure_ascii=False)
    print("wrote", FF_LOG)
