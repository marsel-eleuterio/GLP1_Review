"""Population data for H1: Census state estimates (Vintage 2025) and ACS 1-year PUMS cells.

Sources (www2.census.gov, no key needed):
  sc-est2025-alldata6.csv   resident population by state, sex, Hispanic origin, race and single year of age,
                            1 July 2020-2025 (Vintage 2025). Kept whole; adult totals derived from it.
  ACS 1-year PUMS person files (csv_pus.zip), 2011-2019, 2021-2024, and the experimental 2020 file.
                            Each zip is downloaded, hashed, reduced to post-stratification cells and deleted
                            (about 600 MB each; use --keep-zips to keep them).

Cells follow the H1 model (Q19): state x age group (18-24, 25-34, 35-44, 45-54, 55-64, 65+) x sex x race and
ethnicity (White, Black, Hispanic, Asian, other or multiracial; Hispanic of any race first, as in BRFSS
_IMPRACE) x education (less than high school, high school or GED, some college or associate degree,
bachelor's or more; as in BRFSS _EDUCAG). Adults 18+ in the 50 states and DC, excluding people in
institutional group quarters (BRFSS samples households): RELP == 16 up to 2018, RELSHIPP == 37 from 2019.

Writes:
  dados_brutos/census/sc-est2025-alldata6.csv
  dados_limpos/census/adult_pop_state_2020_2025.csv        resident 18+ by state and year
  dados_limpos/acs/acs_cells_<year>.csv                     weighted (PWGTP) and unweighted counts per cell
  dados_brutos/census/provenance_census.csv                 URL, bytes, sha256, rows, date

Usage:  uv run python scripts/census_download.py [--years 2011-2024] [--keep-zips]
"""

import argparse
import csv
import hashlib
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

UA = {"User-Agent": "glp1-review research script (Census population data)"}
POPEST = (
    "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/state/asrh/sc-est2025-alldata6.csv"
)
PUMS = "https://www2.census.gov/programs-surveys/acs/data/pums/{y}/1-Year/csv_pus.zip"
PUMS_2020 = "https://www2.census.gov/programs-surveys/acs/experimental/2020/data/pums/1-Year/csv_pus.zip"
STATES = set(range(1, 57)) - {3, 7, 14, 43, 52}  # 50 states + DC (FIPS)
COLS = ["ST", "STATE", "AGEP", "SEX", "RAC1P", "HISP", "SCHL", "PWGTP", "RELP", "RELSHIPP"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path) -> tuple[int, str]:
    if dest.exists():  # left by an interrupted run; .part files are never renamed, so this is complete
        return dest.stat().st_size, sha256(dest)
    part = dest.with_suffix(dest.suffix + ".part")
    h = hashlib.sha256()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
                with open(part, "wb") as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
                        h.update(chunk)
            break
        except OSError as e:
            if attempt == 2:
                raise
            print(f"    retry after error: {e}")
            h = hashlib.sha256()
            time.sleep(10 * (attempt + 1))
    part.replace(dest)
    return dest.stat().st_size, h.hexdigest()


def popest(raw: Path, clean: Path, prov: list[dict]) -> None:
    dest = raw / "sc-est2025-alldata6.csv"
    size, sha = fetch(POPEST, dest)
    d = pd.read_csv(dest, dtype={"STATE": int})
    d = d[(d.SUMLEV == 40) & (d.SEX == 0) & (d.ORIGIN == 0) & (d.AGE >= 18) & d.STATE.isin(STATES)]
    yrs = [c for c in d.columns if c.startswith("POPESTIMATE")]
    adult = d.groupby(["STATE", "NAME"])[yrs].sum().reset_index()
    adult.columns = ["state_fips", "state"] + [int(c[-4:]) for c in yrs]
    adult.to_csv(clean / "adult_pop_state_2020_2025.csv", index=False)
    print(f"Census Vintage 2025: adult (18+) resident population 2025 = {adult[2025].sum():,}")
    prov.append(
        {
            "source": "Census Bureau state population estimates, Vintage 2025 (sc-est2025-alldata6)",
            "year": "2020-2025",
            "url": POPEST,
            "bytes": size,
            "sha256": sha,
            "rows": len(d),
            "note": "kept whole",
        }
    )


