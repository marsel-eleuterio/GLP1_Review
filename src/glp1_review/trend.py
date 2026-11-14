"""Counterfactual trend (pre-registration Q19, H1 Stage 2), shared by H1, H3, NC1 and NC2.

For each draw of a yearly series, a trend is fitted to the pre-period on the chosen scale (logit for
prevalences, identity for BMI quantiles or height) and projected to the post-period with the closed-form
posterior predictive of a Bayesian linear regression under the reference prior: Student-t with n - p degrees
of freedom (7 for a linear trend on 2011-2019), location = OLS prediction and scale = s * sqrt(1 + x0'(X'X)^-1 x0).
The departure is observed minus projected, on the original scale.

Alternative counterfactuals (Q24): other pre-windows, a quadratic trend, and "level" (the last pre-break level,
2022 by default, continued at the pre-period slope).
"""

from dataclasses import dataclass

import numpy as np
from scipy import stats

PRE = tuple(range(2011, 2020))
POST = (2023, 2024, 2025)


def logit(p):
    p = np.asarray(p, dtype=float)
    return np.log(p / (1 - p))


def expit(x):
    return 1 / (1 + np.exp(-np.asarray(x, dtype=float)))


@dataclass
class Departures:
    years: tuple[int, ...]
    draws: np.ndarray  # (n_draws, n_post) departures, original scale (x100 if percent=True)

    def summary(self, prob: float = 0.95) -> dict[int, tuple[float, float, float]]:
        lo, hi = (1 - prob) / 2 * 100, (1 + prob) / 2 * 100
        q = np.percentile(self.draws, [50, lo, hi], axis=0)
        return {y: (q[0, i], q[1, i], q[2, i]) for i, y in enumerate(self.years)}

    def mean_over_post(self) -> np.ndarray:
        return self.draws.mean(axis=1)

    def prob_less(self, year_a: int, year_b: int) -> float:
        """P(D_a < D_b), e.g. P(D_2025 < D_2023)."""
        a, b = self.years.index(year_a), self.years.index(year_b)
        return float(np.mean(self.draws[:, a] < self.draws[:, b]))


def _design(t: np.ndarray, form: str) -> np.ndarray:
    tc = t - 2015.0
    if form in ("linear", "level"):
        return np.column_stack([np.ones_like(tc), tc])
    if form == "quadratic":
        return np.column_stack([np.ones_like(tc), tc, tc**2])
    raise ValueError(f"unknown form {form!r}")


def departures(
    series: np.ndarray,
    years: list[int] | tuple[int, ...],
    pre: tuple[int, ...] = PRE,
    post: tuple[int, ...] = POST,
    scale: str = "logit",
    form: str = "linear",
    level_year: int = 2022,
    predictive: bool = True,
    percent: bool = True,
    rng: np.random.Generator | None = None,
) -> Departures:
    """Departures D_t = observed_t - projected_t for each draw.

    series: (n_draws, n_years) or (n_years,) values on the original scale (prevalence as a proportion when
    scale="logit"). predictive=False uses the predictive mean instead of a Student-t draw (for point estimates).
    percent=True multiplies departures by 100 (percentage points) when scale="logit".
    """
    rng = rng or np.random.default_rng(20261114)
    y = np.atleast_2d(np.asarray(series, dtype=float))
    years = list(years)
    ip = [years.index(t) for t in pre]
    iq = [years.index(t) for t in post]
    f = logit if scale == "logit" else (lambda v: np.asarray(v, dtype=float))
    finv = expit if scale == "logit" else (lambda v: v)
    yt = f(y)

    X = _design(np.array(pre, dtype=float), form)
    X0 = _design(np.array(post, dtype=float), form)
    n, k = X.shape
    dof = n - k
    XtX_inv = np.linalg.inv(X.T @ X)
    coef = yt[:, ip] @ X @ XtX_inv  # (n_draws, k) OLS for every draw at once
    resid = yt[:, ip] - coef @ X.T
    s = np.sqrt((resid**2).sum(axis=1) / dof)  # (n_draws,)
    h = np.einsum("ij,jk,ik->i", X0, XtX_inv, X0)  # leverage of each post year
    loc = coef @ X0.T  # (n_draws, n_post)
    if form == "level":
        il = years.index(level_year)
        loc = yt[:, [il]] + coef[:, [1]] * (np.array(post, dtype=float) - level_year)
        X_l = _design(np.array([level_year], dtype=float), "linear")
        d0 = X0 - X_l  # only the slope term matters
        h = np.einsum("ij,jk,ik->i", d0, XtX_inv, d0)
    scl = s[:, None] * np.sqrt(1 + h)[None, :]
    if predictive:
        proj = loc + scl * stats.t.rvs(dof, size=loc.shape, random_state=rng)
    else:
        proj = loc
    d = y[:, iq] - finv(proj)
    if percent and scale == "logit":
        d = 100 * d
    return Departures(tuple(post), d)
