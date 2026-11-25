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
comparison and the self-report correction remain pending until the full text is read (done: section 7).

## 7. Ward et al. (2019): projection and self-report correction (15 November 2026)

The author saved the article and its supplementary appendix locally (nejm.org refuses automated downloads; the
files stay outside the repository, in the git-ignored `literatura/`).

- **External counterfactual.** Appendix Table 8.1.1, US (National): 35.1% in 2010, 42.0% in 2020 and 48.9% in 2030
  (adults 18+, BRFSS corrected with NHANES). The Q24 comparison uses 2020 and 2030, the two points that bracket
  2022-2025: +0.69 pp a year, +2.07 pp over three years. The gain is 6.9 pp in each decade, so the straight line
  follows the fitted multinomial-logistic curve closely. Ward's population (18+) matches ours; DeCleene's is 20+.
- **Self-report correction.** Implemented as in the appendix (section 2): within sex and period, measured minus
  reported BMI at each quantile, smoothed with a cubic spline over the quantiles, added to each respondent at the
  weighted quantile of their reported BMI, plus normal noise (SD 0.5) for rounding; Kolmogorov-Smirnov distance
  between corrected and measured distributions reported as a check. Choices where the paper is silent, or where our
  years differ from theirs:
  - **Periods.** BRFSS 2011-2016 with NHANES 2011-2012, 2013-2014 and 2015-2016 (Ward's own last period);
    BRFSS 2017-2020 with NHANES 2017-March 2020; BRFSS 2021-2025 with NHANES August 2021-August 2023. No NHANES
    data cover 2024-2025, so the 2021-2023 calibration is carried forward.
  - **Variant added: one calibration fixed at 2011-2020**, applied to every year. Reason: the period-specific
    calibration matches each period's BRFSS distribution to NHANES, so it imports the NHANES level of 2021-2023
    into 2021-2025 and puts a step at each period boundary, two of which fall inside the 2011-2019 trend window.
    The fixed calibration removes the level and shape of the bias and keeps all of the BRFSS change after 2020.
    Both are reported; neither enters a verdict.
  - **Quantile grid and smoothing.** Quantiles 0.01 to 0.99 in steps of 0.01 (weighted, linear interpolation as in
    H3); cubic smoothing spline with the penalty chosen by generalized cross-validation
    (`scipy.interpolate.make_smoothing_spline`).
  - **Quantile of each respondent.** Weighted mid-point rank within sex and period, over the pooled years, so the
    correction is one map from reported to corrected BMI for the whole period and changes within a period are kept.
  - **NHANES.** Adults 18+ with measured BMI, pregnant women excluded, MEC examination weights; when cycles are
    pooled, weights are scaled by the years each cycle covers (3.2 for 2017-March 2020). Downloaded by
    `scripts/nhanes_download.py`, which reproduces the NCHS Data Brief 508 age-adjusted prevalence within 0.04 pp
    for 2013-2014, 2015-2016, 2017-March 2020 and 2021-2023 (`dados_limpos/nhanes/nhanes_check.csv`).
  - **Difference from Ward.** Pregnant BRFSS respondents are not excluded (the item is not in our extraction);
    the corrected series feeds the H1 direct weighted series, not the MRP model.
- The correction is applied only to BRFSS data read through the guarded loader; before registration it was tested
  on simulated data only.

## 8. Code review before registration (16 November 2026)

A review of `src/glp1_review/` against the pre-registration, before the code is frozen, found ten problems. Nine
were fixed, each with a regression test (`tests/test_review_fixes.py`); none touched real outcome data.

1. **H1, Q23 fallback not implemented.** When a year failed every Q23 step the pipeline stopped. Now the
   composition-adjusted direct series becomes the primary H1 series, as Q23 states (implementation notes, H1).
2. **H1, convergence checked on five parameters only.** The R-hat/ESS rule now covers every parameter in the
   posterior, as Q23 requires; before, an unconverged age × sex, race or education effect would have passed.
3. **H2 and the BMI imputation, income codes.** `_INCOMG1` (from 2021) splits the top bracket of `_INCOMG`
   ($50k+) into three. Codes 6 and 7 are merged into 5, so the income categories mean the same in every year; before,
   a change of meaning in 2021 fell inside the H2 post-period. Q12 updated.
4. **NC1, bootstrap.** Men and women were bootstrapped with independent PSU draws although they share PSUs, which
   misstates the SE of their average (the TOST of Q22 depends on it). Each replicate now resamples PSUs once for
   both.
5. **Missing BMI, predictive mean matching.** An operator-precedence slip drew among 6 donors, not the 5 of Q14,
   and did not take the nearest ones. Now one of the 5 observed cases with the nearest predicted values.
6. **H3 RIF variant (Q24), years without race.** The "not available" race dummy equalled the sum of the 2015 and
   2016 year dummies, so those years' adjusted quantiles were arbitrary (several kg/m² off in a test). Their race
   dummies are now set to the reference means: adjusted for the other covariates only, as in the primary H3.
7. **Self-report correction (Q24), fixed calibration.** The "2011-2020" calibration was computed on BRFSS 2011-2025,
   including the outcome years. It now uses 2011-2020 only and is applied to every year (section 7).
8. **H6, missing weights.** A person with neither LSAQWT nor LONGWT positive would have turned every estimate into
   NaN without an error. Such persons are dropped from the frame, and the fit refuses a missing weight.
9. **Unused loaders.** `data.load_brfss`, `load_acs_cells` and `load_adult_population` duplicated the loaders in
   `prepare.py` and had diverged from them; removed (the guarded loader is `prepare.brfss`).

Not changed: the H4 permutation test refits the event study for each of the 20,000 permutations (about 0.05 s
each; roughly 15 minutes for H4 and 2-3 hours with the Q24 variants). It is slow but correct, and a faster version
would be new code to verify; it stays as is.

## 9. OSF registration (25 November 2026)

Registered on OSF on 25 November 2026 at 16:56 UTC as a Secondary Data Preregistration, public from the start:
https://osf.io/xw7zg/, DOI 10.17605/OSF.IO/XW7ZG. OSF stopped creating projects on 16 November 2026, so the
registration was started without a project and the package was attached to the "Data collection procedures
documentation" field. No outcome microdata had been analysed before this date (Q18). The analysis code was
unlocked by writing the DOI to `docs/osf_registration.txt`.

**Archived package.** `osf_glp1_2026-11-25.zip`, SHA-256
`0d75fd0497cb98b2dbc45691d656d0efa8fd814db0a856340ccad257cdc997bf` (downloaded back from OSF and kept as
`resultados/osf_glp1_2026-11-25_registered.zip`). It is the package built after commit bfc155f. A later rebuild
(commit bfb6950) differs only in `1_documents/preregistro_osf_v2.md` (the references note in item 3 below) and
in `MANIFEST_sha256.csv`; it was not the one registered.

**Errata in the registered form.** Three clerical differences between the registered form and
`preregistro_osf_v2.md`, found by comparing the archived responses (OSF API) with the source text. None changes a
hypothesis, model, threshold or decision rule, so none is a deviation:

1. *Q3 (research questions).* The pasted text was cut after "ages 40–6": research question 4 should end "…which
   show a decline concentrated at ages 40–64, and with measured NHANES estimates? (descriptive)". The complete
   text is in `preregistro_osf_v2.md` inside the archived package, and the question corresponds to H0, which is
   descriptive.
2. *References note.* The registered reference list keeps an outdated note saying that the methods references
   without a link were cited from memory. They had already been checked against Crossref (`citation_check.md`,
   item C2, also in the archived package).
3. *Escaped symbols.* OSF stores "<" and ">" as "&lt;" and "&gt;" in Q19 and Q22 (for example
   "P(D_2025 &lt; D_2023)"); the page displays them correctly.

**Not done before registration.** The simulated precision analysis planned on 18 November 2026 was not run; Q21
gives analytic power only. If it is run, it is reported in the preprint as a check made after registration.
