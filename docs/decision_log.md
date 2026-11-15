# Decision log before registration

Marsel Eleutério · 14 November 2026 · Changes to the first pre-registration draft (`preregistro_osf_rascunho.md`)
applied in v2 (`preregistro_osf_v2.md`), each with its reason. All were made before any outcome microdata were
analysed. Several were found while testing the analysis code on simulated data (`tests/`).

## 1. Smallest effects of interest (Q20) and inference criteria (Q22)

### Assumptions

Standard errors are those of the first draft, with the actual H6 count:

| Hypothesis | Estimand | SE | Source |
| --- | --- | --- | --- |
| H2 | π̄, diabetes differential (kg/m²) | 0.11 | Q21: SD 6.3, design effect 1.8, ~50,000 adults with diabetes a year, residual SD 0.08 |
| H3 | C, P90 − P50 contrast (kg/m²) | 0.20 | Q21: annual residual SD 0.15 |
| H6 | β, initiators vs never-users (kg/m², 2 years) | 0.33 | SD(ΔBMI) 2.5, design effect 1.5, **89 initiators and 5,211 never-users** (Q13) |

### Power to be classified "supported"

With Holm, the first hypothesis tested uses α/3, the relevant case when only one of the three has an effect.

| True effect | H2 two-sided α 0.05 (draft Q21) | H2 two-sided Holm | H2 one-sided Holm | H3 two-sided α 0.05 | H3 two-sided Holm | H3 one-sided Holm | H6 two-sided α 0.05 | H6 two-sided Holm | H6 one-sided Holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| −0.2 | 44% | 28% | 38% | 17% | 8% | 13% | 9% | 4% | 6% |
| −0.3 | 78% | 63% | 73% | 32% | 19% | 26% | 15% | 7% | 11% |
| −0.5 | ~100% | 98% | 99% | 71% | 54% | 65% | 33% | 19% | 27% |
| −0.75 | 100% | 100% | 100% | 96% | 91% | 95% | 63% | 46% | 56% |
| −1.0 | 100% | 100% | 100% | 100% | 100% | 100% | 86% | 75% | 82% |

The first draft reported power without the Holm adjustment.

### Problem: H3 and H6 could never be "contradicted"

In the first draft a hypothesis was contradicted if equivalence testing (TOST, α 0.05) showed its effect to be
smaller than the smallest effect of interest (SESOI), which requires the whole 90% interval to lie within ±SESOI.
The half-width of that interval is 1.645 × SE:

| Hypothesis | SESOI (Q20) | 90% CI half-width | P(contradicted) if the true effect is zero |
| --- | --- | --- | --- |
| H2 | −0.2 | 0.18 | 14% |
| H3 | −0.3 | 0.33 | **0%, impossible** |
| H6 | −0.5 | 0.54 | **0%, impossible** |

The overall verdict "absent" requires two contradicted hypotheses (or NC1 failing). Only H2 could be contradicted
by equivalence, with a 14% chance, so a true absence of the drug signature would almost certainly have been
labelled "mixed", never "absent".

### Options considered

- **A. One-sided contradiction:** contradicted if the whole 90% CI lies above −SESOI (one-sided test that the
  effect is less negative than the SESOI, α 0.05). SESOIs unchanged. P(contradicted | zero effect): H2 57%, H3 44%,
  H6 45%. A significant positive estimate still counts as contradiction.
- **B. One-sided test for "supported"**, consistent with the directional predictions and with A. Modest gain (H6
  at −1.0: 75% → 82% with Holm).
- **C. Raise the SESOIs until detectable** (H3 −0.5; H6 −1.0). Rejected: a SESOI must be a substantive threshold,
  not a consequence of sample size.
- **D. Keep the draft rules** and state that H3 and H6 can only be supported or inconclusive.

### Decision

1. **One-sided contradiction** (A) for H2, H3 and H6.
2. **One-sided test for "supported"** (B), Holm across the three.
3. **H6 SESOI kept at −0.5 kg/m²**; its low power at that value is declared in Q21.

Applied in v2: Q21 (one-sided power, unadjusted and at the first Holm step, and P(contradicted) at zero effect)
and Q22 (definitions of supported, contradicted and inconclusive, with the rationale). Q20 and the overall
verdict rule are unchanged.

