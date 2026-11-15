# OSF pre-registration: GLP-1 and the US adult obesity curve (draft, version 2)

14 November 2026 · Marsel Eleutério

Version 2 fills the fields that depended on the download scripts (Q7, Q8, Q10, Q12, Q13, Q18, Q21, Q23) with the
results of 14 November 2026 and revises the inference and model choices listed in `decision_log.md` (Q19, Q21,
Q22, Q23). Version 1 is kept unchanged in `preregistro_osf_rascunho.md`; the differences are in the git history.

Draft of the 25 answers of the OSF Secondary Data Preregistration template, in the order of the form, to be
reviewed and pasted field by field. Text in brackets is still to be completed.

## Before submitting

- [x] ORCID in Q2 (0009-0008-0021-8866)
- [x] Run the download, extract and validate scripts and record the download dates in Q8 (14 November 2026; BRFSS
  through an alternative route, see Q7 and Q8)
- [x] Copy the MEPS case counts into Q13 and Q21 and recompute H6 power (89 initiators in the primary sample; H6
  stays in the confirmatory family)
- [x] Check in the BRFSS coverage report the year the diabetes item changes (Q12, Q19, Q23): 2019
- [x] Review the smallest effects of interest (Q20) and the inference criteria (Q22): SESOIs kept; one-sided
  support and contradiction (`decision_log.md`)
- [ ] Read the original articles cited in Q4, Q18, Q19 and Q20 and check the numbers. **Partly done on 14 November 2026**
  (`citation_check.md`): every number that sets a pre-registered parameter matched its source; still to read: Callaway
  et al. (2024) on continuous treatments, Ward et al. (2019) full text, Holm (1979)
- [ ] Decide whether to keep the AI-assistance statement in Q18 (recommended)
- [ ] Upload the OSF package (`resultados/osf_glp1_<date>.zip`, built by `scripts/build_osf_package.py`) before
  registering. **Blocked on 14 November 2026:** the new OSF account returns "Account not valid"; waiting for OSF
  Support. The project link for Q7 is also pending.

## Part 1. Study information

### Q1. Working title

Is the break in the US adult obesity trend a GLP-1 effect? Preregistered signature tests in BRFSS 2011–2025 and MEPS 2018–2024

### Q2. Authors

Marsel Eleutério, independent researcher. ORCID: https://orcid.org/0009-0008-0021-8866.

### Q3. Research questions

1. By how much did self-reported adult obesity prevalence in the United States depart, in 2023–2025, from the trajectory projected from 2011–2019, in percentage points and in millions of adults?
2. Does that departure carry the signatures expected if GLP-1 receptor agonists (semaglutide, tirzepatide, liraglutide, dulaglutide, exenatide and related drugs) contributed to it: a larger departure among adults with diagnosed diabetes, a larger shift in the upper tail of the BMI distribution, a larger departure in states with higher use, and a BMI decrease among individuals who start these drugs?
3. Is the size of the departure compatible with what observed uptake, persistence and per-user weight loss could produce?
4. How do BRFSS estimates compare with Gallup's published estimates, which show a decline concentrated at ages 40–64, and with measured NHANES estimates? (descriptive)

### Q4. Hypotheses

Each hypothesis is classified by what the author already knows about the data (Q18). The pilot examined the national series and state-level aggregates, so H1 and H4 are registered as estimation targets with fixed specifications, not as independent tests. H2, H3 and H6 rely on information that has not been analysed and form the confirmatory family. H5 is a consistency check, H0 is descriptive, and two negative controls (NC1, NC2) accompany the tests. Rationale for all hypotheses: GLP-1 use for weight management rose steeply after semaglutide 2.4 mg was approved for this indication in 2021 and tirzepatide reached the market (type 2 diabetes in 2022, weight management in 2023), so any population effect should appear from 2023 on. Earlier reports found that adult obesity stopped rising or fell from 2023 and that the change coincides with GLP-1 uptake in time, region and age (Rader et al. 2024; Gallup 2025; Epic Research 2026); none tested the signatures below.

- **H0 (descriptive). Source reconciliation.** BRFSS (telephone, self-reported) shows a plateau after 2022, while Gallup (web panel, self-reported) shows a decline. The gap and its documented sources (sampling frame, mode, weighting, question wording) are described against NHANES measured estimates, together with age-specific changes (Gallup reports its largest declines at ages 40–64, where GLP-1 use is highest). No test.
- **H1 (estimation target). Trend break.** Adult obesity prevalence in 2023–2025 is below its 2011–2019 trajectory, and the gap widens over time. Prediction: negative departure in 2025, larger in 2025 than in 2023. Framework: Bayesian multilevel regression and post-stratification with a counterfactual trend.
- **H2 (confirmatory). Diabetes contrast.** In 2023–2025, mean BMI departs more from its pre-2020 trajectory among adults with diagnosed diabetes than among adults without diabetes (triple difference). Prediction: negative differential. Rationale: GLP-1 use is several times higher among adults with diabetes (26.5% used an injectable GLP-1 in the 2024 NHIS; in a November 2025 KFF poll, 45% of adults with diabetes and 12% of all adults reported current use), so a drug effect should concentrate there, while survey artefacts and secular changes should affect both groups. Use in this group was already rising before 2020 (from 3.8% in 2010 to 11.5% in 2019 among adults with diabetes and excess weight; Galindo et al. 2023), so the diabetes-specific trend absorbs the earlier, slower uptake and H2 tests the acceleration after 2022.
- **H3 (confirmatory). Upper-tail signature.** In 2023–2025, composition-adjusted BMI quantiles depart more from their trend at the 90th percentile than at the median. Prediction: negative contrast (90th minus 50th percentile). Rationale: the drugs are prescribed to people with high BMI (among adults with diagnosed diabetes, injectable GLP-1 use rises from 16.7% at a healthy weight to 32.4% with obesity in the 2024 NHIS) and produce large individual losses, so the upper tail should move first, while secular or reporting changes would shift the whole distribution.
- **H4 (estimation target). State dose–response.** States with higher GLP-1 use in 2024 show larger post-2022 departures from their own pre-2020 trajectory. Prediction: negative slope per standard deviation of a latent use index. Framework: continuous-exposure event study with permutation inference and sensitivity bounds for pre-trends, plus a dose–response analysis following Callaway, Goodman-Bacon and Sant'Anna (2024). The gradient is a causal response only under strong parallel trends.
- **H5 (consistency check). Mechanical plausibility.** The national departure in 2025 lies inside the range that a microsimulation of uptake × persistence × per-user weight loss produces when applied to the observed BMI distribution.
- **H6 (confirmatory). Individual change.** In MEPS Panels 23 and 24, adults who start a GLP-1 receptor agonist between the two BMI measurements show a larger BMI decrease than adults who never use one, adjusting for baseline BMI and covariates. Placebo: in Panel 23, adults who start only in 2021, after the second measurement, show no differential BMI decrease between 2018 and 2020. Prediction: negative for initiators, null for late initiators. A secondary contrast compares initiators with late initiators, a not-yet-treated group that also chose the drug.
- **NC1 (negative control). Height.** Self-reported height shows no departure from its 2011–2019 trend in 2023–2025 (equivalence within ±0.5 cm). A change in reporting or sample composition strong enough to move BMI would also tend to move height.
- **NC2 (negative control). Placebo break.** The H1 and H2 procedures applied to a pseudo-break in 2017 (trend fitted on 2011–2015, departure measured in 2017–2019) show no departure.

