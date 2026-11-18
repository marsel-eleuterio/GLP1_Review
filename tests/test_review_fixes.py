"""Regression tests for the code review of 16 November 2026 (decision_log.md, section 8)."""

import numpy as np
import pandas as pd
import pytest
from test_h3_nc1 import simulate as simulate_h3
from test_self_report import simulate as simulate_sr

from glp1_review import h1_mrp, h3_quantiles, h6_panel, mi, self_report
from glp1_review.data import harmonise_brfss


def test_income_codes_mean_the_same_bracket_every_year():
    raw = pd.DataFrame(
        {
            "age5": 5,
            "sex": 1,
            "race": 1,
            "educ": 2,
            "bmicat": 3,
            "plan_raw": 1,
            "income": [
                1,
                4,
                5,
                5,
                6,
                7,
                9,
            ],  # 5 = $50k+ (_INCOMG) or $50-100k (_INCOMG1); 6, 7 only in _INCOMG1
        }
    )
    assert harmonise_brfss(raw)["income"].tolist() == [1, 4, 5, 5, 5, 5, 9]


def test_converged_checks_every_parameter():
    import arviz as az

    rng = np.random.default_rng(1)
    good = rng.normal(size=(4, 1000))
    stuck = np.repeat(np.arange(4.0)[:, None], 1000, axis=1) + rng.normal(
        0, 0.01, (4, 1000)
    )  # chains disagree
    idata = az.from_dict(
        {
            "posterior": {"mu": good, "gamma": good, "a_educ": stuck[..., None].repeat(4, axis=2)},
            "sample_stats": {"diverging": np.zeros((4, 1000), bool)},
        }
    )
    info = h1_mrp.converged(idata)
    assert not info["ok"] and info["max_rhat"] > 1.5


def test_composition_adjusted_series_fills_missing_states():
    Y = pd.DataFrame(
        [(s, y, base + 0.5 * (y - 2011)) for s, base in (("A", 30.0), ("B", 40.0)) for y in range(2011, 2016)]
    )
    Y.columns = ["state", "year", "y"]
    Y = Y[~((Y.state == "B") & (Y.year == 2015))]  # B missing in the last year
    s = h1_mrp.composition_adjusted_series(Y, pd.Series({"A": 1.0, "B": 3.0}))
    assert s[2011] == pytest.approx(37.5) and s[2015] == pytest.approx(39.5)  # not pulled down to A's level


def test_h1_falls_back_to_the_direct_series_when_q23_fails(monkeypatch, tmp_path):
    from fake_tree import build

    from glp1_review import guard, prepare, run
    from glp1_review.paths import PILOT_DATA

    paths = build(tmp_path / "data", n_per_year=1500)
    src = prepare.Sources(clean=paths["clean"], raw=paths["raw"], pilot_data=PILOT_DATA)
    reg = tmp_path / "osf_registration.txt"
    reg.write_text("TEST")
    monkeypatch.setattr(guard, "REGISTRATION_FILE", reg)

    def fail(*a, **k):
        raise RuntimeError("did not converge")

    monkeypatch.setattr(h1_mrp, "fit_year_q23", fail)
    b = prepare.brfss(src)
    out = tmp_path / "out"
    out.mkdir()
    res = run.step_h1(b, src, run.Config(fallback_draws=500), out)
    assert res["primary_series"].startswith("composition-adjusted direct series")
    assert all(v["step"] == "failed every Q23 step" for v in res["fit_log"].values())
    m, lo, hi = res["D2025_pp"]
    assert lo < m < hi and np.isfinite(m)


def test_rif_series_years_without_race_keep_their_level():
    rng = np.random.default_rng(5)
    df = simulate_h3(rng, n=3000)
    df["bmi"] += np.where(df["race"] == "B", 3.0, 0.0)
    df.loc[df.year.isin([2015, 2016]), "race"] = h3_quantiles.NOT_AVAILABLE
    years, s = h3_quantiles.rif_series(df, (0.50,))
    med = s[0.50]
    for y in (2015, 2016):
        g = df[df.year == y]
        raw = float(np.interp(0.5, *_wecdf(g["bmi"], g["wt"])))
        assert med[years.index(y)] == pytest.approx(raw, abs=0.4)  # was shifted by several kg/m2


def _wecdf(x, w):
    o = np.argsort(x.to_numpy())
    xs, ws = x.to_numpy()[o], w.to_numpy()[o]
    cw = np.cumsum(ws)
    return (cw - 0.5 * ws) / cw[-1], xs


def test_nc1_sexes_share_psu_draws():
    rng = np.random.default_rng(6)
    df = simulate_h3(rng, n=1500)
    P = h3_quantiles.prepare(df[df.sex == "M"], "htm")
    st, psu = h3_quantiles._psu_keys(P)
    assert all(s.split("|")[0] == p.split("|")[0] for s, p in zip(st[:50], psu[:50], strict=True))
    est, info = h3_quantiles.fit_nc1(df.assign(age_group="35-44"), n_rep=20, seed=1)
    assert len(info["replicates"]) == 20 and np.isfinite(est.se) and est.se > 0


def test_pmm_draws_from_the_k_nearest_donors():
    rng = np.random.default_rng(7)
    n = 200
    X_obs = np.column_stack([np.ones(n), np.arange(n, dtype=float)])
    y_obs = np.arange(n, dtype=float)  # fitted values equal y exactly
    X_mis = np.array([[1.0, 100.2]] * 4000)
    picks = mi._pmm(X_obs, y_obs, X_mis, rng, k=5)
    assert set(np.unique(picks)) == {98.0, 99.0, 100.0, 101.0, 102.0}
    edge = mi._pmm(X_obs, y_obs, np.array([[1.0, -3.0]] * 2000), rng, k=5)
    assert set(np.unique(edge)) == {0.0, 1.0, 2.0, 3.0, 4.0}


def test_h6_weight_falls_back_and_rejects_missing():
    df = pd.DataFrame({"lsaqwt": [100.0, 0.0, 0.0, np.nan], "longwt": [50.0, 80.0, np.nan, np.nan]})
    w = h6_panel.analysis_weight(df)
    assert w.iloc[:2].tolist() == [100.0, 80.0] and w.iloc[2:].isna().all()
    assert h6_panel.analysis_weight(df[["lsaqwt"]]).iloc[1:].isna().all()


def test_fixed_calibration_ignores_years_after_2020():
    rng = np.random.default_rng(8)
    b, nh = simulate_sr(rng, n_year=1500)
    c1, _ = self_report.correct(b, nh, self_report.PERIODS_FIXED, seed=3)
    b2 = b.copy()
    b2.loc[b2.year >= 2023, "bmi"] += 3.0  # a change in the outcome years must not move the calibration
    c2, _ = self_report.correct(b2, nh, self_report.PERIODS_FIXED, seed=3)
    early = b.year <= 2020
    assert np.allclose(c1.loc[early, "bmi"], c2.loc[early, "bmi"])
    late = b.year >= 2023
    assert (c2.loc[late, "bmi"] - c1.loc[late, "bmi"]).mean() == pytest.approx(3.0, abs=0.6)
