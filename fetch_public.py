#!/usr/bin/env python3
"""Stage 3 enrichment: fetch PUBLIC sources, extract plain text, cache it.

Each source is fetched once with `requests`, converted to text (BeautifulSoup, scripts/nav stripped), and written to
    public_sources/<source_id>.txt           (the text the verifier matches quotes against)
    public_sources/index.json                (URL, fetch URL, access date, sha256, kind, licence note)
Government documents (BLS, SBA, SEC filings) are U.S. public records and are committed in full. For commercial pages
(company marketing, trade press) only the paragraphs around each cited quote are committed (written by five_forces.ipynb, Stage 3),
so the repository does not republish someone else's article; the sha256 of the full fetched text is still recorded.

Usage:  python fetch_public.py            fetch anything not already cached
        python fetch_public.py --refresh  re-fetch everything
No API key, no paid service. SEC asks for a descriptive User-Agent; BLS blocks scripted requests, so the BLS page is
fetched from the Internet Archive's snapshot of the same URL (recorded as fetch_url; the cited source is still BLS).
"""
import json, os, re, sys, hashlib, datetime
import requests
from bs4 import BeautifulSoup

OUT = "public_sources"
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
SEC_UA = "fcfo-pipeline coursework research contact@example.org"   # SEC requires "name email"; placeholder contact

SOURCES = [
    {"source_id": "bls_ooh_accountants", "kind": "government",
     "title": "Occupational Outlook Handbook: Accountants and Auditors", "publisher": "U.S. Bureau of Labor Statistics",
     "url": "https://www.bls.gov/ooh/business-and-financial/accountants-and-auditors.htm",
     "fetch_url": "https://web.archive.org/web/20260926192746id_/https://www.bls.gov/ooh/business-and-financial/accountants-and-auditors.htm"},
    {"source_id": "sec_cbiz_10k_fy2025", "kind": "government",
     "title": "CBIZ, Inc. Form 10-K for fiscal year ended Dec 31, 2025 (filed 2026-02-26)", "publisher": "SEC EDGAR (CIK 0000944148)",
     "url": "https://www.sec.gov/Archives/edgar/data/944148/000094414826000038/cbz-20251231.htm"},
    {"source_id": "sba_advocacy_faq_2026", "kind": "government",
     "title": "Frequently Asked Questions About Small Business (January 2026)", "publisher": "U.S. SBA Office of Advocacy",
     "url": "https://advocacy.sba.gov/wp-content/uploads/2026/02/FINAL_FAQsAboutSmallBusiness_2026_012826.pdf"},
    {"source_id": "cfodive_aicpa_trends_2025", "kind": "commercial",
     "title": "US accounting degree graduates drop 6.6% (coverage of AICPA 2025 Trends report)", "publisher": "CFO Dive (trade press)",
     "url": "https://www.cfodive.com/news/us-accounting-degree-graduates-drop-talent-shortage/803914/"},
    {"source_id": "intuit_ai_agents_2025", "kind": "commercial",
     "title": "Intuit Introduces Ground-Breaking Virtual Team of AI Agents to Fuel Growth for Businesses", "publisher": "Intuit Inc. (press release)",
     "url": "https://investors.intuit.com/news-events/press-releases/detail/1258/intuit-introduces-ground-breaking-virtual-team-of-ai-agents-to-fuel-growth-for-businesses"},
    {"source_id": "pilot_cfo_services", "kind": "commercial",
     "title": "Pilot: CFO services (vendor marketing page)", "publisher": "Pilot.com",
     "url": "https://pilot.com/cfo-services"},
    {"source_id": "techcrunch_bench_2024", "kind": "commercial",
     "title": "Bench shuts down, leaving thousands of businesses without access to accounting and tax docs", "publisher": "TechCrunch (trade press), 2024-12-27",
     "url": "https://techcrunch.com/2024/12/27/bench-shuts-down-leaving-thousands-of-businesses-without-access-to-accounting-and-tax-docs/"},
]

def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form"]):
        t.decompose()
    for t in soup.find_all(style=re.compile(r"display:\s*none")):
        t.decompose()                                    # iXBRL hidden facts in SEC filings
    text = soup.get_text("\n")
    text = text.replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in text.split("\n")]
    out, blank = [], False
    for l in lines:
        if l:
            out.append(l); blank = False
        elif not blank:
            out.append(""); blank = True
    return "\n".join(out).strip()

def pdf_to_text(content):
    import io, pdfplumber
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        out = []
        for i, p in enumerate(pdf.pages, 1):
            w = p.width / 2                        # two-column layouts interleave; keep a column-by-column copy too
            cols = [(p.crop((0, 0, w, p.height)).extract_text() or ""), (p.crop((w, 0, p.width, p.height)).extract_text() or "")]
            out.append(f"[page {i}]\n" + (p.extract_text() or "") + "\n[columns]\n" + "\n".join(cols))
        return "\n\n".join(out)

def fetch(src, tries=4):
    import time
    url = src.get("fetch_url", src["url"])
    ua = SEC_UA if "sec.gov" in url else ("curl/8.7.1" if "web.archive.org" in url else BROWSER_UA)
    for k in range(tries):
        r = requests.get(url, headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/pdf",
                                       "Accept-Language": "en-US,en;q=0.9"}, timeout=90)
        if r.status_code == 429 and k < tries - 1:          # Internet Archive rate limit: back off and retry
            time.sleep(15 * (k + 1)); continue
        r.raise_for_status(); break
    if not r.headers.get("content-type", "").lower().count("charset"):
        r.encoding = "utf-8"                              # archive raw snapshots omit the charset
    if url.lower().endswith(".pdf") or r.headers.get("content-type", "").startswith("application/pdf"):
        return pdf_to_text(r.content)
    return html_to_text(r.text)

def full_path(sid):   # full text of commercial pages stays local (cache/ is git-ignored)
    return os.path.join("cache", "public_full", sid + ".txt")

def main():
    refresh = "--refresh" in sys.argv
    os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.dirname(full_path("x")), exist_ok=True)
    idx_path = os.path.join(OUT, "index.json")
    index = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    for src in SOURCES:
        sid = src["source_id"]
        if sid in index and os.path.exists(full_path(sid)) and not refresh:
            print(f"cached   {sid}"); continue
        try:
            text = fetch(src)
        except Exception as e:
            print(f"FAILED   {sid}: {e}"); continue
        open(full_path(sid), "w").write(text)
        index[sid] = {**src, "accessed": datetime.date.today().isoformat(),
                      "sha256_full_text": hashlib.sha256(text.encode()).hexdigest()[:16], "chars_full_text": len(text),
                      "committed_text": "full" if src["kind"] == "government" else "excerpts around cited quotes only"}
        if src["kind"] == "government":
            open(os.path.join(OUT, sid + ".txt"), "w").write(text)
        print(f"fetched  {sid}: {len(text):,} chars")
    json.dump(index, open(idx_path, "w"), indent=1)

if __name__ == "__main__":
    main()