## Part 2. Data description

### Q5. Datasets and subsets

1. **BRFSS** (Behavioral Risk Factor Surveillance System, CDC), annual public-use files combining landline and cell-phone interviews, 2011–2025. Subset: adults 18+ in the 50 states and DC; territories excluded. The series starts in 2011 because that year introduced raking weights and the cell-phone sample, which makes earlier years non-comparable.
2. **MEPS** (Medical Expenditure Panel Survey, Household Component, AHRQ). Full Year Consolidated files 2018–2024 (HC-209, HC-216, HC-224, HC-233, HC-243, HC-251, HC-256); Prescribed Medicines files 2018–2024 (HC-206A, HC-213A, HC-220A, HC-229A, HC-239A, HC-248A, HC-254A); four-year longitudinal files for Panel 23, 2018–2021 (HC-236), and Panel 24, 2019–2022 (HC-245). The window starts in 2018, the first year of the redesigned MEPS questionnaire. Subset: adults 18+.
3. **State GLP-1 use.** CMS Medicare Part D Prescribers by Geography and Drug, 2019–2024; CMS Medicaid State Drug Utilization Data, 2021–2025; all-payer prescriptions per 100 residents in 2024 (PurpleLab claims, as published by GLP-1 Newsroom and audited by The RX Index).
4. **Population.** Census Bureau annual state estimates of the adult population, and American Community Survey 1-year public-use microdata (PUMS) for post-stratification cells.
5. **Validation and context.** CDC open data on nutrition, physical activity and obesity (BRFSS aggregates, dataset hn4x-zwk7); Gallup's published national obesity series; KFF and Gallup published GLP-1 use rates; NHANES published measured-obesity estimates.

### Q6. Openness and access barriers

All sources are free. BRFSS, MEPS, CMS, CDC open data, Census and ACS files are public and need no registration. Three barriers apply. MEPS height and weight (as opposed to BMI) are restricted to the AHRQ Data Center and will not be used. PurpleLab counts are proprietary, so only the published rates per 100 residents are available. Gallup and KFF microdata are not public, so only their published estimates are used.

### Q7. Access

- BRFSS: https://www.cdc.gov/brfss/annual_data/annual_YEAR.html (files LLCPYEARXPT.zip). On 14 November 2026 www.cdc.gov refused every automated request (HTTP 403) and web.archive.org was unreachable, so the files were obtained from the Hugging Face dataset jamesjiadazhan/BRFSS, revision 6e0af4750a9622dc297421924aab450774c00a2f: a column-for-column Parquet conversion of the CDC annual files (no recoding), made from Internet Archive captures of the CDC URLs (26 July 2026 for 2011–2024, 18 September 2026 for 2025). The CDC URL and the MD5 of each original zip are recorded in provenance_hf.csv.
- MEPS: https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-NUMBER (Stata files)
- Medicare Part D by geography and drug: https://data.cms.gov/data-api/v1/dataset/c8ea3f8e-3a09-4fea-86f2-8902fb4b0920/data (2024; earlier years have their own dataset ids, listed in provenance_cms.csv)
- Medicaid State Drug Utilization Data: https://catalog.data.gov/dataset/state-drug-utilization-data-2025
- CDC open data: https://catalog.data.gov/dataset/nutrition-physical-activity-and-obesity-behavioral-risk-factor-surveillance-system
- Download scripts (brfss_microdata.py, meps_microdata.py, brfss_hf_download.py, brfss_extract_parquet.py, cms_glp1_download.py, census_download.py), the MEPS SHA-256 manifest and the provenance files of BRFSS, CMS and Census/ACS are in this OSF project: [OSF link].

### Q8. Download and access dates

Marsel Eleutério, the only author:

- Aggregated tables used in the pilot (CDC open data, Census estimates, the CMS-derived state tables published by The RX Index, KFF and Gallup reports): accessed 12–13 November 2026.
- BRFSS microdata 2011–2025: downloaded 14 November 2026 (route in Q7). Validated the same day against the CDC open-data aggregates: 792 state-years compared, mean absolute difference 0.025 pp, maximum 0.12 pp; the national series matches within 0.05 pp in every year.
- MEPS files: downloaded 14 November 2026 from meps.ahrq.gov (16 Stata files; SHA-256 manifest in the OSF project). Codebook checks: 24 of 24 comparable counts match, no mismatch.
- Medicare Part D and Medicaid files from CMS: downloaded 14 November 2026 through the official APIs (cms_glp1_download.py). Medicare Part D by Geography and Drug 2019–2024: all state-level rows (2024 file released 21 May 2026). Medicaid State Drug Utilization Data 2021–2025 (versions of 13 July 2026): GLP-1 rows selected by product-name prefix, every name kept listed for review. Medicaid and CHIP monthly enrollment 2021–2025. Every row count matches the API count; dataset ids, release dates and SHA-256 in provenance_cms.csv.
- ACS PUMS: 1-year person files 2011–2019, experimental 2020 and 2021–2024 downloaded 14 November 2026, before any BMI analysis, and reduced to post-stratification cell counts (census_download.py; the 2025 file is not yet released, so 2024 is used for 2025 as stated in Q19). Census state population estimates, Vintage 2025, downloaded the same day. SHA-256 in provenance_census.csv.

### Q9. Data collection and representativeness

- **BRFSS.** State-based random-digit-dial survey of non-institutionalized adults by landline and cell phone, run by state health departments with CDC, with about 350,000 to 510,000 records a year. Weights are raked to age, sex, race and ethnicity, education, marital status, home tenure and phone ownership. Height and weight are self-reported, which underestimates obesity relative to measurement. Some states are missing in some years; in the CDC aggregates these are NJ 2019, FL 2021, KY and PA 2023, TN 2024, and CA, MS and NV 2025.
- **MEPS.** Nationally representative of the US civilian non-institutionalized population, drawn from National Health Interview Survey respondents. Overlapping panels are interviewed five times over two years; Panels 23 and 24 were extended to nine rounds over four years. Prescribed medicines are reported by households and supplemented by pharmacy data. Adult BMI comes from a self-administered questionnaire collected only in even years (2018, 2020, 2022, 2024). The full-year files have between 19,140 (2024) and 30,461 (2018) records.
- **State use measures.** Administrative claims, not people: Medicare Part D counts prescriptions filled by enrollees, most of them 65 or older; Medicaid counts reimbursed prescriptions; PurpleLab extrapolates all-payer claims. None counts persons on treatment, which is why they enter H4 as indicators of a latent exposure.

