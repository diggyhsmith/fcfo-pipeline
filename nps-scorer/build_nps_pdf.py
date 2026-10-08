#!/usr/bin/env python3
"""Build the ONE-PDF submission for the Customer Loyalty Scorer from nps_data.json + reflection_nps.md, then check the PDF by code.

Edit reflection_nps.md (250-500 words, keep the three bold labels) and re-run from this folder:
    python build_nps_pdf.py            -> nps_submission.pdf
Repo URL comes from ../submission_config.json {"repo_url": ...} or --repo URL.

Exactly three sections, in this order:
    1. Tool link (nps-scorer/nps_scorer.ipynb on GitHub + nbviewer backup), at the top of page one
    2. Output: scores, bucket boundaries and why, 4-star sensitivity, sample size + selection bias per company, chart,
       three real excerpts, limits (incl. the bimodal-review bias), and the one-page starting-a-company track analysis
    3. Reflection (from reflection_nps.md, written by the student)

Separate from ../build_pdf.py and ../build_five_forces_pdf.py (earlier deliverables); only their styling helpers are reused.
"""
import json, re, sys, argparse
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, Preformatted, Image, PageBreak

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from build_pdf import clean, md_inline, link, styles, grid, GREY   # shared styling from the first deliverable

OUT = HERE / "nps_submission.pdf"
REFLECTION = HERE / "reflection_nps.md"
TITLE = "Customer Loyalty Scorer (NPS): esthetician bookkeeping competitors"
PLACEHOLDER = "TO BE WRITTEN BY THE STUDENT"

def urls_for(repo):
    repo = re.sub(r"\.git$", "", repo.rstrip("/"))
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        sys.exit(f"repo_url must look like https://github.com/USER/REPO, got {repo!r}")
    u, n = m.groups()
    return {"repo": repo, "folder": f"{repo}/tree/main/nps-scorer",
            "notebook": f"{repo}/blob/main/nps-scorer/nps_scorer.ipynb",
            "nbviewer": f"https://nbviewer.org/github/{u}/{n}/blob/main/nps-scorer/nps_scorer.ipynb"}

def notebook_score_table(path=HERE / "nps_scorer.ipynb"):
    """The score table exactly as the executed notebook printed it (real saved output, not retyped)."""
    nb = json.loads(Path(path).read_text())
    for c in nb["cells"]:
        for o in c.get("outputs", []) if c["cell_type"] == "code" else []:
            t = "".join(o.get("text", ""))
            if t.startswith("Company") and "check vs Google histogram" in t:
                return t.rstrip()
    return ""

def reflection_paragraphs(text):
    return [p.strip() for p in re.sub(r"<!--.*?-->", "", text, flags=re.S).strip().split("\n\n") if p.strip()]

f = lambda v: "n/a" if v is None else f"{v:+d}"
ci = lambda v: "n/a" if not v else f"{v[0]:+d} to {v[1]:+d}"
pct = lambda v: "-" if v is None else f"{v:.1f}%"

