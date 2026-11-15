"""H4: state dose-response event study (pre-registration Q19).

Exposure E_s: one-factor measurement model of the three standardized use indicators
    x_js = lambda_j * eta_s + e_js,  eta_s ~ N(0, 1),  lambda_j ~ HalfNormal(1),  e_js ~ N(0, sigma_j),
    sigma_j ~ HalfNormal(1) (not specified in Q19; weakly informative)
E_s = posterior mean of eta_s scaled to SD 1; 200 posterior draws (each scaled to SD 1) carry its uncertainty.

Event study, unweighted OLS on states x years:
    Y_st = alpha_s + lambda_t + sum_k beta_k (E_s x 1[t = k]) + u_st
with beta_k normalized to a 2015-2019 mean of zero. Estimand beta* = mean(beta_2023..2025) minus the values predicted
for those years by a linear trend in beta_k fitted to 2011-2019. Missing state-years are simply absent.

Inference:
- randomization test: E_s permuted across states (20,000 permutations); two-sided p on |beta*| (decided 2026-11-14);
- Rambachan-Roth smoothness restriction Delta^SD(M) (second differences of the pre-trend path bounded by M pp per
  year^2): implemented as a conservative interval, beta* +- (1.96 SE + B(M)), where B(M) is the worst-case bias of
  the linear extrapolation under Delta^SD(M) for the estimand (computed by linear programming over admissible
  paths). The exact fixed-length CI of Rambachan and Roth (2023) can be narrower; this one is valid but conservative
  (kept in Python by decision of 2026-11-14, declared in Q19).
- Uncertainty in E_s: beta* is re-estimated for each of the 200 factor draws and combined with Rubin's rules.
SE(beta*) for the bounds: cluster-robust by state.

Dose-response (Callaway, Goodman-Bacon and Sant'Anna 2024): dY_s = mean of the available years 2023-2025 minus each
state's own 2011-2019 linear-trend projection. Reported: top minus bottom tercile of E_s, and the average derivative
of a quadratic fit of dY_s on E_s (average causal response). Both with the same permutation test.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linprog

PRE = tuple(range(2011, 2020))
NORM = tuple(range(2015, 2020))
POST = (2023, 2024, 2025)


# --------------------------------------------------------------------------------------------- exposure
def standardize(x: pd.DataFrame) -> pd.DataFrame:
    return (x - x.mean()) / x.std(ddof=0)


def factor_exposure(
    indicators: pd.DataFrame, n_draws: int = 200, seed: int = 20261114, sampler_kwargs=None
) -> dict:
    """indicators: index = state, columns = the three use indicators (no missing). Returns E (posterior mean,
    SD 1), draws (n_draws x n_states, each SD 1) and the loadings."""
    import pymc as pm

    z = standardize(indicators).to_numpy()
    n, k = z.shape
    kw = {
        "draws": 1000,
        "tune": 1000,
        "chains": 4,
        "nuts_sampler": "nutpie",
        "progressbar": False,
        "random_seed": seed,
    }
    kw.update(sampler_kwargs or {})
    with pm.Model():
        lam = pm.HalfNormal("lambda", 1.0, shape=k)
        eta = pm.Normal("eta", 0.0, 1.0, shape=n)
        sig = pm.HalfNormal("sigma", 1.0, shape=k)
        pm.Normal("x", eta[:, None] * lam[None, :], sig[None, :], observed=z)
        idata = pm.sample(**kw)
    eta_draws = idata.posterior["eta"].stack(s=("chain", "draw")).to_numpy().T  # (S, n)
    rng = np.random.default_rng(seed)
    pick = eta_draws[rng.choice(len(eta_draws), n_draws, replace=False)]
    scale = lambda v: (v - v.mean(axis=-1, keepdims=True)) / v.std(axis=-1, keepdims=True)  # noqa: E731
    E = scale(eta_draws.mean(axis=0))
    return {
        "E": pd.Series(E, index=indicators.index),
        "draws": scale(pick),
        "loadings": idata.posterior["lambda"].mean(("chain", "draw")).to_numpy(),
        "idata": idata,
    }


# --------------------------------------------------------------------------------------------- event study
def _twfe_residualize(panel: pd.DataFrame, cols: list[str], w: np.ndarray | None = None) -> pd.DataFrame:
    """Two-way (state, year) within-transformation for an unbalanced panel by alternating projections
    (weighted means when w is given)."""
    out = panel[cols].astype(float).copy()
    ww = pd.Series(np.ones(len(panel)) if w is None else w, index=panel.index)

    def wmean(df, key):
        num = df.mul(ww, axis=0).groupby(panel[key]).transform("sum")
        return num.div(ww.groupby(panel[key]).transform("sum"), axis=0)

    for _ in range(200):
        prev = out.copy()
        out = out - wmean(out, "state")
        out = out - wmean(out, "year")
        if np.max(np.abs(out.to_numpy() - prev.to_numpy())) < 1e-12:
            break
    return out


@dataclass
class EventStudy:
    beta: pd.Series  # normalized beta_k by year
    cov: np.ndarray  # cluster-robust covariance of the normalized betas
    beta_star: float
    se_star: float


def _beta_star_weights(years: list[int], pre=PRE, post=POST) -> np.ndarray:
    """Linear weights a such that beta* = a' beta (mean post minus linear-trend prediction from pre)."""
    t = np.array(pre, float)
    X = np.column_stack([np.ones_like(t), t - 2015])
    P = np.column_stack([np.ones(len(post)), np.array(post, float) - 2015]) @ np.linalg.inv(X.T @ X) @ X.T
    a = np.zeros(len(years))
    for y in post:
        a[years.index(y)] += 1 / len(post)
    for j, y in enumerate(pre):
        a[years.index(y)] -= P[:, j].mean()
    return a


