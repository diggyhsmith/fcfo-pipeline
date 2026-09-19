"""Helper for the build session: print cached page text. Usage: python dev/pg.py DOC_ID 3 4 7-9 [--raw]"""
import json, sys
doc = sys.argv[1]; raw = "--raw" in sys.argv
want = []
for a in sys.argv[2:]:
    if a.startswith("--"): continue
    if "-" in a: lo, hi = a.split("-"); want += list(range(int(lo), int(hi) + 1))
    else: want.append(int(a))
for l in open("cache/pages.jsonl"):
    p = json.loads(l)
    if p["doc_id"] == doc and p["pdf_page"] in want:
        print(f"\n##### {doc} | PDF p.{p['pdf_page']} | printed {p['printed_page']} #####")
        print(p["text_raw"] if raw else p["text"])
