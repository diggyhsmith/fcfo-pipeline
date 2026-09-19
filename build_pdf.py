#!/usr/bin/env python3
"""Build the ONE-PDF submission from brief.json + reflection.md + the executed pipeline.ipynb, then verify the PDF by code.

Edit reflection.md (or submission_config.json) and re-run:   python build_pdf.py            -> submission.pdf
Repo URL comes from submission_config.json {"repo_url": "https://github.com/USER/REPO"} or  --repo URL.

Sections, in order:  1. Working tool link | 2. Output (2a NAICS, 2b brief, 2c sources, 2d gaps, 2e method/AI/limits) | 3. Reflection
"""
import json, re, sys, os, html, argparse, datetime, textwrap
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Preformatted, PageBreak

OUT = "submission.pdf"
BLUE = colors.HexColor("#1a4f8b")
GREY = colors.HexColor("#555555")

# ------------------------------------------------------------------------------------------------ helpers
def clean(s):
    """Escape for reportlab Paragraph markup and keep to characters the built-in Helvetica (cp1252) can draw."""
    s = "" if s is None else str(s)
    s = s.replace("≥", ">=").replace("≤", "<=").replace("→", "->").replace("•", "-")
    s = re.sub(r"[\ue000-\uf8ff]", "", s)
    s = s.encode("cp1252", "replace").decode("cp1252")
    return escape(s)

def md_inline(s):
    """**bold** and *italic* from reflection.md to reportlab tags."""
    s = clean(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)

def link(url):
    return f'<a href="{escape(url)}" color="#1a4f8b"><u>{escape(url)}</u></a>'

def repo_urls(repo):
    repo = repo.rstrip("/")
    repo = re.sub(r"\.git$", "", repo)
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        sys.exit(f"repo_url must look like https://github.com/USER/REPO, got {repo!r}")
    user, name = m.groups()
    return {"repo": repo, "notebook": f"{repo}/blob/main/pipeline.ipynb",
            "nbviewer": f"https://nbviewer.org/github/{user}/{name}/blob/main/pipeline.ipynb"}

def notebook_outputs(path="pipeline.ipynb"):
    nb = json.load(open(path))
    chunks = []
    for c in nb["cells"]:
        if c["cell_type"] != "code": continue
        txt = "".join("".join(o.get("text", "")) for o in c.get("outputs", []) if o.get("output_type") == "stream" and o.get("name") == "stdout")
        if txt.strip(): chunks.append(txt)
    return chunks

def pick_excerpt(chunks):
    """Real, saved pipeline output: NAICS choice, verification summary, conflicts, final summary. Nothing here is typed by hand."""
    joined = "\n".join(chunks)
    out = []
    m = re.search(r"Chosen NAICS: [^\n]+", joined); out += [m.group(0)] if m else []
    m = re.search(r"Mode: [^\n]+\n\nQuotes checked:[^\n]+\nNumbers in signal values[^\n]+", joined); out += ["", m.group(0)] if m else []
    m = re.search(r"Conflicts kept side by side \(never averaged\):\n(?:  \[[^\n]+\n)+", joined)
    if m: out += ["", m.group(0).rstrip()]
    m = re.search(r"FINAL SUMMARY\n(?:  [^\n]+\n?)+", joined)
    if m: out += ["", m.group(0).rstrip()]
    return "\n".join(out)

