"""BRFSS microdata: download, extract the needed columns, and validate against the CDC API tables.

Run this on your own computer (the analysis sandbox cannot reach cdc.gov file downloads).

  python brfss_microdata.py download --out brfss_raw            # 2011-2025 XPT zips (~1 GB), asks before downloading
  python brfss_microdata.py extract  --raw brfss_raw --out brfss_clean
  python brfss_microdata.py validate --clean brfss_clean --api dados
  python brfss_microdata.py selftest                            # checks the logic on synthetic data, no network

Requires: python>=3.9, pandas, numpy. (selftest also uses pyreadstat if installed, to build a fake XPT file.)

What 'validate' does: recomputes weighted adult obesity (BMI >= 30, BRFSS _BMI5CAT == 4, weight _LLCPWT) by
state-year from the microdata and compares it with the numbers the pilot took from the CDC open API
(dados/brfss_ob_total_*.csv and brfss_us_total.csv). Differences up to ~0.15 pp are rounding; larger ones are flagged.
Sample sizes (n) are compared too.

Harmonised columns written by 'extract' (one csv.gz per year):
  year, state (FIPS), abbr, wt (_LLCPWT), psu (_PSU), strat (_STSTR), bmi (_BMI5/100), bmicat (_BMI5CAT),
  age5 (_AGEG5YR), sex (_SEX or SEXVAR), race (_IMPRACE), educ (_EDUCAG), income (_INCOMG or _INCOMG1),
  diab_raw (DIABETE2/3/4), diabetes (1 yes; 0 no or pre-diabetes; NaN pregnancy-only/DK/refused),
  plan_raw (_HLTHPLN or _HLTHPL1 or HLTHPLN1), htm (HTM4, metres), wtkg (WTKG3/100, kg).
A coverage report (coverage_report.csv) says which source column was found for each year; a blank means the column
does not exist that year and has to be checked in the codebook before the analysis uses it.
"""
import argparse
import csv
import hashlib
import io
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

import numpy as np
import pandas as pd

YEARS = list(range(2011, 2026))
BASE = "https://www.cdc.gov/brfss/annual_data/{y}/files/LLCP{y}XPT.{ext}"
UA = {"User-Agent": "Mozilla/5.0 (research script; BRFSS microdata download)"}

FIPS = {1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT", 10: "DE", 11: "DC", 12: "FL", 13: "GA",
        15: "HI", 16: "ID", 17: "IL", 18: "IN", 19: "IA", 20: "KS", 21: "KY", 22: "LA", 23: "ME", 24: "MD",
        25: "MA", 26: "MI", 27: "MN", 28: "MS", 29: "MO", 30: "MT", 31: "NE", 32: "NV", 33: "NH", 34: "NJ",
        35: "NM", 36: "NY", 37: "NC", 38: "ND", 39: "OH", 40: "OK", 41: "OR", 42: "PA", 44: "RI", 45: "SC",
        46: "SD", 47: "TN", 48: "TX", 49: "UT", 50: "VT", 51: "VA", 53: "WA", 54: "WV", 55: "WI", 56: "WY",
        66: "GU", 72: "PR", 78: "VI"}

# output name -> candidate source columns, first one present wins
CANDIDATES = {
    "state": ["_STATE"], "wt": ["_LLCPWT"], "psu": ["_PSU"], "strat": ["_STSTR"],
    # 2026-11-14: SEX (2011-17) and SEX1 (2018) added; same codes as _SEX (1 male, 2 female) plus 7/9 DK/refused
    "bmi5": ["_BMI5"], "bmicat": ["_BMI5CAT"], "age5": ["_AGEG5YR"], "sex": ["_SEX", "SEXVAR", "SEX1", "SEX"],
    "race": ["_IMPRACE"], "educ": ["_EDUCAG"], "income": ["_INCOMG1", "_INCOMG"],
    # 2026-11-14: _HLTHPL2 (2024-25) added; same codes as _HLTHPL1/_HLTHPLN (1 insured, 2 not, 9 DK/missing)
    "diab_raw": ["DIABETE4", "DIABETE3", "DIABETE2"],
    "plan_raw": ["_HLTHPL2", "_HLTHPL1", "_HLTHPLN", "HLTHPLN1"],
    "htm4": ["HTM4"], "wtkg3": ["WTKG3"],
}


