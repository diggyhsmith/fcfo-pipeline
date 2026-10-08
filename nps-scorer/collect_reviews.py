#!/usr/bin/env python3
"""Collect public reviews for the four named competitors and cache them to nps-scorer/cache/<slug>.json.

Source priority (same for every company, so the numbers are comparable):
    1. Trustpilot  - checked for every company first. Used only if the page has >= 15 reviews.
    2. Google Maps - fallback. Loaded in a real headless browser (Playwright), because the public Places API
                     returns at most 5 "most relevant" reviews per listing. Logged out, Google Maps shows a
                     "limited view": the star histogram for EVERY review on the listing (Google's own count per
                     star level) but only ~3-6 itemized reviews; sorting, filters and "More reviews" require
                     sign-in, which this tool does not do. Both the histogram and every itemized review that
                     can be displayed are recorded.
    3. Yelp        - checked where the company itself linked a Yelp page; Yelp answers automated browsers
                     with HTTP 403, so it is logged as blocked, not worked around.

Nothing is estimated. A review is cached only if its star rating was read off the page. Reviewer names are
NOT stored (not needed to trace a quote); each review keeps Google's review id, its stars, relative date,
text, and the listing URL it came from.

Run:  ~/.venvs/fcfo/bin/python collect_reviews.py         (about 2-3 minutes; pauses 3-5 s between page loads)
"""
import json, re, sys, time, random, datetime as dt, urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
TRUSTPILOT_MIN = 15

# How each company was located. "google" is the URL that identifies the listing; the notes say why that
# listing is the right business (identity is checked again against the page's own name/address below).
COMPANIES = [
    {"slug": "kopsa_otte", "name": "Kopsa Otte CPAs and Advisors", "website": "kopsaotte.com",
     "trustpilot_domains": ["kopsaotte.com"],
     "google": "https://www.google.com/maps/place/Kopsa+Otte+Associates+LLC/data=!4m2!3m1!1s0x8797455fcd1efb2f:0x9ff9f165e1ba1ca0?hl=en",
     # found via google.com/maps/search/Kopsa+Otte+CPAs+York+NE; place id pinned so reruns hit the same listing
     "expect": {"name_has": "Kopsa Otte", "address_has": "306 E 7th St, York, NE"},
     "identity_note": "Google listing 'Kopsa Otte Associates LLC' at 306 E 7th St, York, NE 68467, phone (402) 362-6636, "
                      "website kopsaotte.com; the same street address and phone are printed on kopsaotte.com."},
    {"slug": "xendoo", "name": "Xendoo", "website": "xendoo.com",
     "trustpilot_domains": ["xendoo.com"],
     "google": "https://www.google.com/maps/place/Xendoo+Online+Accounting,+Bookkeeping+%26+Tax/data=!4m2!3m1!1s0x88d903cf576518a5:0xb0f2c0ddeab13955?hl=en",
     # found via google.com/maps/search/Xendoo+Fort+Lauderdale; place id pinned so reruns hit the same listing
     "expect": {"name_has": "Xendoo", "address_has": "6700 N Andrews Ave"},
     "identity_note": "Google listing 'Xendoo Online Accounting, Bookkeeping & Tax' at 6700 N Andrews Ave #300, Fort "
                      "Lauderdale, FL (company HQ), website xendoo.com. Reviews are firm-wide, not limited to the Beauty & "
                      "Wellness vertical; Google does not separate them."},
    {"slug": "elite_business_solutions", "name": "Elite Business Solutions", "website": "elitebsolutions.com",
     "trustpilot_domains": ["elitebsolutions.com"],
     "google": "https://g.page/r/CSFYh8dP9I-0EAg",
     "expect": {"name_has": "Elite Business", "address_has": ""},
     "yelp": "https://www.yelp.com/biz/elite-business-solutions-albany",
     "identity_note": "elitebsolutions.com now redirects to a domain-for-sale page. The archived site (Wayback Machine, "
                      "2023-06-13) lists Albany, NY and (518) 243-8722 and links its own 'leave a Google review' button to "
                      "g.page/r/CSFYh8dP9I-0EAg, which resolves to 'Elite Business Accounting Solutions, Inc.' (Odessa, FL, "
                      "marked Permanently closed). That self-linked listing is used. A same-name Omaha firm on Google "
                      "(elitesolutionsomaha.com) is a different business and was NOT used."},
    {"slug": "jasmine_thomas", "name": "Jasmine Thomas & Associates", "website": "jasminethomasassociates.com",
     "trustpilot_domains": ["jasminethomasassociates.com"],
     "google": None,
     "google_searches": ["https://www.google.com/maps/search/Jasmine+Thomas+%26+Associates/@43.0731,-89.4012,12z?hl=en",
                         "https://www.google.com/maps/search/Jasmine+Thomas+accountant/@43.0731,-89.4012,12z?hl=en",
                         "https://www.google.com/maps/search/Jasmine+Thomas+%26+Associates+LLC?hl=en"],
     "identity_note": "Madison, WI beauty-industry accountant (Brava Magazine profile, 2024-09-11; phone 779-236-6330). "
                      "jasminethomasassociates.com is now a GoDaddy parked page. No Google Maps listing under the firm's "
                      "name exists near Madison; the only 'Jasmine Thomas' tax listing Google returns is a permanently "
                      "closed TurboTax preparer in Oakbrook Terrace, IL with no reviews, which is not this firm."},
]

