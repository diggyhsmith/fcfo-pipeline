# Competitor Mapping Tool: strategic groups as a clustering problem

**Open the tool (no login; outputs saved in the file):**
* GitHub: https://github.com/diggyhsmith/fcfo-pipeline/blob/main/competitor-map/competitor_map.ipynb
* nbviewer: https://nbviewer.org/github/diggyhsmith/fcfo-pipeline/blob/main/competitor-map/competitor_map.ipynb

Industry: bookkeeping, tax and advisory services for US small businesses. The notebook takes a list of competitors (`competitors.json`),
reads each firm's own public pages, records seven attributes per firm with the **source URL and retrieval date of every value**, and lets
the data choose the map axes (PCA) and the groups (k-means, checked with Ward hierarchical clustering, different seeds and drop-one-attribute runs).
A hypothetical point for Fine Line Financials is projected onto the finished map at $125, $200 and $350 a month. It is **not** used in the fit.

## Result of this run (pages retrieved 2026-11-10)

* 26 firms in the input list; **20 fitted**. Four could not be read with a plain request (Xendoo, Block Advisors, Padgett, Straight Talk CPAs), and two from the earlier NPS list are defunct (parked domains).
* PCA: PC1 39% (storefront network, per-return pricing vs. online with a posted monthly price), PC2 24% (bookkeeping only and cheap vs. files tax returns, pricier, more services).
* k = 3 (silhouette 0.38; Ward gives the identical partition): online bookkeeping + tax filing (15), bookkeeping only (2), office-network tax preparers (3).
* Surprise: the four firms with salon/spa pages do not form their own group; dropping the niche attribute moves no firm.
* Fine Line Financials (hypothetical) lands nearest the bookkeeping-only group at every price, in open space; not filing tax returns places it more than its price does.

## Who did what

| Step | Done by |
|---|---|
| Choosing the firms; reading their pages and writing `attributes.json` (values, URLs, short verbatim quotes); choosing the checklist, encodings and rules | Claude Code (an LLM agent) during the build session, as stated judgment |
| Fetching and caching every page, re-checking every quote against the cached page, counting services, encoding, imputing, PCA, k-means, Ward, stability runs, projection, charts | Plain, deterministic Python in the notebook |

## Rules

* **Fetching** (`fetch.py`): plain `python-requests` user agent, never changed; `robots.txt` is read first; a page that answers 403, times out or
  is parked is recorded as "not available" and is **not** retried with another client. Emails and phone numbers are redacted before caching.
* **Evidence**: a value is used only if read from a cached page; quotes are re-checked in code and a value whose quote is not found counts as missing.
* **Missing values**: an attribute missing for more than half the firms is dropped from the fit (reviews: 70% missing); a firm missing more than
  two remaining attributes is not fitted; other gaps are imputed (median / most common) and flagged; firms with no posted monthly price also get a
  `price_published = 0` flag.

## Run it

```bash
pip install -r requirements.txt
python dev/build_notebook.py                                              # cells live in dev/cells.py
jupyter nbconvert --to notebook --execute --inplace competitor_map.ipynb  # offline from cache/
python build_pdf.py                                                       # competitor_map_submission.pdf (local only)
```

A fresh clone runs offline. `cache/pages/*.json` keeps each page's URL, HTTP status, robots verdict, retrieval date and **only the text lines the
analysis uses** (quote lines, checklist and beauty-term lines, current-year lines). Whole-page text (`cache/full/`) stays local, so the repo does
not republish commercial pages. The offline run reproduces every number. Delete a page's file in `cache/pages/` to re-fetch it live.

## Layout

```
competitor_map.ipynb          the tool (executed; outputs saved)
competitors.json              input list: firms, pages to read, hand-drawn group (comparison only)
attributes.json               hand-read values with URL + quote
fetch.py                      polite cached fetcher
results.json                  numbers used by the PDF
competitor_map.png, k_selection.png, dendrogram.png
cache/                        manifest, robots.txt copies, reduced page text
build_pdf.py, reflection_competitor_map.md
dev/cells.py, dev/build_notebook.py
```

Limits: small n (20); attributes chosen by hand; sources are dated, public and partly marketing (review figures on a firm's own site are
self-selected); several values missing; clustering depends on scaling and encoding; the Fine Line Financials points are assumptions.