### Q10. Codebooks and documentation

- BRFSS annual codebooks and the "Calculated Variables in Data Files" documents, for _BMI5, _BMI5CAT, _AGEG5YR, _SEX/SEXVAR/SEX1/SEX, _IMPRACE, _EDUCAG, _INCOMG/_INCOMG1, HLTHPLN1/_HLTHPLN/_HLTHPL1/_HLTHPL2, DIABETE3/DIABETE4, HTM4, _LLCPWT, _STSTR and _PSU.
- MEPS documentation and codebook of each file, in particular the HC-256 text on body mass index (adult BMI ADBMI42, collected in alternating years, top-coded at 50 and bottom-coded at 10 from 2020 on) and section 3.11 (variance estimation with VARSTR and VARPSU), and the HC-236 and HC-245 documentation (round-specific BMI ADBMI2, ADBMI6, ADBMI4, ADBMI8; weights LONGWT and LSAQWT).
- CMS data dictionaries for Part D by geography and drug and for the State Drug Utilization Data.

## Part 3. Variables

### Q11. Manipulated variables

None. This is an observational study of secondary data.

### Q12. Measured variables

- **Outcomes, BRFSS.** BMI = _BMI5 / 100, calculated by CDC from self-reported height and weight; obesity = _BMI5CAT equal to 4 (BMI ≥ 30); thresholds 25, 35 and 40 derived from BMI.
- **Outcomes, MEPS.** Adult BMI ADBMI42 in 2018, 2020, 2022 and 2024; ADBMI2 and ADBMI6 (Panel 23, 2018 and 2020) and ADBMI4 and ADBMI8 (Panel 24, 2020 and 2022); ΔBMI = second measurement minus first.
- **Negative-control outcome.** BRFSS HTM4, computed height in metres.
- **Period.** Pre-period 2011–2019, transition 2020–2022 (pandemic and early uptake), post-period 2023–2025.
- **Diagnosed diabetes, BRFSS.** DIABETE3 in 2011–2018 and DIABETE4 from 2019 (item change t_item = 2019, from coverage_report.csv): 1 = yes; 3 = no and 4 = prediabetes coded as no; 2 = during pregnancy only, 7 = don't know and 9 = refused treated as missing.
- **State GLP-1 use (H4).** Three indicators: Medicare Part D GLP-1 claims per 100 adult residents (2024), Medicaid GLP-1 prescriptions per 1,000 enrollees (2025), all-payer prescriptions per 100 residents (2024); combined into a latent index (Q19).
- **Individual GLP-1 use, MEPS.** At least one purchase in the year of a drug whose Multum name (RXDRGNAM) contains semaglutide, tirzepatide, liraglutide, dulaglutide, exenatide, lixisenatide or albiglutide; household-reported names (RXNAME) are used as a check. Initiator: first purchase in a panel year after the first BMI measurement and up to the second, with no purchase in earlier panel years. Late initiator (Panel 23): first purchase in 2021. Never-user: no purchase in any panel year.
- **Covariates, BRFSS.** Age group (_AGEG5YR collapsed to 18–24, 25–34, 35–44, 45–54, 55–64, 65+), sex (_SEX from 2019, SEX1 in 2018, SEX in 2011–2017; codes 7 and 9 treated as missing), race and ethnicity (_IMPRACE collapsed to White, Black, Hispanic, Asian, other or multiracial; _IMPRACE does not exist in 2015–2016, so in those two years race and ethnicity enters as a separate "not available" category; sensitivity: models without race and ethnicity), education (_EDUCAG, four levels), income (_INCOMG or _INCOMG1), health-care coverage (HLTHPLN1 in 2011–2020, _HLTHPLN in 2021–2022, _HLTHPL1 in 2023, _HLTHPL2 in 2024–2025; 1 = insured, 2 = not insured, other codes missing), state and year.
- **Covariates, MEPS.** Age, sex, race and ethnicity (RACETHX), census region, insurance coverage (INSCOVyy), poverty category (POVCATyy), diagnosed diabetes (DIABDX_M18) and baseline BMI.

### Q13. Units of analysis, inclusion criteria and expected sample size

- **BRFSS.** Respondents aged 18+ in the 50 states and DC with a valid BMI (_BMI5CAT 1–4). Size: 6,048,517 interviews over 2011–2025, counted in the extracted microdata on 14 November 2026 (the CDC open-data sample sizes, which also count the territories, add up to 6,049,086). State-year analyses use 51 units × 15 years minus the eight state-years without data; H4 uses the 50 states that have all three use indicators (DC lacks the all-payer measure).
- **MEPS cross-section.** Adults with a valid ADBMI42: 18,252 in 2018, 13,801 in 2020, 10,601 in 2022 and 10,828 in 2024, according to the codebooks (53,482 person-years).
- **MEPS panels (H6).** Adults with BMI at both rounds who are initiators or never-users; late initiators (Panel 23) enter the placebo and the not-yet-treated comparison. Panel 24 has 5,565 persons, 4,883 of them present in all nine rounds. Counts from the extracted files (14 November 2026). With BMI at both rounds: Panel 23, 3,472 (3,341 never-users, 42 prevalent users, 47 initiators, 26 late initiators); Panel 24, 2,085 (1,990 never-users, 48 prevalent users, 46 initiators). Primary H6 sample (also present in all nine rounds and with known GLP-1 status in every panel year, Q14): Panel 23, 3,249 never-users, 44 initiators and 26 late initiators; Panel 24, 1,962 never-users and 45 initiators; pooled, 89 initiators and 5,211 never-users.

### Q14. Missing data

- **BRFSS BMI.** Missing when height or weight is refused or unknown. The primary analysis uses complete cases, as CDC does; the share missing is reported by year, sex and age. Because a rise in missing weight among heavier respondents could mimic a decline, the missing share is tested for a departure from its 2011–2019 trend (reported with H1). Sensitivity: multiple imputation of BMI (20 imputations, chained equations within year, using age, sex, race and ethnicity, education, income, state, diabetes, general health and height).
- **Missing state-years.** Enter the national series through the MRP model, which predicts them from state effects and a lagged state-level predictor; they are excluded from state-level regressions. Sensitivity: states observed in all years only.
- **Diabetes.** Respondents with codes 2, 7 or 9 are excluded from H2.
- **MEPS.** BMI codes −1 and −15 are missing. The self-administered questionnaire weights adjust for questionnaire nonresponse; otherwise complete cases. Panel members not present in all rounds are excluded from the primary H6 analysis (included in a sensitivity with LONGWT), and persons whose GLP-1 status is unknown in any panel year are excluded from H6.

### Q15. Outliers

