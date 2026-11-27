"""Descriptive quantities needed only by the preprint figures (paper/figures), derived after the full run.

Nothing here changes an estimate or a classification. Each function reuses the registered building blocks and
returns a by-product that the pipeline computed but did not save:

- `nc1_yearly`: NC1 height departure for every year (the registered NC1 keeps only the 2023-2025 mean). Same
  composition adjustment, sexes, trend and Rao-Wu bootstrap as `h3_quantiles.fit_nc1`; pre-period years show the
  residual from the 2011-2019 line, 2020-2025 the departure from its projection. Its 2023-2025 mean reproduces the
  registered NC1 point estimate.
- `h4_event_and_states`: H4 event-study coefficients with their cluster-robust SEs (the run saved the coefficients
  only) and each state's 2023-2025 departure from its own 2011-2019 line (computed for the tercile contrast, not
  saved).
- `h5_draws`: all draws of the H5 microsimulation (the run saved the 5th, 50th and 95th percentiles).
"""

import numpy as np
import pandas as pd

from glp1_review import h3_quantiles, h4_states, h5_microsim, prepare, trend
from glp1_review.survey import psu_codes, rao_wu_multipliers

ALL_POST = (2020, 2021, 2022, 2023, 2024, 2025)


def _yearly_departures(m: np.ndarray, years: list, predictive: bool, rng) -> np.ndarray:
    """Residuals from the 2011-2019 line in the pre-period; departures from its projection afterwards."""
    years = list(years)
    ip = [years.index(t) for t in trend.PRE]
    b = np.polyfit(np.array(trend.PRE, float) - 2015, m[ip], 1)
    out = m - np.polyval(b, np.array(years, float) - 2015)
    post = tuple(t for t in ALL_POST if t in years)
    d = trend.departures(m, years, post=post, scale="identity", predictive=predictive, rng=rng).draws[0]
    for t, v in zip(post, d, strict=True):
        out[years.index(t)] = v
    return out


def nc1_yearly(
    df: pd.DataFrame, n_rep: int = 500, seed: int = 20261115, ages=("25-34", "35-44", "45-54", "55-64")
) -> pd.DataFrame:
    """Columns: departure (cm, mean of the two sexes), se (SD of the bootstrap replicates), by year."""
    base = df[df["age_group"].isin(ages) & df["htm"].notna()].assign(height_cm=lambda x: 100 * x["htm"])
    rng = np.random.default_rng(seed)
    Ps = {sex: h3_quantiles.prepare(g, "height_cm") for sex, g in base.groupby("sex")}
    years = list(next(iter(Ps.values())).years)
    assert all(list(P.years) == years for P in Ps.values())
    point = np.mean(
        [_yearly_departures(P.series(P.dfl(P.w), "mean")[0], years, False, rng) for P in Ps.values()], axis=0
    )
    keys = {sex: h3_quantiles._psu_keys(P) for sex, P in Ps.items()}
    codes, psu_stratum = psu_codes(
        np.concatenate([k[0] for k in keys.values()]), np.concatenate([k[1] for k in keys.values()])
    )
    offsets = np.cumsum([0] + [len(P.w) for P in Ps.values()])
    reps = []
    for start in range(0, n_rep, 25):
        R = min(25, n_rep - start)
        mult = rao_wu_multipliers(psu_stratum, R, rng)
        for r in range(R):
            vals = []
            for i, P in enumerate(Ps.values()):
                w = P.dfl(P.w * mult[codes[offsets[i] : offsets[i + 1]], r])
                vals.append(_yearly_departures(P.series(w, "mean")[0], years, True, rng))
            reps.append(np.mean(vals, axis=0))
    se = np.std(np.array(reps), axis=0, ddof=1)
    return pd.DataFrame({"departure": point, "se": se}, index=pd.Index(years, name="year"))


def h4_event_and_states(b: pd.DataFrame, E: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """E: posterior-mean exposure by state (h4_exposure.csv, column E). Returns (beta, se by year) and the
    states' 2023-2025 departures (pp)."""
    Y = prepare.h4_outcome(b)
    Y = Y[Y["state"].isin(E.index)]
    es = h4_states.event_study(Y, E)
    betas = pd.DataFrame({"beta": es.beta, "se": np.sqrt(np.diag(es.cov))})
    betas.index.name = "year"
    return betas, h4_states.state_departures(Y).rename("departure")


def h5_draws(
    b: pd.DataFrame, src: prepare.Sources, published_rate: float, n_draws: int, seed: int
) -> np.ndarray:
    """Same inputs and parameters as run.step_h5."""
    inp = prepare.h5_inputs(b, src)
    p = h5_microsim.Params(
        meps_rate=inp["meps_rate"], published_rate=published_rate, n_draws=n_draws, seed=seed
    )
    return h5_microsim.simulate(inp["bmi"], inp["diab"], inp["w"], inp["use_prob"], p)
