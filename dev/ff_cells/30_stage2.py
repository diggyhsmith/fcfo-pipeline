# %% [markdown]
# ## Stage 2: evidence-depth checklist (organizes the search; it never produces a sub-score)
#
# The sub-dimensions below come from the course's Five Forces glossary. They are used for one thing only: checking that a force's facts
# cover **different** sub-dimensions instead of being three versions of one point. Each fact in `five_forces_evidence.json` has a
# `subdimension` label. The checklist matches labels to glossary items by keyword. **No numeric sub-score is computed or output.**
#
# Counting raw quotes from `brief.json` overstates the evidence. Several quotes restate one fact, some describe large corporate buyers rather
# than our segment, and most come from a single IBISWorld report. So the "solid" count below counts only the facts the agent kept from
# `brief.json` (`origin.type == "brief"`) after reading them against the $2M-$20M segment. A force is **thin** if it has fewer than 3 solid facts
# or fewer than 2 sub-dimensions. Thin forces **must** be enriched in Stage 3.

# %%
CHECKLIST = {
    "rivalry": [("market concentration / fragmentation", ["concentration", "number and diversity"]),
                ("product / price standardization", ["standardization", "price transparency", "differentiation"]),
                ("industry growth rate", ["growth", "incumbents moving"]),
                ("capacity utilization", ["capacity"]),
                ("exit barriers / fixed costs", ["fixed costs", "exit"])],
    "buyer_power": [("buyer concentration", ["buyer concentration", "buyer size"]),
                    ("buyer switching costs", ["buyer switching"]),
                    ("demand / growth trend", ["demand trend"]),
                    ("threat of backward integration", ["backward integration"]),
                    ("buyer price sensitivity", ["price sensitivity", "buyer dependence"])],
    "supplier_power": [("supplier concentration", ["supplier concentration"]),
                       ("cost / difficulty of switching suppliers", ["switching suppliers"]),
                       ("supplier brand / input importance", ["input importance"]),
                       ("threat of supplier forward integration", ["forward integration"])],
    "new_entrants": [("capital / scale requirements", ["capital", "technology lowering"]),
                     ("brand / marketing investment", ["brand"]),
                     ("IP or regulatory barriers", ["regulatory", "licensing"]),
                     ("profitability and growth attracting entrants", ["profitability", "entry frequency"])],
    "substitutes": [("availability and awareness of substitutes", ["availability", "adoption"]),
                    ("relative price", ["relative price"]),
                    ("relative performance", ["relative performance", "threat rating"]),
                    ("customer switching cost to the substitute", ["switching cost to substitute"])],
}

def checklist_item(force, subdim):
    s = subdim.lower()
    for item, keys in CHECKLIST[force]:
        if any(k in s for k in keys):
            return item
    return None

evidence = json.load(open(EVIDENCE))
facts = evidence["facts"]
ids = [f["fact_id"] for f in facts]
assert len(ids) == len(set(ids)), "duplicate fact_id"
for f in facts:
    assert f["force"] in FORCES, f"{f['fact_id']}: unknown force {f['force']}"
    assert f["direction"] in ("+", "-", "mixed"), f"{f['fact_id']}: bad direction"
    f["checklist_item"] = checklist_item(f["force"], f["subdimension"])
    assert f["checklist_item"], f"{f['fact_id']}: subdimension {f['subdimension']!r} matches no checklist item"

def coverage(fs, force):
    hit = Counter(f["checklist_item"] for f in fs if f["force"] == force)
    return hit

THIN = []
print("Brief-only coverage (facts kept from brief.json):\n")
for k, name in FORCES.items():
    fs = [f for f in facts if f["force"] == k and f["origin"]["type"] == "brief"]
    hit = coverage(fs, k)
    thin = len(fs) < MIN_FACTS or len(hit) < MIN_SUBDIMS
    docs = Counter(f["origin"]["doc_id"] for f in fs)
    if thin: THIN.append(k)
    print(f"{name}: {len(fs)} solid facts from brief.json, {len(hit)} sub-dimensions -> {'THIN: must enrich' if thin else 'meets 3/2 minimum'}")
    for item, _ in CHECKLIST[k]:
        print(f"    [{'x' if hit[item] else ' '}] {item}" + (f"  ({hit[item]})" if hit[item] else ""))
    print(f"    sources: {dict(docs)}")
print("\nThin after Stages 0-2:", [FORCES[k] for k in THIN] or "none")
ibis = sum(1 for f in facts if f["origin"]["type"] == "brief" and f["origin"]["doc_id"].startswith("ibisworld"))
nb = sum(1 for f in facts if f["origin"]["type"] == "brief")
print(f"Share of brief-derived facts that come from IBISWorld: {ibis}/{nb}. Because of that single-publisher dependence, Stage 3 also adds "
      f"independent public evidence to forces that are not thin.")
