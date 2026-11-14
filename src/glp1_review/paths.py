"""Canonical project paths. Import these instead of hard-coding directories."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DOCS = ROOT / "docs"
SCRIPTS = ROOT / "scripts"
PILOT = ROOT / "piloto"
PILOT_DATA = PILOT / "dados"
PILOT_OUTPUTS = PILOT / "saidas"

# Microdata (not versioned, see .gitignore)
RAW = ROOT / "dados_brutos"
CLEAN = ROOT / "dados_limpos"
RAW_BRFSS = RAW / "brfss"
RAW_MEPS = RAW / "meps"
CLEAN_BRFSS = CLEAN / "brfss"
CLEAN_MEPS = CLEAN / "meps"

RESULTS = ROOT / "resultados"
