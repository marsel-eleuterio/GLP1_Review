# Analysis run log

Record of every run of the pre-registered analyses on the real data after the OSF registration
(doi:10.17605/OSF.IO/XW7ZG, 25 November 2026): what was run, what went wrong, how it was fixed and what the run
produced. Code changes are also recorded in `decision_log.md` (sections 10 onwards). Outputs are in
`resultados/analysis/<run>/` (not committed).

## Smoke tests (25 November 2026)

`scripts/run_analysis.py --quick` (few MCMC draws, replicates and permutations), commits e8b5b01 and fda46d8.

1. First attempt (`smoke_quick_20261125`): spent over an hour in the first H2 regression. Cause: two survey helpers
   looped over the ~36,000 BRFSS strata comparing every PSU label. Rewritten with identical results
   (decision_log section 10, commit e8b5b01); run stopped and restarted.
2. Second attempt (`smoke_quick_20261125b`): H1, H0, H2, H3, NC1, H4, H6 and H5 ran; Q24 stopped in the H2
   composition reweighting (missing age groups with pandas 3). Fixed in commit fda46d8 (decision_log section 10).
3. Retest of H1, H4 and Q24 (`smoke_quick_20261125c`): completed without errors. Q24 took 1 h 52 min.

Timing measured on the real data (`resultados/bench_reps.log`): an H3 fit costs about 9 minutes whatever the
number of replicates (about 0.6 s per replicate), NC1 about 5 minutes (about 1 s per replicate), one BMI
imputation 31 s, one H4 permutation 38 ms. Expected length of the full run: 9-10 hours, most of it Q24.

## Full run 1 (`full_20261125`)

- Started 25 November 2026, 23:50, commit fda46d8, default configuration (`Config()`), log
  `resultados/analysis_full.log`.
- Monitoring every 30 minutes overnight. If a run fails or stalls, the cause, the fix and the restart are
  recorded below.

### H1 convergence (26 November 2026, 06:15)

H1 took 6 h 25 min (68 MCMC fits). The MRP model passed the Q23 convergence rule (R-hat < 1.01, bulk ESS > 400
and no divergent transitions, on every parameter) only in 2021 (after 2,000 tuning steps) and 2024 (primary
model). In the other 13 years it failed all five Q23 steps, typically by small margins: maximum R-hat 1.008-1.026,
minimum bulk ESS 210-520 and 0-6 divergences. As Q23 prescribes, the composition-adjusted direct series became the
primary H1 series ("Q23 fallback; MRP failed in [2011-2020, 2022, 2023, 2025]", `h1.json`). This is the registered
procedure, not a run failure, so the run was not stopped or changed. The full per-step diagnostics are in
`h1.json` (`fit_log`).

### Completion (26 November 2026, 13:17)

The run finished with exit code 0 at 13:17 (13 h 27 min; Q24 alone 6 h 24 min), with no traceback, no stall and
no restart. All outputs are in `resultados/analysis/full_20261125/` (`summary.md`, `verdicts.json`, one file per
step, `q24.csv` with 60 rows; the two rows without estimates are the variants marked "not applicable" in the code).
Classifications under the registered rules (Q22): H2, H3 and H6 inconclusive, overall verdict "mixed"; H1 break
present (on the Q23 fallback series); H4 not supportive; H5 compatible; NC1, NC2 (H1) and NC2 (H2) pass.

## Sensitivity: MRP without the Q23 gate (`sens_mrp_nogate_20261126`)

Declared sensitivity of `decision_log.md` section 11. Started 26 November 2026 (H1 only, primary MRP model in every
year, same seeds and sampler as the registered run).
