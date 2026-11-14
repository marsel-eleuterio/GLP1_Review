"""The pilot must keep reproducing the outputs of the original 2026-11-12 run (piloto/saidas)."""

import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from glp1_review.paths import PILOT, PILOT_DATA, PILOT_OUTPUTS


@pytest.fixture(scope="module")
def pilot_run(tmp_path_factory) -> Path:
    work = tmp_path_factory.mktemp("pilot")
    for f in PILOT_DATA.glob("*.csv"):
        shutil.copy(f, work)
    for script, args in [("pilot_glp1_obesity.py", [work, work]), ("pilot_extra.py", [work])]:
        res = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", str(PILOT / script), *map(str, args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert res.returncode == 0, res.stderr
        (work / f"{Path(script).stem}.stdout.txt").write_text(res.stdout, encoding="utf-8")
    return work


def test_checksums_ok(pilot_run):
    out = (pilot_run / "pilot_glp1_obesity.stdout.txt").read_text(encoding="utf-8")
    assert "MISMATCH" not in out


@pytest.mark.parametrize(
    "name",
    [
        "pilot_national_series.csv",
        "pilot_age_table.csv",
        "pilot_state_table.csv",
        "pilot_regressions.csv",
    ],
)
def test_tables_match_original(pilot_run, name):
    new = pd.read_csv(pilot_run / name)
    ref = pd.read_csv(PILOT_OUTPUTS / name)
    pd.testing.assert_frame_equal(new, ref, check_exact=False, rtol=1e-6)


@pytest.mark.parametrize(
    ("stdout", "original"),
    [
        ("pilot_glp1_obesity.stdout.txt", "pilot_output.txt"),
        ("pilot_extra.stdout.txt", "pilot_extra_output.txt"),
    ],
)
def test_printed_output_matches_original(pilot_run, stdout, original):
    new = (pilot_run / stdout).read_text(encoding="utf-8").split()
    ref = (PILOT_OUTPUTS / original).read_text(encoding="utf-8").split()
    assert new == ref
