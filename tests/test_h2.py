"""H2 triple difference on simulated BRFSS-like data with a known diabetes-specific break."""

import numpy as np
import pandas as pd
import pytest

from glp1_review import h2_tripdiff as h2

YEARS = np.arange(2011, 2026)


def simulate(
    rng, pi_post=-0.5, n_per_year=6000, n_states=15, theta=0.03, kappa=0.4, item=2019, gap_shock_sd=0.0
):
    rows = []
    sy_fe = rng.normal(0, 0.6, (n_states, len(YEARS)))
    gap_shock = rng.normal(0, gap_shock_sd, len(YEARS))  # year-level shocks to the diabetes gap
    for iy, y in enumerate(YEARS):
        n = n_per_year
        state = rng.integers(0, n_states, n)
        age = rng.choice(["18-24", "25-34", "35-44", "45-54", "55-64", "65+"], n)
        sex = rng.choice(["M", "F"], n)
        old = np.isin(age, ["55-64", "65+"])
        diab = (rng.random(n) < np.where(old, 0.2, 0.06)).astype(int)
        strat = rng.integers(0, 30, n)
        psu = rng.integers(0, 8, n)
        bmi = (
            27
            + sy_fe[state, iy]
            + 0.8 * old
            + 0.3 * (sex == "F")
            + diab * (3.0 + 0.5 * (sex == "F") + theta * (y - 2015) + kappa * (y >= item))
            + diab * pi_post * (y >= 2023)
            + diab * gap_shock[iy]
            + rng.normal(0, 5.5, n)
        )
        rows.append(
            pd.DataFrame(
                {
                    "year": y,
                    "state": state,
                    "age_group": age,
                    "sex": sex,
                    "race": rng.choice(["W", "B", "H", "A", "O"], n),
                    "educ": rng.integers(1, 5, n),
                    "income": rng.integers(1, 6, n),
                    "diabetes": diab,
                    "bmi": bmi,
                    "wt": rng.uniform(50, 500, n),
                    "strat": strat,
                    "psu": psu,
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def test_h2_recovers_post_break():
    rng = np.random.default_rng(20)
    df = simulate(rng, pi_post=-0.5)
    est, res = h2.fit(df)
    assert est.est == pytest.approx(-0.5, abs=3.5 * est.se)
    assert est.se < 0.45
    # pi for 2020-2022 should be ~0: no break before 2023
    for k in (2020, 2021, 2022):
        b, s = res.get(f"pi_{k}")
        assert abs(b) < 4 * s


def test_h2_no_break_coverage():
    rng = np.random.default_rng(21)
    hits, n_sim = 0, 40
    for _ in range(n_sim):
        est, _ = h2.fit(simulate(rng, pi_post=0.0, n_per_year=2500))
        hits += abs(est.est) <= 1.96 * est.se
    assert hits / n_sim >= 0.85


def test_h2_item_shift_absorbed():
    """A level shift at the item change in 2019 must not leak into pi_2023-2025."""
    rng = np.random.default_rng(22)
    est, res = h2.fit(simulate(rng, pi_post=0.0, kappa=1.5))
    assert abs(est.est) < 4 * est.se
    k, k_se = res.get("D_item")
    # kappa is identified from 2019 alone (2020+ have their own pi_k), so it is noisy: check within 3.5 SE
    assert abs(k - 1.5) < 3.5 * k_se


def test_nc2_spec_runs_and_drops_collinear_item_term():
    rng = np.random.default_rng(23)
    df = simulate(rng, pi_post=-0.5, n_per_year=3000)
    est, res = h2.fit(df, h2.NC2)
    assert "D_item" not in res.names
    assert abs(est.est) < 4 * est.se  # no break in 2017-2018
    assert h2.NC2.estimand_years == (2017, 2018) and max(h2.NC2.years) == 2018  # 2019 item change excluded
    est2, det = h2.fit_two_stage(df, h2.NC2)
    assert est2.dof == 3  # trend on 2011-2015, two parameters
    assert abs(est2.est) < est2.q(0.975) * est2.se


def test_two_stage_covers_under_year_shocks_where_single_stage_does_not():
    """With year-level shocks to the diabetes gap and large samples, the design-based SE of the single regression
    is far too small; the two-stage SE (Q21-consistent) keeps nominal coverage."""
    rng = np.random.default_rng(31)
    hits1 = hits2 = 0
    n_sim = 40
    for _ in range(n_sim):
        df = simulate(rng, pi_post=0.0, n_per_year=4000, gap_shock_sd=0.6, kappa=0.0)
        e1, _ = h2.fit(df)
        e2, _ = h2.fit_two_stage(df)
        hits1 += abs(e1.est) <= 1.96 * e1.se
        hits2 += abs(e2.est) <= e2.q(0.975) * e2.se
    assert hits2 / n_sim >= 0.85
    assert hits1 < hits2


def test_two_stage_recovers_break():
    rng = np.random.default_rng(32)
    est, det = h2.fit_two_stage(simulate(rng, pi_post=-1.0, n_per_year=8000, kappa=0.8))
    assert est.dof == 6
    assert abs(est.est + 1.0) < est.q(0.975) * est.se
