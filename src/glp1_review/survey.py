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
    e = y - Xa @ beta
    u = Xa * (w * e)[:, None]  # score contributions

    st = pd.Series(np.asarray(strata)).astype(str).to_numpy()
    ps = pd.Series(np.asarray(psu)).astype(str).to_numpy()
    key = pd.Series(st) + "|" + pd.Series(ps)
    codes, uniq = pd.factorize(key)
    U = np.zeros((len(uniq), u.shape[1]))
    np.add.at(U, codes, u)  # PSU totals
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
    if singles:  # single-PSU strata: centre at the grand mean of PSU totals
        S = np.array(singles)
        D = S - U.mean(axis=0)
        meat += D.T @ D
    cov = A_inv @ meat @ A_inv
    return DesignFit(names, beta, cov, len(y), len(uniq), len(np.unique(st)))


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
