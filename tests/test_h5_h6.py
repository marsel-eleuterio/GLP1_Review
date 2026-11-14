"""H5 and H6 on simulated data with known answers."""

import numpy as np
import pandas as pd
import pytest

from glp1_review import h5_microsim as h5
from glp1_review import h6_panel as h6


# ------------------------------------------------------------------------------------------- H6
def simulate_panels(rng, beta=-1.2, beta_late=0.0, n_never=5200, n_init=90, n_late=26, n_psu=120):
    n = n_never + n_init + n_late
    group = np.array(["never"] * n_never + ["initiator"] * n_init + ["late"] * n_late)
    panel = np.where(rng.random(n) < 0.6, 23, 24)
    panel[group == "late"] = 23
    bmi0 = rng.normal(29, 6, n).clip(15, 60)
    bmi0[group != "never"] += 6  # users start heavier
    psu = rng.integers(0, n_psu, n)
    psu_effect = rng.normal(0, 0.4, n_psu)
    age = rng.choice(["18-44", "45-64", "65+"], n)
    sex = rng.choice(["M", "F"], n)
    dbmi = (
        0.2
        - 0.05 * (bmi0 - 30)
        + beta * (group == "initiator")
        + beta_late * (group == "late")
        + 0.3 * (age == "65+")
        + psu_effect[psu]
        + rng.normal(0, 2.3, n)
    )
    return pd.DataFrame(
        {
            "panel": panel,
            "group": group,
            "bmi_t0": bmi0,
            "dbmi": dbmi,
            "age_group": age,
            "sex": sex,
            "race": rng.choice(["A", "B", "C"], n),
            "diabetes0": rng.integers(0, 2, n),
            "insured0": rng.integers(0, 2, n),
            "lsaqwt": rng.uniform(1000, 9000, n),
            "longwt": rng.uniform(1000, 9000, n),
            "varstr": rng.integers(1, 60, n),
            "varpsu": psu,
        }
    )


def test_h6_recovers_effect_with_large_sample():
    rng = np.random.default_rng(10)
    df = simulate_panels(rng, beta=-1.2, n_init=2000)
    est, fit = h6.fit_primary(df)
    assert est.est == pytest.approx(-1.2, abs=0.2)
    assert 0.03 < est.se < 0.2


def test_h6_interval_coverage():
    rng = np.random.default_rng(11)
    hits, n_sim = 0, 150
    for _ in range(n_sim):
        est, _ = h6.fit_primary(simulate_panels(rng, beta=-1.0))
        hits += abs(est.est + 1.0) <= 1.96 * est.se
    assert 0.88 <= hits / n_sim <= 0.99


def test_h6_placebo_and_nyt():
    rng = np.random.default_rng(12)
    df = simulate_panels(rng, beta=-1.0, beta_late=0.0, n_late=400, n_init=400)
    late, _ = h6.fit_placebo_late(df)
    nyt, _ = h6.fit_not_yet_treated(df)
    assert abs(late.est) < 3 * late.se
    assert nyt.est == pytest.approx(-1.0, abs=4 * nyt.se)


def test_h6_lsaqwt_falls_back_to_longwt():
    rng = np.random.default_rng(13)
    df = simulate_panels(rng)
    df.loc[df.panel == 23, "lsaqwt"] = np.nan
    est, _ = h6.fit_primary(df)
    assert np.isfinite(est.est) and np.isfinite(est.se)


def test_h6_groups():
    g = pd.DataFrame(
        {
            "glp1_2018": [0, 1, 0, 0, 0, np.nan],
            "glp1_2019": [0, 0, 1, 0, 0, 0],
            "glp1_2020": [0, 0, 0, 0, 0, 0],
            "glp1_2021": [0, 1, 1, 1, 0, 0],
        }
    )
    out = h6.classify_groups(g, [2018, 2019, 2020, 2021], 2018, 2020).tolist()
    assert out[:5] == ["never", "prevalent", "initiator", "late", "never"]
    assert pd.isna(out[5])  # a year with unknown status -> excluded from H6


# ------------------------------------------------------------------------------------------- H5
def _use(p_by_class):
    idx = pd.MultiIndex.from_tuples([(c, d) for c in range(1, 5) for d in (0, 1)], names=["cls", "diab"])
    return pd.DataFrame({"p": [p_by_class.get(c, 0.0) for c, d in idx]}, index=idx)


def test_h5_hand_computed_effect():
    """All adults have BMI 28 (class 1), half use, everyone persists and loses 10%: counterfactual BMI 31.1,
    so obesity would be 50 pp higher without the drugs -> effect -50 pp."""
    n = 1000
    bmi, diab, w = np.full(n, 28.0), np.zeros(n, int), np.ones(n)
    p = h5.Params(
        meps_rate=0.5,
        published_rate=0.5,
        n_draws=50,
        fixed={"persistence_no_diab": 1.0, "loss_persistent": 0.10, "national_rate": 0.5},
    )
    eff = h5.simulate(bmi, diab, w, _use({1: 0.5}), p)
    assert np.allclose(eff, -50.0)


def test_h5_no_effect_far_above_threshold():
    n = 500
    bmi = np.full(n, 45.0)
    p = h5.Params(meps_rate=0.1, published_rate=0.2, n_draws=100)
    eff = h5.simulate(bmi, np.zeros(n, int), np.ones(n), _use({4: 0.2}), p)
    assert np.allclose(eff, 0.0)


def test_h5_realistic_range_and_h6_version():
    rng = np.random.default_rng(14)
    n = 20000
    bmi = rng.lognormal(np.log(28.5), 0.21, n)
    diab = (rng.random(n) < 0.12).astype(int)
    w = rng.uniform(0.5, 2, n)
    use = _use({1: 0.04, 2: 0.08, 3: 0.12, 4: 0.16})
    p = h5.Params(meps_rate=0.05, published_rate=0.12, n_draws=500)
    eff = h5.simulate(bmi, diab, w, use, p)
    assert np.all(eff <= 0) and -6 < np.median(eff) < -0.3
    eff6 = h5.simulate_h6(bmi, diab, w, use, p, beta_h6=-1.0)
    assert np.all(eff6 <= 0) and np.median(eff6) > np.median(eff)  # smaller loss -> smaller effect
