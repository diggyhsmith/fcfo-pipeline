# Notes for reflection (kept as the build goes; facts only)

- Build session date: 2026-09-19. Working dir is inside OneDrive; the venv was moved out to avoid syncing thousands of files.
- `gh` is NOT installed on this machine (not merely unauthenticated). Needed a repo URL + push credentials from the user.
- User said the third report was MarketResearch.com; it is actually a First Research (D&B Hoovers) industry profile, a browser printout.
  Its "Associated Industry Codes" section (PDF p.26) is EMPTY in the printout, so no NAICS code is stated; had to leave scope as "inferred from title".
- The three reports do not line up with the chosen NAICS 541611: 54161 (IBISWorld) is a superset of it; 54121c covers 541211+541219 (the rejected neighbor); First Research states no code.
- Two-column IBISWorld pages interleave under default pdfplumber extraction; a quote wrapping across lines was not contiguous. Built a column-aware variant and let the verifier accept either.
- IBISWorld 54121c contradicts itself: executive summary says $157.4bn / 1.3% / 2.3% -> $176.3bn, but the At-a-Glance and Performance snapshot say $158.4bn / 1.4% / 2.1%. Kept both.
- Report dates: 54121c "Published: May 2026", 54161 "Published: August 2026", First Research "Data Published: July 2025" (with a July 2026 quarterly update and 2023 valuation multiples inside it). Mixed vintages.
- First Research gives NO market share percentages for any competitor (only names and "50 largest ... just less than 50%"); IBISWorld gives Big Four shares only. Nothing for the fractional niche.
- Verifier history (be honest about it): my first verify.py accepted a fuzzy match at >=90 with only a digit guard. A negative control I wrote (change 'grew' to 'shrank') PASSED at fuzzy 95.4, i.e. the rule as specified would have let a meaning-reversing edit through. Tightened: fuzzy passes only if every word and every digit run of the quote is in the matched window. Also found IBISWorld tables embed private-use icon glyphs (U+E953) between labels and numbers, which broke an exact match on the At-a-Glance revenue quote; stripped them in normalisation.
- After tightening, all 79 real quotes verified in round 1 (0 failures, 0 corrected in retry). The extraction quotes were copied from the cached text, so the verifier had nothing to catch in THIS run; the only real catches were against the verifier's own weaknesses. Do not claim it caught extraction errors.

# Five Forces build (2026-10-02; facts only, not the reflection)

- brief.json's own force tags looked sufficient by raw quote count (11-24 quotes per force), but after reading them against the $2M-$20M segment only 2 facts each were usable for new entrants, suppliers and substitutes. Several quotes restated one point, and some described large corporate buyers. 14 of 19 usable brief facts came from IBISWorld.
- Six (signal, document) findings had no clean tag (S1 market size x3, S6 x2, S7 First Research) and had to be mapped by hand with a stated reason.
- The code cross-check caught an agent error: fact P5 was labeled "from brief.json" but one of its two quotes was a new extraction from the same page. The rule dropped it until the origin was corrected.
- Sources conflict: IBISWorld calls consulting fragmented (top firm 5.3%), First Research calls accounting "concentrated" (top 50 hold just under 50%). IBISWorld rates DIY accounting substitutes "Low", while the consulting report and CBIZ's 10-K treat AI and software as active threats.
- IBISWorld's "high" buyer-power rating is driven by large corporate clients, not by our segment.
- The CPA licence is legally required only for SEC/attest work (BLS; CBIZ 10-K), so fractional CFO advisory has no licence gate.
- Access problems: bls.gov returns 403 to scripts (used the Internet Archive snapshot); SEC requires a contact User-Agent; the SBA 2025 FAQ URL was a 404 (used the Feb 2026 PDF); the SBA PDF is two-column and needed column-aware extraction; GeekWire returned 403 (used TechCrunch).
- The course spreadsheet uses 5 = most attractive (weak force) with decimals and equal 0.2 weights (example overall 3.39); the assignment uses 5 = strong force, whole numbers, no averaging.
- Verification: 55/55 Five Forces quotes and 79/79 first-project quotes pass; 7/7 corrupted-quote controls rejected. As before, the quotes were copied from cached text, so passing shows faithful copying, not correct interpretation.
- Scores (agent judgment): rivalry 4, buyers 3, suppliers 4, new entrants 4, substitutes 3. Torn 2-vs-3 on buyers and 3-vs-4 on substitutes.
