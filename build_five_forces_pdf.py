#!/usr/bin/env python3
"""Build the ONE-PDF submission for the Five Forces scorer from five_forces.json + reflection_five_forces.md, then check the PDF by code.

Edit reflection_five_forces.md (250-500 words, keep the three bold labels) and re-run:
    python build_five_forces_pdf.py            -> five_forces_submission.pdf
Repo URL comes from submission_config.json {"repo_url": ...} or --repo URL.

Exactly three sections, in this order:
    1. Working tool link (five_forces.ipynb on GitHub + nbviewer backup), at the top of page one
    2. Output: scores, five forces with rationale and labeled cited facts, overall read, least-confident force, spreadsheet conflicts
    3. Reflection (from reflection_five_forces.md, written by the student)

This is a separate builder from build_pdf.py (which builds the first assignment's submission.pdf from brief.json + reflection.md);
both are kept so each deliverable can still be rebuilt.
"""
import json, re, sys, os, argparse
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, Preformatted

from build_pdf import clean, md_inline, link, styles, grid, BLUE, GREY

OUT = "five_forces_submission.pdf"
REFLECTION = "reflection_five_forces.md"
TITLE = "Porter's Five Forces Scorer: fractional CFO services"
PLACEHOLDER = "TO BE WRITTEN BY THE STUDENT"

def urls_for(repo):
    repo = re.sub(r"\.git$", "", repo.rstrip("/"))
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        sys.exit(f"repo_url must look like https://github.com/USER/REPO, got {repo!r}")
    u, n = m.groups()
    return {"repo": repo, "notebook": f"{repo}/blob/main/five_forces.ipynb",
            "nbviewer": f"https://nbviewer.org/github/{u}/{n}/blob/main/five_forces.ipynb"}

def notebook_excerpt(path="five_forces.ipynb"):
    """Real saved output from the executed notebook: the score listing and the verification counts. Nothing typed by hand."""
    nb = json.load(open(path))
    txt = "\n".join("".join(o.get("text", "")) for c in nb["cells"] if c["cell_type"] == "code"
                    for o in c.get("outputs", []) if o.get("output_type") == "stream")
    out = []
    m = re.search(r"Scores \(listed, NOT averaged\):\n(?:  .+\n)+", txt)
    if m: out.append(m.group(0).rstrip())
    m = re.search(r"first-project quotes[^\n]+\n\nFive Forces evidence quotes, by origin:\n(?:  .+\n)+", txt)
    if m: out.append(m.group(0).rstrip())
    m = re.search(r"Forces below the 3-fact / 2-sub-dimension minimum: [^\n]+", txt)
    if m: out.append(m.group(0))
    return "\n\n".join(out)

def cite_text(c):
    where = []
    if c.get("pdf_page"):
        where.append(f"PDF p.{c['pdf_page']}" + (f" (printed {c['printed_page']})" if c.get("printed_page") else ""))
    if c.get("url"):
        where.append(link(c["url"]))
    loc = ", ".join([clean(c["section"])] + where)
    return f"&ldquo;{clean(c['quote'])}&rdquo; <font color='#555555'>{clean(c['source'])}; {loc}. <i>{clean(c['verification'])}</i></font>"

def reflection_paragraphs(text):
    return [p.strip() for p in re.sub(r"<!--.*?-->", "", text, flags=re.S).strip().split("\n\n") if p.strip()]

