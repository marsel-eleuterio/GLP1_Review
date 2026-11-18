"""H1 Stage 1: multilevel regression and post-stratification of adult obesity, one model per year (pre-registration Q19).

    y_c ~ Binomial(n_c, p_c)   (unweighted counts of obese respondents in cell c)
    logit p_c = mu + a_state + a_age + a_sex + a_race + a_educ + a_age x sex
    a_state ~ N(a_division + gamma * z_s, sigma_state)
    mu ~ N(-0.8, 1); gamma ~ N(0, 1); group effects ~ N(0, sigma_g) constrained to sum to zero (ZeroSumNormal),
    sigma_g ~ HalfNormal(1), non-centred; sex as a fixed effect (ZeroSumNormal, sigma 1)
Revised on 2026-11-14 before registration: the first-draft model (unconstrained effects, centred, hierarchical sex)
did not converge on simulated data with any Q23 step; the sum-to-zero constraint removes the joint shift of the
intercept and the effects, and a hierarchical SD for a 2-level factor is not estimable. Sampler: target_accept 0.95.
Cells: state (50 + DC) x age (6) x sex (2) x race and ethnicity (5) x education (4). z_s is the centred logit of the
state's direct weighted estimate in the previous available year (the next available year for the first year of the
series), so states without data in a year (e.g. California in 2025) are predicted from their division and z_s.
Years without the race variable (2015-2016, _IMPRACE absent) drop the race effect and post-stratify over cells
collapsed across race. Post-stratification to ACS 1-year PUMS adult counts gives posterior draws of national prevalence P_t.

Convergence (Q23): R-hat < 1.01, bulk ESS > 400 and no divergent transitions. If a year fails, `fit_year_q23` tries in
order: 2,000 tuning steps; target_accept 0.99; dropping the age x sex interaction; dropping the education effect. Every simplification is recorded. If all fail, the caller falls back to the
composition-adjusted direct series as the primary H1 series.

Stage 2 (departures, millions of adults) is trend.departures(); `national_departures` wraps both.
"""

import numpy as np
import pandas as pd

from glp1_review import trend
from glp1_review.data import AGE6, EDUC4, RACE5, SEX2, STATES

CELL = ["state", "age_group", "sex", "race", "educ"]


def cell_counts(d: pd.DataFrame) -> pd.DataFrame:
    """Unweighted cell counts of respondents with obesity status and complete covariates."""
    keep = d.dropna(subset=["obese", "age_group", "sex", "educ"])
    cols = CELL if keep["race"].notna().any() else [c for c in CELL if c != "race"]
    keep = keep.dropna(subset=cols)
    g = keep.groupby(cols, observed=True)["obese"].agg(y="sum", n="size").reset_index()
    return g


def direct_estimates(d: pd.DataFrame) -> pd.DataFrame:
    """Weighted direct obesity prevalence by state and year (proportions)."""
    v = d.dropna(subset=["obese", "wt"])
    g = v.assign(wy=v["wt"] * v["obese"]).groupby(["year", "state"])[["wy", "wt"]].sum()
    return (g["wy"] / g["wt"]).rename("p").reset_index()


def z_previous(direct: pd.DataFrame, year: int) -> pd.Series:
    """Centred logit of each state's direct estimate in the previous available year (next if none)."""
    out = {}
    for s in STATES:
        ds = direct[direct["state"] == s].set_index("year")["p"]
        prev = ds[ds.index < year]
        nxt = ds[ds.index > year]
        if len(prev):
            out[s] = prev.iloc[-1]
        elif len(nxt):
            out[s] = nxt.iloc[0]
    s = pd.Series(out, dtype=float)
    z = pd.Series(trend.logit(s.to_numpy()), index=s.index)
    return z - z.mean()


