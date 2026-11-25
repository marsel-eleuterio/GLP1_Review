"""Survey estimation helpers (pre-registration Q16, Q23).

- weighted_quantile: weighted empirical distribution function with linear interpolation (Q23).
- wls_design: weighted least squares with design-based (Taylor linearization) variance, PSUs nested in strata;
  strata with a single PSU are centred at the grand mean (Q23).
- demean: weighted within-transformation for one set of fixed effects (e.g. state x year), exact by FWL.
- rao_wu_weights: Rao-Wu rescaled bootstrap weights, n_h - 1 PSUs drawn with replacement within each stratum.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


def weighted_mean(x, w) -> float:
    x, w = np.asarray(x, float), np.asarray(w, float)
    return float(np.sum(w * x) / np.sum(w))


def weighted_quantile(x, w, q) -> np.ndarray:
    """Quantiles of the weighted ECDF with linear interpolation between the mid-points of the weight mass."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    o = np.argsort(x)
    x, w = x[o], w[o]
    cw = np.cumsum(w)
    p = (cw - 0.5 * w) / cw[-1]
    return np.interp(np.atleast_1d(q), p, x)


def demean(df: pd.DataFrame, cols: list[str], group: pd.Series | np.ndarray, w) -> pd.DataFrame:
    """Subtract the weighted group mean from each column (absorbs one set of fixed effects)."""
    w = np.asarray(w, float)
    g = pd.Series(np.asarray(group)).astype("category").cat.codes.to_numpy()
    sw = np.bincount(g, weights=w)
    out = {}
    for c in cols:
        v = df[c].to_numpy(dtype=float)
        m = np.bincount(g, weights=w * v) / sw
        out[c] = v - m[g]
    return pd.DataFrame(out, index=df.index)


@dataclass
class DesignFit:
    names: list[str]
    coef: np.ndarray
    cov: np.ndarray
    n: int
    n_psu: int
    n_strata: int

    @property
    def se(self) -> np.ndarray:
        return np.sqrt(np.diag(self.cov))

    def get(self, name: str) -> tuple[float, float]:
        i = self.names.index(name)
        return float(self.coef[i]), float(self.se[i])

    def lincom(self, weights: dict[str, float]) -> tuple[float, float]:
        a = np.zeros(len(self.names))
        for k, v in weights.items():
            a[self.names.index(k)] = v
        return float(a @ self.coef), float(np.sqrt(a @ self.cov @ a))


def wls_design(X: pd.DataFrame, y, w, strata, psu, dof_adjust: int = 0) -> DesignFit:
    """WLS with linearized variance. dof_adjust: number of absorbed fixed effects (not used in the
    design-based formula, kept for reporting)."""
    names = list(X.columns)
    Xa = X.to_numpy(dtype=float)
    y, w = np.asarray(y, float), np.asarray(w, float)
    A = Xa.T @ (Xa * w[:, None])
    A_inv = np.linalg.pinv(A)
    beta = A_inv @ (Xa.T @ (w * y))
    we = w * (y - Xa @ beta)  # score contributions are Xa * we[:, None]

    st = pd.Series(np.asarray(strata)).astype(str)
    ps = pd.Series(np.asarray(psu)).astype(str)
    codes, uniq = pd.factorize(st + "|" + ps)  # PSUs nested in strata
    st_codes, st_uniq = pd.factorize(st)
    k, n_st = Xa.shape[1], len(st_uniq)
    # PSU totals of the score contributions, one column at a time: the same sequential sums as np.add.at on the
    # full score matrix, without materializing that n x k matrix (one copy of the design less in memory)
    U = np.column_stack([np.bincount(codes, weights=Xa[:, j] * we, minlength=len(uniq)) for j in range(k)])
    # Between-PSU variance within strata, all strata at once: sum_h n_h/(n_h-1) sum_i (U_hi - mean_h)'(U_hi - mean_h).
    # (A loop over strata compared every PSU label for each of the ~36,000 BRFSS strata.)
    psu_st = np.empty(len(uniq), dtype=np.int64)
    psu_st[codes] = st_codes
    nh = np.bincount(psu_st, minlength=n_st)
    means = (
        np.column_stack([np.bincount(psu_st, weights=U[:, j], minlength=n_st) for j in range(k)])
        / nh[:, None]
    )
    multi = nh[psu_st] > 1
    f = np.zeros(n_st)
    f[nh > 1] = nh[nh > 1] / (nh[nh > 1] - 1)
    D = (U[multi] - means[psu_st[multi]]) * np.sqrt(f[psu_st[multi]])[:, None]
    meat = D.T @ D
    if not multi.all():  # single-PSU strata: centre at the grand mean of PSU totals
        D = U[~multi] - U.mean(axis=0)
        meat += D.T @ D
    cov = A_inv @ meat @ A_inv
    return DesignFit(names, beta, cov, len(y), len(uniq), n_st)


def rao_wu_weights(strata, psu, w, n_rep: int, rng: np.random.Generator) -> np.ndarray:
    """(n_obs, n_rep) replicate weights. Within each stratum with n_h >= 2 PSUs, n_h - 1 PSUs are drawn with
    replacement and each PSU's weights are multiplied by n_h / (n_h - 1) * (times drawn). Single-PSU strata keep
    their weights."""
    w = np.asarray(w, float)
    codes, psu_stratum = psu_codes(strata, psu)
    return w[:, None] * rao_wu_multipliers(psu_stratum, n_rep, rng)[codes]


def psu_codes(strata, psu) -> tuple[np.ndarray, np.ndarray]:
    """Integer PSU code of each row (PSUs are nested in strata) and the stratum of each distinct PSU."""
    st = pd.Series(np.asarray(strata)).astype(str).to_numpy()
    ps = pd.Series(np.asarray(psu)).astype(str).to_numpy()
    key = pd.Series(st) + "\x1f" + pd.Series(ps)
    codes, uniq = pd.factorize(key)
    return codes, pd.Series(uniq).str.split("\x1f").str[0].to_numpy()


def rao_wu_multipliers(psu_stratum, n_rep: int, rng: np.random.Generator) -> np.ndarray:
    """(n_psu, n_rep) Rao-Wu rescaled bootstrap multipliers, given the stratum of each distinct PSU."""
    # Strata in sorted order and PSUs in their original order within each stratum, so the random draws are the
    # same as a loop over np.unique(psu_stratum) with np.flatnonzero; the indices are grouped once instead of
    # comparing every PSU label for each of the ~36,000 BRFSS strata.
    _, inv = np.unique(np.asarray(psu_stratum), return_inverse=True)
    inv = inv.ravel()
    order = np.argsort(inv, kind="stable")
    sizes = np.bincount(inv)
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]])
    reps = np.arange(n_rep)
    mult = np.ones((len(inv), n_rep))
    for s, nh in zip(starts, sizes, strict=True):
        if nh < 2:
            continue
        draws = rng.integers(0, nh, size=(nh - 1, n_rep))
        counts = np.bincount((draws + nh * reps).ravel(), minlength=nh * n_rep).reshape(n_rep, nh).T
        mult[order[s : s + nh]] = nh / (nh - 1) * counts
    return mult
