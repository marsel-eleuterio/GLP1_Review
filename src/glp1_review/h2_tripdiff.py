"""H2: diabetes triple difference on individual BRFSS records (pre-registration Q19).

    BMI_i = lambda_(state,year) + X_i'b + D_i*(a0 + Z_i'a + theta*(t - 2015) + kappa*1[t >= t_item])
            + sum_{k in pi_years} pi_k * D_i * 1[t = k] + e_i

D = diagnosed diabetes (or, for the secondary gradients, ages 50-64 / women / insured). State x year fixed effects
are absorbed by a weighted within-transformation (exact by Frisch-Waugh-Lovell). X = age group x sex, race and
ethnicity, education and income indicators; Z = age group and sex. theta is identified from the years without a
pi_k dummy (2011-2019 in the primary model). kappa absorbs the level shift when the diabetes item changes
(t_item = 2019, DIABETE3 -> DIABETE4); it is dropped automatically when it is collinear with the pi_k dummies.
Survey weights _LLCPWT, design-based SEs with strata _STSTR nested in year and PSUs _PSU.

Estimand: pi_bar = mean of pi_k over `estimand_years` (2023-2025), in kg/m2.

Inference, two stages (decided by the author on 2026-11-14, before registration): a single regression's design-based
SE reflects sampling error only; it ignores year-level shocks to the diabetes gap (the residual SD that Q21 uses for
power), and kappa would rest on 2019 alone. So `fit_two_stage` (primary) first estimates the gap g_t for every year
(D x year dummies, same X, Z and fixed effects), then fits g_t = a + theta*(t - 2015) + kappa*1[t >= t_item] by OLS on
the trend years and projects to the post years, as in H1 Stage 2: pi_t = g_t - projection, and
SE(pi_bar) = s * sqrt(1/m + x0bar'(X'X)^-1 x0bar), Student-t with (n_trend - p) df. `fit` (single regression,
design-based SE) is kept as a secondary estimate.
NC2 (placebo): years 2011-2018, pi_years 2016-2018, estimand_years 2017-2018 (theta fitted to 2011-2015). 2019 is
left out because the diabetes item changes that year and kappa cannot be separated from a break inside the
placebo window (decided by the author on 2026-11-14, before registration).
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from glp1_review.decision import Estimate
from glp1_review.survey import DesignFit, demean, wls_design

X_CATS = ["race", "educ", "income"]
Z_CATS = ["age_group", "sex"]


@dataclass
class Spec:
    years: tuple[int, ...] = tuple(range(2011, 2026))
    pi_years: tuple[int, ...] = (2020, 2021, 2022, 2023, 2024, 2025)
    estimand_years: tuple[int, ...] = (2023, 2024, 2025)
    t_item: int | None = 2019
    interactions: bool = True  # Z_i'a (Q24 sensitivity: without age and sex interactions)
    outcome: str = "bmi"  # or "obese" (linear probability, secondary)
    group: str = "diabetes"  # or a 0/1 column for the secondary gradients


PRIMARY = Spec()
NC2 = Spec(
    years=tuple(range(2011, 2019)),
    pi_years=(2016, 2017, 2018),
    estimand_years=(2017, 2018),
    t_item=None,
)


def _dummies(s: pd.Series, prefix: str) -> pd.DataFrame:
    return pd.get_dummies(s.astype(str), prefix=prefix, drop_first=True, dtype=float)


def build(df: pd.DataFrame, spec: Spec) -> tuple[pd.DataFrame, list[str]]:
    d = df[df["year"].isin(spec.years)]
    D = d[spec.group].astype(float)
    t = d["year"].astype(int)
    parts = [_dummies(d["age_group"].astype(str) + "_" + d["sex"].astype(str), "agesex")]
    parts += [_dummies(d[c], c) for c in X_CATS if c in d and d[c].nunique() > 1]
    X = pd.concat(parts, axis=1)
    X["D"] = D
    X["D_trend"] = D * (t - 2015)
    pi_cols = []
    for k in spec.pi_years:
        X[f"pi_{k}"] = D * (t == k)
        pi_cols.append(f"pi_{k}")
    if spec.t_item is not None:
        post_item = [y for y in spec.years if y >= spec.t_item]
        if not set(post_item) <= set(spec.pi_years):  # otherwise collinear with the pi dummies
            X["D_item"] = D * (t >= spec.t_item)
    if spec.interactions:
        for c in Z_CATS:
            Zc = _dummies(d[c], c)
            X = X.join(Zc.mul(D, axis=0).add_prefix("D_x_"))
    return X, pi_cols


def fit(df: pd.DataFrame, spec: Spec = PRIMARY) -> tuple[Estimate, DesignFit]:
    d = df[df["year"].isin(spec.years) & df[spec.outcome].notna() & df[spec.group].notna()]
    X, pi_cols = build(d, spec)
    X = X.loc[:, X.std() > 0]
    w = d["wt"].to_numpy(float)
    fe = d["state"].astype(str) + "_" + d["year"].astype(str)
    cols = list(X.columns)
    dm = demean(pd.concat([X, d[[spec.outcome]]], axis=1), cols + [spec.outcome], fe, w)
    strata = d["year"].astype(str) + "_" + d["strat"].astype(str)
    psu = strata + "_" + d["psu"].astype(str)
    res = wls_design(dm[cols], dm[spec.outcome], w, strata, psu)
    est, se = res.lincom({f"pi_{k}": 1 / len(spec.estimand_years) for k in spec.estimand_years})
    return Estimate(est, se), res


def yearly_gaps(df: pd.DataFrame, spec: Spec = PRIMARY) -> tuple[pd.Series, np.ndarray, DesignFit]:
    """Stage 1: diabetes gap g_t for every year (D x year dummies, no trend or item terms), with the same X, Z
    interactions, state x year fixed effects, weights and design-based covariance."""
    d = df[df["year"].isin(spec.years) & df[spec.outcome].notna() & df[spec.group].notna()]
    stage1 = Spec(
        years=spec.years,
        pi_years=spec.years,
        estimand_years=spec.estimand_years,
        t_item=None,
        interactions=spec.interactions,
        outcome=spec.outcome,
        group=spec.group,
    )
    X, pi_cols = build(d, stage1)
    X = X.drop(columns=["D", "D_trend"])  # every year has its own gap
    X = X.loc[:, X.std() > 0]
    w = d["wt"].to_numpy(float)
    fe = d["state"].astype(str) + "_" + d["year"].astype(str)
    cols = list(X.columns)
    dm = demean(pd.concat([X, d[[spec.outcome]]], axis=1), cols + [spec.outcome], fe, w)
    strata = d["year"].astype(str) + "_" + d["strat"].astype(str)
    psu = strata + "_" + d["psu"].astype(str)
    res = wls_design(dm[cols], dm[spec.outcome], w, strata, psu)
    idx = [res.names.index(c) for c in pi_cols]
    g = pd.Series(res.coef[idx], index=list(spec.years))
    return g, res.cov[np.ix_(idx, idx)], res


def fit_two_stage(df: pd.DataFrame, spec: Spec = PRIMARY) -> tuple[Estimate, dict]:
    """Primary H2 estimate (see module docstring). Returns the estimate with Student-t dof and the details."""
    g, V, _ = yearly_gaps(df, spec)
    trend_years = [y for y in spec.years if y not in spec.pi_years]
    t_tr = np.array(trend_years, float)
    cols = [np.ones_like(t_tr), t_tr - 2015]
    use_item = spec.t_item is not None and spec.t_item in trend_years
    if use_item:
        cols.append((t_tr >= spec.t_item).astype(float))
    Xt = np.column_stack(cols)
    yt = g.loc[trend_years].to_numpy()
    XtX_inv = np.linalg.inv(Xt.T @ Xt)
    b = XtX_inv @ Xt.T @ yt
    dof = len(trend_years) - Xt.shape[1]
    s = float(np.sqrt(np.sum((yt - Xt @ b) ** 2) / dof))
    t0 = np.array(spec.estimand_years, float)
    X0 = np.column_stack(
        [np.ones_like(t0), t0 - 2015] + ([(t0 >= spec.t_item).astype(float)] if use_item else [])
    )
    pi = g.loc[list(spec.estimand_years)].to_numpy() - X0 @ b
    x0bar = X0.mean(axis=0)
    m = len(spec.estimand_years)
    se = s * float(np.sqrt(1 / m + x0bar @ XtX_inv @ x0bar))
    details = {
        "gaps": g,
        "gap_cov": V,
        "trend_coef": b,
        "residual_sd": s,
        "pi": dict(zip(spec.estimand_years, pi, strict=True)),
    }
    return Estimate(float(pi.mean()), se, dof=dof), details


# --------------------------------------------------------------------------------------------- Q24 sensitivities
def wild_cluster_bootstrap(
    df: pd.DataFrame, spec: Spec = PRIMARY, n_boot: int = 9_999, seed: int = 20261114
) -> tuple[Estimate, dict]:
    """Single regression with a wild cluster bootstrap by state (Webb six-point weights, Q23/Q24).
    Unrestricted bootstrap of the coefficient: b* = b + A^-1 sum_g v_g s_g, with s_g the state score totals.
    Returns pi_bar with the bootstrap SE and the 95% percentile interval."""
    d = df[df["year"].isin(spec.years) & df[spec.outcome].notna() & df[spec.group].notna()]
    X, _ = build(d, spec)
    X = X.loc[:, X.std() > 0]
    w = d["wt"].to_numpy(float)
    fe = d["state"].astype(str) + "_" + d["year"].astype(str)
    cols = list(X.columns)
    dm = demean(pd.concat([X, d[[spec.outcome]]], axis=1), cols + [spec.outcome], fe, w)
    Xa, y = dm[cols].to_numpy(), dm[spec.outcome].to_numpy()
    A_inv = np.linalg.pinv(Xa.T @ (Xa * w[:, None]))
    b = A_inv @ (Xa.T @ (w * y))
    e = y - Xa @ b
    g, _ = pd.factorize(d["state"])
    we, n_g = w * e, g.max() + 1  # state score totals, column by column (same sums as np.add.at, less memory)
    S = np.column_stack([np.bincount(g, weights=Xa[:, j] * we, minlength=n_g) for j in range(len(cols))])
    a = np.zeros(len(cols))
    for k in spec.estimand_years:
        a[cols.index(f"pi_{k}")] = 1 / len(spec.estimand_years)
    rng = np.random.default_rng(seed)
    webb = np.array([-np.sqrt(1.5), -1, -np.sqrt(0.5), np.sqrt(0.5), 1, np.sqrt(1.5)])
    V = rng.choice(webb, size=(n_boot, S.shape[0]))
    draws = float(a @ b) + (V @ S) @ A_inv.T @ a
    est = float(a @ b)
    return Estimate(est, float(np.std(draws, ddof=1))), {
        "ci95": tuple(np.percentile(draws, [2.5, 97.5])),
        "clusters": S.shape[0],
    }


def reweight_group_composition(
    df: pd.DataFrame, group: str = "diabetes", ref_years=(2017, 2018, 2019), cells=("age_group", "sex")
) -> pd.DataFrame:
    """Q24: reweight the group (D = 1) in every year to its own 2017-2019 composition (age group x sex);
    the other respondents keep their weights."""
    out = df.copy()
    D = out[group] == 1
    # missing cell values form their own cell, as in h3_quantiles (pandas 3 keeps NaN through astype(str))
    key = out[list(cells)].astype(str).fillna("missing").agg("|".join, axis=1)
    ref = out[D & out["year"].isin(ref_years)].groupby(key[D & out["year"].isin(ref_years)])["wt"].sum()
    ref = ref / ref.sum()
    for y in out.loc[D, "year"].unique():
        m = D & (out["year"] == y)
        own = out[m].groupby(key[m])["wt"].sum()
        own = own / own.sum()
        f = key[m].map(ref).fillna(0.0) / key[m].map(own)
        out.loc[m, "wt"] = out.loc[m, "wt"] * f.to_numpy()
    return out
