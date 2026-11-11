#!/usr/bin/env python3
"""Build the ONE-PDF submission for the Competitor Mapping Tool from results.json + reflection_competitor_map.md, then check it by code.

Run from this folder after executing the notebook:
    python build_pdf.py            -> competitor_map_submission.pdf
Repo URL comes from ../submission_config.json {"repo_url": ...} or --repo URL.

Header (title, author, date placeholder), then exactly three sections, in this order:
    1. Tool link (competitor-map/competitor_map.ipynb on GitHub + nbviewer backup), clickable, at the top of page one
    2. Output: attribute table with sources, dates and missing flags; method; the map; what the axes mean; the groups and their
       stability; the surprise and the hand-drawn comparison; the hypothetical point; what could not be verified; limits
    3. Reflection (three headings, from reflection_competitor_map.md)

Separate from the earlier deliverables' builders; only the shared styling helpers from ../build_pdf.py are reused.
"""
import json, re, sys, math, argparse
from pathlib import Path
from urllib.parse import urlparse
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from build_pdf import clean, md_inline, link, styles, grid, GREY   # shared styling from the first deliverable

OUT = HERE / "competitor_map_submission.pdf"
REFLECTION = HERE / "reflection_competitor_map.md"
TITLE = "Competitor Mapping Tool: Strategic Groups in Small-Business Bookkeeping and Tax"
AUTHOR = "Diggy Smith"
DATE_PLACEHOLDER = "[DATE]"
PLACEHOLDER = "[Replace with your answer"
FORBIDDEN = ["student", "planned", "prompt", "claude", "llm", "chatgpt", "process note"]

def urls_for(repo):
    repo = re.sub(r"\.git$", "", repo.rstrip("/"))
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        sys.exit(f"repo_url must look like https://github.com/USER/REPO, got {repo!r}")
    u, n = m.groups()
    return {"repo": repo, "folder": f"{repo}/tree/main/competitor-map",
            "notebook": f"{repo}/blob/main/competitor-map/competitor_map.ipynb",
            "attributes": f"{repo}/blob/main/competitor-map/attributes.json",
            "nbviewer": f"https://nbviewer.org/github/{u}/{n}/blob/main/competitor-map/competitor_map.ipynb"}

def t(s):
    return clean(str(s)).replace("&amp;middot;", "&middot;")

def md(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t(s))

def a(url, text):
    return f'<a href="{clean(url)}" color="#1a4f8b"><u>{t(text)}</u></a>'

def img(name, width):
    from PIL import Image as PILImage
    w, h = PILImage.open(HERE / name).size
    return Image(str(HERE / name), width=width, height=width * h / w)

def reflection_paragraphs(text):
    return [p.strip() for p in re.sub(r"<!--.*?-->", "", text, flags=re.S).strip().split("\n\n") if p.strip()]

def short_path(u):
    p = urlparse(u)
    path = p.path.strip("/")
    return path.split("/")[-1] or "home"

PRICE_TXT = {"quote_only": "quote only", "no_monthly_plan": "no monthly plan", "not_available": "not available"}