No exclusions beyond the source coding in the primary analysis. BRFSS _BMI5 is already restricted by CDC to plausible combinations of height and weight. MEPS BMI is top-coded at 50 and bottom-coded at 10 from 2020 on; the same coding is applied to 2018 for comparability. The quantile analyses (H3) are insensitive to extreme values. Sensitivity: exclude BRFSS BMI below 12 or above 70, and MEPS changes larger than 10 kg/m² over two years; the number excluded is reported.

### Q16. Sampling weights

Yes. BRFSS: _LLCPWT with _STSTR and _PSU (strata nested within year) and Taylor linearization for H2, NC1 and the direct state estimates used in H4; H3 uses a rescaled bootstrap of PSUs within strata. The MRP model for H1 is fitted to unweighted cell counts and post-stratified to ACS population counts (adults 18+ in the 50 states and DC, excluding people in institutional group quarters, whom BRFSS does not sample; cells built by census_download.py), which takes the place of the survey weights; the weighted direct series is reported alongside. MEPS: person weights (PERWTyyF) for use rates, the self-administered questionnaire weight for cross-sectional BMI, and LSAQWT (LONGWT if LSAQWT is absent from HC-236) for H6, always with VARSTR and VARPSU.

## Part 4. Knowledge of data

### Q17. Prior publications and presentations

None. The author has not published or presented work based on BRFSS or MEPS. The pilot described in Q18 is unpublished; its code and outputs are in this OSF project.

### Q18. Prior knowledge of the data

On 12–13 November 2026 the author ran a pilot on aggregated data only (BRFSS tables from the CDC open-data API, state use tables, Census estimates, published polls). Its main results are listed here; the complete output (pilot_output.txt and pilot_extra_output.txt) is in the OSF project.

1. **National series (relevant to H1).** Obesity rose about 0.49–0.50 percentage points a year in 2011–2019. The national estimate was 33.3% in 2022 and 33.5% in 2025, or 32.9% after adjusting for the states missing in 2025. In 2025 the departure from the 2011–2019 trend was −0.73 pp in the unadjusted series and −1.18 pp in a state-composition-adjusted series (−1.75 pp against a 2011–2022 trend); the adjusted departures correspond to about 3.1 to 4.7 million adults.
2. **BMI categories (relevant to H3).** Overweight (BMI 25–29.9) stayed close to its 2011–2019 trend in 2023–2025 (+0.1 pp in 2025), while the share with BMI below 25 was 0.5–0.6 pp above its trend. BMI quantiles were not computed.
3. **Age and sex (relevant to the secondary H2 gradients).** Departures by age group did not follow published use by age: their correlations with use across six age groups ranged from −0.40 to +0.67, depending on the use source and the departure measure. The 2025 departure was −0.90 pp for women and −0.44 pp for men.
4. **States (relevant to H4).** With the 2024 all-payer use measure, the change in obesity from 2021–22 to 2024–25 was 0.33 pp lower per standard deviation of use (HC3 standard error 0.16; permutation p = 0.05; r = −0.28). The slope was driven by West Virginia, Kentucky, Louisiana and Oklahoma: −0.03 pp per SD without them. The Medicaid measure showed no association. Alternative specifications (Medicare claims per adult or claim share, a 2019–2022 baseline, precision weights, adjustment for or residualization on the 2015–2019 level, dropping states missing a post-period year) gave slopes between −0.18 and −0.52 pp per SD. With the deviation from each state's own 2011–2019 trend as outcome, the slope was −0.93 pp per SD, falling to −0.43 (p = 0.11) after adjusting for the 2015–2019 obesity level. Placebo periods gave −0.06 pp per SD for 2015/16 to 2018/19 (p = 0.71), +0.35 for 2012/13 to 2015/16 (p = 0.008), and −0.40 for the deviation-from-trend placebo (p = 0.07). In an event study, the slopes were negative in 2011–2014 (−0.62 to −0.23), close to zero in 2015–2019, and −0.35 and −0.39 in 2024 and 2025; after removing the linear pre-trend in the slopes, the post-period slopes were −0.44 (2023), −0.82 (2024) and −0.93 (2025). A power check gave about 74% power if a 1.5 pp national departure were proportional to all-payer use. By tercile of all-payer use, the mean deviation from the states' own 2011–2019 trend in 2024–25 was +0.01 pp (low use), −1.03 pp (middle) and −1.81 pp (high).
5. **Published reports.** The author has read earlier reports on the same question: Rader et al. (2024), who found a fall in measured BMI and obesity in 2023 in records of 16.7 million adults, largest in the South, where GLP-1 dispensing was highest; Gallup (2025, 2026), with obesity at 39.9% in 2022 and 37.0% in 2025 and the largest declines at ages 40–64; Epic Research (2026); state counts from Trust for America's Health (2025) and the CDC maps (2026); NHANES estimates to 2023; and published GLP-1 use rates by age, sex, diabetes, BMI class and insurance (KFF, Gallup, NCHS). These reports motivated the hypotheses and the parameter ranges in Q19 and Q20. None analyses BMI by diabetes status, BMI quantiles or within-person change in the datasets used here.
6. **Microdata.** On 14 November 2026 BRFSS and MEPS microdata were downloaded and processed only by the scripts in this project. They reproduce published aggregates (state-year obesity prevalence and codebook counts) and count cases (adults with BMI, GLP-1 users per year, initiators per panel). The MEPS extraction also printed the weighted share of adults with a GLP-1 purchase per year, overall and among adults with diagnosed diabetes (0.84% and 7.2% in 2018, 4.99% and 30.4% in 2024); this is exposure, not outcome. The BRFSS coverage report led to adding source names for sex (SEX, SEX1) and health-care coverage (_HLTHPL2) to brfss_microdata.py, after checking in the CDC dictionaries that their codes match; this change is documented in the OSF project. No BMI analysis by diabetes status, BMI quantile, height trend or GLP-1 use has been run.

Not yet examined: anything by diagnosed diabetes (H2), BMI quantiles (H3), BMI change in MEPS (H6), self-reported height (NC1), and the 2017 pseudo-break in the microdata (NC2).

Consequences for this plan: H1 and H4 are registered as estimation targets with fixed specifications, not as confirmatory tests; the BMI-category predictions in H3 are secondary because the category shares were seen; the confirmatory tests are H2, H3 (quantile contrast) and H6, together with NC1.

AI assistance: the pilot, the download scripts and the draft of this registration were prepared with an AI assistant (Claude, Anthropic) under the author's direction. The author is responsible for every analytic decision.

## Part 5. Analyses

### Q19. Statistical models

