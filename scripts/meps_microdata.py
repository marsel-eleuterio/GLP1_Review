"""MEPS public use files for the GLP-1 study: download, extract, link the panels, and check against the codebooks.

Run this on your own computer (the analysis sandbox cannot download from meps.ahrq.gov).

  python meps_microdata.py download --out meps_raw          # 16 Stata zips (~110 MB), asks before downloading
  python meps_microdata.py extract  --raw meps_raw --out meps_clean
  python meps_microdata.py selftest                         # checks the logic on synthetic files, no network

Files (numbers and links checked on the MEPS site on 13 Nov 2026):
  Full Year Consolidated (FYC), one per year:  2018 HC-209, 2019 HC-216, 2020 HC-224, 2021 HC-233, 2022 HC-243,
                                               2023 HC-251, 2024 HC-256
  Prescribed Medicines (PMED), one per year:   2018 HC-206A, 2019 HC-213A, 2020 HC-220A, 2021 HC-229A,
                                               2022 HC-239A, 2023 HC-248A, 2024 HC-254A
  Four-year longitudinal panels:               Panel 23 (2018-2021) HC-236, Panel 24 (2019-2022) HC-245

Facts that shape the design:
  * Adult BMI (ADBMI42) is collected only in even years: 2018, 2020, 2022, 2024. Height and weight are not public.
  * The same person has BMI twice only in the two four-year panels: Panel 23 in 2018 and 2020 (ADBMI2, ADBMI6),
    Panel 24 in 2020 and 2022 (ADBMI4, ADBMI8).
  * 2020+ files top-code BMI at 50 and bottom-code it at 10; 2018 does not, so bmi_h applies the same coding to 2018.

What 'extract' writes. It only COUNTS: no BMI is compared between GLP-1 users and non-users, so the
pre-registration can still say the outcome-by-exposure data were not analysed.
  meps_persons_<year>.csv.gz     one row per person: weights, design, age, sex, diabetes, BMI (even years), GLP-1 fills
  meps_glp1_fills_<year>.csv.gz  the GLP-1 prescription records (drug name, household name, cost, weight)
  meps_panel23.csv.gz, meps_panel24.csv.gz  panel persons with BMI at two rounds and GLP-1 use in each panel year
  checks.csv                     counts and totals compared with the numbers printed in the MEPS codebooks
  inventory.txt                  counts the pre-registration needs (adults with BMI, GLP-1 users, initiators per panel)

Requires: python>=3.9, pandas, numpy.
"""
import argparse
import csv
import hashlib
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

import numpy as np
import pandas as pd

URL = "https://meps.ahrq.gov/mepsweb/data_files/pufs/{p}/{p}dta.zip"
UA = {"User-Agent": "Mozilla/5.0 (research script; MEPS public use files)"}
FYC = {2018: "h209", 2019: "h216", 2020: "h224", 2021: "h233", 2022: "h243", 2023: "h251", 2024: "h256"}
PMED = {2018: "h206a", 2019: "h213a", 2020: "h220a", 2021: "h229a", 2022: "h239a", 2023: "h248a", 2024: "h254a"}
PANELS = {
    23: {"puf": "h236", "years": [2018, 2019, 2020, 2021], "bmi": [("ADBMI2", 2018), ("ADBMI6", 2020)]},
    24: {"puf": "h245", "years": [2019, 2020, 2021, 2022], "bmi": [("ADBMI4", 2020), ("ADBMI8", 2022)]},
}
GLP1_GENERIC = r"SEMAGLUTIDE|TIRZEPATIDE|LIRAGLUTIDE|DULAGLUTIDE|EXENATIDE|LIXISENATIDE|ALBIGLUTIDE"
GLP1_BRAND = (r"OZEMPIC|WEGOVY|RYBELSUS|MOUNJARO|ZEPBOUND|TRULICITY|VICTOZA|SAXENDA|BYETTA|BYDUREON|ADLYXIN|"
              r"XULTOPHY|SOLIQUA|TANZEUM")