def event_study(Y: pd.DataFrame, E: pd.Series) -> EventStudy:
    """Y: columns state, year, y (pp), optionally w (weights for the Q24 population- or precision-weighted
    variants; unweighted otherwise). E: exposure by state."""
    d = Y[Y["state"].isin(E.index)].copy()
    years = sorted(d["year"].unique())
    ref = years[0]
    X = pd.DataFrame(
        {f"b_{k}": (d["year"] == k) * d["state"].map(E) for k in years if k != ref}, index=d.index
    )
    cols = list(X.columns)
    w = d["w"].to_numpy(float) if "w" in d else np.ones(len(d))
    R = _twfe_residualize(pd.concat([d[["state", "year", "y"]], X], axis=1), cols + ["y"], w)
    Xa, ya = R[cols].to_numpy(), R["y"].to_numpy()
    XtX_inv = np.linalg.pinv(Xa.T @ (Xa * w[:, None]))
    b = XtX_inv @ Xa.T @ (w * ya)
    e = ya - Xa @ b
    S = np.zeros((len(cols), len(cols)))
    for s in d["state"].unique():
        m = (d["state"] == s).to_numpy()
        u = Xa[m].T @ (w[m] * e[m])
        S += np.outer(u, u)
    G = d["state"].nunique()
    V = G / (G - 1) * XtX_inv @ S @ XtX_inv
    # full vector with the reference year at 0, then normalize to a 2015-2019 mean of zero
    full = np.concatenate([[0.0], b])
    Vf = np.zeros((len(years), len(years)))
    Vf[1:, 1:] = V
    N = np.eye(len(years))
    for y in NORM:
        N[:, years.index(y)] -= 1 / len(NORM)
    bn, Vn = N @ full, N @ Vf @ N.T
    a = _beta_star_weights(years)
    return EventStudy(pd.Series(bn, index=years), Vn, float(a @ bn), float(np.sqrt(a @ Vn @ a)))


def beta_star(Y: pd.DataFrame, E: pd.Series) -> float:
    return event_study(Y, E).beta_star


def permutation_p(
    stat_fn, Y: pd.DataFrame, E: pd.Series, n_perm: int = 20_000, seed: int = 20261114
) -> tuple[float, float]:
    """Two-sided randomization p for stat_fn(Y, E) permuting E across states. Returns (observed, p)."""
    rng = np.random.default_rng(seed)
    obs = stat_fn(Y, E)
    vals = np.array(
        [stat_fn(Y, pd.Series(rng.permutation(E.to_numpy()), index=E.index)) for _ in range(n_perm)]
    )
    return obs, float((1 + np.sum(np.abs(vals) >= abs(obs))) / (n_perm + 1))


