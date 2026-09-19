# %% [markdown]
# ## Stage 2: Extraction (seven signals, each with page-level evidence)
#
# **Choice:** the extraction schema is defined *first* (`extraction_schema.json`). The default extractor, `claude_code_files`, loads
# `extractions/<doc_id>.json`, which **Claude Code (an LLM agent) wrote during the build session** by reading the cached page text of one document at a
# time. It is not an API call and no model runs inside this notebook. Every signal carries `evidence[]` = `doc_id, pdf_page, section_heading, quote (<=25 words)`,
# a `status` (FOUND / PARTIAL / NOT_FOUND), a `confidence`, and notes on scope.
#
# **Alternatives rejected:** (1) a paid LLM API (the project is zero-cost by requirement); (2) regex/keyword extraction (cannot read
# a market-share table or judge "biggest trend"); (3) one pass over all three reports at once (a conclusion from one report would leak into another's extraction,
# so each document got its own pass).
#
# **Optional second backend:** `extractor="gemini"` calls Google's Gemini API with a free AI Studio key (`GEMINI_API_KEY`). It is **implemented, untested**:
# no key was available in the build session, so it has never called the live API. Its parsing, chunking and rate-limit logic was exercised only against a mock (below).
# Its output would go through the same code-side verifier, so a bad Gemini extraction would fail loudly instead of being trusted.
#
# **Limits:** LLM extraction is not deterministic; re-running the extraction step could produce different signals or different quotes.
# Verification catches wrong quotes and numbers, not wrong interpretations.

# %%
EXTRACTION_SCHEMA = json.load(open("extraction_schema.json"))
SIGNAL_META = {
    "S1": ("Industry size and five-year growth", "context"),
    "S2": ("Top competitors and market share", "rivalry"),
    "S3": ("Regulatory or compliance pressure", "barriers to entry"),
    "S4": ("Key-input concentration or fragility (talent, software)", "supplier power"),
    "S5": ("Customer concentration or fragmentation", "buyer power"),
    "S6": ("Biggest trend of the next five years", "chosen, with reason"),
    "S7": ("Biggest threat of the next five years", "chosen, with reason"),
}

def load_extractions_claude_files(extract_dir=EXTRACT_DIR):
    """Default extractor: read the JSON files the Claude Code agent wrote."""
    out = {}
    for f in sorted(glob.glob(os.path.join(extract_dir, "*.json"))):
        ext = json.load(open(f))
        out[ext["doc_id"]] = ext
    if not out:
        raise FileNotFoundError(f"No extraction files in {extract_dir}/. Use extractor='gemini' (needs GEMINI_API_KEY) or add files.")
    return out

# ---- Gemini backend: IMPLEMENTED, UNTESTED against the live API ------------------------------------------------------------------
GEMINI_API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MIN_INTERVAL_S = 13          # free tier is roughly 5-10 requests/min; 13 s spacing stays under 5/min
GEMINI_MAX_CHARS_PER_CALL = 350_000 # documents longer than this are split into page chunks and merged
GEMINI_TEST_STATUS = "implemented, untested (never called the live Gemini API; logic exercised only with a mock)"
_last_gemini_call = [0.0]

