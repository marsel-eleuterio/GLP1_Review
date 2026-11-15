"""H3 (BMI upper-tail signature) and NC1 (height negative control), pre-registration Q19.

Composition adjustment (DiNardo-Fortin-Lemieux): each year's sample is reweighted to the 2017-2019 joint distribution
of age group x sex x race and ethnicity x education. With these four categorical covariates the logistic model of
"reference years vs year t" is taken as saturated (all 6 x 2 x 5 x 4 = 240 cells), whose fitted odds are exactly the
ratio of weighted cell shares, so the DFL factor is share_ref(cell) / share_t(cell). Cells absent from the reference
period get weight zero.

H3: for each year and q in {0.10, 0.25, 0.50, 0.75, 0.90, 0.95}, the reweighted weighted quantile of BMI. Each series
goes through the H1 Stage-2 trend procedure (identity scale), giving departures D_q,t. Estimand
C = mean over 2023-2025 of (D_0.90,t - D_0.50,t). Uncertainty: Rao-Wu rescaled bootstrap of PSUs within strata and
year (500 replicates), repeating reweighting, quantiles and the trend projection (with its Student-t predictive draw,
so year-level shocks are included, consistent with H2) in every replicate. SE = SD of the replicate estimates.

NC1: mean self-reported height (HTM4, cm) of adults 25-64 by sex, composition-adjusted in the same way (the sex
cell is fixed within each series), through the same trend procedure. Estimand: mean departure in 2023-2025, averaged
over the two sexes; each sex is also reported. Equivalence margin +-0.5 cm (Q22).
"""

import numpy as np
import pandas as pd

from glp1_review import trend
from glp1_review.decision import Estimate
from glp1_review.survey import rao_wu_weights

QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
REF_YEARS = (2017, 2018, 2019)
CELL_VARS = ("age_group", "sex", "race", "educ")


def cell_key(df: pd.DataFrame, cell_vars=CELL_VARS) -> pd.Series:
    return df[list(cell_vars)].astype(str).agg("|".join, axis=1)


def dfl_factor(year: np.ndarray, cell: np.ndarray, w: np.ndarray, ref_years=REF_YEARS) -> np.ndarray:
    """Multiplicative DFL factor per observation: share of its cell in the reference years / share in its own year."""
    d = pd.DataFrame({"year": year, "cell": cell, "w": w})
    ref = d[d["year"].isin(ref_years)].groupby("cell")["w"].sum()
    ref = ref / ref.sum()
    own = d.groupby(["year", "cell"])["w"].sum()
    own = own / own.groupby(level=0).transform("sum")
    num = d["cell"].map(ref).fillna(0.0).to_numpy()
    den = own.loc[list(zip(d["year"], d["cell"], strict=True))].to_numpy()
    return num / den


def _sorted_quantiles(x_sorted: np.ndarray, w_sorted: np.ndarray, qs) -> np.ndarray:
    """Weighted quantiles for one or many weight columns (x already sorted). w_sorted: (n,) or (n, R)."""
    W = w_sorted if w_sorted.ndim == 2 else w_sorted[:, None]
    cw = np.cumsum(W, axis=0)
    p = (cw - 0.5 * W) / cw[-1]
    out = np.empty((len(qs), W.shape[1]))
    for r in range(W.shape[1]):
        out[:, r] = np.interp(qs, p[:, r], x_sorted)
    return out


def _series(df: pd.DataFrame, value: str, stat: str, qs, w_col: str, years) -> np.ndarray:
    """(n_stats, n_years) yearly quantiles (stat='quantile') or means (stat='mean') with weights w_col."""
    out = []
    for y in years:
        g = df[df["year"] == y]
        x, w = g[value].to_numpy(float), g[w_col].to_numpy(float)
        if stat == "mean":
            out.append([np.sum(w * x) / np.sum(w)])
        else:
            o = np.argsort(x)
            out.append(_sorted_quantiles(x[o], w[o], qs)[:, 0])
    return np.array(out).T


def _prepare(df: pd.DataFrame, value: str, cell_vars=CELL_VARS) -> pd.DataFrame:
    d = df[df[value].notna() & df["wt"].notna()].copy()
    d["cell"] = cell_key(d, cell_vars)
    d["w_dfl"] = d["wt"] * dfl_factor(d["year"].to_numpy(), d["cell"].to_numpy(), d["wt"].to_numpy(float))
    return d