# ------------------------------------------------------------------------------------------------ document
def styles():
    ss = getSampleStyleSheet()
    S = {}
    S["body"] = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.4, leading=12.4, spaceAfter=4)
    S["small"] = ParagraphStyle("small", parent=S["body"], fontSize=8, leading=10.2, textColor=colors.black, spaceAfter=2)
    S["cite"] = ParagraphStyle("cite", parent=S["small"], leftIndent=12, textColor=colors.HexColor("#222222"))
    S["h1"] = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=BLUE, spaceBefore=10, spaceAfter=6)
    S["h2"] = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=BLUE, spaceBefore=9, spaceAfter=4)
    S["h3"] = ParagraphStyle("h3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=9.8, leading=12, spaceBefore=8, spaceAfter=2)
    S["mono"] = ParagraphStyle("mono", fontName="Courier", fontSize=6.9, leading=8.3, backColor=colors.HexColor("#f3f3f3"), borderPadding=4)
    S["cell"] = ParagraphStyle("cell", parent=S["small"], fontSize=7.6, leading=9.4)
    S["cellb"] = ParagraphStyle("cellb", parent=S["cell"], fontName="Helvetica-Bold")
    return S

def cite_line(c):
    printed = f" (printed {c['printed_page']})" if c.get("printed_page") else ""
    return (f"[{clean(c['doc_id'])}, {clean(c['section_heading'] or 'no heading detected')}, PDF p.{c['pdf_page']}{printed}] "
            f"&ldquo;{clean(c['quote'])}&rdquo; <i>{clean(c['verification'])}</i>")

def grid(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if header: st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6edf5")))
    t.setStyle(TableStyle(st))
    return t

def build(brief, reflection, urls, excerpt, path=OUT):
    S = styles()
    W = letter[0] - 1.5 * inch
    story = []
    P = lambda txt, st="body": story.append(Paragraph(txt, S[st]))

    # ---------------- 1. Working tool link (very top of page one)
    P("1. Working tool link", "h1")
    P(f"Notebook (opens with no login, outputs saved in the file): {link(urls['notebook'])}")
    P(f"Same notebook in nbviewer: {link(urls['nbviewer'])}")
    P(f"Repository (README, extractions, verification log, brief): {link(urls['repo'])}")
    P(f"{clean(brief['meta']['company'])}. {clean(brief['meta']['description'])}", "small")
    P(f"Generated {clean(brief['meta']['generated'][:10])}. Extraction by Claude Code (an LLM agent); verification, reconciliation, gaps and this brief by code.", "small")

    # ---------------- 2. Output
    P("2. Output", "h1")
    n = brief["naics"]
    P("2a. NAICS code selected", "h2")
    P(f"<b>{clean(n['chosen_code'])} {clean(n['chosen_title'])}</b> (2022 NAICS). Closest neighbor rejected: {clean(n['neighbor_code'])} {clean(n['neighbor_title'])}.")
    P(f"<b>Why this code and not {clean(n['neighbor_code'])}:</b> {clean(n['justification'])}")
    P(f"Source: 2022 NAICS Manual, U.S. Census Bureau, {link(n['manual_url'])} (accessed {clean(n['accessed'])}; landing page {link(n['landing_page'])}). "
      f"Candidates fetched and compared: {', '.join(clean(c['code']) for c in n['candidates'])}. All {n['quotes_verified']} phrases quoted in the justification were checked in code against the fetched entries.", "small")
    rows = [[Paragraph("Report", S["cellb"]), Paragraph("Stated code / NAICS 2022 listed", S["cellb"]), Paragraph("Match with chosen code?", S["cellb"])]]
    for r in brief["report_scope"]:
        rows.append([Paragraph(clean(r["doc_id"]), S["cell"]), Paragraph(clean(f"{r['stated_code'] or 'none stated'} / {', '.join(r['naics_2022_listed']) or 'none'}"), S["cell"]),
                     Paragraph(clean(("YES. " if r["covers_chosen_code"] else "NO. ") + r["relation"]), S["cell"])])
    story += [Spacer(1, 3), grid(rows, [1.95 * inch, 1.45 * inch, W - 3.4 * inch])]

    P("2b. The brief: seven signals, each cited and verified", "h2")
    P(clean(brief["meta"]["proxy_industry_warning"]), "small")
    P(f"Primary-value rule: {clean(brief['meta']['primary_rule'])} Citation format: [doc_id, section, PDF page (printed page)] then a verbatim quote of 25 words or fewer, then its verification label "
      f"(verified = quote found on that page; verified_adjacent_page = found on a neighboring page).", "small")
    for sg in brief["signals"]:
        blk = [Paragraph(f"{clean(sg['signal_id'])}. {clean(sg['name'])}", S["h3"]),
               Paragraph(f"<b>Force tag:</b> {clean(sg['force_tag'])} &nbsp;|&nbsp; <b>Status:</b> {clean(sg['status'])} (for the proxy industry, not the fractional niche) &nbsp;|&nbsp; <b>Verified quotes:</b> {sg['quotes_verified']}", S["small"])]
        story.append(KeepTogether(blk))
        for i, x in enumerate(([sg["primary"]] if sg["primary"] else []) + sg["other_documents"]):
            tag = "PRIMARY" if i == 0 else "ALSO"
            P(f"<b>{tag}: {clean(x['doc_id'])}</b> ({clean(x['status'])}; confidence {clean(x['confidence']['level'])}: {clean(x['confidence']['reason'])})", "small")
            P(f"<b>Value:</b> {clean(x['value_text'])}", "small")
            P(f"<b>Summary:</b> {clean(x['summary'])}", "small")
            for c in x["citations"]:
                P("Cite " + cite_line(c), "cite")
            P(f"<b>Scope note:</b> {clean(x['notes'])}", "cite")
        for c in sg["not_supported_by"]:
            P(f"<b>Not supported by {clean(c['doc_id'])}:</b> {clean(c['status'])}", "small")
        for c in sg["conflicts"]:
            head = [Paragraph(f"<b>Conflict</b> ({clean(c['kind'].replace('_', ' '))}): {clean(c['metric'])}. Shown side by side, never averaged.", S["small"])]
            cols = len(c["sides"]); cw = W / cols
            cells = [[Paragraph(f"<b>{clean(s['doc_id'])}</b><br/>value: <b>{clean(s['value'])}</b><br/>{clean(s['period_or_year'])}", S["cell"]) for s in c["sides"]],
                     [Paragraph(cite_line(s["citation"]) if s["citation"] else "no verified citation", S["cell"]) for s in c["sides"]]]
            head += [grid(cells, [cw] * cols, header=False), Paragraph(f"Why they may differ: {clean(c['why_they_may_differ'])}", S["cite"]), Spacer(1, 2)]
            story.append(KeepTogether(head))

    P("2c. Source list", "h2")
    rows = [[Paragraph(h, S["cellb"]) for h in ("Title", "Publisher", "Date", "Report code", "How a stranger finds it")]]
    for s in brief["sources"]:
        code = s["stated_industry_code"] or "not stated"
        if s.get("code_note"): code += " (" + s["code_note"] + ")"
        rows.append([Paragraph(clean(s["title"]), S["cell"]), Paragraph(clean(s["publisher"]), S["cell"]), Paragraph(clean(s["publication_date"]), S["cell"]),
                     Paragraph(clean(code), S["cell"]), Paragraph(clean(s["how_to_find"]), S["cell"])])
    story.append(grid(rows, [1.55 * inch, 1.1 * inch, 0.75 * inch, 1.5 * inch, W - 4.9 * inch]))
    P("The PDFs were downloaded by hand from a library subscription and are not redistributed. Naming the exact report title and date lets anyone with access retrieve the same file.", "small")

    P("2d. What the pipeline could not find, and what I would need to find it", "h2")
    P("Blunt version: no signal describes fractional CFO services themselves. Everything below is a proxy, and the suggested sources were not consulted; they are where such data would likely live.", "small")
    labels = {"document-signal": "Signal gaps by document", "conflict": "Unresolved conflicts", "structural": "Structural gaps"}
    for scope in ("document-signal", "conflict", "structural"):
        items = [g for g in brief["gaps"] if g["scope"] == scope]
        if not items: continue
        P(labels[scope], "h3")
        for g in items:
            who = f" ({clean(g['signal_id'] or '')}{', ' + clean(g['doc_id']) if g['doc_id'] else ''})" if (g["signal_id"] or g["doc_id"]) else ""
            P(f"<b>{clean(g['why'])}</b>{who}. <b>Missing:</b> {clean(g['what_is_missing'])} <b>What would find it:</b> {clean(g['what_would_find_it'])}", "small")

    P("2e. Method, AI use, and limits", "h2")
    v = brief["verification_summary"]
    P("Who did what", "h3")
    P("<b>Agent-performed:</b> reading the cached page text and writing the seven signals, their summaries, confidence ratings and verbatim quotes was done by <b>Claude Code, an LLM agent</b> (model claude-sonnet-5), "
      "during the build session, one document at a time. It was not a paid API call and not a human. It also wrote the code and the drafts of this document. "
      "<b>Code-executed:</b> PDF text extraction, the NAICS manual fetch and phrase check, quote verification, number checks, cross-document reconciliation, gap generation and the brief are ordinary Python, "
      "run top to bottom in the notebook so the saved outputs are real. I did not trust the model's quotes: each one is string-matched against the cited page.")
    P("Choices, rejected alternatives, and why", "h3")
    rows = [[Paragraph(h, S["cellb"]) for h in ("Stage", "Choice", "Rejected alternative", "Why")],
            ["Ingest", "pdfplumber, per page, cached with printed page label; column-aware and raw text variants", "One text blob per document; pypdf only", "A citation without a page is not findable; two-column pages break quotes under default extraction"],
            ["NAICS", "Fetch the official 2022 manual, compare candidates, quote its words, assert the quotes exist", "Pick by report title; recall definitions from memory", "Lets the classification, not data availability, choose the proxy; a mis-quote fails the run"],
            ["Extraction", "LLM agent reads pages, writes JSON to a fixed schema with evidence on every claim; NOT_FOUND over inference", "Paid API; keyword rules; one pass over all reports", "Zero cost; tables and 'biggest trend' need reading; separate passes stop one report contaminating another"],
            ["Verification", "Normalise and string-match every quote on its page, then adjacent pages, then tightly-guarded fuzzy match; check every number is in a quote", "Ask the model to re-check itself; plain fuzzy >= 90", "A self-check can repeat the error; plain fuzzy passed a changed word (grew to shrank) in my own control test"],
            ["Reconciliation", "Primary by scope proximity to the chosen code, then FOUND, then recency; conflicts kept side by side", "Averaging; newest-report-wins", "Averaging invents a number nobody published; the newest report is not the nearest to our code"],
            ["Gaps", "Generated from the run, naming a source type for each", "A generic limitations paragraph", "Tells a founder what number to go and get"]]
    rows = [rows[0]] + [[Paragraph(clean(c), S["cell"]) for c in r] for r in rows[1:]]
    story.append(grid(rows, [0.85 * inch, 2.15 * inch, 1.6 * inch, W - 4.6 * inch]))
    P("Why page-level citation and manual upload", "h3")
    P("A page number is the smallest unit a reader can check in under a minute, and it makes quote verification mechanical. The reports are paywalled and licensed for reading, not redistribution, so I downloaded them by hand "
      "instead of scraping, kept them out of the repository (reports/ and cache/ are git-ignored), and commit only quotes of 25 words or fewer. Consequence: without the PDFs, Stage 0 and Stage 3 cannot be re-run; "
      "the notebook then replays the committed verification log and says so.")
    P("What verification proves, and what it does not", "h3")
    P(f"It proves that each quote exists on the page cited (or an adjacent page) and that each number in a value appears in a verified quote. In this run: <b>{v['quotes_checked']} quotes checked, {v['passed']} passed, "
      f"{v['failed']} failed, {v['corrected_in_retry']} corrected in retry</b> ({v['passed_exact']} exact, {v['passed_adjacent_page']} adjacent-page, {v['passed_fuzzy']} fuzzy); numbers checked {v['numbers_checked']}, unmatched {v['numbers_unmatched']}; "
      f"fix-and-retry rounds run {v.get('rounds_run', 1)} (limit 2). It does <b>not</b> prove the interpretation is right: whether a table row was read correctly, whether 'biggest trend' was chosen sensibly, or whether a figure "
      "describes our niche. Zero failures means the quotes were copied faithfully, not that the analysis is correct. A verifier self-test in the notebook (corrupting quotes four ways) shows it can fail.")
    P("Other limits", "h3")
    P("<b>Non-determinism:</b> LLM extraction can differ between runs; a re-extraction might pick different quotes or a different 'biggest' trend. The saved extractions are the record of this run. "
      "<b>Proxy-industry problem:</b> fractional CFO has no NAICS code, so all figures describe management consulting or accounting; only one of the three reports sits on the chosen code. "
      "<b>Dated and mixed vintages:</b> the reports are dated " + ", ".join(clean(f"{s['title']} ({s['publication_date']})") for s in brief["sources"]) + "; the First Research printout also carries older embedded data. "
      "<b>Third report:</b> it is a First Research (Dun &amp; Bradstreet) profile from D&amp;B Hoovers, not a MarketResearch.com report, and its industry-code page printed empty. "
      f"<b>Gemini backend:</b> {clean(brief['meta']['gemini_backend_status'])}. It has never called the live API; only its parsing, retry and merge logic ran against a mock. No paid service was used anywhere.")
    P("Hand check and spot-check list", "h3")
    P(clean(brief["meta"]["hand_checked_line"].split(" (")[0]))
    P(f"Five findings drawn at random (seed {brief['spot_check']['seed']}) for a human to compare against the PDFs:", "small")
    for x in brief["spot_check"]["items"]:
        P(f"{clean(x['signal_id'])} {clean(x['name'])}: <b>{clean(x['doc_id'])}</b>, PDF p.{x['pdf_page']} (printed {clean(x['printed_page'])}): &ldquo;{clean(x['quote'])}&rdquo;", "cite")
    P("Excerpt of real pipeline output (saved from the executed notebook)", "h3")
    for line in excerpt.split("\n"):        # wrap to the page width (Courier 6.9pt fits ~118 characters) so nothing is clipped
        for w in (textwrap.wrap(line, 118, subsequent_indent="      ", break_long_words=True) or [" "]):
            story.append(Preformatted(w, S["mono"]))

    # ---------------- 3. Reflection
    P("3. Reflection", "h1")
    for para in [p for p in reflection.strip().split("\n\n") if p.strip()]:
        P(md_inline(para))

    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GREY)
        canvas.drawString(0.75 * inch, 0.45 * inch, "Industry Intelligence Pipeline: fractional CFO services")
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc.page}")
        canvas.restoreState()
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.7 * inch, bottomMargin=0.75 * inch,
                            title="Industry Intelligence Pipeline: fractional CFO services", author="MAcc strategy class project")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

