"""Shared categories and harmonisation of the extracted BRFSS data. The loaders are in prepare.py; the one that
returns outcome variables (prepare.brfss) calls guard.require_registration() first (pre-registration Q18).

Category labels match the ACS post-stratification cells written by scripts/census_download.py.
"""

import numpy as np
import pandas as pd

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
FIPS_ABBR = {
    1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT", 10: "DE", 11: "DC", 12: "FL", 13: "GA", 15: "HI",
    16: "ID", 17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA", 23: "ME", 24: "MD", 25: "MA", 26: "MI",
    27: "MN", 28: "MS", 29: "MO", 30: "MT", 31: "NE", 32: "NV", 33: "NH", 34: "NJ", 35: "NM", 36: "NY", 37: "NC",
    38: "ND", 39: "OH", 40: "OK", 41: "OR", 42: "PA", 44: "RI", 45: "SC", 46: "SD", 47: "TN", 48: "TX", 49: "UT",
    50: "VT", 51: "VA", 53: "WA", 54: "WV", 55: "WI", 56: "WY",
}  # fmt: skip


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
    if "income" in d:
        # _INCOMG (to 2020): 1-4 = <$15k, $15-25k, $25-35k, $35-50k, 5 = $50k+, 9 = unknown. _INCOMG1 (from 2021)
        # splits $50k+ into 5 = $50-100k, 6 = $100-200k, 7 = $200k+; collapsed to 5 so codes mean the same every year.
        out["income"] = d["income"].replace({6: 5, 7: 5})
    return out
