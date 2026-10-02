# %% [markdown]
# ## Stage 5: overall read (dominant forces, not an average)
#
# The written assignment asks for the one or two forces that dominate, not an average. The checks below make sure the overall read names 1-2
# forces that exist and that it is 3-5 sentences. They also make sure the read is consistent with the scores: a dominant force must score at
# least as high as every force that is not named. **The five scores are listed but never averaged.**
#
# ## Stage 6: least-confident force
#
# The force the agent was least sure of, why, and what evidence would settle it.

# %%
ov = scores["overall_read"]
dom = ov["dominant_forces"]
KEYWORD = {"rivalry": "rivalry", "buyer_power": "buyer", "supplier_power": "supplier", "new_entrants": "new entrants", "substitutes": "substitut"}
assert 1 <= len(dom) <= 2 and all(d in FORCES for d in dom), "overall read must name 1-2 known forces"
assert all(KEYWORD[d] in ov["text"].lower() for d in dom), "dominant forces must be named in the text"
assert 3 <= len(sentences(ov["text"])) <= 5, f"overall read has {len(sentences(ov['text']))} sentences (want 3-5)"
assert min(RESULT[d]["score"] for d in dom) >= max(r["score"] for k, r in RESULT.items() if k not in dom), \
    "a force named as dominant scores below a force that is not named"
assert not re.search(r"\d\.\d", ov["text"]), "overall read contains a decimal (looks like an average)"

print("Scores (listed, NOT averaged):")
for k, r in RESULT.items():
    print(f"  {r['score']}  {r['name']}" + ("   <- dominant" if k in dom else ""))
print("\nOverall read:\n" + "\n".join(textwrap.wrap(ov["text"], 110)))

lc = scores["least_confident"]
assert lc["force"] in FORCES
print(f"\nLeast-confident force: {FORCES[lc['force']]} (score {RESULT[lc['force']]['score']})")
print("Why:", lc["why"])
print("What would settle it:", lc["what_would_settle_it"])
