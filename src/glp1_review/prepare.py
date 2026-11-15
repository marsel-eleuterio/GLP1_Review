"""Build the inputs of each pre-registered analysis from the extracted files.

Every function that touches outcome data (BMI, obesity, height, or BMI by GLP-1 use) calls
guard.require_registration() first. Exposure inputs (CMS, Census, RX Index) carry no outcome and are not guarded.
`Sources` points at the data folders, so the pipeline can be tested on a simulated tree with the same layout.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from glp1_review import h1_mrp, h5_microsim
from glp1_review.data import AGE6, STATES, harmonise_brfss
from glp1_review.guard import require_registration
from glp1_review.h3_quantiles import NOT_AVAILABLE
from glp1_review.h6_panel import classify_groups, merge_sparse
from glp1_review.paths import CLEAN, PILOT_DATA, RAW

YEARS = tuple(range(2011, 2026))
GLP1_GENERIC = (
    "semaglutide",
    "tirzepatide",
    "liraglutide",
    "dulaglutide",
    "exenatide",
    "lixisenatide",
    "albiglutide",
)
MEPS_RACE = {1: "Hispanic", 2: "White", 3: "Black", 4: "Asian", 5: "Other or multiracial"}
H6_PANELS = {23: ([2018, 2019, 2020, 2021], 2018, 2020), 24: ([2019, 2020, 2021, 2022], 2020, 2022)}


@dataclass
class Sources:
    clean: Path = CLEAN
    raw: Path = RAW
    pilot_data: Path = PILOT_DATA


DEFAULT = Sources()


def _name_to_abbr(src: Sources) -> dict:
    ab = pd.read_csv(src.pilot_data / "state-abbrevs.csv")
    return dict(zip(ab["state"], ab["abbreviation"], strict=True))


# --------------------------------------------------------------------------------------------- BRFSS (guarded)
def brfss(src: Sources = DEFAULT, years=YEARS) -> pd.DataFrame:
    """Harmonised BRFSS rows, 50 states + DC. Years without the race variable get race = "Not available"."""
    require_registration()
    frames = []
    for y in years:
        d = pd.read_csv(src.clean / "brfss" / f"brfss_{y}.csv.gz")
        h = harmonise_brfss(d[d["state"].isin(STATES)])
        if h["race"].isna().all():
            h["race"] = NOT_AVAILABLE
        h["age50_64"] = h["age5"].isin([7, 8, 9]).astype(float)
        h["women"] = (h["sex"] == "Female").astype(float).where(h["sex"].notna())
        frames.append(h)
    return pd.concat(frames, ignore_index=True)


def nhanes(src: Sources = DEFAULT) -> pd.DataFrame:
    """NHANES adults 18+ with measured BMI (scripts/nhanes_download.py), for the Q24 self-report correction.
    External measured data, not a study outcome: not guarded."""
    return pd.read_csv(src.clean / "nhanes" / "nhanes_adults.csv.gz")


def h1_inputs(b: pd.DataFrame, src: Sources = DEFAULT) -> dict:
    """Per year: MRP cells, z (previous-year direct estimate), ACS frame, whether race enters."""
    direct = h1_mrp.direct_estimates(b)
    out = {}
    for y in sorted(b["year"].unique()):
        d = b[b["year"] == y].copy()
        use_race = not (d["race"] == NOT_AVAILABLE).all()
        if not use_race:
            d["race"] = np.nan
        out[int(y)] = {
            "cells": h1_mrp.cell_counts(d),
            "z": h1_mrp.z_previous(direct, int(y)),
            "frame": pd.read_csv(src.clean / "acs" / f"acs_cells_{min(int(y), 2024)}.csv"),
            "use_race": use_race,
        }
    return out


def adults_millions(src: Sources = DEFAULT, years=(2023, 2024, 2025)) -> dict:
    pop = pd.read_csv(src.clean / "census" / "adult_pop_state_2020_2025.csv")
    return {y: float(pop[str(y)].sum()) / 1e6 for y in years}


def h4_outcome(b: pd.DataFrame) -> pd.DataFrame:
    """Direct weighted obesity prevalence (pp) by state (postal code) and year."""
    d = h1_mrp.direct_estimates(b)
    fips2abbr = b.drop_duplicates("state").set_index("state")["abbr"]
    return pd.DataFrame({"state": d["state"].map(fips2abbr), "year": d["year"], "y": 100 * d["p"]})


# --------------------------------------------------------------------------------------------- exposure (no outcome)
def h4_exposure(src: Sources = DEFAULT) -> pd.DataFrame:
    """The three state use indicators (Q12): Medicare Part D GLP-1 claims per 100 adult residents (2024), Medicaid
    GLP-1 prescriptions per 1,000 enrollees (2025), all-payer prescriptions per 100 residents (2024)."""
    n2a = _name_to_abbr(src)
    pop = pd.read_csv(src.clean / "census" / "adult_pop_state_2020_2025.csv")
    pop["abbr"] = pop["state"].map(n2a)
    adults24 = pop.set_index("abbr")["2024"]

    m = pd.read_csv(src.raw / "cms" / "medicare_partd_state_2024.csv.gz", dtype={"Prscrbr_Geo_Cd": str})
    glp = m[m["Gnrc_Name"].str.lower().str.contains("|".join(GLP1_GENERIC), na=False)]
    claims = glp.groupby(glp["Prscrbr_Geo_Desc"].map(n2a))["Tot_Clms"].sum()

    s = pd.read_csv(src.raw / "cms" / "medicaid_sdud_glp1_2025.csv.gz")
    rx = s[s["state"].isin(adults24.index)].groupby("state")["number_of_prescriptions"].sum()
    e = pd.read_csv(src.raw / "cms" / "medicaid_enrollment_2021_2025.csv.gz")
    e = e[e["reporting_period"] // 100 == 2025].copy()
    e["rank"] = np.where(e["final_report"] == "Y", 0, np.where(e["preliminary_or_updated"] == "U", 1, 2))
    e = e.sort_values("rank").drop_duplicates(["state_abbreviation", "reporting_period"])
    enrol = (
        pd.to_numeric(e["total_medicaid_enrollment"], errors="coerce").groupby(e["state_abbreviation"]).mean()
    )

    r = pd.read_csv(src.pilot_data / "rxindex_medicaid_2025.csv")
    allpayer = r.set_index(r["state"].map(n2a))["publisher_map_audit_per_100_residents_2024"]

    out = pd.DataFrame(
        {
            "medicare_claims_per100_adults_2024": 100 * claims / adults24,
            "medicaid_rx_per1000_enrollees_2025": 1000 * rx / enrol,
            "allpayer_rx_per100_2024": allpayer,
        }
    )
    return out.dropna()


# --------------------------------------------------------------------------------------------- MEPS (guarded)
def h5_inputs(b: pd.DataFrame, src: Sources = DEFAULT) -> dict:
    """BRFSS 2025 adults with BMI; MEPS 2024 probability of GLP-1 use by BMI class x diabetes; MEPS 2024 adult rate."""
    require_registration()
    d = b[(b["year"] == 2025) & b["bmi"].notna() & b["diabetes"].notna()]
    m = pd.read_csv(src.clean / "meps" / "meps_persons_2024.csv.gz")
    adults = m[pd.to_numeric(m["age"], errors="coerce") >= 18]
    rate = float(np.average(adults["glp1_any"], weights=adults["perwt"]))
    a = adults[adults["bmi"].notna() & adults["diabetes"].notna()].copy()
    a["w"] = a["saqwt"].where(a["saqwt"] > 0, a["perwt"])
    a["cls"] = h5_microsim.bmi_class(a["bmi"].to_numpy())
    a = a[a["cls"] > 0]
    p = a.groupby(["cls", "diabetes"]).apply(
        lambda g: np.average(g["glp1_any"], weights=g["w"]), include_groups=False
    )
    use = p.rename("p").to_frame()
    use.index = use.index.set_levels([use.index.levels[0].astype(int), use.index.levels[1].astype(int)])
    return {
        "bmi": d["bmi"].to_numpy(),
        "diab": d["diabetes"].astype(int).to_numpy(),
        "w": d["wt"].to_numpy(),
        "use_prob": use,
        "meps_rate": rate,
    }


def h6_frame(src: Sources = DEFAULT, all_rounds: bool = True) -> pd.DataFrame:
    """Panels 23 and 24 with group, BMI change and baseline covariates (Q12-Q15, Q19, Q23).
    all_rounds=False keeps persons not present in all nine rounds (Q24 sensitivity)."""
    require_registration()
    parts = []
    for k, (yrs, t0, t1) in H6_PANELS.items():
        p = pd.read_csv(src.clean / "meps" / f"meps_panel{k}.csv.gz", dtype={"id": str})
        per = pd.read_csv(src.clean / "meps" / f"meps_persons_{t0}.csv.gz", dtype={"id": str})
        p["group"] = classify_groups(p, yrs, t0, t1)
        p = p.merge(per[["id", "age", "sex", "race", "inscov", "diabetes"]], on="id", how="left")
        p["panel"] = k
        parts.append(p)
    df = pd.concat(parts, ignore_index=True)
    df = df[
        ((df["all9rds"] == 1) | (not all_rounds))
        & df["bmi_t0"].notna()
        & df["bmi_t1"].notna()
        & (df["age"] >= 18)
        & df["group"].notna()
    ]
    df = df.assign(
        bmi_t0=df["bmi_t0"].clip(10, 50),
        dbmi=df["bmi_t1"].clip(10, 50) - df["bmi_t0"].clip(10, 50),
        age_group=pd.cut(df["age"], [17, 24, 34, 44, 54, 64, 200], labels=AGE6).astype(object),
        sex=df["sex"].map({1: "Male", 2: "Female"}),
        race=df["race"].map(MEPS_RACE),
        diabetes0=df["diabetes"],
        insured0=df["inscov"].isin([1, 2]).astype(float),
    )
    df["age_group"] = merge_sparse(df, "age_group", order=list(AGE6))
    df["race"] = merge_sparse(df, "race")
    return df.reset_index(drop=True)