def rubin(estimates: np.ndarray, variances: np.ndarray) -> tuple[float, float]:
    m = len(estimates)
    qbar = float(np.mean(estimates))
    total = float(np.mean(variances) + (1 + 1 / m) * np.var(estimates, ddof=1))
    return qbar, float(np.sqrt(total))


# --------------------------------------------------------------------------------------------- RR bounds
def sd_worst_case_bias(M: float, pre=PRE, post=POST) -> float:
    """Largest |a' delta| over pre-trend paths delta with |second differences| <= M, delta normalized like beta
    (2015-2019 mean zero). a' delta is the bias of beta* (linear extrapolation) when the untreated path is delta."""
    years = list(range(min(pre), max(post) + 1))
    a = _beta_star_weights(years, pre, post)
    n = len(years)
    if M == 0:
        return 0.0
    D2 = np.zeros((n - 2, n))
    for i in range(n - 2):
        D2[i, i : i + 3] = [1, -2, 1]
    A_eq = np.zeros((1, n))
    for y in NORM:
        A_eq[0, years.index(y)] = 1 / len(NORM)
    A_ub = np.vstack([D2, -D2])
    b_ub = np.full(2 * (n - 2), M)
    res = linprog(-a, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=[0.0], bounds=[(None, None)] * n)
    return float(-res.fun)


def rr_interval(est: float, se: float, M: float) -> tuple[float, float]:
    b = sd_worst_case_bias(M)
    return est - 1.96 * se - b, est + 1.96 * se + b


# --------------------------------------------------------------------------------------------- dose-response
def state_departures(Y: pd.DataFrame, pre=PRE, post=POST) -> pd.Series:
    out = {}
    for s, g in Y.groupby("state"):
        g = g.set_index("year")["y"]
        tp = [t for t in pre if t in g.index]
        tq = [t for t in post if t in g.index]
        if len(tp) < 3 or not tq:
            continue
        b = np.polyfit(np.array(tp, float) - 2015, g.loc[tp].to_numpy(), 1)
        out[s] = float(np.mean(g.loc[tq].to_numpy() - np.polyval(b, np.array(tq, float) - 2015)))
    return pd.Series(out)


def tercile_contrast(dY: pd.Series, E: pd.Series, n_groups: int = 3) -> float:
    e = E.loc[dY.index]
    q = pd.qcut(e, n_groups, labels=False)
    return float(dY[q == n_groups - 1].mean() - dY[q == 0].mean())


def average_causal_response(dY: pd.Series, E: pd.Series, degree: int = 2) -> float:
    e = E.loc[dY.index].to_numpy()
    c = np.polyfit(e, dY.to_numpy(), degree)
    deriv = np.polyder(c)
    return float(np.mean(np.polyval(deriv, e)))


def rm_interval(es: EventStudy, mbar: float, pre=PRE, post=POST) -> tuple[float, float]:
    """Q24 Rambachan-Roth relative-magnitude restriction, conservative version (like `rr_interval`): post-period
    violations of the linear pre-trend may grow each year by at most mbar times the largest year-to-year change of
    the pre-period deviations from that trend. Worst-case bias for year t is mbar * m * (t - max(pre)); the bias of
    beta* is its mean over the post years. Interval: beta* +- (1.96 SE + bias)."""
    b = es.beta
    t = np.array([y for y in pre if y in b.index], float)
    coef = np.polyfit(t - 2015, b.loc[t.astype(int)].to_numpy(), 1)
    resid = b.loc[t.astype(int)].to_numpy() - np.polyval(coef, t - 2015)
    m = float(np.max(np.abs(np.diff(resid)))) if len(resid) > 1 else 0.0
    bias = mbar * m * float(np.mean([y - max(pre) for y in post]))
    return es.beta_star - 1.96 * es.se_star - bias, es.beta_star + 1.96 * es.se_star + bias
