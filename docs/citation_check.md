# Citation check: every external number used in the pre-registration and the preprint

14 November 2026. Each number cited from an outside source in `docs/preregistro_osf_v2.md` (v2) or
`paper/manuscript.md`, checked against the original where it was reachable: PubMed abstracts and PubMed Central
full texts (NCBI E-utilities), the publisher or agency page, and Crossref for bibliographic details.

Status: **verified** (number found in the original), **verified, with caveat**, **partial** (original reached but the
number is not in the part available), **not verified** (only a press or secondary summary), **not reachable**.

## A. Numbers that set pre-registered parameters (frozen at registration)

| # | Claim | Used in | Source checked | Status | Note |
| --- | --- | --- | --- | --- | --- |
| A1 | One-year discontinuation 64.8% without and 46.5% with type 2 diabetes; 125,474 adults | Q19 (H5 persistence), Q24 | Rodriguez et al. 2025, JAMA Netw Open 8(1):e2457349, PMID 39888616 (abstract) | verified | Cohort: dual-labeled GLP-1 RA (liraglutide, semaglutide, tirzepatide) initiators 2018-2023, BMI ≥ 27; Kaplan-Meier estimates |
| A2 | 12-month on-treatment weight loss 8.3% semaglutide, 15.3% tirzepatide | Q19 (H5 loss of persistent users) | Rodriguez et al. 2024, JAMA Intern Med 184(9):1056-1064, PMID 38976257 (PMC full text) | verified, with caveat | −8.3% (95% CI −9.0 to −7.6) and −15.3% (−16.0 to −14.5) at 12 months among patients still on treatment, propensity-matched; formulations labeled for type 2 diabetes. Fits "persistent users" |
| A3 | One-year loss 3.6% (stopped within 3 months) and 6.8% (stopped at 3-12 months) | Q19 (H5 loss of non-persistent users), Q24 | Gasoyan et al. 2025, Obesity 33(9):1657-1667, PMID 40491239 (abstract) | verified | Adults without type 2 diabetes; same paper: 11.9% without discontinuation, 8.7% overall |
| A4 | −14.9% at 68 weeks (STEP 1) | Q19 (H5 range) | Wilding et al. 2021, NEJM 384(11):989-1002, PMID 33567185 | verified | Semaglutide 2.4 mg, no diabetes; placebo −2.4% |
| A5 | −20.9% at 72 weeks with 15 mg (SURMOUNT-1) | Q19 (H5 range) | Jastreboff et al. 2022, NEJM 387(3):205-216, PMID 35658024 | verified | Also −15.0% (5 mg) and −19.5% (10 mg) |
| A6 | 26.5% of adults with diagnosed diabetes used injectable GLP-1 in 2024 (NHIS) | Q4 (H2), Q20 (SESOI rationale), manuscript | NCHS Data Brief 537 (agency page) | verified | Title: "GLP-1 Injectable Use Among Adults With Diagnosed Diabetes: United States, 2024" |
| A7 | 16.7% (healthy weight) to 32.4% (obesity) among adults with diabetes (NHIS 2024) | Q4 (H3) | NCHS Data Brief 537 | verified | Overweight 22.2% |
| A8 | 12% of adults and 45% of adults with diabetes currently taking a GLP-1 (KFF, Nov 2025) | Q4, Q20, H5 upper rate, manuscript | KFF poll page | verified | Fieldwork 27 Oct-2 Nov 2025, n = 1,350; 57% of adults with diabetes ever used |
| A9 | MEPS 2024 adult use rate (lower bound of H5) | Q19 | Computed from MEPS 2024 by the project | n/a | 4.99% of adults with a GLP-1 purchase (weighted), counted 14 Nov 2026 |

## B. Numbers in the rationale and introduction

| # | Claim | Used in | Source checked | Status | Note |
| --- | --- | --- | --- | --- | --- |
| B1 | Measured BMI and obesity fell in 2023 among 16.7 million adults; largest fall in the South, where GLP-1 dispensing was highest | Q4, Q18, manuscript | Rader, Hazan, Brownstein 2024, JAMA Health Forum 5(12):e243685, PMID 39671205 (PMC full text) | verified, with caveat | 16,743,822 adults; mean BMI 30.24 (2022) → 30.21 (2023); dispensing South 6.0%, Midwest 5.1%, Northeast 4.4%, West 3.4%. **The obesity percentages 46.2% → 45.6% (2021 → 2023) quoted in the literature review are from the unweighted sensitivity analysis**; the census-weighted estimates are only in the figure |
| B2 | GLP-1 RA use among adults with diabetes and overweight rose from 3.8% (2010) to 11.5% (2019) | Q4 (H2), manuscript | Galindo et al. 2023, Obesity 31(12):2924-2935, PMID 37919239 (PMC full text) | verified | MEPS 2010-2019, adults with diabetes and BMI ≥ 27 (≥ 25 for Asian adults). The abstract gives only all weight-reducing medications (6.4% → 21.2%) |
| B3 | Gallup: 39.9% (2022) → 37.0% (2025); −4.3 at 40-49, −5.0 at 50-64; use 5.8% → 12.4% | Q3, Q4, Q18, H0, manuscript | Gallup article, Oct 2025 | verified | 14 Nov 2026 (`dados_externos/published_estimates.csv`) |
| B4 | Gallup 65+: +0.8 | literature review only | Gallup article | not verified | Text says "essentially unchanged"; not used in v2 or the manuscript |
| B5 | Gallup 2026: 36.8% | H0, manuscript (source note) | Gallup article, Jul 2026 | verified | Revised 8 Sep 2026 after reweighting |
| B6 | NHANES 40.3% (Aug 2021-Aug 2023), 41.9% (2017-2020) and earlier cycles | Q18, H0, manuscript | NCHS Data Brief 508 | verified | Age-adjusted, adults 20+ |
| B7 | Epic Research 2026 (fall in obesity; rising prescriptions) | Q4, Q18 (cited without numbers) | press summary only | not verified | Original not reached; no number from it is used |
| B8 | State counts, Trust for America's Health 2025 and CDC maps 2026 | Q18 (cited without numbers) | — | not verified | No number used |