# numbers printed in the MEPS codebooks (unweighted counts unless the name says otherwise)
EXPECTED = {
    ("fyc", 2018): {"records": 30461, "ADBMI42 valid": 18252, "ADBMI42 = -15": 1318, "ADBMI42 = -1": 10891},
    ("fyc", 2020): {"records": 27805, "ADBMI42 valid": 13801, "ADBMI42 = -15": 672, "ADBMI42 = -1": 13332},
    ("fyc", 2022): {"records": 22431, "ADBMI42 valid": 10601, "ADBMI42 = -15": 698, "ADBMI42 = -1": 11132},
    ("fyc", 2024): {"records": 19140, "ADBMI42 valid": 10828, "ADBMI42 = -15": 780, "ADBMI42 = -1": 7532,
                    "DIABDX_M18 = 1": 2285, "DIABDX_M18 = 2": 16743},
    ("pmed", 2024): {"records": 204550, "RXDRGNAM = -15": 7263, "sum of PERWT24F": 3029450238},
    ("long", 24): {"records": 5565, "ALL9RDS = 1": 4883, "sum of LONGWT if ALL9RDS = 1 (millions)": 303.7},
}


def all_files():
    out = [("fyc", y, p) for y, p in FYC.items()] + [("pmed", y, p) for y, p in PMED.items()]
    return out + [("long", k, v["puf"]) for k, v in PANELS.items()]


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
        shutil.copyfileobj(r, f, 1 << 20)
    os.replace(dest + ".part", dest)


