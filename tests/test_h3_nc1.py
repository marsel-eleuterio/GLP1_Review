"""H3 (quantile contrast) and NC1 (height) on simulated data with known answers."""

import numpy as np
import pandas as pd
import pytest

from glp1_review import h3_quantiles as h3

YEARS = np.arange(2011, 2026)
AGES = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]


def simulate(rng, tail_shift=0.0, old_jump=0.0, n=4000, trend_bmi=0.12):
    """BMI rises linearly; from 2023 the top 20% lose `tail_shift` kg/m2 (the median does not move);
    from 2023 the share of 55+ jumps by `old_jump` (composition change, no change within cells)."""
    rows = []
    for y in YEARS:
        p_old = 0.30 + (old_jump if y >= 2023 else 0.0)
        old = rng.random(n) < p_old
        age = np.where(old, rng.choice(AGES[4:], n), rng.choice(AGES[:4], n))
        sex = rng.choice(["M", "F"], n)
        bmi = np.exp(rng.normal(np.log(27.0), 0.2, n)) + 2.5 * old + trend_bmi * (y - 2011)
        if y >= 2023 and tail_shift:
            cut = np.quantile(bmi, 0.80)
            bmi = np.where(bmi > cut, np.maximum(bmi - tail_shift, cut), bmi)
        height = np.where(sex == "M", 1.76, 1.62) - 0.02 * old + rng.normal(0, 0.07, n)
        rows.append(
            pd.DataFrame(
                {
                    "year": y,
                    "bmi": bmi,
                    "htm": height,
                    "wt": rng.uniform(50, 300, n),
                    "strat": rng.integers(0, 20, n),
                    "psu": rng.integers(0, 6, n),
                    "age_group": age,
                    "sex": sex,
                    "race": rng.choice(["W", "B", "H"], n),
                    "educ": rng.integers(1, 5, n),
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def test_dfl_factor_reproduces_reference_composition():
    rng = np.random.default_rng(40)
    df = simulate(rng, old_jump=0.25)
    d = h3._prepare(df, "bmi")
    old = d["age_group"].isin(["55-64", "65+"])
    ref_share = d.loc[d.year.isin(h3.REF_YEARS)].pipe(lambda x: np.average(old[x.index], weights=x.wt))
    for y in (2011, 2024):
        g = d[d.year == y]
        assert np.average(old[g.index], weights=g.w_dfl) == pytest.approx(ref_share, abs=1e-9)


def test_h3_recovers_tail_contrast():
    rng = np.random.default_rng(41)
    est, det = h3.fit_h3(simulate(rng, tail_shift=1.5), n_rep=30)
    assert est.est < -0.8  # P90 falls, median does not
    assert abs(det["departures"][0.5].mean()) < 0.3
    assert est.se > 0


def test_h3_composition_jump_is_neutralized():
    rng = np.random.default_rng(42)
    est, det = h3.fit_h3(simulate(rng, tail_shift=0.0, old_jump=0.25), n_rep=30)
    assert abs(est.est) < 3 * est.se + 0.15
    # without reweighting the jump in older adults would move the upper quantiles
    d = h3._prepare(simulate(np.random.default_rng(42), old_jump=0.25), "bmi")
    raw = h3._series(d, "bmi", "quantile", [0.9], "wt", sorted(d.year.unique()))[0]
    adj = h3._series(d, "bmi", "quantile", [0.9], "w_dfl", sorted(d.year.unique()))[0]
    assert raw[-1] - raw[-4] > adj[-1] - adj[-4] + 0.3


def test_nc1_no_change_passes_equivalence():
    from glp1_review.decision import nc1_passes

    rng = np.random.default_rng(43)
    est, det = h3.fit_nc1(simulate(rng, old_jump=0.25, n=40000), n_rep=20)
    assert abs(est.est) < 0.5
    assert set(det["by_sex"]) == {"M", "F"}
    assert nc1_passes(est)