## C. Methods statements

| # | Claim | Used in | Source checked | Status | Note |
| --- | --- | --- | --- | --- | --- |
| C1 | With a continuous treatment and no untreated group only comparisons across doses are identified; they are causal only under stronger ("strong") parallel trends | Q4, Q19 (H4) | Callaway, Goodman-Bacon, Sant'Anna, arXiv 2107.02637 (draft of 31 Dec 2025; full text) | verified | Section 3: with no untreated units, under parallel trends E[ΔY\|D=d] − E[ΔY\|D=d_L] = ATT(d\|d) − ATT(d_L\|d_L), which mixes the causal response with selection bias; "continuous variation in the dose can be used to learn about causal effects even if there is no untreated comparison group, but interpreting these results as causal effects of the treatments requires strengthening Assumption PT". Their name for the stronger assumption is "strong parallel trends" |
| C2 | DiNardo, Fortin, Lemieux 1996; Firpo, Fortin, Lemieux 2009; Park, Gelman, Bafumi 2004; Rambachan, Roth 2023; Rao, Wu 1988; Lakens 2017; Van den Akker et al. 2021; Webb 2023 | Q19, Q22-Q24, manuscript | Crossref | verified (bibliographic) | Details corrected in `paper/references.bib` |
| C3 | Holm 1979, Scand J Stat 6(2):65-70 | Q22, manuscript | OpenAlex (JSTOR record) | verified (bibliographic) | Volume 6, pages 65-70, DOI 10.2307/4615733 |
| C4 | Rubin 1987 (book) | Q19, manuscript | — | not verified | Standard reference |

## D. Inputs of the Q24 external and self-report analyses

| # | Claim | Used in | Source checked | Status | Note |
| --- | --- | --- | --- | --- | --- |
| D1 | DeCleene et al. 2026 projection: 42.5% of adults in 2022 → 46.9% in 2035 (bias-corrected, ages ≥ 20) | Q24 external counterfactual | JAMA 335(11):975-985, PMID 41604179 (abstract) | verified | Implied average change ≈ +0.34 pp a year (linear between 2022 and 2035). **Implemented** in `sensitivity.q24_external` |
| D2 | Ward et al. 2019 projection: national adult obesity 35.1% (2010), 42.0% (2020, 95% CI 41.2-42.7), 48.9% (2030, 47.7-50.1); BRFSS 1993-2016 corrected with NHANES, adults 18+ | Q24 external counterfactual | NEJM 381(25):2440-2450 and supplementary appendix, Table 8.1.1 (full text, saved by the author on 15 Nov 2026) | verified | The article gives only the 2030 figures; the 2010-2030 path is in the appendix table. The gain is 6.9 pp in each decade, so a straight line between 2020 and 2030 (+0.69 pp a year, +2.07 pp over 2022-2025) follows the fitted curve closely. **Implemented** in `sensitivity.q24_external` |
| D3 | NHANES-calibrated, quantile-specific correction of self-reported BMI (Ward et al. 2019) | Q24 self-report correction | Supplementary appendix, section 2 (full text) | verified | By sex and period (1993-1994, 1999-2004, 2005-2010, 2011-2016): measured minus reported BMI by quantile, smoothed with cubic splines, added to each BRFSS respondent at the weighted quantile of their reported BMI, plus N(0, 0.5) noise for rounding; checked with two-sample Kolmogorov-Smirnov tests. NHANES adults 18+, pregnant women excluded. The paper does not report the quantile grid or the spline smoothing. **Implemented** in `self_report.py` (choices in `decision_log.md`, section 7) |

## E. Exploratory analysis (Q25)

| # | Claim | Used in | Source checked | Status | Note |
| --- | --- | --- | --- | --- | --- |
| E1 | State dates of Medicaid coverage of GLP-1s for obesity | Q25 | Wing et al. 2026, NBER w34949 (full text, Table 2) | verified | 17 states, first coverage from MI (2022-Q1) to TN and UT (2025-Q3), with the quarter each drug was added and later terminations and restrictions; saved in `dados_externos/medicaid_glp1_obesity_coverage.csv` |
| E2 | Same | Q25 | Khanna, Wang, Venkataramani 2026, JAMA Health Forum 7(9):e263353, PMC13615463 (full text) | verified (consistent) | Treated states (CA, PA, MN, MA, MI, MS, NH, VA, RI) agree with Wing et al.; the paper classifies them by prior-authorization stringency and discusses why its substitution findings differ from Wing et al. |

## What is left for the author to read

Updated 15 November 2026: Ward et al. (2019) was read from the copy the author saved locally (article and
supplementary appendix, kept outside the repository), which completes D2 and D3. Nothing that enters an analysis is
left unread. Optional: Epic Research (B7), TFAH and CDC maps (B8), cited without numbers.

No number that enters a pre-registered parameter (section A) disagreed with its source.