# ----------------------------------------------------------------------------------------------- download
def zip_ok(path):
    try:
        with zipfile.ZipFile(path) as z:
            return z.testzip() is None
    except zipfile.BadZipFile:
        return False


def fetch(url, dest):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(dest + ".part", "wb") as f:
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
            done += len(b)
            if total:
                print(f"\r    {done / 1e6:6.1f}/{total / 1e6:.1f} MB", end="", flush=True)
    print()
    os.replace(dest + ".part", dest)


def cmd_download(a):
    os.makedirs(a.out, exist_ok=True)
    years = parse_years(a.years)
    print(f"Will download BRFSS XPT zips for {years[0]}-{years[-1]} ({len(years)} files, about 60 MB each) from cdc.gov into {os.path.abspath(a.out)}")
    if not a.yes and input("Proceed? [y/N] ").strip().lower() != "y":
        print("Cancelled.")
        return
    manifest, failed = [], []
    for y in years:
        dest = os.path.join(a.out, f"LLCP{y}XPT.zip")
        if os.path.exists(dest) and zip_ok(dest):
            print(f"{y}: already there, skipping")
        else:
            got = False
            for ext in ("zip", "ZIP"):   # older years use upper-case .ZIP
                url = BASE.format(y=y, ext=ext)
                try:
                    print(f"{y}: {url}")
                    fetch(url, dest)
                    got = zip_ok(dest)
                    if got:
                        break
                    print("    file is not a valid zip, trying next candidate")
                except (urllib.error.URLError, TimeoutError) as e:
                    print(f"    failed: {e}")
            if not got:
                failed.append(y)
                continue
        h = hashlib.sha256()
        with open(dest, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        manifest.append((y, os.path.basename(dest), os.path.getsize(dest), h.hexdigest()))
    with open(os.path.join(a.out, "manifest_sha256.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "file", "bytes", "sha256"])
        w.writerows(manifest)
    print(f"Done. {len(manifest)} files ok (hashes in manifest_sha256.csv). Failed years: {failed or 'none'}")
    if failed:
        print("For failed years open https://www.cdc.gov/brfss/annual_data/annual_<year>.html, copy the XPT link, "
              "and save the file as LLCP<year>XPT.zip in the same folder.")


# ----------------------------------------------------------------------------------------------- extract
def parse_years(s):
    if not s:
        return YEARS
    if "-" in s:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def harmonise(df_raw, year):
    """df_raw: raw BRFSS columns (any subset). Returns (harmonised df, {output col: source col or ''})."""
    used, out = {}, pd.DataFrame(index=df_raw.index)
    for name, cands in CANDIDATES.items():
        src = next((c for c in cands if c in df_raw.columns), "")
        used[name] = src
        out[name] = pd.to_numeric(df_raw[src], errors="coerce") if src else np.nan
    res = pd.DataFrame({"year": year, "state": out["state"].astype("Int64")})
    res["abbr"] = res["state"].map(FIPS)
    res["wt"], res["psu"], res["strat"] = out["wt"], out["psu"], out["strat"]
    res["bmi"] = out["bmi5"] / 100.0
    res["bmicat"] = out["bmicat"]
    for k in ("age5", "sex", "race", "educ", "income", "diab_raw", "plan_raw"):
        res[k] = out[k]
    res["diabetes"] = out["diab_raw"].map({1: 1, 3: 0, 4: 0})        # 2 (pregnancy only), 7, 9 -> NaN
    res["htm"] = out["htm4"] / 100.0 if used["htm4"] else np.nan      # HTM4: metres with 2 implied decimals
    res["wtkg"] = out["wtkg3"] / 100.0 if used["wtkg3"] else np.nan   # WTKG3 has 2 implied decimals
    return res, used


def read_xpt_zip(path, wanted):
    """Read only wanted columns from the XPT inside a zip. Returns (df, total_rows, all_columns)."""
    with tempfile.TemporaryDirectory() as tmp:
        full = os.path.join(tmp, "data.xpt")
        with zipfile.ZipFile(path) as z:
            # some BRFSS zips name the member with a trailing space ("LLCP2021.XPT "), which Windows cannot
            # extract as is, so the member is copied to a clean name instead of extracted
            member = next(n for n in z.namelist() if n.strip().lower().endswith(".xpt"))
            with z.open(member) as src, open(full, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
        parts, total, cols = [], 0, []
        # the reader is closed before the temporary folder is removed (Windows refuses to delete open files)
        with pd.read_sas(full, format="xport", chunksize=50000, encoding="latin-1") as reader:
            for ch in reader:
                if not cols:
                    cols = list(ch.columns)
                total += len(ch)
                parts.append(ch[[c for c in ch.columns if c in wanted]])
        return pd.concat(parts, ignore_index=True), total, cols


def cmd_extract(a):
    os.makedirs(a.out, exist_ok=True)
    wanted = {c for cands in CANDIDATES.values() for c in cands}
    rows = []
    for y in parse_years(a.years):
        z = os.path.join(a.raw, f"LLCP{y}XPT.zip")
        if not os.path.exists(z):
            print(f"{y}: {z} not found, skipping")
            continue
        t = time.time()
        raw, total, _ = read_xpt_zip(z, wanted)
        res, used = harmonise(raw, y)
        res.to_csv(os.path.join(a.out, f"brfss_{y}.csv.gz"), index=False)
        rows.append({"year": y, "records": total, **{k: v for k, v in used.items()}})
        miss = [k for k, v in used.items() if not v]
        print(f"{y}: {total:,} records, {time.time() - t:.0f}s; columns not found: {miss or 'none'}")
    pd.DataFrame(rows).to_csv(os.path.join(a.out, "coverage_report.csv"), index=False)
    print("coverage_report.csv written (blank = column absent that year; check the codebook).")


# ----------------------------------------------------------------------------------------------- validate
def prevalence(df, by):
    """Weighted share with bmicat == 4 among valid BMI categories (1-4), plus unweighted n."""
    d = df[df["bmicat"].isin([1, 2, 3, 4]) & df["wt"].notna()]
    g = d.assign(w_ob=d["wt"] * (d["bmicat"] == 4)).groupby(by)
    out = pd.DataFrame({"prev": 100 * g["w_ob"].sum() / g["wt"].sum(), "n": g.size()})
    return out


def cmd_validate(a):
    api = pd.concat([pd.read_csv(os.path.join(a.api, f"brfss_ob_total_{p}.csv"))
                     for p in ("2011_2015", "2016_2021", "2022_2025")], ignore_index=True)
    us_api = pd.read_csv(os.path.join(a.api, "brfss_us_total.csv"))
    us_api = us_api[us_api["q"] == "Q036"].set_index("year")
    frames = []
    for y in YEARS:
        p = os.path.join(a.clean, f"brfss_{y}.csv.gz")
        if os.path.exists(p):
            frames.append(pd.read_csv(p, usecols=["year", "abbr", "wt", "bmicat"]))
    if not frames:
        sys.exit("no extracted files found; run 'extract' first")
    df = pd.concat(frames, ignore_index=True)
    mine = prevalence(df, ["year", "abbr"]).reset_index()
    cmp_ = mine.merge(api.rename(columns={"loc": "abbr", "value": "api", "n": "n_api"})[["year", "abbr", "api", "n_api"]],
                      on=["year", "abbr"], how="inner")
    cmp_["diff"] = cmp_["prev"] - cmp_["api"]
    cmp_["n_diff"] = cmp_["n"] - cmp_["n_api"]
    cmp_.to_csv(os.path.join(a.clean, "validation_state_year.csv"), index=False)
    bad = cmp_[cmp_["diff"].abs() > 0.2]
    print(f"state-years compared: {len(cmp_)} | mean abs diff {cmp_['diff'].abs().mean():.3f} pp | "
          f"max {cmp_['diff'].abs().max():.2f} pp | beyond 0.2 pp: {len(bad)} | exact n match: {(cmp_['n_diff'] == 0).mean():.1%}")
    if len(bad):
        print(bad.sort_values("diff", key=abs, ascending=False).head(15).to_string(index=False))
    # national: pooled with and without territories vs CDC 'US' row
    rows = []
    for y, d in df.groupby("year"):
        s50 = d[~d["abbr"].isin(["GU", "PR", "VI"])]
        rows.append({"year": y, "pooled_50_dc": prevalence(s50.assign(k=1), "k")["prev"].iloc[0],
                     "pooled_all": prevalence(d.assign(k=1), "k")["prev"].iloc[0],
                     "api_us": us_api["value"].get(y, np.nan),
                     "n_pooled_all": int(d["bmicat"].isin([1, 2, 3, 4]).sum()), "n_api": us_api["n"].get(y, np.nan)})
    nat = pd.DataFrame(rows)
    nat.to_csv(os.path.join(a.clean, "validation_national.csv"), index=False)
    print(nat.round(2).to_string(index=False))
    print("Files: validation_state_year.csv, validation_national.csv")
    print("Note: the pooled national figure is not exactly the CDC 'US' row (which uses its own state-level weighting); "
          "small gaps there are expected. State-level gaps beyond rounding are the thing to investigate.")


# ----------------------------------------------------------------------------------------------- selftest
def cmd_selftest(_):
    rng = np.random.default_rng(1)
    n = 4000
    raw = pd.DataFrame({
        "_STATE": rng.choice([1, 2, 72], n), "_LLCPWT": rng.uniform(50, 3000, n), "_PSU": np.arange(n),
        "_STSTR": rng.integers(1, 50, n), "_BMI5": rng.integers(1500, 5000, n).astype(float),
        "_AGEG5YR": rng.integers(1, 14, n), "SEXVAR": rng.integers(1, 3, n), "DIABETE4": rng.choice([1, 2, 3, 4, 7], n),
        "HTM4": rng.integers(150, 190, n).astype(float), "WTKG3": rng.integers(5000, 12000, n).astype(float)})
    raw["_BMI5CAT"] = pd.cut(raw["_BMI5"] / 100, [0, 18.5, 25, 30, 99], right=False, labels=[1, 2, 3, 4]).astype(float)
    res, used = harmonise(raw, 2024)
    assert used["sex"] == "SEXVAR" and used["diab_raw"] == "DIABETE4" and used["race"] == "", used
    assert set(res["abbr"].unique()) == {"AL", "AK", "PR"}
    assert res["diabetes"].isna().sum() == raw["DIABETE4"].isin([2, 7]).sum()
    assert abs(res["htm"].max() - 1.89) < 1e-9
    p = prevalence(res, ["year", "abbr"])
    d = res[res["abbr"] == "AL"]
    manual = 100 * (d["wt"] * (d["bmicat"] == 4)).sum() / d["wt"].sum()
    assert abs(p.loc[(2024, "AL"), "prev"] - manual) < 1e-9 and p.loc[(2024, "AL"), "n"] == len(d)
    print("harmonise + prevalence: ok")
    try:
        import pyreadstat
    except ImportError:
        print("pyreadstat not installed: the XPT reading step was not exercised (pip install pyreadstat to test it).")
        return
    with tempfile.TemporaryDirectory() as tmp:
        xpt = os.path.join(tmp, "LLCP2024.XPT")
        pyreadstat.write_xport(raw.drop(columns=[]), xpt, file_format_version=5, table_name="LLCP2024")
        zp = os.path.join(tmp, "LLCP2024XPT.zip")
        with zipfile.ZipFile(zp, "w") as z:
            z.write(xpt, "LLCP2024.XPT ")   # trailing space on purpose, as in some real BRFSS zips
        got, total, cols = read_xpt_zip(zp, {c for v in CANDIDATES.values() for c in v})
        assert total == n and "_LLCPWT" in cols and abs(got["_LLCPWT"].sum() - raw["_LLCPWT"].sum()) < 1e-3
    print("XPT zip read: ok")
    print("selftest passed")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download"); d.add_argument("--out", required=True); d.add_argument("--years"); d.add_argument("--yes", action="store_true")
    e = sub.add_parser("extract"); e.add_argument("--raw", required=True); e.add_argument("--out", required=True); e.add_argument("--years")
    v = sub.add_parser("validate"); v.add_argument("--clean", required=True); v.add_argument("--api", required=True)
    sub.add_parser("selftest")
    a = ap.parse_args()
    {"download": cmd_download, "extract": cmd_extract, "validate": cmd_validate, "selftest": cmd_selftest}[a.cmd](a)


if __name__ == "__main__":
    main()
