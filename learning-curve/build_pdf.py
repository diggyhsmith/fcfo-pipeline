#!/usr/bin/env python3
"""Build the ONE-PDF submission for the Learning-Curve Calculator from lc_results.json + reflection_learning_curve.md, then check it by code.

Run from this folder after executing the notebook:
    python build_pdf.py            -> learning_curve_submission.pdf
Repo URL comes from ../submission_config.json {"repo_url": ...} or --repo URL.

Header (title, author, date), then exactly three sections, in this order:
    1. Tool link (learning-curve/learning_curve.ipynb on GitHub + nbviewer backup), clickable, at the top of page one
    2. Output: learning rate, b, R², n (raw and inflation-adjusted), log-log plot, every data point with filing + accession links,
       units source quotes, direct units vs proxy, sensitivity checks, interpretation, what could not be verified
    3. Reflection (three headings, from reflection_learning_curve.md)

Separate from the earlier deliverables' builders; only the shared styling helpers from ../build_pdf.py are reused.
"""
import json, re, sys, argparse, datetime as dt
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from build_pdf import clean, md_inline, link, styles, grid, GREY   # shared styling from the first deliverable

OUT = HERE / "learning_curve_submission.pdf"
REFLECTION = HERE / "reflection_learning_curve.md"
TITLE = "Learning-Curve Calculator: H&R Block (HRB)"
AUTHOR = "Diggy Smith"
PLACEHOLDER = "TO BE WRITTEN BY THE STUDENT"

def urls_for(repo):
    repo = re.sub(r"\.git$", "", repo.rstrip("/"))
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        sys.exit(f"repo_url must look like https://github.com/USER/REPO, got {repo!r}")
    u, n = m.groups()
    return {"repo": repo, "folder": f"{repo}/tree/main/learning-curve",
            "notebook": f"{repo}/blob/main/learning-curve/learning_curve.ipynb",
            "nbviewer": f"https://nbviewer.org/github/{u}/{n}/blob/main/learning-curve/learning_curve.ipynb"}

def reflection_paragraphs(text):
    return [p.strip() for p in re.sub(r"<!--.*?-->", "", text, flags=re.S).strip().split("\n\n") if p.strip()]

pct = lambda v: f"{v:+.1%}"
a = lambda url, text: f'<a href="{clean(url)}" color="#1a4f8b"><u>{clean(text)}</u></a>'

