"""H0 source reconciliation: published tables and the post-registration BRFSS-by-Gallup-groups code."""

import numpy as np
import pandas as pd
import pytest

from glp1_review import h0_sources as h0


def test_published_table_is_complete_and_sourced():
    p = h0.load_published()
    assert p["url"].str.startswith("https://").all()
    assert set(p["verified"]) <= {"yes", "no"}
    # every derived 2022 Gallup level equals the published 2025 level + published change
    lv = p[(p.source == "Gallup") & (p.measure == "obesity")].pivot_table(
        index="group", columns="period", values="value_pct"
    )
    for grp, chg in {"age 40-49": 4.3, "age 50-64": 5.0, "men": 2.3, "women": 3.5}.items():
        assert lv.loc[grp, "2022"] == pytest.approx(lv.loc[grp, "2025"] + chg)


def test_national_table_and_changes():
    t = h0.national_table()
    assert t.loc[2022, "gallup"] == 39.9 and t.loc[2025, "gallup"] == 37.0
    assert t.loc[2022, "brfss_cdc"] == 33.3 and t.loc[2025, "brfss_cdc"] == 33.5
    c = h0.change_2022_2025().set_index("source")["change_pp"]
    assert c["Gallup, published"] == pytest.approx(-2.9)
    assert c["BRFSS, composition-adjusted (pilot)"] == pytest.approx(-0.37)


def test_design_table_has_the_three_sources():
    d = h0.load_design()
    assert list(d.columns) == ["BRFSS", "Gallup", "NHANES"]
    assert "Mode" in d.index and "Measured" in d.loc["Height and weight", "NHANES"]


def test_brfss_by_gallup_groups_on_simulated_microdata():
    rng = np.random.default_rng(70)
    n = 40000
    rows = []
    for y in (2022, 2025):
        age5 = rng.integers(1, 14, n)
        p = np.where(np.isin(age5, [5, 6]), 0.45 - (0.04 if y == 2025 else 0), 0.33)
        rows.append(
            pd.DataFrame(
                {
                    "year": y,
                    "age5": age5,
                    "sex": rng.choice(["Male", "Female"], n),
                    "obese": (rng.random(n) < p).astype(float),
                    "wt": rng.uniform(50, 300, n),
                    "strat": rng.integers(0, 40, n),
                    "psu": rng.integers(0, 5, n),
                }
            )
        )
    g = h0.brfss_by_gallup_groups(pd.concat(rows, ignore_index=True))
    tab = h0.age_change_table(g)
    assert tab.loc["age 40-49", "brfss_change"] == pytest.approx(
        -4.0, abs=4 * tab.loc["age 40-49", "brfss_change_se"]
    )
    assert abs(tab.loc["age 18-29", "brfss_change"]) < 4 * tab.loc["age 18-29", "brfss_change_se"]
    assert tab.loc["age 40-49", "gallup_change"] == -4.3
    assert tab.loc["men", "gallup_change"] == pytest.approx(-2.3)
    assert np.isnan(tab.loc["age 65+", "gallup_change"])  # unverified +0.8 is excluded


def test_figure_renders(tmp_path):
    out = h0.plot_published_series(tmp_path / "h0.png")
    assert out.exists() and out.stat().st_size > 20_000
