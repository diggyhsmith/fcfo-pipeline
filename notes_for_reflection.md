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