- **H1, two stages.** Stage 1 is multilevel regression and post-stratification, fitted separately for each year 2011–2025. Cells c are state × age group (6) × sex (2) × race and ethnicity (5) × education (4); y_c obese respondents out of n_c, y_c ~ Binomial(n_c, p_c), logit(p_c) = μ + α_state + α_age + α_sex + α_race + α_educ + α_age×sex. State effects follow α_state ~ Normal(α_division + γ·z_s, σ_state), where z_s is the centred logit of the state's direct estimate in the previous available year, so that states missing in a year (for example California in 2025) are predicted. Priors: μ ~ Normal(−0.8, 1); γ ~ Normal(0, 1); group effects (division, age, education, race and ethnicity, age × sex) Normal(0, σ_g) with σ_g ~ Half-Normal(0, 1), constrained to sum to zero within each factor and in non-centred form; sex, with only two levels, enters as a fixed effect (sum-to-zero, Normal(0, 1)); the state effects' deviations from α_division + γ·z_s also sum to zero. These constraints remove the joint shift of the intercept and the group effects that is not identified by the data: without them the model did not converge on simulated data under any of the Q23 steps. Cells are post-stratified to ACS 1-year PUMS adult counts (the 2024 frame for 2025 if the 2025 file is not released; the experimental file for 2020), giving posterior draws of national prevalence P_t. Stage 2 builds the counterfactual: for each draw, a linear trend in logit(P_t) is fitted to 2011–2019 and projected to 2023–2025 with its closed-form posterior predictive (Student-t, 7 df), and the departure D_t = P_t − projected P_t is computed in percentage points and in millions of adults (Census adult population, Vintage 2025). Reported: posterior median and 95% credible interval of D_2023, D_2024 and D_2025, and P(D_2025 < D_2023). Sampler: PyMC (NUTS, as implemented by nutpie), 4 chains × 1,000 draws after 1,000 tuning steps, target acceptance 0.95.
- **H2, triple difference.** Survey-weighted linear regression on individual BRFSS records, 2011–2025: BMI_i = λ_(state,year) + X_i′β + D_i·(α_0 + Z_i′α + θ·(t − 2015) + κ·1[t ≥ t_item]) + Σ_(k=2020..2025) π_k·D_i·1[t = k] + ε_i. Here D_i is diagnosed diabetes; state × year fixed effects absorb national and state shocks common to both groups; X_i are age group × sex, race and ethnicity, education and income indicators; Z_i (age group and sex) let the diabetes gap differ by age and sex; θ is the diabetes-specific linear trend identified from 2011–2019; κ absorbs a level shift when the diabetes item changes (t_item, from coverage_report.csv); π_k is the deviation of the diabetes gap from its trend in year k. Estimand: π̄ = (π_2023 + π_2024 + π_2025) / 3, in kg/m². Inference in two stages, because a single regression's design-based standard error reflects sampling error only and would ignore year-level shocks to the diabetes gap (with about 400,000 interviews a year it would be far too small), and because κ would rest on 2019 alone: stage 1 estimates the gap g_t for every year 2011–2025 with the same model (D_i × year indicators in place of the trend, item and π terms); stage 2 fits g_t = a + θ·(t − 2015) + κ·1[t ≥ t_item] by OLS to 2011–2019 and projects it to 2023–2025, so that π_t = g_t minus the projection and SE(π̄) = s·√(1/3 + x̄₀′(X′X)⁻¹x̄₀), with a Student-t reference distribution on 6 degrees of freedom (the closed-form predictive used in H1 Stage 2). The single-regression estimate with design-based standard errors is reported as a secondary result. Secondary: obesity (0/1) as a linear-probability outcome, and the gradients for ages 50–64, women and insured adults in place of diabetes.
- **H3, quantile contrast.** For each year and q ∈ {0.10, 0.25, 0.50, 0.75, 0.90, 0.95}, the weighted quantile of BMI is computed after reweighting the year's sample to the 2017–2019 joint distribution of age group, sex, race and ethnicity and education (DiNardo–Fortin–Lemieux reweighting with a logistic model of year versus reference). Each quantile series goes through the H1 Stage-2 trend procedure, giving departures Δ_q,t. Estimand: C = mean over 2023–2025 of (Δ_0.90,t − Δ_0.50,t). Uncertainty: Rao–Wu rescaled bootstrap of PSUs within strata and year (500 replicates), repeating reweighting, quantiles and trend projection in each replicate. Secondary: distribution regression for P(BMI ≥ k), k ∈ {25, 30, 35, 40}, with the same trend procedure; category shares, already seen in aggregates, are reported descriptively.
- **H4, state event study.** Outcome Y_st: direct weighted obesity prevalence by state and year. Exposure E_s: posterior mean of a one-factor measurement model of the three standardized use indicators (x_js = λ_j·η_s + ε_js, η_s ~ Normal(0, 1), λ_j ~ Half-Normal(0, 1)), scaled to SD 1. Model: Y_st = α_s + λ_t + Σ_k β_k·(E_s × 1[t = k]) + u_st, with the β_k normalized to a 2015–2019 mean of zero. Estimand: β* = mean of β_2023..β_2025 minus the values predicted for those years by a linear trend in β_k fitted to 2011–2019. Inference: two-sided randomization test on |β*| permuting E_s across states (20,000 permutations) and Rambachan–Roth smoothness bounds (M ∈ {0, 0.02, 0.05} pp per year²), computed conservatively as β* ± (1.96·SE + B(M)), where B(M) is the worst-case bias of the linear extrapolation over pre-trend paths whose second differences are bounded by M (linear programming) and SE is clustered by state; the exact fixed-length interval of Rambachan and Roth (2023) can only be narrower. Uncertainty in E_s is propagated over 200 posterior draws of the factor, combined with Rubin's rules. Dose–response (Callaway, Goodman-Bacon and Sant'Anna 2024): every state has some use, so there is no untreated group and only comparisons across doses are identified. For ΔY_s, the mean of the available years in 2023–2025 minus the value projected from the state's own 2011–2019 linear trend, two estimates are reported: the difference between the top and the bottom tercile of E_s, and the average derivative of a quadratic fit of ΔY_s on E_s (the average causal response). Both use the permutation test above. The slope and these contrasts are causal responses only under strong parallel trends, that is, if states at different doses would have followed the same path had they received the same dose; otherwise they are descriptive gradients.
- **H5, microsimulation.** Applied to the 2025 BRFSS adults with BMI, 10,000 draws. Use: probabilities by BMI class (25–30, 30–35, 35–40, 40+) and diabetes from MEPS 2024, scaled so that national adult use lies between the MEPS 2024 rate and the published 2025 rates (KFF, Gallup). Persistence at one year: Uniform(0.30, 0.45) without diabetes and Uniform(0.45, 0.60) with diabetes, around the 35.2% and 53.5% implied by the one-year discontinuation rates of 64.8% and 46.5% in Rodriguez et al. (2025). Weight loss: Uniform(8%, 16%) for persistent users, spanning the real-world 12-month losses of 8.3% with semaglutide and 15.3% with tirzepatide (Rodriguez et al. 2024), against 14.9% in STEP 1 (68 weeks) and 20.9% in SURMOUNT-1 (72 weeks, 15 mg); Uniform(2%, 7%) for non-persistent users, around the one-year losses of 3.6% for patients who stopped within 3 months and 6.8% for those who stopped between 3 and 12 months (Gasoyan et al. 2025). Counterfactual BMI of a simulated user = observed BMI / (1 − loss). Simulated effect = observed obesity prevalence minus counterfactual prevalence. If H6 estimates the per-initiator change with SE below 0.5 kg/m², a second version replaces persistence × loss with that estimate, read as a lower bound because initiators in 2019–2022 mostly used earlier drugs and lower doses.
- **H6, individual change.** Weighted linear regression pooled over Panels 23 and 24, among adults with BMI at both rounds who are initiators or never-users: ΔBMI_i = α + β·Init_i + δ·Panel24_i + f(BMI_t0,i) + X_i′γ + ε_i, where f is linear plus quadratic in baseline BMI and X_i covers age group, sex, race and ethnicity, baseline diabetes and baseline insurance. Weights LSAQWT; design-based standard errors with VARSTR and VARPSU. Estimand: β, in kg/m² over two years. Placebo (Panel 23): the same model with late initiators (first purchase in 2021) against never-users; estimand β_late. Not-yet-treated comparison (Panel 23): the same model restricted to initiators and late initiators, who all chose the drug and differ only in timing; estimand β_nyt. Secondary: number of GLP-1 purchases between the measurements (1–3, 4–8, 9+) and log BMI as outcome.
- **NC1, height.** BRFSS HTM4 by sex for adults 25–64 (avoiding age-related height loss), composition-adjusted as in H3 and passed through the H1 Stage-2 trend procedure. Estimand: mean departure in 2023–2025, in cm.
- **NC2, placebo break.** H1 Stage 2 with the trend fitted to 2011–2015 and the departure measured in 2017–2019; the H2 model with π_k for 2017–2018 and θ fitted to 2011–2015 (2019 is left out for H2 because the diabetes item changes that year, so the item shift cannot be separated from a placebo break; same two-stage inference as H2).
- **H0.** Descriptive comparison of BRFSS (MRP and direct estimates), Gallup's published annual estimates and NHANES published measured estimates, with a table of design differences, and of age-specific changes from 2022 to 2025 in BRFSS against those published by Gallup. No test.

