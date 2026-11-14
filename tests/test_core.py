"""Core analysis helpers on simulated data with known answers."""

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from glp1_review import decision as dec
from glp1_review import guard, survey, trend

YEARS = list(range(2011, 2026))


# ------------------------------------------------------------------------------------------- guard
def test_guard_blocks_without_registration(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "REGISTRATION_FILE", tmp_path / "osf_registration.txt")
    with pytest.raises(guard.NotRegisteredError):
        guard.require_registration()
    (tmp_path / "osf_registration.txt").write_text("https://doi.org/10.17605/OSF.IO/XXXXX")
    assert guard.require_registration().startswith("https://doi.org")


# ------------------------------------------------------------------------------------------- trend
def _logit_series(slope=0.025, level=-0.95, brk=0.0, noise=0.0, rng=None):
    t = np.array(YEARS, float)
    x = level + slope * (t - 2015) + brk * np.clip(t - 2022, 0, None)
    if noise:
        x = x + rng.normal(0, noise, len(t))
    return trend.expit(x)


def test_trend_no_break_is_zero_without_noise():
    d = trend.departures(_logit_series(), YEARS, predictive=False)
    assert np.allclose(d.draws, 0, atol=1e-10)


def test_trend_recovers_known_break():
    p = _logit_series(brk=-0.03)
    d = trend.departures(p, YEARS, predictive=False)
    base = _logit_series()
    expected = 100 * (p[-3:] - base[-3:])
    assert np.allclose(d.draws[0], expected, atol=1e-9)
    assert d.draws[0, 2] < d.draws[0, 0] < 0  # widens over time


def test_trend_predictive_interval_coverage():
    """No break, normal noise on the logit scale: the 95% interval of D_2025 contains zero in ~95% of
    simulations (exact for the Student-t predictive)."""
    rng = np.random.default_rng(1)
    hits, n_sim = 0, 400
    for _ in range(n_sim):
        p = _logit_series(noise=0.01, rng=rng)
        d = trend.departures(np.tile(p, (1000, 1)), YEARS, rng=rng)
        lo, hi = np.percentile(d.draws[:, 2], [2.5, 97.5])
        hits += lo <= 0 <= hi
    assert 0.91 <= hits / n_sim <= 0.985


def test_trend_quadratic_and_level_run():
    p = _logit_series(brk=-0.02)
    for form in ("quadratic", "level"):
        d = trend.departures(p, YEARS, form=form, predictive=False)
        assert d.draws.shape == (1, 3)
    lvl = trend.departures(p, YEARS, form="level", predictive=False)
    assert lvl.draws[0, 0] < 0


# ------------------------------------------------------------------------------------------- survey
def test_weighted_quantile_equal_weights_matches_median():
    x = np.arange(1, 102, dtype=float)
    assert survey.weighted_quantile(x, np.ones_like(x), 0.5)[0] == pytest.approx(51.0)


def test_weighted_quantile_weights_shift():
    x = np.array([1.0, 2.0, 3.0])
    assert survey.weighted_quantile(x, [1, 1, 10], 0.5)[0] > 2.5


def test_wls_design_matches_statsmodels_point_estimates_and_cluster_se():
    rng = np.random.default_rng(3)
    n, g = 4000, 200
    psu = rng.integers(0, g, n)
    x = rng.normal(size=n)
    y = 1 + 0.5 * x + rng.normal(size=g)[psu] + rng.normal(size=n)
    w = rng.uniform(0.5, 2, n)
    X = pd.DataFrame({"const": 1.0, "x": x})
    fit = survey.wls_design(X, y, w, strata=np.zeros(n), psu=psu)
    ref = sm.WLS(y, X, weights=w).fit(cov_type="cluster", cov_kwds={"groups": psu, "use_correction": False})
    assert np.allclose(fit.coef, ref.params, atol=1e-10)
    # one stratum: linearization = cluster-robust with G/(G-1) correction
    assert fit.se[1] == pytest.approx(ref.bse["x"] * np.sqrt(g / (g - 1)), rel=1e-6)


