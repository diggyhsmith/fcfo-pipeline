# %% [markdown]
# # Industry Intelligence Pipeline: fractional CFO services
#
# **What this is.** A pipeline that takes a company description, picks a NAICS code from the official Census manual,
# ingests industry-report PDFs (IBISWorld, First Research) that were downloaded by hand, extracts seven structured
# "signals" with a page-level citation on every one, **verifies every quote against the PDF page in code**, reconciles
# the documents, lists the gaps, and writes a brief.
#
# **Who did what (read this first).**
# * The *extraction* step (reading pages, writing `extractions/*.json`) was performed by **Claude Code, an LLM agent**, during the build
#   session. No paid API was called, and no API key was used.
# * Everything else in this notebook is ordinary Python that runs when you execute it: PDF text extraction, the NAICS fetch,
#   quote verification, cross-document reconciliation, gap analysis and brief generation.
# * The verifier checks that a quote **exists on the cited page**. It does not check that the LLM interpreted the quote correctly.
#
# **Licensing.** The reports are paywalled. They are not in the repository. Only short quotes (<= 25 words) appear in committed files.
# Without the PDFs, Stages 0 and 3 cannot be re-executed. The notebook then replays the saved verification log and says so.
#
# **Design rule used throughout:** each stage has a markdown cell above it stating the choice, the rejected alternative, and why.

# %%
# ---- CONFIG: edit this cell to run a different industry -------------------------------------------------------------
import os, sys, re, json, glob, time, hashlib, random, datetime, logging, warnings, textwrap, collections, unicodedata
from pathlib import Path

if os.environ.get("ANTHROPIC_API_KEY"):
    raise RuntimeError("ANTHROPIC_API_KEY is set. This project is zero-cost by design: unset it and re-run.")

logging.getLogger("pdfminer").setLevel(logging.ERROR)   # pdfplumber is chatty on unusual PDF colour spaces
warnings.filterwarnings("ignore")

COMPANY      = "Working name TBD, fractional CFO services"
DESCRIPTION  = ("Fractional (part-time, outsourced) CFO services for US small and mid-sized businesses with roughly "
                "$2M-$20M revenue. The company does not exist yet (founders are MAcc students), so the brief describes "
                "the industry we would enter.")
REPORTS_DIR  = "reports"            # paywalled PDFs, never committed
CACHE_DIR    = "cache"              # page text cache, never committed
EXTRACT_DIR  = "extractions"        # one JSON per document (committed; quotes are <= 25 words)
EXTRACTOR    = "claude_code_files"  # or "gemini" (implemented, untested; see Stage 2)
GEMINI_MODEL = None                 # None = pick from the live model list at run time (see Stage 2 backend)

# Candidate NAICS codes for the choice in Stage 1 (Census 2022 manual).
NAICS_CANDIDATES = ["541611", "541219", "541211", "541618", "541990", "561110"]
NAICS_MANUAL_URL = "https://www.census.gov/naics/reference_files_tools/2022_NAICS_Manual.pdf"
NAICS_LANDING    = "https://www.census.gov/naics/"

# The NAICS choice is a judgement, so it lives here where you can change it. Stage 1 re-validates it: every phrase in JUSTIFICATION_QUOTES
# must appear in the fetched manual entry of that code, or the notebook stops.
CHOSEN_CODE, NEIGHBOR_CODE = "541611", "541219"
JUSTIFICATION_QUOTES = {
    "541611": ["financial planning and budgeting", "Financial management (except investment advice) consulting services",
               "providing operating advice and assistance to businesses"],
    "541219": ["providing accounting services (except tax return preparation services only or payroll services only)",
               "Accountant (except CPA) offices, bookkeeper offices, and billing offices are included"],
}
NAICS_JUSTIFICATION = (
    "We chose 541611 because the manual defines it as \"providing operating advice and assistance to businesses\" on issues such as "
    "\"financial planning and budgeting\" and lists \"Financial management (except investment advice) consulting services\" as an example, "
    "which describes advice to a client's management; the closest neighbor, 541219, is instead defined as \"providing accounting services "
    "(except tax return preparation services only or payroll services only)\" for establishments outside CPA offices, and its own text says "
    "\"Accountant (except CPA) offices, bookkeeper offices, and billing offices are included\", so it is organized around producing the books rather than advising management on them."
)
print("Company:", COMPANY)
print("Reports dir:", REPORTS_DIR, "| PDFs found:", len(glob.glob(f"{REPORTS_DIR}/*.pdf")))