def build(d, reflection, urls, path=OUT):
    S = styles()
    S["cell"].fontSize, S["cell"].leading = 6.9, 8.3
    S["small"].fontSize, S["small"].leading = 7.9, 9.9
    S["body"].fontSize, S["body"].leading = 9.0, 11.6
    W = letter[0] - 1.5 * inch
    story = []
    P = lambda x, s="body": story.append(Paragraph(x, S[s]))
    C = lambda x, s="cell": Paragraph(x, S[s])
    G = {g["id"]: g for g in d["groups"]}
    gid = {f: g["id"] for g in d["groups"] for f in g["firms"]}
    online = gid["Bench"]; books = gid["Merritt Bookkeeping"]; office = gid["Jackson Hewitt"]
    drop = {r["attribute dropped"]: r for r in d["drop"]}
    mine = d["mine"]
    # the sentences below describe this run's result; refuse to print them if the numbers no longer say so
    assert d["k"] == 3 and gid["Liberty Tax"] == gid["Fiducial"] == office and gid["Complete Controller"] == books
    assert len({gid[f] for f in ("Kopsa Otte CPAs & Advisors", "Remote Books Online", "Acuity", "Monaco CPA", "Pilot")}) == 1
    assert drop["niche"]["ARI vs full fit"] > 0.999 and all(m["group_name"].startswith("bookkeeping only") for m in mine)

    # ---------------------------------------------------------------- header
    from reportlab.lib.styles import ParagraphStyle
    story.append(Paragraph(f"<b>{t(TITLE)}</b>", ParagraphStyle("title", parent=S["body"], fontSize=15, leading=19, spaceAfter=2)))
    P(f"{AUTHOR} &nbsp;&middot;&nbsp; {DATE_PLACEHOLDER}", "body")

    # ---------------------------------------------------------------- 1
    P("1. Tool link", "h1")
    P(f"<b>Notebook (GitHub, no login, outputs saved):</b> {link(urls['notebook'])}")
    P(f"<b>Backup viewer (nbviewer):</b> {link(urls['nbviewer'])}")
    P(f"Folder with the input list, the cited attribute file {a(urls['attributes'], 'attributes.json')}, the page cache and this builder: "
      f"{link(urls['folder'])}. Edit the competitor list at the top of the notebook to map any set of firms.", "small")

    # ---------------------------------------------------------------- 2
    P("2. Output", "h1")
    P(f"<b>Industry:</b> bookkeeping, tax and advisory services for US small businesses. <b>Input:</b> {d['n_input']} firms (the four from the "
      f"earlier NPS scorer plus national online services, tax-prep chains, advisory firms and salon/spa specialists). {d['pages_read']} of "
      f"{d['pages_total']} public pages could be read (retrieved {', '.join(d['retrieved'])}); {d['quotes_checked']} quotes behind the values were "
      f"re-checked against the cached pages, all found. <b>{d['n_fit']} firms are fitted</b>; six are shown but not fitted (below).", "small")

    P("2a. Attribute table (every competitor; * = imputed for the fit; - = missing)", "h2")
    hdr = ["Firm", "Grp", "Start price /mo", "Services (of 15)", "Walk-in locations", "Channel", "Beauty niche", "Files tax", "Reviews (score, n, source)"]
    tab = [[C(f"<b>{h}</b>") for h in hdr]]
    rows = sorted(d["table"], key=lambda r: (not r["fitted"], r["group"] or 9, r["firm"]))
    for r in rows:
        imp = set(r["imputed"])
        has_price = isinstance(r["price"], (int, float)) and not math.isnan(r["price"])
        price = f"${r['price']:,.0f}" if has_price else PRICE_TXT.get(r["price_status"], "-")
        if any("price" in i for i in imp): price += "*"
        br = "-" if r["breadth"] is None else str(r["breadth"])
        if any("breadth" in i for i in imp) or (r["fitted"] and r["breadth"] is None): br += "*"
        loc = "-" if r["locations"] is None else f"{r['locations']:,}"
        if r["fitted"] and r["locations"] is None: loc += "*"
        ch = "-" if not r["channel"] else r["channel"] + (" (inferred)" if r["channel_basis"] == "inferred" else "")
        yn = lambda v: "-" if v is None else ("yes" if v else "no")
        ni = yn(r["niche"]) + ("*" if r["fitted"] and r["niche"] is None else "")
        rv = "-" if r["review_score"] is None and r["review_count"] is None else \
            f"{r['review_score'] if r['review_score'] is not None else '-'}, {r['review_count']:,}" if r["review_count"] else f"{r['review_score']}, n -"
        if rv != "-" and r["review_source"]:
            rv += f" ({r['review_source'].replace(' via firm site', ', firm site').replace('nps-scorer (Google Maps, read 2026-10-08)', 'NPS scorer')})"
        firm = t(r["firm"]) if r["fitted"] else f"<i>{t(r['firm'])}</i>: {t(r['status'])}"
        tab.append([C(firm), C(str(r["group"] or "")), C(t(price)), C(br), C(loc), C(t(ch)), C(ni), C(yn(r["files_tax"])), C(t(rv))])
    story.append(grid(tab, [W * x for x in (0.2, 0.04, 0.1, 0.07, 0.08, 0.1, 0.07, 0.06, 0.28)]))
    P("<b>Definitions.</b> Price: lowest posted monthly price for a recurring plan (Acuity: lowest example client on its pricing page). Services: hits on a "
      "15-item checklist defined in code (bookkeeping, cleanup, payroll, business and individual returns, tax planning, CFO/forecasting, sales tax, "
      "entity setup, loan-readiness, bill pay, 1099s, IRS notices, HR, R&amp;D credits), counted only in short listing lines. Walk-in locations: offices the firm "
      "states (online firms with no office listed = 0). Channel: online / hybrid / office network. Beauty niche: a page or section addressed to salons, "
      "spas or beauty businesses. Files tax: the firm says it prepares or files returns. Reviews: the earlier NPS scorer's Google Maps data, otherwise "
      "the rating the firm shows on its own site (self-selected).", "small")
    src = []
    for r in rows:
        if not r["sources"]:
            continue
        dates = sorted({s["retrieved"] for s in r["sources"] if s["retrieved"]})
        src.append(f"<b>{t(r['firm'])}</b> ({', '.join(dates)}): " + ", ".join(a(s["url"], short_path(s["url"])) for s in r["sources"]))
    P("<b>Sources (each value's page, retrieval date in brackets; every link is the page the value was read from):</b> " + "; ".join(src) +
      ". Kopsa Otte and Xendoo review counts: nps-scorer/nps_data.json (Google Maps, read 2026-10-08).", "small")

    P("2b. Method, and why", "h2")
    imp_price = sum(1 for i in d["imputed"] if "price" in i["feature"])
    P(f"<b>Features.</b> Seven attributes were gathered; reviews were missing for {d['attr_share']['reviews']:.0%} of operating firms and, by the stated rule "
      "(an attribute missing for more than half the firms is dropped and only shown), are left out of the fit. The fit uses seven columns: log10 starting price, "
      "a <i>publishes a monthly price</i> flag, service count, log10(1 + walk-in locations), channel (0 online, 1 hybrid, 2 office), beauty niche (0/1) and "
      f"files tax (0/1). Logs, because prices run $85-$750 and locations 0-5,100. <b>Missing cells:</b> the {imp_price} firms with no posted monthly price "
      "get the median price <i>and</i> the flag, so quote-only and per-return pricing stays visible rather than silently filled; "
      f"{len(d['imputed']) - imp_price} other cells were imputed (median, or most common value for yes/no) and are starred above. A firm missing more than two "
      "attributes is not fitted. All columns are <b>standardized</b>, because otherwise the column with the widest raw range would dominate.", "small")
    sil = d["silhouette"]
    P(f"<b>PCA</b> on the standardized columns finds the two directions of greatest spread (explained variance: PC1 {d['evr'][0]:.0%}, PC2 {d['evr'][1]:.0%}, "
      f"together {d['evr'][0] + d['evr'][1]:.0%}). <b>k-means</b> (50 random starts per k) runs on all seven columns, not just two PCs, so no information is "
      f"discarded. The map is a view of the result. <b>k</b> is the highest mean silhouette among k = 2-6 with every group of two or more firms "
      f"(k = 7-8 score {sil['7']:.2f}-{sil['8']:.2f} but are mostly pairs, which describe firms, not groups): <b>k = {d['k']}, silhouette "
      f"{sil[str(d['k'])]:.2f}</b>, with the elbow bending at the same k. <b>Ward hierarchical clustering</b> on the same data gives the identical "
      f"partition (adjusted Rand index {d['ari_hc']:.2f}). The silhouette and elbow charts are in 2e.", "small")
    story.append(KeepTogether([Paragraph("2c. The map", S["h2"]), img("competitor_map.png", W * 0.78)]))
    P("Stars: Fine Line Financials, a <b>hypothetical</b> point at three prices, projected with the already-fitted scaler and PCA. Its values are assumptions, "
      "not data, and it took no part in the fit.", "small")

    P("2d. What the two axes represent (from the loadings)", "h2")
    L = d["loadings"]
    tab = [[C("<b>Feature</b>"), C("<b>PC1</b>"), C("<b>PC2</b>")]] + [[C(t(k)), C(f"{v['PC1']:+.2f}"), C(f"{v['PC2']:+.2f}")] for k, v in L.items()]
    lt = grid(tab, [W * 0.3, W * 0.07, W * 0.07])
    txt = Paragraph(
        f"<b>PC1 ({d['evr'][0]:.0%}): physical presence and how the firm prices.</b> High on walk-in locations and an office channel; low on posting a "
        "monthly price and on service count. Right = branch networks that sell tax returns one at a time (Jackson Hewitt, Liberty Tax, Fiducial); "
        "left = online firms with a posted subscription and a longer service list.<br/><br/>"
        f"<b>PC2 ({d['evr'][1]:.0%}): how far the firm goes past the books.</b> High on filing tax returns, starting price and service count (and "
        "weakly on beauty niche). Bottom = bookkeeping only, cheap (Merritt, Complete Controller); top = firms that also prepare returns, charge more and "
        "list more (Acuity, Kruze, Monaco CPA, Bookkeeper360).", S["small"])
    from reportlab.platypus import Table
    story.append(Table([[lt, txt]], colWidths=[W * 0.46, W * 0.54], style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 8)]))

    P("2e. The groups, how k was chosen, and how stable they are", "h2")
    story.append(img("k_selection.png", W * 0.62))
    for g in d["groups"]:
        P(f"&bull; <b>Group {g['id']}, {t(g['name'])} ({len(g['firms'])}):</b> {t(', '.join(g['firms']))}.", "small")
    tab = [[C("<b>Attribute dropped</b>"), C("<b>ARI vs full fit</b>"), C("<b>Firms that switch group</b>")]]
    for r in d["drop"]:
        tab.append([C(t(r["attribute dropped"])), C(f"{r['ARI vs full fit']:.2f}"), C(t(r["firms that switch group"]))])
    story.append(grid(tab, [W * 0.16, W * 0.12, W * 0.72]))
    P(f"<b>Reading it:</b> silhouette {sil[str(d['k'])]:.2f} is weak-to-moderate structure. The two small groups stand clearly apart; the online group is a loose "
      f"cloud. The groups hold when service count, niche or price is dropped, and change when <b>files tax</b> (ARI {drop['files_tax']['ARI vs full fit']:.2f}) "
      f"or <b>footprint</b> ({drop['footprint']['ARI vs full fit']:.2f}) is dropped: those two attributes carry the grouping. Seeds: with 50 starts every seed gives the "
      f"same groups; with a single start only {d['seed_same_1start']:.0%} of 100 seeds do, so the answer depends on enough restarts. Firms that move most: "
      f"{t(', '.join(f'{k} ({v} of 6)' for k, v in sorted(d['switch'].items(), key=lambda x: -x[1])[:4]))}.", "small")

    P("2f. The grouping that surprised me, and the groups I would have drawn by hand", "h2")
    P("<b>The beauty specialists do not form a group of their own.</b> Kopsa Otte (salons and spas for over 40 years), Remote Books Online, Acuity and Monaco CPA "
      "all have salon or spa pages, and I expected them to cluster. Instead they sit inside the online group next to startup specialists like Pilot and Kruze, "
      f"and dropping the niche column moves no firm at all (ARI {drop['niche']['ARI vs full fit']:.2f}). The tree does put the four on one branch, but it only splits "
      f"off at k = 4, where the silhouette falls to {sil['4']:.2f}: a sub-niche inside the online group, not a separate strategic group. On these attributes, "
      "serving salons is a marketing page on an ordinary online bookkeeping-and-tax model.", "small")
    h = d["hand"]
    tab = [[C("<b>Drawn by hand (before the fit)</b>")] + [C(f"<b>{c}</b>") for c in h["cols"]]] + \
          [[C(t(r))] + [C(str(v)) for v in vals] for r, vals in zip(h["rows"], h["values"])]
    story.append(grid(tab, [W * 0.3] + [W * 0.1] * len(h["cols"])))
    P(f"Agreement with my hand-drawn groups is low (adjusted Rand {d['ari_hand']:.2f}). The data keeps one of my lines (tax-prep chains), adds one I did not draw "
      "(bookkeeping only), and merges my online, advisory and beauty groups into one. I sorted firms by <b>who they sell to</b>; the data sorts them by "
      "<b>what they sell and how they deliver it</b>. Either public attributes cannot see customer focus, or, more likely, the online segment is one crowded "
      "strategic group whose members differ mainly in marketing. That says the industry is legible on business model and illegible on target customer.", "small")

    P("2g. Fine Line Financials as a hypothetical point (assumptions, not data)", "h2")
    P(f"Assumed: monthly price $125 / $200 / $350; price posted publicly; service count {d['my_breadth']} (bookkeeping, cleanup, business setup, run through "
      "the same checklist); no walk-in location; online; beauty niche = yes; files tax returns = no.", "small")
    tab = [[C("<b>Scenario</b>"), C("<b>PC1</b>"), C("<b>PC2</b>"), C("<b>Nearest group</b>"), C("<b>Three nearest competitors (distance)</b>")]]
    for m in mine:
        tab.append([C(f"${m['price']}/mo"), C(f"{m['pc1']:.2f}"), C(f"{m['pc2']:.2f}"), C(f"{m['group'] + 1}: {t(m['group_name'])}"),
                    C(t(", ".join(f"{n} ({x})" for n, x in zip(m["neighbours"], m["nn_dist"]))))])
    story.append(grid(tab, [W * 0.1, W * 0.07, W * 0.07, W * 0.28, W * 0.48]))
    P(f"At every price the point lands nearest the bookkeeping-only group, because it does not file returns. Its nearest competitor is "
      f"{min(m['nn_dist'][0] for m in mine):.1f}-{max(m['nn_dist'][0] for m in mine):.1f} away, against a typical competitor-to-nearest-competitor distance of "
      f"{d['nn_median']:.1f}, so it sits in <b>open space</b>: no fitted firm combines a beauty niche, no tax filing and a posted price. Raising the price from $125 "
      f"to $350 moves it {mine[-1]['pc2'] - mine[0]['pc2']:.1f} units up PC2 toward the full-service online firms (distance to that group's centre "
      f"{mine[0]['d_centres'][online - 1]:.2f} to {mine[-1]['d_centres'][online - 1]:.2f}) without changing its nearest group. On these attributes, the "
      "no-tax-filing decision places the firm more than its price does. At $350 it is priced like the full-service firms while offering what the "
      "bookkeeping-only firms offer.", "small")

    P("2h. What could not be verified", "h2")
    P("<b>Not readable, so shown but not fitted:</b> Xendoo (from the NPS list; every page answers HTTP 403 to a plain request; only its 177 Google reviews are "
      "used), Block Advisors (H&amp;R Block), Padgett Business Services and Straight Talk CPAs (HTTP 403; not retried with another client). "
      "<b>Dropped as defunct:</b> Elite Business Solutions (domain for sale) and Jasmine Thomas &amp; Associates (parked domain), both from the NPS list. "
      "<b>Missing cells:</b> prices for Kopsa Otte and QuickBooks Live (services page 403; price not in the page HTML), Ignite Spot and Decimal (quote only); "
      "QuickBooks Live's office count; Complete Controller's salon page (403); Kopsa Otte's and inDinero's service counts (services pages 403); and "
      "review scores for 14 of 20 fitted firms (Trustpilot, G2, Capterra and BBB refuse plain requests). A salon-finance firm found in a search could not be "
      "located at any working domain and was left out. Firm-displayed ratings could not be checked against the rating sites themselves.", "small")

    P("2i. Limits", "h2")
    for l in d["limits"]:
        P("&bull; " + md(l), "small")

    # ---------------------------------------------------------------- 3
    story.append(Spacer(1, 4))
    P("3. Reflection", "h1")
    for para in reflection_paragraphs(reflection):
        P(md_inline(para))

    def footer(canvas, doc_):
        canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GREY)
        canvas.drawString(0.75 * inch, 0.45 * inch, f"Competitor Mapping Tool | {AUTHOR}")
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc_.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.55 * inch,
                            bottomMargin=0.7 * inch, title=TITLE, author=AUTHOR)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