def fit_year(
    cells: pd.DataFrame,
    z: pd.Series,
    division: dict,
    seed: int,
    sampler_kwargs=None,
    centred: bool = False,
    zerosum: bool = True,
    sex_fixed: bool = True,
    agesex: bool = True,
    educ: bool = True,
):
    import pymc as pm

    use_race = "race" in cells
    st_idx = {s: i for i, s in enumerate(STATES)}
    divs = sorted(set(division.values()))
    div_of_state = np.array([divs.index(division[s]) for s in STATES])
    zz = z.reindex(STATES).fillna(0.0).to_numpy()
    s_i = cells["state"].map(st_idx).to_numpy()
    a_i = cells["age_group"].map({a: i for i, a in enumerate(AGE6)}).to_numpy()
    x_i = cells["sex"].map({s: i for i, s in enumerate(SEX2)}).to_numpy()
    e_i = cells["educ"].map({e: i for i, e in enumerate(EDUC4)}).to_numpy()
    r_i = cells["race"].map({r: i for i, r in enumerate(RACE5)}).to_numpy() if use_race else None

    kw = {
        "draws": 1000,
        "tune": 1000,
        "chains": 4,
        "target_accept": 0.95,
        "nuts_sampler": "nutpie",
        "progressbar": False,
        "random_seed": seed,
    }
    kw.update(sampler_kwargs or {})

    def group(name, size):
        sd = pm.HalfNormal(f"sd_{name}", 1.0)
        if (
            zerosum
        ):  # N(0, sd) deviations constrained to sum to zero: removes the additive non-identifiability
            if centred:
                return pm.ZeroSumNormal(f"a_{name}", sigma=sd, shape=size)
            raw = pm.ZeroSumNormal(f"raw_{name}", sigma=1.0, shape=size)
            return pm.Deterministic(f"a_{name}", raw * sd)
        if centred:
            return pm.Normal(f"a_{name}", 0.0, sd, shape=size)
        raw = pm.Normal(f"raw_{name}", 0.0, 1.0, shape=size)
        return pm.Deterministic(f"a_{name}", raw * sd)

    with pm.Model() as model:
        mu = pm.Normal("mu", -0.8, 1.0)
        gamma = pm.Normal("gamma", 0.0, 1.0)
        a_div = group("division", len(divs))
        sd_state = pm.HalfNormal("sd_state", 1.0)
        m_state = a_div[div_of_state] + gamma * zz
        if zerosum:
            dev = (
                pm.ZeroSumNormal("dev_state", sigma=sd_state, shape=len(STATES))
                if centred
                else pm.ZeroSumNormal("raw_state", sigma=1.0, shape=len(STATES)) * sd_state
            )
            a_state = pm.Deterministic("a_state", m_state + dev)
        elif centred:
            a_state = pm.Normal("a_state", m_state, sd_state, shape=len(STATES))
        else:
            raw_state = pm.Normal("raw_state", 0.0, 1.0, shape=len(STATES))
            a_state = pm.Deterministic("a_state", m_state + raw_state * sd_state)
        a_age = group("age", 6)
        # a hierarchical SD for a 2-level factor is barely identified and creates a funnel; fixed effect instead
        a_sex = pm.ZeroSumNormal("a_sex", sigma=1.0, shape=2) if sex_fixed else group("sex", 2)
        eta = mu + a_state[s_i] + a_age[a_i] + a_sex[x_i]
        if educ:
            eta = eta + group("educ", 4)[e_i]
        if agesex:
            eta = eta + group("agesex", 12)[a_i * 2 + x_i]
        if use_race:
            a_race = group("race", 5)
            eta = eta + a_race[r_i]
        pm.Binomial("y", n=cells["n"].to_numpy(), logit_p=eta, observed=cells["y"].to_numpy())
        idata = pm.sample(**kw)
    return idata, model


def _dataset(node):
    """xarray Dataset from an InferenceData group (PyMC >= 6 returns DataTree nodes)."""
    return node.to_dataset() if hasattr(node, "to_dataset") else node


def converged(idata) -> dict:
    import arviz as az

    # every sampled and derived parameter (group effects, raw deviations, SDs), as Q23 requires
    s = az.summary(idata, kind="diagnostics")
    ss = _dataset(idata.sample_stats)
    div = int(ss["diverging"].sum()) if "diverging" in ss else 0
    info = {
        "max_rhat": float(s["r_hat"].max()),
        "min_ess_bulk": float(s["ess_bulk"].min()),
        "divergences": div,
    }
    info["ok"] = info["max_rhat"] < 1.01 and info["min_ess_bulk"] > 400 and div == 0
    return info


Q23_STEPS = [
    ("primary", {}),
    ("2,000 tuning steps", {"tune": 2000}),
    ("target_accept 0.99", {"tune": 2000, "target_accept": 0.99}),
    ("drop age x sex", {"tune": 2000, "target_accept": 0.99, "agesex": False}),
    ("drop education", {"tune": 2000, "target_accept": 0.99, "agesex": False, "educ": False}),
]


def fit_year_q23(cells, z, division, seed, sampler_kwargs=None):
    """Fit with the Q23 fallback sequence. Returns (idata, step label, diagnostics, model options) or raises
    RuntimeError if every step fails (the caller then uses the direct series)."""
    log = []
    for label, opts in Q23_STEPS:
        model_opts = {k: opts[k] for k in ("centred", "agesex", "educ") if k in opts}
        skw = dict(sampler_kwargs or {})
        skw.update({k: opts[k] for k in ("target_accept", "tune") if k in opts})
        idata, _ = fit_year(cells, z, division, seed, skw, **model_opts)
        diag = converged(idata)
        log.append((label, diag))
        if diag["ok"]:
            return idata, label, log, model_opts
    raise RuntimeError(f"MRP did not converge after every Q23 step: {log}")


