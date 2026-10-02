# %% [markdown]
# ## Stage 4: score each force (judgment), with the rules enforced in code
#
# The scores and rationales in `five_forces_scores.json` are the agent's judgment. Code does not invent them, and code does not compute them
# from the facts. **The code does refuse any score that breaks the rules:**
#
# * the score is an integer from 1 to 5 (no decimals, no strings);
# * the rationale is 2-3 sentences and cites, by ID, at least 3 **verified** facts **of that force**;
# * the cited facts span at least 2 checklist sub-dimensions;
# * every fact the rationale cites exists and was not dropped in Stage 3.
#
# The **direction tally** (facts that make the force stronger `+` vs weaker `-`) is printed only as a sanity check on the judgment. It is not
# a score. A score of 4-5 alongside mostly `-` facts, or 1-2 alongside mostly `+` facts, is flagged for a human to look at.

# %%
scores = json.load(open(SCORES))
FACT = {f["fact_id"]: f for f in FACTS}
ALL_IDS = {f["fact_id"] for f in facts}

def sentences(t):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", t.strip()) if s]

problems, RESULT = [], OrderedDict()
for k, name in FORCES.items():
    s = scores["forces"][k]
    sc, rat = s["score"], s["rationale"]
    if not (isinstance(sc, int) and not isinstance(sc, bool) and 1 <= sc <= 5):
        problems.append(f"{k}: score {sc!r} is not a whole number 1-5")
    cited = list(OrderedDict.fromkeys(re.findall(r"\b([RBPNX]\d+)\b", rat)))
    unknown = [i for i in cited if i not in ALL_IDS]
    unverified = [i for i in cited if i in ALL_IDS and i not in FACT]
    wrong_force = [i for i in cited if i in FACT and FACT[i]["force"] != k]
    good = [i for i in cited if i in FACT and FACT[i]["force"] == k]
    subdims = {FACT[i]["checklist_item"] for i in good}
    n_sent = len(sentences(rat))
    if unknown: problems.append(f"{k}: rationale cites unknown facts {unknown}")
    if unverified: problems.append(f"{k}: rationale cites dropped/unverified facts {unverified}")
    if wrong_force: problems.append(f"{k}: rationale cites facts of another force {wrong_force}")
    if len(good) < MIN_FACTS: problems.append(f"{k}: rationale cites only {len(good)} verified facts")
    if len(subdims) < MIN_SUBDIMS: problems.append(f"{k}: cited facts cover only {len(subdims)} sub-dimension(s)")
    if not 2 <= n_sent <= 3: problems.append(f"{k}: rationale has {n_sent} sentences (want 2-3)")
    fs = [f for f in FACTS if f["force"] == k]
    tally = Counter(f["direction"] for f in fs)
    flag = (sc >= 4 and tally["-"] > tally["+"]) or (sc <= 2 and tally["+"] > tally["-"])
    RESULT[k] = {"name": name, "score": sc, "rationale": rat, "cited_fact_ids": good, "subdimensions_cited": sorted(subdims),
                 "tally": {"+": tally["+"], "-": tally["-"], "mixed": tally["mixed"]}, "tally_flag": flag,
                 "low_evidence": k in LOW_EVIDENCE}

assert not problems, "Scoring rules broken:\n" + "\n".join(problems)
print("All scoring rules pass.\n")

for k, r in RESULT.items():
    print("=" * 110)
    print(f"{r['name'].upper()}: {r['score']} / 5" + ("   [LOW EVIDENCE]" if r["low_evidence"] else ""))
    print("Rationale:", r["rationale"])
    print(f"Direction tally (sanity check only, not a score): +{r['tally']['+']} / -{r['tally']['-']} / mixed {r['tally']['mixed']}"
          + ("   <-- FLAG: score and tally point different ways" if r["tally_flag"] else ""))
    print("Facts, grouped by sub-dimension:")
    for item, _ in CHECKLIST[k]:
        for f in [f for f in FACTS if f["force"] == k and f["checklist_item"] == item]:
            print(f"  {f['fact_id']:3} ({f['direction']:>5}) [{item}] {f['claim']}")
            for c in f["citations"]:
                where = (c.get("doc_id") or c.get("source_id")) + (f", p.{c['pdf_page']}" if c.get("pdf_page") else "")
                print(f"        \"{c['quote']}\"  ({where}; {c['section']}) [{c['verification']}]")
