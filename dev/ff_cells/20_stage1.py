# %% [markdown]
# ## Stage 1: map the untagged and ambiguous signals
#
# Every finding Stage 0 could not place gets an explicit mapping here, with one line of justification. The code below **fails** if any
# untagged finding is left unmapped, or if a mapping names a finding that does not exist. A finding may feed more than one force. The
# first force listed is where it counts as evidence; any other force listed is only context.

# %%
STAGE1_MAP = {
    ("S1", "ibisworld_54161"): (["rivalry", "new_entrants"],
        "Industry growth rate is a rivalry sub-dimension: 1.0%/yr forecast growth means share is won from rivals; size/growth is also what attracts entrants."),
    ("S1", "ibisworld_54121c"): (["rivalry"],
        "Growth rate again (rivalry). This is the report that contradicts itself ($158.4bn/1.4% vs $157.4bn/1.3%); both are kept and neither is used for a score."),
    ("S1", "firstresearch_accounting-services"): (["rivalry"],
        "133,000 establishments = number of competitors (rivalry: fragmentation); the 4%/yr forecast is the growth sub-dimension."),
    ("S6", "ibisworld_54161"): (["new_entrants", "rivalry"],
        "'Entry of niche firms ... expected to increase' is direct evidence on entry; more niche entrants then raise rivalry."),
    ("S6", "firstresearch_accounting-services"): (["new_entrants"],
        "Cloud/SaaS/AI adoption by small accounting FIRMS lowers the cost of operating a small practice (entry), not a tool clients use instead (so not substitutes)."),
    ("S7", "firstresearch_accounting-services"): (["buyer_power", "new_entrants"],
        "'Slow economy cuts business needs' is the demand-trend sub-dimension of buyer power; the litigation-risk quote for firms that act as consultants is a (weak) entry barrier."),
}

untagged = [f for f in findings if not f["clean"]]
missing = [(f["signal_id"], f["doc_id"]) for f in untagged if (f["signal_id"], f["doc_id"]) not in STAGE1_MAP]
extra = [k for k in STAGE1_MAP if k not in {(f["signal_id"], f["doc_id"]) for f in untagged}]
assert not missing, f"untagged findings without a mapping: {missing}"
assert not extra, f"mappings for findings that are not untagged: {extra}"

for f in untagged:
    forces, why = STAGE1_MAP[(f["signal_id"], f["doc_id"])]
    f["mapped_forces"] = forces
    print(f"{f['signal_id']} {f['doc_id']:34} tag={f['force_tag']!r}\n    -> {', '.join(forces)}: {why}")

brief_by_force = defaultdict(list)                 # every brief finding, by the force it is evidence for
for f in findings:
    primary = f["tag_forces"][0] if f["clean"] else f["mapped_forces"][0]
    brief_by_force[primary].append(f)
print("\nAll brief.json evidence per force after Stage 1 (primary mapping):")
for k, name in FORCES.items():
    fs = brief_by_force[k]
    print(f"  {name:38} findings={len(fs)}  verified quotes={sum(len(f['citations']) for f in fs):2}  "
          f"documents={len({f['doc_id'] for f in fs})}")