def composition_adjusted_series(Y: pd.DataFrame, weights: pd.Series) -> pd.Series:
    """Q23 fallback, as in the pilot: weighted two-way fixed effects (state + year) on the direct state estimates,
    national value of year t = weighted mean over all states of (state effect + year effect), so states missing in a
    year are filled from their own level. Y: state, year, y (any scale); weights: by state (adult population)."""
    d = Y.dropna(subset=["y"])
    d = d[d["state"].isin(weights.index)]
    states = sorted(d["state"].unique())
    years = sorted(d["year"].unique())
    si = {s: i for i, s in enumerate(states)}
    yi = {y: i for i, y in enumerate(years)}
    X = np.zeros((len(d), len(states) + len(years) - 1))
    X[np.arange(len(d)), d["state"].map(si).to_numpy()] = 1.0
    t = d["year"].map(yi).to_numpy()
    rows = np.flatnonzero(t > 0)
    X[rows, len(states) + t[rows] - 1] = 1.0
    w = weights.reindex(d["state"]).to_numpy(float)
    sw = np.sqrt(w)
    beta = np.linalg.lstsq(X * sw[:, None], d["y"].to_numpy(float) * sw, rcond=None)[0]
    alpha, tau = beta[: len(states)], np.r_[0.0, beta[len(states) :]]
    ws = weights.reindex(states).to_numpy(float)
    level = float(np.sum(ws * alpha) / ws.sum())
    return pd.Series(level + tau, index=years)


def poststratify(
    idata,
    frame: pd.DataFrame,
    use_race: bool,
    n_draws: int | None = None,
    seed: int = 0,
    agesex: bool = True,
    educ: bool = True,
) -> np.ndarray:
    """National prevalence draws. frame: ACS cells with state_fips, age, sex, race, educ, pop."""
    post = _dataset(idata.posterior).stack(s=("chain", "draw"))
    f = frame.rename(columns={"state_fips": "state", "age": "age_group"})
    if not use_race:
        f = f.groupby(["state", "age_group", "sex", "educ"], as_index=False)["pop"].sum()
    st = f["state"].map({s: i for i, s in enumerate(STATES)}).to_numpy()
    ai = f["age_group"].map({a: i for i, a in enumerate(AGE6)}).to_numpy()
    xi = f["sex"].map({s: i for i, s in enumerate(SEX2)}).to_numpy()
    ei = f["educ"].map({e: i for i, e in enumerate(EDUC4)}).to_numpy()
    eta = (
        post["mu"].to_numpy()[None, :]
        + post["a_state"].to_numpy()[st]
        + post["a_age"].to_numpy()[ai]
        + post["a_sex"].to_numpy()[xi]
    )
    if educ:
        eta = eta + post["a_educ"].to_numpy()[ei]
    if agesex:
        eta = eta + post["a_agesex"].to_numpy()[ai * 2 + xi]
    if use_race:
        ri = f["race"].map({r: i for i, r in enumerate(RACE5)}).to_numpy()
        eta = eta + post["a_race"].to_numpy()[ri]
    w = f["pop"].to_numpy() / f["pop"].sum()
    P = (w[:, None] * trend.expit(eta)).sum(axis=0)
    if n_draws is not None and n_draws < len(P):
        P = np.random.default_rng(seed).choice(P, n_draws, replace=False)
    return P


def national_departures(
    P: dict[int, np.ndarray], adults_millions: dict[int, float] | None = None, **trend_kwargs
) -> dict:
    """Stage 2. P: year -> draws of national prevalence (same number of draws per year; independent yearly fits are
    paired by draw index). Returns departures in pp, in millions of adults, and P(D_2025 < D_2023)."""
    years = sorted(P)
    n = min(len(v) for v in P.values())
    M = np.column_stack([np.asarray(P[y])[:n] for y in years])
    dep = trend.departures(M, years, **trend_kwargs)
    p = dep.prob_less(2025, 2023) if {2023, 2025} <= set(dep.years) else None
    out = {"departures": dep, "summary_pp": dep.summary(), "p_2025_below_2023": p}
    if adults_millions:
        mill = dep.draws / 100 * np.array([adults_millions[y] for y in dep.years])[None, :]
        out["summary_millions"] = trend.Departures(dep.years, mill).summary()
    return out
