"""Run the pre-registered analyses end to end and write tables, draws and a verdict summary (English).

Order: H1 (MRP + Stage 2, alternative counterfactuals, NC2) -> H0 (adds BRFSS by Gallup groups) -> H2 (two-stage,
secondary single regression, secondary outcomes and gradients, NC2) -> H3 -> NC1 -> H4 -> H6 -> H5 (needs H1 and
H6) -> verdicts (Q22). Every step writes its own files, so a partial run keeps what it finished.

Outcome data are only read through prepare.*, which refuses to run before the registration (guard.py).
`Config.quick()` shrinks draws, replicates and permutations for testing; the primary run uses `Config()`.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from glp1_review import decision as dec
from glp1_review import (
    h0_sources,
    h1_mrp,
    h2_tripdiff,
    h3_quantiles,
    h4_states,
    h5_microsim,
    h6_panel,
    prepare,
    sensitivity,
    trend,
)
from glp1_review.data import DIVISION

ALTERNATIVES = {  # Q24 counterfactual trends for H1 (and the H1 decision rule, Q22)
    "linear 2011-2021": {"pre": tuple(range(2011, 2022))},
    "linear 2015-2019": {"pre": tuple(range(2015, 2020))},
    "quadratic 2011-2019": {"form": "quadratic"},
    "2022 level, 2011-2019 slope": {"form": "level"},
}
H4_TOP4 = ("WV", "KY", "LA", "OK")


@dataclass
class Config:
    mrp_sampler: dict = field(default_factory=dict)  # PyMC defaults of h1_mrp (4 chains x 1,000 + 1,000)
    mrp_q23: bool = True
    h3_reps: int = 500
    nc1_reps: int = 500
    h4_perm: int = 20_000
    h4_factor_draws: int = 200
    h4_factor_sampler: dict = field(default_factory=dict)
    h5_draws: int = 10_000
    published_rate_2025: float = 0.12  # KFF, Nov 2025: 12% of adults currently taking a GLP-1 (any purpose)
    q24_reps: int = 200  # bootstrap replicates of each H3/NC1 sensitivity variant
    mi_m: int = 20  # imputations of BMI (Q14)
    wcb_boot: int = 9_999  # wild cluster bootstrap replications (H2)
    seed: int = 20261114

    @classmethod
    def quick(cls) -> "Config":
        return cls(
            mrp_sampler={"draws": 150, "tune": 200, "chains": 2},
            mrp_q23=False,
            h3_reps=10,
            nc1_reps=10,
            h4_perm=100,
            h4_factor_draws=10,
            h4_factor_sampler={"draws": 200, "tune": 200, "chains": 2},
            h5_draws=200,
            q24_reps=4,
            mi_m=2,
            wcb_boot=99,
        )


def _write(out: Path, name: str, obj) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(out / f"{name}.csv", index=True)
    else:
        (out / f"{name}.json").write_text(json.dumps(obj, indent=2, default=float), encoding="utf-8")


def _est(e: dec.Estimate) -> dict:
    return {"estimate": e.est, "se": e.se, "dof": e.dof}


# --------------------------------------------------------------------------------------------- steps
def step_h1(b, src, cfg, out) -> dict:
    inputs = prepare.h1_inputs(b, src)
    P, log = {}, {}
    for y, inp in inputs.items():
        if cfg.mrp_q23:
            idata, label, diag, opts = h1_mrp.fit_year_q23(
                inp["cells"], inp["z"], DIVISION, seed=cfg.seed + y, sampler_kwargs=cfg.mrp_sampler
            )
        else:
            idata, _ = h1_mrp.fit_year(
                inp["cells"], inp["z"], DIVISION, seed=cfg.seed + y, sampler_kwargs=cfg.mrp_sampler
            )
            label, diag, opts = "primary (no Q23 check)", [], {}
        P[y] = h1_mrp.poststratify(
            idata, inp["frame"], inp["use_race"], **{k: v for k, v in opts.items() if k in ("agesex", "educ")}
        )
        log[y] = {"step": label, "diagnostics": diag, "use_race": inp["use_race"]}
    years = sorted(P)
    n = min(len(v) for v in P.values())
    np.savez(
        out / "h1_prevalence_draws.npz", years=np.array(years), P=np.column_stack([P[y][:n] for y in years])
    )
    mill = prepare.adults_millions(src)
    primary = h1_mrp.national_departures(P, adults_millions=mill)
    rows = [
        {"counterfactual": "primary: linear 2011-2019", "year": y, "median_pp": m, "lo95": lo, "hi95": hi}
        for y, (m, lo, hi) in primary["summary_pp"].items()
    ]
    alt_signs = []
    for name, kw in ALTERNATIVES.items():
        a = h1_mrp.national_departures(P, **kw)
        for y, (m, lo, hi) in a["summary_pp"].items():
            rows.append({"counterfactual": name, "year": y, "median_pp": m, "lo95": lo, "hi95": hi})
        alt_signs.append(a["summary_pp"][2025][0])
    nc2 = h1_mrp.national_departures(P, pre=tuple(range(2011, 2016)), post=(2017, 2018, 2019))
    res = {
        "national_prevalence_median": {y: float(np.median(P[y])) for y in years},
        "D2025_pp": primary["summary_pp"][2025],
        "D_millions": primary.get("summary_millions"),
        "p_D2025_below_D2023": primary["p_2025_below_2023"],
        "alternatives_D2025_median": dict(zip(ALTERNATIVES, alt_signs, strict=True)),
        "break_present": dec.h1_break_present(primary["summary_pp"][2025][1:], alt_signs),
        "nc2_departures_pp": nc2["summary_pp"],
        "nc2_passes": all(lo <= 0 <= hi for _, lo, hi in nc2["summary_pp"].values()),
        "fit_log": log,
    }
    _write(out, "h1_departures", pd.DataFrame(rows).set_index("counterfactual"))
    _write(out, "h1", res)
    return {**res, "_P": P}  # posterior draws kept in memory for the Q24 external comparison


def step_h0(b, h1, out) -> dict:
    groups = h0_sources.brfss_by_gallup_groups(b)
    tab = h0_sources.age_change_table(groups)
    nat = h0_sources.national_table()
    if h1:
        nat["brfss_mrp_median"] = pd.Series(h1["national_prevalence_median"]).mul(100)
    _write(out, "h0_age_changes", tab)
    _write(out, "h0_national", nat)
    return {"age_changes": tab.round(2).to_dict()}


def step_h2(b, out) -> dict:
    spec = h2_tripdiff.PRIMARY
    est, det = h2_tripdiff.fit_two_stage(b, spec)
    single, _ = h2_tripdiff.fit(b, spec)
    rows = [
        {"model": "primary, two-stage", **_est(est)},
        {"model": "secondary, single regression", **_est(single)},
    ]
    for name, s in {
        "secondary: obesity (LPM, x100)": h2_tripdiff.Spec(outcome="obese100"),
        "gradient: ages 50-64": h2_tripdiff.Spec(group="age50_64", t_item=None),
        "gradient: women": h2_tripdiff.Spec(group="women", t_item=None),
        "gradient: insured": h2_tripdiff.Spec(group="insured", t_item=None),
    }.items():
        e, _ = h2_tripdiff.fit_two_stage(b.assign(obese100=100 * b["obese"]), s)
        rows.append({"model": name, **_est(e)})
    nc2, _ = h2_tripdiff.fit_two_stage(b, h2_tripdiff.NC2)
    rows.append({"model": "NC2 placebo (2017-2018)", **_est(nc2)})
    _write(out, "h2", pd.DataFrame(rows).set_index("model"))
    _write(out, "h2_yearly_gaps", det["gaps"].rename("gap").to_frame())
    lo, hi = nc2.est - nc2.q(0.975) * nc2.se, nc2.est + nc2.q(0.975) * nc2.se
    return {"primary": est, "nc2_passes": lo <= 0 <= hi}


def step_h3(b, cfg, out) -> dict:
    est, det = h3_quantiles.fit_h3(b[b["bmi"].notna()], n_rep=cfg.h3_reps, seed=cfg.seed)
    _write(out, "h3_quantiles", det["quantiles"])
    _write(out, "h3_departures", pd.DataFrame(det["departures"], index=list(trend.POST)))
    _write(out, "h3", _est(est))
    return {"primary": est}


def step_nc1(b, cfg, out) -> dict:
    est, det = h3_quantiles.fit_nc1(b[b["htm"].notna()], n_rep=cfg.nc1_reps, seed=cfg.seed + 1)
    res = {**_est(est), "by_sex": det["by_sex"], "passes": dec.nc1_passes(est)}
    _write(out, "nc1", res)
    return {"primary": est, "passes": res["passes"]}


def step_h4(b, src, cfg, out) -> dict:
    X = prepare.h4_exposure(src)
    fx = h4_states.factor_exposure(
        X, n_draws=cfg.h4_factor_draws, seed=cfg.seed, sampler_kwargs=cfg.h4_factor_sampler
    )
    E = fx["E"]
    Y = prepare.h4_outcome(b)
    Y = Y[Y["state"].isin(E.index)]
    es = h4_states.event_study(Y, E)
    draws = [h4_states.event_study(Y, pd.Series(d, index=E.index)) for d in fx["draws"]]
    est, se = h4_states.rubin(np.array([d.beta_star for d in draws]), np.array([d.se_star**2 for d in draws]))
    _, p_perm = h4_states.permutation_p(h4_states.beta_star, Y, E, n_perm=cfg.h4_perm, seed=cfg.seed)
    rr = {m: h4_states.rr_interval(est, se, m) for m in (0.0, 0.02, 0.05)}
    dY = h4_states.state_departures(Y)
    terc, p_terc = h4_states.permutation_p(
        lambda y, e: h4_states.tercile_contrast(dY, e), Y, E, n_perm=cfg.h4_perm, seed=cfg.seed + 1
    )
    acr, p_acr = h4_states.permutation_p(
        lambda y, e: h4_states.average_causal_response(dY, e), Y, E, n_perm=cfg.h4_perm, seed=cfg.seed + 2
    )
    keep = ~E.index.isin(H4_TOP4)
    no4 = h4_states.event_study(Y[Y["state"].isin(E.index[keep])], E[keep])
    res = {
        "beta_star_posterior_mean_E": es.beta_star,
        "beta_star_rubin": est,
        "se_rubin": se,
        "p_permutation_two_sided": p_perm,
        "rr_intervals": {str(k): v for k, v in rr.items()},
        "supportive": dec.h4_supportive(p_perm, rr[0.02]),
        "tercile_contrast": terc,
        "p_tercile": p_terc,
        "average_causal_response": acr,
        "p_acr": p_acr,
        "without_WV_KY_LA_OK": {"beta_star": no4.beta_star, "se": no4.se_star},
        "loadings": fx["loadings"].tolist(),
    }
    _write(out, "h4_exposure", X.assign(E=E))
    _write(out, "h4_event_betas", es.beta.rename("beta").to_frame())
    _write(out, "h4", res)
    return {**res, "_X": X, "_E": E, "_Y": Y}  # kept in memory for the Q24 step, not written


def step_h6(src, out) -> dict:
    df = prepare.h6_frame(src)
    n_init = h6_panel.n_initiators(df)
    est, _ = h6_panel.fit_primary(df)
    late, _ = h6_panel.fit_placebo_late(df)
    nyt, _ = h6_panel.fit_not_yet_treated(df)
    counts = df.groupby(["panel", "group"]).size().unstack(fill_value=0)
    _write(out, "h6_counts", counts)
    _write(
        out,
        "h6",
        {
            "primary": _est(est),
            "placebo_late": _est(late),
            "not_yet_treated": _est(nyt),
            "initiators": n_init,
        },
    )
    return {"primary": est, "late": late, "initiators": n_init}


def step_h5(b, src, cfg, h1, h6, out) -> dict:
    inp = prepare.h5_inputs(b, src)
    p = h5_microsim.Params(
        meps_rate=inp["meps_rate"],
        published_rate=cfg.published_rate_2025,
        n_draws=cfg.h5_draws,
        seed=cfg.seed,
    )
    sim = h5_microsim.simulate(inp["bmi"], inp["diab"], inp["w"], inp["use_prob"], p)
    _, lo, hi = h1["D2025_pp"]
    res = {
        "simulated_effect_pp": {
            "p5": float(np.percentile(sim, 5)),
            "median": float(np.median(sim)),
            "p95": float(np.percentile(sim, 95)),
        },
        "D2025_ci": [lo, hi],
        "classification": dec.h5_compatibility((lo, hi), sim),
        "meps_2024_adult_rate": inp["meps_rate"],
    }
    if h6 and h6["primary"].se < 0.5:
        sim2 = h5_microsim.simulate_h6(
            inp["bmi"], inp["diab"], inp["w"], inp["use_prob"], p, beta_h6=h6["primary"].est
        )
        res["version_2_h6"] = {
            "median": float(np.median(sim2)),
            "classification": dec.h5_compatibility((lo, hi), sim2),
        }
    _write(out, "h5", res)
    return res


def verdicts(r: dict) -> dict:
    fam_est = {k: r[k]["primary"] for k in ("H2", "H3", "H6") if k in r}
    family = dec.classify_family(
        fam_est, h6_late=r.get("H6", {}).get("late"), h6_initiators=r.get("H6", {}).get("initiators")
    )
    nc1_pass = r["NC1"]["passes"] if "NC1" in r else None
    out = {"family": family, "NC1_passes": nc1_pass}
    if nc1_pass is not None and len(fam_est) == 3:
        out["overall"] = dec.overall_verdict(family, nc1_pass)
    if "H1" in r:
        out["H1_break_present"] = r["H1"]["break_present"]
        out["NC2_H1_passes"] = r["H1"]["nc2_passes"]
    if "H2" in r:
        out["NC2_H2_passes"] = r["H2"]["nc2_passes"]
    if "H4" in r:
        out["H4_supportive"] = r["H4"]["supportive"]
    if "H5" in r:
        out["H5"] = r["H5"]["classification"]
    return out


def summary_markdown(v: dict, r: dict, cfg: Config) -> str:
    lines = [
        "# Pre-registered analyses: results summary",
        "",
        f"Configuration: `{json.dumps(asdict(cfg))}`",
        "",
    ]
    if "overall" in v:
        lines += [f"**Overall verdict (Q22): {v['overall']}**", ""]
    lines += ["| Hypothesis | Estimate | SE | Classification |", "| --- | --- | --- | --- |"]
    for k, info in v["family"].items():
        e = r[k]["primary"]
        lines.append(f"| {k} | {e.est:.3f} | {e.se:.3f} | {info['label']} |")
    for k in ("H1_break_present", "H4_supportive", "H5", "NC1_passes", "NC2_H1_passes", "NC2_H2_passes"):
        if k in v:
            lines.append(f"| {k} | | | {v[k]} |")
    return "\n".join(lines) + "\n"


def step_q24(b, src, cfg, out, r) -> dict:
    """Q24 sensitivity analyses (sensitivity.py); results are reported in full whatever their direction."""
    rows = []
    rows += sensitivity.q24_h1(b, m_imputations=cfg.mi_m, seed=cfg.seed)
    if "H1" in r:
        rows += sensitivity.q24_external(r["H1"]["_P"])
    rows += sensitivity.q24_self_report(b, prepare.nhanes(src), seed=cfg.seed)
    rows += sensitivity.q24_h2(b, m_imputations=cfg.mi_m, n_boot=cfg.wcb_boot, seed=cfg.seed)
    rows += sensitivity.q24_h3(b, n_rep=cfg.q24_reps, m_imputations=cfg.mi_m, seed=cfg.seed)
    rows += sensitivity.q24_nc1(b, n_rep=cfg.q24_reps, seed=cfg.seed + 1)
    if "H4" in r:
        h = r["H4"]
        pop = pd.read_csv(src.clean / "census" / "adult_pop_state_2020_2025.csv")
        adults = pop.set_index(pop["state"].map(prepare._name_to_abbr(src)))["2024"]
        rows += sensitivity.q24_h4(b, h["_X"], h["_E"], h["_Y"], adults, n_perm=cfg.h4_perm, seed=cfg.seed)
    if "H1" in r:
        _, lo, hi = r["H1"]["D2025_pp"]
        rows += sensitivity.q24_h5(
            prepare.h5_inputs(b, src), cfg.published_rate_2025, (lo, hi), n_draws=cfg.h5_draws, seed=cfg.seed
        )
    rows += sensitivity.q24_h6(prepare.h6_frame(src), prepare.h6_frame(src, all_rounds=False))
    tab = pd.DataFrame(rows)
    _write(out, "q24", tab.set_index(["hypothesis", "variant"]))
    return {"n_rows": len(tab)}


STEPS = ("h1", "h0", "h2", "h3", "nc1", "h4", "h6", "h5", "q24")


def run(out: Path, cfg: Config | None = None, steps=STEPS, src: prepare.Sources = prepare.DEFAULT) -> dict:
    cfg = cfg or Config()
    out.mkdir(parents=True, exist_ok=True)
    needs_brfss = set(steps) - {"h6"}
    b = prepare.brfss(src) if needs_brfss else None
    r: dict = {}
    if "h1" in steps:
        r["H1"] = step_h1(b, src, cfg, out)
    if "h0" in steps:
        r["H0"] = step_h0(b, r.get("H1"), out)
    if "h2" in steps:
        r["H2"] = step_h2(b, out)
    if "h3" in steps:
        r["H3"] = step_h3(b, cfg, out)
    if "nc1" in steps:
        r["NC1"] = step_nc1(b, cfg, out)
    if "h4" in steps:
        r["H4"] = step_h4(b, src, cfg, out)
    if "h6" in steps:
        r["H6"] = step_h6(src, out)
    if "h5" in steps and "H1" in r:
        r["H5"] = step_h5(b, src, cfg, r["H1"], r.get("H6"), out)
    if "q24" in steps:
        r["Q24"] = step_q24(b, src, cfg, out, r)
    v = verdicts(r)
    _write(
        out,
        "verdicts",
        json.loads(json.dumps(v, default=lambda o: o.__dict__ if hasattr(o, "__dict__") else float(o))),
    )
    (out / "summary.md").write_text(summary_markdown(v, r, cfg), encoding="utf-8")
    return {"results": r, "verdicts": v}