def pause(lo=3.0, hi=5.0):
    time.sleep(random.uniform(lo, hi))

def check_trustpilot(page, domain):
    """Return {url, status, exists, review_count} from Trustpilot's server-rendered page data."""
    url = f"https://www.trustpilot.com/review/{domain}"
    for attempt in range(3):                      # Trustpilot's WAF 403s the first hit now and then
        r = page.goto(url, wait_until="domcontentloaded", timeout=60000)
        status = r.status if r else None
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page.content(), re.S)
        if status == 404:
            return {"url": url, "http_status": 404, "exists": False, "review_count": 0}
        if m:
            pp = json.loads(m.group(1))["props"]["pageProps"]
            bu = pp.get("businessUnit") or {}
            if bu:
                return {"url": url, "http_status": status, "exists": True, "display_name": bu.get("displayName"),
                        "claimed": bu.get("isClaimed"), "review_count": bu.get("numberOfReviews", 0),
                        "language_filter": (pp.get("filters") or {}).get("selected", {}).get("languages")}
        pause(6, 9)
    return {"url": url, "http_status": status, "exists": None, "review_count": None, "note": "blocked after 3 tries"}

def check_yelp(page, url):
    r = page.goto(url, wait_until="domcontentloaded", timeout=60000)
    return {"url": url, "http_status": r.status if r else None,
            "note": "Yelp returns 403 to automated browsers; not worked around" if r and r.status == 403 else ""}

def place_header(page):
    g = lambda sel, attr=None: (page.query_selector(sel).get_attribute(attr) if attr else page.query_selector(sel).inner_text()) \
        if page.query_selector(sel) else None
    body = page.inner_text("body")
    return {"name": g("h1.DUwDvf"), "rating_line": (g("div.F7nice") or "").replace("\n", " "),
            "address": (g("button[data-item-id='address']", "aria-label") or "").replace("Address: ", "").strip(),
            "website": (g("a[data-item-id='authority']", "aria-label") or "").replace("Website: ", "").strip(),
            "permanently_closed": "Permanently closed" in body, "final_url": page.url}

def read_reviews(page, url, how):
    """Every itemized review currently rendered. A review is kept only if its star rating is on the page."""
    for b in page.query_selector_all("button.w8nwRe"):            # expand "More" so text is complete
        try: b.click(); time.sleep(0.2)
        except Exception: pass
    out = []
    for el in page.query_selector_all("div.jftiEf[data-review-id]"):
        star = el.query_selector("span.kvMYJc")
        sm = re.match(r"\s*(\d)", (star.get_attribute("aria-label") or "") if star else "")
        if not sm:                                                # never guess a rating that was not on the page
            continue
        txt, date = el.query_selector("span.wiI7pd"), el.query_selector("span.rsqaWe")
        out.append({"review_id": el.get_attribute("data-review-id"), "stars": int(sm.group(1)),
                    "date_relative": date.inner_text() if date else None,
                    "text": txt.inner_text().strip() if txt else "",
                    "owner_replied": bool(el.query_selector("div.CDe7pd")),
                    "how_surfaced": how, "source": "Google Maps", "source_url": url})
    return out

