---
title: "Is the break in the US adult obesity trend a GLP-1 effect? Pre-registered signature tests in BRFSS 2011–2025 and MEPS 2018–2024"
author:
  - name: Marsel Eleutério
    affiliation: Independent researcher
    orcid: 0009-0008-0021-8866
date: "{{DATE}}"
bibliography: references.bib
abstract: |
  **Background.** Self-reported adult obesity in the United States stopped rising after 2022, while the use of
  GLP-1 receptor agonists multiplied. Earlier reports showed that the two coincide in time, region and age; none
  tested whether the change carries the signatures the drugs would leave.

  **Methods.** In a pre-registered study ([doi:10.17605/OSF.IO/XW7ZG](https://doi.org/10.17605/OSF.IO/XW7ZG)) we estimated the departure of adult obesity from its
  2011–2019 trajectory in 6.0 million BRFSS interviews and tested three signatures that should appear if the drugs
  explain the break: a larger departure among adults with diagnosed diabetes (H2), a larger shift in the upper tail
  of the BMI distribution (H3), and a BMI decrease among adults who start a GLP-1 in the MEPS longitudinal panels
  (H6). A state dose–response analysis (H4), a microsimulation of uptake, persistence and weight loss (H5), and two
  negative controls (self-reported height and a placebo break in 2017) complete the design. Because the multilevel
  model did not meet the pre-registered convergence criteria, the pre-specified composition-adjusted direct series
  was used for the national trend.

  **Results.** In 2025 adult obesity was 1.4 percentage points below its projected trajectory (95% interval 0.5 to 2.2), about 3.7 million adults, and the departure was probably larger than in 2023 (probability 0.96); every alternative counterfactual trend gave a departure of the same sign. Self-reported height showed no departure, and a placebo break in 2017 showed none. The size of the departure was compatible with simulated GLP-1 uptake. States with higher use had larger departures (−0.69 percentage points per standard deviation of use), but the estimate was not robust to the pre-registered bounds on pre-existing trends. The three signature estimates had the predicted sign (diabetes differential −0.16 kg/m²; upper-tail contrast −0.06 kg/m²; initiators −1.0 kg/m²), but none was supported after multiplicity adjustment and none was ruled out: each was classified as inconclusive, and the overall pre-registered verdict is mixed.

  **Conclusions.** The break in the US adult obesity trend is real, is not a reporting artefact detectable in self-reported height, and is of a size that GLP-1 receptor agonists could produce. Current survey data are not precise enough to confirm or exclude the signatures expected of a drug effect. Larger longitudinal samples of new users and measured BMI are needed to attribute the break.
---

<!--
Skeleton of 14 November 2026, written before the OSF registration; results filled on 26 November 2026 from the
full run resultados/analysis/full_20261125 (commit fda46d8). Still open: {{DATE}} and {{REPO.URL}} (at submission)
and {{SENS.MRP}} (post-registration sensitivity, decision_log section 11). paper/README.md maps every placeholder to
its source file and key.
Convert with pandoc: see paper/README.md.
-->

# Introduction

Adult obesity in the United States rose almost every year for three decades. After 2022 the curve bent: the
share of adults with obesity reported to the Behavioral Risk Factor Surveillance System (BRFSS) stopped rising,
Gallup's web panel reported a fall from 39.9% in 2022 to 37.0% in 2025 [@gallup2025], and measured BMI in
the electronic records of 16.7 million adults fell slightly in 2023 [@rader2024]. Over the same years the use of
GLP-1 receptor agonists (semaglutide, tirzepatide and related drugs) multiplied: by late 2025, 12% of US adults,
and 45% of adults with diabetes, reported taking one [@kff2025]. Among adults with diabetes, use was already
rising before 2020 [@galindo2023], and in 2024 about a quarter used an injectable GLP-1 [@nchs537].

The coincidence invites a causal reading, and the reports so far are consistent with it: the fall is largest in
the South, where dispensing is highest [@rader2024], and at ages 40–64, where use is highest [@gallup2025]. But
coincidence in time, region or age is also what secular change, survey artefacts or the end of the pandemic would
produce. No study has asked whether the change has the *shape* that the drugs would give it.

This paper tests that shape. If GLP-1 drugs explain the bend, several predictions must hold together: the
departure should be larger among adults with diagnosed diabetes, who use the drugs several times more often; it
should start in the upper tail of the BMI distribution, where the drugs are prescribed; it should be larger in
states with higher use; it should match what uptake, persistence and per-user weight loss can produce; and
individuals who start the drugs should lose BMI relative to those who do not. Each prediction can fail, and a
measurement artefact would make them come apart. All hypotheses, models and decision rules were registered on the
Open Science Framework before any outcome microdata were analysed ([doi:10.17605/OSF.IO/XW7ZG](https://doi.org/10.17605/OSF.IO/XW7ZG)).

# Data

## BRFSS, 2011–2025

The BRFSS is a state-based telephone survey of non-institutionalized adults, with landline and cell-phone samples
since 2011 [@cdcbrfss]. We use the 15 annual public-use files from 2011 to 2025, restricted to adults in the 50
states and the District of Columbia with a valid body-mass index (6,048,517 interviews). Height and weight are
self-reported ("About how much do you weigh without shoes?"; "About how tall are you without shoes?"). Some
states are missing in some years (New Jersey 2019; Florida 2021; Kentucky and Pennsylvania 2023; Tennessee 2024;
California, Mississippi and Nevada 2025).

Because www.cdc.gov refused automated downloads, the annual files were obtained as a column-for-column Parquet
conversion of the CDC files built from Internet Archive captures of the CDC URLs, at a pinned revision
[@hfbrfss]. Before any other use we reproduced the published state-year obesity prevalence from the CDC open-data
API: across 792 state-years the mean absolute difference was 0.025 percentage points (maximum 0.12), and the
national series matched within 0.05 points in every year. The diabetes item changed name in 2019 (DIABETE3 to
DIABETE4).

## MEPS, 2018–2024

The Medical Expenditure Panel Survey Household Component [@meps] links individual prescription purchases, with
drug names, to self-reported BMI, which adults report in even years. We use the full-year consolidated and
prescribed-medicines files for 2018–2024 and the four-year longitudinal files of Panels 23 (2018–2021) and 24
(2019–2022), in which the same person reports BMI twice. GLP-1 use is a purchase of semaglutide, tirzepatide,
liraglutide, dulaglutide, exenatide, lixisenatide or albiglutide. The primary longitudinal sample has
89 initiators and 5,211 never-users (89 and 5,211 when counted before registration).

## State GLP-1 use, population and published comparators

State use is measured by three indicators: Medicare Part D GLP-1 claims per 100 adult residents in 2024
[@cmspartd], Medicaid GLP-1 prescriptions per 1,000 enrollees in 2025 [@cmssdud], and all-payer prescriptions per
100 residents in 2024 (PurpleLab, as audited by The RX Index). Post-stratification uses American Community Survey
1-year public-use microdata, 2011–2024, for adults outside institutional group quarters, and Census Bureau state
population estimates (Vintage 2025) convert departures into numbers of adults. For the source comparison we use
Gallup's published estimates [@gallup2025; @gallup2026] and NHANES measured estimates [@nchs508].

# Pre-registration

The registration ([doi:10.17605/OSF.IO/XW7ZG](https://doi.org/10.17605/OSF.IO/XW7ZG), 25 November 2026), which follows the secondary-data template of @vandenakker, fixed the hypotheses, models, smallest effects of interest, inference
criteria and sensitivity analyses below, and the analysis code, written and tested on simulated data, was archived
with it. Before registration the microdata were used only to reproduce published aggregates and to count cases.
Changes made to the first draft before registration, each with its reason, are listed in Appendix A.
**After registration.** No hypothesis, model, threshold or decision rule was changed. Four things are reported
here. (i) Three clerical differences between the registered form and the archived plan: research question 4 was
cut short when pasted, an outdated note on the reference list was kept, and the form stores "<" and ">" as HTML
entities; the archived plan has the complete text. (ii) Two implementation fixes found by smoke tests on the real
data before the main run: the survey-variance and bootstrap helpers were rewritten for the BRFSS design (about
36,000 strata), with bit-for-bit identical estimates and random draws and a design covariance equal to rounding
error; and the composition reweighting of one H2 sensitivity analysis now treats a missing age group as its own
cell. (iii) The multilevel model of H1 failed the registered convergence rule in 13 of 15 years, so the
composition-adjusted direct series is the primary H1 series, as the registration prescribes. (iv) One analysis was
added after registration and is labelled as such: the multilevel model fitted in every year without the
convergence gate, reported with its diagnostics (Appendix B). Details are in the decision log of the repository
(sections 9–11).

| | Hypothesis | Prediction | Role |
| --- | --- | --- | --- |
| H0 | Source reconciliation | Describe why Gallup falls and BRFSS does not | Descriptive |
| H1 | Trend break | Obesity in 2023–2025 below its 2011–2019 trajectory, gap widening | Estimation target |
| H2 | Diabetes contrast | Larger departure in mean BMI among adults with diagnosed diabetes | Confirmatory |
| H3 | Upper-tail signature | 90th percentile of BMI departs more than the median | Confirmatory |
| H4 | State dose–response | Larger departure where use is higher | Estimation target |
| H5 | Mechanical plausibility | Departure within what uptake × persistence × loss can produce | Consistency check |
| H6 | Individual change | GLP-1 initiators lose BMI relative to never-users; no change before initiation | Confirmatory |
| NC1 | Height | No departure in self-reported height (±0.5 cm) | Negative control |
| NC2 | Placebo break | No departure at a pseudo-break in 2017 | Negative control |

: Pre-registered hypotheses. {#tbl:hypotheses}

**Inference.** The three confirmatory predictions are directional and tested one-sided with Holm's adjustment
[@holm1979]. A hypothesis is *supported* if its Holm-adjusted p-value is below 0.05; *contradicted* if the whole
90% confidence interval lies above minus its smallest effect of interest (−0.2 kg/m² for H2, −0.3 for H3, −0.5
for H6), which includes significant estimates in the opposite direction; and *inconclusive* otherwise. The
overall verdict is "signature present" if at least two of H2, H3 and H6 are supported, none is contradicted and the
height control passes; "absent" if at least two are contradicted or the height control fails; and "mixed"
otherwise.

# Methods

## H1: departure from the 2011–2019 trajectory

For each year we fit a multilevel logistic model of obesity to cells of state × age group (6) × sex × race and
ethnicity (5) × education (4) [@park2004]. State effects are centred on a division effect plus a predictor built
from the state's direct estimate in the previous available year, so that states missing in a year are predicted.
Group effects are normal with half-normal scales and constrained to sum to zero, sex enters as a fixed effect, and
the model is fitted with the No-U-Turn sampler in PyMC (4 chains × 1,000 draws). Post-stratification to ACS adult
counts gives posterior draws of national prevalence. For each draw a linear trend in the logit of prevalence is
fitted to 2011–2019 and projected to 2023–2025 with its closed-form posterior predictive (Student-t, 7 degrees of
freedom); the departure is observed minus projected prevalence. Each year's fit had to meet a convergence rule
(R-hat below 1.01, bulk effective sample size above 400 and no divergent transitions, for every parameter), with a
registered sequence of remedies (more tuning, a higher target acceptance, dropping the age × sex interaction, then
education). If any year failed every step, the registration made the composition-adjusted direct series the primary
national series: weighted two-way fixed effects (state and year) on the direct state estimates, with the national
value of each year the population-weighted mean over all states, which also fills states missing in a year. That
series has no posterior draws; its departure carries the Student-t predictive uncertainty of the trend projection.

## H2: diabetes contrast

On individual BRFSS records, a survey-weighted regression of BMI on state × year fixed effects, age group × sex,
race and ethnicity, education and income, and a diagnosed-diabetes indicator interacted with age group, sex and
year, gives the diabetes gap for every year. A linear trend plus a level shift at the 2019 item change is fitted
to the 2011–2019 gaps and projected to 2023–2025; the estimand is the mean departure of the gap, π̄, in kg/m², with
the Student-t predictive (6 degrees of freedom) as reference distribution. This two-stage inference includes
year-level shocks to the gap, which a single regression's design-based standard error would ignore.

## H3: upper tail

Each year's sample is reweighted to the 2017–2019 joint distribution of age group, sex, race and ethnicity and
education [@dinardo1996]. Weighted BMI quantiles (10th to 95th percentiles) go through the same trend procedure,
and the estimand is the mean 2023–2025 departure of the 90th percentile minus that of the median. Uncertainty comes
from a Rao–Wu rescaled bootstrap of primary sampling units within strata [@rao1988] (500 replicates), repeating
the reweighting, quantiles and projection in each replicate.

## H4: states

The exposure is the posterior mean of a one-factor model of the three standardized use indicators. An event study
of state obesity on state and year effects and exposure × year interactions, normalized to 2015–2019, gives β*,
the mean 2023–2025 coefficient minus its projection from a linear trend in the 2011–2019 coefficients. Inference
uses a two-sided randomization test that permutes the exposure across states (20,000 permutations) and smoothness
bounds for pre-trends [@rambachan2023], computed conservatively; uncertainty in the exposure is propagated over
200 posterior draws with Rubin's rules [@rubin1987]. A dose–response analysis following
@callaway2024 contrasts the top and bottom terciles of exposure and reports the average causal response.

## H5: mechanical plausibility

A microsimulation applies GLP-1 use probabilities by BMI class and diabetes (MEPS 2024), scaled so that national
use lies between the MEPS 2024 rate and the 12% reported for 2025 [@kff2025], one-year persistence
[@rodriguez2025] and per-user weight loss from real-world cohorts and trials [@rodriguez2024; @gasoyan2025;
@wilding2021; @jastreboff2022] to the 2025 BRFSS BMI distribution, giving the obesity reduction the drugs could
produce (10,000 draws).

## H6: individual change

In the MEPS panels, a weighted regression of the two-year change in BMI on initiation (first purchase between the
two measurements), panel, a quadratic in baseline BMI and baseline covariates compares initiators with never-users,
with design-based standard errors. Late initiators in Panel 23, who start only after the second measurement, are a
placebo; the comparison of initiators with late initiators is a not-yet-treated contrast.

## Negative controls and sensitivity analyses

Self-reported height of adults 25–64, composition-adjusted as in H3, must show no departure (equivalence within
±0.5 cm) [@lakens2017]. The H1 and H2 procedures applied to a pseudo-break in 2017 must show none either. The
pre-registered sensitivity analyses (alternative counterfactual trends, pandemic years removed, balanced panel of
states, multiple imputation of missing BMI, interview mode, and hypothesis-specific variants) are reported in full
in Appendix B.

All code, from download to tables, is in the project repository and the OSF archive ({{REPO.URL}}).

# Results

## Sources disagree on the trend, not only on the level (H0)

The three sources differ in level, as expected from self-report against measurement: NHANES, which measures height
and weight, found 40.3% of adults with obesity in August 2021–August 2023 [@nchs508]; Gallup reported 39.9% in 2022
and BRFSS 33.3% (Figure 1). They also differ in direction. From 2022 to 2025 Gallup fell 2.9 points, while BRFSS
rose 0.2 points as published and fell 0.4 points once the states missing in 2025 are accounted for. Gallup's 2022
peak rests on 3,035 interviews collected in one January week (margin ±2.0 points), and its weights were revised in
September 2026; NHANES ends before the period of the decline.

![US adult obesity by source. Panel A: long-run published series. Panel B: level in 2022 and 2025 and change.](../docs/figures/h0_published_series.png){#fig:h0}

In BRFSS, obesity did not fall at the ages where Gallup reports its largest declines: from 2022 to 2025 it changed by 0.3 points at 30–39 (SE 0.6), 0.5 at 40–49 (0.7) and 0.9 at 50–64 (0.5), against Gallup's −2.2, −4.3 and −5.0; overall, 0.1 against −2.9.

## The departure from the 2011–2019 trajectory (H1)

The multilevel model met the pre-registered convergence rule in only two years (2021 and 2024); in the other 13 it failed every step of the registered sequence, by small margins (maximum R-hat 1.008–1.026, minimum bulk effective sample size 210–520, 0–6 divergent transitions). As registered, the national series is therefore the composition-adjusted direct series: weighted two-way fixed effects on the state estimates, which also fills states missing in a year. Its uncertainty comes only from the trend projection. The departure was −0.41 points in 2023 and −0.64 in 2024, with intervals that include zero. In 2025, obesity was −1.37 percentage points (95% predictive interval −2.23 to −0.54) from its
projected value, about 3.7 million fewer adults with obesity than projected (95% interval 1.5 to 6.0); the probability that the 2025 departure exceeds the
2023 departure is 0.96. The alternative counterfactual trends give −1.77 (linear, 2011–2021), −2.33 (linear, 2015–2019), −2.87 (quadratic, 2011–2019) and −1.95 points (2022 level with the 2011–2019 slope). Classification: break present.

## Diabetes contrast (H2)

The diabetes gap in mean BMI fell below its 2011–2019 trend in 2023–2025 in the predicted direction, but by less than the smallest effect of interest (−0.2 kg/m²). The one-sided p-value was 0.044 before adjustment, and the 90% confidence interval (−0.32 to −0.01) does not exclude effects of interest. π̄ = −0.16 kg/m² (SE 0.08; Holm-adjusted one-sided p 0.13): inconclusive.

## Upper tail (H3)

The 90th percentile of BMI departed from its trend by about as much as the median. The 90% confidence interval (−0.40 to 0.28) is wide enough to include both no effect and the smallest effect of interest (−0.3 kg/m²). C = −0.06 kg/m² (SE 0.21; Holm-adjusted p 0.39): inconclusive.

## States (H4)

States with higher GLP-1 use departed more from their own 2011–2019 trajectories after 2022. The gradient did not depend on the four states that drove the pilot estimate, on the weighting or on any single state (although the Medicaid indicator alone showed none), and the top tercile of use fell 1.70 points further below its trajectory than the bottom tercile (average causal response −0.73). The yearly slopes were already negative in 2011–2014 (−0.57 to −0.23), however, and once departures from a linear pre-trend of the size allowed by the registration are admitted, the interval includes zero; by the registered rule the result is not supportive, and the gradient is a causal response only under strong parallel trends. β* = −0.69 percentage points per standard deviation of use (permutation p < 0.001;
smoothness-bound interval at M = 0.02: −1.82 to 0.44). Without West Virginia, Kentucky, Louisiana and Oklahoma:
−0.70 (SE 0.20). Classification: not supportive.

## Individual change (H6)

Adults who started a GLP-1 between the two BMI measurements lost BMI relative to never-users, by an amount within the range expected (−0.5 to −3 kg/m²), but with a standard error close to two-thirds of the estimate; the 90% confidence interval (−2.05 to 0.01) includes zero. Adults who started only after the second measurement did not lose BMI beforehand. Compared with those late initiators, who also chose the drug, initiators changed by −1.93 kg/m² (SE 0.85; secondary contrast, Panel 23 only). Initiators changed BMI by −1.02 kg/m² relative to never-users over two years (SE 0.63;
Holm-adjusted p 0.13); late initiators (placebo): 1.29 kg/m² (SE 0.91), not significantly negative. Classification: inconclusive.

## Mechanical plausibility (H5)

Applying GLP-1 use, persistence and per-user weight loss to the 2025 BMI distribution gives a reduction in obesity of the same order as the observed departure. The microsimulation gives a reduction of −1.15 percentage points (90% range −1.81 to −0.67),
against the observed departure of −1.37: compatible.

## Negative controls

Height: −0.11 cm (90% CI −0.21 to −0.004); equivalence within ±0.5 cm established: passes. Placebo break in 2017: with the trend fitted to 2011–2015, the departures of the national series in 2017–2019 were 0.19 (−1.00 to 1.32), 0.66 (−0.88 to 1.97), 0.51 (−0.89 to 2.00) points, and the placebo diabetes differential was −0.05 kg/m² (SE 0.11); both pass.

## Overall verdict

**Mixed.** None of the three confirmatory signatures was supported and none was contradicted, and the height control passed. The pre-registered rule therefore classifies the evidence for a GLP-1 signature as mixed: the data neither confirm nor exclude it.

# Discussion

The pre-registered question was not whether US adult obesity stopped rising, but whether the change has the shape
GLP-1 receptor agonists would give it. The answer is in two parts. The break is clear: in 2025 obesity was about
1.4 percentage points, or 3.7 million adults, below its 2011–2019 trajectory, under every
counterfactual trend we registered, with no departure in self-reported height and no break at a placebo date. And
its size is what the drugs could produce: a microsimulation built from observed uptake, persistence and weight
loss gives a reduction of the same order. The shape, however, is not resolved. The three signatures that should
distinguish a drug effect from other causes all had the predicted sign, but each was estimated with too little
precision to be supported or ruled out. The state gradient was strong and stable across specifications but did not
survive the registered allowance for pre-existing trends.

Three features of the data limit what they can show. The diabetes contrast (H2) is estimated from a gap that varies
from year to year more than its sampling error, and with nine pre-period years the projected gap is uncertain; the
estimate (−0.16 kg/m²) lies between no effect and the smallest effect of interest. For the upper tail (H3), the bootstrap
interval is wider than the smallest effect of interest, and the point estimate is close to zero. The MEPS panels (H6) end in 2022, before the largest rise in use,
and contain 89 initiators; the registration anticipated that H6 would be underpowered at its smallest effect
of interest, and the estimate (−1.0 kg/m²) is larger than that threshold but not distinguishable from zero.

Two results bear on alternatives to a drug effect. Self-reported height did not change, which argues against a
shift in how respondents report their body size large enough to move BMI. And BRFSS does not reproduce the
age pattern that Gallup reports: obesity did not fall among adults aged 40–64, where use is highest (Section H0).
The sources differ in mode, frame and weighting, and the registered design cannot say which is closer to the
truth; NHANES measurements after 2023 would settle it.

The multilevel model did not meet the registered convergence criteria, which were strict (every one of several
hundred parameters had to reach R-hat below 1.01, an effective sample size above 400 and no divergent
transition). The registered fallback, the composition-adjusted direct series used in the pilot, is therefore the
primary national series; the multilevel estimates are reported as a sensitivity analysis added after registration
(Appendix B).

Attributing the break will need data that track individuals who start the drugs over longer periods, with measured
weight, and a larger number of years after 2022 to estimate the diabetes and upper-tail contrasts precisely. Until
then, the honest summary is that the bend in the curve is real and of a plausible size for a drug effect, but its
cause is not established.

**Limitations known before the results.** BMI in BRFSS and MEPS is self-reported, and its bias may change with
the interview mode, which shifted from landline to cell phone over the period. State use measures count claims or
prescriptions, not people; Medicare counts by prescriber state, and only one measure, from a commercial source,
covers private insurance. The MEPS panels end in 2022, before the largest increase in use, and include
89 initiators, so H6 has limited power at its smallest effect of interest. The BRFSS files were
obtained through a mirror of Internet Archive captures, validated against the CDC aggregates, and a later CDC
re-release would not be reflected. Several states are missing in some years, including three in 2025.

# Data and code availability

All data are public. Download scripts with checksums, provenance records, the analysis code and its tests, and the
pre-registration are in {{REPO.URL}} and attached to the OSF registration ([doi:10.17605/OSF.IO/XW7ZG](https://doi.org/10.17605/OSF.IO/XW7ZG)).

# Use of AI assistance

The pilot, the download scripts, the analysis code, the check of cited numbers and drafts of this paper were
prepared with an AI assistant (Claude, Anthropic) under the author's direction. The author is responsible for
every analytic decision and for the text.

# Funding and competing interests

No funding. The author declares no competing interests.

# Appendix A. Changes to the first pre-registration draft {-}

Made before registration, with reasons, in `docs/decision_log.md`: one-sided tests and a reachable contradiction
rule for the confirmatory family (Q21, Q22); two-stage inference for H2 (Q19); the placebo window of H2 restricted
to 2017–2018 because the diabetes item changes in 2019; sum-to-zero group effects and sex as a fixed effect in the
MRP model, which did not converge as first specified (Q19, Q23); a two-sided permutation test and conservative
smoothness bounds for H4; race treated as "not available" in 2015–2016; the 12% KFF rate as the upper bound of
national use in H5.

# Appendix B. Sensitivity analyses {-}

The RIF variant of H3 follows @firpo2009. The observed change from 2022 to 2025 is compared with the change implied by two projections made before the
rise in use. @ward2019 forecast national adult obesity (ages 18+) rising from 42.0% in 2020 to 48.9% in 2030,
about 2.1 points over 2022-2025; @decleene2026 forecast 42.5% in 2022 and 46.9% in 2035 (ages 20+), about 1.0
point: the primary national series changed by −0.37 points from 2022 to 2025, against projected increases of 2.07 (Ward et al.) and 1.02 points (DeCleene et al.), shortfalls of −2.44 and −1.38 points. Changes are compared, not levels, because both projections are calibrated to measured
BMI.

Self-reported BMI was also corrected with NHANES measurements, following @ward2019. Within each sex and period,
the difference between measured (NHANES) and reported (BRFSS) BMI was estimated at each percentile, smoothed
with a cubic spline, and added to each respondent's BMI at their percentile, with normal noise (SD 0.5) for the
rounding of reported height and weight. The periods pair BRFSS 2011-2016, 2017-2020 and 2021-2025 with the
NHANES cycles of 2011-2016, 2017-March 2020 and August 2021-August 2023; no NHANES data cover 2024-2025, so the
last calibration is carried forward. A variant applies one calibration, from 2011-2020, to every year:
the 2025 departure of the corrected direct series is −5.84 points with period-specific calibrations (corrected prevalence 39.6% in 2022 and 39.8% in 2025) and −1.00 point with the fixed calibration (42.4% and 42.5%). The period-specific calibration changes in 2017 and 2021, inside and after the trend window, so part of its larger departure reflects the change of calibration; the fixed calibration is the cleaner comparison.

**Multilevel model without the convergence gate (added after registration).** {{SENS.MRP}}

| Hypothesis | Variant | Estimate | SE | 95% interval | Note |
| --- | --- | --- | --- | --- | --- |
| H1 | primary (direct weighted series, for comparison) | −0.92 |  |  | D2025, pp, predictive mean |
| H1 | balanced panel of states (direct series) | −1.66 |  |  | 43 states |
| H1 | interview mode: cell only (direct series) | −2.27 |  |  | combined-frame weights |
| H1 | interview mode: landline only (direct series) | −4.95 |  |  | combined-frame weights |
| H1 | share with missing BMI: departure from 2011-2019 trend, mean 2023-2025 | −2.63 |  |  | pp; a rise could mimic a decline |
| H1 | multiple imputation of BMI (20), direct series | −0.94 | 0.09 |  | se = between-imputation SD |
| H1 | pandemic years removed |  |  |  | not applicable: the primary trend uses 2011-2019 and each year is fitted separately |
| H1 | external: observed change 2022-2025 (primary H1 series) | −0.37 |  |  | pp |
| H1 | external: observed minus projected change, DeCleene et al. 2026 (IHME; data to 2022; ages 20+, bias-corrected) | −1.38 |  |  | projected change 2022-2025 = +1.02 pp (42.5% in 2022 to 46.9% in 2035) |
| H1 | external: observed minus projected change, Ward et al. 2019 (BRFSS 1993-2016, NHANES-corrected; ages 18+) | −2.44 |  |  | projected change 2022-2025 = +2.07 pp (42.0% in 2020 to 48.9% in 2030) |
| H1 | self-report correction (NHANES-calibrated, by sex and period, as in Ward et al. 2019), direct series | −5.84 |  |  | D2025, pp; corrected prevalence 39.6% (2022), 39.8% (2025); KS distance to NHANES 0.123 before, 0.014 after (max over sex x period) |
| H1 | self-report correction (NHANES-calibrated, calibration fixed at 2011-2020), direct series | −1.00 |  |  | D2025, pp; corrected prevalence 42.4% (2022), 42.5% (2025); KS distance to NHANES 0.105 before, 0.021 after (max over sex x period) |
| H2 | without age and sex interactions | −0.11 | 0.07 | −0.28 to 0.07 |  |
| H2 | ages 45-74 only | −0.14 | 0.12 | −0.43 to 0.15 |  |
| H2 | diabetes group reweighted to its 2017-2019 age x sex composition | −0.16 | 0.08 | −0.37 to 0.05 |  |
| H2 | single regression, wild cluster bootstrap by state (Webb) | −0.16 | 0.11 | −0.37 to 0.05 | 51 clusters |
| H2 | item-change term off | −0.20 | 0.09 | −0.40 to 0.01 |  |
| H2 | pandemic years removed | −0.16 | 0.08 | −0.36 to 0.03 |  |
| H2 | balanced panel of states | −0.27 | 0.14 | −0.61 to 0.08 |  |
| H2 | interview mode: cell only | −0.21 | 0.18 | −0.64 to 0.23 |  |
| H2 | interview mode: landline only | −0.32 | 0.08 | −0.50 to −0.13 |  |
| H2 | multiple imputation of BMI (20) | −0.19 | 0.09 | −0.36 to −0.02 | Rubin's rules |
| H3 | 75th percentile in place of the 90th | 0.04 | 0.14 | −0.25 to 0.32 |  |
| H3 | 95th percentile in place of the 90th | 0.14 | 0.23 | −0.32 to 0.60 |  |
| H3 | reweighting to the 2011 composition | −0.02 | 0.18 | −0.38 to 0.34 |  |
| H3 | reweighting to the 2022 composition | −0.16 | 0.18 | −0.51 to 0.19 |  |
| H3 | RIF regression with covariates instead of reweighting | −0.08 |  |  | point estimate |
| H3 | balanced panel of states | 0.06 | 0.20 | −0.34 to 0.46 |  |
| H3 | interview mode: cell only | −0.09 | 0.22 | −0.53 to 0.34 |  |
| H3 | interview mode: landline only | 0.19 | 0.24 | −0.28 to 0.66 |  |
| H3 | multiple imputation of BMI (20) | −0.13 | 0.05 |  | point estimates; se = between-imputation SD |
| H3 | pandemic years removed |  |  |  | not applicable: the trend uses 2011-2019 and the contrast 2023-2025 |
| NC1 | all adults 18+ | −0.04 | 0.05 | −0.14 to 0.07 |  |
| NC1 | by sex: Female | −0.16 |  |  | point estimate |
| NC1 | by sex: Male | −0.05 |  |  | point estimate |
| H4 | indicator alone: medicare_claims_per100_adults_2024 | −0.67 | 0.20 | −1.07 to −0.28 | permutation p 0.000 |
| H4 | indicator alone: medicaid_rx_per1000_enrollees_2025 | −0.03 | 0.17 | −0.36 to 0.31 | permutation p 0.889 |
| H4 | indicator alone: allpayer_rx_per100_2024 | −0.74 | 0.17 | −1.07 to −0.41 | permutation p 0.000 |
| H4 | population weights | −0.76 | 0.27 | −1.28 to −0.23 | permutation p 0.002 |
| H4 | precision weights (1 / sampling variance, Kish n) | −0.67 | 0.17 | −1.01 to −0.34 | permutation p 0.000 |
| H4 | leave-one-state-out (range) | −0.72 |  | −0.83 to −0.60 | estimate = mean of the 50 fits |
| H4 | without WV, KY, LA and OK | −0.70 | 0.20 | −1.09 to −0.31 | permutation p 0.001 |
| H4 | without states missing a post-period year | −0.63 | 0.23 | −1.07 to −0.19 | permutation p 0.001 |
| H4 | Rambachan-Roth relative magnitude, Mbar = 0.5 | −0.72 | 0.19 | −2.08 to 0.63 | conservative |
| H4 | Rambachan-Roth relative magnitude, Mbar = 1.0 | −0.72 | 0.19 | −3.06 to 1.62 | conservative |
| H4 | dose-response, quartiles (top minus bottom) | −1.87 |  |  |  |
| H4 | dose-response, cubic fit (average causal response) | −0.71 |  |  |  |
| H4 | pandemic years removed | −0.72 | 0.19 | −1.09 to −0.35 | permutation p 0.000 |
| H4 | balanced panel of states | −0.65 | 0.23 | −1.09 to −0.20 | permutation p 0.001 |
| H5 | loss of non-persistent users U(0%, 4%) | −0.97 |  | −1.58 to −0.55 | compatible |
| H5 | persistence fixed at 35.2% and 53.5% | −1.16 |  | −1.80 to −0.68 | compatible |
| H5 | national use fixed at the MEPS 2024 rate | −0.69 |  | −0.89 to −0.50 | compatible |
| H6 | prevalent users as a third group | −1.00 | 0.62 | −2.22 to 0.22 |  |
| H6 | LONGWT instead of LSAQWT | −1.36 | 0.65 | −2.63 to −0.10 |  |
| H6 | persons not present in all rounds included | −0.97 | 0.60 | −2.14 to 0.20 |  |
| H6 | changes larger than 10 kg/m2 excluded | −1.07 | 0.59 | −2.23 to 0.09 |  |
| H6 | by diabetes status: with diabetes | −0.74 | 0.66 | −2.04 to 0.56 | 71 initiators |
| H6 | by diabetes status: without diabetes | −0.67 | 1.08 | −2.79 to 1.46 | 18 initiators |
| H6 | Panel 23 only | −1.62 | 0.82 | −3.24 to −0.01 | 44 initiators |
| H6 | Panel 24 only | −0.44 | 0.87 | −2.14 to 1.25 | 45 initiators |

: Pre-registered sensitivity analyses (Q24), full table. Units: H1 percentage points (departure in 2025 unless stated); H2, H3 and H6 kg/m²; H4 percentage points per SD of use; H5 percentage points; NC1 cm. {#tbl:q24}

# References {-}
