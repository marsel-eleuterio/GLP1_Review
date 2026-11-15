"""Unit tests of the Q24 building blocks on simulated data."""

import numpy as np
import pandas as pd
import pytest
from test_h2 import simulate as simulate_brfss
from test_h3_nc1 import simulate as simulate_h3
from test_h4 import simulate as simulate_states

from glp1_review import h2_tripdiff as h2
from glp1_review import h3_quantiles as h3
from glp1_review import h4_states as h4
from glp1_review import mi


def test_wild_cluster_bootstrap_close_to_cluster_robust_se():
    rng = np.random.default_rng(80)
    df = simulate_brfss(rng, pi_post=0.0, n_per_year=3000, n_states=30)
    e_wcb, info = h2.wild_cluster_bootstrap(df, n_boot=999)
    e_single, _ = h2.fit(df)
    assert e_wcb.est == pytest.approx(e_single.est)
    assert info["clusters"] == 30
    assert 0.3 * e_single.se < e_wcb.se < 3 * e_single.se


def test_reweight_group_composition_matches_reference():
    rng = np.random.default_rng(81)
    df = simulate_brfss(rng, n_per_year=2000)
    out = h2.reweight_group_composition(df)
    D = out["diabetes"] == 1
    old = out["age_group"].isin(["55-64", "65+"])
    ref = out[D & out.year.isin([2017, 2018, 2019])]
    ref_share = np.average(old[ref.index], weights=ref["wt"])
    for y in (2011, 2025):
        g = out[D & (out.year == y)]
        assert np.average(old[g.index], weights=g["wt"]) == pytest.approx(ref_share, abs=1e-9)
    assert (out.loc[~D, "wt"] == df.loc[~D, "wt"]).all()


def test_rm_interval_widens_with_mbar():
    rng = np.random.default_rng(82)
    Y, E = simulate_states(rng, slope_post=-0.5)
    es = h4.event_study(Y, E)
    lo0, hi0 = h4.rm_interval(es, 0.0)
    lo1, hi1 = h4.rm_interval(es, 1.0)
    assert lo1 < lo0 and hi1 > hi0
    assert (hi0 - lo0) == pytest.approx(2 * 1.96 * es.se_star)


def test_event_study_weights_of_one_equal_unweighted():
    rng = np.random.default_rng(83)
    Y, E = simulate_states(rng)
    assert h4.event_study(Y.assign(w=1.0), E).beta_star == pytest.approx(h4.event_study(Y, E).beta_star)


def test_imputation_fills_missing_bmi_and_rubin():
    rng = np.random.default_rng(84)
    n = 3000
    df = pd.DataFrame(
        {
            "year": 2020,
            "age_group": rng.choice(["18-24", "45-54", "65+"], n),
            "sex": rng.choice(["Male", "Female"], n),
            "race": rng.choice(["White", "Black"], n),
            "educ": rng.choice(["HS or GED", "College"], n),
            "income": rng.integers(1, 5, n),
            "state": rng.integers(1, 6, n),
            "diabetes": rng.integers(0, 2, n).astype(float),
            "genhlth": rng.integers(1, 6, n).astype(float),
            "htm": np.where(rng.random(n) < 0.05, np.nan, rng.normal(1.7, 0.1, n)),
            "wt": 1.0,
        }
    )
    df["bmi"] = np.exp(3.3 + 0.05 * df["diabetes"] + 0.03 * df["genhlth"] + rng.normal(0, 0.15, n))
    df["obese"] = (df["bmi"] >= 30).astype(float)
    true_mean = df["bmi"].mean()
    df.loc[rng.random(n) < 0.1, ["bmi", "obese"]] = np.nan
    imps = list(mi.imputations(df, m=3, seed=1))
    for c in imps:
        assert c["bmi"].notna().all() and c["obese"].notna().all()
        assert c["bmi"].mean() == pytest.approx(true_mean, rel=0.02)
    assert not np.allclose(imps[0]["bmi"], imps[1]["bmi"])  # imputations differ
    q, se, _ = mi.rubin([1.0, 1.2, 0.8], [0.01, 0.01, 0.01])
    assert q == pytest.approx(1.0) and se == pytest.approx(np.sqrt(0.01 + (4 / 3) * 0.04))


def test_rif_contrast_detects_tail_shift_and_variants_run():
    rng = np.random.default_rng(85)
    shifted = simulate_h3(rng, tail_shift=1.5, n=4000)
    flat = simulate_h3(np.random.default_rng(86), tail_shift=0.0, n=4000)
    assert h3.rif_contrast(shifted) < h3.rif_contrast(flat) - 0.5
    e75, _ = h3.fit_h3(shifted, n_rep=3, upper=0.75)
    e11, _ = h3.fit_h3(shifted, n_rep=3, ref_years=(2011,))
    assert np.isfinite(e75.est) and np.isfinite(e11.est)