def build(d, reflection, urls, path=OUT, today=None):
    S = styles()
    W = letter[0] - 1.5 * inch
    story = []
    P = lambda t, s="body": story.append(Paragraph(t, S[s]))
    C = lambda t, s="cell": Paragraph(t, S[s])
    rows, fit = d["rows"], d["fit"]
    fn, fr = fit["nominal"], fit["real"]

    # ---------------------------------------------------------------- header
    P(f"<font size=16><b>{clean(TITLE)}</b></font>", "body")
    P(f"{AUTHOR} &nbsp;&middot;&nbsp; {today}", "body")
    story.append(Spacer(1, 2))

    # ---------------------------------------------------------------- 1
    P("1. Tool link", "h1")
    P(f"<b>Notebook (GitHub, no login, outputs saved):</b> {link(urls['notebook'])}")
    P(f"<b>Backup viewer (nbviewer):</b> {link(urls['nbviewer'])}")
    P(f"Folder with the cached EDGAR, 10-K text and FRED data, <font face='Courier'>units_HRB.json</font> (every unit figure with its quote) "
      f"and this builder: {link(urls['folder'])}", "small")

    # ---------------------------------------------------------------- 2
    P("2. Output", "h1")
    P(f"<b>Company:</b> {clean(d['company'])} (CIK {d['cik']}), {d['window']}, n = {fn['n']} fiscal years. "
      f"<b>Cost:</b> the 10-K line &ldquo;Cost(s) of revenues&rdquo; (XBRL <font face='Courier'>CostOfRevenue</font> to FY2018, "
      f"<font face='Courier'>CostOfGoodsAndServicesSold</font> from FY2019), HRB's COGS-type subtotal, so no fallback to total operating expenses "
      f"was needed; latest restated value per year. <b>Units:</b> {clean(d['units_meta']['unit_name'])}, read from each 10-K. "
      f"<b>Cumulative units are counted from FY{rows[0]['fy']}, the first year of this window, not from HRB's founding (1955)</b>, so N "
      f"leaves out several hundred million earlier returns.", "small")

    P("2a. Learning rate, b, R² and n", "h2")
    hdr = [C("<b>Fit</b>"), C("<b>Learning rate = 1 &minus; 2<super>&minus;b</super></b>"), C("<b>95% CI (rate)</b>"),
           C("<b>b</b>"), C("<b>SE(b)</b>"), C("<b>R²</b>"), C("<b>n</b>"), C("<b>Cost(1)</b>")]
    tab = [hdr]
    for name, f in (("Raw (nominal $)", fn), (f"Inflation-adjusted (FY{rows[-1]['fy']} $, CPI-U)", fr)):
        tab.append([C(f"<b>{name}</b>"), C(f"<b>{pct(f['lr'])}</b>"), C(f"{pct(f['lr_lo'])} to {pct(f['lr_hi'])}"),
                    C(f"<b>{f['b']:+.4f}</b>"), C(f"{f['se_b']:.4f}"), C(f"<b>{f['r2']:.3f}</b>"), C(str(f["n"])), C(f"${f['cost1']:.2f}")])
    story.append(grid(tab, [W * x for x in (0.24, 0.17, 0.15, 0.09, 0.08, 0.08, 0.05, 0.14)]))
    P(f"Fit: ln(cost per return) = ln Cost(1) &minus; b&middot;ln N by least squares, N = cumulative returns in millions (Cost(1) is an "
      f"extrapolation to the first million and means little). <b>A negative learning rate means unit cost rose with volume:</b> nominal cost "
      f"per return rose {abs(fn['lr']):.1%} per doubling of cumulative returns; in real terms the slope is indistinguishable from zero.", "small")

    story.append(KeepTogether([Paragraph("2b. Log-log plot with fitted line (both axes log scale): raw vs inflation-adjusted", S["h2"]),
                               Image(str(HERE / "lc_loglog.png"), width=W, height=W * 860 / 2100)]))

    P("2c. Every data point, with filing and accession links", "h2")
    tab = [[C("<b>FY</b>"), C("<b>Period</b>"), C("<b>Cost of rev. $M</b>"), C("<b>Returns (000)</b>"), C("<b>Cum. (000)</b>"),
            C("<b>$/return</b>"), C("<b>Real $/ret.</b>"), C("<b>Cost: 10-K accession</b>"), C("<b>Units: 10-K accession, page</b>")]]
    for r in rows:
        tab.append([C(str(r["fy"])), C(f"{r['start'][:7]} to {r['end'][:7]}"), C(f"{r['cost']/1e6:,.1f}" + ("*" if r["cost_restated"] else "")),
                    C(f"{r['units_k']:,}"), C(f"{r['cum_units_k']:,}"), C(f"{r['unit_cost']:.2f}"), C(f"{r['real_unit_cost']:.2f}"),
                    C(a(r["cost_index_url"], r["cost_accession"])), C(a(r["units_doc_url"], r["units_accession"]) + f", p.{r['page']}")])
    story.append(grid(tab, [W * x for x in (0.06, 0.14, 0.09, 0.09, 0.08, 0.07, 0.08, 0.19, 0.20)]))
    P("Cost accession links open the EDGAR filing index of the latest 10-K reporting that year's cost (XBRL companyfacts); units links open the 10-K "
      "document the figure was read from, with its printed page. * = cost restated: the FY2015 10-K moved an &ldquo;Interest&rdquo; line out of cost of "
      "revenues (FY2013 first reported $1,604.8M, FY2014 $1,627.7M), which is why the window starts in FY2013 (FY2012 was never restated). "
      f"No annual figure exists for the May&ndash;June 2021 transition period when HRB moved its year end from April 30 to June 30. CPI: "
      f"{clean(d['cpi_source'])}" + (f"; {', '.join(d['cpi_gaps'])} was never published (federal shutdown), so that year averages 11 months." if d.get("cpi_gaps") else "."), "small")

    P("2d. Where each unit figure comes from (quote verified in code against the cached 10-K text)", "h2")
    for r in rows:
        P(f"<b>FY{r['fy']}</b> &mdash; {clean(r['section'])}, p.{r['page']}: &ldquo;{clean(r['quote'])}&rdquo;. <i>{clean(r['note'])}</i>", "cite")
    P(f"<b>Rule:</b> {clean(d['units_meta']['selection_rule'])} All {len(rows)} figures verified; none dropped"
      + (f" (dropped: {d['unverified_dropped']})" if d["unverified_dropped"] else "") + ".", "small")

    P("2e. Direct units vs proxy: what accuracy still costs", "h2")
    for h, t in d["accuracy"]:
        P(f"<b>{clean(h)}</b> {clean(t)}", "small")

    P("2f. Sensitivity checks (one assumption changed at a time)", "h2")
    tab = [[C("<b>Change</b>"), C("<b>Raw: rate / b / R²</b>"), C("<b>Real: rate / b / R²</b>"), C("<b>n</b>")]]
    tab.append([C("Base case (above)"), C(f"{pct(fn['lr'])} / {fn['b']:+.3f} / {fn['r2']:.2f}"), C(f"{pct(fr['lr'])} / {fr['b']:+.3f} / {fr['r2']:.2f}"), C(str(fn["n"]))])
    for name, s in d["sensitivity"].items():
        sn, sr = s["nominal"], s["real"]
        tab.append([C(clean(name)), C(f"{pct(sn['lr'])} / {sn['b']:+.3f} / {sn['r2']:.2f}"), C(f"{pct(sr['lr'])} / {sr['b']:+.3f} / {sr['r2']:.2f}"), C(str(sn["n"]))])
    story.append(grid(tab, [W * x for x in (0.52, 0.2, 0.2, 0.08)]))
    P("None of the data choices changes the conclusion: the raw curve slopes up (about &minus;10% to &minus;12% learning rate) and the real one is flat.", "small")

    P("2g. Interpretation", "h2")
    P(" ".join(clean(s) for s in d["interpretation"]))

    P("2h. What could not be verified", "h2")
    P("(1) The definition behind the FY2023&ndash;FY2026 totals: HRB stopped publishing its return table after FY2022, so those four years rest on a one-line "
      "Item 1 total (0.1 million precision) that matched the table exactly in FY2021 and FY2022 but is not defined in the later filings. "
      "(2) Why FY2016 moved from 23,124 to 23,121 thousand (no footnote found). (3) HRB's cumulative returns before FY2013 (not in any filing used), "
      "so the true position on its experience curve is unknown. (4) How much of cost of revenues belongs to non-tax products: HRB does not split it.", "small")

    # ---------------------------------------------------------------- 3
    story.append(Spacer(1, 6))
    P("3. Reflection", "h1")
    for para in reflection_paragraphs(reflection):
        P(md_inline(para))

    def footer(canvas, doc_):
        canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GREY)
        canvas.drawString(0.75 * inch, 0.45 * inch, f"{TITLE} | {AUTHOR}")
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc_.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.6 * inch,
                            bottomMargin=0.7 * inch, title=TITLE, author=AUTHOR)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

