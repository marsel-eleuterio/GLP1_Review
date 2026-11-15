"""Multiple imputation of BRFSS BMI (pre-registration Q14, sensitivity).

Within each year, BMI is imputed by predictive mean matching from a linear model of log BMI on age group x sex,
race and ethnicity (where available), education, income, state, diagnosed diabetes, self-rated general health and,
when reported, height. Proper imputation: for each of the M imputations the coefficients are drawn from their
posterior (sigma^2 from a scaled inverse chi-square, beta | sigma^2 normal); each missing value takes the observed
BMI of one of the k = 5 donors whose predicted values are closest to its own draw-based prediction. Respondents with
a missing covariate other than height keep a missing BMI. Only BMI is imputed (the chained equations of Q14 reduce
to one equation because the other covariates are used as observed).

`imputations` yields one completed data set at a time, so the 20 copies are never held in memory together.
"""

from collections.abc import Iterator

import numpy as np
import pandas as pd

COVARS = ["age_group", "sex", "race", "educ", "income", "state", "diabetes", "genhlth"]


def _design(d: pd.DataFrame, with_height: bool) -> np.ndarray:
    parts = [
        pd.get_dummies(d[c].astype(str), prefix=c, drop_first=True, dtype=float)
        for c in COVARS
        if d[c].nunique() > 1
    ]
    X = pd.concat(parts, axis=1)
    X.insert(0, "const", 1.0)
    if with_height:
        h = d["htm"].to_numpy(float)
        X["htm"], X["htm2"] = h - 1.7, (h - 1.7) ** 2
    return X.to_numpy()


def _pmm(X_obs, y_obs, X_mis, rng, k=5) -> np.ndarray:
    n, p = X_obs.shape
    XtX_inv = np.linalg.pinv(X_obs.T @ X_obs)
    b = XtX_inv @ X_obs.T @ y_obs
    resid = y_obs - X_obs @ b
    sigma2 = float(resid @ resid) / rng.chisquare(n - p)
    L = np.linalg.cholesky(sigma2 * XtX_inv + 1e-12 * np.eye(p))
    b_star = b + L @ rng.standard_normal(p)
    pred_obs = X_obs @ b
    pred_mis = X_mis @ b_star
    order = np.argsort(pred_obs)
    sorted_pred = pred_obs[order]
    pos = np.searchsorted(sorted_pred, pred_mis)
    pick = np.clip(pos + rng.integers(-k // 2, k - k // 2, size=len(pos)), 0, len(order) - 1)
    return y_obs[order[pick]]


def imputations(b: pd.DataFrame, m: int = 20, seed: int = 20261114) -> Iterator[pd.DataFrame]:
    """Yield m completed copies of b (bmi filled where possible; obese recomputed)."""
    rng = np.random.default_rng(seed)
    complete = b[COVARS].notna().all(axis=1) & b["wt"].notna()
    for _ in range(m):
        out = b.copy()
        for _y, g in b[complete].groupby("year"):
            obs = g["bmi"].notna()
            mis = ~obs
            if not mis.any():
                continue
            logb = np.log(g.loc[obs, "bmi"].to_numpy(float))
            for with_h in (True, False):
                hm = g["htm"].notna() if with_h else g["htm"].isna()
                tgt = mis & hm
                if not tgt.any():
                    continue
                donors = obs & (g["htm"].notna() if with_h else True)
                X_all = _design(g, with_h if with_h else False)
                X_obs = X_all[donors.to_numpy()]
                y_obs = np.log(g.loc[donors, "bmi"].to_numpy(float)) if with_h else logb
                imp = _pmm(X_obs, y_obs, X_all[tgt.to_numpy()], rng)
                out.loc[tgt[tgt].index, "bmi"] = np.exp(imp)
        filled = out["bmi"].notna() & b["bmi"].isna()
        out.loc[filled, "obese"] = (out.loc[filled, "bmi"] >= 30).astype(float)
        yield out


def rubin(estimates, variances) -> tuple[float, float, float]:
    """Pooled estimate, total SE and Barnard-Rubin-free large-sample df (Rubin 1987)."""
    q = np.asarray(estimates, float)
    u = np.asarray(variances, float)
    m = len(q)
    qbar, ubar, bvar = q.mean(), u.mean(), q.var(ddof=1) if m > 1 else 0.0
    t = ubar + (1 + 1 / m) * bvar
    r = (1 + 1 / m) * bvar / ubar if ubar > 0 else np.inf
    df = (m - 1) * (1 + 1 / r) ** 2 if r > 0 else np.inf
    return float(qbar), float(np.sqrt(t)), float(df)
