"""Q24 robustness and sensitivity analyses. Each function returns rows
{hypothesis, variant, estimate, se, lo, hi, note}; `run.step_q24` writes them to q24.csv.

Covered here: pandemic years, balanced panel of states, alternative reference compositions (H3), missing BMI
(trend in the share missing; multiple imputation), interview mode (cell vs landline), and the hypothesis-specific
lists for H2, H3, H4, H5, H6 and NC1. The counterfactual-trend alternatives of H1 are computed in `run.step_h1`.

Not computed here, pending the original articles (see the decision log): the external counterfactuals (Ward et al.
2019; DeCleene et al. 2026) and the NHANES-calibrated self-report correction (Ward et al. 2019).
"""

import numpy as np
import pandas as pd

from glp1_review import h2_tripdiff as h2
from glp1_review import h3_quantiles as h3
from glp1_review import h4_states as h4
from glp1_review import h5_microsim as h5
from glp1_review import h6_panel as h6
from glp1_review import mi, trend
from glp1_review.decision import Estimate, h5_compatibility

PANDEMIC = (2020, 2021)
H4_TOP4 = ("WV", "KY", "LA", "OK")


def _row(h, variant, est=None, se=None, lo=None, hi=None, note=""):
    if isinstance(est, Estimate):
        e = est
        est, se = e.est, e.se
        q = e.q(0.975)
        lo, hi = (e.est - q * e.se, e.est + q * e.se) if lo is None else (lo, hi)
    return {"hypothesis": h, "variant": variant, "estimate": est, "se": se, "lo": lo, "hi": hi, "note": note}


def balanced_states(b: pd.DataFrame) -> list:
    years = b["year"].nunique()
    n = b.dropna(subset=["obese"]).groupby("state")["year"].nunique()
    return n[n == years].index.tolist()


def direct_series(b: pd.DataFrame) -> pd.Series:
    """Weighted national obesity prevalence (proportion) by year, 50 states + DC as present."""
    v = b.dropna(subset=["obese", "wt"])
    g = v.assign(wy=v["wt"] * v["obese"]).groupby("year")[["wy", "wt"]].sum()
    return g["wy"] / g["wt"]


def direct_departure_2025(b: pd.DataFrame) -> float:
    s = direct_series(b)
    return float(trend.departures(s.to_numpy(), list(s.index), predictive=False).draws[0][-1])


# --------------------------------------------------------------------------------------------- H1 (direct series)
def q24_h1(b: pd.DataFrame, m_imputations: int = 20, seed: int = 20261114) -> list:
    rows = [
        _row(
            "H1",
            "primary (direct weighted series, for comparison)",
            direct_departure_2025(b),
            note="D2025, pp, predictive mean",
        )
    ]
    keep = balanced_states(b)
    rows.append(
        _row(
            "H1",
            "balanced panel of states (direct series)",
            direct_departure_2025(b[b["state"].isin(keep)]),
            note=f"{len(keep)} states",
        )
    )
    for mode in ("cell", "landline"):
        rows.append(
            _row(
                "H1",
                f"interview mode: {mode} only (direct series)",
                direct_departure_2025(b[b["phone"] == mode]),
                note="combined-frame weights",
            )
        )
    miss = b.dropna(subset=["wt"]).assign(mis=lambda x: x["bmi"].isna().astype(float))
    g = miss.assign(wm=miss["wt"] * miss["mis"]).groupby("year")[["wm", "wt"]].sum()
    share = g["wm"] / g["wt"]
    dep = trend.departures(share.to_numpy(), list(share.index), scale="identity", predictive=False).draws[0]
    rows.append(
        _row(
            "H1",
            "share with missing BMI: departure from 2011-2019 trend, mean 2023-2025",
            100 * float(np.mean(dep)),
            note="pp; a rise could mimic a decline",
        )
    )
    ds = [direct_departure_2025(c) for c in mi.imputations(b, m=m_imputations, seed=seed)]
    rows.append(
        _row(
            "H1",
            f"multiple imputation of BMI ({m_imputations}), direct series",
            float(np.mean(ds)),
            float(np.std(ds, ddof=1)) if len(ds) > 1 else None,
            note="se = between-imputation SD",
        )
    )
    rows.append(
        _row(
            "H1",
            "pandemic years removed",
            note="not applicable: the primary trend uses 2011-2019 and each year is fitted separately",
        )
    )
    return rows


