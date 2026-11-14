# CLAUDE.md

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
- Tests: `uv run pytest`
- Lint: `uv run ruff check .` / `uv run ruff format .`
- Pilot: `uv run python scripts/run_pilot.py` (writes to `resultados/piloto/`)

## Language

Study documents are in Portuguese; the OSF pre-registration answers are in English. Code and comments in
English.
