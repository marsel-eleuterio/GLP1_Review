"""Loaders and harmonisation of the extracted data. Every loader that returns outcome variables (BMI, obesity,
height) calls guard.require_registration() first (pre-registration Q18).

Category labels match the ACS post-stratification cells written by scripts/census_download.py.
"""

import numpy as np
import pandas as pd

from glp1_review.guard import require_registration
from glp1_review.paths import CLEAN, CLEAN_BRFSS

AGE6 = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
RACE5 = ["White", "Black", "Hispanic", "Asian", "Other or multiracial"]
EDUC4 = ["Less than HS", "HS or GED", "Some college", "College"]
SEX2 = ["Male", "Female"]

# Census divisions by state FIPS (50 states + DC)
DIVISION = {
    9: 1, 23: 1, 25: 1, 33: 1, 44: 1, 50: 1,
    34: 2, 36: 2, 42: 2,
    17: 3, 18: 3, 26: 3, 39: 3, 55: 3,
    19: 4, 20: 4, 27: 4, 29: 4, 31: 4, 38: 4, 46: 4,
    10: 5, 11: 5, 12: 5, 13: 5, 24: 5, 37: 5, 45: 5, 51: 5, 54: 5,
    1: 6, 21: 6, 28: 6, 47: 6,
    5: 7, 22: 7, 40: 7, 48: 7,
    4: 8, 8: 8, 16: 8, 30: 8, 32: 8, 35: 8, 49: 8, 56: 8,
    2: 9, 6: 9, 15: 9, 41: 9, 53: 9,
}  # fmt: skip
STATES = sorted(DIVISION)


def harmonise_brfss(d: pd.DataFrame) -> pd.DataFrame:
    """Map BRFSS codes to the shared categories. Unknown codes -> NaN."""
    out = d.copy()
    out["age_group"] = pd.cut(d["age5"], [0, 1, 3, 5, 7, 9, 13], labels=AGE6).astype(object)
    out["sex"] = d["sex"].map({1: "Male", 2: "Female"})
    out["race"] = d["race"].map(
        {
            1: "White",
            2: "Black",
            3: "Asian",
            4: "Other or multiracial",
            5: "Hispanic",
            6: "Other or multiracial",
        }
    )
    out["educ"] = d["educ"].map(dict(zip([1, 2, 3, 4], EDUC4, strict=True)))
    out["obese"] = np.where(d["bmicat"].isin([1, 2, 3, 4]), (d["bmicat"] == 4).astype(float), np.nan)
    out["insured"] = d["plan_raw"].map({1: 1.0, 2: 0.0})
    return out


def load_brfss(years=range(2011, 2026), columns=None) -> pd.DataFrame:
    """Harmonised BRFSS microdata, 50 states + DC. Contains outcomes: requires the registration."""
    require_registration()
    frames = []
    for y in years:
        d = pd.read_csv(CLEAN_BRFSS / f"brfss_{y}.csv.gz", usecols=columns)
        frames.append(harmonise_brfss(d[d["state"].isin(STATES)]))
    return pd.concat(frames, ignore_index=True)


def load_acs_cells(year: int) -> pd.DataFrame:
    """ACS post-stratification cells (no outcome; no guard). 2025 uses the 2024 frame (Q19)."""
    y = min(year, 2024)
    return pd.read_csv(CLEAN / "acs" / f"acs_cells_{y}.csv")


def load_adult_population() -> pd.DataFrame:
    return pd.read_csv(CLEAN / "census" / "adult_pop_state_2020_2025.csv")
