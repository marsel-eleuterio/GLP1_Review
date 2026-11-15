# paper/

Preprint skeleton (English; arXiv stat.AP), written on 14 November 2026 before the OSF registration.

| File | Content |
| --- | --- |
| `manuscript.md` | Text with pandoc citations (`[@key]`) and result placeholders (`{{...}}`) |
| `references.bib` | References; entries marked `verify` must be checked against the original articles |

Only the published-estimates part of H0 (Results, first subsection) contains numbers now. Everything that depends
on outcome microdata is a placeholder, filled after registration from the pipeline outputs in
`resultados/analysis/<run>/` (`scripts/run_analysis.py`).

## Placeholders

| Placeholder | Source file | Key or row |
| --- | --- | --- |
| `{{OSF.DOI}}`, `{{OSF.DATE}}` | `docs/osf_registration.txt` | registration DOI and date |
| `{{REPO.URL}}` | — | public repository URL at submission |
| `{{DEVIATIONS.AFTER_REGISTRATION}}` | — | any change made after registration, with reason (none so far) |
| `{{H0.AGE_COMPARISON}}` | `h0_age_changes.csv` | BRFSS change 2022-2025 by Gallup group vs Gallup |
| `{{H1.D2025}}`, `{{H1.D2025_CI}}` | `h1.json` | `D2025_pp` (median; 2.5 and 97.5 percentiles) |
| `{{H1.D2025_MILLIONS}}` | `h1.json` | `D_millions[2025]` |
| `{{H1.P_WIDENING}}` | `h1.json` | `p_D2025_below_D2023` |
| `{{H1.CLASS}}` | `verdicts.json` | `H1_break_present` |
| `{{H2.EST}}`, `{{H2.SE}}` | `h2.csv` | row "primary, two-stage" |
| `{{H2.P_HOLM}}`, `{{H2.CLASS}}` | `verdicts.json` | `family.H2.p_holm`, `family.H2.label` |
| `{{H3.EST}}`, `{{H3.SE}}` | `h3.json` | `estimate`, `se` |
| `{{H3.P_HOLM}}`, `{{H3.CLASS}}` | `verdicts.json` | `family.H3` |
| `{{H4.EST}}`, `{{H4.P_PERM}}`, `{{H4.RR002}}`, `{{H4.NO4}}` | `h4.json` | `beta_star_rubin`, `p_permutation_two_sided`, `rr_intervals["0.02"]`, `without_WV_KY_LA_OK` |
| `{{H4.CLASS}}` | `verdicts.json` | `H4_supportive` |
| `{{H6.EST}}`, `{{H6.SE}}`, `{{H6.LATE}}`, `{{H6.N_INITIATORS}}` | `h6.json` | `primary`, `placebo_late`, `initiators` |
| `{{H6.N_NEVER}}` | `h6_counts.csv` | never-users, both panels |
| `{{H6.P_HOLM}}`, `{{H6.CLASS}}` | `verdicts.json` | `family.H6` |
| `{{H5.MEDIAN}}`, `{{H5.RANGE}}`, `{{H5.CLASS}}` | `h5.json` | `simulated_effect_pp`, `classification` |
| `{{NC1.EST}}`, `{{NC1.CI90}}`, `{{NC1.CLASS}}` | `nc1.json` | `estimate`, `se` (90% CI = ±1.645 SE), `passes` |
| `{{NC2.TEXT}}` | `h1.json`, `h2.csv` | `nc2_departures_pp`, row "NC2 placebo (2017-2018)" |
| `{{VERDICT.OVERALL}}` | `verdicts.json` | `overall` |
| `{{Q24.TABLE}}` | `q24.csv` | full table |
| `{{Q24.EXTERNAL}}` | — | external counterfactuals and self-report correction, implemented after reading Ward et al. (2019) and DeCleene et al. (2026) |
| `{{*.TEXT}}`, `{{RESULTS.ABSTRACT}}`, `{{CONCLUSIONS.ABSTRACT}}`, `{{DISCUSSION}}` | — | prose written after the results |

## Converting

With pandoc (not installed in this environment):

    pandoc paper/manuscript.md --citeproc --bibliography paper/references.bib -o paper/manuscript.pdf
    pandoc paper/manuscript.md --citeproc --bibliography paper/references.bib -s -o paper/manuscript.tex