def verify_pdf(path, d, urls, reflection):
    from pypdf import PdfReader
    r = PdfReader(str(path))
    FOOT = re.compile(re.escape(f"Competitor Mapping Tool | {AUTHOR}") + r"\s*Page \d+\s*")
    text = FOOT.sub("", "\n".join((p.extract_text() or "") for p in r.pages))
    T = re.sub(r"\s+", "", text).lower()
    sq = lambda s: re.sub(r"\s+", "", s).lower()
    checks = []
    need = lambda label, cond: checks.append((label, bool(cond)))
    p1 = re.sub(r"\s+", "", FOOT.sub("", r.pages[0].extract_text() or "")).lower()
    need("page-one header: title, author, date placeholder", p1.startswith(sq(TITLE)[:40]) and sq(AUTHOR) in p1[:200] and sq(DATE_PLACEHOLDER) in p1[:220])
    pos = [T.find(sq(h)) for h in ("1. Tool link", "2. Output", "3. Reflection")]
    need("exactly the three sections, in order", all(p >= 0 for p in pos) and pos == sorted(pos))
    links1 = {str(x.get_object()["/A"]["/URI"]) for x in (r.pages[0].get("/Annots") or []) if x.get_object().get("/A")}
    need("notebook + nbviewer links clickable on page one", urls["notebook"] in links1 and urls["nbviewer"] in links1)
    all_links = {str(x.get_object()["/A"]["/URI"]) for p in r.pages for x in (p.get("/Annots") or []) if x.get_object().get("/A")}
    need("every source URL is a clickable link", {s["url"] for row in d["table"] for s in row["sources"]} <= all_links)
    need("every competitor in the attribute table", all(sq(clean(row["firm"]).replace("&amp;", "&"))[:12] in T for row in d["table"]))
    need("PCA variance and k/silhouette printed", sq(f"k = {d['k']}, silhouette {d['silhouette'][str(d['k'])]:.2f}") in T and sq(f"PC1 {d['evr'][0]:.0%}") in T)
    need("both charts embedded (k selection, map)", sum(len(p.images) for p in r.pages) >= 2)
    need("axes explained, surprise, hand comparison, hypothetical, limits", all(sq(h) in T for h in (
        "What the two axes represent", "surprised me", "drawn by hand", "hypothetical point", "Limits")))
    need("three reflection headings", all(sq(h) in T for h in ("What was hardest to build?", "What would you not trust this tool to decide",
                                                               "What did it show you that the framework could not?")))
    need("no email address in the PDF", not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text))
    low = text.lower()
    bad = [w for w in FORBIDDEN if low.count(w) > reflection.lower().count(w)]
    need(f"no process/prompt words outside the reflection placeholders ({', '.join(FORBIDDEN)})", not bad)
    return checks, len(r.pages), bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo"); ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    repo = args.repo or json.loads((HERE.parent / "submission_config.json").read_text())["repo_url"]
    urls = urls_for(repo)
    d = json.loads((HERE / "results.json").read_text())
    reflection = REFLECTION.read_text()
    build(d, reflection, urls, args.out)
    checks, pages, bad = verify_pdf(args.out, d, urls, reflection)
    failed = [c for c in checks if not c[1]]
    print(f"Built {args.out}: {pages} pages; {len(checks)} content checks, {len(checks) - len(failed)} passed.")
    for label, ok in checks:
        if not ok: print("  FAILED:", label, bad if "process" in label else "")
    if PLACEHOLDER in reflection or DATE_PLACEHOLDER == "[DATE]":
        print(f"  TO DO: replace the reflection placeholders in {REFLECTION.name} and the {DATE_PLACEHOLDER} placeholder (DATE_PLACEHOLDER in this file), then re-run.")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
