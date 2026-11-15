"""H3 (quantile contrast) and NC1 (height) on simulated data with known answers."""

import numpy as np
import pandas as pd

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


def test_dfl_reproduces_reference_composition():
    rng = np.random.default_rng(40)
    df = simulate(rng, old_jump=0.25)
    df["old"] = df["age_group"].isin(["55-64", "65+"]).astype(float)
    P = h3.prepare(df, "old")
    share = P.series(P.dfl(P.w), "mean")[0]  # weighted share of 55+ per year after reweighting
    ref = df[df.year.isin(h3.REF_YEARS)]
    assert np.allclose(share, np.average(ref["old"], weights=ref["wt"]), atol=1e-9)


def test_dfl_years_without_race_use_reduced_cells():
    """2015-2016 have no race variable: those years are reweighted on age x sex x education, not zeroed."""
    rng = np.random.default_rng(44)
    df = simulate(rng, old_jump=0.25)
    df.loc[df.year.isin([2015, 2016]), "race"] = h3.NOT_AVAILABLE
    df["old"] = df["age_group"].isin(["55-64", "65+"]).astype(float)
    P = h3.prepare(df, "old")
    w = P.dfl(P.w)
    for y in (2015, 2016):
        a, b = P.bounds[y]
        assert w[a:b].sum() > 0
    share = P.series(w, "mean")[0]
    ref = df[df.year.isin(h3.REF_YEARS)]
    assert np.allclose(share, np.average(ref["old"], weights=ref["wt"]), atol=1e-9)


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
    P = h3.prepare(simulate(np.random.default_rng(42), old_jump=0.25), "bmi")
    raw = P.series(P.w, "quantile", [0.9])[0]
    adj = P.series(P.dfl(P.w), "quantile", [0.9])[0]
    assert raw[-1] - raw[-4] > adj[-1] - adj[-4] + 0.3


def test_nc1_no_change_passes_equivalence():
    from glp1_review.decision import nc1_passes

    rng = np.random.default_rng(43)
    est, det = h3.fit_nc1(simulate(rng, old_jump=0.25, n=40000), n_rep=20)
    assert abs(est.est) < 0.5
    assert set(det["by_sex"]) == {"M", "F"}
    assert nc1_passes(est)
