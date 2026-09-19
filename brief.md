# Industry brief: Working name TBD, fractional CFO services

*Fractional (part-time, outsourced) CFO services for US small and mid-sized businesses with roughly $2M-$20M revenue. The company does not exist yet (founders are MAcc students), so the brief describes the industry we would enter.*

**Extraction:** Claude Code (an LLM agent) in the build session; verification, reconciliation, gaps and this brief are code.
**Verification mode this run:** LIVE: every quote re-checked against the PDF page text just extracted

> Fractional CFO has no industry code. Every figure describes a proxy industry (chosen NAICS 541611) or the accounting neighbor; see gaps.

## NAICS selected

**541611 Administrative Management and General Management Consulting Services** (2022 NAICS Manual: https://www.census.gov/naics/reference_files_tools/2022_NAICS_Manual.pdf, accessed 2026-09-19).

We chose 541611 because the manual defines it as "providing operating advice and assistance to businesses" on issues such as "financial planning and budgeting" and lists "Financial management (except investment advice) consulting services" as an example, which describes advice to a client's management; the closest neighbor, 541219, is instead defined as "providing accounting services (except tax return preparation services only or payroll services only)" for establishments outside CPA offices, and its own text says "Accountant (except CPA) offices, bookkeeper offices, and billing offices are included", so it is organized around producing the books rather than advising management on them.

## Verification summary

Quotes checked 79; passed 79 (exact 79, adjacent page 0, fuzzy 0); failed 0; corrected in retry 0; numbers checked 55, unmatched 0.

## Signals

### S1 Industry size and five-year growth
*force: context | status: FOUND (for the proxy industry, not the fractional niche) | quotes verified: 10*

**Primary: ibisworld_54161 (FOUND, confidence med)**
- Value: market size: 420.2; market size unit: USD billion (industry revenue); market size year: 2026 (estimated); cagr historical pct: 2.1; historical period: 2021-2026; cagr forecast pct: 1.0; forecast period: 2026-2031; forecast market size usd bn: 441.6; closest segment: name: Financial management consulting, and consulting combined with implementation, revenue usd bn: 27.3, share pct: 6.5
- Summary: US management consulting revenue is an estimated $420.2bn, having grown at a 2.1% CAGR over the last five years and forecast to grow only 1.0% a year to $441.6bn. The closest product line to CFO-type work, financial management consulting, is a 6.5% slice.
- Cite [ibisworld_54161, At a Glance > Executive Summary, PDF p.9 (printed 6)] "Revenue grew at a CAGR of 2.1% to an estimated $420.2 billion over the past five years" (verified)
- Cite [ibisworld_54161, At a Glance > Executive Summary, PDF p.10 (printed 7)] "Revenue is poised to grow at a CAGR of 1.0% to an estimated $441.6 billion over the next five years" (verified)
- Cite [ibisworld_54161, At a Glance > Products & Services, PDF p.8 (printed 5)] "Financial management consulting, and 27.3 6.5 consulting combined with implementation" (verified)
- Note: Broader industry than ours. The 27.3 / 6.5 pair is read from a table whose label wraps over several lines; the quote is the verbatim run of text.

**Also: ibisworld_54121c (FOUND, confidence med)**
- Value: market size: 158.4; market size unit: USD billion (industry revenue); market size year: 2026 (estimated); cagr historical pct: 1.4; historical period: 2021-2026; cagr forecast pct: 2.1; forecast period: 2026-2031
- Summary: The report gives two different sets of headline numbers: $158.4bn, 1.4% past and 2.1% forecast CAGR in the At a Glance panel, and $157.4bn, 1.3% and 2.3% (to $176.3bn) in the executive-summary text. Both are recorded; the panel is used as primary because it repeats on two pages.
- Cite [ibisworld_54121c, At a Glance, PDF p.6 (printed 3)] "Revenue Employees 2021-26 1.4% $158.4bn 663.5k 2026-31 2.1%" (verified)
- Cite [ibisworld_54121c, At a Glance > Executive Summary, PDF p.7 (printed 4)] "Accounting services revenue grew at a CAGR of 1.3% to an estimated $157.4 billion over the past five years" (verified)
- Cite [ibisworld_54121c, At a Glance > Executive Summary, PDF p.7 (printed 4)] "Accounting services revenue is expected to grow at a CAGR of 2.3%" (verified)
- Cite [ibisworld_54121c, At a Glance > Executive Summary, PDF p.8 (printed 5)] "to an estimated $176.3 billion over the next five years." (verified)
- Note: Broader and differently composed than our niche. The primary/alternate choice is arbitrary in that the source does not say which set is right; the reconciliation stage keeps both.

**Also: firstresearch_accounting-services (PARTIAL, confidence med)**
- Value: market size: 153; market size unit: USD billion (combined annual revenue); market size year: not stated on the page (report data published July 2025); historical period: not stated; cagr forecast pct: 4; forecast period: 2024-2029; forecast basis: Current (nominal) dollars, for 'US accounting, tax prep, bookkeeping, and payroll services'; establishments: 133000
- Summary: The US accounting services industry has about 133,000 establishments and about $153bn of annual revenue, with revenue forecast to compound at 4% a year from 2024 to 2029. No historical growth rate and no year for the $153bn are given.
- Cite [firstresearch_accounting-services, Industry Overview > Fast Facts, PDF p.1 (printed 1)] "The US accounting services industry includes about 133,000 establishments" (verified)
- Cite [firstresearch_accounting-services, Industry Overview > Fast Facts, PDF p.1 (printed 1)] "combined annual revenue of about $153 billion." (verified)
- Cite [firstresearch_accounting-services, Industry Overview > Industry Forecast, PDF p.1 (printed 1)] "forecast to grow at an annual compounded rate of 4% between 2024 and 2029" (verified)
- Note: Broader industry (accounting, tax prep, bookkeeping, payroll). The report was published July 2025, older than both IBISWorld reports.

**Conflict (value_disagreement_same_industry_family): Market size (USD bn)**
- firstresearch_accounting-services: 153 (not stated) [firstresearch_accounting-services, Industry Overview > Fast Facts, PDF p.1 (printed 1)] "combined annual revenue of about $153 billion."
- ibisworld_54121c: 158.4 (2021-2026) [ibisworld_54121c, At a Glance, PDF p.6 (printed 3)] "Revenue Employees 2021-26 1.4% $158.4bn 663.5k 2026-31 2.1%"
- Why they may differ: Both describe accounting services but with different scope (First Research includes payroll and tax preparation), vintage (July 2025 vs May 2026) and, for growth, different periods and price basis. The reports do not say which is right.

**Conflict (value_disagreement_same_industry_family): Forecast 5-yr CAGR (%)**
- firstresearch_accounting-services: 4 (2024-2029) [firstresearch_accounting-services, Industry Overview > Industry Forecast, PDF p.1 (printed 1)] "forecast to grow at an annual compounded rate of 4% between 2024 and 2029"
- ibisworld_54121c: 2.1 (2026-2031) [ibisworld_54121c, At a Glance, PDF p.6 (printed 3)] "Revenue Employees 2021-26 1.4% $158.4bn 663.5k 2026-31 2.1%"
- Why they may differ: Both describe accounting services but with different scope (First Research includes payroll and tax preparation), vintage (July 2025 vs May 2026) and, for growth, different periods and price basis. The reports do not say which is right.

**Conflict (within_document): Market size (USD bn)**
- ibisworld_54121c: 158.4 (At a Glance / Performance Snapshot) [ibisworld_54121c, At a Glance, PDF p.6 (printed 3)] "Revenue Employees 2021-26 1.4% $158.4bn 663.5k 2026-31 2.1%"
- ibisworld_54121c: 157.4 (Executive Summary text) [ibisworld_54121c, At a Glance > Executive Summary, PDF p.7 (printed 4)] "Accounting services revenue grew at a CAGR of 1.3% to an estimated $157.4 billion over the past five years"
- Why they may differ: Executive Summary text (PDF pp.7-8) versus At a Glance and Performance Snapshot (PDF pp.6, 9) within the same report

**Conflict (within_document): Historical 5-yr CAGR (%)**
- ibisworld_54121c: 1.4 (At a Glance / Performance Snapshot) [ibisworld_54121c, At a Glance, PDF p.6 (printed 3)] "Revenue Employees 2021-26 1.4% $158.4bn 663.5k 2026-31 2.1%"
- ibisworld_54121c: 1.3 (Executive Summary text) [ibisworld_54121c, At a Glance > Executive Summary, PDF p.7 (printed 4)] "Accounting services revenue grew at a CAGR of 1.3% to an estimated $157.4 billion over the past five years"
- Why they may differ: Executive Summary text (PDF pp.7-8) versus At a Glance and Performance Snapshot (PDF pp.6, 9) within the same report

**Conflict (within_document): Forecast 5-yr CAGR (%)**
- ibisworld_54121c: 2.1 (At a Glance / Performance Snapshot) [ibisworld_54121c, At a Glance, PDF p.6 (printed 3)] "Revenue Employees 2021-26 1.4% $158.4bn 663.5k 2026-31 2.1%"
- ibisworld_54121c: 2.3 (Executive Summary text) [ibisworld_54121c, At a Glance > Executive Summary, PDF p.7 (printed 4)] "Accounting services revenue is expected to grow at a CAGR of 2.3%"
- Why they may differ: Executive Summary text (PDF pp.7-8) versus At a Glance and Performance Snapshot (PDF pp.6, 9) within the same report

### S2 Top competitors and market share
*force: rivalry | status: FOUND (for the proxy industry, not the fractional niche) | quotes verified: 12*

**Primary: ibisworld_54161 (FOUND, confidence med)**
- Value: Deloitte 5.3% (revenue $22.4bn); Accenture Plc band 2.5–5%; EY band 2.5–5%; PwC band 2.5–5%; KPMG band 0–2.5% | share basis: Share of total US Management Consulting (IBISWorld 54161) industry revenue, 2026 / IBISWorld share band (percent of 54161 industry revenue), 2026
- Summary: Only Deloitte has a point share (5.3%); the next four global firms are given as bands. The industry is fragmented, with the top 20 firms holding roughly a quarter of revenue and most establishments being nonemployers.
- Cite [ibisworld_54161, Companies > Market Share, PDF p.34 (printed 31)] "Industry-specific company revenue as a share of total industry revenue." (verified)
- Cite [ibisworld_54161, Companies > Market Share, PDF p.34 (printed 31)] "Deloitte ($22.4bn) 5.3% Other Companies ($397.9bn) 94.7%" (verified)
- Cite [ibisworld_54161, Companies > Company Details, PDF p.34 (printed 31)] "Accenture Plc 2.5–5 10,000+ EY 2.5–5 10,000+ PwC 2.5–5 10,000+ KPMG 0–2.5 10,000+" (verified)
- Cite [ibisworld_54161, At a Glance > Executive Summary, PDF p.9 (printed 6)] "with the top 20 firms representing almost one-quarter of firm revenue" (verified)
- Cite [ibisworld_54161, Competitive Forces > Concentration, PDF p.29 (printed 26)] "with over 80.0% of all consultant establishments comprising small, nonemploying companies" (verified)
- Note: None of these firms sells fractional CFO services to $2M-$20M companies. Shares are of the whole management-consulting industry, not of our niche.

**Also: ibisworld_54121c (FOUND, confidence high)**
- Value: PwC 9.7% (revenue $15.4bn); Deloitte 9.5% (revenue $15.1bn); EY 9.4% (revenue $14.9bn); KPMG 5.8% (revenue $9.2bn) | share basis: Share of total US Accounting Services (IBISWorld 54121c) industry revenue, 2026
- Summary: The Big Four hold 5.8% to 9.7% each of accounting-services revenue, and no other firm is given a share. The rest of the industry is a long tail in which 38.1% of establishments have no employees.
- Cite [ibisworld_54121c, Companies > Market Share, PDF p.32 (printed 29)] "Industry-specific company revenue as a share of total industry revenue." (verified)
- Cite [ibisworld_54121c, Companies > Market Share, PDF p.32 (printed 29)] "Pwc ($15.4bn) 9.7% Deloitte ($15.1bn) 9.5%" (verified)
- Cite [ibisworld_54121c, Companies > Market Share, PDF p.32 (printed 29)] "Ey ($14.9bn) 9.4% Kpmg ($9.2bn) 5.8%" (verified)
- Cite [ibisworld_54121c, Competitive Forces > Concentration, PDF p.27 (printed 24)] "Despite moderate concentration, the national industry's market structure is pyramid-shaped." (verified)
- Cite [ibisworld_54121c, Competitive Forces > Concentration, PDF p.27 (printed 24)] "38.1% of all accounting establishments operating as nonemployers" (verified)
- Note: The Big Four sell audit and tax to large clients, not fractional CFO services to $2M-$20M firms. The report's own text says 'moderate concentration' while its structure table says concentration is Low.

**Also: firstresearch_accounting-services (PARTIAL, confidence low)**
- Value: ADP no share given; H&R Block no share given; Paychex no share given | share basis: no share stated
- Summary: Three leading companies are named (ADP, H&R Block, Paychex) with no market shares. The only concentration measure is that the 50 largest firms hold just under half of revenue.
- Cite [firstresearch_accounting-services, Industry Overview > Fast Facts, PDF p.1 (printed 1)] "Leading companies include ADP, H&R Block, and Paychex (all based in the US)." (verified)
- Cite [firstresearch_accounting-services, Industry Description > Competitive Landscape, PDF p.5 (printed 5)] "the 50 largest US companies account for just less than 50% of revenue" (verified)
- Note: No competitor share percentages, so this signal cannot fill the 'top 3-5 with shares' requirement. Leaders named are payroll and tax-prep firms, not fractional CFO providers.

**Conflict (same_firm_different_share_basis): Market share of PwC**
- ibisworld_54121c: 9.7 (Share of total US Accounting Services (IBISWorld 54121c) industry revenue, 2026) [ibisworld_54121c, Companies > Market Share, PDF p.32 (printed 29)] "Pwc ($15.4bn) 9.7% Deloitte ($15.1bn) 9.5%"
- ibisworld_54161: 2.5–5 (IBISWorld share band (percent of 54161 industry revenue), 2026) [ibisworld_54161, Companies > Market Share, PDF p.34 (printed 31)] "Industry-specific company revenue as a share of total industry revenue."
- Why they may differ: The denominators are different industries (accounting vs management consulting), so the shares are not comparable and must not be averaged or added.

**Conflict (same_firm_different_share_basis): Market share of Deloitte**
- ibisworld_54121c: 9.5 (Share of total US Accounting Services (IBISWorld 54121c) industry revenue, 2026) [ibisworld_54121c, Companies > Market Share, PDF p.32 (printed 29)] "Pwc ($15.4bn) 9.7% Deloitte ($15.1bn) 9.5%"
- ibisworld_54161: 5.3 (Share of total US Management Consulting (IBISWorld 54161) industry revenue, 2026) [ibisworld_54161, Companies > Market Share, PDF p.34 (printed 31)] "Deloitte ($22.4bn) 5.3% Other Companies ($397.9bn) 94.7%"
- Why they may differ: The denominators are different industries (accounting vs management consulting), so the shares are not comparable and must not be averaged or added.

**Conflict (same_firm_different_share_basis): Market share of EY**
- ibisworld_54121c: 9.4 (Share of total US Accounting Services (IBISWorld 54121c) industry revenue, 2026) [ibisworld_54121c, Companies > Market Share, PDF p.32 (printed 29)] "Ey ($14.9bn) 9.4% Kpmg ($9.2bn) 5.8%"
- ibisworld_54161: 2.5–5 (IBISWorld share band (percent of 54161 industry revenue), 2026) [ibisworld_54161, Companies > Market Share, PDF p.34 (printed 31)] "Industry-specific company revenue as a share of total industry revenue."
- Why they may differ: The denominators are different industries (accounting vs management consulting), so the shares are not comparable and must not be averaged or added.

**Conflict (same_firm_different_share_basis): Market share of KPMG**
- ibisworld_54121c: 5.8 (Share of total US Accounting Services (IBISWorld 54121c) industry revenue, 2026) [ibisworld_54121c, Companies > Market Share, PDF p.32 (printed 29)] "Ey ($14.9bn) 9.4% Kpmg ($9.2bn) 5.8%"
- ibisworld_54161: 0–2.5 (IBISWorld share band (percent of 54161 industry revenue), 2026) [ibisworld_54161, Companies > Market Share, PDF p.34 (printed 31)] "Industry-specific company revenue as a share of total industry revenue."
- Why they may differ: The denominators are different industries (accounting vs management consulting), so the shares are not comparable and must not be averaged or added.

### S3 Regulatory or compliance pressure
*force: barriers to entry | status: FOUND (for the proxy industry, not the fractional niche) | quotes verified: 12*

**Primary: ibisworld_54161 (FOUND, confidence med)**
- Value: regulation level: Low, steady (IBISWorld industry-structure rating); barriers to entry level: Low, steady (IBISWorld rating); pressures: Regulatory pressure is limited and mostly federal; state consumer-privacy laws are the main enforcement for data-heavy projects; The most commonly sought licence named is the Certified Management Consultant (CMC); Sarbanes-Oxley discourages one firm providing both consulting and auditing to the same client
- Summary: IBISWorld rates regulation and entry barriers in management consulting as low and steady. The main constraints it names are privacy rules, the CMC credential, and Sarbanes-Oxley separation of consulting from audit.
- Cite [ibisworld_54161, At a Glance > Industry Structure, PDF p.9 (printed 6)] "Barriers to Entry Low Steady Regulation and Policy Low Steady" (verified)
- Cite [ibisworld_54161, External Environment > Key Takeaways, PDF p.38 (printed 35)] "Regulatory pressures are limited and concentrated at the federal level." (verified)
- Cite [ibisworld_54161, Competitive Forces > Barriers to Entry, PDF p.30 (printed 27)] "The most commonly sought-after license is the Certified Management Consultant (CMC) license" (verified)
- Cite [ibisworld_54161, External Environment > Regulation & Policy, PDF p.39 (printed 36)] "discouraging firms from providing consulting and auditing services to the same client" (verified)
- Note: The report's 'low' regulation rating is for general management consulting. A fractional CFO run by CPAs would also sit under the accounting-industry rules in the other reports. Whether the CMC licence is mandatory is not stated on the cited page.

**Also: ibisworld_54121c (FOUND, confidence high)**
- Value: regulation level: High, increasing (IBISWorld industry-structure rating); barriers to entry level: Low, increasing (IBISWorld rating); cpa education credits: 150; pressures: CPA designation requires passing the Uniform CPA Examination and holding 150 credits; SEC oversight; the Sarbanes-Oxley Act barred accountants from providing certain consultancy services to clients
- Summary: IBISWorld rates regulation of accounting services as high and rising, anchored on the CPA licence (exam plus 150 credits) and SEC/Sarbanes-Oxley rules, yet still rates the barriers to entry as low.
- Cite [ibisworld_54121c, At a Glance > Industry Structure, PDF p.7 (printed 4)] "Barriers to Entry Low Increasing Regulation and Policy High Increasing" (verified)
- Cite [ibisworld_54121c, External Environment > Key Takeaways, PDF p.38 (printed 35)] "Accountants face considerable regulatory oversight." (verified)
- Cite [ibisworld_54121c, External Environment > Regulation & Policy > CPA requirement, PDF p.39 (printed 36)] "To be designated as a CPA, an individual must pass the Uniform CPA Examination and have 150 credits" (verified)
- Cite [ibisworld_54121c, External Environment > Regulation & Policy > SEC, PDF p.40 (printed 37)] "barred accountants from providing certain consultancy services to clients under the Sarbanes-Oxley Act of 2002" (verified)
- Note: This is the regulation of CPA firms. The source does not say whether providing fractional CFO advice requires a CPA licence.

**Also: firstresearch_accounting-services (FOUND, confidence med)**
- Value: regulation level: High regulatory complexity (the report's own challenge heading); pressures: Directives from the IRS, SEC and PCAOB, plus self-regulation by FASB and AICPA; Hundreds of rules and opinions to track, a particular burden for small firms; State licensing of accountants and firms, with some reciprocity; Tax preparers must register with the IRS, pass competency exams and take continuing education
- Summary: The report lists 'High Regulatory Complexity' as the first business challenge: many directives from the IRS and SEC, hundreds of rules, state licensing, and registration requirements for tax preparers.
- Cite [firstresearch_accounting-services, Challenges, Trends & Opportunities > High Regulatory Complexity, PDF p.14 (printed 14)] "Accounting firms must comply with numerous directives from government and industry groups including the IRS and SEC." (verified)
- Cite [firstresearch_accounting-services, Challenges, Trends & Opportunities > High Regulatory Complexity, PDF p.14 (printed 14)] "Practices must stay current with hundreds of official rules and formal opinions, a special challenge for small firms with little or no staff." (verified)
- Cite [firstresearch_accounting-services, Industry Description > Finance & Regulation > Regulation, PDF p.7 (printed 7)] "Accountants and accounting firms must have licenses in the states where they do business." (verified)
- Cite [firstresearch_accounting-services, Industry Description > Finance & Regulation > Regulation, PDF p.7 (printed 7)] "Increased regulations now require tax preparers to register with the IRS, pass competency exams, and fulfill continuing education credits." (verified)
- Note: Describes regulation of accounting firms. Whether a non-audit fractional CFO firm is covered is not stated.

**Conflict (rating_disagreement_different_scope): Regulation & policy rating**
- firstresearch_accounting-services: High regulatory complexity (the report's own challenge heading) (First Research rating/wording) [firstresearch_accounting-services, Challenges, Trends & Opportunities > High Regulatory Complexity, PDF p.14 (printed 14)] "Accounting firms must comply with numerous directives from government and industry groups including the IRS and SEC."
- ibisworld_54121c: High, increasing (IBISWorld industry-structure rating) (IBISWorld rating/wording) [ibisworld_54121c, At a Glance > Industry Structure, PDF p.7 (printed 4)] "Barriers to Entry Low Increasing Regulation and Policy High Increasing"
- ibisworld_54161: Low, steady (IBISWorld industry-structure rating) (IBISWorld rating/wording) [ibisworld_54161, At a Glance > Industry Structure, PDF p.9 (printed 6)] "Barriers to Entry Low Steady Regulation and Policy Low Steady"
- Why they may differ: Each rating is for a different industry (management consulting vs accounting firms) and the publishers word them differently, so they are not the same measurement; shown side by side, not merged.

### S4 Key-input concentration or fragility (talent, software)
*force: supplier power | status: FOUND (for the proxy industry, not the fractional niche) | quotes verified: 11*

**Primary: ibisworld_54161 (FOUND, confidence med)**
- Value: inputs: input: Skilled consultants (labour), finding: Wages are the industry's largest cost; talent is hard and expensive to hire and retain., mean salary usd: 113790 | input: Computers and software (equipment suppliers), finding: The report says supplier influence is elevated because switching computer and software suppliers is costly.
- Summary: The key inputs are skilled consultants and computing/software. Wages are the largest cost category (mean management-consultant salary $113,790 in 2025 per BLS), and the report says supplier influence over equipment and software is elevated.
- Cite [ibisworld_54161, Competitive Forces > Buyer & Supplier Power, PDF p.33 (printed 30)] "Suppliers' influence remains elevated due to the valuable machinery and equipment they procure for consultants' services." (verified)
- Cite [ibisworld_54161, Competitive Forces > Barriers to Entry > Labor Expenses, PDF p.31 (printed 28)] "Attracting and retaining top talent involves high salaries and benefits" (verified)
- Cite [ibisworld_54161, Financial Benchmarks > Cost Structure, PDF p.42 (printed 39)] "Wages represent the industry's most significant expense category." (verified)
- Cite [ibisworld_54161, Financial Benchmarks > Cost Structure, PDF p.42 (printed 39)] "the mean annual management consultant salary accelerated to $113,790 in 2025" (verified)
- Note: The numeric supplier-power rating label sits on a page break and could not be quoted, so it is left null. No credentialed-talent supply data specific to CFO-level staff.

**Also: ibisworld_54121c (FOUND, confidence med)**
- Value: inputs: input: CPA-credentialed accountants (labour), finding: Wages are the largest and most consistent cost; demand has outpaced new accountants entering practice., median salary 2024 usd: 81680, median salary 2025 usd: 83680 | input: Technology networks and software, finding: Digital service delivery depends on fast, reliable networks whose costs move with energy prices.
- Summary: The scarce input is credentialed accountants: wages are the largest cost, the median accountant salary rose from $81,680 to $83,680 in a year, and demand has outrun new entrants. Technology and network suppliers are the second input.
- Cite [ibisworld_54121c, Financial Benchmarks > Cost Structure, PDF p.42 (printed 39)] "Wages remain the largest and most consistent expenditure for accounting services" (verified)
- Cite [ibisworld_54121c, Financial Benchmarks > Cost Structure, PDF p.42 (printed 39)] "median accountant salary, which rose from $81,680 in 2024 to $83,680 in 2025" (verified)
- Cite [ibisworld_54121c, At a Glance > Executive Summary, PDF p.7 (printed 4)] "increased demand for accounting services has drastically outpaced the number of new accountants that have begun operating" (verified)
- Cite [ibisworld_54121c, Competitive Forces > Buyer & Supplier Power > Suppliers, PDF p.30 (printed 27)] "The digitization of accounting services heavily depends on fast and reliable technological networks" (verified)
- Note: The numeric supplier-power rating straddles a page break and is not quoted, so it is left null. The salary figures are for accountants generally, not CFO-level staff.

**Also: firstresearch_accounting-services (PARTIAL, confidence low)**
- Value: inputs: input: Skilled personnel (partners and junior accountants), finding: Firms depend heavily on senior partners' reputation and junior accountants' competence, and recruiting well-qualified specialists is getting harder. | input: Accounting software vendors, finding: Software producers update industry-specific products to track rule changes; no vendor concentration or pricing is given.
- Summary: The report treats staffing as the main input constraint (dependence on senior partners, difficulty recruiting specialists) and mentions software vendors only as tools that track rule changes; it gives no supplier concentration data.
- Cite [firstresearch_accounting-services, Challenges, Trends & Opportunities > Dependence on Skilled Personnel, PDF p.14 (printed 14)] "Accounting firms depend heavily on the reputation and expertise of senior partners and the competence of junior accountants." (verified)
- Cite [firstresearch_accounting-services, Executive Insight > Human Resources > Recruiting Specialists, PDF p.12 (printed 12)] "recruiting well-qualified specialists becomes more difficult" (verified)
- Cite [firstresearch_accounting-services, Industry Description > Technology, PDF p.6 (printed 6)] "Software producers update industry-specific products to reflect changes in accounting, tax, and auditing rules." (verified)
- Note: Supplier power as a concept is not analysed in this report; only the dependence on people and software is stated.

### S5 Customer concentration or fragmentation
*force: buyer power | status: FOUND (for the proxy industry, not the fractional niche) | quotes verified: 14*

**Primary: ibisworld_54161 (FOUND, confidence med)**
- Value: Financial services companies 27.7%; Households, consumers and individuals 19.0%; Government organizations and Not-for-profit 18.4%; Energy, resource and industrial 15.0%; Technology, media and telecommunications 11.2%; Healthcare and life sciences 8.7% | customer structure: Diversified across customer classes; SWOT lists low customer-class concentration. Largest segment is financial services; households and individuals (including nonemploying businesses and sole proprietors) are second., buyer power rating: High (larger corporate buyers wield bargaining power)
- Summary: No customer class dominates: financial services is the largest at 27.7% of 2026 revenue, and no segment is above 30%. The report says large corporate buyers hold significant bargaining power.
- Cite [ibisworld_54161, At a Glance > SWOT, PDF p.9 (printed 6)] "Strengths Low Capital Requirements Low Customer Class Concentration" (verified)
- Cite [ibisworld_54161, Products and Markets > Major Markets Segmentation, PDF p.23 (printed 20)] "Financial services companies ($116.4bn) 27.7%" (verified)
- Cite [ibisworld_54161, Products and Markets > Major Markets Segmentation, PDF p.23 (printed 20)] "Households, consumers and individuals ($79.8bn) 19.0%" (verified)
- Cite [ibisworld_54161, Products and Markets > Major Markets Segmentation, PDF p.23 (printed 20)] "Government organizations and Not-for-profit ($77.3bn) 18.4% Energy, resource and industrial ($63.0bn) 15.0%" (verified)
- Cite [ibisworld_54161, Products and Markets > Major Markets Segmentation, PDF p.23 (printed 20)] "Technology, media and telecommunications companies ($47.1bn) 11.2% Healthcare and life sciences sector ($36.6bn) 8.7%" (verified)
- Cite [ibisworld_54161, Competitive Forces > Buyer & Supplier Power, PDF p.32 (printed 29)] "Larger companies wield significant bargaining power, prioritizing consultants' quality of service, brand name and pricing." (verified)
- Note: Segments are by client type, not client size. The 'Households, consumers and individuals' segment is said to include nonemploying businesses and sole proprietorships, the closest hint of small-business buyers.

**Also: ibisworld_54121c (FOUND, confidence med)**
- Value: Finance sector 24.9%; Retail sector 13.2%; Individual 12.4%; Public 12.0%; Utilities and mining sector 10.5%; Manufacturing and industrial sector 10.1%; Nonprofit 3.4%; Other businesses 13.5% | customer structure: Fragmented across customer classes; SWOT lists low customer-class concentration. Corporate clients (finance, retail, utilities, manufacturing) dominate; individuals are 12.4%., buyer power rating: Moderate; low switching costs
- Summary: No customer class exceeds a quarter of revenue (finance is largest at 24.9%), and the report rates buyer power as moderate with low switching costs, so clients can move providers or use software.
- Cite [ibisworld_54121c, Products and Markets > Major Markets Segmentation, PDF p.21 (printed 18)] "Finance sector ($39.4bn) 24.9% Retail sector ($20.9bn) 13.2% Individual ($19.6bn) 12.4%" (verified)
- Cite [ibisworld_54121c, Products and Markets > Major Markets Segmentation, PDF p.21 (printed 18)] "Public ($19.0bn) 12.0% Utilities and mining sector ($16.6bn) 10.5% Manufacturing and industrial sector ($16.0bn) 10.1% Nonprofit ($5.4bn) 3.4% Other businesses ($21.4bn) 13.5%" (verified)
- Cite [ibisworld_54121c, At a Glance > SWOT, PDF p.7 (printed 4)] "Low Capital Requirements Low Customer Class Concentration" (verified)
- Cite [ibisworld_54121c, Competitive Forces > Buyer & Supplier Power, PDF p.30 (printed 27)] "Moderate Steady Buyers: Low switching costs" (verified)
- Cite [ibisworld_54121c, Competitive Forces > Buyer & Supplier Power, PDF p.30 (printed 27)] "the accounting services space has low switching costs" (verified)
- Note: Segmentation is by client type, not size, so the $2M-$20M band cannot be isolated. The report says small businesses are an influential driver but gives no share.

**Also: firstresearch_accounting-services (PARTIAL, confidence low)**
- Value: customer structure: Customers are businesses, nonprofits, government and individuals; some practices specialize by segment or industry. No segment shares are given.; pricing note: Clients often compare firms on the price of basic services.
- Summary: Customer types are listed with no shares, so concentration cannot be measured. Buyers are described as comparing firms on the price of basic services, and small business owners are said to rely heavily on their accountants for advice.
- Cite [firstresearch_accounting-services, Industry Description > Sales & Marketing, PDF p.6 (printed 6)] "Typical customers are businesses, nonprofits, government, and individuals" (verified)
- Cite [firstresearch_accounting-services, Executive Insight > Sales/Marketing > Developing Pricing Strategy, PDF p.12 (printed 12)] "Potential clients often compare accounting firms by the price of basic services, adding importance to competitive pricing." (verified)
- Cite [firstresearch_accounting-services, Industry Description > Products & Operation, PDF p.5 (printed 5)] "Small business owners often rely heavily on their accounting firms for advice." (verified)
- Note: The only small-business statement is that owners rely on accountants for advice, which supports demand for advisory work but does not quantify buyers.

**Conflict (rating_disagreement_different_scope): Buyer power rating**
- ibisworld_54121c: Moderate; low switching costs (IBISWorld rating/wording) [ibisworld_54121c, Products and Markets > Major Markets Segmentation, PDF p.21 (printed 18)] "Finance sector ($39.4bn) 24.9% Retail sector ($20.9bn) 13.2% Individual ($19.6bn) 12.4%"
- ibisworld_54161: High (larger corporate buyers wield bargaining power) (IBISWorld rating/wording) [ibisworld_54161, At a Glance > SWOT, PDF p.9 (printed 6)] "Strengths Low Capital Requirements Low Customer Class Concentration"
- Why they may differ: Each rating is for a different industry (management consulting vs accounting firms) and the publishers word them differently, so they are not the same measurement; shown side by side, not merged.

### S6 Biggest trend of the next five years
*force: new entrants / rivalry (niche specialization) | status: FOUND (for the proxy industry, not the fractional niche) | quotes verified: 6*

**Primary: ibisworld_54161 (FOUND, confidence med)**
- Value: trend: Specialization: niche firms, especially technology-focused ones, are expected to enter and small consultancies are told to specialize to compete with large firms.
- Summary: The report expects more niche entrants specializing in new technology and says specialization is necessary for smaller consultancies to defend against larger rivals.
- Cite [ibisworld_54161, At a Glance > Executive Summary, PDF p.9 (printed 6)] "the entry of niche firms specializing in new technology (IT, VR, AR and AI) is expected to increase" (verified)
- Cite [ibisworld_54161, Performance > Outlook, PDF p.14 (printed 11)] "Specialization is necessary, as it helps smaller consultancies protect against competitive threats by providing timeliness, quality and validity in client consultations." (verified)
- Note: The report does not rank trends; the selection and the reason are the extractor's.

**Also: ibisworld_54121c (FOUND, confidence high)**
- Value: trend: Accounting firms expanding into advisory and consulting services as automation frees capacity.
- Summary: The report says the most notable coming development is greater investment in advisory services, driven by the profit in consulting and by automation of low-value tasks.
- Cite [ibisworld_54121c, Performance > Outlook, PDF p.12 (printed 9)] "The most notable development for accounting service providers will be the increased investment in advisory services." (verified)
- Cite [ibisworld_54121c, Performance > Outlook, PDF p.12 (printed 9)] "the massive profit associated with consulting services will cause companies to expand advisory operations" (verified)
- Note: The report does not say the advisory push is aimed at small businesses.

**Also: firstresearch_accounting-services (FOUND, confidence med)**
- Value: trend: Cloud computing, SaaS and hosted solutions, alongside AI productivity tools, are becoming standard for small accounting firms.
- Summary: Cloud, SaaS and hosted software are becoming common in small accounting firms, and the report says AI is a major help in raising productivity.
- Cite [firstresearch_accounting-services, Challenges, Trends & Opportunities > Business Trends > Firms Update Technology, Move Operations Online, PDF p.14 (printed 14)] "Cloud computing, software as a service applications (SaaS), and hosted solutions are becoming increasingly common among small accounting firms." (verified)
- Cite [firstresearch_accounting-services, Industry Description > Technology, PDF p.6 (printed 6)] "Artificial Intelligence (AI) is a major help in increasing productivity." (verified)
- Note: The report does not rank trends; other listed trends include alignment with international accounting standards and online tax preparation.

### S7 Biggest threat of the next five years
*force: substitutes | status: FOUND (for the proxy industry, not the fractional niche) | quotes verified: 6*

**Primary: ibisworld_54161 (FOUND, confidence med)**
- Value: threat: Substitutes: in-house teams and generative-AI or software tools that give away analysis consultants used to charge for.
- Summary: In-house alternatives and generative AI are the threats the report stresses most for the client segment that includes small businesses.
- Cite [ibisworld_54161, Products and Markets > Major Markets, PDF p.22 (printed 19)] "in-house channels remain the largest competitive threat and ate into the segment's revenue stream" (verified)
- Cite [ibisworld_54161, Performance > Current Performance, PDF p.13 (printed 10)] "The proliferation of generative AI technology threatens management consultants by efficiently compiling research and offering free analysis" (verified)
- Note: The report's own Substitutes rating is only moderate; 'biggest' is the extractor's choice, made on the strength of the two quotes.

**Also: ibisworld_54121c (FOUND, confidence med)**
- Value: threat: DIY and software substitutes: AI-enabled automation and low-cost providers such as TurboTax and H&R Block.
- Summary: Automation is helping accountants but also enables do-it-yourself substitutes, especially for smaller tax and statement-review work, and TurboTax and H&R Block are named as growing competitors.
- Cite [ibisworld_54121c, Performance > Current Performance > Automation and AI, PDF p.12 (printed 9)] "it also poses a significant competitive threat via DIY solutions, particularly for smaller tax preparation or statement review cases" (verified)
- Cite [ibisworld_54121c, Performance > Outlook > Consumer competition, PDF p.13 (printed 10)] "great competition from alternative accounting service providers, such as TurboTax and H&R Block" (verified)
- Note: Internal tension: the industry-structure summary rates the substitutes force low while the text calls DIY a significant threat. The threat is stated mainly for tax preparation, not CFO-style work.

**Also: firstresearch_accounting-services (FOUND, confidence med)**
- Value: threat: A slow economy cutting business demand for accounting services.
- Summary: The report's headline risk is that a slow economy reduces business needs; separately, it says accounting practices that act as consultants shaping clients' business decisions face high litigation risk.
- Cite [firstresearch_accounting-services, Industry Overview > Industry Growth Rating, PDF p.1 (printed 1)] "Risk: Slow economy cuts business needs" (verified)
- Cite [firstresearch_accounting-services, Challenges, Trends & Opportunities > Litigation Risk, PDF p.14 (printed 14)] "Accounting practices that serve as consultants in shaping clients' business decisions are at high risk." (verified)
- Note: The litigation-risk statement concerns firms that consult on clients' business decisions, which is close to what a fractional CFO does; it is not the chosen threat but is worth a reader's attention.

## Sources

- **Accounting Services in the US**, IBISWorld, May 2026, code: 54121c. Find it: BYU Library > Business databases > IBISWorld > search the report title (US industry reports).
- **Management Consulting in the US**, IBISWorld, August 2026, code: 54161. Find it: BYU Library > Business databases > IBISWorld > search the report title (US industry reports).
- **First Research Industry Profile: Accounting Services**, First Research (Dun & Bradstreet), accessed via D&B Hoovers, July 2025, code: not stated. Find it: BYU Library > Business databases > D&B Hoovers > Industries > First Research > 'Accounting Services' (Industry Overview).

## Gaps

- **PARTIAL** (S1, firstresearch_accounting-services): Broader industry (accounting, tax prep, bookkeeping, payroll). The report was published July 2025, older than both IBISWorld reports. *To find it:* A report on a closer proxy than all management consulting or all accounting. Census Bureau Economic Census / Nonemployer Statistics receipts for NAICS 541611 and 541219 (census.gov/naics for the code, data.census.gov for the tables), and IBISWorld 'financial management consulting' segment data.
- **PARTIAL + low confidence** (S2, firstresearch_accounting-services): No competitor share percentages, so this signal cannot fill the 'top 3-5 with shares' requirement. Leaders named are payroll and tax-prep firms, not fractional CFO providers. *To find it:* No report here gives a niche share. Look for a vendor report on outsourced / virtual / fractional CFO or 'bookkeeping and advisory' services (existence not confirmed; not searched), Census Economic Census concentration ratios (top-4/8/20/50 share) by NAICS, or bottom-up counts from state CPA-society firm directories and LinkedIn / Google Business listings.
- **PARTIAL + low confidence** (S4, firstresearch_accounting-services): Supplier power as a concept is not analysed in this report; only the dependence on people and software is stated. *To find it:* BLS Occupational Employment and Wage Statistics for financial managers and accountants by state; accounting-software vendor market-share studies (QuickBooks, Xero, NetSuite class); AICPA firm-staffing surveys on CPA supply.
- **PARTIAL + low confidence** (S5, firstresearch_accounting-services): The only small-business statement is that owners rely on accountants for advice, which supports demand for advisory work but does not quantify buyers. *To find it:* Census Statistics of U.S. Businesses (SUSB) receipts-size tables and SBA Office of Advocacy small-business profiles for the $2M-$20M revenue band; a buyer survey (owners' willingness to pay for part-time finance leadership).
- **unresolved conflict: Market size (USD bn)**: Values differ: firstresearch_accounting-services = 153; ibisworld_54121c = 158.4. Both describe accounting services but with different scope (First Research includes payroll and tax preparation), vintage (July 2025 vs May 2026) and, for growth, different periods and price basis. The reports do not say which is right. *To find it:* The publisher's methodology note (IBISWorld / First Research analyst support) or a primary statistical source such as the Census Economic Census.
- **unresolved conflict: Forecast 5-yr CAGR (%)**: Values differ: firstresearch_accounting-services = 4; ibisworld_54121c = 2.1. Both describe accounting services but with different scope (First Research includes payroll and tax preparation), vintage (July 2025 vs May 2026) and, for growth, different periods and price basis. The reports do not say which is right. *To find it:* The publisher's methodology note (IBISWorld / First Research analyst support) or a primary statistical source such as the Census Economic Census.
- **unresolved conflict: Market size (USD bn)**: Values differ: ibisworld_54121c = 158.4; ibisworld_54121c = 157.4. Executive Summary text (PDF pp.7-8) versus At a Glance and Performance Snapshot (PDF pp.6, 9) within the same report *To find it:* The publisher's methodology note (IBISWorld / First Research analyst support) or a primary statistical source such as the Census Economic Census.
- **unresolved conflict: Historical 5-yr CAGR (%)**: Values differ: ibisworld_54121c = 1.4; ibisworld_54121c = 1.3. Executive Summary text (PDF pp.7-8) versus At a Glance and Performance Snapshot (PDF pp.6, 9) within the same report *To find it:* The publisher's methodology note (IBISWorld / First Research analyst support) or a primary statistical source such as the Census Economic Census.
- **unresolved conflict: Forecast 5-yr CAGR (%)**: Values differ: ibisworld_54121c = 2.1; ibisworld_54121c = 2.3. Executive Summary text (PDF pp.7-8) versus At a Glance and Performance Snapshot (PDF pp.6, 9) within the same report *To find it:* The publisher's methodology note (IBISWorld / First Research analyst support) or a primary statistical source such as the Census Economic Census.
- **No industry code for fractional CFO**: Fractional CFO has no NAICS code, so every number in this brief describes a PROXY industry (chosen: 541611, Administrative Management and General Management Consulting Services). Growth, size and share for the fractional niche itself are unknown, and the proxy may grow at a different rate. *To find it:* Nothing will publish this directly; a bottom-up estimate (number of $2M-$20M firms x adoption rate x average retainer) built from Census SUSB plus buyer interviews.
- **No report gives market share for the fractional niche**: The only shares printed are for the Big Four and a few global firms (of management consulting or of CPA accounting); First Research prints none. None of those firms is a competitor for $2M-$20M clients in the way a fractional CFO boutique or platform would be. *To find it:* No report here gives a niche share. Look for a vendor report on outsourced / virtual / fractional CFO or 'bookkeeping and advisory' services (existence not confirmed; not searched), Census Economic Census concentration ratios (top-4/8/20/50 share) by NAICS, or bottom-up counts from state CPA-society firm directories and LinkedIn / Google Business listings.
- **Reports do not line up with the chosen code**: firstresearch_accounting-services: No code stated, so a match cannot be confirmed. The activities listed (auditing, bookkeeping, payroll, tax) describe the accounting family (5412), not management consulting 541611.; ibisworld_54121c: Mismatch: covers 541211 and 541219, the accounting neighbors rejected in Stage 1, not 541611. Audit is about half of its revenue, which fractional CFO work is not.; ibisworld_54161: Superset of the chosen 541611 (all management consulting incl. marketing, operations, HR, IT); financial management consulting is only one product line. *To find it:* Buy or access a report whose stated code matches the chosen NAICS, or one on a niche named 'outsourced accounting/CFO services'.
- **Mixed and dated vintages**: Publication dates: firstresearch_accounting-services = July 2025, ibisworld_54121c = May 2026, ibisworld_54161 = August 2026. The First Research printout also embeds valuation multiples last updated January 2023 and an economic indicator dated May 2026 inside a report whose data was published July 2025. *To find it:* Re-pull each report at analysis time and record the publication date next to each number.
- **No pricing, retainer or margin data for the niche**: None of the seven signals covers what fractional CFOs charge or earn; the IBISWorld profit margins are for whole industries. *To find it:* Interviews and public rate cards; AICPA / trade compensation surveys.
- **Verification proves quotes exist, not that they were understood**: Code confirmed each quote is on its cited page. It cannot confirm that the LLM's summary, its choice of 'biggest' trend/threat, or its reading of a table row is right. *To find it:* A human reading the spot-check list against the PDFs (see the method section).

## Spot-check list (5 random findings, seed 20260919)

- S7 Biggest threat of the next five years: firstresearch_accounting-services, PDF p.1 (printed 1): "Risk: Slow economy cuts business needs"
- S2 Top competitors and market share: ibisworld_54161, PDF p.34 (printed 31): "Accenture Plc 2.5–5 10,000+ EY 2.5–5 10,000+ PwC 2.5–5 10,000+ KPMG 0–2.5 10,000+"
- S4 Key-input concentration or fragility (talent, software): firstresearch_accounting-services, PDF p.14 (printed 14): "Accounting firms depend heavily on the reputation and expertise of senior partners and the competence of junior accountants."
- S2 Top competitors and market share: ibisworld_54121c, PDF p.32 (printed 29): "Pwc ($15.4bn) 9.7% Deloitte ($15.1bn) 9.5%"
- S4 Key-input concentration or fragility (talent, software): ibisworld_54121c, PDF p.42 (printed 39): "median accountant salary, which rose from $81,680 in 2024 to $83,680 in 2025"

Hand-checked by me: [ ] of [ ] citations. (left blank on purpose; to be filled in by the student)
