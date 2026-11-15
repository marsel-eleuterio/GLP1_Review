# Implementation notes for the pre-registered analyses

14 November 2026 · Code in `src/glp1_review/`, written before registration and tested on simulated data only
(`tests/`). This note records every step that Q19 does not fully specify and the choice the code makes. Choices
that change results materially were decided by the author and are logged in `decision_log.md`.

## Pre-registration guard

`guard.py`: any loading of real BMI, obesity or height data (`data.load_brfss`) raises an error until
`docs/osf_registration.txt` holds the registration DOI or URL.

## Shared

| Step | Choice | Module |
| --- | --- | --- |
| Stage-2 predictive | Bayesian linear regression under the reference prior: Student-t with n − p df, location = OLS prediction, scale = s·√(1 + x₀′(X′X)⁻¹x₀) | `trend.py` |
| "2022 level" counterfactual (Q24) | Observed 2022 level + slope estimated on 2011-2019; uncertainty from the slope only | `trend.py` |
| Single-PSU strata | Centred at the grand mean of PSU totals (Q23) | `survey.py` |
| Rao-Wu bootstrap | n_h − 1 PSUs drawn with replacement within each stratum, factor n_h/(n_h − 1) | `survey.py` |

## H1 (MRP)

| Step | Choice |
| --- | --- |
| z_s in the first year (2011) | No previous year: uses the next available direct estimate |
| Race in 2015-2016 | No `_IMPRACE`: the race effect is dropped in those years and post-stratification sums over race cells |
| Group effects | N(0, σ) constrained to sum to zero (ZeroSumNormal), non-centred; sex as a fixed effect; state deviations sum to zero (decision log, section 4) |
| Division effect | A group effect like the others |
| Sampler | NUTS via `nutpie` (no C compiler on the build machine); 4 chains × 1,000 draws + 1,000 tuning, target acceptance 0.95 |
| Pairing across years | Yearly fits are independent; Stage 2 pairs draws by index |
| Categories | Age from `_AGEG5YR` (1; 2-3; 4-5; 6-7; 8-9; 10-13), race from `_IMPRACE` (4 and 6 → "other or multiracial"), education from `_EDUCAG` |

## H2

Two-stage inference (decision log, section 3). State × year fixed effects absorbed by a weighted within
transformation (exact by Frisch-Waugh-Lovell). Strata nested within year.

## H3 and NC1

| Step | Choice |
| --- | --- |
| Logistic model of the DFL reweighting | Saturated in the 240 cells (age × sex × race × education): the factor is the ratio of the cell's weighted share in 2017-2019 to its share in the year |
| Quantiles | Weighted ECDF with linear interpolation (Q23) |
| Uncertainty | Rao-Wu bootstrap (500 replicates) repeating reweighting, quantiles and projection, **with the Student-t predictive draw in each replicate**, so that year-level shocks are included, as in H2 |
| NC1 "by sex" | Mean height by sex, each series with its own trend; the estimand is the mean of the two departures, and each sex is reported |

## H4

| Step | Choice |
| --- | --- |
| Prior of the factor noise | σ_j ~ Half-Normal(1) (not specified in Q19) |
| Event study | Unweighted OLS with state and year fixed effects (alternating projections on the unbalanced panel); SE clustered by state |
| Permutation test | Two-sided on \|β*\| (decision log, section 4) |
| Rambachan-Roth bounds | Conservative version (decision log, section 4; declared in Q19): β* ± (1.96·SE + B(M)), where B(M) is the worst-case bias of the linear extrapolation when second differences of the pre-trend path are bounded by M (linear programming). The exact fixed-length interval of HonestDiD (R only) can only be narrower |
| Dose-response | State departure = mean of the available years in 2023-2025 minus the projection of the state's own 2011-2019 trend (at least 3 pre-period years) |

## H5

Within each of the 10,000 parameter draws, the expectation over who uses and who persists is computed exactly
(use probability × persistence) instead of simulating person by person, so the draws carry parameter uncertainty
only. Within a draw the loss is the same for every user.

## H6

LSAQWT, with LONGWT where LSAQWT is missing; strata nested within panel. Persons whose GLP-1 status is unknown in
any panel year are excluded.

## Analysis inputs from the real files (`prepare.py`)

