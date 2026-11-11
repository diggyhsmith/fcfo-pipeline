"""Polite, cached page fetcher for competitor_map.ipynb.

Rules (the notebook prints them): plain python-requests User-Agent, never changed; robots.txt is read first and a disallowed URL is
not fetched; a page that answers 4xx/5xx, times out or is a parked domain is recorded as "not available" and is not retried with
another client. Emails and phone numbers are redacted from cached text, so the cache holds no contact details.

cache/full/<key>.txt      visible page text (git-ignored: full copies of commercial pages are not republished)
cache/pages/<key>.json    what the repo keeps: URL, status, retrieval date, robots verdict, and only the text lines the analysis uses
cache/manifest.json       one row per URL attempted
"""
import json, re, hashlib, datetime as dt, warnings
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
FULL, PAGES = CACHE / "full", CACHE / "pages"
for d in (FULL, PAGES, CACHE / "robots"):
    d.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = CACHE / "manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}
UA = requests.utils.default_user_agent()          # "python-requests/x.y"; not changed for any site
TODAY = dt.date.today().isoformat()

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)")
PARKED = re.compile(r"domain (?:is )?for sale|buy this domain|parked free|this domain may be for sale|expireddomains", re.I)

def key(url):
    p = urlparse(url)
    slug = re.sub(r"[^a-z0-9]+", "-", (p.netloc + p.path).lower()).strip("-")[:70]
    return f"{slug}-{hashlib.sha1(url.encode()).hexdigest()[:8]}"

def save_manifest():
    MANIFEST_PATH.write_text(json.dumps(MANIFEST, indent=1, sort_keys=True))

def redact(s):
    return PHONE.sub("[phone]", EMAIL.sub("[email]", s))

def robots_ok(url):
    """True/False from the site's robots.txt for our User-Agent; None if robots.txt itself could not be read (treated as allowed,
    which is the robots.txt convention for a missing file, but recorded)."""
    p = urlparse(url)
    root = f"{p.scheme}://{p.netloc}"
    f = CACHE / "robots" / (re.sub(r"[^a-z0-9]+", "-", p.netloc.lower()) + ".txt")
    if not f.exists():
        try:
            r = requests.get(root + "/robots.txt", timeout=30)
            f.write_text(r.text if r.status_code == 200 else f"# HTTP {r.status_code}\n")
        except Exception as e:
            f.write_text(f"# unreachable: {type(e).__name__}\n")
    txt = f.read_text()
    if txt.startswith("# HTTP 4") or txt.startswith("# unreachable"):
        return None
    rp = RobotFileParser()
    rp.parse(txt.splitlines())
    return rp.can_fetch(UA, url)

def visible_text(html):
    s = BeautifulSoup(html, "html.parser")
    for t in s(["script", "style", "noscript", "svg", "template"]):
        t.decompose()
    lines = (re.sub(r"\s+", " ", l).strip() for l in s.get_text("\n").split("\n"))
    return redact("\n".join(l for l in lines if l))

def fetch(url):
    """Return dict(url, status, retrieved, text or None, note). Fetches once; afterwards served from the cache."""
    k = key(url)
    meta_f, full_f = PAGES / f"{k}.json", FULL / f"{k}.txt"
    if meta_f.exists():
        meta = json.loads(meta_f.read_text())
        meta["text"] = full_f.read_text() if full_f.exists() else "\n".join(meta.get("kept_lines", [])) or None
        meta["from"] = "full text" if full_f.exists() else ("kept lines" if meta["text"] else "none")
        return meta
    meta = {"url": url, "retrieved": TODAY, "user_agent": UA}
    ok = robots_ok(url)
    meta["robots"] = {True: "allowed", False: "DISALLOWED", None: "robots.txt not readable"}[ok]
    if ok is False:
        meta.update(status="not fetched", note="robots.txt disallows this URL for our user agent")
    else:
        try:
            r = requests.get(url, timeout=45)
            meta.update(status=r.status_code, final_url=r.url)
            if r.status_code >= 400:
                meta["note"] = f"HTTP {r.status_code}: not available (not retried with another client)"
            else:
                text = visible_text(r.text)
                if PARKED.search(text[:3000]) or PARKED.search(r.url) or len(text) < 200:
                    meta["note"] = "parked / for-sale / empty page: firm treated as not operating at this domain"
                    meta["parked"] = True
                full_f.write_text(text)
                meta["chars"] = len(text)
        except Exception as e:
            meta.update(status="error", note=f"{type(e).__name__}: not available")
    MANIFEST[url] = {k2: meta.get(k2) for k2 in ("retrieved", "status", "robots", "note", "final_url")}
    save_manifest()
    meta_f.write_text(json.dumps(meta, indent=1))
    meta["text"] = full_f.read_text() if full_f.exists() else None
    meta["from"] = "full text" if meta["text"] else "none"
    return meta

def _norm(s):
    return re.sub(r"\s+", " ", s.replace("\u2019", "'").replace("\u2018", "'")).strip().lower()

def keep_lines(url, patterns, quotes=()):
    """Write into cache/pages/<key>.json only the text lines matching any of `patterns`, plus the run of lines that holds each quote
    (kept in page order, so a quote spanning several lines stays contiguous). A fresh clone re-runs every check on these lines, and the
    repo does not hold whole commercial pages. Returns the number of lines kept. Idempotent: on a reduced cache it re-reads the kept lines."""
    k = key(url)
    meta_f, full_f = PAGES / f"{k}.json", FULL / f"{k}.txt"
    if not meta_f.exists():
        return 0
    meta = json.loads(meta_f.read_text())
    if not full_f.exists():
        return len(meta.get("kept_lines", []))
    lines = full_f.read_text().split("\n")
    rx = re.compile("|".join(patterns), re.I)
    keep = {i for i, l in enumerate(lines) if rx.search(l)}
    for q in quotes:
        nq = _norm(q)
        for i in range(len(lines)):
            acc, j = "", i
            while j < len(lines) and len(acc) < len(nq) + 200:
                acc = _norm(acc + " " + lines[j])
                if nq in acc:
                    while i < j and nq in _norm(" ".join(lines[i + 1:j + 1])):   # trim to the shortest run that still holds the quote
                        i += 1
                    keep.update(range(i, j + 1))
                    break
                j += 1
            if nq in acc:
                break
    meta["kept_lines"] = [lines[i] for i in sorted(keep)]
    meta_f.write_text(json.dumps(meta, indent=1))
    return len(keep)
