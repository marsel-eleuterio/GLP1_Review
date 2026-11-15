"""NHANES measured BMI for the Q24 self-report correction (Ward et al. 2019, appendix section 2).

Source (wwwn.cdc.gov, public-use files, no key needed): the demographics (DEMO) and body measures (BMX) files of
the five NHANES cycles that overlap BRFSS 2011-2025:

  2011-2012 (G), 2013-2014 (H), 2015-2016 (I), 2017-March 2020 pre-pandemic (P_), August 2021-August 2023 (L)

Kept: adults 18+ examined in the mobile examination centre with a measured BMI, excluding pregnant women
(RIDEXPRG == 1), as in Ward et al. (2019, appendix 1.2) and NCHS Data Brief 508. Weight: the MEC examination weight
(WTMEC2YR; WTMECPRP for the 2017-March 2020 file). `span` is the number of years each cycle covers (3.2 for the
2017-March 2020 file), used to pool cycles.

Check (allowed before registration: it reproduces published numbers): age-adjusted obesity prevalence among adults
20+ by cycle, direct method, 2000 projected US population (20-39, 40-59, 60+), against the NCHS Data Brief 508
values in dados_externos/published_estimates.csv.

Writes:
  dados_brutos/nhanes/<file>.xpt                    the ten original files
  dados_brutos/nhanes/provenance_nhanes.csv         URL, bytes, sha256, rows, date
  dados_limpos/nhanes/nhanes_adults.csv.gz          cycle, span, sex, age, bmi, wt, psu, strat
  dados_limpos/nhanes/nhanes_check.csv              reproduced vs published age-adjusted prevalence

Usage:  uv run python scripts/nhanes_download.py
"""

import csv
import hashlib
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "dados_brutos" / "nhanes"
CLEAN = ROOT / "dados_limpos" / "nhanes"
PUBLISHED = ROOT / "dados_externos" / "published_estimates.csv"

UA = {"User-Agent": "glp1-review research script (NHANES public-use files)"}
BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{start}/DataFiles/{name}.xpt"
# cycle label: (first year of the folder, DEMO file, BMX file, MEC weight, years covered)
CYCLES = {
    "2011-2012": (2011, "DEMO_G", "BMX_G", "WTMEC2YR", 2.0),
    "2013-2014": (2013, "DEMO_H", "BMX_H", "WTMEC2YR", 2.0),
    "2015-2016": (2015, "DEMO_I", "BMX_I", "WTMEC2YR", 2.0),
    "2017-2020": (2017, "P_DEMO", "P_BMX", "WTMECPRP", 3.2),
    "2021-2023": (2021, "DEMO_L", "BMX_L", "WTMEC2YR", 2.0),
}
# 2000 projected US population, adults 20+ (NCHS age adjustment for adult obesity)
STD_POP = {"20-39": 77_670_000, "40-59": 72_816_000, "60+": 45_364_000}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path) -> tuple[int, str]:
    if dest.exists():  # .part files are only renamed when complete
        return dest.stat().st_size, sha256(dest)
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
                part.write_bytes(r.read())
            break
        except OSError as e:
            if attempt == 2:
                raise
            print(f"    retry after error: {e}")
            time.sleep(10 * (attempt + 1))
    part.replace(dest)
    return dest.stat().st_size, sha256(dest)


def read_xpt(path: Path) -> pd.DataFrame:
    d = pd.read_sas(path, format="xport", encoding="latin-1")
    d.columns = [c.upper() for c in d.columns]
    return d


def age_adjusted_obesity(d: pd.DataFrame) -> float:
    a = d[d["age"] >= 20]
    grp = pd.cut(a["age"], [19, 39, 59, 200], labels=list(STD_POP))
    total = sum(STD_POP.values())
    out = 0.0
    for g, pop in STD_POP.items():
        s = a[grp == g]
        out += pop / total * np.average(s["bmi"] >= 30, weights=s["wt"])
    return 100 * out


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    CLEAN.mkdir(parents=True, exist_ok=True)
    prov, frames = [], []
    for label, (start, demo, bmx, wcol, span) in CYCLES.items():
        files = {}
        for name in (demo, bmx):
            url = BASE.format(start=start, name=name)
            dest = RAW / f"{name}.xpt"
            size, sha = fetch(url, dest)
            files[name] = read_xpt(dest)
            prov.append(
                {
                    "cycle": label,
                    "file": dest.name,
                    "url": url,
                    "bytes": size,
                    "sha256": sha,
                    "rows": len(files[name]),
                    "accessed": time.strftime("%Y-%m-%d"),
                }
            )
            print(f"{label} {name}: {len(files[name]):,} rows, {size:,} bytes")
        d = files[demo].merge(files[bmx][["SEQN", "BMXBMI"]], on="SEQN", how="inner")
        keep = (d["RIDAGEYR"] >= 18) & d["BMXBMI"].notna() & (d[wcol] > 0) & (d["RIDEXPRG"] != 1)
        d = d[keep]
        frames.append(
            pd.DataFrame(
                {
                    "cycle": label,
                    "span": span,
                    "sex": d["RIAGENDR"].map({1: "Male", 2: "Female"}).to_numpy(),
                    "age": d["RIDAGEYR"].astype(int).to_numpy(),
                    "bmi": d["BMXBMI"].round(1).to_numpy(),
                    "wt": d[wcol].to_numpy(),
                    "psu": d["SDMVPSU"].astype(int).to_numpy(),
                    "strat": d["SDMVSTRA"].astype(int).to_numpy(),
                }
            )
        )
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(CLEAN / "nhanes_adults.csv.gz", index=False)
    with open(RAW / "provenance_nhanes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(prov[0]))
        w.writeheader()
        w.writerows(prov)

    pub = pd.read_csv(PUBLISHED)
    pub = pub[
        (pub["source"] == "NHANES") & (pub["measure"] == "obesity (age-adjusted)") & (pub["group"] == "total")
    ]
    pub = pub.set_index("period")["value_pct"]
    rows = []
    for label, g in out.groupby("cycle"):
        rows.append(
            {
                "cycle": label,
                "n_adults_18plus": len(g),
                "reproduced_pct": round(age_adjusted_obesity(g), 2),
                "published_pct": pub.get(label, np.nan),
            }
        )
    check = pd.DataFrame(rows)
    check["difference_pp"] = (check["reproduced_pct"] - check["published_pct"]).round(2)
    check.to_csv(CLEAN / "nhanes_check.csv", index=False)
    print(check.to_string(index=False))
    bad = check["difference_pp"].abs() > 0.3
    if bad.any():
        raise SystemExit(
            f"Reproduced prevalence differs from the published value by more than 0.3 pp:\n{check[bad]}"
        )
    print(f"ok: {len(out):,} adults written to {CLEAN / 'nhanes_adults.csv.gz'}")


if __name__ == "__main__":
    main()