def gemini_pick_model(api_key, session=requests):
    """Pick a model from the live list (never a hard-coded name). Prefers the newest stable 'flash' model that supports generateContent."""
    r = session.get(f"{GEMINI_API_ROOT}/models", headers={"x-goog-api-key": api_key}, params={"pageSize": 200}, timeout=30)
    r.raise_for_status()
    names = [m["name"].split("/", 1)[1] for m in r.json().get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
    bad = ("lite", "image", "tts", "live", "audio", "embedding", "preview", "exp", "thinking", "vision")
    pool = [n for n in names if "flash" in n and not any(b in n for b in bad)] or [n for n in names if "flash" in n]
    if not pool:
        raise RuntimeError(f"No flash model with generateContent in the live list: {names[:10]}")
    return sorted(pool)[-1]

def gemini_prompt(meta, pages):
    text = "\n".join(f"=== PDF PAGE {p['pdf_page']} ===\n{p['text']}" for p in pages)
    shapes = json.dumps(EXTRACTION_SCHEMA["signal_value_shapes"], indent=1)
    return textwrap.dedent(f"""\
        You are extracting seven industry signals from ONE report, using ONLY the text below. Return a single JSON object that follows this contract.
        doc_id = "{meta['doc_id']}". Keys: doc_id, extracted_by, extraction_date, report_scope, signals[7].
        Each signal: signal_id (S1..S7), force_tag, status (FOUND|PARTIAL|NOT_FOUND), value (object or null), summary (1-2 sentences, own words),
        evidence[] of {{doc_id, pdf_page (integer), section_heading, quote}}, confidence {{level: high|med|low, reason}}, notes.
        Rules: quotes must be copied verbatim from the cited page and be at most 25 words; every number in value must appear in a quote;
        prefer NOT_FOUND to inference; say in notes when a figure covers a broader or narrower industry than fractional CFO services; never use outside knowledge.
        Signals: {json.dumps({k: v[0] for k, v in SIGNAL_META.items()})}
        Value shapes: {shapes}
        report_scope needs stated_industry_code, scope_summary, naics_2022_listed, relation_to_chosen_naics, evidence[].
        TEXT:
        {text}""")

def gemini_call(prompt, api_key, model, session=requests, sleep=time.sleep, clock=time.time, max_tries=5):
    """One rate-limited call. Waits to respect the free-tier spacing, backs off on 429/5xx, returns parsed JSON."""
    for attempt in range(max_tries):
        wait = GEMINI_MIN_INTERVAL_S - (clock() - _last_gemini_call[0])
        if wait > 0: sleep(wait)
        _last_gemini_call[0] = clock()
        r = session.post(f"{GEMINI_API_ROOT}/models/{model}:generateContent", headers={"x-goog-api-key": api_key},
                         json={"contents": [{"parts": [{"text": prompt}]}],
                               "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}, timeout=300)
        if r.status_code in (429, 500, 503):
            sleep(min(120, 2 ** attempt * 15)); continue
        r.raise_for_status()
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(txt)
    raise RuntimeError("Gemini call failed after retries (rate limit or server error)")

def _chunk_pages(pages, max_chars):
    chunks, cur, n = [], [], 0
    for p in pages:
        if cur and n + len(p["text"]) > max_chars:
            chunks.append(cur); cur, n = [], 0
        cur.append(p); n += len(p["text"])
    if cur: chunks.append(cur)
    return chunks

def merge_chunk_extractions(parts):
    """Merge per-chunk extractions: per signal keep the chunk with the strongest status (FOUND > PARTIAL > NOT_FOUND)."""
    rank = {"FOUND": 2, "PARTIAL": 1, "NOT_FOUND": 0}
    merged = dict(parts[0])
    best = {}
    for part in parts:
        for s in part["signals"]:
            if s["signal_id"] not in best or rank[s["status"]] > rank[best[s["signal_id"]]["status"]]:
                best[s["signal_id"]] = s
    merged["signals"] = [best[k] for k in sorted(best)]
    return merged

def extract_with_gemini(pages_by_doc, docs, api_key, model=None, session=requests, out_dir="extractions_gemini", **kw):
    model = model or GEMINI_MODEL or gemini_pick_model(api_key, session)
    os.makedirs(out_dir, exist_ok=True)
    out = {}
    for doc_id, pages in pages_by_doc.items():
        parts = [gemini_call(gemini_prompt(docs[doc_id], ch), api_key, model, session=session, **kw)
                 for ch in _chunk_pages(pages, GEMINI_MAX_CHARS_PER_CALL)]
        ext = merge_chunk_extractions(parts) if len(parts) > 1 else parts[0]
        ext["doc_id"] = doc_id
        ext["extracted_by"] = f"Gemini model {model} via the free AI Studio API (not Claude); quotes still verified in code"
        ext["extraction_date"] = datetime.date.today().isoformat()
        json.dump(ext, open(os.path.join(out_dir, f"{doc_id}.json"), "w"), indent=1)
        out[doc_id] = ext
    return out

def run_extractor(extractor, pages=None, docs=None):
    if extractor == "claude_code_files":
        return load_extractions_claude_files(), "claude_code_files: Claude Code (LLM agent) wrote these files in the build session"
    if extractor == "gemini":
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("extractor='gemini' needs GEMINI_API_KEY (free AI Studio key, no billing). Not set, so nothing was run.")
        by_doc = collections.defaultdict(list)
        for p in pages or []: by_doc[p["doc_id"]].append(p)
        return extract_with_gemini(by_doc, docs, key), f"gemini: run at {datetime.datetime.now().isoformat(timespec='seconds')} (status of this backend: {GEMINI_TEST_STATUS})"
    raise ValueError(f"unknown extractor {extractor!r}")

# %%
EXTRACTIONS, EXTRACTOR_NOTE = run_extractor(EXTRACTOR, PAGES, DOCS)
print("Extractor:", EXTRACTOR_NOTE, "\n")
print(f"{'doc_id':<36}{'sig':<5}{'status':<10}{'conf':<6}{'#quotes':<8} force_tag")
for d, ext in EXTRACTIONS.items():
    for s in ext["signals"]:
        print(f"{d:<36}{s['signal_id']:<5}{s['status']:<10}{s['confidence']['level']:<6}{len(s['evidence']):<8} {s['force_tag']}")
    print(f"  extracted_by: {ext['extracted_by'][:110]}\n")

# %% [markdown]
# **Gemini backend: offline logic check (mock only).** The cell below feeds the Gemini code path a *fake* HTTP session that returns a canned
# response. It checks that model selection from a list, prompt building, rate-limit spacing, a 429 retry, chunk merging and JSON parsing all run without error.
# It does **not** show that Gemini follows the schema, that the endpoint or field names are current, or that the free tier accepts this request. That is why
# the backend stays labelled *implemented, untested*.

# %%
class _FakeResp:
    def __init__(self, code, payload): self.status_code, self._p = code, payload
    def json(self): return self._p
    def raise_for_status(self):
        if self.status_code >= 400: raise RuntimeError(f"HTTP {self.status_code}")

class _FakeSession:
    """Stands in for `requests`; never touches the network."""
    def __init__(self, canned): self.canned, self.calls, self._n = canned, [], 0
    def get(self, url, **kw):
        return _FakeResp(200, {"models": [{"name": "models/gemini-9-pro", "supportedGenerationMethods": ["generateContent"]},
                                          {"name": "models/gemini-9-flash-lite", "supportedGenerationMethods": ["generateContent"]},
                                          {"name": "models/gemini-9-flash", "supportedGenerationMethods": ["generateContent"]},
                                          {"name": "models/gemini-8-flash", "supportedGenerationMethods": ["generateContent"]},
                                          {"name": "models/text-embedding-9", "supportedGenerationMethods": ["embedContent"]}]})
    def post(self, url, **kw):
        self._n += 1; self.calls.append(url)
        if self._n == 1: return _FakeResp(429, {})                       # first call is rate-limited -> must retry
        return _FakeResp(200, {"candidates": [{"content": {"parts": [{"text": json.dumps(self.canned)}]}}]})

_doc = next(iter(EXTRACTIONS))
_fake = _FakeSession(EXTRACTIONS[_doc])
_slept = []
_fake_pages = [{"doc_id": _doc, "pdf_page": i, "text": "x" * 200} for i in range(1, 4)]
GEMINI_MAX_CHARS_PER_CALL, _saved = 500, GEMINI_MAX_CHARS_PER_CALL                # force 2 chunks so the merge path runs
_out = extract_with_gemini({_doc: _fake_pages}, {_doc: {"doc_id": _doc}}, "FAKE-KEY", session=_fake,
                           out_dir=os.path.join(CACHE_DIR, "gemini_mock"), sleep=_slept.append, clock=lambda: 1e9)
GEMINI_MAX_CHARS_PER_CALL = _saved
assert gemini_pick_model("k", _fake) == "gemini-9-flash", "model must come from the live list, newest stable flash"
assert len(_fake.calls) == 3 and all("gemini-9-flash:generateContent" in u for u in _fake.calls), "expected 1 retry + 2 chunk calls"
assert len(_out[_doc]["signals"]) == 7 and _out[_doc]["extracted_by"].startswith("Gemini")
print("Mock check passed: picked model from list, retried after a 429, made", len(_fake.calls) - 1, "chunk calls, merged to 7 signals.")
print("Status of the Gemini backend:", GEMINI_TEST_STATUS)

# %%
SCOPE_TABLE = report_scope_table(EXTRACTIONS, DOCS, CHOSEN_CODE)
print(f"Chosen code: {CHOSEN_CODE}. Which report covers what:\n")
for r in SCOPE_TABLE:
    print(f"- {r['doc_id']}  |  stated code: {r['stated_code']}  |  NAICS 2022 listed: {r['naics_2022_listed'] or 'none stated'}  |  covers chosen code: {r['covers_chosen_code']}")
    print(textwrap.indent(textwrap.fill(r["relation"], 112), "    "))