def build(ff, reflection, urls, excerpt, path=OUT):
    S = styles()
    W = letter[0] - 1.5 * inch
    story = []
    P = lambda t, s="body": story.append(Paragraph(t, S[s]))

    # ---------------------------------------------------------------- 1
    P("1. Working tool link", "h1")
    P(f"<b>Notebook (GitHub, no login, outputs saved):</b> {link(urls['notebook'])}")
    P(f"<b>Backup viewer (nbviewer):</b> {link(urls['nbviewer'])}")
    P(f"Repository: {link(urls['repo'])}. The notebook reads <font face='Courier'>brief.json</font> from the earlier industry-intelligence "
      f"pipeline (same repo, <font face='Courier'>pipeline.ipynb</font>), maps its signals to the five forces, adds public evidence where the "
      f"brief was thin, verifies every quote in code, enforces the scoring rules, and writes <font face='Courier'>five_forces.json</font>, "
      f"which this PDF is built from.", "small")

    # ---------------------------------------------------------------- 2
    P("2. Output", "h1")
    m = ff["meta"]
    P(f"<b>Company:</b> {clean(m['company'])}. <b>Segment:</b> {clean(m['segment'])}. <b>Industry code:</b> {clean(m['naics'])}.", "small")
    P(f"<b>Scale:</b> {clean(ff['method']['scale'])}", "small")
    rows = [[Paragraph("<b>Force</b>", S["cell"]), Paragraph("<b>Score</b>", S["cell"]), Paragraph("<b>Facts / sub-dimensions covered</b>", S["cell"])]]
    for f in ff["forces"]:
        rows.append([Paragraph(clean(f["name"]), S["cell"]), Paragraph(f"<b>{f['score']}</b>", S["cell"]),
                     Paragraph(f"{len(f['facts'])} facts: " + clean("; ".join(f["subdimensions_covered"])), S["cell"])])
    story.append(grid(rows, [W * 0.36, W * 0.08, W * 0.56]))
    P("Scores are listed, not averaged. Each fact's label in [brackets] shows which sub-dimension it covers; (+) means the fact "
      "makes the force stronger, (-) weaker, (mixed) both. Fact IDs in each rationale point to the facts listed under it.", "small")

    P("2a. Overall industry attractiveness", "h2")
    P(f"<b>Dominant forces: {clean(', '.join(ff['overall_read']['dominant_forces']))}.</b> {clean(ff['overall_read']['text'])}")

    P("2b. The five forces, scored", "h2")
    for f in ff["forces"]:
        block = [Paragraph(f"{clean(f['name'])}: {f['score']} / 5", S["h3"]), Paragraph(clean(f["rationale"]), S["body"])]
        story.append(KeepTogether(block))
        for x in f["facts"]:
            item = [Paragraph(f"<b>{x['fact_id']}</b> <b>[{clean(x['label'])}]</b> ({clean(x['direction'])}) {clean(x['claim'])}", S["small"])]
            item += [Paragraph(cite_text(c), S["cite"]) for c in x["citations"]]
            story.append(KeepTogether(item))
        story.append(Spacer(1, 3))

    lc = ff["least_confident"]
    P("2c. Least-confident force", "h2")
    P(f"<b>{clean(lc['force'])} (scored {lc['score']}).</b> {clean(lc['why'])}")
    P(f"<b>What would settle it:</b> {clean(lc['what_would_settle_it'])}")

    P("2d. Method: two conflicts with the course spreadsheet, and how they were resolved", "h2")
    P(f"<b>Scale polarity.</b> {clean(ff['method']['polarity_conflict'])}")
    P(f"<b>Granularity.</b> {clean(ff['method']['granularity_conflict'])}")
    P(f"<b>What the spreadsheet was used for.</b> {clean(ff['method']['spreadsheet_used_for'])}")
    P(f"<b>Evidence rules.</b> {clean(ff['method']['evidence_rules'])}", "small")
    P(f"<b>Who did what.</b> {clean(ff['method']['who_did_what'])}", "small")
    v = ff["verification_summary"]
    P(f"<b>Verification.</b> {v['five_forces_quotes_checked']} Five Forces quotes checked, {v['five_forces_quotes_passed']} passed, "
      f"{v['five_forces_quotes_failed']} failed ({v['by_origin']['brief']['checked']} from brief.json, {v['by_origin']['report_page']['checked']} new "
      f"report-page extractions, {v['by_origin']['public']['checked']} public). All {v['brief_json_quotes_checked']} quotes from the first project "
      f"re-checked: {v['brief_json_quotes_passed']} passed. {v['negative_controls_rejected']} of {v['negative_controls_run']} deliberately corrupted "
      f"quotes were rejected. Facts dropped: {len(v['facts_dropped'])}. Thin before enrichment: {clean(', '.join(ff['thin_before_enrichment']))}.", "small")
    P("<b>Limits.</b> " + " ".join(f"({i}) {clean(x)}" for i, x in enumerate(ff["limits"], 1)), "small")
    if excerpt:
        P("Excerpt of the saved notebook output (copied from five_forces.ipynb, not retyped):", "small")
        story.append(Preformatted(excerpt, S["mono"]))

    # ---------------------------------------------------------------- 3
    P("3. Reflection", "h1")
    for para in reflection_paragraphs(reflection):
        P(md_inline(para))

    def footer(canvas, doc_):
        canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GREY)
        canvas.drawString(0.75 * inch, 0.45 * inch, TITLE)
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc_.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.7 * inch,
                            bottomMargin=0.75 * inch, title=TITLE, author="MAcc strategy class project")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

