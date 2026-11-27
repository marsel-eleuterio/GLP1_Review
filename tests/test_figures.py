"""Preprint figures: the closed-form trajectory equals the registered trend procedure, and every figure renders
from synthetic inputs."""

import numpy as np
import pandas as pd
import pytest

from glp1_review import figures as F
from glp1_review import trend

YEARS = list(range(2011, 2026))


def _series(seed=1):
    rng = np.random.default_rng(seed)
    lg = -0.95 + 0.03 * (np.arange(15) - 4) + rng.normal(0, 0.01, 15)
    lg[-3:] -= [0.02, 0.03, 0.06]
    return pd.Series(1 / (1 + np.exp(-lg)), index=YEARS)


def test_trajectory_equals_registered_trend_procedure():
    s = _series()
    tr = F.trajectory(s)
    point = trend.departures(s.to_numpy(), YEARS, predictive=False).draws[0]
    assert np.allclose(tr.loc[[2023, 2024, 2025], "departure"], point, atol=1e-9)
    mc = trend.departures(np.tile(s.to_numpy(), (40_000, 1)), YEARS, rng=np.random.default_rng(2)).summary()
    for i, y in enumerate((2023, 2024, 2025)):
        assert tr.loc[y, "dlo"] == pytest.approx(mc[y][1], abs=0.03)
        assert tr.loc[y, "dhi"] == pytest.approx(mc[y][2], abs=0.03)
        assert np.isclose(tr.loc[y, "departure"], point[i])


def test_num_uses_unicode_minus_and_no_negative_zero():
    assert F.num(-1.37, 2) == "−1.37"
    assert F.num(-0.04, 1) == "0.0"
    assert F.num(0.9, 1, sign=True) == "+0.9"


def test_figures_render(tmp_path):
    rng = np.random.default_rng(3)
    nat = pd.DataFrame({"brfss_cdc": np.linspace(27.4, 33.5, 15), "gallup": np.nan}, index=YEARS)
    nat.loc[2022, "gallup"], nat.loc[2025, "gallup"] = 39.9, 37.0
    adj = pd.Series(np.linspace(27.4, 32.9, 15), index=YEARS)
    nh = pd.DataFrame(
        {
            "period": ["2013-2014", "2015-2016", "2017-2020", "2021-2023"],
            "value_pct": [37.7, 39.6, 41.9, 40.3],
            "se": [0.9, 1.6, 1.2, 1.9],
        }
    )
    ages = pd.DataFrame(
        {
            "brfss_change": [0.3, 0.5, 0.9],
            "brfss_change_se": [0.6, 0.65, 0.5],
            "gallup_change": [-2.2, -4.3, -5.0],
        },
        index=["age 30-39", "age 40-49", "age 50-64"],
    )
    paths = [F.fig_sources(nat, adj, nh, ages, tmp_path / "f1.png")]
    reg = pd.DataFrame(
        {
            "year": [2023, 2024, 2025],
            "median_pp": [-0.4, -0.6, -1.4],
            "lo95": [-1.2, -1.4, -2.2],
            "hi95": [0.4, 0.2, -0.5],
        }
    )
    nc1y = pd.DataFrame({"departure": rng.normal(0, 0.05, 15), "se": 0.06}, index=YEARS)
    paths.append(
        F.fig_h1(
            _series(),
            reg,
            {2017: (0.2, -1.0, 1.3)},
            nc1y,
            {"estimate": -0.1, "se": 0.06},
            tmp_path / "f2.png",
        )
    )
    sig = [
        {
            "key": k,
            "title": k,
            "sub": "sub",
            "est": e,
            "se": se,
            "dof": d,
            "ci90": [e - 1.7 * se, e + 1.7 * se],
            "p_holm": 0.13,
            "label": "inconclusive",
        }
        for k, e, se, d in (("H2", -0.16, 0.08, 6), ("H3", -0.06, 0.21, None), ("H6", -1.0, 0.63, None))
    ]
    paths.append(F.fig_signatures(sig, tmp_path / "f3.png"))
    betas = pd.DataFrame({"beta": rng.normal(0, 0.2, 15), "se": 0.2}, index=YEARS)
    states = pd.DataFrame(
        {"E": rng.normal(0, 1, 40), "departure": rng.normal(-1, 1, 40)},
        index=[f"S{i}" for i in range(38)] + ["WV", "KY"],
    )
    h4 = {
        "beta_star_rubin": -0.69,
        "beta_star_posterior_mean_E": -0.72,
        "rr_intervals": {"0.02": [-1.8, 0.4]},
    }
    paths.append(F.fig_h4(betas, states, h4, tmp_path / "f4.png"))
    paths.append(
        F.fig_h5(rng.normal(-1.15, 0.3, 5000), (-1.37, -2.23, -0.54), 0.05, 0.12, tmp_path / "f5.png")
    )
    panels = [
        {
            "title": "H1",
            "column": 0,
            "rows": [("primary", -1.4, -2.2, -0.5, "primary"), ("v", -1.0, np.nan, np.nan, "variant")],
        },
        {
            "title": "H2",
            "column": 1,
            "sesoi": 0.2,
            "rows": [("primary", -0.16, -0.35, 0.03, "primary"), ("post", -0.2, -0.4, 0.0, "post")],
        },
    ]
    paths.append(F.fig_q24(panels, tmp_path / "f6.png"))
    for p in paths:
        assert p.exists() and p.stat().st_size > 30_000
