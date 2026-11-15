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