def test_demean_absorbs_fixed_effects():
    rng = np.random.default_rng(4)
    n = 3000
    grp = rng.integers(0, 60, n)
    fe = rng.normal(0, 5, 60)
    x = rng.normal(size=n) + 0.3 * fe[grp]
    y = 2.0 * x + fe[grp] + rng.normal(size=n)
    w = rng.uniform(0.5, 2, n)
    df = pd.DataFrame({"y": y, "x": x})
    dm = survey.demean(df, ["y", "x"], grp, w)
    fit = survey.wls_design(dm[["x"]], dm["y"], w, np.zeros(n), np.arange(n))
    dummies = pd.get_dummies(grp, prefix="g", dtype=float)
    ref = sm.WLS(y, pd.concat([df[["x"]], dummies], axis=1), weights=w).fit()
    assert fit.coef[0] == pytest.approx(ref.params["x"], rel=1e-8)


def test_rao_wu_weights_unbiased_for_total():
    rng = np.random.default_rng(5)
    strata = np.repeat(np.arange(20), 50)
    psu = np.tile(np.repeat(np.arange(5), 10), 20)
    w = rng.uniform(1, 3, len(strata))
    rw = survey.rao_wu_weights(strata, psu, w, 2000, rng)
    assert rw.sum(axis=0).mean() == pytest.approx(w.sum(), rel=0.01)


# ------------------------------------------------------------------------------------------- decision
def test_holm():
    adj = dec.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj == {"a": 0.03, "c": 0.06, "b": 0.06}


def test_classify_family_labels():
    fam = dec.classify_family(
        {"H2": dec.Estimate(-0.6, 0.11), "H3": dec.Estimate(0.05, 0.20), "H6": dec.Estimate(-0.3, 0.33)},
        h6_late=dec.Estimate(0.1, 0.4),
        h6_initiators=89,
    )
    assert fam["H2"]["label"] == "supported"
    assert fam["H3"]["label"] == "contradicted"  # 90% CI above -0.3
    assert fam["H6"]["label"] == "inconclusive"
    assert dec.overall_verdict(fam, nc1_pass=True) == "mixed"


def test_h6_placebo_and_minimum_initiators():
    fam = dec.classify_family(
        {"H6": dec.Estimate(-2.0, 0.3)}, h6_late=dec.Estimate(-1.5, 0.4), h6_initiators=89
    )
    assert fam["H6"]["label"] == "inconclusive"
    fam = dec.classify_family({"H2": dec.Estimate(-1, 0.1), "H6": dec.Estimate(-2.0, 0.3)}, h6_initiators=25)
    assert fam["H6"]["label"] == "descriptive" and fam["H2"]["label"] == "supported"


def test_verdicts():
    sup = {"label": "supported"}
    con = {"label": "contradicted"}
    assert (
        dec.overall_verdict({"H2": sup, "H3": sup, "H6": {"label": "inconclusive"}}, True)
        == "GLP-1 signature present"
    )
    assert dec.overall_verdict({"H2": con, "H3": con, "H6": sup}, True) == "absent"
    assert dec.overall_verdict({"H2": sup, "H3": sup, "H6": sup}, False) == "absent"
    assert dec.nc1_passes(dec.Estimate(0.05, 0.1)) and not dec.nc1_passes(dec.Estimate(0.4, 0.1))


def test_tie_supported_and_contradicted_is_contradicted():
    """Significantly negative but significantly smaller than the SESOI -> contradicted (Q22, 2026-11-14)."""
    fam = dec.classify_family({"H2": dec.Estimate(-0.05, 0.01)})
    assert fam["H2"]["label"] == "contradicted"


def test_t_based_estimate_is_more_conservative():
    e_norm, e_t = dec.Estimate(-0.3, 0.15), dec.Estimate(-0.3, 0.15, dof=6)
    assert dec.p_one_sided_negative(e_t) > dec.p_one_sided_negative(e_norm)
