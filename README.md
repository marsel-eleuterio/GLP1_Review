# GLP1_Review

**Is the break in the US adult obesity trend a GLP-1 effect?**

A pre-registered, secondary-data study. US adult obesity stopped rising after 2022 while GLP-1 use
(semaglutide, tirzepatide) multiplied. That the curve bent is already published; nobody had tested whether the
change carries the *signature* of the drugs. This project tests predictions that should hold together if GLP-1
drugs explain the break, and come apart if it has another cause, such as a measurement artefact.

| # | Hypothesis | Prediction | Role |
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

Data: BRFSS 2011–2025 (6.0 million interviews), MEPS 2018–2024 and its longitudinal panels 23–24, state GLP-1 use
from CMS Medicare Part D, Medicaid SDUD and The RX Index, ACS and Census population, NHANES and Gallup published
estimates.

## Status (27 November 2026)

- **Pre-registered** on OSF on 25 November 2026,
  [doi:10.17605/OSF.IO/XW7ZG](https://doi.org/10.17605/OSF.IO/XW7ZG), before any outcome microdata were analysed.
- **Analysed:** the full pre-registered run finished on 26 November 2026 (`docs/analysis_run_log.md`).
- **Preprint** drafted in `paper/` (arXiv stat.AP), with figures and tables from the full run.

Results under the registered decision rules:

- **H1:** the break is present. In 2025 obesity was 1.37 percentage points below its 2011–2019 trajectory (95%
  predictive interval −2.23 to −0.54), about 3.7 million adults.
- **H5:** the size is compatible with what GLP-1 use could produce (simulated −1.15 pp).
- **NC1 and NC2:** both negative controls pass.
- **H2, H3 and H6:** all three signatures have the predicted sign but are inconclusive; the overall verdict is
  **mixed**.
- **H4:** the state gradient is not supportive once the registered allowance for pre-trends is applied.

Changes after registration are listed in [docs/decision_log.md](docs/decision_log.md) (sections 9–11).

## Repository layout

```
GLP1_Review/
├── projeto_glp1.zip   Original work package (2026-11-14), frozen
├── initial_docs/      The package extracted, frozen: read-only reference for the copies below
├── docs/              Study plan, OSF pre-registration, decision and run logs, literature review
├── piloto/            Pilot of 2026-11-12: code, aggregated input data (dados/) and original outputs (saidas/)
├── dados_externos/    Published estimates (Gallup, NHANES) and source design table, each number sourced
├── paper/             Preprint (English, pandoc Markdown), figures and references
├── scripts/           Download, extraction, analysis, figure and OSF-package scripts
├── src/glp1_review/   Analysis package: one module per hypothesis, trend and survey helpers, figures
├── tests/             Pytest suite (pilot reproducibility, every model on simulated data, figures)
├── dados_brutos/      Raw microdata downloads            (git-ignored, except manifests and provenance)
├── dados_limpos/      Extracted study columns            (git-ignored)
└── resultados/        Generated outputs                  (git-ignored)
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) (it installs the right Python automatically).

```powershell
uv sync                     # creates .venv with Python 3.12 + numpy, pandas, requests, dev tools
uv sync --extra analysis    # adds PyMC, ArviZ, nutpie, statsmodels, matplotlib (models and figures)
uv run pre-commit install   # optional: lint hooks on commit
```

Without uv: `python -m venv .venv`, activate it (`.venv\Scripts\activate` on Windows), then
`pip install -e .` (or `pip install -e ".[analysis]"`).

## Usage

```powershell
uv run pytest                           # fast tests, including the pilot reproducing piloto/saidas/
uv run pytest -m slow                   # end-to-end pipeline on simulated data (about 10 minutes)
uv run python scripts/run_pilot.py      # re-runs the pilot into resultados/piloto/
uv run python scripts/run_analysis.py   # all pre-registered analyses (about 13 hours; --quick for a smoke test)
uv run python scripts/make_figures.py   # preprint figures from the full run into paper/figures/
```

The data workflow (downloads, extraction and validation against published numbers) is described in
[scripts/README.md](scripts/README.md); building the preprint PDF in [paper/README.md](paper/README.md).

## Pre-registration rule

Until the OSF registration, microdata were used only to **reproduce already-published numbers and count cases**:
no BMI by diabetes, by quantile or by GLP-1 use, and no height trends. The sequence was: run the data scripts →
complete the draft → register (25 November 2026) → analyse.

## Documents

Study documents written after the work package are in English; the original plan, literature review and
work-package README are in Portuguese.

- [Study plan](docs/plano_de_estudo.md) ([PDF](docs/plano_de_estudo.pdf))
- [OSF pre-registration, version 2 (registered)](docs/preregistro_osf_v2.md); first draft:
  [version 1](docs/preregistro_osf_rascunho.md) ([PDF](docs/preregistro_osf_rascunho.pdf))
- [Decision log](docs/decision_log.md), [implementation notes](docs/implementation_notes.md),
  [analysis run log](docs/analysis_run_log.md), [citation check](docs/citation_check.md)
- [Preprint](paper/manuscript.md)
- [Literature review](docs/revisao_da_literatura.md) ([PDF](docs/revisao_da_literatura.pdf))
- [Pilot notes](piloto/LEIAME.md)

## Data sources

CDC BRFSS (microdata and open API `hn4x-zwk7`), AHRQ MEPS, CMS Medicare Part D and Medicaid State Drug
Utilization Data, U.S. Census Bureau population estimates and ACS PUMS, NCHS NHANES, The RX Index / PurpleLab
(state-level GLP-1 use), KFF and Gallup polls. Third-party data keep their original terms; see below.

## Citation and license

© 2026 Marsel Eleutério.

- **Code** (`*.py`, configuration, tests): [MIT](LICENSE).
- **Study documents** (`docs/`, `paper/`, `piloto/LEIAME.md`: study plan, pre-registration, literature review,
  preprint text and figures): [CC BY 4.0](LICENSE-docs). You may share and adapt them with attribution.
- **Third-party data** (`piloto/dados/`, downloaded microdata): original terms of each source, listed in
  [LICENSE](LICENSE).

Citation metadata in [CITATION.cff](CITATION.cff).
