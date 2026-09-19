# %% [markdown]
# ## Stage 4: Reconciliation across documents
#
# **Choice:** for each signal, code gathers every document's *verified* finding and picks one **primary** by a stated rule:
# (1) the report whose stated NAICS scope contains the chosen code (541611) beats one that does not; (2) then FOUND beats PARTIAL; (3) then the more recent publication date.
# The primary is a *presentation choice*. Nothing is dropped or averaged: any place where two documents (or one document against itself) give different values for the
# same metric goes into `conflicts[]` with both sides, page citations and a note on why they differ.
#
# **Alternatives rejected:** averaging or weighting values (it would invent a number no report published, and the reports measure different industries); always preferring the newest report
# (the newest report is not the one nearest our NAICS code); silently dropping the loser.
#
# **Limit:** the rule ranks by *scope proximity*, and scope proximity here is weak: the "closest" report (54161) is all management consulting. Different-industry figures are shown as "not comparable", not as disagreement.

# %%
PRIMARY_RULE = ("Primary = the document whose stated NAICS scope includes the chosen code; then FOUND before PARTIAL; then the more recent publication date. "
                "Other documents' findings are always shown alongside; conflicting values are never averaged.")

def parse_pub_date(s):
    try: return datetime.datetime.strptime(s.replace("Data Published: ", "").strip(" ."), "%B %Y").date()
    except Exception: return datetime.date.min

def scope_rank(ext, chosen=None):
    chosen = chosen or CHOSEN_CODE
    codes = ext["report_scope"].get("naics_2022_listed", [])
    if chosen in codes: return 0
    if any(c[:5] == chosen[:5] for c in codes): return 1
    return 2

def industry_family(doc, ext):
    codes = ext["report_scope"].get("naics_2022_listed", [])
    if any(c.startswith("5412") for c in codes) or "accounting" in doc.get("title", "").lower(): return "accounting"
    if any(c.startswith("5416") for c in codes): return "management consulting"
    return "other"

def _cite(items, doc_id, sid, prefer_number=None):
    ev = [i for i in items if i["doc_id"] == doc_id and i["signal_id"] == sid and i["result"] in ("verified", "verified_adjacent_page")]
    if prefer_number is not None:
        for i in ev:
            if round(float(prefer_number), 6) in {round(n, 6) for n in numbers_in(i["quote"])}: return _fmt_cite(i)
    return _fmt_cite(ev[0]) if ev else None

def _fmt_cite(i):
    return {"doc_id": i["doc_id"], "section_heading": i["section_heading"], "pdf_page": i["pdf_page"], "printed_page": i["printed_page"],
            "quote": i["quote"], "verification": i["result"]}

def _lead_rating(text):
    m = re.match(r"\s*(Low|Moderate|High)\b", text or "", re.I)
    return m.group(1).capitalize() if m else None

