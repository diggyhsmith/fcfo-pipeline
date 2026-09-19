# %% [markdown]
# ## Stage 3: Verification, in code (`verify.py`, shown in full below)
#
# **Choice:** the LLM's quotes are never trusted. For every evidence quote, code normalises whitespace, case, hyphens, smart quotes and dashes and checks the
# quote appears on the **cited page**; if not, on an **adjacent page** (labelled `verified_adjacent_page`); otherwise a **fuzzy match** (rapidfuzz >= 90) is tried.
# Each item ends `verified`, `verified_adjacent_page` or `FAILED`. Quotes over 25 words fail (licensing). Every number in a signal's `value` must appear in that signal's
# verified quotes. A signal left with no verified evidence becomes `UNVERIFIED` and goes to the gaps list.
#
# **Alternative rejected:** asking the LLM to "double-check itself". A model that misquoted once can misquote again while confirming; string matching against the page cannot.
# **Fuzzy matching was tightened:** a negative control (changing "grew" to "shrank") passed the plain >= 90 rule at 95.4, so the shipped rule also demands that every word and every digit run
# of the quote occur in the matched window. Fuzzy matching is for PDF-extraction glitches, not for paraphrase.
#
# **What this proves:** the quote exists on that page. **What it does not prove:** that the quote supports the interpretation in `summary`/`value`. A human still has to read the spot-check list.

# %%
# @@INCLUDE verify.py@@

# %%
def stage3_verify(extractions, cache_dir=CACHE_DIR, log_path="verification_log.json"):
    """Live mode: re-verify every quote against the cached pages. Replay mode (no PDFs on this machine): reuse the committed log and say so."""
    prev = load_log(log_path)
    rounds = (prev or {}).get("rounds", [])
    if os.path.exists(os.path.join(cache_dir, "pages.jsonl")):
        idx = build_page_index(load_pages_cache(cache_dir))
        items, number_rows, struct = verify_all(extractions, idx)
        log = write_log(log_path, items, number_rows, struct, rounds)
        return items, number_rows, struct, log, "LIVE: every quote re-checked against the PDF page text just extracted"
    if prev is None:
        raise RuntimeError("No PDFs/cache and no committed verification_log.json: nothing to verify against.")
    return prev["items"], prev["number_checks"], prev.get("structure_errors", {}), prev, \
        "REPLAY: PDFs are not on this machine, so quotes were NOT re-checked; showing the committed log from the build session"

ITEMS, NUMROWS, STRUCT, LOG, VERIFY_MODE = stage3_verify(EXTRACTIONS)
SUMM = summarize(ITEMS, NUMROWS, STRUCT)
_prev_rounds = LOG.get("rounds", [])
_failed_r1 = {tuple(k) for k in (_prev_rounds[0]["failed_keys"] if _prev_rounds else [])}
_ok_now = {(i["doc_id"], i["signal_id"], i["evidence_index"]) for i in ITEMS if i["result"] != "FAILED"}
SUMM["corrected_in_retry"] = len(_failed_r1 & _ok_now)
SUMM["rounds_run"] = len(_prev_rounds)
print("Mode:", VERIFY_MODE)
print(f"\nQuotes checked: {SUMM['quotes_checked']} | passed: {SUMM['passed']} (exact {SUMM['passed_exact']}, adjacent page {SUMM['passed_adjacent_page']}, fuzzy {SUMM['passed_fuzzy']})"
      f" | failed: {SUMM['failed']} | corrected in retry: {SUMM['corrected_in_retry']} | fix-and-retry rounds run: {SUMM['rounds_run']} (max {MAX_ROUNDS})")
print(f"Numbers in signal values checked against their quotes: {SUMM['numbers_checked']} | not found: {SUMM['numbers_unmatched']} | schema/structure errors: {SUMM['structure_errors']}")
for it in ITEMS:
    if it["result"] == "FAILED": print("  FAILED:", it["doc_id"], it["signal_id"], it["reason"])
VERIFIED = apply_verification(EXTRACTIONS, ITEMS, NUMROWS)
print("\nSignals whose final status differs from what the extractor claimed:",
      [(d, s) for d, sigs in VERIFIED.items() for s, v in sigs.items() if v["status_final"] != v["status_claimed"]] or "none")
print("\nShort sample of verified evidence (document, page, quote):")
for it in [i for i in ITEMS if i["signal_id"] == "S2"][:3]:
    print(f"  [{it['doc_id']}, PDF p.{it['pdf_page']} (printed {it['printed_page']})] {it['result']}: \"{it['quote'][:90]}\"")

# %% [markdown]
# **Verifier self-test.** All real quotes passing is only reassuring if the verifier can also *fail*. This cell takes verified quotes, corrupts them in four ways (change a digit, swap a word,
# cite the wrong page, replace with an invented sentence) and checks the verifier rejects every corruption while still accepting the untouched originals. It is a test of the verifier, **not** a finding about the extraction:
# in this run the LLM's real quotes had no failures to catch.

# %%
def verifier_self_test(items, cache_dir=CACHE_DIR, n=24, seed=7):
    if not os.path.exists(os.path.join(cache_dir, "pages.jsonl")):
        return None
    idx = build_page_index(load_pages_cache(cache_dir))
    rng = random.Random(seed)
    pool = [i for i in items if i["result"] == "verified" and i["signal_id"] != "SCOPE"]
    rng.shuffle(pool)
    rows, seen = collections.Counter(), collections.Counter()
    def bump(kind, caught):
        seen[kind] += 1; rows[kind] += int(caught)
    for it in pool[:n]:
        q, d, p = it["quote"], it["doc_id"], it["pdf_page"]
        bump("control (untouched)", check_quote(idx, d, p, q)["result"] != "FAILED")
        m = re.search(r"\d", q)
        if m:
            bad = q[:m.start()] + str((int(q[m.start()]) + 1) % 10) + q[m.start() + 1:]
            bump("digit changed", check_quote(idx, d, p, bad)["result"] == "FAILED")
        words = [w for w in re.findall(r"[A-Za-z]{5,}", q)]
        if words:
            bump("word swapped", check_quote(idx, d, p, q.replace(rng.choice(words), "zebra", 1))["result"] == "FAILED")
        bump("wrong page (+7)", check_quote(idx, d, p + 7, q)["result"] == "FAILED")
        bump("invented sentence", check_quote(idx, d, p, "Fractional CFO retainers average four thousand dollars per month")["result"] == "FAILED")
    return seen, rows

_st = verifier_self_test(ITEMS)
if _st is None:
    print("Self-test skipped (no page cache on this machine).")
else:
    seen, ok = _st
    print(f"{'test':<24}{'cases':<8}{'as expected':<12}")
    for k in seen: print(f"{k:<24}{seen[k]:<8}{ok[k]:<12}")
    assert all(ok[k] == seen[k] for k in seen), "verifier failed its own self-test"
    print("\nVerifier behaves as intended on all cases (controls accepted, every corruption rejected).")