def _contrast(qseries: np.ndarray, years, qs, rng, predictive: bool) -> float:
    i90, i50 = qs.index(0.90), qs.index(0.50)
    d90 = trend.departures(qseries[i90], years, scale="identity", predictive=predictive, rng=rng).draws[0]
    d50 = trend.departures(qseries[i50], years, scale="identity", predictive=predictive, rng=rng).draws[0]
    return float(np.mean(d90 - d50))


def _bootstrap(d: pd.DataFrame, years, n_rep: int, rng, stat_fn, chunk: int = 50) -> np.ndarray:
    """Replicate estimates. Replicate weights are drawn year by year (strata nested in year) and the DFL factor is
    recomputed from the replicate weights."""
    reps = []
    by_year = {y: d[d["year"] == y] for y in years}
    for start in range(0, n_rep, chunk):
        R = min(chunk, n_rep - start)
        rw = {
            y: rao_wu_weights(g["strat"], g["psu"], g["wt"].to_numpy(float), R, rng)
            for y, g in by_year.items()
        }
        for r in range(R):
            parts = []
            for y, g in by_year.items():
                parts.append(g.assign(wt=rw[y][:, r]))
            rep = pd.concat(parts)
            rep = rep[rep["wt"] > 0]
            rep["w_dfl"] = rep["wt"] * dfl_factor(
                rep["year"].to_numpy(), rep["cell"].to_numpy(), rep["wt"].to_numpy()
            )
            reps.append(stat_fn(rep))
    return np.array(reps)


def fit_h3(df: pd.DataFrame, n_rep: int = 500, seed: int = 20261114, qs=QUANTILES) -> tuple[Estimate, dict]:
    """df: year, bmi, wt, strat, psu, age_group, sex, race, educ."""
    years = sorted(df["year"].unique())
    qs = list(qs)
    d = _prepare(df, "bmi")
    q_obs = _series(d, "bmi", "quantile", qs, "w_dfl", years)
    rng = np.random.default_rng(seed)
    c_hat = _contrast(q_obs, years, qs, rng, predictive=False)

    def stat(rep):
        return _contrast(_series(rep, "bmi", "quantile", qs, "w_dfl", years), years, qs, rng, predictive=True)

    reps = _bootstrap(d, years, n_rep, rng, stat)
    deps = {
        q: trend.departures(q_obs[i], years, scale="identity", predictive=False).draws[0]
        for i, q in enumerate(qs)
    }
    return Estimate(c_hat, float(np.std(reps, ddof=1))), {
        "quantiles": pd.DataFrame(q_obs.T, index=years, columns=qs),
        "departures": deps,
        "replicates": reps,
    }


def fit_nc1(
    df: pd.DataFrame, n_rep: int = 500, seed: int = 20261115, ages=("25-34", "35-44", "45-54", "55-64")
) -> tuple[Estimate, dict]:
    """df: year, htm (metres), wt, strat, psu, age_group, sex, race, educ. Adults 25-64 by default (Q19);
    pass all age groups for the Q24 sensitivity."""
    years = sorted(df["year"].unique())
    base = df[df["age_group"].isin(ages)].assign(height_cm=lambda x: 100 * x["htm"])
    rng = np.random.default_rng(seed)
    per_sex, reps_all = {}, []
    for sex, g in base.groupby("sex"):
        d = _prepare(g, "height_cm")
        m = _series(d, "height_cm", "mean", None, "w_dfl", years)[0]
        per_sex[sex] = float(np.mean(trend.departures(m, years, scale="identity", predictive=False).draws[0]))

        def stat(rep):
            mr = _series(rep, "height_cm", "mean", None, "w_dfl", years)[0]
            return float(np.mean(trend.departures(mr, years, scale="identity", rng=rng).draws[0]))

        reps_all.append(_bootstrap(d, years, n_rep, rng, stat))
    est = float(np.mean(list(per_sex.values())))
    reps = np.mean(np.vstack(reps_all), axis=0)
    return Estimate(est, float(np.std(reps, ddof=1))), {"by_sex": per_sex, "replicates": reps}