### Q20. Effect sizes

| Hypothesis | Estimand | Smallest effect of interest | Expected range |
| --- | --- | --- | --- |
| H1 | Departure in 2025, D_2025 | −0.5 pp (about 1.3 million adults) | −0.7 to −1.8 pp (pilot) |
| H2 | Diabetes differential, π̄ | −0.2 kg/m² | −0.2 to −1.5 kg/m² |
| H3 | Quantile contrast, C | −0.3 kg/m² | Not estimated |
| H4 | Detrended slope, β* | −0.25 pp per SD | −0.4 to −0.9 pp per SD (pilot) |
| H6 | Initiators vs never-users, β | −0.5 kg/m² | −0.5 to −3 kg/m² |
| NC1 | Height departure | Equivalence margin ±0.5 cm | 0 |

The expected ranges for H2 and H6 follow from the H5 ranges. At a BMI of 35, persistence of 30–60% with losses of 8–16%, and losses of 2–7% for non-persistent users, give a mean change per user of −1.3 to −4.3 kg/m². For H6 the most negative value is capped at −3 because many initiators start shortly before the second measurement, and the least negative is set at the smallest effect of interest because initiators in 2019–2022 mostly used earlier drugs and lower doses (an assumption, not an estimate). H2 multiplies the per-user change by an assumed 15–35 point gap in use between adults with and without diabetes; published use among adults with diabetes ranges from 26.5% (NHIS 2024) to 45% (KFF, November 2025), against 12% of all adults. A height change of 0.5 cm would shift the BMI of a 170 cm adult with BMI 29 by about 0.17 kg/m², enough to move obesity prevalence by a few tenths of a percentage point, a sizeable fraction of the departure the pilot suggests.

### Q21. Statistical power

Approximate, under the stated assumptions. H1 and H4 figures are two-sided at α = 0.05. For the confirmatory family the figures are one-sided, as tested in Q22, and are given both unadjusted (α = 0.05) and for the first Holm step (α = 0.05/3), which is the relevant case when only one of the three hypotheses has an effect:

- **H1.** The pilot's trend-projection error for 2025 is 0.32–0.34 pp. Power: 31–35% for −0.5 pp, 84–88% for −1.0 pp, 94–96% for −1.2 pp.
- **H2.** The annual sampling error of the diabetes gap is about 0.04 kg/m² (SD 6.3, design effect 1.8, about 50,000 adults with diabetes a year). With a residual SD of 0.08 kg/m² for the annual gap around its trend, SE(π̄) ≈ 0.11 and with the two-stage inference of Q19 (Student-t, 6 degrees of freedom) one-sided power is 49% at −0.2, 78% at −0.3 and 94% at −0.4 kg/m² unadjusted, and 26%, 53% and 79% at the first Holm step (two-sided, normal reference, as in the first draft: 44%, 78% and 95%; 32–70% at −0.2 and 85–100% at −0.4 for residual SDs of 0.06–0.10). If π̄ is zero, the probability of classifying H2 as contradicted (Q22) is 45%.
- **H3.** With an annual residual SD of 0.15 kg/m² for the 90th-minus-50th contrast, SE(C) ≈ 0.20 and one-sided power is 44% at −0.3, 80% at −0.5 and 91% at −0.6 kg/m² unadjusted, and 26%, 65% and 81% at the first Holm step. If C is zero, the probability of classifying H3 as contradicted is 44%.
- **H4.** The pilot simulation gives about 74% power if a 1.5 pp national departure is proportional to all-payer use, and 41% for 1.0 pp.
- **H6.** With SD(ΔBMI) = 2.5 kg/m², design effect 1.5 and 2,500 never-users, the minimum effect detectable with 80% power is 1.58 kg/m² with 30 initiators, 1.23 with 50, 0.97 with 80, 0.80 with 120 and 0.63 with 200. The primary sample has 89 initiators and 5,211 never-users (Q13), so the minimum detectable effect is 0.92 kg/m²; SE(β) ≈ 0.33 and one-sided power is 45% at the smallest effect of interest (−0.5 kg/m²), 74% at −0.75, 92% at −1.0 and above 99% at −1.5 kg/m² unadjusted, and 27%, 56%, 82% and 99% at the first Holm step. If β is zero, the probability of classifying H6 as contradicted is 45%. H6 stays in the confirmatory family (Q22 requires at least 30 initiators), but it is underpowered at its smallest effect of interest: unless the true effect is larger than about −0.75 kg/m², the most likely classification is inconclusive. The smallest effect of interest is kept at −0.5 kg/m² because it is a substantive threshold, not one derived from the sample size.
- **NC1.** The annual sampling error of mean height is below 0.05 cm, so equivalence at ±0.5 cm should be well powered unless the year-to-year residual is much larger.

### Q22. Inference criteria

