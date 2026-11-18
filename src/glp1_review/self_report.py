"""NHANES-calibrated correction of self-reported BMI (Q24), following Ward et al. (2019), supplementary appendix,
section 2:

1. Within each sex and time period, compare the weighted distribution of self-reported BMI (BRFSS) with that of
   measured BMI (NHANES) at a grid of quantiles: d(q) = Q_NHANES(q) - Q_BRFSS(q).
2. Fit a cubic smoothing spline to d(q) across q.
3. For each BRFSS respondent, take the weighted quantile of their self-reported BMI within sex and period, predict
   d at that quantile and add it to their BMI.
4. Add normal noise (mean 0, SD 0.5) to smooth the rounding of reported height and weight.
5. Check with the two-sample Kolmogorov-Smirnov distance that the corrected and measured distributions agree.

Periods (Ward used 1993-1994, 1999-2004, 2005-2010 and 2011-2016, matching NHANES cycles to BRFSS years):

  PERIODS (primary, as in Ward)   BRFSS 2011-2016 <-> NHANES 2011-2012, 2013-2014, 2015-2016 (Ward's last period)
                                  BRFSS 2017-2020 <-> NHANES 2017-March 2020
                                  BRFSS 2021-2025 <-> NHANES August 2021-August 2023 (2024-2025: no NHANES yet, the
                                                      2021-2023 calibration is carried forward)
  PERIODS_FIXED (variant)         one calibration, BRFSS 2011-2020 <-> NHANES 2011-March 2020, applied to every
                                  year, so the corrected series keeps all of the BRFSS change after 2020.

The quantile of each respondent is read from the weighted distribution of the calibration years (the pooled years
of the period; 2011-2020 in the fixed variant), so the correction is one map from reported to corrected BMI per
period and changes within a period, or after 2020 in the fixed variant, are kept.

The functions are pure; the BRFSS input comes from the guarded loader (pre-registration rule) and they are tested on
simulated data only.
"""

import numpy as np
import pandas as pd
from scipy.interpolate import make_smoothing_spline

from glp1_review.survey import weighted_quantile

GRID = np.round(np.arange(0.01, 1.0, 0.01), 2)
NOISE_SD = 0.5
# period: (BRFSS calibration years, BRFSS years corrected, NHANES cycles)
PERIODS = {
    "2011-2016": (range(2011, 2017), range(2011, 2017), ("2011-2012", "2013-2014", "2015-2016")),
    "2017-2020": (range(2017, 2021), range(2017, 2021), ("2017-2020",)),
    "2021-2025": (range(2021, 2026), range(2021, 2026), ("2021-2023",)),
}
PERIODS_FIXED = {
    "2011-2020": (range(2011, 2021), range(2011, 2026), ("2011-2012", "2013-2014", "2015-2016", "2017-2020")),
}


def weighted_rank(x, w, at=None) -> np.ndarray:
    """Mid-point weighted ECDF of (x, w) (ties share the rank of their pooled mass), evaluated at each element of x,
    or at `at` by linear interpolation between the distinct values of x."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    ux, inv = np.unique(x, return_inverse=True)
    mass = np.bincount(inv, weights=w)
    cum = np.cumsum(mass)
    p = (cum - 0.5 * mass) / cum[-1]
    return p[inv] if at is None else np.interp(np.asarray(at, float), ux, p)


def nhanes_weights(n: pd.DataFrame) -> np.ndarray:
    """MEC weights scaled by the years each cycle covers, so pooled cycles count by calendar time."""
    return n["wt"].to_numpy(float) * n["span"].to_numpy(float)


def bias_curve(self_bmi, self_w, meas_bmi, meas_w, grid=GRID):
    """Fitted d(q) = Q_measured(q) - Q_self(q), a cubic smoothing spline (penalty chosen by GCV)."""
    d = weighted_quantile(meas_bmi, meas_w, grid) - weighted_quantile(self_bmi, self_w, grid)
    return make_smoothing_spline(grid, d), d


def ks_distance(x1, w1, x2, w2) -> float:
    """Two-sample Kolmogorov-Smirnov distance between two weighted empirical distributions."""
    x1, w1, x2, w2 = (np.asarray(a, float) for a in (x1, w1, x2, w2))
    pts = np.union1d(x1, x2)

    def ecdf(x, w):
        o = np.argsort(x)
        c = np.cumsum(w[o]) / w.sum()
        return np.concatenate([[0.0], c])[np.searchsorted(x[o], pts, side="right")]

    return float(np.max(np.abs(ecdf(x1, w1) - ecdf(x2, w2))))


def correct(b: pd.DataFrame, nhanes: pd.DataFrame, periods: dict = PERIODS, seed: int = 20261115):
    """Return (corrected copy of b, diagnostics). `b` needs year, sex, bmi, wt; `nhanes` needs cycle, span, sex,
    bmi, wt. Corrected rows get new bmi and obese (BMI >= 30); rows with missing BMI, sex or weight, or outside every
    period, are left missing."""
    rng = np.random.default_rng(seed)
    out = b.copy()
    out["bmi"] = np.nan
    out["obese"] = np.nan
    diag = []
    for period, (calib_years, years, cycles) in periods.items():
        for sex in ("Male", "Female"):
            ok = (b["sex"] == sex) & b["bmi"].notna() & (b["wt"] > 0)
            c = ok & b["year"].isin(list(calib_years))
            m = ok & b["year"].isin(list(years))
            n = nhanes[nhanes["cycle"].isin(cycles) & (nhanes["sex"] == sex)]
            if not c.any() or not m.any() or n.empty:
                continue
            xc, wc = b.loc[c, "bmi"].to_numpy(float), b.loc[c, "wt"].to_numpy(float)
            x, w = b.loc[m, "bmi"].to_numpy(float), b.loc[m, "wt"].to_numpy(float)
            nb, nw = n["bmi"].to_numpy(float), nhanes_weights(n)
            spline, raw = bias_curve(xc, wc, nb, nw)
            q = weighted_rank(xc, wc, at=x)
            adj = x + spline(q) + rng.normal(0.0, NOISE_SD, len(x))
            out.loc[m, "bmi"] = adj
            out.loc[m, "obese"] = (adj >= 30).astype(float)
            diag.append(
                {
                    "period": period,
                    "sex": sex,
                    "n_brfss_calibration": int(c.sum()),
                    "n_brfss": int(m.sum()),
                    "n_nhanes": len(n),
                    "bias_q10": float(spline(0.10)),
                    "bias_q50": float(spline(0.50)),
                    "bias_q90": float(spline(0.90)),
                    "ks_before": ks_distance(x, w, nb, nw),
                    "ks_after": ks_distance(adj, w, nb, nw),
                    "obese_self": float(np.average(x >= 30, weights=w)),
                    "obese_corrected": float(np.average(adj >= 30, weights=w)),
                    "obese_nhanes": float(np.average(nb >= 30, weights=nw)),
                }
            )
    return out, pd.DataFrame(diag)
