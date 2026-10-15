# Learning-Curve Calculator (H&R Block, HRB)

Fourth deliverable in this repo. Fits **Cost(N) = Cost(1) · N^-b** to H&R Block's cost per tax return against cumulative returns,
FY2013-FY2026, from free public data only (no login, no paid API, no key).

**Open the tool (outputs saved):** [learning_curve.ipynb](learning_curve.ipynb)
([nbviewer](https://nbviewer.org/github/diggyhsmith/fcfo-pipeline/blob/main/learning-curve/learning_curve.ipynb))

| Result (n = 14 fiscal years) | Learning rate (1 − 2^−b) | b | R² |
|---|---|---|---|
| Raw, nominal $ | −11.4% (unit cost *rises* per doubling) | −0.155 | 0.79 |
| Inflation-adjusted (CPI-U) | −1.3% (95% CI −4.8% to +2.1%) | −0.019 | 0.05 |

No learning curve is visible: nominal cost per return rose from $61.59 to $98.49 while annual volume stayed flat; in real terms it is roughly flat.

## Data

| Input | Source | How it is checked |
|---|---|---|
| Cost | 10-K "Cost(s) of revenues" via SEC EDGAR XBRL `companyfacts` (`CostOfRevenue` to FY2018, `CostOfGoodsAndServicesSold` from FY2019); latest restated value per year | Accession of the latest 10-K reporting each year, from the API |
| Units | Tax returns prepared worldwide (assisted + DIY), read from each 10-K's text; listed with quotes in `units_HRB.json` | The notebook finds each quote verbatim in the cached filing text, checks the number and column, and computes the printed page |
| Inflation | FRED `CPIAUCSL` public CSV | fiscal-year averages |

Cumulative units are counted from FY2013 (the first year of the window), not from HRB's founding. The window starts in FY2013 because the FY2015 10-K
moved an interest line out of cost of revenues and only restated FY2013-FY2014. The notebook explains every restatement, the 2021 fiscal-year change, and the remaining limits.

| Step | Done by |
|---|---|
| Reading the 10-Ks and writing `units_HRB.json` (figures, quotes, sections, notes) | Claude Code (LLM agent) during the build session |
| Downloads, caching, quote/number/page verification, restatement history, CPI, fit, plot, sensitivity checks, interpretation text | Python in the notebook |

## Run

```bash
pip install -r requirements.txt
export SEC_USER_AGENT="Your Name your-contact@example.com"   # only needed if cache/ is missing a file; never written to disk
python dev/build_notebook.py                                  # rebuild the notebook from dev/cells.py (optional)
jupyter nbconvert --to notebook --execute --inplace learning_curve.ipynb
python build_pdf.py                                           # learning_curve_submission.pdf from lc_results.json + reflection_learning_curve.md
```

Change `TICKER` at the top of the notebook to pull another company's cost series; the units side needs a `units_<TICKER>.json` because units are not in XBRL.

```
learning_curve.ipynb            the tool (executed; outputs saved)
units_HRB.json                  unit figures with quotes, sections, restatement notes
cache/                          EDGAR companyfacts + submissions, plain text of each 10-K used, FRED CPI CSV
lc_results.json, lc_loglog.png  outputs read by build_pdf.py
build_pdf.py                    builds and checks learning_curve_submission.pdf
reflection_learning_curve.md    reflection (written by the student)
dev/cells.py, dev/build_notebook.py   notebook source and builder
```