def scroll_overview(page, times=4):
    pane = page.query_selector("div.m6QErb.DxyBCb")
    for _ in range(times):
        if pane: pane.evaluate("el => el.scrollTo(0, el.scrollHeight)")
        time.sleep(random.uniform(1.8, 2.6))

def scroll_until_stable(page, max_scrolls=150, patience=5):
    """Scroll the review list until no new reviews load `patience` times in a row (2-3 s between scrolls)."""
    seen, still = -1, 0
    for _ in range(max_scrolls):
        for pane in page.query_selector_all("div.m6QErb.DxyBCb"):
            pane.evaluate("el => el.scrollTo(0, el.scrollHeight)")
        time.sleep(random.uniform(2.0, 3.0))
        n = len(page.query_selector_all("div.jftiEf[data-review-id]"))
        still = still + 1 if n == seen else 0
        seen = n
        if still >= patience:
            break

def scrape_google_with_retry(page, url, expect, tries=3):
    """Google's logged-out page sometimes renders partially (no rating line or histogram); reload and retry."""
    for i in range(tries):
        hdr, reviews = scrape_google(page, url, expect)
        if hdr.get("listed_review_count") and hdr.get("star_histogram"):
            return hdr, reviews
        print(f"  partial render on try {i + 1}; retrying"); pause(8, 12)
    return hdr, reviews

def scrape_google(page, url, expect):
    """Logged-out Google Maps is a 'limited view': it renders Google's star histogram for ALL reviews on the
    listing, but itemizes only ~3 reviews, plus one review behind each 'review summary' snippet. Sorting,
    topic filters, the Reviews tab list and 'More reviews' all open a sign-in wall. So we record (a) the
    histogram, which is Google's own count of every rating on the listing, and (b) every itemized review
    that can be displayed without signing in."""
    page.goto(url, wait_until="domcontentloaded", timeout=60000); pause(6, 8)
    if page.query_selector("form[action*='consent']"):          # EU-style consent wall; not expected from the US
        page.click("button:has-text('Accept all')"); pause()
    if not page.query_selector("h1.DUwDvf"):                     # search page: open the top result
        first = page.query_selector("div[role='feed'] a.hfpxzc")
        if first: first.click(); pause(5, 7)
    hdr = place_header(page)
    assert hdr["name"] and expect["name_has"].lower() in hdr["name"].lower(), f"wrong listing: {hdr}"
    assert expect["address_has"] in hdr["address"], f"address mismatch: {hdr}"
    m = re.search(r"\(([\d,]+)\)", hdr["rating_line"])
    hdr["listed_review_count"] = int(m.group(1).replace(",", "")) if m else None
    scroll_overview(page)
    hist = {}
    for row in page.query_selector_all("tr[aria-label]"):
        hm = re.match(r"(\d) stars?, ([\d,]+) reviews?", row.get_attribute("aria-label") or "")
        if hm: hist[int(hm.group(1))] = int(hm.group(2).replace(",", ""))
    hdr["star_histogram"] = {str(k): hist.get(k, 0) for k in range(5, 0, -1)} if hist else None
    if hist:
        assert sum(hist.values()) == hdr["listed_review_count"], f"histogram {hist} != listed {hdr['listed_review_count']}"
    hdr["final_url"] = page.url
    hdr["review_topics"] = [b.get_attribute("aria-label") for b in page.query_selector_all("button[aria-label*=', mentioned in']")]
    reviews = read_reviews(page, hdr["final_url"], "default overview")
    tab = page.query_selector("button[role='tab'][aria-label*='Reviews']")
    if tab:                                                       # small listings: the Reviews tab lists all of them
        tab.click(); pause()
        if "Sign-in to get the best" in page.inner_text("body"):
            page.keyboard.press("Escape"); pause()
        else:
            scroll_until_stable(page)
            reviews += read_reviews(page, hdr["final_url"], "Reviews tab")
        page.goto(hdr["final_url"], wait_until="domcontentloaded", timeout=60000); pause(6, 8)
        scroll_overview(page)
    n_snip = len(page.query_selector_all("div.OXD3gb[role='button']"))
    hdr["summary_snippets"] = []
    for i in range(n_snip):
        snips = page.query_selector_all("div.OXD3gb[role='button']")
        if i >= len(snips): break
        hdr["summary_snippets"].append(snips[i].inner_text().strip())
        snips[i].click(); pause()
        if "Sign-in to get the best" in page.inner_text("body"):
            page.keyboard.press("Escape"); pause(); continue
        reviews += read_reviews(page, hdr["final_url"], f"review-summary snippet {i + 1}")
        page.goto(hdr["final_url"], wait_until="domcontentloaded", timeout=60000); pause(6, 8)
        scroll_overview(page)
    uniq = list({r["review_id"]: r for r in reviews}.values())
    return hdr, uniq

