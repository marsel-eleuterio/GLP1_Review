# GLP1_Review

**Is the break in the US adult obesity trend a GLP-1 effect?**

A pre-registered, secondary-data study. US adult obesity stopped rising after 2022 while GLP-1 use
(semaglutide, tirzepatide) multiplied. That the curve bent is already published; nobody has tested
whether the change carries the *signature* of the drugs. This project tests seven falsifiable
predictions that should appear together if GLP-1s explain the break, and come apart if it is a
measurement artefact.

| # | Hypothesis | Prediction that can fail | Data |
| --- | --- | --- | --- |
| H0 | Sources agree | The Gallup (decline) vs BRFSS (plateau) gap is explained by sample, mode and weighting | Gallup, BRFSS, NHANES |
| H1 | Trend break | After 2022 obesity falls below the 2011–2019 trajectory, and the gap grows each year | BRFSS 2011–2025 |
| H2 | Gradient by profile | Larger deviation where use is higher; primary contrast: diagnosed diabetes vs others | BRFSS microdata + KFF, Gallup, MEPS |
| H3 | BMI signature | The BMI 90th percentile departs from trend more than the median | BRFSS microdata |
| H4 | State dose-response | States with more use deviate more, net of baseline level and prior trend | BRFSS + state-level use (CMS, RX Index) |
| H5 | Mechanical plausibility | The observed deviation fits use × persistence × weight loss | Trials, real-world studies, MEPS |
| H6 | Individual loss | New GLP-1 users lose BMI relative to non-users, with no pre-trend | MEPS panels 23 and 24 |

Negative controls: self-reported height and the 2015–2019 period must not show the same pattern.

**Status (2026-11-14):** pilot done with aggregated data; literature review closed; OSF
pre-registration in draft. Next step: download the BRFSS and MEPS microdata and reproduce the CDC API
numbers, then register on OSF before any confirmatory analysis.

> Study documents are written in Portuguese; the OSF pre-registration answers are in English.

## Repository layout

```
GLP1_Review/
├── projeto_glp1.zip   Original work package (2026-11-14), frozen
├── initial_docs/      The package extracted, frozen: read-only reference for the copies below
├── docs/              Study plan, OSF pre-registration draft, literature review (.md + .pdf)
├── piloto/            Pilot of 2026-11-12: code, aggregated input data (dados/) and original outputs (saidas/)
├── dados_externos/    Published estimates (Gallup, NHANES) and source design table, each number sourced
├── scripts/           Data download/extraction scripts and runners
├── src/glp1_review/   Analysis package (shared paths, future models)
├── tests/             Pytest suite (pilot reproducibility)
├── dados_brutos/      Raw microdata downloads            (git-ignored, except sha256 manifests)
├── dados_limpos/      Extracted study columns            (git-ignored)
└── resultados/        Generated outputs                  (git-ignored)
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) (it installs the right Python automatically).

```powershell
uv sync                     # creates .venv with Python 3.12 + numpy, pandas, requests, dev tools
uv sync --extra analysis    # adds PyMC, ArviZ, statsmodels, matplotlib (modelling phase)
uv run pre-commit install   # optional: lint hooks on commit
```

Without uv: `python -m venv .venv`, activate it (`.venv\Scripts\activate` on Windows), then
`pip install -e .` (or `pip install -e ".[analysis]"`).

## Usage

```powershell
uv run pytest                           # checks the pilot still reproduces piloto/saidas/
uv run python scripts/run_pilot.py      # re-runs the pilot into resultados/piloto/
```

Microdata workflow (BRFSS ≈ 1 GB from cdc.gov, MEPS ≈ 110 MB from meps.ahrq.gov) is described in
[scripts/README.md](scripts/README.md) and [docs/pacote_de_trabalho.md](docs/pacote_de_trabalho.md).


## Pre-registration rule

Until the OSF registration, microdata may only be used to **reproduce already-published numbers and
count cases**. No BMI by diabetes, by quantile, by GLP-1 use, and no height trends. Sequence: run the
scripts → complete the draft → register → analyse.

## Documents

- [Study plan](docs/plano_de_estudo.md) ([PDF](docs/plano_de_estudo.pdf))
- [OSF pre-registration draft](docs/preregistro_osf_rascunho.md) ([PDF](docs/preregistro_osf_rascunho.pdf))
- [Literature review](docs/revisao_da_literatura.md) ([PDF](docs/revisao_da_literatura.pdf))
- [Pilot notes](piloto/LEIAME.md)

## Data sources

CDC BRFSS (microdata and open API `hn4x-zwk7`), AHRQ MEPS, CMS Medicare Part D and Medicaid State Drug
Utilization Data, U.S. Census Bureau population estimates, The RX Index / PurpleLab (state-level GLP-1
use), KFF and Gallup polls. Third-party data keep their original terms; see below.

## Citation and license

© 2026 Marsel Eleutério.

- **Code** (`*.py`, configuration, tests): [MIT](LICENSE).
- **Study documents** (`docs/`, `piloto/LEIAME.md`: study plan, pre-registration, literature review):
  [CC BY 4.0](LICENSE-docs). You may share and adapt them with attribution.
- **Third-party data** (`piloto/dados/`, downloaded microdata): original terms of each source, listed in
  [LICENSE](LICENSE).

Citation metadata in [CITATION.cff](CITATION.cff).
