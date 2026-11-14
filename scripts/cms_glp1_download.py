"""Download state-level GLP-1 use from CMS for H4: Medicare Part D (2019-2024) and Medicaid State Drug
Utilization Data (2021-2025), plus Medicaid enrollment (denominator).

Sources (official APIs, no key needed):
  Medicare Part D Prescribers - by Geography and Drug, one data.cms.gov dataset per year
      (ids from https://data.cms.gov/data.json). All rows with Prscrbr_Geo_Lvl = State are saved, so the
      GLP-1 selection can be audited and redone.
  Medicaid State Drug Utilization Data <year>, data.medicaid.gov datastore. Rows are selected on the
      server by product_name prefixes (names are truncated to 10 characters); every distinct name kept is
      listed in medicaid_sdud_product_names.csv for review.
  State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data (monthly), 2021-2025.

Writes (default dados_brutos/cms):
  medicare_partd_state_<year>.csv.gz      all state-level drug rows
  medicaid_sdud_glp1_<year>.csv.gz        GLP-1 rows (all states, quarters, utilization types)
  medicaid_sdud_product_names.csv         distinct product names kept, by year, with prescription totals
  medicaid_enrollment_2021_2025.csv.gz    monthly enrollment rows
  provenance_cms.csv                      source, dataset id, release date, query, rows, bytes, sha256

Usage:  uv run python scripts/cms_glp1_download.py
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "glp1-review research script (CMS GLP-1 state data)"}

PARTD_TITLE = "Medicare Part D Prescribers - by Geography and Drug"
PARTD_PREFERRED = {2024: "c8ea3f8e-3a09-4fea-86f2-8902fb4b0920"}  # the id cited in the pre-registration (Q7)
PARTD_YEARS = range(2019, 2025)

SDUD_IDS = {  # data.medicaid.gov identifiers, State Drug Utilization Data (modified 2026-07-13)
    2021: "eec7fbe6-c4c4-5915-b3d0-be5828ef4e9d",
    2022: "200c2cba-e58d-4a95-aa60-14b99736808d",
    2023: "d890d3a9-6b00-43fd-8b31-fcba4c8e2909",
    2024: "61729e5a-7aa8-448c-8903-ba3e0cd0ea3c",
    2025: "158a1baa-5506-400a-8ec3-97756f0b0536",
}
ENROLL_ID = "6165f45b-ca93-5bb5-9d06-db29c692a360"
# brand and generic prefixes of GLP-1 receptor agonists (incl. tirzepatide and insulin combinations)
SDUD_PREFIXES = [
    "OZEMPIC",
    "WEGOVY",
    "RYBELSUS",
    "MOUNJARO",
    "ZEPBOUND",
    "TRULICITY",
    "VICTOZA",
    "SAXENDA",
    "BYETTA",
    "BYDUREON",
    "ADLYXIN",
    "XULTOPHY",
    "SOLIQUA",
    "TANZEUM",
    "SEMAGLUT",
    "TIRZEPAT",
    "LIRAGLUT",
    "DULAGLUT",
    "EXENATID",
    "EXANATID",
    "LIXISENA",
    "ALBIGLUT",
]
GLP1_GENERIC = (
    "semaglutide",
    "tirzepatide",
    "liraglutide",
    "dulaglutide",
    "exenatide",
    "lixisenatide",
    "albiglutide",
)

PAGE = 5000


def get_json(url: str, tries: int = 4):
    for i in range(tries):
        try:
            # 60 s without any data counts as a stalled connection (a 09:15 run hung on one)
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except OSError as e:
            if i == tries - 1:
                raise
            print(f"    retry after error: {e}")
            time.sleep(5 * (i + 1))


def write_csv_gz(path: Path, rows: list[dict]) -> tuple[int, str]:
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    data = buf.getvalue().encode("utf-8")
    with gzip.GzipFile(path, "wb", mtime=0) as f:  # mtime=0: same content -> same bytes -> same hash
        f.write(data)
    return path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv_gz(path: Path) -> list[dict]:
    """Rows of a file written by an earlier run (reused instead of downloading again)."""
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def stamp(path: Path) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime))


def write_prov(out: Path, prov: list[dict]) -> None:
    """Written after every item, so an interrupted run keeps the provenance of what it finished."""
    with open(out / "provenance_cms.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(prov[0].keys()))
        w.writeheader()
        w.writerows(prov)


# ------------------------------------------------------------------------------------------- Medicare
def partd_ids() -> dict[int, tuple[str, str]]:
    cat = get_json("https://data.cms.gov/data.json")
    out = {}
    for ds in cat["dataset"]:
        if not ds["title"].startswith(PARTD_TITLE):
            continue
        for d in ds.get("distribution", []):
            url = d.get("accessURL", "")
            if "data-api/v1/dataset/" not in url:
                continue
            year = int(d.get("title", "").rsplit(":", 1)[-1].strip()[:4])
            dsid = url.split("/dataset/")[1].split("/")[0]
            if year in PARTD_PREFERRED and dsid != PARTD_PREFERRED[year]:
                continue
            out.setdefault(year, (dsid, d.get("modified", ds.get("modified", ""))))
    return out


def medicare(out: Path, prov: list[dict]) -> None:
    ids = partd_ids()
    for y in PARTD_YEARS:
        dsid, modified = ids[y]
        base = f"https://data.cms.gov/data-api/v1/dataset/{dsid}/data"
        flt = "filter[Prscrbr_Geo_Lvl]=State"
        expected = get_json(f"{base}/stats?{flt}")["found_rows"]
        path = out / f"medicare_partd_state_{y}.csv.gz"
        if path.exists():
            rows = read_csv_gz(path)
            size, sha = path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            rows, offset = [], 0
            while True:
                page = get_json(f"{base}?{flt}&size={PAGE}&offset={offset}")
                rows += page
                if len(page) < PAGE:
                    break
                offset += PAGE
            size, sha = write_csv_gz(path, rows)
        glp1 = sum(any(g in r["Gnrc_Name"].lower() for g in GLP1_GENERIC) for r in rows)
        ok = len(rows) == expected
        print(
            f"Medicare {y}: {len(rows):,} state rows (API stats {expected:,}) {'ok' if ok else 'MISMATCH'}; "
            f"GLP-1 rows {glp1}"
        )
        prov.append(
            {
                "source": "Medicare Part D by Geography and Drug",
                "year": y,
                "dataset_id": dsid,
                "released_or_modified": modified,
                "query": f"{base}?{flt}",
                "rows": len(rows),
                "rows_expected": expected,
                "file": path.name,
                "bytes": size,
                "sha256": sha,
                "downloaded_utc": stamp(path),
            }
        )
        write_prov(out, prov)


# ------------------------------------------------------------------------------------------- Medicaid
def dkan_query(dsid: str, params: list[tuple[str, str]], count_only: bool = False, page: int = PAGE):
    base = f"https://data.medicaid.gov/api/1/datastore/query/{dsid}/0"
    if count_only:
        d = get_json(base + "?" + urllib.parse.urlencode(params + [("count", "true"), ("results", "false")]))
        return [], d.get("count"), base
    rows, offset = [], 0
    while True:
        q = params + [("limit", str(page)), ("offset", str(offset)), ("count", "true")]
        d = get_json(base + "?" + urllib.parse.urlencode(q))
        rows += d["results"]
        if len(d["results"]) < page:
            return rows, d.get("count"), base
        offset += page


def medicaid_modified() -> dict[str, str]:
    meta = get_json(
        "https://data.medicaid.gov/api/1/metastore/schemas/dataset/items?show-reference-ids=false"
    )
    return {ds["identifier"]: ds.get("modified", "") for ds in meta}


def medicaid(out: Path, prov: list[dict]) -> None:
    modified = medicaid_modified()
    names = []
    for y, dsid in SDUD_IDS.items():
        path = out / f"medicaid_sdud_glp1_{y}.csv.gz"
        reuse = path.exists()
        rows, counts = [], 0
        for pre in SDUD_PREFIXES:
            r, c, base = dkan_query(
                dsid,
                [
                    ("conditions[0][property]", "product_name"),
                    ("conditions[0][value]", f"{pre}%"),
                    ("conditions[0][operator]", "like"),
                ],
                count_only=reuse,
            )
            rows += r
            counts += c or 0
        if reuse:
            rows = read_csv_gz(path)
            size, sha = path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            size, sha = write_csv_gz(path, rows)
        tot = {}
        for r in rows:
            n = r["number_of_prescriptions"]
            tot[r["product_name"]] = tot.get(r["product_name"], 0) + (float(n) if n not in ("", None) else 0)
        names += [{"year": y, "product_name": k, "prescriptions": round(v)} for k, v in sorted(tot.items())]
        print(f"Medicaid SDUD {y}: {len(rows):,} GLP-1 rows (API count {counts:,}); {len(tot)} product names")
        prov.append(
            {
                "source": f"Medicaid State Drug Utilization Data {y}",
                "year": y,
                "dataset_id": dsid,
                "released_or_modified": modified.get(dsid, ""),
                "query": f"{base} product_name LIKE <prefix>% for {','.join(SDUD_PREFIXES)}",
                "rows": len(rows),
                "rows_expected": counts,
                "file": path.name,
                "bytes": size,
                "sha256": sha,
                "downloaded_utc": stamp(path),
            }
        )
        write_prov(out, prov)
    with open(out / "medicaid_sdud_product_names.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "product_name", "prescriptions"])
        w.writeheader()
        w.writerows(names)


def enrollment(out: Path, prov: list[dict]) -> None:
    modified = medicaid_modified()
    # this table has ~100 wide columns: pages of 5,000 rows never returned (2026-11-14), 500 take ~2 s
    rows, count, base = dkan_query(
        ENROLL_ID,
        [
            ("conditions[0][property]", "reporting_period"),
            ("conditions[0][value]", "202101"),
            ("conditions[0][operator]", ">="),
            ("conditions[1][property]", "reporting_period"),
            ("conditions[1][value]", "202512"),
            ("conditions[1][operator]", "<="),
        ],
        page=500,
    )
    path = out / "medicaid_enrollment_2021_2025.csv.gz"
    size, sha = write_csv_gz(path, rows)
    print(f"Medicaid enrollment 2021-2025: {len(rows):,} state-month rows (API count {count:,})")
    prov.append(
        {
            "source": "State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data",
            "year": "2021-2025",
            "dataset_id": ENROLL_ID,
            "released_or_modified": modified.get(ENROLL_ID, ""),
            "query": f"{base} reporting_period 202101-202512",
            "rows": len(rows),
            "rows_expected": count,
            "file": path.name,
            "bytes": size,
            "sha256": sha,
            "downloaded_utc": stamp(path),
        }
    )
    write_prov(out, prov)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="dados_brutos/cms")
    ap.add_argument(
        "--only-enrollment", action="store_true", help="keep the other provenance rows as they are"
    )
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    prov: list[dict] = []
    if a.only_enrollment:
        with open(out / "provenance_cms.csv", newline="") as f:
            prov = [r for r in csv.DictReader(f) if "Enrollment" not in r["source"]]
        for r in prov:
            r["rows"], r["rows_expected"] = int(r["rows"]), int(r["rows_expected"])
    else:
        medicare(out, prov)
        medicaid(out, prov)
    enrollment(out, prov)
    bad = [p for p in prov if p["rows_expected"] not in (None, p["rows"])]
    print(f"Done. provenance_cms.csv written. Row-count mismatches: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