- **Confirmatory family (H2, H3, H6).** All three predictions are directional (a negative estimand), so each is tested one-sided. **Supported:** the one-sided test of H0: estimand ≥ 0 against H1: estimand < 0 gives a Holm-adjusted p below 0.05 across the three hypotheses. **Contradicted:** the estimand is shown to be less negative than the smallest effect of interest Δ (Q20), that is, the one-sided test of H0: estimand ≤ −Δ against H1: estimand > −Δ rejects at α = 0.05 (equivalently, the whole 90% confidence interval lies above −Δ); this includes estimates significantly in the opposite direction. **Inconclusive:** neither. An estimate that is both supported and contradicted (significantly negative but shown to be smaller in magnitude than Δ) is classified as contradicted: the effect exists but is too small to matter. For H2 the tests use the Student-t reference of its two-stage inference (Q19). The contradiction test is not adjusted for multiplicity, because it is used to rule out effects of interest, not to claim them. Rationale: with the standard errors in Q21, a two-sided equivalence test (TOST) at ±Δ could never classify H3 or H6 as contradicted, because their 90% intervals are wider than Δ; the one-sided version matches the directional predictions and makes every verdict reachable.
- **H6 conditions.** H6 also requires that β_late is not significantly negative; if it is, H6 is classified as inconclusive (a pre-existing trajectory). If fewer than 30 initiators with BMI at both rounds exist across the two panels, H6 is reported descriptively and leaves the family, and Holm runs over H2 and H3. The contrast between initiators and late initiators (β_nyt, Panel 23) is a secondary estimate and stays out of the decision rule, because few late initiators are expected.
- **Negative controls.** NC1 passes if equivalence testing (two one-sided tests, α = 0.05) establishes equivalence within ±0.5 cm. NC2 passes if the 95% interval of each placebo departure includes zero.
- **H1.** The trend break is present if the 95% credible interval of D_2025 excludes zero under the primary counterfactual and the sign is the same under the alternative counterfactuals in Q24. Its size is reported in every case.
- **H4.** Supportive if the permutation p for β* is below 0.05 and the Rambachan–Roth interval at M = 0.02 excludes zero. The estimate without WV, KY, LA and OK is reported with it, as are the tercile contrast and the average causal response, which do not change this classification.
- **H5.** Compatible if the 95% credible interval of D_2025 overlaps the central 90% of the simulated effects. If the whole interval lies below the 5th percentile of the simulated effects (more negative), the departure is larger than the drugs can explain; if it lies above the 95th percentile, it is smaller than expected.
- **Overall verdict.** "GLP-1 signature present" if at least two of H2, H3 and H6 are supported, none is contradicted and NC1 passes; "absent" if at least two are contradicted or NC1 fails; "mixed" otherwise.

### Q23. Assumption violations, non-convergence and other problems

- **MRP convergence (H1).** Required: R-hat below 1.01, bulk effective sample size above 400 and no divergent transitions. If a year fails, in this order: 2,000 tuning steps; target acceptance 0.99; drop the age × sex interaction; drop the education effect. Any simplification is reported. If a year still fails, the composition-adjusted direct series (state × year fixed effects on weighted state estimates, as in the pilot) becomes the primary H1 series.
- **Survey regressions.** Design-based standard errors; strata with a single PSU are handled by centring at the grand mean. With 51 states, state-clustered inference for H2 uses a wild cluster bootstrap (Webb weights, 9,999 replications) as a sensitivity.
- **Latent exposure (H4).** If the one-factor model does not converge, or an indicator loads with the wrong sign, the exposure becomes the standardized mean of the indicators with positive loadings, and each indicator is also reported alone.
- **Diabetes item change (H2).** The primary model includes the level-shift term κ; the model without it is a sensitivity. If the change falls outside 2011–2019, κ is dropped from the primary model and the year is reported. The change is in 2019 (DIABETE3 to DIABETE4), inside the pre-period, so κ stays in the primary model.
- **Small MEPS cells (H6).** If a covariate category has fewer than 5 initiators, it is merged with the adjacent category. The rule for fewer than 30 initiators is in Q22.
- **Weighted quantiles (H3).** Computed from the weighted empirical distribution function with linear interpolation; bootstrap replicates that fail are redrawn and their number is reported.

### Q24. Robustness and sensitivity

- **Counterfactual trends.** Linear on 2011–2021 and on 2015–2019, quadratic on 2011–2019, and the 2022 level continued at the 2011–2019 slope.
- **External counterfactuals.** The observed change from 2022 to 2025 is set against the average annual change implied by two projections built on data from before the rise in GLP-1 use (Ward et al. 2019, BRFSS 1993–2016; DeCleene et al. 2026, data to 2022). Changes are compared, not levels, because those projections are calibrated to measured BMI.
- **Pandemic years.** All models re-estimated without 2020 and 2021.
- **Composition.** Balanced panel of states observed in every year; reweighting to the 2011 and the 2022 compositions instead of 2017–2019.
- **Self-report.** BMI corrected with an NHANES-calibrated adjustment for self-report bias, as in Ward et al. (2019).
- **Missing BMI.** Multiple imputation (Q14), and the trend in the share missing.
- **Interview mode.** Separate estimates for cell-phone and landline interviews.
- **H2.** Without the age and sex interactions; ages 45–74 only; diabetes group reweighted to its 2017–2019 composition; wild cluster bootstrap by state; item-change term on and off.
- **H3.** 75th and 95th percentiles in place of the 90th; RIF regression with covariates instead of reweighting.
- **H4.** Each indicator alone; population weights; precision weights; leave-one-state-out; without WV, KY, LA and OK; without states missing a post-period year; Rambachan–Roth relative-magnitude bounds (M̄ = 0.5 and 1); dose–response with quartiles instead of terciles and with a cubic fit.
- **H5.** Loss of non-persistent users drawn from Uniform(0%, 4%); persistence fixed at 35.2% and 53.5%; national use fixed at the MEPS 2024 rate.
- **H6.** Prevalent users as a third group; LONGWT instead of LSAQWT; persons not present in all rounds included; changes larger than 10 kg/m² excluded; by diabetes status; each panel separately.
- **NC1.** All adults 18+; by sex.

The primary results are those in Q19; sensitivity results are reported in full, whatever their direction.

### Q25. Exploratory analyses

Labelled as exploratory in the preprint:

- Reconciliation of BRFSS with Gallup and NHANES (H0), including mode, weighting and age-specific changes.
- Heterogeneity of the departure by state, income, education and race and ethnicity.
- Severe obesity (BMI ≥ 40).
- MEPS: GLP-1 use and spending by insurance type and by drug (semaglutide versus tirzepatide), the yearly drug mix as a possible reason for a widening departure, and the 2024 BMI distribution of users and non-users.
- Medicaid coverage of GLP-1s for obesity as a natural experiment: obesity among low-income adults in BRFSS before and after coverage begins, with staggered adoption dates taken from Wing et al. (2026) and Khanna et al. (2026). Low power is expected, because the added use is small.
- Year-by-year departures in the 2020–2022 transition.
- Any analysis suggested by the results.

