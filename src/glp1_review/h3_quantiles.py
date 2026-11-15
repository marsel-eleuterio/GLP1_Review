"""H3 (BMI upper-tail signature) and NC1 (height negative control), pre-registration Q19.

Composition adjustment (DiNardo-Fortin-Lemieux): each year's sample is reweighted to the 2017-2019 joint distribution
of age group x sex x race and ethnicity x education. With these four categorical covariates the logistic model of
"reference years vs year t" is taken as saturated (all 6 x 2 x 5 x 4 = 240 cells), whose fitted odds are exactly the
ratio of weighted cell shares, so the DFL factor is share_ref(cell) / share_t(cell). Cells absent from the reference
period get weight zero. In years where a cell variable is not available (race and ethnicity in 2015-2016, recorded
as "Not available"), the cells drop that variable and the reference shares are computed on the same reduced cells.

H3: for each year and q in {0.10, 0.25, 0.50, 0.75, 0.90, 0.95}, the reweighted weighted quantile of BMI. Each series
goes through the H1 Stage-2 trend procedure (identity scale), giving departures D_q,t. Estimand
C = mean over 2023-2025 of (D_0.90,t - D_0.50,t). Uncertainty: Rao-Wu rescaled bootstrap of PSUs within strata and
year (500 replicates), repeating reweighting, quantiles and the trend projection (with its Student-t predictive draw,
so year-level shocks are included, consistent with H2) in every replicate. SE = SD of the replicate estimates.

NC1: mean self-reported height (HTM4, cm) of adults 25-64 by sex, composition-adjusted in the same way (the sex
cell is fixed within each series), through the same trend procedure. Estimand: mean departure in 2023-2025, averaged
over the two sexes; each sex is also reported. Equivalence margin +-0.5 cm (Q22).

Implementation: cells are integer-coded once and rows are sorted by (year, value) once, so each bootstrap replicate
only recomputes weights, the DFL factor (bincount) and cumulative sums.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from glp1_review import trend
from glp1_review.decision import Estimate
from glp1_review.survey import rao_wu_weights

QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
REF_YEARS = (2017, 2018, 2019)
CELL_VARS = ("age_group", "sex", "race", "educ")
NOT_AVAILABLE = "Not available"


@dataclass
class Prepared:
    """Rows sorted by (year, value); one integer cell code per row for each set of available cell variables."""

    years: list
    bounds: dict  # year -> (start, end) row slice
    x: np.ndarray  # value, sorted within year
    w: np.ndarray  # survey weight
    strat: np.ndarray
    psu: np.ndarray
    codes: np.ndarray  # (n_sets, n) cell codes
    n_cells: list  # number of cells per set
    set_of_year: dict  # year -> index of its variable set
    ref_mask: np.ndarray

    def dfl(self, w: np.ndarray) -> np.ndarray:
        out = np.zeros_like(w)
        ref = []
        for s, k in enumerate(self.n_cells):
            r = np.bincount(self.codes[s][self.ref_mask], weights=w[self.ref_mask], minlength=k)
            ref.append(r / r.sum())
        for y, (a, b) in self.bounds.items():
            s = self.set_of_year[y]
            c = self.codes[s][a:b]
            own = np.bincount(c, weights=w[a:b], minlength=self.n_cells[s])
            own = own / own.sum()
            with np.errstate(divide="ignore", invalid="ignore"):
                f = np.where(own[c] > 0, ref[s][c] / own[c], 0.0)
            out[a:b] = w[a:b] * f
        return out

    def series(self, w: np.ndarray, stat: str, qs=None) -> np.ndarray:
        """(n_stats, n_years): weighted quantiles (stat='quantile') or the weighted mean (stat='mean')."""
        cols = []
        for y in self.years:
            a, b = self.bounds[y]
            ww, xx = w[a:b], self.x[a:b]
            if stat == "mean":
                cols.append([np.sum(ww * xx) / np.sum(ww)])
            else:
                cw = np.cumsum(ww)
                p = (cw - 0.5 * ww) / cw[-1]
                cols.append(np.interp(qs, p, xx))
        return np.array(cols).T


def _available(g: pd.DataFrame, cell_vars) -> tuple:
    return tuple(v for v in cell_vars if not (g[v].isna() | (g[v].astype(str) == NOT_AVAILABLE)).all())


def prepare(df: pd.DataFrame, value: str, cell_vars=CELL_VARS, ref_years=REF_YEARS) -> Prepared:
    d = df[df[value].notna() & df["wt"].notna() & (df["wt"] > 0)].sort_values(
        ["year", value], kind="mergesort"
    )
    years = sorted(d["year"].unique())
    avail = {y: _available(g, cell_vars) for y, g in d.groupby("year")}
    sets = sorted(set(avail.values()), key=len, reverse=True)
    codes, n_cells = [], []
    for s in sets:
        key = d[list(s)].astype(str).fillna("missing").agg("|".join, axis=1)
        c, u = pd.factorize(key)
        codes.append(c)
        n_cells.append(len(u))
    yv = d["year"].to_numpy()
    bounds = {}
    for y in years:
        idx = np.flatnonzero(yv == y)
        bounds[y] = (int(idx[0]), int(idx[-1]) + 1)
    return Prepared(
        years=years,
        bounds=bounds,
        x=d[value].to_numpy(float),
        w=d["wt"].to_numpy(float),
        strat=d["strat"].to_numpy(),
        psu=d["psu"].to_numpy(),
        codes=np.vstack(codes),
        n_cells=n_cells,
        set_of_year={y: sets.index(avail[y]) for y in years},
        ref_mask=np.isin(yv, ref_years),
    )


def bootstrap(P: Prepared, n_rep: int, rng, stat_fn, chunk: int = 25) -> np.ndarray:
    """Replicate estimates. Rao-Wu weights are drawn year by year (strata nested in year); the DFL factor is
    recomputed from the replicate weights; stat_fn receives the reweighted replicate weights."""
    reps = []
    for start in range(0, n_rep, chunk):
        R = min(chunk, n_rep - start)
        W = np.empty((len(P.w), R))
        for _y, (a, b) in P.bounds.items():
            W[a:b] = rao_wu_weights(P.strat[a:b], P.psu[a:b], P.w[a:b], R, rng)
        for r in range(R):
            reps.append(stat_fn(P.dfl(W[:, r])))
    return np.array(reps)


def _contrast(qseries: np.ndarray, years, qs, rng, predictive: bool) -> float:
    i90, i50 = qs.index(0.90), qs.index(0.50)
    d90 = trend.departures(qseries[i90], years, scale="identity", predictive=predictive, rng=rng).draws[0]
    d50 = trend.departures(qseries[i50], years, scale="identity", predictive=predictive, rng=rng).draws[0]
    return float(np.mean(d90 - d50))


def fit_h3(df: pd.DataFrame, n_rep: int = 500, seed: int = 20261114, qs=QUANTILES) -> tuple[Estimate, dict]:
    """df: year, bmi, wt, strat, psu, age_group, sex, race, educ."""
    qs = list(qs)
    P = prepare(df, "bmi")
    years = P.years
    q_obs = P.series(P.dfl(P.w), "quantile", qs)
    rng = np.random.default_rng(seed)
    c_hat = _contrast(q_obs, years, qs, rng, predictive=False)
    reps = bootstrap(
        P, n_rep, rng, lambda w: _contrast(P.series(w, "quantile", qs), years, qs, rng, predictive=True)
    )
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
    base = df[df["age_group"].isin(ages)].assign(height_cm=lambda x: 100 * x["htm"])
    rng = np.random.default_rng(seed)
    per_sex, reps_all = {}, []
    for sex, g in base.groupby("sex"):
        P = prepare(g, "height_cm")
        years = P.years
        m = P.series(P.dfl(P.w), "mean")[0]
        per_sex[sex] = float(np.mean(trend.departures(m, years, scale="identity", predictive=False).draws[0]))

        def stat(w, P=P, years=years):
            mr = P.series(w, "mean")[0]
            return float(np.mean(trend.departures(mr, years, scale="identity", rng=rng).draws[0]))

        reps_all.append(bootstrap(P, n_rep, rng, stat))
    est = float(np.mean(list(per_sex.values())))
    reps = np.mean(np.vstack(reps_all), axis=0)
    return Estimate(est, float(np.std(reps, ddof=1))), {"by_sex": per_sex, "replicates": reps}
