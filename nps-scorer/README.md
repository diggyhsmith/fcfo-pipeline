# Customer Loyalty Scorer (NPS): esthetician bookkeeping competitors

Third deliverable in this repo (BYU MAcc strategy course, "starting a company" track). It turns real, public, star-rated
reviews into a review-derived Net Promoter Score for four named competitors.

**Open the tool (no login; outputs saved in the file):**
* GitHub: https://github.com/diggyhsmith/fcfo-pipeline/blob/main/nps-scorer/nps_scorer.ipynb
* nbviewer: https://nbviewer.org/github/diggyhsmith/fcfo-pipeline/blob/main/nps-scorer/nps_scorer.ipynb

**Scope change.** The earlier deliverables (`../pipeline.ipynb`, `../five_forces.ipynb`) framed the project as fractional CFO
services for US SMBs (NAICS 541611). The team has since narrowed it to bookkeeping, tax and loan-readiness for independent
estheticians and spa/suite owners; this scorer works on that narrower niche.

## Result (Google Maps reviews, retrieved 2026-10-08)

| Company | Source | n | NPS (5* P / 4* Pa / 1-3* D) | NPS if 4* = promoter | 95% interval |
|---|---|---|---|---|---|
| Kopsa Otte CPAs and Advisors | Google Maps | 2 | +100 | +100 | -22 to +96 |
| Xendoo | Google Maps | 177 | +86 | +86 | +77 to +92 |
| Elite Business Solutions | Google Maps (listing permanently closed) | 4 | +100 | +100 | +8 to +98 |
| Jasmine Thomas & Associates | none found (domain parked) | 0 | n/a | n/a | n/a |

Trustpilot had zero reviews for all four, so every score uses Google Maps. Only Xendoo clears 50 reviews.

## Files

| File | What it is |
|---|---|
| `nps_scorer.ipynb` | The tool: source decisions, bucketing, sensitivity, intervals, bias, excerpts, charts, track analysis |
| `collect_reviews.py` | Review collector (Playwright headless browser). Checks Trustpilot first, then Google Maps; logs Yelp as blocked |
| `cache/*.json` | Every review used: Google review id, stars, relative date, text, source URL; plus the attempt log and Google's star histogram. Reviewer names are not stored. |
| `nps_data.json` | Everything the PDF needs, written by the notebook |
| `nps_chart.png`, `nps_vs_volume.png` | Charts |
| `build_nps_pdf.py` + `reflection_nps.md` | Builds `nps_submission.pdf` (not committed). Edit the reflection, then `python build_nps_pdf.py` |

## Re-running

```bash
~/.venvs/fcfo/bin/pip install -r requirements.txt && ~/.venvs/fcfo/bin/playwright install chromium
~/.venvs/fcfo/bin/python collect_reviews.py        # optional: re-collect (merges with the cache by review id)
~/.venvs/fcfo/bin/jupyter nbconvert --to notebook --execute --inplace nps_scorer.ipynb
~/.venvs/fcfo/bin/python build_nps_pdf.py
```

Google's logged-out view shows different subsets of reviews on different loads, so the collector merges reviews across
runs by Google's review id and the notebook stops unless the itemized star counts equal Google's own histogram.
