"""Self-report correction (Ward et al. 2019, appendix section 2) on simulated data."""

import numpy as np
import pandas as pd
import pytest

from glp1_review import self_report as sr
from glp1_review import sensitivity as sens


def under_report(bmi):
    """Self-report bias that grows with BMI, as Ward et al. found (about 0.4 at BMI 22, 2 at BMI 40)."""
    return 0.4 + 0.09 * np.clip(bmi - 22, 0, None)


def simulate(rng, years=range(2011, 2026), n_year=4000, n_cycle=3000, drift=0.08):
    """BRFSS-like self-reported BMI by year (mean rises `drift` log-points per decade) and NHANES measured BMI."""
    rows = []
    for y in years:
        sex = rng.choice(["Male", "Female"], n_year)
        true = np.exp(rng.normal(np.log(28.0) + drift * (y - 2011) / 10, 0.2, n_year))
        rows.append(
            pd.DataFrame(
                {
                    "year": y,
                    "sex": sex,
                    "bmi": (true - under_report(true)).round(1),
                    "true_bmi": true,
                    "wt": rng.uniform(50, 500, n_year),
                }
            )
        )
    b = pd.concat(rows, ignore_index=True)
    b["obese"] = (b["bmi"] >= 30).astype(float)
    mid = {
        "2011-2012": 2011.5,
        "2013-2014": 2013.5,
        "2015-2016": 2015.5,
        "2017-2020": 2018.6,
        "2021-2023": 2022.5,
    }
    nh = []
    for c, ym in mid.items():
        true = np.exp(rng.normal(np.log(28.0) + drift * (ym - 2011) / 10, 0.2, n_cycle))
        nh.append(
            pd.DataFrame(
                {
                    "cycle": c,
                    "span": 3.2 if c == "2017-2020" else 2.0,
                    "sex": rng.choice(["Male", "Female"], n_cycle),
                    "bmi": true.round(1),
                    "wt": rng.uniform(5e3, 5e4, n_cycle),
                }
            )
        )
    return b, pd.concat(nh, ignore_index=True)


def test_weighted_rank_and_ks():
    x = np.array([3.0, 1.0, 2.0, 2.0])
    r = sr.weighted_rank(x, np.ones(4))
    assert r.tolist() == pytest.approx([0.875, 0.125, 0.5, 0.5])
    a = np.arange(100.0)
    assert sr.ks_distance(a, np.ones(100), a, np.ones(100)) == 0.0
    assert sr.ks_distance(a, np.ones(100), a + 1000, np.ones(100)) == 1.0


def test_correction_recovers_measured_distribution():
    rng = np.random.default_rng(90)
    b, nh = simulate(rng)
    c, diag = sr.correct(b, nh, sr.PERIODS, seed=1)
    assert set(diag["period"]) == set(sr.PERIODS) and len(diag) == 6
    assert (diag["ks_after"] < diag["ks_before"]).all()
    assert diag["ks_after"].max() < 0.04
    # bias grows across the distribution, as simulated
    assert (diag["bias_q90"] > diag["bias_q10"] + 0.8).all()
    for _, r in diag.iterrows():
        assert r["obese_corrected"] == pytest.approx(r["obese_nhanes"], abs=0.025)
        assert r["obese_self"] < r["obese_corrected"] - 0.02
    # prevalence by year now tracks true (measured) BMI
    for y in (2013, 2019, 2023):
        g = c[c.year == y]
        true = np.average(g["true_bmi"] >= 30, weights=g["wt"])
        assert np.average(g["obese"], weights=g["wt"]) == pytest.approx(true, abs=0.03)


def test_within_period_change_is_kept():
    rng = np.random.default_rng(91)
    b, nh = simulate(rng, drift=0.0)
    b.loc[b.year == 2025, "bmi"] -= 1.0  # a fall at the end of the 2021-2025 period
    for periods in (sr.PERIODS, sr.PERIODS_FIXED):
        c, _ = sr.correct(b, nh, periods, seed=2)
        m = c.groupby("year").apply(lambda g: np.average(g["bmi"], weights=g["wt"]), include_groups=False)
        assert m[2025] - m[2024] == pytest.approx(-1.0, abs=0.25)


def test_rows_outside_periods_or_missing_stay_missing():
    rng = np.random.default_rng(92)
    b, nh = simulate(rng, years=range(2019, 2023), n_year=1500)
    b.loc[b.index[:10], "bmi"] = np.nan
    b.loc[b.index[10:20], "sex"] = np.nan
    c, _ = sr.correct(b, nh, {"2021-2025": sr.PERIODS["2021-2025"]}, seed=3)
    assert c.loc[b.index[:20], "bmi"].isna().all()
    assert c.loc[c.year < 2021, "obese"].isna().all()
    assert c.loc[(c.year >= 2021) & b["bmi"].notna() & b["sex"].notna(), "obese"].notna().all()


def test_q24_self_report_rows():
    rng = np.random.default_rng(93)
    b, nh = simulate(rng, n_year=2500)
    rows = sens.q24_self_report(b, nh, seed=4)
    assert len(rows) == 2
    for r in rows:
        assert np.isfinite(r["estimate"]) and "KS distance" in r["note"]
    assert "as in Ward" in rows[0]["variant"] and "fixed" in rows[1]["variant"]
