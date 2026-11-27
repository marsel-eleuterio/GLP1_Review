# paper/

Preprint (English; arXiv stat.AP). The skeleton was written on 14 November 2026, before the OSF registration, with
placeholders for every result; they were filled on 26 November 2026 from the full run (`full_20261125`) and the
declared sensitivity (`sens_mrp_nogate_20261126`).

| File | Content |
| --- | --- |
| `manuscript.md` | Text with pandoc citations (`[@key]`); no placeholders remain |
| `references.bib` | References; entries marked `verify` must be checked against the original articles |
| `figures/` | Figures 1–6, drawn by `scripts/make_figures.py` (module `glp1_review.figures`) from the full run |
| `typst-header.typ` | Table layout for the PDF built with Typst |

## Where the numbers come from

Each number in the manuscript was filled from the pipeline outputs in `resultados/analysis/<run>/`
(`scripts/run_analysis.py`), through these placeholders:

| Placeholder | Source file | Key or row |
| --- | --- | --- |
| `{{OSF.DOI}}`, `{{OSF.DATE}}` | `docs/osf_registration.txt` | registration DOI and date |
| `{{REPO.URL}}` | — | public repository URL at submission |
| `{{DEVIATIONS.AFTER_REGISTRATION}}` | `docs/decision_log.md` sections 9-11 | filled 26 November 2026 |
| `{{SENS.MRP}}` | `resultados/analysis/sens_mrp_nogate_20261126/h1.json` | post-registration sensitivity (decision_log 11) |
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
| `{{Q24.EXTERNAL}}` | `q24.csv` | rows "external: observed change 2022-2025 (MRP)" and "external: observed minus projected change, Ward …" and "…, DeCleene …" |
| `{{Q24.SELFREPORT}}` | `q24.csv` | rows "self-report correction (NHANES-calibrated, …), direct series": D2025 with the corrected 2022 and 2025 levels, both variants |
| `{{*.TEXT}}`, `{{RESULTS.ABSTRACT}}`, `{{CONCLUSIONS.ABSTRACT}}`, `{{DISCUSSION}}` | — | prose written after the results |

## Converting

PDF for review, with pandoc 3.14 and Typst 0.15 (Windows: `winget install JohnMacFarlane.Pandoc Typst.Typst`),
from the `paper/` folder:

    pandoc manuscript.md --citeproc --bibliography references.bib --pdf-engine=typst --columns=1000 \
      --include-in-header=typst-header.typ -V papersize=a4 -V margin.x=2.2cm -V margin.y=2.4cm \
      -V fontsize=10.5pt -o manuscript.pdf

`--columns=1000` lets the table columns take their natural widths; `typst-header.typ` keeps short tables whole, floating
to the top or bottom of a page, and lets the long Q24 table break across pages. `manuscript.pdf` is not committed. For the arXiv LaTeX source:

    pandoc manuscript.md --citeproc --bibliography references.bib -s -o manuscript.tex