# --------------------------------------------------------------------------------------------- H2
def q24_h2(b: pd.DataFrame, m_imputations: int = 20, n_boot: int = 9_999, seed: int = 20261114) -> list:
    P = h2.PRIMARY
    S = h2.Spec
    rows = []
    fit2 = lambda df, spec=P: h2.fit_two_stage(df, spec)[0]  # noqa: E731
    rows.append(_row("H2", "without age and sex interactions", fit2(b, S(interactions=False))))
    rows.append(_row("H2", "ages 45-74 only", fit2(b[b["age5"].between(6, 11)])))
    rows.append(
        _row(
            "H2",
            "diabetes group reweighted to its 2017-2019 age x sex composition",
            fit2(h2.reweight_group_composition(b)),
        )
    )
    e, info = h2.wild_cluster_bootstrap(b, P, n_boot=n_boot, seed=seed)
    rows.append(
        _row(
            "H2",
            "single regression, wild cluster bootstrap by state (Webb)",
            e.est,
            e.se,
            *info["ci95"],
            note=f"{info['clusters']} clusters",
        )
    )
    rows.append(_row("H2", "item-change term off", fit2(b, S(t_item=None))))
    yrs = tuple(y for y in range(2011, 2026) if y not in PANDEMIC)
    rows.append(
        _row("H2", "pandemic years removed", fit2(b, S(years=yrs, pi_years=(2022, 2023, 2024, 2025))))
    )
    rows.append(_row("H2", "balanced panel of states", fit2(b[b["state"].isin(balanced_states(b))])))
    for mode in ("cell", "landline"):
        rows.append(_row("H2", f"interview mode: {mode} only", fit2(b[b["phone"] == mode])))
    ests, vars_ = [], []
    for c in mi.imputations(b, m=m_imputations, seed=seed):
        e = fit2(c)
        ests.append(e.est)
        vars_.append(e.se**2)
    q, se, _ = mi.rubin(ests, vars_)
    rows.append(
        _row(
            "H2",
            f"multiple imputation of BMI ({m_imputations})",
            q,
            se,
            q - 1.96 * se,
            q + 1.96 * se,
            note="Rubin's rules",
        )
    )
    return rows


# --------------------------------------------------------------------------------------------- H3 and NC1
def q24_h3(b: pd.DataFrame, n_rep: int = 200, m_imputations: int = 20, seed: int = 20261114) -> list:
    d = b[b["bmi"].notna()]
    rows = []
    for up in (0.75, 0.95):
        rows.append(
            _row(
                "H3",
                f"{int(up * 100)}th percentile in place of the 90th",
                h3.fit_h3(d, n_rep=n_rep, seed=seed, upper=up)[0],
            )
        )
    for ref in ((2011,), (2022,)):
        rows.append(
            _row(
                "H3",
                f"reweighting to the {ref[0]} composition",
                h3.fit_h3(d, n_rep=n_rep, seed=seed, ref_years=ref)[0],
            )
        )
    rows.append(
        _row(
            "H3",
            "RIF regression with covariates instead of reweighting",
            h3.rif_contrast(d),
            note="point estimate",
        )
    )
    rows.append(
        _row(
            "H3",
            "balanced panel of states",
            h3.fit_h3(d[d["state"].isin(balanced_states(b))], n_rep=n_rep, seed=seed)[0],
        )
    )
    for mode in ("cell", "landline"):
        rows.append(
            _row(
                "H3",
                f"interview mode: {mode} only",
                h3.fit_h3(d[d["phone"] == mode], n_rep=n_rep, seed=seed)[0],
            )
        )
    cs = [
        h3.fit_h3(c[c["bmi"].notna()], n_rep=2, seed=seed)[0].est
        for c in mi.imputations(b, m=m_imputations, seed=seed)
    ]
    rows.append(
        _row(
            "H3",
            f"multiple imputation of BMI ({m_imputations})",
            float(np.mean(cs)),
            float(np.std(cs, ddof=1)) if len(cs) > 1 else None,
            note="point estimates; se = between-imputation SD",
        )
    )
    rows.append(
        _row(
            "H3",
            "pandemic years removed",
            note="not applicable: the trend uses 2011-2019 and the contrast 2023-2025",
        )
    )
    return rows