def verify_pdf(path, d, reflection, urls, today):
    from pypdf import PdfReader
    r = PdfReader(str(path))
    FOOT = re.compile(re.escape(f"{TITLE} | {AUTHOR}") + r"\s*Page \d+\s*")
    text = FOOT.sub("", "\n".join((p.extract_text() or "") for p in r.pages))
    T = re.sub(r"\s+", "", text).lower()
    sq = lambda s: re.sub(r"\s+", "", s).lower()
    checks = []
    need = lambda label, cond: checks.append((label, bool(cond)))
    p1 = re.sub(r"\s+", "", FOOT.sub("", r.pages[0].extract_text() or "")).lower()
    need("page-one header: title, author, date", p1.startswith(sq(TITLE)) and sq(AUTHOR) in p1[:120] and sq(today) in p1[:160])
    heads = ["1. Tool link", "2. Output", "3. Reflection"]
    pos = [T.find(sq(h)) for h in heads]
    need("exactly the three sections, in order", all(p >= 0 for p in pos) and pos == sorted(pos))
    links = {str(x.get_object()["/A"]["/URI"]) for x in (r.pages[0].get("/Annots") or []) if x.get_object().get("/A")}
    need("notebook + nbviewer links clickable on page one", urls["notebook"] in links and urls["nbviewer"] in links)
    for k in ("nominal", "real"):
        f = d["fit"][k]
        need(f"{k}: learning rate, b, R², n printed", all(sq(v) in T for v in (pct(f["lr"]), f"{f['b']:+.4f}", f"{f['r2']:.3f}")))
    all_links = {str(x.get_object()["/A"]["/URI"]) for p in r.pages for x in (p.get("/Annots") or []) if x.get_object().get("/A")}
    need("every data row has accession links", all(row["cost_index_url"] in all_links and row["units_doc_url"] in all_links for row in d["rows"]))
    need("every unit quote printed", all(sq(row["quote"]) in T for row in d["rows"]))
    need("cumulative-from-window limitation stated", "countedfromfy2013" in T)
    need("direct units vs proxy section", "directunits,notaproxy" in T)
    need("interpretation printed", all(sq(clean(s))[:60].replace("&amp;", "&") in T for s in d["interpretation"]))
    need("plot embedded", sum(len(p.images) for p in r.pages) >= 1)
    need("three reflection headings", all(sq(h) in T for h in ("What was hardest to build?", "What would you not trust this tool to decide",
                                                               "What did it show you that the framework could not?")))
    return checks, len(r.pages)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo"); ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    repo = args.repo or json.loads((HERE.parent / "submission_config.json").read_text())["repo_url"]
    urls = urls_for(repo)
    d = json.loads((HERE / "lc_results.json").read_text())
    reflection = REFLECTION.read_text()
    today = dt.date.today().strftime("%B %-d, %Y")
    build(d, reflection, urls, args.out, today)
    checks, pages = verify_pdf(args.out, d, reflection, urls, today)
    failed = [c for c in checks if not c[1]]
    print(f"Built {args.out}: {pages} pages; {len(checks)} content checks, {len(checks) - len(failed)} passed.")
    for label, ok in checks:
        if not ok: print("  FAILED:", label)
    if PLACEHOLDER in reflection:
        print(f"  REFLECTION NOT WRITTEN YET: replace the placeholders in {REFLECTION.name} (keep the three bold headings), then re-run.")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