def cells(df: pd.DataFrame, year: int) -> pd.DataFrame:
    df = df[(df.AGEP >= 18) & df.ST.isin(STATES)]
    inst = (df.RELSHIPP == 37) if "RELSHIPP" in df and df.RELSHIPP.notna().any() else (df.RELP == 16)
    df = df[~inst]
    age = pd.cut(
        df.AGEP, [17, 24, 34, 44, 54, 64, 200], labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    )
    race = np.select(
        [df.HISP > 1, df.RAC1P == 1, df.RAC1P == 2, df.RAC1P == 6],
        ["Hispanic", "White", "Black", "Asian"],
        "Other or multiracial",
    )
    educ = pd.cut(
        df.SCHL, [0, 15, 17, 20, 24], labels=["Less than HS", "HS or GED", "Some college", "College"]
    )
    out = pd.DataFrame(
        {
            "year": year,
            "state_fips": df.ST,
            "age": age,
            "sex": df.SEX.map({1: "Male", 2: "Female"}),
            "race": race,
            "educ": educ,
            "w": df.PWGTP,
        }
    )
    g = out.groupby(["year", "state_fips", "age", "sex", "race", "educ"], observed=True)
    return g["w"].agg(pop="sum", n="size").reset_index()


def pums_year(y: int, raw: Path, clean: Path, keep: bool, prov: list[dict]) -> None:
    url = PUMS_2020 if y == 2020 else PUMS.format(y=y)
    z = raw / f"acs_pums_{y}_csv_pus.zip"
    t = time.time()
    size, sha = fetch(url, z)
    parts, total = [], 0
    with zipfile.ZipFile(z) as zf:
        for name in [n for n in zf.namelist() if n.lower().endswith(".csv")]:
            with zf.open(name) as f:
                raw_header = f.readline().decode().rstrip().split(",")
            header = [c.strip().upper() for c in raw_header]
            use = [orig for orig, up in zip(raw_header, header, strict=True) if up in COLS]
            with zf.open(name) as f:
                for ch in pd.read_csv(f, usecols=use, chunksize=500_000):
                    ch.columns = [c.strip().upper() for c in ch.columns]
                    ch = ch.rename(columns={"STATE": "ST"})  # renamed from ST in the 2024 file
                    total += len(ch)
                    parts.append(cells(ch, y))
    c = pd.concat(parts).groupby(["year", "state_fips", "age", "sex", "race", "educ"], observed=True)[
        ["pop", "n"]
    ]
    c = c.sum().reset_index()
    c.to_csv(clean / f"acs_cells_{y}.csv", index=False)
    if not keep:
        z.unlink()
    print(
        f"ACS {y}: {total:,} person records, {len(c):,} cells, adult household pop {c['pop'].sum():,.0f} "
        f"({time.time() - t:.0f}s)"
    )
    prov.append(
        {
            "source": f"ACS 1-year PUMS person file {y}" + (" (experimental weights)" if y == 2020 else ""),
            "year": y,
            "url": url,
            "bytes": size,
            "sha256": sha,
            "rows": total,
            "note": "zip kept" if keep else "zip deleted after building cells",
        }
    )


def write_prov(raw: Path, prov: list[dict]) -> None:
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = raw / "provenance_census.csv"
    old = []
    if path.exists():
        with open(path, newline="") as f:
            old = [r for r in csv.DictReader(f) if str(r["year"]) not in {str(p["year"]) for p in prov}]
    rows = old + [{**p, "downloaded_utc": stamp} for p in prov]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", default="2011-2024")
    ap.add_argument("--keep-zips", action="store_true")
    ap.add_argument("--skip-popest", action="store_true")
    a = ap.parse_args()
    raw, clean_c, clean_a = Path("dados_brutos/census"), Path("dados_limpos/census"), Path("dados_limpos/acs")
    for p in (raw, clean_c, clean_a):
        p.mkdir(parents=True, exist_ok=True)
    lo, hi = (int(x) for x in a.years.split("-"))
    if not a.skip_popest:
        prov = []
        popest(raw, clean_c, prov)
        write_prov(raw, prov)
    for y in range(lo, hi + 1):
        prov = []
        pums_year(y, raw, clean_a, a.keep_zips, prov)
        write_prov(raw, prov)  # after every year, so a failure keeps what is done
    print("Done. provenance_census.csv written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