def build(d, reflection, urls, table_excerpt, path=OUT):
    S = styles()
    W = letter[0] - 1.5 * inch
    story = []
    P = lambda t, s="body": story.append(Paragraph(t, S[s]))
    C = lambda t, s="cell": Paragraph(t, S[s])
    comps = d["companies"]

    # ---------------------------------------------------------------- 1
    P("1. Tool link", "h1")
    P(f"<b>Notebook (GitHub, no login, outputs saved):</b> {link(urls['notebook'])}")
    P(f"<b>Backup viewer (nbviewer):</b> {link(urls['nbviewer'])}")
    P(f"Folder with the review cache (every review used, with source URL, stars, date and text), the collector script and "
      f"<font face='Courier'>nps_data.json</font>: {link(urls['folder'])}", "small")

    # ---------------------------------------------------------------- 2
    P("2. Output", "h1")
    m = d["meta"]
    P(f"<b>Track:</b> {clean(m['track'])}. <b>Segment:</b> {clean(m['segment'])}. Four named competitors are scored; the "
      f"student's own company is pre-launch. Reviews retrieved {clean(', '.join(m['retrieved']))}.", "small")
    P(f"<b>Scope change since the last two deliverables:</b> {clean(m['pivot_note'])}", "small")

    P("2a. NPS by company", "h2")
    rows = [[C("<b>Company</b>"), C("<b>Source used</b>"), C("<b>n</b>"), C("<b>5* / 4* / 3* / 2* / 1*</b>"),
             C("<b>% Prom.</b>"), C("<b>% Detr.</b>"), C("<b>NPS</b>"), C("<b>95% interval</b>"), C("<b>Confidence</b>")]]
    for c in comps:
        p, st = c["primary"], c["stars"]
        rows.append([C(clean(c["company"])), C(clean(c["source_used"] or "none found")), C(str(p["n"])),
                     C(" / ".join(str(st[k]) for k in "54321")), C(pct(p["pct_promoters"])), C(pct(p["pct_detractors"])),
                     C(f"<b>{f(p['nps'])}</b>"), C(ci(c["ci95"])), C(clean(c["confidence"]))])
    story.append(grid(rows, [W * x for x in (0.17, 0.09, 0.05, 0.13, 0.08, 0.08, 0.07, 0.10, 0.23)]))
    P(f"<b>Bucket boundaries:</b> {clean(d['method']['boundary'])}", "small")
    P(f"<b>Why 4 stars is passive:</b> {clean(d['method']['boundary_why'])}", "small")
    P(f"<b>Interval:</b> {clean(d['method']['interval'])} With 2 or 4 reviews the interval covers much of the scale: the two +100 "
      f"scores are anecdotes, not evidence that those firms are better liked than Xendoo.", "small")
    if table_excerpt:
        P("Score table as printed by the executed notebook (copied from its saved output, not retyped):", "small")
        story.append(Preformatted(table_excerpt, S["mono"]))

    P("2b. 4-star sensitivity: what each NPS becomes if 4 stars count as promoters", "h2")
    rows = [[C("<b>Company</b>"), C("<b>n</b>"), C("<b>4-star reviews</b>"), C("<b>NPS, 4* = passive (primary)</b>"),
             C("<b>NPS, 4* = promoter</b>"), C("<b>Change</b>")]]
    for c in comps:
        a, b = c["primary"]["nps"], c["alt_4star_promoter"]["nps"]
        rows.append([C(clean(c["company"])), C(str(c["primary"]["n"])), C(str(c["stars"]["4"])), C(f(a)), C(f(b)),
                     C("n/a" if a is None else f"{b - a:+d}")])
    story.append(grid(rows, [W * x for x in (0.30, 0.08, 0.13, 0.19, 0.17, 0.13)]))
    n_all = sum(c["primary"]["n"] for c in comps); four = sum(c["stars"]["4"] for c in comps)
    P(f"The boundary choice moves no score: only {four} of {n_all} reviews is 4-star. That near-empty passive bucket is the "
      f"bimodal bias in action (see 2e). One more edge case: Xendoo's single 3-star review reads as praise but counts as a detractor "
      f"because the rule reads stars, not words; re-bucketing it would move Xendoo's NPS by under one point.", "small")

    P("2c. Sources, sample size and selection bias per company", "h2")
    P(f"<b>Source rule (same for all four):</b> {clean(d['method']['source_rule'])}", "small")
    for c in comps:
        p = c["primary"]
        block = [Paragraph(f"<b>{clean(c['company'])}</b> &mdash; n = {p['n']}, NPS {f(p['nps'])} "
                           f"(95% interval {ci(c['ci95'])}); source: {clean(c['source_used'] or 'none: no reviewable public presence')}"
                           + (f" (<a href=\"{clean(c['source_url'])}\" color=\"#1a4f8b\"><u>open the Google Maps listing</u></a>)"
                              if c.get("source_url") else ""), S["small"]),
                 Paragraph("<i>Checked:</i> " + clean("; ".join(c["attempts"])), S["cite"]),
                 Paragraph("<i>Identity:</i> " + clean(c["identity_note"]), S["cite"]),
                 Paragraph("<i>Selection bias:</i> " + clean(c["selection_bias"]), S["cite"])]
        story.append(KeepTogether(block)); story.append(Spacer(1, 3))

    story.append(KeepTogether([Paragraph("2d. NPS by company (best to worst)", S["h2"]),
                               Image(str(HERE / "nps_chart.png"), width=W * 0.86, height=W * 0.86 * 4.4 / 8.6)]))

    P("2e. Three real review excerpts showing the bucketing", "h2")
    for e in d["excerpts"]:
        story.append(KeepTogether([
            Paragraph(f"<b>{e['bucket'].capitalize()} ({e['stars']} stars)</b> &mdash; {clean(e['company'])}, {clean(e['source'])}, "
                      f"{clean(e['date'])}", S["small"]),
            Paragraph(f"&ldquo;{clean(e['quote'])}&rdquo;", S["cite"]),
            Paragraph(f"<i>Why this bucket:</i> {clean(e['why'])} <font color='#555555'>Google review id {clean(e['review_id'])}, "
                      f"cached in nps-scorer/cache/.</font>", S["cite"])]))
        story.append(Spacer(1, 3))

    P("2f. Limits (read before using these numbers)", "h2")
    P("<b>Bimodal review bias.</b> " + clean(d["limits"][0]), "small")
    P(" ".join(f"({i}) {clean(x)}" for i, x in enumerate(d["limits"][1:], 2)), "small")

    # one page for the track
    story.append(PageBreak())
    P("2g. Starting-a-company track: loyalty vs. review volume, and the wedge", "h2")
    story.append(Image(str(HERE / "nps_vs_volume.png"), width=W * 0.92, height=W * 0.92 * 4.6 / 8.6))
    for h, t in d["track"]["text"]:
        P(f"<b>{clean(h)}</b> {clean(t)}", "small")

    # ---------------------------------------------------------------- 3
    story.append(PageBreak())
    P("3. Reflection", "h1")
    for para in reflection_paragraphs(reflection):
        P(md_inline(para))

    def footer(canvas, doc_):
        canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GREY)
        canvas.drawString(0.75 * inch, 0.45 * inch, TITLE)
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc_.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.7 * inch,
                            bottomMargin=0.75 * inch, title=TITLE, author="MAcc strategy class project")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