def q24_nc1(b: pd.DataFrame, n_rep: int = 200, seed: int = 20261115) -> list:
    from glp1_review.data import AGE6

    e, det = h3.fit_nc1(b[b["htm"].notna()], n_rep=n_rep, seed=seed, ages=tuple(AGE6))
    rows = [_row("NC1", "all adults 18+", e)]
    e1, det1 = h3.fit_nc1(b[b["htm"].notna()], n_rep=n_rep, seed=seed)
    for sex, v in det1["by_sex"].items():
        rows.append(_row("NC1", f"by sex: {sex}", v, note="point estimate"))
    return rows


# --------------------------------------------------------------------------------------------- H4
def q24_h4(
    b: pd.DataFrame,
    X: pd.DataFrame,
    E: pd.Series,
    Y: pd.DataFrame,
    adults_2024: pd.Series,
    n_perm: int = 20_000,
    seed: int = 20261114,
) -> list:
    rows = []

    def es_row(variant, Yv, Ev, note=""):
        es = h4.event_study(Yv, Ev)
        _, p = h4.permutation_p(h4.beta_star, Yv, Ev, n_perm=n_perm, seed=seed)
        return _row(
            "H4",
            variant,
            es.beta_star,
            es.se_star,
            es.beta_star - 1.96 * es.se_star,
            es.beta_star + 1.96 * es.se_star,
            note=f"permutation p {p:.3f}" + (f"; {note}" if note else ""),
        )

    for col in X.columns:
        z = (X[col] - X[col].mean()) / X[col].std(ddof=0)
        rows.append(es_row(f"indicator alone: {col}", Y, z))
    rows.append(es_row("population weights", Y.assign(w=Y["state"].map(adults_2024)), E))
    v = b.dropna(subset=["obese", "wt"])
    g = v.groupby(["state", "year"]).agg(
        p=("obese", "mean"), sw=("wt", "sum"), sw2=("wt", lambda x: float(np.sum(x**2)))
    )
    g["neff"] = g["sw"] ** 2 / g["sw2"]
    g["prec"] = g["neff"] / (g["p"] * (1 - g["p"]) * 1e4)  # pp scale
    abbr = b.drop_duplicates("state").set_index("state")["abbr"]
    prec = g["prec"].rename(index=abbr, level=0)
    rows.append(
        es_row(
            "precision weights (1 / sampling variance, Kish n)",
            Y.assign(w=[prec.get((s, t), np.nan) for s, t in zip(Y["state"], Y["year"], strict=True)]).dropna(
                subset=["w"]
            ),
            E,
        )
    )
    loo = []
    for s in E.index:
        keep = E.index != s
        loo.append(h4.event_study(Y[Y["state"] != s], E[keep]).beta_star)
    rows.append(
        _row(
            "H4",
            "leave-one-state-out (range)",
            float(np.mean(loo)),
            None,
            float(np.min(loo)),
            float(np.max(loo)),
            note="estimate = mean of the 50 fits",
        )
    )
    keep = ~E.index.isin(H4_TOP4)
    rows.append(es_row("without WV, KY, LA and OK", Y[Y["state"].isin(E.index[keep])], E[keep]))
    post = Y[Y["year"].isin(trend.POST)].groupby("state")["year"].nunique()
    full = post[post == len(trend.POST)].index
    rows.append(
        es_row("without states missing a post-period year", Y[Y["state"].isin(full)], E[E.index.isin(full)])
    )
    es = h4.event_study(Y, E)
    for mbar in (0.5, 1.0):
        lo, hi = h4.rm_interval(es, mbar)
        rows.append(
            _row(
                "H4",
                f"Rambachan-Roth relative magnitude, Mbar = {mbar}",
                es.beta_star,
                es.se_star,
                lo,
                hi,
                note="conservative",
            )
        )
    dY = h4.state_departures(Y)
    rows.append(
        _row("H4", "dose-response, quartiles (top minus bottom)", h4.tercile_contrast(dY, E, n_groups=4))
    )
    rows.append(
        _row(
            "H4",
            "dose-response, cubic fit (average causal response)",
            h4.average_causal_response(dY, E, degree=3),
        )
    )
    rows.append(es_row("pandemic years removed", Y[~Y["year"].isin(PANDEMIC)], E))
    nyears = Y.groupby("state")["year"].nunique()
    bal = nyears[nyears == Y["year"].nunique()].index
    rows.append(es_row("balanced panel of states", Y[Y["state"].isin(bal)], E[E.index.isin(bal)]))
    return rows