## Part 6. Statement of integrity

The author confirms that this preregistration was completed truthfully, that Part 4 lists everything he knows about the data that is relevant to the hypotheses, and that no other preregistration covers the same hypotheses and data. Any deviation from this plan will be reported in the preprint, with its reason.

## References

Pages accessed on 12-14 November 2026. Methods references without a link were cited from memory: check volume and
pages before using them in the preprint.

**Data and documentation**

- CDC, [BRFSS 2024 Annual Data](https://www.cdc.gov/brfss/annual_data/annual_2024.html) and [BRFSS 2025 Annual Data](https://www.cdc.gov/brfss/annual_data/annual_2025.html)
- AHRQ, [MEPS HC-256: 2024 Full Year Consolidated Data File](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-256) and its [documentation](https://meps.ahrq.gov/mepsweb/data_stats/download_data/pufs/h256/h256doc.shtml)
- AHRQ, [MEPS HC-254A: 2024 Prescribed Medicines File](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-254A)
- AHRQ, [MEPS HC-245: Panel 24 Four-Year Longitudinal Data File](https://meps.ahrq.gov/mepsweb/data_stats/download_data/pufs/h245/h245doc.shtml) and [MEPS HC-236: Panel 23 Four-Year Longitudinal Data File](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-236)
- CMS, [Medicare Part D by geography and drug](https://data.cms.gov/data-api/v1/dataset/c8ea3f8e-3a09-4fea-86f2-8902fb4b0920/data) and [Medicaid State Drug Utilization Data 2025](https://catalog.data.gov/dataset/state-drug-utilization-data-2025)
- NCHS, [Data Brief 508](https://www.cdc.gov/nchs/products/databriefs/db508.htm): obesity and severe obesity, NHANES August 2021-August 2023
- Hugging Face dataset [jamesjiadazhan/BRFSS](https://huggingface.co/datasets/jamesjiadazhan/BRFSS), revision 6e0af4750a9622dc297421924aab450774c00a2f (Parquet conversion of the CDC annual files)

**Pre-registration template**

- OSF, [Select a Registration Template](https://help.osf.io/hc/en-us/articles/360019738794-Select-a-Registration-Template)
- Van den Akker et al., [Preregistration of secondary data analysis: a template and tutorial](https://open.lnu.se/index.php/metapsychology/article/view/2625), Meta-Psychology

**Microsimulation parameters (H5)**

- Wilding et al. (2021), STEP 1, N Engl J Med: −14.9% with semaglutide 2.4 mg vs −2.4% with placebo at 68 weeks ([summary](https://wikijournalclub.org/wiki/STEP_1))
- Jastreboff et al. (2022), [SURMOUNT-1](https://doi.org/10.1056/NEJMoa2206038), N Engl J Med 387:205-16: −20.9% with tirzepatide 15 mg at 72 weeks
- Rodriguez et al. (2025), JAMA Network Open: 125,474 adults starting a GLP-1 in 2018-2023; one-year discontinuation 46.5% with type 2 diabetes and 64.8% without ([summary](https://www.healthday.com/healthpro-news/weight-loss/many-with-overweight-obesity-discontinue-glp-1-receptor-agonists-within-one-year))

**Prior work and methods cited in the answers**

- Rader, Hazan and Brownstein (2024), JAMA Health Forum: fall in BMI and obesity in 2023 among 16.7 million adults ([summary](https://ajmc.com/view/obesity-prevalence-bmi-decreased-in-us-for-first-time-in-a-decade))
- Gallup: obesity and GLP-1 use, [Oct 2025](https://news.gallup.com/poll/696599/obesity-rate-declining.aspx) and [Jul 2026](https://news.gallup.com/poll/712157/glp-usage-reaches-new-high.aspx)
- Epic Research (2026): GLP-1 use and obesity in Epic Cosmos ([summary](https://www.rttnews.com/3656241/new-epic-research-data-links-growing-glp-1-use-with-falling-obesity-rates-in-us.aspx))
- [NCHS Data Brief 537](https://www.cdc.gov/nchs/products/databriefs/db537.htm) (2025): injectable GLP-1 use among adults with diabetes, NHIS 2024
- [KFF Health Tracking Poll, Nov 2025](https://www.kff.org/public-opinion/poll-1-in-8-adults-say-they-are-currently-taking-a-glp-1-drug-for-weight-loss-diabetes-or-another-condition-even-as-half-say-the-drugs-are-difficult-to-afford/)
- Galindo et al. (2023), Obesity: GLP-1 use in MEPS 2010-2019 ([PDF](https://sochob.cl/web1/wp-content/uploads/2023/11/Use-and-continuity-of-weight‐modifying-medications-among-adults-with-diabetes-and-overweight.pdf))
- Rodriguez et al. (2024), JAMA Internal Medicine: 12-month weight loss with semaglutide and tirzepatide ([summary](https://www.healio.com/news/endocrinology/20240812/tirzepatide-led-to-greater-realworld-weight-loss-than-semaglutide-for-adults-with-obesity))
- Gasoyan et al. (2025), Obesity: weight loss among patients who discontinue treatment ([summary](https://newsroom.clevelandclinic.org/2025/06/10/cleveland-clinic-research-finds-injectable-medications-for-obesity-produce-smaller-weight-loss-in-a-real-world-setting-compared-to-randomized-clinical-trials))
- Callaway, Goodman-Bacon and Sant'Anna (2024), [Difference-in-differences with a Continuous Treatment](https://www.nber.org/papers/w32117), NBER w32117
- Ward et al. (2019), N Engl J Med ([summary](https://news.harvard.edu/gazette/story/2019/12/close-to-half-of-u-s-population-projected-to-have-obesity-by-2030/)) and DeCleene et al. (2026), JAMA ([summary](https://www.healio.com/news/primary-care/20260128/us-obesity-prevalence-projected-to-rise-to-nearly-47-by-2035)): obesity projections
- Wing et al. (2026), [NBER w34949](https://www.nber.org/system/files/working_papers/w34949/w34949.pdf), and Khanna, Wang and Venkataramani (2026), JAMA Health Forum ([summary](https://www.ajmc.com/view/medicaid-obesity-glp-1-coverage-may-offset-some-diabetes-labeled-use)): Medicaid coverage

**Methods (no link)**

- DiNardo, Fortin and Lemieux (1996), Econometrica: reweighting to a fixed composition
- Firpo, Fortin and Lemieux (2009), Econometrica: RIF regression
- Park, Gelman and Bafumi (2004), Political Analysis: MRP
- Rambachan and Roth (2023), Review of Economic Studies: bounds for pre-trends
- Rao and Wu (1988), Journal of the American Statistical Association: rescaled bootstrap
- Lakens (2017), Social Psychological and Personality Science: equivalence tests
- Rubin (1987), Multiple Imputation for Nonresponse in Surveys
