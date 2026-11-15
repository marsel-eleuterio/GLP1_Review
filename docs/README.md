# Study documents

| File | Content | Language |
| --- | --- | --- |
| [preregistro_osf_v2](preregistro_osf_v2.md) | **Working version of the OSF pre-registration** (25 answers of the Secondary Data Preregistration template), with the script results filled in and the decisions of 14 November 2026 applied | English |
| [decision_log](decision_log.md) | Every change from the first draft, with its reason (effect sizes, inference rules, H1 model, H2 inference, NC2 window, H4 inference) | English |
| [implementation_notes](implementation_notes.md) | Steps the pre-registration does not fully specify and the choice the analysis code makes | English |
| [h0_sources](h0_sources.md) | H0 source reconciliation, published-estimates part, with [figures/h0_published_series.png](figures/h0_published_series.png) | English |
| [preregistro_osf_rascunho](preregistro_osf_rascunho.md) (.md and .pdf) | First pre-registration draft (13-14 November 2026), kept unchanged | English answers, Portuguese notes |
| [plano_de_estudo](plano_de_estudo.md) (.md and .pdf) | Study plan, with the literature-review adjustments | Portuguese (original) |
| [revisao_da_literatura](revisao_da_literatura.md) (.md and .pdf) | Literature review, closed on 14 November 2026 | Portuguese (original) |
| [pacote_de_trabalho](pacote_de_trabalho.md) | README of the original work package: work order, checks and OSF steps | Portuguese (original) |

The study is published in English (arXiv stat.AP, with a Portuguese summary for outreach). The plan, the literature
review and the work-package README are the original Portuguese documents and are kept as they were. In the .md
versions the two charts of the plan appear only as captions; they are in the PDF.

The original documents also exist online, where earlier edits were made:
plan https://claude.ai/artifact/FR5vRnExpkyoARUPSPtre8,
pre-registration draft https://claude.ai/artifact/CNLPEMmVjupDYkQfUGnb6p,
literature review https://claude.ai/artifact/KjoyDLWaMUG6ZkTsDUeTuX.

License: the documents in this folder are under [CC BY 4.0](../LICENSE-docs) (free use and adaptation, with
attribution to Marsel Eleutério). The code is under MIT ([LICENSE](../LICENSE)).

`pacote_de_trabalho.md` describes the original package. Its paths (`scripts\`, `piloto\`, `dados_brutos\`,
`dados_limpos\`) hold in this repository; its `python ...` commands become `uv run python ...` (see the root
README and `scripts/README.md`).

## Provenance of each file

`initial_docs/` is the content of `projeto_glp1.zip` (work package of 14 November 2026), extracted with its original
structure. Both are immutable. The project files below are byte-identical copies:

| In `initial_docs/` | In the project |
| --- | --- |
| `LEIAME.md` | `docs/pacote_de_trabalho.md` |
| `docs/*` | `docs/*` (same names) |
| `piloto/**` | `piloto/**` (same names) |
| `scripts/brfss_microdata.py`, `scripts/meps_microdata.py` | `scripts/` (same names; `brfss_microdata.py` later changed, see `scripts/README.md`) |

History: the first version of `initial_docs/` (morning of 14 November 2026) was a flattened copy of the package,
with file names and contents mismatched and 5 files missing. It was replaced by the extraction of the zip the same
day.