# --------------------------------------------------------------------------------------------- H5
def q24_h5(
    inp: dict, published_rate: float, d2025_ci: tuple, n_draws: int = 10_000, seed: int = 20261114
) -> list:
    rows = []
    variants = {
        "loss of non-persistent users U(0%, 4%)": h5.Params(
            inp["meps_rate"], published_rate, loss_stopped=(0.0, 0.04), n_draws=n_draws, seed=seed
        ),
        "persistence fixed at 35.2% and 53.5%": h5.Params(
            inp["meps_rate"],
            published_rate,
            n_draws=n_draws,
            seed=seed,
            fixed={"persistence_no_diab": 0.352, "persistence_diab": 0.535},
        ),
        "national use fixed at the MEPS 2024 rate": h5.Params(
            inp["meps_rate"],
            published_rate,
            n_draws=n_draws,
            seed=seed,
            fixed={"national_rate": inp["meps_rate"]},
        ),
    }
    for name, p in variants.items():
        sim = h5.simulate(inp["bmi"], inp["diab"], inp["w"], inp["use_prob"], p)
        rows.append(
            _row(
                "H5",
                name,
                float(np.median(sim)),
                None,
                float(np.percentile(sim, 5)),
                float(np.percentile(sim, 95)),
                note=h5_compatibility(d2025_ci, sim),
            )
        )
    return rows


# --------------------------------------------------------------------------------------------- H6
def q24_h6(df: pd.DataFrame, df_all_rounds: pd.DataFrame) -> list:
    rows = [
        _row("H6", "prevalent users as a third group", h6.fit_with_prevalent(df)[0]),
        _row("H6", "LONGWT instead of LSAQWT", h6.fit_primary(df.assign(lsaqwt=df["longwt"]))[0]),
        _row("H6", "persons not present in all rounds included", h6.fit_primary(df_all_rounds)[0]),
        _row("H6", "changes larger than 10 kg/m2 excluded", h6.fit_primary(df[df["dbmi"].abs() <= 10])[0]),
    ]
    for v, lab in ((1, "with diabetes"), (0, "without diabetes")):
        sub = df[df["diabetes0"] == v]
        rows.append(
            _row(
                "H6",
                f"by diabetes status: {lab}",
                h6.fit_primary(sub)[0],
                note=f"{h6.n_initiators(sub)} initiators",
            )
        )
    for k in (23, 24):
        sub = df[df["panel"] == k]
        rows.append(
            _row("H6", f"Panel {k} only", h6.fit_primary(sub)[0], note=f"{h6.n_initiators(sub)} initiators")
        )
    return rows