def verify_pdf(path, d, reflection, urls):
    from pypdf import PdfReader
    r = PdfReader(str(path))
    FOOT = re.compile(re.escape(TITLE) + r"\s*Page \d+\s*")
    text = FOOT.sub("", "\n".join((p.extract_text() or "") for p in r.pages))
    sq = lambda s: re.sub(r"\s+", "", clean(s or "")).lower().replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")
    T = re.sub(r"\s+", "", text).lower()
    checks = []
    need = lambda label, cond: checks.append((label, bool(cond)))
    heads = ["1. Tool link", "2. Output", "3. Reflection"]
    pos = [T.find(sq(h)) for h in heads]
    need("exactly the three sections, in order", all(p >= 0 for p in pos) and pos == sorted(pos))
    need("section 1 is the first content on page one",
         re.sub(r"\s+", "", FOOT.sub("", r.pages[0].extract_text() or "")).lower().startswith(sq(heads[0])))
    p1 = {str(a.get_object()["/A"]["/URI"]) for a in (r.pages[0].get("/Annots") or []) if a.get_object().get("/A")}
    need("notebook + nbviewer links clickable on page one", urls["notebook"] in p1 and urls["nbviewer"] in p1)
    for c in d["companies"]:
        need(f"{c['slug']}: NPS + n in table", sq(c["company"]) in T and f"{c['primary']['n']}" in text)
        need(f"{c['slug']}: selection bias sentence", sq(c["selection_bias"]) in T)
        need(f"{c['slug']}: sensitivity value", sq(f(c["alt_4star_promoter"]["nps"])) in T)
    need("pivot note", sq(d["meta"]["pivot_note"]) in T)
    need("boundary + why", sq(d["method"]["boundary"]) in T and sq(d["method"]["boundary_why"]) in T)
    need("three excerpts, one per bucket", sorted(e["bucket"] for e in d["excerpts"]) == ["detractor", "passive", "promoter"]
         and all(sq(e["quote"]) in T for e in d["excerpts"]))
    need("bimodal limitation stated", "bimodalreviewbias" in T and sq(d["limits"][0]) in T)
    need("track analysis text", all(sq(t) in T for _, t in d["track"]["text"]))
    need("two chart images embedded", sum(len(p.images) for p in r.pages) >= 2)
    need("real notebook output excerpt", "checkvsgooglehistogram" in T)
    paras = reflection_paragraphs(reflection)
    need("reflection text in PDF", all(sq(re.sub(r"\*", "", p))[:80] in T for p in paras))
    return checks, len(r.pages)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo"); ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    repo = a.repo or json.loads((HERE.parent / "submission_config.json").read_text())["repo_url"]
    urls = urls_for(repo)
    d = json.loads((HERE / "nps_data.json").read_text())
    reflection = REFLECTION.read_text()
    body = re.sub(r"<!--.*?-->", "", reflection, flags=re.S)
    words = len(re.findall(r"\S+", re.sub(r"\*", "", body)))
    build(d, reflection, urls, notebook_score_table(), a.out)
    checks, pages = verify_pdf(a.out, d, reflection, urls)
    failed = [c for c in checks if not c[1]]
    print(f"Built {a.out}: {pages} pages; {len(checks)} content checks, {len(checks) - len(failed)} passed.")
    for label, ok in checks:
        if not ok: print("  FAILED:", label)
    labels = len([p for p in reflection_paragraphs(reflection) if p.startswith("**")])
    if PLACEHOLDER in reflection:
        print(f"  REFLECTION NOT WRITTEN YET: {REFLECTION.name} still has placeholders. Write 250-500 words under the three labels, then re-run.")
    elif not 250 <= words <= 500:
        print(f"  WARNING: reflection is {words} words; the assignment asks for 250-500.")
    elif labels != 3:
        print(f"  WARNING: reflection should keep the three bold labels (found {labels}).")
    else:
        print(f"  Reflection: {words} words, 3 labeled answers.")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
