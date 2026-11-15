"""H1 MRP on simulated cells from a known model, and the BRFSS harmonisation."""

import numpy as np
import pandas as pd
import pytest

from glp1_review import h1_mrp, trend
from glp1_review.data import AGE6, DIVISION, EDUC4, RACE5, SEX2, STATES, harmonise_brfss

SAMPLER = {"draws": 300, "tune": 400, "chains": 2}


def simulate_year(rng, n_per_cell=4, drop_state=6):
    grid = pd.MultiIndex.from_product(
        [STATES, AGE6, SEX2, RACE5, EDUC4], names=["state", "age_group", "sex", "race", "educ"]
    ).to_frame(index=False)
    z = pd.Series(rng.normal(0, 0.2, len(STATES)), index=STATES)
    a_state = 0.8 * z + rng.normal(0, 0.05, len(STATES))
    eff = {
        "age_group": dict(zip(AGE6, [-0.6, -0.1, 0.1, 0.3, 0.35, 0.1], strict=True)),
        "sex": {"Male": 0.0, "Female": 0.05},
        "race": dict(zip(RACE5, [0.0, 0.4, 0.3, -0.9, 0.1], strict=True)),
        "educ": dict(zip(EDUC4, [0.2, 0.15, 0.05, -0.3], strict=True)),
    }
    eta = -0.75 + grid["state"].map(a_state) + sum(grid[k].map(v) for k, v in eff.items())
    p = trend.expit(eta)
    pop = rng.uniform(1000, 30000, len(grid))
    n = rng.poisson(n_per_cell, len(grid))
    y = rng.binomial(n, p)
    cells = grid.assign(y=y, n=n)
    cells = cells[(cells["n"] > 0) & (cells["state"] != drop_state)]
    frame = grid.rename(columns={"state": "state_fips", "age_group": "age"}).assign(pop=pop)
    truth = float(np.sum(pop * p) / pop.sum())
    truth_missing_state = float(
        np.sum((pop * p)[grid.state == drop_state]) / pop[grid.state == drop_state].sum()
    )
    return cells, frame, z - z.mean(), truth, truth_missing_state


def test_mrp_recovers_national_prevalence_with_a_missing_state():
    rng = np.random.default_rng(60)
    cells, frame, z, truth, truth_ca = simulate_year(rng)
    idata, _ = h1_mrp.fit_year(cells, z, DIVISION, seed=1, sampler_kwargs=SAMPLER)
    P = h1_mrp.poststratify(idata, frame, use_race=True)
    lo, hi = np.percentile(P, [2.5, 97.5])
    assert lo - 0.005 <= truth <= hi + 0.005
    assert hi - lo < 0.03
    # the state without data (FIPS 6) is predicted from its division and z
    one = frame[frame.state_fips == 6]
    P_ca = h1_mrp.poststratify(idata, one, use_race=True)
    assert abs(np.median(P_ca) - truth_ca) < 0.05


def test_mrp_without_race_and_non_centred_runs():
    rng = np.random.default_rng(61)
    cells, frame, z, truth, _ = simulate_year(rng)
    cells_nr = cells.groupby(["state", "age_group", "sex", "educ"], as_index=False)[["y", "n"]].sum()
    idata, _ = h1_mrp.fit_year(
        cells_nr, z, DIVISION, seed=2, sampler_kwargs=SAMPLER, centred=False, agesex=False
    )
    P = h1_mrp.poststratify(idata, frame, use_race=False, agesex=False)
    assert abs(np.median(P) - truth) < 0.02


def test_national_departures_millions():
    rng = np.random.default_rng(62)
    years = list(range(2011, 2026))
    base = trend.expit(
        -0.9 + 0.025 * (np.array(years) - 2015) - 0.03 * np.clip(np.array(years) - 2022, 0, None)
    )
    P = {y: base[i] + rng.normal(0, 0.002, 500) for i, y in enumerate(years)}
    out = h1_mrp.national_departures(P, adults_millions={2023: 262.0, 2024: 265.0, 2025: 267.0})
    med25 = out["summary_pp"][2025][0]
    assert med25 < 0 and out["summary_millions"][2025][0] == pytest.approx(med25 / 100 * 267.0, rel=0.05)
    assert out["p_2025_below_2023"] > 0.5


def test_harmonise_brfss_codes():
    d = pd.DataFrame(
        {
            "age5": [1, 2, 3, 9, 10, 14],
            "sex": [1, 2, 7, 1, 2, 9],
            "race": [1, 5, 3, 4, 6, np.nan],
            "educ": [1, 2, 3, 4, 9, 1],
            "bmicat": [1, 2, 3, 4, np.nan, 4],
            "plan_raw": [1, 2, 9, 7, 1, 2],
        }
    )
    h = harmonise_brfss(d)
    assert h["age_group"].tolist()[:5] == ["18-24", "25-34", "25-34", "55-64", "65+"] and pd.isna(
        h["age_group"][5]
    )
    assert h["sex"].tolist()[:2] == ["Male", "Female"] and h["sex"][[2, 5]].isna().all()
    assert h["race"].tolist()[:5] == [
        "White",
        "Hispanic",
        "Asian",
        "Other or multiracial",
        "Other or multiracial",
    ]
    assert pd.isna(h["educ"][4]) and h["obese"].tolist()[:4] == [0, 0, 0, 1] and pd.isna(h["obese"][4])
    assert h["insured"].tolist()[:2] == [1.0, 0.0] and h["insured"][[2, 3]].isna().all()