## 2. Covariates and post-stratification

- **Race and ethnicity in BRFSS 2015-2016:** `_IMPRACE` does not exist in those years. It enters as a separate
  "not available" category in models that adjust for race; sensitivity: models without race and ethnicity (Q12).
- **ACS post-stratification:** adults outside institutional group quarters only, because BRFSS samples
  households (Q16; `scripts/census_download.py`).

## 3. H2 inference, tie rule, NC2 window

Found while testing the code on simulated data (`tests/test_h2.py`):

- **H2 uncertainty.** A single regression's design-based SE reflects sampling error only and ignores year-level
  shocks to the diabetes gap (the residual SD 0.08 that Q21 uses for power); with about 400,000 interviews a year
  the interval would be far too narrow. In addition, κ (diabetes item change in 2019) would rest on 2019 alone.
  **Decision:** two-stage inference (yearly gaps, then trend + κ fitted to 2011-2019 and projected to 2023-2025,
  Student-t with 6 df), as in H1. The single regression is kept as a secondary result. In simulations with
  year-level shocks the single regression loses coverage and the two-stage version keeps it. Recomputed H2 power
  (Q21): 26% at −0.2, 53% at −0.3 and 79% at −0.4 at the first Holm step.
- **Tie in Q22.** An estimate that is significantly negative but shown to be smaller than the SESOI is
  **contradicted**.
- **NC2 for H2.** The pre-registered placebo window (departure in 2017-2019) includes 2019, the year the
  diabetes item changes, and κ cannot be estimated inside it. **Decision:** for H2 the placebo departure is
  measured in 2017-2018 (trend on 2011-2015). NC2 for H1 stays in 2017-2019.

## 4. H1 model and H4 inference

- **H1 (MRP).** As specified in the first draft, the model did not converge on simulated data under any of the
  five Q23 steps (R-hat up to 1.23; bulk ESS 13-63): the intercept and the unconstrained group effects can shift
  jointly without changing predictions. **Decision:** sum-to-zero group effects (ZeroSumNormal) in non-centred
  form, sex as a fixed effect, target acceptance 0.95. Result on BRFSS-sized simulations: R-hat ≤ 1.005,
  ESS > 2,000, national prevalence recovered within ~0.1 pp. New Q23 sequence: 2,000 tuning steps; target
  acceptance 0.99; drop age × sex; drop education.
- **H4 permutation test:** two-sided on |β*|.
- **Rambachan-Roth bounds:** conservative version in Python (worst-case bias under ΔSD(M) added to the 95% CI),
  declared in Q19; the exact fixed-length interval (HonestDiD, R only) can only be narrower.

## 5. H5 upper national rate and Q24 coverage (14 November 2026)

- **H5 upper bound of national use:** 12% (KFF poll, 27 October-2 November 2025: adults currently taking a GLP-1
  for any purpose), verified against the source. Gallup's 12.4% refers to weight-loss use only; MEPS, the lower
  bound, counts any purpose, so the KFF figure is the consistent upper bound. Confirmed by the author.
- **Q24 sensitivity analyses** are implemented in `src/glp1_review/sensitivity.py` and run by the `q24` step of the
  pipeline. Interview mode uses `QSTVER` (10-13 landline, 20-23 cell) and the BMI imputation uses `GENHLTH`; both
  were added to the extraction by `scripts/brfss_extract_parquet.py`, leaving `brfss_microdata.py` unchanged.
  Two Q24 items wait for the reading of the original articles, because they need numbers from them: the external
  counterfactuals (Ward et al. 2019; DeCleene et al. 2026) and the NHANES-calibrated self-report correction
  (Ward et al. 2019).

## 6. External counterfactual (14 November 2026)

The DeCleene et al. (2026) projection was verified in the original (42.5% of adults in 2022 to 46.9% in 2035) and
the Q24 comparison was implemented: the observed 2022-2025 change from the H1 posterior minus the projected change,
taken as linear between the two published points (+0.34 pp a year, +1.02 pp over three years). The projection's own
uncertainty is not propagated because its interval for the change is not published. The Ward et al. (2019)
comparison and the self-report correction remain pending until the full text is read.