def cmd_download(a):
    os.makedirs(a.out, exist_ok=True)
    files = all_files()
    print(f"Will download {len(files)} MEPS Stata zips (about 110 MB in total) from meps.ahrq.gov into {os.path.abspath(a.out)}")
    if not a.yes and input("Proceed? [y/N] ").strip().lower() != "y":
        print("Cancelled.")
        return
    manifest, failed = [], []
    for kind, key, puf in files:
        dest = os.path.join(a.out, f"{puf}dta.zip")
        if not (os.path.exists(dest) and zip_ok(dest)):
            url = URL.format(p=puf)
            print(f"{kind} {key}: {url}")
            try:
                fetch(url, dest)
            except (urllib.error.URLError, TimeoutError) as e:
                print(f"    failed: {e}")
            if not (os.path.exists(dest) and zip_ok(dest)):
                failed.append(puf)
                continue
        else:
            print(f"{kind} {key}: already there, skipping")
        h = hashlib.sha256()
        with open(dest, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        manifest.append((kind, key, puf, os.path.getsize(dest), h.hexdigest()))
    with open(os.path.join(a.out, "manifest_sha256.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "year_or_panel", "puf", "bytes", "sha256"])
        w.writerows(manifest)
    print(f"Done. {len(manifest)} files ok (hashes in manifest_sha256.csv). Failed: {failed or 'none'}")
    if failed:
        print("For a failed file open https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-<number>, "
              "download the Stata version and save it in the same folder as <puf>dta.zip (for example h256dta.zip).")


# ----------------------------------------------------------------------------------------------- reading
def read_dta_zip(path, wanted):
    """Read the wanted columns (upper-case names) from the .dta inside a zip. Returns (df, all column names)."""
    with tempfile.TemporaryDirectory() as tmp:
        full = os.path.join(tmp, "data.dta")
        with zipfile.ZipFile(path) as z:
            member = next(n for n in z.namelist() if n.strip().lower().endswith(".dta"))
            with z.open(member) as src, open(full, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
        with pd.read_stata(full, iterator=True, convert_categoricals=False) as rdr:
            names = list(rdr.variable_labels().keys())
        by_upper = {n.upper(): n for n in names}
        cols = [by_upper[c] for c in wanted if c in by_upper]
        df = pd.read_stata(full, columns=cols, convert_categoricals=False)
    df.columns = [c.upper() for c in df.columns]
    return df, [n.upper() for n in names]


def norm_id(s):
    if pd.api.types.is_numeric_dtype(s):
        return s.astype("Int64").astype(str)
    return s.astype(str).str.strip()


def pick(df, cands):
    return next((c for c in cands if c in df.columns), "")


# ----------------------------------------------------------------------------------------------- checks
def observed(kind, key, df):
    o = {"records": len(df)}
    if kind == "fyc":
        if "ADBMI42" in df:
            b = pd.to_numeric(df["ADBMI42"], errors="coerce")
            o["ADBMI42 valid"] = int((b > 0).sum())
            o["ADBMI42 = -15"] = int((b == -15).sum())
            o["ADBMI42 = -1"] = int((b == -1).sum())
        if "DIABDX_M18" in df:
            d = pd.to_numeric(df["DIABDX_M18"], errors="coerce")
            o["DIABDX_M18 = 1"] = int((d == 1).sum())
            o["DIABDX_M18 = 2"] = int((d == 2).sum())
    elif kind == "pmed":
        if "RXDRGNAM" in df:
            o["RXDRGNAM = -15"] = int((df["RXDRGNAM"].astype(str).str.strip() == "-15").sum())
        w = f"PERWT{key % 100:02d}F"
        if w in df:
            o[f"sum of {w}"] = float(df[w].sum())
    elif kind == "long":
        if "ALL9RDS" in df:
            a = pd.to_numeric(df["ALL9RDS"], errors="coerce") == 1
            o["ALL9RDS = 1"] = int(a.sum())
            if "LONGWT" in df:
                o["sum of LONGWT if ALL9RDS = 1 (millions)"] = round(float(df.loc[a, "LONGWT"].sum()) / 1e6, 1)
    return o


def compare(kind, key, puf, obs):
    rows = []
    exp = EXPECTED.get((kind, key), {})
    for name, val in obs.items():
        e = exp.get(name)
        if e is None:
            status = "no reference here: compare with the codebook"
        else:
            tol = 0.051 if "millions" in name else (max(1.0, 1e-6 * abs(e)) if name.startswith("sum") else 0)
            status = "ok" if abs(val - e) <= tol else "MISMATCH"
        rows.append({"file": puf, "kind": kind, "year_or_panel": key, "check": name, "observed": val,
                     "expected": e, "status": status})
    return rows


# ----------------------------------------------------------------------------------------------- extract
def fyc_spec(y):
    yy = f"{y % 100:02d}"
    return {"id": ["DUPERSID"], "panel": ["PANEL"], "perwt": [f"PERWT{yy}F"], "saqwt": [f"SAQWT{yy}F", f"PSAQWT{yy}F"],
            "varstr": ["VARSTR"], "varpsu": ["VARPSU"], "age": [f"AGE{yy}X", "AGELAST"], "sex": ["SEX"],
            "race": ["RACETHX"], "region": [f"REGION{yy}"], "inscov": [f"INSCOV{yy}"], "povcat": [f"POVCAT{yy}"],
            "diab_raw": ["DIABDX_M18", "DIABDX"], "bmi_raw": ["ADBMI42"]}


def harmonise_fyc(df, y):
    used = {k: pick(df, v) for k, v in fyc_spec(y).items()}
    out = pd.DataFrame(index=df.index)
    out["year"] = y
    for k, src in used.items():
        out[k] = df[src] if src else np.nan
    out["id"] = norm_id(df[used["id"]])
    out["diabetes"] = pd.to_numeric(out["diab_raw"], errors="coerce").map({1: 1, 2: 0})
    b = pd.to_numeric(out["bmi_raw"], errors="coerce")
    out["bmi"] = b.where(b > 0)
    out["bmi_h"] = out["bmi"].clip(10, 50)
    return out, used


def glp1_fills(df, y):
    yy = f"{y % 100:02d}"
    gen = df["RXDRGNAM"].astype(str).str.upper() if "RXDRGNAM" in df else pd.Series("", index=df.index)
    brand = df["RXNAME"].astype(str).str.upper() if "RXNAME" in df else pd.Series("", index=df.index)
    by_gen = gen.str.contains(GLP1_GENERIC, regex=True)
    by_brand = brand.str.contains(GLP1_BRAND, regex=True)
    m = by_gen | by_brand
    f = pd.DataFrame({"year": y, "id": norm_id(df.loc[m, "DUPERSID"]), "rxdrgnam": gen[m], "rxname": brand[m],
                      "by_generic": by_gen[m].astype(int), "by_brand": by_brand[m].astype(int)})
    f["perwt"] = df.loc[m, f"PERWT{yy}F"] if f"PERWT{yy}F" in df else np.nan
    f["cost"] = df.loc[m, f"RXXP{yy}X"] if f"RXXP{yy}X" in df else np.nan
    return f


def cmd_extract(a):
    os.makedirs(a.out, exist_ok=True)
    checks, inv, persons = [], [], {}
    for y, puf in FYC.items():
        z = os.path.join(a.raw, f"{puf}dta.zip")
        if not os.path.exists(z):
            print(f"FYC {y}: {z} not found, skipping")
            continue
        wanted = [c for v in fyc_spec(y).values() for c in v]
        df, _ = read_dta_zip(z, wanted)
        checks += compare("fyc", y, puf, observed("fyc", y, df))
        p, used = harmonise_fyc(df, y)
        miss = [k for k, v in used.items() if not v]
        pz = os.path.join(a.raw, f"{PMED[y]}dta.zip")
        if os.path.exists(pz):
            yy = f"{y % 100:02d}"
            pm, _ = read_dta_zip(pz, ["DUPERSID", "RXRECIDX", "RXDRGNAM", "RXNAME", f"PERWT{yy}F", f"RXXP{yy}X",
                                      "TC1", "TC1S1", "TC1S1_1"])
            checks += compare("pmed", y, PMED[y], observed("pmed", y, pm))
            f = glp1_fills(pm, y)
            f.to_csv(os.path.join(a.out, f"meps_glp1_fills_{y}.csv.gz"), index=False)
            agg = f.groupby("id").agg(glp1_fills=("id", "size"), glp1_cost=("cost", "sum"))
            p = p.merge(agg, left_on="id", right_index=True, how="left")
            p["glp1_fills"] = p["glp1_fills"].fillna(0).astype(int)
            p["glp1_cost"] = p["glp1_cost"].fillna(0.0)
            p["glp1_any"] = (p["glp1_fills"] > 0).astype(int)
            names = f.groupby("rxdrgnam").size().sort_values(ascending=False)
            match = (f"{len(f):,} GLP-1 records: {int(f.by_generic.sum()):,} by Multum name, "
                     f"{int(((f.by_brand == 1) & (f.by_generic == 0)).sum()):,} only by household name")
        else:
            print(f"PMED {y}: {pz} not found; GLP-1 columns left empty")
            p["glp1_fills"], p["glp1_cost"], p["glp1_any"] = np.nan, np.nan, np.nan
            names, match = pd.Series(dtype=int), "no PMED file"
        p.to_csv(os.path.join(a.out, f"meps_persons_{y}.csv.gz"), index=False)
        persons[y] = p[["id", "glp1_any"]]
        adults = pd.to_numeric(p["age"], errors="coerce") >= 18
        w = pd.to_numeric(p["perwt"], errors="coerce").fillna(0)
        share = 100 * (w[adults] * p.loc[adults, "glp1_any"].fillna(0)).sum() / w[adults].sum() if w[adults].sum() else np.nan
        dia = adults & (p["diabetes"] == 1)
        share_d = 100 * (w[dia] * p.loc[dia, "glp1_any"].fillna(0)).sum() / w[dia].sum() if w[dia].sum() else np.nan
        inv.append(f"{y}: {len(p):,} persons, {int(adults.sum()):,} adults, adults with BMI {int((adults & p['bmi'].notna()).sum()):,}, "
                   f"persons with a GLP-1 fill {int(p['glp1_any'].fillna(0).sum()):,} ({match}); weighted % of adults with a "
                   f"GLP-1 fill {share:.2f} (adults with diabetes {share_d:.1f}); columns not found: {miss or 'none'}")
        if len(names):
            inv.append("      drug names: " + ", ".join(f"{k} {v}" for k, v in names.head(8).items()))
        print(inv[-2] if len(names) else inv[-1])

    for k, spec in PANELS.items():
        z = os.path.join(a.raw, f"{spec['puf']}dta.zip")
        if not os.path.exists(z):
            print(f"Panel {k}: {z} not found, skipping")
            continue
        bmi_cols = [c for c, _ in spec["bmi"]]
        wanted = ["DUPERSID", "PANEL", "LONGWT", "LSAQWT", "VARSTR", "VARPSU", "ALL9RDS"] + bmi_cols + \
                 [f"DIABDXY{i}_M18" for i in range(1, 5)]
        df, _ = read_dta_zip(z, wanted)
        checks += compare("long", k, spec["puf"], observed("long", k, df))
        out = pd.DataFrame({"id": norm_id(df["DUPERSID"])})
        for c in ["LONGWT", "LSAQWT", "VARSTR", "VARPSU", "ALL9RDS"] + [f"DIABDXY{i}_M18" for i in range(1, 5)]:
            out[c.lower()] = df[c].values if c in df else np.nan
        for i, (c, yr) in enumerate(spec["bmi"]):
            b = pd.to_numeric(df[c], errors="coerce") if c in df else pd.Series(np.nan, index=df.index)
            out[f"bmi_t{i}"] = b.where(b > 0).values
            out[f"bmi_t{i}_year"] = yr
        for yr in spec["years"]:
            if yr in persons:
                g = persons[yr].drop_duplicates("id").set_index("id")["glp1_any"]
                out[f"glp1_{yr}"] = out["id"].map(g)
            else:
                out[f"glp1_{yr}"] = np.nan
        out.to_csv(os.path.join(a.out, f"meps_panel{k}.csv.gz"), index=False)
        t0, t1 = spec["bmi"][0][1], spec["bmi"][1][1]
        yrs = spec["years"]
        G = out[[f"glp1_{y}" for y in yrs]]
        both = out["bmi_t0"].notna() & out["bmi_t1"].notna()
        known = G.notna().all(axis=1)
        before = G[[f"glp1_{y}" for y in yrs if y <= t0]].fillna(0).sum(axis=1) > 0
        between = G[[f"glp1_{y}" for y in yrs if t0 < y <= t1]].fillna(0).sum(axis=1) > 0
        after_cols = [f"glp1_{y}" for y in yrs if y > t1]
        after = G[after_cols].fillna(0).sum(axis=1) > 0 if after_cols else pd.Series(False, index=out.index)
        never = known & (G.fillna(0).sum(axis=1) == 0)
        line = (f"Panel {k} ({yrs[0]}-{yrs[-1]}, BMI in {t0} and {t1}): {len(out):,} persons, with BMI at both rounds "
                f"{int(both.sum()):,}; among them: never used GLP-1 {int((both & never).sum()):,}, already using by {t0} "
                f"{int((both & before).sum()):,}, started between {t0} and {t1} {int((both & ~before & between).sum()):,}")
        if after_cols:
            line += f", started only after {t1} (placebo group) {int((both & ~before & ~between & after).sum()):,}"
        if not known.all():
            line += f"; GLP-1 status unknown in some year for {int((~known).sum()):,} persons (PMED/FYC year missing)"
        inv.append(line)
        print(line)

    pd.DataFrame(checks).to_csv(os.path.join(a.out, "checks.csv"), index=False)
    with open(os.path.join(a.out, "inventory.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(inv) + "\n")
    bad = [c for c in checks if c["status"] == "MISMATCH"]
    print(f"\nchecks.csv: {len(checks)} checks, {sum(c['status'] == 'ok' for c in checks)} ok against the codebook, "
          f"{len(bad)} mismatches, the rest to compare by hand.")
    for c in bad:
        print(f"  MISMATCH {c['file']} {c['check']}: observed {c['observed']}, codebook {c['expected']}")
    print("inventory.txt written. No BMI was compared between GLP-1 users and non-users.")


# ----------------------------------------------------------------------------------------------- selftest
def cmd_selftest(_):
    rng = np.random.default_rng(5)
    with tempfile.TemporaryDirectory() as raw, tempfile.TemporaryDirectory() as out:
        def write_zip(df, puf):
            p = os.path.join(raw, f"{puf}.dta")
            df.to_stata(p, write_index=False, version=118)
            with zipfile.ZipFile(os.path.join(raw, f"{puf}dta.zip"), "w") as z:
                z.write(p, f"{puf}.dta")
            os.remove(p)

        ids = [f"24{i:08d}" for i in range(400)]
        truth = {}
        for y in (2019, 2020, 2021, 2022):
            yy = f"{y % 100:02d}"
            n = len(ids)
            fyc = pd.DataFrame({"DUPERSID": ids, "PANEL": 24, f"PERWT{yy}F": rng.uniform(1000, 30000, n),
                                "VARSTR": rng.integers(1, 100, n), "VARPSU": rng.integers(1, 3, n),
                                f"AGE{yy}X": rng.integers(0, 90, n), "SEX": rng.integers(1, 3, n),
                                "DIABDX_M18": rng.choice([1, 2, -1], n)})
            if y % 2 == 0:
                fyc["ADBMI42"] = np.where(rng.random(n) < 0.8, rng.uniform(17, 45, n).round(1), -1.0)
            write_zip(fyc, FYC[y])
            users = rng.choice(ids, 40, replace=False)
            rx = pd.DataFrame({"DUPERSID": np.r_[users, rng.choice(ids, 200)],
                               "RXDRGNAM": ["SEMAGLUTIDE"] * 20 + ["TIRZEPATIDE"] * 20 + ["METFORMIN"] * 200,
                               "RXNAME": ["OZEMPIC"] * 20 + ["MOUNJARO"] * 20 + ["GLUCOPHAGE"] * 200})
            rx[f"PERWT{yy}F"] = rng.uniform(1000, 30000, len(rx))
            rx[f"RXXP{yy}X"] = rng.uniform(5, 1200, len(rx))
            write_zip(rx, PMED[y])
            truth[y] = set(users)
        lng = pd.DataFrame({"DUPERSID": ids, "LONGWT": rng.uniform(1000, 9000, len(ids)), "ALL9RDS": rng.choice([0, 1], len(ids)),
                            "ADBMI4": np.where(rng.random(len(ids)) < 0.7, 30.0, -1.0),
                            "ADBMI8": np.where(rng.random(len(ids)) < 0.7, 29.0, -15.0)})
        write_zip(lng, "h245")

        class A:
            pass
        a = A(); a.raw, a.out = raw, out
        print("Running extract on SYNTHETIC files: 'not found' lines and codebook mismatches below are expected.\n")
        cmd_extract(a)
        print()
        for y in (2019, 2020, 2021, 2022):
            p = pd.read_csv(os.path.join(out, f"meps_persons_{y}.csv.gz"), dtype={"id": str})
            assert set(p.loc[p.glp1_any == 1, "id"]) == truth[y], y
        pn = pd.read_csv(os.path.join(out, "meps_panel24.csv.gz"), dtype={"id": str})
        both = pn.bmi_t0.notna() & pn.bmi_t1.notna()
        assert both.sum() == ((lng.ADBMI4 > 0) & (lng.ADBMI8 > 0)).sum()
        pre = pn.id.isin(truth[2019] | truth[2020])
        btw = pn.id.isin(truth[2021] | truth[2022])
        text = open(os.path.join(out, "inventory.txt"), encoding="utf-8").read()
        assert f"started between 2020 and 2022 {int((both & ~pre & btw).sum()):,}" in text, text
        chk = pd.read_csv(os.path.join(out, "checks.csv"))
        assert (chk.loc[(chk.file == "h245") & (chk.check == "records"), "observed"] == len(ids)).all()
    print("selftest passed (Stata zip reading, GLP-1 flags, person-year files, panel linkage, codebook checks)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download"); d.add_argument("--out", required=True); d.add_argument("--yes", action="store_true")
    e = sub.add_parser("extract"); e.add_argument("--raw", required=True); e.add_argument("--out", required=True)
    sub.add_parser("selftest")
    a = ap.parse_args()
    {"download": cmd_download, "extract": cmd_extract, "selftest": cmd_selftest}[a.cmd](a)


if __name__ == "__main__":
    main()