def search_google(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60000); pause(5, 7)
    if page.query_selector("h1.DUwDvf"):
        h = place_header(page)
        return [{"name": h["name"], "address": h["address"], "website": h["website"]}]
    out = []
    for r in page.query_selector_all("div[role='feed'] div.Nv2PK")[:8]:
        a = r.query_selector("a.hfpxzc")
        out.append({"name": a.get_attribute("aria-label") if a else None, "card": r.inner_text().replace("\n", " | ")[:160]})
    return out

def main(only=None):
    CACHE.mkdir(exist_ok=True)
    today = dt.date.today().isoformat()
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(user_agent=UA, locale="en-US", viewport={"width": 1300, "height": 950})
        page = ctx.new_page()
        for c in COMPANIES:
            if only and c["slug"] not in only:
                continue
            rec = {"company": c["name"], "slug": c["slug"], "website": c["website"], "retrieved": today,
                   "identity_note": c["identity_note"], "attempts": [], "reviews": []}
            for d in c["trustpilot_domains"]:
                tp = check_trustpilot(page, d); pause()
                rec["attempts"].append({"source": "Trustpilot", **tp})
            tp_n = max([a.get("review_count") or 0 for a in rec["attempts"]] + [0])
            if tp_n >= TRUSTPILOT_MIN:
                raise SystemExit(f"{c['name']}: Trustpilot has {tp_n} reviews; add a Trustpilot review scraper before continuing")
            if c.get("yelp"):
                rec["attempts"].append({"source": "Yelp", **check_yelp(page, c["yelp"])}); pause()
            if c["google"]:
                hdr, reviews = scrape_google_with_retry(page, c["google"], c["expect"]); pause()
                rec["attempts"].append({"source": "Google Maps", "url": c["google"], "listing": hdr,
                                        "itemized_reviews_retrieved": len(reviews)})
                # Logged-out Google shows a different subset of itemized reviews on different loads, so reviews
                # are merged across runs by Google's review id (each one was really displayed and read). The
                # histogram is taken from the latest run that rendered it in full.
                old = json.loads((CACHE / f"{c['slug']}.json").read_text()) if (CACHE / f"{c['slug']}.json").exists() else {}
                now = dt.datetime.now().isoformat(timespec="seconds")
                merged = {r["review_id"]: r for r in old.get("reviews", [])}
                new_ids = [r["review_id"] for r in reviews if r["review_id"] not in merged]
                for r in reviews:
                    merged.setdefault(r["review_id"], {**r, "first_retrieved": now})
                rec["reviews"] = list(merged.values())
                rec["star_histogram"] = hdr["star_histogram"] or old.get("star_histogram")
                rec["listed_review_count"] = hdr["listed_review_count"] or old.get("listed_review_count")
                rec["review_topics"] = hdr.get("review_topics") or old.get("review_topics", [])
                rec["runs"] = old.get("runs", []) + [{"run_at": now, "itemized_this_run": len(reviews),
                                                       "new_this_run": len(new_ids),
                                                       "histogram_this_run": hdr["star_histogram"]}]
                rec["source_used"] = "Google Maps"
                rec["source_url"] = hdr["final_url"]
            else:
                for u in c.get("google_searches", []):
                    rec["attempts"].append({"source": "Google Maps search", "url": u, "results": search_google(page, u)}); pause()
                rec["source_used"] = None
                rec["source_url"] = None
            (CACHE / f"{c['slug']}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
            listed = next((a["listing"].get("listed_review_count") for a in rec["attempts"] if a.get("listing")), None)
            print(f"{c['name']}: {len(rec['reviews'])} itemized reviews cached; listing shows {listed}; "
                  f"histogram {rec.get('star_histogram')}; source: {rec['source_used']}")
        b.close()

if __name__ == "__main__":
    main(sys.argv[1:] or None)
