# CAGE Distance Framework Tool (US to Canada)

Fifth deliverable in this repo. Scores Pankaj Ghemawat's four CAGE distances (Cultural, Administrative, Geographic, Economic) between any two
countries **for a stated industry**, from free public data only (no login, no paid API, no key). The default run is a US firm selling
bookkeeping, tax and loan-readiness services to estheticians and spa suites in Canada.

**Open the tool (outputs saved):** [cage_distance.ipynb](cage_distance.ipynb)
([nbviewer](https://nbviewer.org/github/diggyhsmith/fcfo-pipeline/blob/main/cage-distance/cage_distance.ipynb))

| US to Canada | Cultural | Administrative | Geographic | Economic | Total (industry weights) |
|---|---|---|---|---|---|
| Score (0-100, higher = more distance) | 10.3 | 35.6 | 1.5 | 26.3 | **23.5, low (borderline)** |
| Industry weight | 0.25 | 0.40 | 0.10 | 0.25 | |

Single largest risk: the **sales-tax regime (GST/HST/PST)**, including the firm's own possible obligation to register for GST/HST as a non-resident seller.
The rating flips to moderate once Administrative carries about 0.45-0.47 of the weight; no weighting can reach "high". Contrast pairs with the same rules:
US to UK 28.6 (moderate), US to Japan 60.2 (high).

## Evidence

| Dimension | Indicators | Source |
|---|---|---|
| Cultural | Kogut-Singh index on Hofstede's six dimensions; common official language; religion-mix overlap | geerthofstede.com data matrix (2015); CEPII GeoDist; CIA World Factbook (retired in 2026; last snapshot via the factbook.json mirror) |
| Administrative | Industry rules (tax filing, sales tax, payroll, who may prepare and represent, privacy, Quebec language, loan programs); WGI governance gap; trade agreement; OFAC programs | `cage_facts.json` (official IRS, CRA, OPC, CAI, SBA, ISED, USTR pages; every quote re-checked in the notebook); World Bank WGI API; ofac.treasury.gov |
| Geographic | Great-circle distance between capitals (computed), shared border, time-zone gap, internet users, LPI | CEPII; IANA tz database; World Bank API |
| Economic | GDP per capita PPP, GNI per capita (Atlas), price level ratio (computed from PPP factor and exchange rate) | World Bank API |

A source that cannot be fetched, or a quote that is not found on its page, is printed as **not verified** and left out of the score. In this run that was:
the Ontario Public Accounting Act (e-Laws serves a JavaScript shell to scripts) and Quebec's Charter of the French language (Légis Québec returns HTTP 403 to scripts).
The cache holds the plain text of each official page used and the raw data files.

| Step | Done by |
|---|---|
| Indicator choice, scoring rules, weights and their justification, the fact table `cage_facts.json` (claims, severities, quotes) | Claude Code (LLM agent) during the build session, as stated judgment |
| Fetching, caching, quote checks, every score, total, rating, recommendation, sensitivity, charts | Python in the notebook (deterministic) |

## Run

```bash
pip install -r requirements.txt
python dev/build_notebook.py                                   # rebuild the notebook from dev/cells.py (optional)
jupyter nbconvert --to notebook --execute --inplace cage_distance.ipynb
python build_pdf.py                                            # cage_distance_submission.pdf from cage_results.json + reflection_cage.md
```

Change `HOME`, `TARGET` (ISO alpha-2; "UK" is accepted) and `INDUSTRY` at the top. Country-level indicators work for any pair; the industry facts
and trade agreement come from `cage_facts.json`, so a new pair needs its own entries there (without them the notebook says so and scores Administrative on the rest).
Delete a file in `cache/` to re-fetch it.

```
cage_distance.ipynb              the tool (executed; outputs saved)
cage_facts.json                  curated, cited fact table (trade agreements + industry rules per pair)
cache/                           Hofstede CSV, CEPII files, World Bank JSON, Factbook extract, text of every official page, manifest.json (URL -> retrieval date)
cage_results.json, *.png         outputs read by build_pdf.py
build_pdf.py                     builds and checks cage_distance_submission.pdf
reflection_cage.md               reflection (written by the student)
dev/cells.py, dev/build_notebook.py   notebook source and builder
```
