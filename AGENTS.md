# AGENTS.md

## Rules

- `initial_docs/` and `projeto_glp1.zip` are **immutable**. Never edit, rename, move, reformat or delete
  anything in them. `initial_docs/` is the zip extracted with its original structure (read it there);
  copy or derive files from it into `docs/`, `piloto/`, `scripts/` etc. Files in `docs/`, `piloto/` and
  `scripts/brfss_microdata.py` / `scripts/meps_microdata.py` are byte-identical copies (map in
  `docs/README.md`). Keep those two scripts unformatted (they are cited in the pre-registration).
- Pre-registration rule: until the OSF registration, microdata may only be used to reproduce published
  numbers and to count cases. No BMI by diabetes, by quantile, by GLP-1 use, nor height trends.
- `piloto/` is the record of the 2026-11-12 pilot. Do not change its code or data; `tests/test_pilot.py`
  checks that it still reproduces `piloto/saidas/`.

## Commands

- Setup: `uv sync` (creates `.venv`); with models: `uv sync --extra analysis`
- Tests: `uv run pytest` (fast); end-to-end pipeline on simulated data: `uv run pytest -m slow` (~10 min)
- Lint: `uv run ruff check .` / `uv run ruff format .`
- Pilot: `uv run python scripts/run_pilot.py` (writes to `resultados/piloto/`)

## Language

**The study is published in English** (arXiv stat.AP, with a Portuguese summary for outreach; decided in
`docs/plano_de_estudo.md`, "Decisões tomadas"). Everything that goes to the OSF package, the preprint or the
public repository is written in English: pre-registration answers, decision log, implementation notes,
hypothesis write-ups, figures, data and provenance tables, `scripts/README.md`, code and comments. The original
study documents copied from `initial_docs/` (plan, literature review, work-package and pilot LEIAME) stay in
Portuguese. Conversation with the author is in Portuguese.
