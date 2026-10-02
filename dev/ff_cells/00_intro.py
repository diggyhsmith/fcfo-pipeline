# %% [markdown]
# # Porter's Five Forces Scorer: fractional CFO services (NAICS 541611 proxy)
#
# **What this notebook does.** It reads the industry brief built by `pipeline.ipynb` (`brief.json`). It maps every brief signal to the
# Five Forces, finds the forces with too little evidence, adds evidence from public sources for them, and **verifies every quote in code**
# against cached source text. It then applies a set of scoring rules to the scores and writes `five_forces.json` and `five_forces.md`.
# The company is "TBD, Fractional CFO Services", selling to US small and mid-sized businesses with about $2M-$20M revenue.
#
# **Who did what (read this first)**
#
# | Step | Done by |
# |---|---|
# | Choosing the facts, writing each claim, copying the quotes (`five_forces_evidence.json`) | **Claude Code, an LLM agent**, in the build session (2026-10-02). No paid API, no API key. |
# | The five scores, rationales, overall read and least-confident force (`five_forces_scores.json`) | **Claude Code (LLM agent)**. These are judgments, not computed. |
# | Fetching public sources (`fetch_public.py`), mapping, coverage checks, quote verification, rule checks on the scores, writing outputs | Plain Python in this notebook, run top to bottom |
# | Checking that each fact *means* what its claim says | **Not done by code.** Verification proves a quote exists on the cited page, not that the interpretation is right. A human has to read it. |
#
# ## Method: the scale, and two deliberate departures from the course spreadsheet
#
# **Scale used here: 1-5, whole numbers only. 5 = the force is strong and squeezes industry profits hard; 1 = the force is weak.**
#
# The course's reference spreadsheet (`Porters 5 Forces template with Neighbor Example.xlsx`, a self-storage example) is used only as a
# **standard of evidence depth**: every force should rest on several specific, cited facts, not a feeling. Its scoring method is **not** used,
# for two reasons:
#
# 1. **Scale polarity conflict.** The spreadsheet scores every force for *attractiveness to incumbents*: 5 = most attractive (a weak
#    force), 1 = least attractive (a strong force). Its summary row reads "Overall Industry Attractiveness (5 = most attractive, 1 = least
#    attractive)". The written assignment uses the **opposite** convention: "5 means the force is strong, it squeezes industry profits hard;
#    1 means weak." **This tool follows the written assignment.** A 4 here means a strong force that hurts profits. On the spreadsheet's
#    scale the same force would be about a 2.
# 2. **Granularity conflict.** The spreadsheet scores dozens of weighted sub-components per force, averages them into decimal force scores
#    (the example's rivalry is 2.4167), then averages the five forces with equal 0.2 weights into one overall number (3.39). The assignment
#    requires **whole numbers** and says that naming the one or two forces that dominate is better than averaging. So this tool uses the
#    spreadsheet's sub-dimension categories (from its glossary) **only as a checklist** (Stage 2). The checklist makes sure each force's 3+
#    facts are not three versions of the same point. The output is one whole-number score per force, never a sub-score, and **no number is
#    averaged across forces anywhere in this notebook**. Where the judgment was torn between two numbers, the rationale says so instead of
#    using a decimal.
#
# **Evidence rules (enforced in code below):** every scored fact has at least one citation (document, section, page where one exists) with a
# verbatim quote of 25 words or fewer. A fact whose quote does not verify is dropped, not kept. Every force needs at least 3 verified facts
# covering at least 2 checklist sub-dimensions. Quotes from the paywalled reports stay at 25 words or fewer, and their full text is never
# committed (`reports/`, `cache/` are git-ignored).
#
# **Run it:** `pip install -r requirements.txt`, then `jupyter nbconvert --to notebook --execute --inplace five_forces.ipynb`. A fresh clone
# without the paywalled PDFs **replays** the committed report-quote verification and says so. Public-source quotes are always re-verified live
# against `public_sources/`.

# %%
import json, os, re, sys, datetime, inspect, hashlib, textwrap
from collections import Counter, defaultdict, OrderedDict

import verify                                     # the Stage 3 verifier from pipeline.ipynb (verify.py); source printed in Stage 7
from verify import normalize, build_page_index, check_quote

BRIEF = "brief.json"
EVIDENCE = "five_forces_evidence.json"           # facts + quotes (written by the LLM agent)
SCORES = "five_forces_scores.json"               # scores + rationales (written by the LLM agent)
REPORT_CACHE = "cache/pages.jsonl"               # paywalled report page text (git-ignored; present only on the build machine)
PUBLIC_DIR = "public_sources"                    # committed public text (+ index.json)
PUBLIC_FULL = "cache/public_full"                # full text of commercial pages (git-ignored)
FF_LOG = "five_forces_verification_log.json"
OUT_JSON, OUT_MD = "five_forces.json", "five_forces.md"

FORCES = OrderedDict([
    ("rivalry", "Rivalry among existing competitors"),
    ("buyer_power", "Bargaining power of buyers"),
    ("supplier_power", "Bargaining power of suppliers"),
    ("new_entrants", "Threat of new entrants"),
    ("substitutes", "Threat of substitutes"),
])
MIN_FACTS, MIN_SUBDIMS = 3, 2
REPORTS_AVAILABLE = os.path.exists(REPORT_CACHE)
print("Report page cache present:", REPORTS_AVAILABLE,
      "-> report quotes will be", "re-verified LIVE" if REPORTS_AVAILABLE else "REPLAYED from the committed log (PDFs not in this clone)")
