"""A simulated data tree with the same file layout and columns as the real extracted data, for pipeline tests.

Effects are planted where the pipeline should find them: obesity rises 0.5 pp a year to 2022 and then bends down;
adults with diabetes lose extra BMI from 2023; MEPS initiators lose BMI; state use is higher where obesity bends more.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from glp1_review.data import FIPS_ABBR, STATES
from glp1_review.paths import PILOT_DATA

YEARS = range(2011, 2026)


def _names() -> dict:
    ab = pd.read_csv(PILOT_DATA / "state-abbrevs.csv")
    a2n = dict(zip(ab["abbreviation"], ab["state"], strict=True))
    return {f: a2n[a] for f, a in FIPS_ABBR.items()}


def build(root: Path, n_per_year: int = 6000, seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    names = _names()
    use = pd.Series(rng.normal(0, 1, len(STATES)), index=STATES)  # latent state use
    clean, raw = root / "dados_limpos", root / "dados_brutos"
    for p in ("brfss", "acs", "census", "meps"):
        (clean / p).mkdir(parents=True, exist_ok=True)
    (raw / "cms").mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- BRFSS
    state_eff = pd.Series(rng.normal(0, 0.15, len(STATES)), index=STATES)
    for y in YEARS:
        n = n_per_year
        st = rng.choice(STATES, n)
        if y == 2025:
            st = np.where(np.isin(st, [6, 28, 32]), 1, st)  # CA, MS, NV missing in 2025
        age5 = rng.integers(1, 14, n)
        sex = rng.integers(1, 3, n)
        diab = (rng.random(n) < 0.08 + 0.01 * age5).astype(float)
        bend = -0.15 * max(0, y - 2022) * (1 + 0.3 * use.reindex(st).to_numpy())
        logit = (
            -0.95
            + 0.025 * (min(y, 2022) - 2015)
            + 0.04 * (age5 - 7) / 3
            + state_eff.reindex(st).to_numpy()
            + 0.6 * diab
            + bend
        )
        bmi = np.exp(rng.normal(np.log(27.3), 0.2, n)) + 3.0 * (logit + 0.95)
        bmi = bmi - 0.8 * diab * (y >= 2023)
        bmicat = np.digitize(bmi, [18.5, 25, 30]) + 1
        race = rng.choice([1, 2, 3, 4, 5, 6], n, p=[0.6, 0.12, 0.05, 0.02, 0.17, 0.04]).astype(float)
        if y in (2015, 2016):
            race[:] = np.nan
        pd.DataFrame(
            {
                "year": y, "state": st, "abbr": [FIPS_ABBR[s] for s in st], "wt": rng.uniform(50, 900, n),
                "psu": rng.integers(0, 40, n), "strat": rng.integers(0, 60, n), "bmi": bmi, "bmicat": bmicat,
                "age5": age5, "sex": sex, "race": race, "educ": rng.integers(1, 5, n), "income": rng.integers(1, 6, n),
                "diab_raw": np.where(diab == 1, 1, 3), "plan_raw": rng.choice([1, 2], n, p=[0.9, 0.1]),
                "diabetes": diab, "htm": np.where(sex == 1, 1.76, 1.62) + rng.normal(0, 0.07, n),
                "wtkg": bmi * 1.7**2,
            }
        ).to_csv(clean / "brfss" / f"brfss_{y}.csv.gz", index=False)  # fmt: skip

    # ---------------------------------------------------------------- ACS cells and Census
    from glp1_review.data import AGE6, EDUC4, RACE5, SEX2

    grid = pd.MultiIndex.from_product(
        [STATES, AGE6, SEX2, RACE5, EDUC4], names=["state_fips", "age", "sex", "race", "educ"]
    ).to_frame(index=False)
    for y in range(2011, 2025):
        grid.assign(year=y, pop=rng.uniform(100, 5000, len(grid)).round(), n=10).to_csv(
            clean / "acs" / f"acs_cells_{y}.csv", index=False
        )
    pop = pd.DataFrame({"state_fips": STATES, "state": [names[s] for s in STATES]})
    for y in range(2020, 2026):
        pop[str(y)] = rng.uniform(4e5, 3e7, len(STATES)).round()
    pop.to_csv(clean / "census" / "adult_pop_state_2020_2025.csv", index=False)

    # ---------------------------------------------------------------- MEPS
    ids = {23: [f"23{i:06d}" for i in range(3000)], 24: [f"24{i:06d}" for i in range(2500)]}
    for y in range(2018, 2025):
        pid = ids[23] + ids[24]
        n = len(pid)
        bmi = np.where(y % 2 == 0, rng.normal(29, 6, n).clip(15, 60), np.nan)
        pd.DataFrame(
            {
                "year": y, "id": pid, "age": rng.integers(18, 85, n), "sex": rng.integers(1, 3, n),
                "race": rng.integers(1, 6, n), "inscov": rng.choice([1, 2, 3], n), "diabetes": (rng.random(n) < 0.12).astype(float),
                "perwt": rng.uniform(1000, 30000, n), "saqwt": rng.uniform(1000, 30000, n), "bmi": bmi,
                "glp1_any": (rng.random(n) < 0.02 + 0.006 * (y - 2018)).astype(int),
            }
        ).to_csv(clean / "meps" / f"meps_persons_{y}.csv.gz", index=False)  # fmt: skip
    for k, yrs in ((23, [2018, 2019, 2020, 2021]), (24, [2019, 2020, 2021, 2022])):
        n = len(ids[k])
        g = rng.choice(["never", "initiator", "late"], n, p=[0.9, 0.06, 0.04])
        G = {f"glp1_{y}": np.zeros(n, int) for y in yrs}
        G[f"glp1_{yrs[2]}"] = (g == "initiator").astype(int)
        G[f"glp1_{yrs[3]}"] = np.isin(g, ["initiator", "late"]).astype(int)
        b0 = rng.normal(31, 6, n).clip(15, 60)
        pd.DataFrame(
            {
                "id": ids[k], "longwt": rng.uniform(1000, 9000, n), "lsaqwt": rng.uniform(1000, 9000, n),
                "varstr": rng.integers(1, 80, n), "varpsu": rng.integers(1, 3, n), "all9rds": 1,
                "bmi_t0": b0, "bmi_t1": b0 + rng.normal(0.2, 2.3, n) - 1.5 * (g == "initiator"), **G,
            }
        ).to_csv(clean / "meps" / f"meps_panel{k}.csv.gz", index=False)  # fmt: skip

    # ---------------------------------------------------------------- CMS
    ab = [FIPS_ABBR[s] for s in STATES]
    m = pd.DataFrame(
        {
            "Prscrbr_Geo_Lvl": "State", "Prscrbr_Geo_Cd": [str(s) for s in STATES], "Prscrbr_Geo_Desc": [names[s] for s in STATES],
            "Gnrc_Name": "Semaglutide", "Tot_Clms": (pop["2024"] * (0.08 + 0.02 * use.to_numpy())).clip(1000),
        }
    )  # fmt: skip
    pd.concat([m, m.assign(Gnrc_Name="Metformin HCl", Tot_Clms=1e6)]).to_csv(
        raw / "cms" / "medicare_partd_state_2024.csv.gz", index=False
    )
    pd.DataFrame({"state": ab, "number_of_prescriptions": rng.uniform(1e4, 5e5, len(ab))}).to_csv(
        raw / "cms" / "medicaid_sdud_glp1_2025.csv.gz", index=False
    )
    e = pd.DataFrame(
        [
            (a, 202500 + mth, pu, "Y" if pu == "U" else "N", rng.uniform(1e5, 3e6))
            for a in ab
            for mth in range(1, 13)
            for pu in ("P", "U")
        ],
        columns=[
            "state_abbreviation",
            "reporting_period",
            "preliminary_or_updated",
            "final_report",
            "total_medicaid_enrollment",
        ],
    )
    e.to_csv(raw / "cms" / "medicaid_enrollment_2021_2025.csv.gz", index=False)
    return {"clean": clean, "raw": raw}