| Input | Construction |
| --- | --- |
| BRFSS rows | 50 states + DC; codes mapped to the ACS categories (`data.harmonise_brfss`); in years without the race variable (2015-2016) race = "Not available" |
| H3/NC1 reweighting in 2015-2016 | Cells drop race in those years and the 2017-2019 reference shares are computed on the same reduced cells (otherwise every cell would be absent from the reference and those years would get zero weight) |
| H4 Medicare indicator | Part D 2024 state rows whose generic name contains semaglutide, tirzepatide, liraglutide, dulaglutide, exenatide, lixisenatide or albiglutide (insulin combinations included); total claims / Census 2024 adults × 100 |
| H4 Medicaid indicator | SDUD 2025 GLP-1 prescriptions, all utilization types (suppressed cells are missing and contribute nothing) / average monthly total Medicaid enrollment in 2025 (final or updated report preferred over preliminary) × 1,000 |
| H4 all-payer indicator | PurpleLab rate per 100 residents in 2024, as audited by The RX Index (pilot data); DC has none, so H4 uses 50 states |
| H5 use probabilities | MEPS 2024 adults with BMI: share with a GLP-1 purchase by BMI class × diabetes, self-administered questionnaire weight (person weight where it is zero) |
| H5 national rates | Lower bound: MEPS 2024 share of adults with a GLP-1 purchase (person weight). Upper bound: 12%, KFF poll of 27 Oct-2 Nov 2025, adults currently taking a GLP-1 for any purpose (verified; `dados_externos/published_estimates.csv`). Gallup's 12.4% refers to weight-loss use only and is not used |
| H6 sample | Panels 23 and 24, present in all nine rounds, adults at the first BMI round, known GLP-1 status in every panel year; BMI clipped to [10, 50] in both rounds (Q15) |
| H6 covariates | From the full-year file of the first BMI year (2018 for Panel 23, 2020 for Panel 24): age group (6 groups), sex, race and ethnicity (RACETHX, 5 groups), diagnosed diabetes, any insurance (INSCOV 1-2); categories with fewer than 5 initiators merged with an adjacent one (Q23) |

## Running

`scripts/run_analysis.py` (after registration) runs H1 → H0 → H2 → H3 → NC1 → H4 → H6 → H5 and the Q22 verdicts,
writing tables, H1 posterior draws, `verdicts.json` and `summary.md` to `resultados/analysis/<timestamp>/`.
`--quick` shrinks draws, replicates and permutations for smoke tests. `tests/test_pipeline.py` runs the whole
pipeline on a simulated tree with the same file layout (`tests/fake_tree.py`) and checks that the guard blocks it
without a registration.

## Q24 sensitivity analyses (`sensitivity.py`)

| Item | Implementation |
| --- | --- |
| Counterfactual trends (H1) | `run.step_h1`: linear 2011-2021, linear 2015-2019, quadratic 2011-2019, 2022 level with the 2011-2019 slope |
| Pandemic years | Removed for H2 (stage 1 and 2) and H4; not applicable to H1 and H3, whose trends use 2011-2019 and whose years are estimated separately |
| Balanced panel | States with BRFSS data in all 15 years: H1 (direct weighted series), H2, H3, H4 |
| Other compositions (H3) | DFL reference 2011 or 2022 instead of 2017-2019 |
| Missing BMI | Departure of the weighted share with missing BMI from its 2011-2019 trend; 20 imputations (`mi.py`, predictive mean matching, proper draws) for the H1 direct series, H2 (Rubin's rules) and H3 (point estimates) |
| Interview mode | Separate estimates for cell-phone and landline interviews (H1 direct series, H2, H3) with the combined-frame weight `_LLCPWT`; mode-specific weights are not used |
| H2 | No age and sex interactions; ages 45-74 (`_AGEG5YR` 6-11); diabetes group reweighted to its 2017-2019 age × sex composition; single regression with a wild cluster bootstrap by state (Webb six-point weights, 9,999 draws, unrestricted); item-change term off |
| H3 | 75th and 95th percentiles; RIF regression (pooled WLS of the RIF on year and cell covariates, evaluated at 2017-2019 covariate means; point estimate) |
| H4 | Each indicator alone; population weights (2024 adults); precision weights (Kish effective n / p(1 − p)); leave-one-state-out range; without WV, KY, LA and OK; without states missing a post-period year; relative-magnitude bounds (conservative: post-period violation per year ≤ M̄ × the largest year-to-year change of the detrended pre-period betas); quartile contrast; cubic average causal response |
| H5 | Loss of non-persistent users U(0%, 4%); persistence fixed at 35.2% and 53.5%; national use fixed at the MEPS 2024 rate |
| H6 | Prevalent users as a third group; LONGWT; persons not present in all rounds; changes > 10 kg/m² excluded; by baseline diabetes; each panel separately |
| NC1 | All adults 18+; by sex |
| External counterfactuals | Observed change 2022-2025 (H1 posterior) minus the change implied by a projection, linear between its published points, over three years. Ward et al. (2019): 42.0% in 2020 to 48.9% in 2030, +0.69 pp a year, +2.07 pp over 2022-2025 (appendix Table 8.1.1, `citation_check.md` D2). DeCleene et al. (2026): 42.5% in 2022 to 46.9% in 2035, +0.34 pp a year, +1.02 pp over 2022-2025 (D1). The projections' own uncertainty is not propagated |
| Self-report correction | `self_report.py`, as in Ward et al. (2019, appendix section 2): by sex and period (BRFSS 2011-2016, 2017-2020, 2021-2025 with NHANES 2011-2016, 2017-March 2020, August 2021-August 2023), measured minus reported BMI at quantiles 0.01-0.99, cubic smoothing spline (GCV), added at each respondent's weighted quantile, N(0, 0.5) noise; variant with one calibration fixed at 2011-2020. H1 departure in 2025 of the direct weighted series, with the corrected 2022 and 2025 levels and the Kolmogorov-Smirnov distance to NHANES before and after (`decision_log.md`, section 7) |