def stage4_reconcile(extractions, verified, items, docs):
    """Returns per-signal records (primary + others + conflicts). Pure code, no model call."""
    order = sorted(extractions, key=lambda d: (scope_rank(extractions[d]), -parse_pub_date(docs[d]["publication_date"] or "").toordinal()))
    records = {}
    for sid in SIGNAL_META:
        cands = []
        for d in extractions:
            sig = next(s for s in extractions[d]["signals"] if s["signal_id"] == sid)
            v = verified[d][sid]
            if v["status_final"] in ("FOUND", "PARTIAL"):
                cands.append((scope_rank(extractions[d]), 0 if v["status_final"] == "FOUND" else 1,
                              -parse_pub_date(docs[d]["publication_date"] or "").toordinal(), d, sig, v))
        cands.sort(key=lambda c: c[:4])
        def pack(c):
            _, _, _, d, sig, v = c
            return {"doc_id": d, "status": v["status_final"], "force_tag": sig["force_tag"], "value": sig["value"], "summary": sig["summary"],
                    "confidence": sig["confidence"], "notes": sig["notes"],
                    "citations": [_fmt_cite(i) for i in v["verified_evidence"]], "numbers_unmatched": v["numbers_unmatched"]}
        records[sid] = {"signal_id": sid, "name": SIGNAL_META[sid][0], "primary": pack(cands[0]) if cands else None,
                        "other_documents": [pack(c) for c in cands[1:]], "conflicts": [], "not_supported_by": [
                            {"doc_id": d, "status": verified[d][sid]["status_final"]} for d in extractions if verified[d][sid]["status_final"] not in ("FOUND", "PARTIAL")]}
    fam = {d: industry_family(docs[d], extractions[d]) for d in extractions}
    val = lambda d, sid: next(s for s in extractions[d]["signals"] if s["signal_id"] == sid)["value"]
    ok = lambda d, sid: verified[d][sid]["status_final"] in ("FOUND", "PARTIAL")

    # (a) same metric, same industry family, different values (S1)
    for metric, label in (("market_size", "Market size (USD bn)"), ("cagr_historical_pct", "Historical 5-yr CAGR (%)"), ("cagr_forecast_pct", "Forecast 5-yr CAGR (%)")):
        docs_with = [d for d in extractions if ok(d, "S1") and val(d, "S1").get(metric) is not None]
        for i, a in enumerate(docs_with):
            for b in docs_with[i + 1:]:
                if fam[a] == fam[b] and val(a, "S1")[metric] != val(b, "S1")[metric]:
                    period = lambda d: val(d, "S1").get("forecast_period" if "forecast" in metric else "historical_period", val(d, "S1").get("market_size_year"))
                    records["S1"]["conflicts"].append({
                        "kind": "value_disagreement_same_industry_family", "metric": label,
                        "sides": [{"doc_id": d, "value": val(d, "S1")[metric], "period_or_year": period(d), "citation": _cite(items, d, "S1", val(d, "S1")[metric])} for d in (a, b)],
                        "why_they_may_differ": "Both describe accounting services but with different scope (First Research includes payroll and tax preparation), vintage (July 2025 vs May 2026) and, for growth, "
                                               "different periods and price basis. The reports do not say which is right."})
    # (b) a document disagreeing with itself
    for d in extractions:
        for sid in SIGNAL_META:
            v = val(d, sid) if ok(d, sid) else None
            if v and "internal_conflict" in v:
                ic = v["internal_conflict"]
                for metric, label in (("market_size", "Market size (USD bn)"), ("cagr_historical_pct", "Historical 5-yr CAGR (%)"), ("cagr_forecast_pct", "Forecast 5-yr CAGR (%)")):
                    if metric in ic and ic[metric] != v.get(metric):
                        records[sid]["conflicts"].append({
                            "kind": "within_document", "metric": label,
                            "sides": [{"doc_id": d, "value": v[metric], "period_or_year": "At a Glance / Performance Snapshot", "citation": _cite(items, d, sid, v[metric])},
                                      {"doc_id": d, "value": ic[metric], "period_or_year": "Executive Summary text", "citation": _cite(items, d, sid, ic[metric])}],
                            "why_they_may_differ": ic.get("where", "")})
    # (c) rating disagreements (different scopes): regulation, entry barriers, buyer power
    for sid, key, label in (("S3", "regulation_level", "Regulation & policy rating"), ("S3", "barriers_to_entry_level", "Barriers to entry rating"),
                            ("S5", "buyer_power_rating", "Buyer power rating")):
        rated = {d: _lead_rating(val(d, sid).get(key)) for d in extractions if ok(d, sid) and val(d, sid).get(key)}
        if len(set(rated.values())) > 1:
            records[sid]["conflicts"].append({
                "kind": "rating_disagreement_different_scope", "metric": label,
                "sides": [{"doc_id": d, "value": val(d, sid)[key], "period_or_year": f"{docs[d]['publisher'].split(' (')[0]} rating/wording", "citation": _cite(items, d, sid)} for d in rated],
                "why_they_may_differ": "Each rating is for a different industry (management consulting vs accounting firms) and the publishers word them differently, so they are not the same measurement; shown side by side, not merged."})
    # (d) same company, different share basis (S2)
    shares = collections.defaultdict(list)
    for d in extractions:
        if ok(d, "S2"):
            for c in val(d, "S2")["competitors"]:
                if c.get("share_pct") is not None or c.get("share_range"):
                    shares[c["name"].lower().replace(" plc", "")].append((d, c))
    for name, lst in shares.items():
        if len({x[0] for x in lst}) > 1:
            records["S2"]["conflicts"].append({
                "kind": "same_firm_different_share_basis", "metric": f"Market share of {lst[0][1]['name']}",
                "sides": [{"doc_id": d, "value": c["share_pct"] if c.get("share_pct") is not None else c["share_range"], "period_or_year": c["share_basis"],
                           "citation": _cite(items, d, "S2", c.get("share_pct"))} for d, c in lst],
                "why_they_may_differ": "The denominators are different industries (accounting vs management consulting), so the shares are not comparable and must not be averaged or added."})
    return records, fam

RECORDS, FAMILY = stage4_reconcile(EXTRACTIONS, VERIFIED, ITEMS, DOCS)
print("Rule:", PRIMARY_RULE, "\n")
print("Industry family per document:", FAMILY, "\n")
for sid, r in RECORDS.items():
    p = r["primary"]
    print(f"{sid} {r['name']}\n   primary: {p['doc_id'] if p else 'NONE'} ({p['status'] if p else '-'}) | other documents: {[o['doc_id'] for o in r['other_documents']]} | conflicts: {len(r['conflicts'])}")
print("\nConflicts kept side by side (never averaged):")
for sid, r in RECORDS.items():
    for c in r["conflicts"]:
        sides = "  vs  ".join(f"{s['doc_id']}={s['value']}" for s in c["sides"])
        print(f"  [{sid}] {c['kind']}: {c['metric']}: {sides}")
