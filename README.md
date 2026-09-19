# Industry Intelligence Pipeline: fractional CFO services

A class project (BYU MAcc strategy course). It takes a company description, picks an industry code from the official
2022 NAICS Manual, ingests industry-report PDFs that were downloaded by hand, extracts seven structured signals with a
**page-level citation on every one**, **verifies every quote against the PDF page in code**, reconciles the reports, lists what
could not be found, and writes a brief.

**Open the working tool (no login needed; outputs are saved in the file):**
* GitHub: https://github.com/diggyhsmith/fcfo-pipeline/blob/main/pipeline.ipynb
* nbviewer: https://nbviewer.org/github/diggyhsmith/fcfo-pipeline/blob/main/pipeline.ipynb

## Who did what (read this first)

| Step | Done by |
|---|---|
| Reading the report pages and writing `extractions/*.json` (the seven signals, summaries, quotes, confidence) | **Claude Code, an LLM agent**, during the build session. Not a paid API call; no API key was used. |
| PDF text extraction, NAICS manual fetch, quote and number verification, reconciliation, gaps, brief | Plain Python in the notebook, executed top to bottom |
| Checking that the LLM understood the sources correctly | **Not done by code.** A human has to read the spot-check list in `brief.md`. The line "Hand-checked by me: [ ] of [ ] citations" is left blank for the student. |

## What it does (stages)

0. **Ingest**: per-page text (`pdfplumber`), printed page labels, report metadata; near-empty pages are flagged.
1. **NAICS selection**: fetches the 2022 NAICS Manual from census.gov, compares candidate codes, and asserts that every phrase quoted in the justification exists in the fetched entry. Chosen: **541611**, against the neighbor 541219.
2. **Extraction**: schema in `extraction_schema.json`; default extractor `claude_code_files` loads `extractions/*.json`. Optional `gemini` backend (see below).
3. **Verification** (`verify.py`, also shown in the notebook): every quote is normalised and string-matched on its cited page, then adjacent pages, then a guarded fuzzy match; every number in a value must appear in a verified quote; quotes over 25 words fail. Log: `verification_log.json`.
4. **Reconciliation**: primary value by a stated rule; conflicts kept side by side, never averaged.
5. **Gaps**: generated from the run, each naming a type of source that would fill it (suggested sources were not consulted).
6. **Brief**: `brief.json`, `brief.md`. `run_pipeline(company, description, reports_dir, extractor)` chains everything.

## Run it

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace pipeline.ipynb     # or open it in Jupyter and Run All
python verify.py --reset          # standalone verification round (needs the PDFs and the cache)
python build_pdf.py --repo https://github.com/USER/REPO   # builds submission.pdf from brief.json + reflection.md
```

To run another industry: edit the config cell (company, description, NAICS candidates and choice), put the PDFs in `reports/`,
and either write `extractions/<doc_id>.json` to the schema or use the Gemini backend. The NAICS choice and the extraction files are the two steps that are industry-specific.

## What is and is not reproducible without the paywalled reports

* **Reproducible from a fresh clone:** Stage 1 (live fetch from census.gov), Stage 2 loading, Stage 4, Stage 5, brief generation, `build_pdf.py`. The notebook
  detects that `reports/` is empty and **replays the committed `verification_log.json`, saying so in its output** (it does not pretend to re-check quotes).
* **Not reproducible without the PDFs:** Stage 0 (ingest) and live Stage 3 verification, because they read the PDFs. The reports are IBISWorld and First Research (Dun & Bradstreet)
  documents accessed through a university library subscription; find them by title (see the source list in `brief.md`).

## Licence and data note

The reports are paywalled and licensed for reading, not redistribution. `reports/`, `cache/` (page text) and `.env` are git-ignored, and nothing in this repository contains full report text.
Only short verbatim quotes (25 words or fewer, enforced in code) appear, as citations. The NAICS definitions in `naics/` come from the public U.S. Census Bureau manual. Code is provided for coursework use.

## Gemini backend: implemented, untested

`extractor="gemini"` uses Google's Gemini API with a free AI Studio key from `GEMINI_API_KEY` (no billing), one call per document (chunked if very long), the same schema,
rate-limit-aware spacing, and a model chosen from the live model list at run time. **It has never been run against the live API**, because no key was available; only its
model-selection, retry, chunk-merge and parsing logic was exercised against a mock inside the notebook. Anything it produced would still pass through the same code-side verifier.

## Limits, stated plainly

* Fractional CFO has no NAICS code, so every number describes a **proxy** industry (management consulting or accounting). Only one of the three reports sits on the chosen code.
* No report gives market share for the fractional niche.
* Verification proves a quote exists on a page, not that its interpretation is right. In this run all 79 quotes verified on the first round, which shows they were copied faithfully, not that the analysis is correct.
* LLM extraction is non-deterministic; re-extracting may change quotes or the "biggest trend/threat" choice.
* The reports are dated (First Research data published July 2025; IBISWorld May and August 2026).
* The third report is a First Research profile (D&B Hoovers), not a MarketResearch.com report, and its industry-code section printed empty.

## Layout

```
pipeline.ipynb            the tool (executed; outputs saved)
verify.py                 Stage 3 as a standalone script (also embedded in the notebook)
build_pdf.py              builds submission.pdf and checks its contents by code
extraction_schema.json    schema for extractions
extractions/              the LLM agent's per-document signal files (quotes <= 25 words)
verification_log.json     result for every quote (no page text)
brief.json / brief.md     the final brief
naics/                    fetched NAICS 2022 candidate definitions with URL and access date
sources.json              report metadata (no report text)
reflection.md             reflection draft (to be rewritten by the student)
notes_for_reflection.md   notes kept during the build
dev/                      cell sources and the notebook builder
```
