"""H4 state event study on simulated panels with a known dose-response."""

import numpy as np
import pandas as pd
import pytest

from glp1_review import h4_states as h4

YEARS = list(range(2011, 2026))


def simulate(rng, slope_post=-0.8, n_states=50, pretrend=0.0, missing=0.03):
    E = pd.Series(rng.normal(size=n_states), index=[f"S{i:02d}" for i in range(n_states)])
    E = (E - E.mean()) / E.std(ddof=0)
    rows = []
    for s, e in E.items():
        a = rng.normal(30, 3)
        tr = rng.normal(0.5, 0.1)
        for t in YEARS:
            if rng.random() < missing:
                continue
            y = a + tr * (t - 2011) + rng.normal(0, 0.6) + pretrend * e * (t - 2015)
            if t >= 2023:
                y += slope_post * e * (t - 2022) / 2
            rows.append((s, t, y))
    return pd.DataFrame(rows, columns=["state", "year", "y"]), E


def test_event_study_recovers_post_slope():
    rng = np.random.default_rng(50)
    Y, E = simulate(rng, slope_post=-0.8)
    es = h4.event_study(Y, E)
    true = -0.8 * np.mean([0.5, 1.0, 1.5])  # mean of the post effects per SD
    assert es.beta_star == pytest.approx(true, abs=3 * es.se_star)
    assert abs(es.beta.loc[list(h4.NORM)].mean()) < 1e-10  # normalization


def test_linear_pretrend_is_removed_by_beta_star():
    rng = np.random.default_rng(51)
    Y, E = simulate(rng, slope_post=0.0, pretrend=0.05)
    es = h4.event_study(Y, E)
    assert abs(es.beta_star) < 3 * es.se_star


def test_permutation_p_small_under_effect_large_under_null():
    rng = np.random.default_rng(52)
    Y, E = simulate(rng, slope_post=-1.0)
    _, p = h4.permutation_p(h4.beta_star, Y, E, n_perm=300)
    assert p < 0.05
    Y0, E0 = simulate(np.random.default_rng(53), slope_post=0.0)
    _, p0 = h4.permutation_p(h4.beta_star, Y0, E0, n_perm=300)
    assert p0 > 0.01


def test_sd_bias_zero_at_m0_and_grows_with_m():
    assert h4.sd_worst_case_bias(0.0) == 0.0
    b1, b2 = h4.sd_worst_case_bias(0.02), h4.sd_worst_case_bias(0.05)
    assert 0 < b1 < b2 and b2 == pytest.approx(2.5 * b1, rel=1e-6)  # linear in M


def test_dose_response():
    rng = np.random.default_rng(54)
    Y, E = simulate(rng, slope_post=-1.0, missing=0.0)
    dY = h4.state_departures(Y)
    assert h4.tercile_contrast(dY, E) < -1.0
    acr = h4.average_causal_response(dY, E)
    assert acr == pytest.approx(-1.0, abs=0.3)  # mean post effect per SD = -1.0


def test_rubin():
    q, se = h4.rubin(np.array([1.0, 1.2, 0.8]), np.array([0.04, 0.04, 0.04]))
    assert q == pytest.approx(1.0) and se == pytest.approx(np.sqrt(0.04 + (4 / 3) * 0.04))


def test_factor_exposure_tracks_latent_use():
    rng = np.random.default_rng(55)
    eta = rng.normal(size=50)
    ind = pd.DataFrame(
        {j: lam * eta + rng.normal(0, 0.5, 50) for j, lam in (("a", 1.0), ("b", 0.8), ("c", 0.6))}
    )
    out = h4.factor_exposure(ind, n_draws=50, sampler_kwargs={"draws": 300, "tune": 300, "chains": 2})
    assert np.corrcoef(out["E"], eta)[0, 1] > 0.9
    assert out["draws"].shape == (50, 50)
    assert np.allclose(out["draws"].std(axis=1), 1)
