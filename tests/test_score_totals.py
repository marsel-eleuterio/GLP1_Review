"""Speed and memory rewrites of the survey helpers (25 November 2026), checked against the implementation as
registered (commit 7d1ec0f), which is kept here as the reference.

- wls_design: PSU score totals with np.bincount instead of np.add.at on the full score matrix, and the
  between-PSU variance computed for all strata at once instead of a loop that compared every PSU label for each
  of the ~36,000 BRFSS strata. Same formula; the sums are taken in another order, so the covariance agrees to
  rounding error (the coefficients are unchanged).
- rao_wu_multipliers: same strata order and same random draws, indices grouped once: bit-for-bit identical.
- H2 wild cluster bootstrap: state score totals with np.bincount: bit-for-bit identical.
"""

import numpy as np
import pandas as pd

from glp1_review import survey


def _wls_design_registered(X, y, w, strata, psu):
    Xa = X.to_numpy(dtype=float)
    y, w = np.asarray(y, float), np.asarray(w, float)
    A = Xa.T @ (Xa * w[:, None])
    A_inv = np.linalg.pinv(A)
    beta = A_inv @ (Xa.T @ (w * y))
    e = y - Xa @ beta
    u = Xa * (w * e)[:, None]
    st = pd.Series(np.asarray(strata)).astype(str).to_numpy()
    ps = pd.Series(np.asarray(psu)).astype(str).to_numpy()
    key = pd.Series(st) + "|" + pd.Series(ps)
    codes, uniq = pd.factorize(key)
    U = np.zeros((len(uniq), u.shape[1]))
    np.add.at(U, codes, u)
    psu_stratum = pd.Series(uniq).str.split("|").str[0].to_numpy()
    meat = np.zeros((u.shape[1], u.shape[1]))
    singles = []
    for h in np.unique(psu_stratum):
        Uh = U[psu_stratum == h]
        nh = len(Uh)
        if nh == 1:
            singles.append(Uh[0])
            continue
        D = Uh - Uh.mean(axis=0)
        meat += nh / (nh - 1) * D.T @ D
    if singles:
        S = np.array(singles)
        D = S - U.mean(axis=0)
        meat += D.T @ D
    return beta, A_inv @ meat @ A_inv, len(uniq), len(np.unique(st))


def _rao_wu_multipliers_registered(psu_stratum, n_rep, rng):
    mult = np.ones((len(psu_stratum), n_rep))
    for h in np.unique(psu_stratum):
        idx = np.flatnonzero(psu_stratum == h)
        nh = len(idx)
        if nh < 2:
            continue
        draws = rng.integers(0, nh, size=(nh - 1, n_rep))
        counts = np.zeros((nh, n_rep))
        for r in range(n_rep):
            counts[:, r] = np.bincount(draws[:, r], minlength=nh)
        mult[idx] = nh / (nh - 1) * counts
    return mult


def _design(seed, n=20_000, k=12, n_strata=40, psu_per_stratum=6):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(n, k)), columns=[f"x{j}" for j in range(k)])
    y = X.to_numpy() @ rng.normal(size=k) + rng.normal(size=n)
    w = rng.uniform(0.2, 5, n)
    strata = rng.integers(0, n_strata, n).astype(str)
    psu = rng.integers(0, psu_per_stratum, n)
    strata[:3], psu[:3] = "single_a", 0  # two strata with a single PSU
    strata[3:5], psu[3:5] = "single_b", 7
    return X, y, w, strata, psu


def test_wls_design_matches_the_registered_implementation():
    # few PSUs per stratum (simulated data) and many strata with about one respondent per PSU (as in BRFSS)
    for seed, n_strata, psu_per_stratum in [(1, 40, 6), (2, 3_000, 50), (3, 500, 3)]:
        X, y, w, strata, psu = _design(seed, n_strata=n_strata, psu_per_stratum=psu_per_stratum)
        fit = survey.wls_design(X, y, w, strata, psu)
        beta, cov, n_psu, n_strata_ref = _wls_design_registered(X, y, w, strata, psu)
        np.testing.assert_array_equal(fit.coef, beta)
        np.testing.assert_allclose(fit.cov, cov, rtol=1e-10, atol=1e-14 * np.abs(cov).max())
        assert (fit.n_psu, fit.n_strata) == (n_psu, n_strata_ref)


def test_rao_wu_multipliers_are_bit_for_bit_the_same():
    rng = np.random.default_rng(5)
    psu_stratum = rng.integers(0, 300, 5_000).astype(str)
    psu_stratum[:2] = ["lonely", "zz_lonely"]  # single-PSU strata keep multiplier 1
    for n_rep in (1, 7, 25):
        new = survey.rao_wu_multipliers(psu_stratum, n_rep, np.random.default_rng(11))
        ref = _rao_wu_multipliers_registered(psu_stratum, n_rep, np.random.default_rng(11))
        np.testing.assert_array_equal(new, ref)


def test_rng_state_after_rao_wu_is_the_same():
    """Later draws (the next bootstrap chunk) must not shift."""
    psu_stratum = np.random.default_rng(6).integers(0, 50, 2_000).astype(str)
    r1, r2 = np.random.default_rng(3), np.random.default_rng(3)
    survey.rao_wu_multipliers(psu_stratum, 10, r1)
    _rao_wu_multipliers_registered(psu_stratum, 10, r2)
    assert r1.integers(0, 10**9) == r2.integers(0, 10**9)


def test_state_totals_match_add_at_bit_for_bit():
    rng = np.random.default_rng(4)
    n, k = 30_000, 9
    Xa, we = rng.normal(size=(n, k)), rng.normal(size=n)
    g = rng.integers(0, 51, n)
    S_ref = np.zeros((51, k))
    np.add.at(S_ref, g, Xa * we[:, None])
    S_new = np.column_stack([np.bincount(g, weights=Xa[:, j] * we, minlength=51) for j in range(k)])
    np.testing.assert_array_equal(S_new, S_ref)