def verify_pdf(path, ff, reflection, urls):
    from pypdf import PdfReader
    r = PdfReader(path)
    FOOT = re.compile(re.escape(TITLE) + r"\s*Page \d+\s*")          # running footer; extracted first on each page
    text = FOOT.sub("", "\n".join((p.extract_text() or "") for p in r.pages))
    sq = lambda s: re.sub(r"\s+", "", clean(s or "")).lower().replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")
    T = re.sub(r"\s+", "", text).lower()
    checks = []
    need = lambda label, cond: checks.append((label, bool(cond)))
    heads = ["1. Working tool link", "2. Output", "3. Reflection"]
    pos = [T.find(sq(h)) for h in heads]
    need("exactly the three sections, in order", all(p >= 0 for p in pos) and pos == sorted(pos))
    need("section 1 is the first content on page one", re.sub(r"\s+", "", FOOT.sub("", r.pages[0].extract_text() or "")).lower().startswith(sq(heads[0])))
    uris = {str(a.get_object()["/A"]["/URI"]) for p in r.pages for a in (p.get("/Annots") or [])
            if a.get_object().get("/A") and a.get_object()["/A"].get("/URI")}
    p1 = {str(a.get_object()["/A"]["/URI"]) for a in (r.pages[0].get("/Annots") or []) if a.get_object().get("/A")}
    need("notebook + nbviewer links clickable on page one", urls["notebook"] in p1 and urls["nbviewer"] in p1)
    for f in ff["forces"]:
        need(f"{f['key']}: name + whole-number score", sq(f"{f['name']}: {f['score']} / 5") in T and isinstance(f["score"], int))
        need(f"{f['key']}: rationale", sq(f["rationale"]) in T)
        need(f"{f['key']}: 3+ facts", len(f["facts"]) >= 3)
        for x in f["facts"]:
            need(f"{x['fact_id']}: label + claim", sq(f"[{x['label']}]") in T and sq(x["claim"]) in T)
            for c in x["citations"]:
                need(f"{x['fact_id']}: quote + verified", sq(c["quote"]) in T and c["verification"].startswith("verified"))
    need("overall read + dominant forces", sq(ff["overall_read"]["text"]) in T and all(sq(d) in T for d in ff["overall_read"]["dominant_forces"]))
    need("least-confident force + what settles it", sq(ff["least_confident"]["why"]) in T and sq(ff["least_confident"]["what_would_settle_it"]) in T)
    need("polarity conflict note", sq(ff["method"]["polarity_conflict"]) in T)
    need("granularity conflict note", sq(ff["method"]["granularity_conflict"]) in T)
    need("real notebook output excerpt", sq("Scores (listed, NOT averaged):") in T)
    need("no quote over 25 words", all(len(c["quote"].split()) <= 25 for f in ff["forces"] for x in f["facts"] for c in x["citations"]))
    paras = reflection_paragraphs(reflection)
    need("reflection text in PDF", all(sq(re.sub(r"\*", "", p))[:80] in T for p in paras))
    return checks, len(r.pages)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo"); ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    repo = a.repo or json.load(open("submission_config.json"))["repo_url"]
    urls = urls_for(repo)
    ff = json.load(open("five_forces.json"))
    reflection = open(REFLECTION).read()
    body = re.sub(r"<!--.*?-->", "", reflection, flags=re.S)
    words = len(re.findall(r"\S+", re.sub(r"\*", "", body)))
    build(ff, reflection, urls, notebook_excerpt(), a.out)
    checks, pages = verify_pdf(a.out, ff, reflection, urls)
    failed = [c for c in checks if not c[1]]
    print(f"Built {a.out}: {pages} pages; {len(checks)} content checks, {len(checks) - len(failed)} passed.")
    for label, ok in checks:
        if not ok: print("  FAILED:", label)
    labels = len([p for p in reflection_paragraphs(reflection) if p.startswith("**")])
    if PLACEHOLDER in reflection:
        print(f"  REFLECTION NOT WRITTEN YET: {REFLECTION} still has placeholders. Write 250-500 words under the three labels, then re-run.")
    elif not 250 <= words <= 500:
        print(f"  WARNING: reflection is {words} words; the assignment asks for 250-500.")
    elif labels != 3:
        print(f"  WARNING: reflection should keep the three bold labels (found {labels}).")
    else:
        print(f"  Reflection: {words} words, 3 labeled answers.")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
