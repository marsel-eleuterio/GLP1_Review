"""End-to-end run of the pre-registered pipeline on a simulated data tree (quick configuration).
Marked slow (about 10 minutes): run with `uv run pytest -m slow`."""

import json

import pytest
from fake_tree import build

from glp1_review import guard, prepare, run
from glp1_review.paths import PILOT_DATA

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    root = tmp_path_factory.mktemp("data")
    paths = build(root)
    return prepare.Sources(clean=paths["clean"], raw=paths["raw"], pilot_data=PILOT_DATA)


def test_guard_blocks_the_pipeline(tree, tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "REGISTRATION_FILE", tmp_path / "missing.txt")
    with pytest.raises(guard.NotRegisteredError):
        run.run(tmp_path / "out", run.Config.quick(), steps=("h2",), src=tree)


def test_full_pipeline_quick(tree, tmp_path, monkeypatch):
    reg = tmp_path / "osf_registration.txt"
    reg.write_text("https://doi.org/10.17605/OSF.IO/TEST")
    monkeypatch.setattr(guard, "REGISTRATION_FILE", reg)
    out = tmp_path / "out"
    res = run.run(out, run.Config.quick(), src=tree)
    v = res["verdicts"]
    for f in (
        "h1_departures.csv",
        "h1.json",
        "h0_age_changes.csv",
        "h2.csv",
        "h3.json",
        "nc1.json",
        "h4.json",
        "h6.json",
        "h5.json",
        "verdicts.json",
        "summary.md",
        "q24.csv",
    ):
        assert (out / f).exists(), f
    assert set(v["family"]) == {"H2", "H3", "H6"}
    assert "overall" in v and v["overall"] in ("GLP-1 signature present", "absent", "mixed")
    # planted effects: diabetes-specific BMI loss from 2023 (H2) and initiator BMI loss (H6)
    assert res["results"]["H2"]["primary"].est < 0
    assert res["results"]["H6"]["primary"].est < -0.5
    h4 = json.loads((out / "h4.json").read_text())
    assert len(h4["rr_intervals"]) == 3
    assert (out / "summary.md").read_text().startswith("# Pre-registered analyses")


def test_q24_table_covers_every_hypothesis(tree, tmp_path, monkeypatch):
    import pandas as pd

    reg = tmp_path / "osf_registration.txt"
    reg.write_text("TEST")
    monkeypatch.setattr(guard, "REGISTRATION_FILE", reg)
    out = tmp_path / "out"
    run.run(out, run.Config.quick(), steps=("h1", "h4", "q24"), src=tree)
    q = pd.read_csv(out / "q24.csv")
    assert {"H1", "H2", "H3", "NC1", "H4", "H5", "H6"} <= set(q["hypothesis"])
    assert q["variant"].str.contains("multiple imputation").sum() == 3
    assert q["variant"].str.contains("interview mode").sum() == 6
    assert q["variant"].str.contains("external: observed minus projected").sum() == 1
