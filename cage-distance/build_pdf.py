#!/usr/bin/env python3
"""Build the ONE-PDF submission for the CAGE Distance tool from cage_results.json + reflection_cage.md, then check it by code.

Run from this folder after executing the notebook:
    python build_pdf.py            -> cage_distance_submission.pdf
Repo URL comes from ../submission_config.json {"repo_url": ...} or --repo URL.

Header (title, author, date placeholder), then exactly three sections, in this order:
    1. Tool link (cage-distance/cage_distance.ipynb on GitHub + nbviewer backup), clickable, at the top of page one
    2. Output: the four dimension cards with sources, the industry assumed and how it changed the weighting, total and rating,
       recommendation and single largest risk, sensitivity analysis (table, chart, where it flips), contrast pairs, what was not verified, limits
    3. Reflection (three headings, from reflection_cage.md)

Separate from the earlier deliverables' builders; only the shared styling helpers from ../build_pdf.py are reused.
"""
import json, re, sys, argparse
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from build_pdf import clean, md_inline, link, styles, grid, GREY   # shared styling from the first deliverable

OUT = HERE / "cage_distance_submission.pdf"
REFLECTION = HERE / "reflection_cage.md"
TITLE = "CAGE Distance Framework Tool: United States to Canada"
AUTHOR = "Diggy Smith"
DATE_PLACEHOLDER = "[DATE]"
PLACEHOLDER = "TO BE WRITTEN BY THE STUDENT"
DIMS = ["Cultural", "Administrative", "Geographic", "Economic"]
# Helvetica (WinAnsi) has no glyph for these; print plain equivalents
GLYPHS = {"→": "to", "−": "-", "≥": ">=", "≤": "<=", "Σ": "sum", "·": "&middot;"}

def urls_for(repo):
    repo = re.sub(r"\.git$", "", repo.rstrip("/"))
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        sys.exit(f"repo_url must look like https://github.com/USER/REPO, got {repo!r}")
    u, n = m.groups()
    return {"repo": repo, "folder": f"{repo}/tree/main/cage-distance",
            "notebook": f"{repo}/blob/main/cage-distance/cage_distance.ipynb",
            "facts": f"{repo}/blob/main/cage-distance/cage_facts.json",
            "nbviewer": f"https://nbviewer.org/github/{u}/{n}/blob/main/cage-distance/cage_distance.ipynb"}

def t(s):
    s = clean(str(s))
    for k, v in GLYPHS.items():
        s = s.replace(k, v)
    return s

