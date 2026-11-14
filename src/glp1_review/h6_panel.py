"""H6: within-person BMI change of GLP-1 initiators vs never-users in MEPS Panels 23 and 24 (pre-registration Q19).

Primary model, pooled over both panels, among adults with BMI at both rounds who are initiators or never-users:
    dBMI_i = a + b*Init_i + d*Panel24_i + f(BMI_t0) + X_i'g + e_i
f = linear + quadratic in baseline BMI; X = age group, sex, race and ethnicity, baseline diabetes, baseline insurance.
Weights LSAQWT (LONGWT where LSAQWT is missing), design-based SEs with VARSTR/VARPSU (strata nested in panel).
Placebo (Panel 23): late initiators vs never-users (b_late). Not-yet-treated (Panel 23): initiators vs late initiators
(b_nyt). Groups are coded upstream in column `group` in {"initiator", "never", "late", "prevalent"}.
"""

import numpy as np
import pandas as pd

from glp1_review.decision import Estimate
from glp1_review.survey import DesignFit, wls_design

COVARIATES = ["age_group", "sex", "race", "diabetes0", "insured0"]


def design_matrix(df: pd.DataFrame, treat_col: str) -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    X["const"] = 1.0
    X[treat_col] = df[treat_col].astype(float)
    if df["panel"].nunique() > 1:
        X["panel24"] = (df["panel"] == 24).astype(float)
    b0 = df["bmi_t0"] - 30.0  # centred for numerical stability
    X["bmi0"] = b0
    X["bmi0_sq"] = b0**2
    for c in COVARIATES:
        if c in df and df[c].nunique() > 1:
            X = X.join(pd.get_dummies(df[c].astype(str), prefix=c, drop_first=True, dtype=float))
    return X


def _fit(df: pd.DataFrame, treat_col: str) -> DesignFit:
    w = df["lsaqwt"].where(df["lsaqwt"] > 0, df.get("longwt"))
    strata = df["panel"].astype(str) + "_" + df["varstr"].astype(str)
    return wls_design(design_matrix(df, treat_col), df["dbmi"], w, strata, df["varpsu"])


def fit_primary(df: pd.DataFrame) -> tuple[Estimate, DesignFit]:
    d = df[df["group"].isin(["initiator", "never"])].copy()
    d["init"] = d["group"] == "initiator"
    fit = _fit(d, "init")
    return Estimate(*fit.get("init")), fit


def fit_placebo_late(df: pd.DataFrame) -> tuple[Estimate, DesignFit]:
    d = df[(df["panel"] == 23) & df["group"].isin(["late", "never"])].copy()
    d["late"] = d["group"] == "late"
    fit = _fit(d, "late")
    return Estimate(*fit.get("late")), fit


def fit_not_yet_treated(df: pd.DataFrame) -> tuple[Estimate, DesignFit]:
    d = df[(df["panel"] == 23) & df["group"].isin(["initiator", "late"])].copy()
    d["init"] = d["group"] == "initiator"
    fit = _fit(d, "init")
    return Estimate(*fit.get("init")), fit


def n_initiators(df: pd.DataFrame) -> int:
    return int((df["group"] == "initiator").sum())


def classify_groups(glp1: pd.DataFrame, years: list[int], t0: int, t1: int) -> pd.Series:
    """Group from yearly GLP-1 purchase flags (columns glp1_<year>): never, prevalent (by t0), initiator
    (first purchase in (t0, t1]), late (first purchase after t1); NaN if any year is unknown."""
    G = glp1[[f"glp1_{y}" for y in years]]
    known = G.notna().all(axis=1)
    before = G[[f"glp1_{y}" for y in years if y <= t0]].fillna(0).sum(axis=1) > 0
    between = G[[f"glp1_{y}" for y in years if t0 < y <= t1]].fillna(0).sum(axis=1) > 0
    after_cols = [f"glp1_{y}" for y in years if y > t1]
    after = G[after_cols].fillna(0).sum(axis=1) > 0 if after_cols else pd.Series(False, index=G.index)
    g = np.select(
        [before, between, after, G.fillna(0).sum(axis=1) == 0],
        ["prevalent", "initiator", "late", "never"],
        default="unknown",
    )
    return pd.Series(np.where(known, g, None), index=G.index)