# ------------------------------------------------------------------------------------------------ verify the PDF by code
def verify_pdf(path, brief, reflection, urls):
    from pypdf import PdfReader
    r = PdfReader(path)
    FOOT = re.compile(r"Industry Intelligence Pipeline: fractional CFO services\s*\nPage \d+\s*\n")
    text = FOOT.sub("", "\n".join((p.extract_text() or "") for p in r.pages))     # running footer would split paragraphs at page breaks
    sq = lambda s: re.sub(r"\s+", "", s or "").lower()
    T = sq(text)
    checks, ok = [], True
    def need(label, cond):
        nonlocal ok
        checks.append((label, bool(cond))); ok &= bool(cond)
    # headings, in order
    heads = ["1.Workingtoollink", "2.Output", "2a.NAICScodeselected", "2b.Thebrief", "2c.Sourcelist", "2d.Whatthepipelinecouldnotfind", "2e.Method,AIuse,andlimits", "3.Reflection"]
    pos = [T.find(sq(h)) for h in heads]
    need("all section headings present", all(p >= 0 for p in pos))
    need("section headings in required order", pos == sorted(pos) and all(p >= 0 for p in pos))
    p1 = FOOT.sub("", r.pages[0].extract_text() or "")
    need("section 1 heading is the first content on page one", sq(p1).startswith(sq("1. Working tool link")))
    # links: text and clickable annotations
    uris = set()
    for p in r.pages:
        for a in (p.get("/Annots") or []):
            o = a.get_object()
            if o.get("/A") and o["/A"].get("/URI"): uris.add(str(o["/A"]["/URI"]))
    need("notebook URL in text", sq(urls["notebook"]) in T)
    need("nbviewer URL in text", sq(urls["nbviewer"]) in T)
    need("notebook URL is a clickable link", urls["notebook"] in uris)
    need("nbviewer URL is a clickable link", urls["nbviewer"] in uris)
    need("notebook link on page one", any(urls["notebook"] in str(a.get_object().get("/A", {}).get("/URI", "")) for a in (r.pages[0].get("/Annots") or [])))
    # 2a
    n = brief["naics"]
    need("NAICS code + title", sq(n["chosen_code"]) in T and sq(n["chosen_title"]) in T)
    need("neighbor code named with 'why not'", sq(n["neighbor_code"]) in T and sq("Why this code and not " + n["neighbor_code"]) in T)
    need("Census manual URL", sq(n["manual_url"]) in T)
    # 2b: every signal, force tag, value, citation, verification status, conflicts
    for sg in brief["signals"]:
        need(f"{sg['signal_id']} name + force tag + status", sq(sg["name"]) in T and sq("Force tag: " + sg["force_tag"]) in T and sq("Status: " + sg["status"]) in T)
        for x in ([sg["primary"]] if sg["primary"] else []) + sg["other_documents"]:
            need(f"{sg['signal_id']} {x['doc_id']} value + summary", sq(x["value_text"]) in T and sq(x["summary"]) in T)
            for c in x["citations"]:
                pr = f" (printed {c['printed_page']})" if c.get("printed_page") else ""
                need(f"{sg['signal_id']} citation {c['doc_id']} p{c['pdf_page']}", sq(f"[{c['doc_id']}, {c['section_heading'] or 'no heading detected'}, PDF p.{c['pdf_page']}{pr}]") in T and sq(c["quote"]) in T and sq(c["verification"]) in T)
        for c in sg["conflicts"]:
            need(f"{sg['signal_id']} conflict '{c['metric']}' both sides", all(sq(str(s["value"])) in T and sq(s["doc_id"]) in T for s in c["sides"]))
    # 2c
    for s in brief["sources"]:
        need(f"source {s['doc_id']}", all(sq(s[k]) in T for k in ("title", "publisher", "publication_date", "how_to_find")))
    # 2d
    for g in brief["gaps"]:
        need(f"gap '{g['why'][:40]}'", sq(g["why"]) in T and sq(g["what_would_find_it"][:60]) in T)
    # 2e
    v = brief["verification_summary"]
    need("verification summary numbers", sq(f"{v['quotes_checked']} quotes checked, {v['passed']} passed, {v['failed']} failed, {v['corrected_in_retry']} corrected in retry") in T)
    need("hand-checked line to fill in", sq("Hand-checked by me: [ ] of [ ] citations") in T)
    need("5 spot-check items with doc + page", len(brief["spot_check"]["items"]) == 5 and all(sq(x["doc_id"]) in T and sq(f"PDF p.{x['pdf_page']}") in T for x in brief["spot_check"]["items"]))
    need("Gemini status stated honestly", sq("implemented, untested") in T)
    need("AI use: Claude Code LLM agent named", sq("Claude Code, an LLM agent") in T)
    for phrase in ("What verification proves", "does not", "Non-determinism", "Proxy-industry problem", "Dated and mixed vintages", "Why page-level citation and manual upload", "Excerpt of real pipeline output"):
        need(f"2e covers: {phrase}", sq(phrase) in T)
    need("excerpt has real output (Quotes checked line)", sq("Quotes checked: %d" % v["quotes_checked"]) in T)
    # 3
    words = len(re.findall(r"\S+", re.sub(r"\*", "", reflection)))
    need(f"reflection word count {words} within 250-500", 250 <= words <= 500)
    need("reflection text present in PDF", sq(re.sub(r"\*", "", reflection.strip().split("\n\n")[-1])[:120]) in T)
    need("3 labeled paragraphs", len([p for p in reflection.strip().split("\n\n") if p.strip().startswith("**")]) == 3)
    # licensing: no quote over 25 words anywhere in the brief
    allq = [c["quote"] for sg in brief["signals"] for x in ([sg["primary"]] if sg["primary"] else []) + sg["other_documents"] for c in x["citations"]]
    need("every quoted passage <= 25 words", all(len(q.split()) <= 25 for q in allq))
    return ok, checks, len(r.pages)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="https://github.com/USER/REPO")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    repo = a.repo or (json.load(open("submission_config.json"))["repo_url"] if os.path.exists("submission_config.json") else None)
    if not repo:
        sys.exit("No repo URL. Pass --repo https://github.com/USER/REPO or create submission_config.json.")
    urls = repo_urls(repo)
    brief = json.load(open("brief.json"))
    reflection = open("reflection.md").read()
    words = len(re.findall(r"\S+", re.sub(r"\*", "", reflection)))
    assert 250 <= words <= 500, f"reflection.md has {words} words; must be 250-500"
    chunks = notebook_outputs()
    if not chunks:
        sys.exit("pipeline.ipynb has no saved outputs: execute it first (jupyter nbconvert --execute --inplace pipeline.ipynb).")
    excerpt = pick_excerpt(chunks)
    build(brief, reflection, urls, excerpt, a.out)
    ok, checks, pages = verify_pdf(a.out, brief, reflection, urls)
    failed = [c for c in checks if not c[1]]
    print(f"Built {a.out}: {pages} pages; {len(checks)} content checks, {len(checks) - len(failed)} passed, reflection {words} words.")
    for label, _ in failed: print("  MISSING:", label)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