def md(s):
    """**bold** -> <b>, after escaping."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t(s))

def a(url, text):
    return f'<a href="{clean(url)}" color="#1a4f8b"><u>{t(text)}</u></a>'

def img(name, width):
    from PIL import Image as PILImage
    w, h = PILImage.open(HERE / name).size
    return Image(str(HERE / name), width=width, height=width * h / w)

def reflection_paragraphs(text):
    return [p.strip() for p in re.sub(r"<!--.*?-->", "", text, flags=re.S).strip().split("\n\n") if p.strip()]

def sources_of(dim):
    seen, out = set(), []
    for c in dim["components"]:
        for s in c["sources"]:
            if s["url"] not in seen:
                seen.add(s["url"])
                out.append(s)
    return out

def build(d, reflection, urls, path=OUT):
    S = styles()
    S["cell"].fontSize, S["cell"].leading = 7.1, 8.6           # denser tables than the earlier deliverables, to keep this one near five pages
    S["small"].fontSize, S["small"].leading = 7.8, 9.8
    W = letter[0] - 1.5 * inch
    story = []
    P = lambda x, s="body": story.append(Paragraph(x, S[s]))
    C = lambda x, s="cell": Paragraph(x, S[s])
    pr, rec = d["pair"], d["recommendation"]
    sc = d["scores"]

    # ---------------------------------------------------------------- header
    P(f"<font size=16><b>{t(TITLE)}</b></font>", "body")
    P(f"{AUTHOR} &nbsp;&middot;&nbsp; {DATE_PLACEHOLDER}", "body")
    story.append(Spacer(1, 2))

    # ---------------------------------------------------------------- 1
    P("1. Tool link", "h1")
    P(f"<b>Notebook (GitHub, no login, outputs saved):</b> {link(urls['notebook'])}")
    P(f"<b>Backup viewer (nbviewer):</b> {link(urls['nbviewer'])}")
    P(f"Folder with the cached sources, the cited fact table <font face='Courier'>cage_facts.json</font> and this builder: {link(urls['folder'])}. "
      f"Set HOME / TARGET / INDUSTRY at the top of the notebook to run any ISO country pair.", "small")

    # ---------------------------------------------------------------- 2
    P("2. Output", "h1")
    P(f"<b>Pair:</b> {t(pr['home_name'])} (home) to {t(pr['target_name'])} (target). <b>Industry assumed:</b> {t(d['industry'])}, delivered online by a US firm. "
      f"Each dimension is scored 0-100 (higher = more distance) by fixed, visible rules in the notebook; every figure is fetched from a cited country-level source "
      f"(retrieved {t(d['generated'])}) or from a verified quote; anything not verified is left out of the score.", "small")

    P("2a. Scores, total and rating", "h2")
    tab = [[C("<b>Dimension</b>"), C("<b>Score</b>"), C("<b>Industry weight</b>"), C("<b>Contribution</b>"), C("<b>Why this weight</b>")]]
    for k in DIMS:
        tab.append([C(f"<b>{k}</b>"), C(f"<b>{sc[k]:.1f}</b>"), C(f"{d['weights'][k]:.2f}"), C(f"{sc[k] * d['weights'][k]:.1f}"), C(t(d["weight_rationale"][k]))])
    tab.append([C("<b>Total</b>"), C(""), C("1.00"), C(f"<b>{d['total']:.1f} ({d['rating']})</b>"), C(
        f"Thresholds: below {d['thresholds']['low']} low; {d['thresholds']['low']}-{d['thresholds']['high']} moderate; {d['thresholds']['high']}+ high "
        "(quarter and half of the scale; a judgment, anchored by the contrast pairs in 2f).")])
    story.append(grid(tab, [W * x for x in (0.14, 0.08, 0.1, 0.13, 0.55)]))
    story.append(Spacer(1, 4))
    story.append(img("cage_scores.png", W * 0.5))
    P(f"<b>How the industry changed the weighting.</b> With equal weights (an industry-neutral reading) the total would be {d['equal_total']:.1f}; the bookkeeping weights "
      f"raise it to {d['total']:.1f} because the dimension this service is most exposed to, Administrative, is also the largest score. Under a contrasting industry, "
      f"{t(d['contrast_industry'])} (Geographic {d['contrast_weights']['Geographic']:.2f}, Economic {d['contrast_weights']['Economic']:.2f}, "
      f"Administrative {d['contrast_weights']['Administrative']:.2f}, Cultural {d['contrast_weights']['Cultural']:.2f}: heavy, cheap-per-tonne product, so transport dominates), "
      f"the same scores give {d['contrast_total']:.1f}. Next door, with a shared border, the cement firm sees little distance; the bookkeeping firm sees more, and it sits in the tax code. "
      "Two judgment calls: Geographic is lowest but not zero (time-zone overlap matters for live calls in tax season), and the Quebec "
      "French issue is scored as a legal (Administrative) fact rather than as Cultural distance.", "small")

    for k in DIMS:
        x = pr["dims"][k]
        block = [Paragraph("2b. Dimension cards (score, indicators, reasoning, sources)", S["h2"])] if k == DIMS[0] else []
        block.append(Paragraph(f"{k} distance: {x['score']:.0f} / 100", S["h3"]))
        tab = [[C("<b>Indicator</b>"), C("<b>US</b>"), C("<b>Canada</b>"), C("<b>Sub</b>"), C("<b>Weight</b>"), C("<b>Status / note</b>")]]
        for c in x["components"]:
            home = "" if c["home"] is None else str(c["home"])
            targ = "" if c["target"] is None else str(c["target"])
            if c["key"] == "religion":
                home, targ = home[:48] + "...", targ[:48] + "..."
            tab.append([C(t(c["indicator"])), C(t(home)), C(t(targ)), C("-" if c["sub"] is None else f"{c['sub']:.0f}"),
                        C(f"{c['weight']:.2f}" + (f" ({c['eff_weight']:.2f})" if abs(c["weight"] - c["eff_weight"]) > 1e-9 else "")),
                        C(("verified" if c["verified"] else "<b>not verified, left out</b>") + (f"; {t(c['note'])}" if c["note"] else ""))])
        block.append(grid(tab, [W * x for x in (0.25, 0.15, 0.18, 0.06, 0.1, 0.26)]))
        block.append(Paragraph("<b>Reasoning.</b> " + " ".join(t(n) for n in x["notes"]), S["small"]))
        if k == "Administrative":
            srcs = "See the fact table in 2c for the industry sources. " + "; ".join(
                a(s["url"], f"{s['publisher']}: {s['title']}") + f" ({t(s['retrieved'])})" for s in sources_of(x)
                if not any(s["url"] == ch["url"] for f in pr["facts"] for ch in f["checks"]))
        else:
            srcs = "; ".join(a(s["url"], f"{s['publisher']}: {s['title']}") + f" ({t(s['retrieved'])})" for s in sources_of(x))
        block.append(Paragraph("<b>Sources.</b> " + srcs, S["small"]))
        story.append(KeepTogether(block[:-2]))   # headings + indicator table stay together; reasoning and sources may flow
        story.extend(block[-2:])

    P("2c. Industry-specific administrative facts (from cage_facts.json; each quote checked against the official page)", "h2")
    tab = [[C("<b>Topic</b>"), C("<b>United States</b>"), C("<b>Canada</b>"), C("<b>Sev. / reach</b>"), C("<b>Official sources</b>")]]
    for f in pr["facts"]:
        status = "" if f["verified"] else "<br/><b>NOT VERIFIED, not scored</b>"
        tab.append([C(f"<b>{t(f['topic'])}</b>{status}"), C(t(f["home"])), C(t(f["target"])), C(f"{f['severity']} / {f['reach']}"),
                    C("; ".join(a(c["url"], c["publisher"]) + ("" if c["ok"] else " <i>(" + t(c["detail"].split(" for url")[0]) + ")</i>")
                           for c in {c["url"]: c for c in f["checks"]}.values()))])
    story.append(grid(tab, [W * x for x in (0.18, 0.22, 0.34, 0.08, 0.18)]))
    P("Severity: 0 same; 1 different rule, same skills; 2 needs separate expertise, a registration or a licence. Reach: all clients (x1) or some (x0.5). "
      f"All facts and quotes are readable in {a(urls['facts'], 'cage_facts.json')}; retrieval date of every page: {t(d['generated'])}.", "small")

    P("2d. Recommendation and the single largest risk", "h2")
    P(f"<b>(1) How significant is the total distance?</b> {md(rec['q1'])}")
    P(f"<b>(2) What should the firm be most cautious about?</b> {md(rec['q2'])}")
    # the hand-written sentences below describe this run's result; refuse to print them if the numbers no longer say so
    assert rec["risk"].startswith("Sales tax") and d["rating"] == "low" and max(sc.values()) < d["thresholds"]["high"] and d["flip"], "re-word 2d/2e for the new results"
    P(f"<b>Single largest risk to flag to leadership: {t(rec['risk'])}.</b> The firm's sales-tax knowledge is American; in Canada it is the core of every "
      "client file and possibly an obligation of the firm itself. Rule that picked it: inside the top-contributing dimension, the risk area with the largest summed "
      "severity x reach among verified facts.")

    P("2e. Sensitivity analysis: does the recommendation change with the weights?", "h2")
    tab = [[C("<b>Scenario</b>"), C("<b>C</b>"), C("<b>A</b>"), C("<b>G</b>"), C("<b>E</b>"), C("<b>Total</b>"), C("<b>Rating</b>"), C("<b>Largest risk</b>")]]
    for s in d["sensitivity"]:
        tab.append([C(t(s["scenario"])), C(f"{s['w_C']:.2f}"), C(f"{s['w_A']:.2f}"), C(f"{s['w_G']:.2f}"), C(f"{s['w_E']:.2f}"),
                    C(f"<b>{s['total']:.1f}</b>"), C(t(s["rating"])), C(t(s["largest_risk"]))])
    story.append(grid(tab, [W * x for x in (0.22, 0.06, 0.06, 0.06, 0.06, 0.08, 0.1, 0.36)]))
    story.append(Spacer(1, 4))
    story.append(img("cage_sensitivity.png", W * 0.68))
    for line in d["flip_text"]:
        P("&bull; " + md(line), "small")
    P("<b>Reading it:</b> the rating is <b>low but borderline</b>. It flips to moderate once Administrative carries about 0.45-0.47 of the weight (from 0.40); no weighting can make it "
      "high, because no single dimension scores 50. The largest risk is the sales-tax regime in every scenario where Administrative contributes most; it changes only when "
      "Cultural or Economic is given 0.70 of the weight.", "small")

    P("2f. Contrast pairs (same code, same rules, same weights)", "h2")
    tab = [[C("<b>Pair</b>")] + [C(f"<b>{k}</b>") for k in DIMS] + [C("<b>Total</b>"), C("<b>Rating</b>"), C("<b>Largest risk</b>")]]
    tab.append([C(f"{t(pr['home_name'])} to {t(pr['target_name'])}")] + [C(f"{sc[k]:.0f}") for k in DIMS] + [C(f"{d['total']:.1f}"), C(d["rating"]), C(t(rec["risk"]))])
    for k, v in d["contrast_pairs"].items():
        tab.append([C(f"{t(v['names'][0])} to {t(v['names'][1])}")] + [C(f"{v['scores'][x]:.0f}") for x in DIMS] + [C(f"{v['total']:.1f}"), C(v["rating"]), C(t(v["risk"]))])
    story.append(grid(tab, [W * x for x in (0.23, 0.08, 0.11, 0.11, 0.08, 0.07, 0.08, 0.24)]))
    P("The UK and Japan fact tables are shorter (5 and 3 facts), so their Administrative scores rest on less evidence. Japan's licensed tax-accountant monopoly and its "
      "foreign-transfer privacy rule are the kind of facts that would push Administrative higher as more are added.", "small")

    P("2g. What could not be verified (left out of every score)", "h2")
    P(" ".join(f"({i}) {t(u)}." for i, u in enumerate(d["unverified"], 1)) +
      f" ({len(d['unverified']) + 1}) World Bank series PA.NUS.PPPC.RF (price level ratio) is archived in the API, so the notebook computes it from PA.NUS.PPP and PA.NUS.FCRF.", "small")

    P("2h. Limits: what this tool cannot see", "h2")
    P("<b>Company-specific factors:</b> it scores countries, not the firm (its people, Canadian expertise, partners, capital, or whether Canadian estheticians want the service). "
      "<b>Regulatory change:</b> the facts are a snapshot of official pages on the retrieval date; it does not watch for new CRA rules, the USMCA joint review, tariffs or "
      "privacy-law changes, and the severities were assigned by hand and need a Canadian tax professional's check. "
      "<b>Rule-based indicators:</b> every score is a deterministic rule on proxies (Hofstede 2015, Factbook religion shares, WGI, World Bank averages); the rules and "
      "sub-weights are visible judgments, not fitted estimates, and national averages hide Quebec. "
      f"<b>Dates:</b> indicators are the latest year both countries report (2022-2025, printed per indicator), Hofstede is a 2015 release, and the Factbook is a frozen "
      f"{t(d['factbook_snapshot'])} snapshot because the CIA retired it. <b>Coverage:</b> only Ontario's accounting law was checked among the provinces, and the OFAC check "
      "matches program names, not the SDN list.", "small")

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

def verify_pdf(path, d, urls):
    from pypdf import PdfReader
    r = PdfReader(str(path))
    FOOT = re.compile(re.escape(f"{TITLE} | {AUTHOR}") + r"\s*Page \d+\s*")
    text = FOOT.sub("", "\n".join((p.extract_text() or "") for p in r.pages))
    T = re.sub(r"\s+", "", text).lower()
    sq = lambda s: re.sub(r"\s+", "", s).lower()
    checks = []
    need = lambda label, cond: checks.append((label, bool(cond)))
    p1 = re.sub(r"\s+", "", FOOT.sub("", r.pages[0].extract_text() or "")).lower()
    need("page-one header: title, author, date placeholder", p1.startswith(sq(TITLE)) and sq(AUTHOR) in p1[:120] and sq(DATE_PLACEHOLDER) in p1[:160])
    heads = ["1. Tool link", "2. Output", "3. Reflection"]
    pos = [T.find(sq(h)) for h in heads]
    need("exactly the three sections, in order", all(p >= 0 for p in pos) and pos == sorted(pos))
    links1 = {str(x.get_object()["/A"]["/URI"]) for x in (r.pages[0].get("/Annots") or []) if x.get_object().get("/A")}
    need("notebook + nbviewer links clickable on page one", urls["notebook"] in links1 and urls["nbviewer"] in links1)
    need("four dimension cards with scores", all(sq(f"{k} distance: {d['scores'][k]:.0f} / 100") in T for k in DIMS))
    need("total and rating printed", sq(f"{d['total']:.1f} ({d['rating']})") in T)
    need("single largest risk printed", sq(f"Single largest risk to flag to leadership: {d['recommendation']['risk']}") in T)
    all_links = {str(x.get_object()["/A"]["/URI"]) for p in r.pages for x in (p.get("/Annots") or []) if x.get_object().get("/A")}
    fact_urls = {c["url"] for f in d["pair"]["facts"] for c in f["checks"]}
    dim_urls = {s["url"] for k in DIMS for c in d["pair"]["dims"][k]["components"] for s in c["sources"]}
    need("every source is a clickable link", fact_urls <= all_links and dim_urls <= all_links)
    need("sensitivity: every scenario printed", all(sq(s["scenario"]) in T for s in d["sensitivity"]))
    need("industry weighting explained (equal + contrast totals)", sq(f"{d['equal_total']:.1f}") in T and sq(f"{d['contrast_total']:.1f}") in T)
    need("limits section", "limits:whatthistoolcannotsee" in T and "company-specificfactors" in T)
    need("both charts embedded", sum(len(p.images) for p in r.pages) >= 2)
    need("three reflection headings", all(sq(h) in T for h in ("What was hardest to build?", "What would you not trust this tool to decide",
                                                               "What did it show you that the framework could not?")))
    need("no personal email in the PDF", not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text))
    return checks, len(r.pages)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo"); ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    repo = args.repo or json.loads((HERE.parent / "submission_config.json").read_text())["repo_url"]
    urls = urls_for(repo)
    d = json.loads((HERE / "cage_results.json").read_text())
    reflection = REFLECTION.read_text()
    build(d, reflection, urls, args.out)
    checks, pages = verify_pdf(args.out, d, urls)
    failed = [c for c in checks if not c[1]]
    print(f"Built {args.out}: {pages} pages; {len(checks)} content checks, {len(checks) - len(failed)} passed.")
    for label, ok in checks:
        if not ok: print("  FAILED:", label)
    if PLACEHOLDER in reflection or DATE_PLACEHOLDER == "[DATE]":
        print(f"  TO DO: replace the reflection placeholders in {REFLECTION.name} and the {DATE_PLACEHOLDER} placeholder (DATE_PLACEHOLDER in this file), then re-run.")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
