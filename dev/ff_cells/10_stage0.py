# %% [markdown]
# ## Stage 0: load `brief.json` and collect the signals already tagged to a force
#
# The first project tagged each (signal, document) finding with a `force_tag`, for example `"supplier power"` or `"barriers to entry"`.
# A tag counts as **clean** if it names exactly one force and is not hedged ("context", "-adjacent"). Everything else goes to Stage 1.
# Only citations that passed the first project's verifier (`verification == "verified"`) are counted.

# %%
brief = json.load(open(BRIEF))
TAG_RULES = [("rivalry", "rivalry"), ("barriers to entry", "new_entrants"), ("new entrants", "new_entrants"),
             ("supplier", "supplier_power"), ("buyer", "buyer_power"), ("substitutes", "substitutes")]

def tag_to_forces(tag):
    t = (tag or "").lower()
    forces = sorted({f for k, f in TAG_RULES if k in t})
    hedged = "context" in t or "adjacent" in t
    return forces, (len(forces) == 1 and not hedged)

findings = []
for s in brief["signals"]:
    for f in [s["primary"]] + s.get("other_documents", []):
        forces, clean = tag_to_forces(f.get("force_tag"))
        cites = [c for c in f.get("citations", []) if c.get("verification", "").startswith("verified")]
        findings.append({"signal_id": s["signal_id"], "signal": s["name"], "doc_id": f["doc_id"], "status": f["status"],
                         "force_tag": f.get("force_tag"), "tag_forces": forces, "clean": clean, "citations": cites,
                         "summary": f.get("summary", "")})

print(f"{len(findings)} (signal, document) findings in brief.json; "
      f"{sum(len(f['citations']) for f in findings)} verified citations\n")
print(f"{'sig':4} {'document':36} {'status':9} {'force_tag':52} {'clean?':6} cites")
for f in findings:
    print(f"{f['signal_id']:4} {f['doc_id']:36} {f['status']:9} {str(f['force_tag'])[:52]:52} {'yes' if f['clean'] else 'NO':6} {len(f['citations'])}")

tagged = defaultdict(list)
for f in findings:
    if f["clean"]:
        tagged[f["tag_forces"][0]].append(f)
print("\nCleanly tagged evidence per force (before Stage 1):")
for k, name in FORCES.items():
    fs = tagged[k]
    n_c = sum(len(f["citations"]) for f in fs)
    docs = sorted({f["doc_id"] for f in fs})
    print(f"  {name:38} findings={len(fs)}  verified quotes={n_c:2}  documents={len(docs)}  {'(3+ quotes)' if n_c >= 3 else '(THIN)'}")
