"""Download the BRFSS XPT zips from the Internet Archive's copies of www.cdc.gov.

Why: www.cdc.gov (Akamai) answers 403 to every non-browser request, so `brfss_microdata.py download`
cannot fetch the files (tested 2026-11-14, all 15 years refused on the first request). The Wayback
Machine keeps byte-for-byte captures of the same CDC URLs. The `id_` form of a snapshot URL returns
the original bytes, without archive rewriting.

This script only places the files where `brfss_microdata.py` expects them
(dados_brutos/brfss/LLCP<year>XPT.zip) and records their provenance. Afterwards run
`brfss_microdata.py download` (it skips files already present and writes manifest_sha256.csv) and
`validate`, which checks the microdata against the CDC open API numbers.

Usage:  uv run python scripts/brfss_wayback_download.py [--years 2011-2025] [--out dados_brutos/brfss]
Writes: <out>/LLCP<year>XPT.zip and <out>/provenance_wayback.csv
"""

import argparse
import csv
import hashlib
import json
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

CDC = "https://www.cdc.gov/brfss/annual_data/{y}/files/LLCP{y}XPT.{ext}"
AVAILABLE = "https://archive.org/wayback/available?url={url}"
UA = {"User-Agent": "glp1-review research script (BRFSS via Internet Archive)"}


def http_get(url: str, timeout: int = 120):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def snapshot(year: int) -> tuple[str, str] | None:
    """Closest 200 snapshot of the CDC zip for this year: (original url, timestamp)."""
    for ext in ("zip", "ZIP"):
        cdc = CDC.format(y=year, ext=ext)
        with http_get(AVAILABLE.format(url=urllib.parse.quote(cdc, safe=""))) as r:
            snap = json.load(r).get("archived_snapshots", {}).get("closest")
        if snap and snap.get("available") and snap.get("status") == "200":
            original = snap["url"].split("/", 5)[5]  # http://web.archive.org/web/<ts>/<original>
            return original, snap["timestamp"]
    return None


def download(url: str, dest: Path) -> None:
    part = dest.with_suffix(".part")
    with http_get(url, timeout=300) as r, open(part, "wb") as f:
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r    {done / 1e6:6.1f}/{total / 1e6:.1f} MB", end="", flush=True)
    print()
    part.replace(dest)


def zip_ok(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as z:
            return z.testzip() is None and any(n.strip().lower().endswith(".xpt") for n in z.namelist())
    except zipfile.BadZipFile:
        return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_years(s: str) -> list[int]:
    if "-" in s:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", default="2011-2025")
    ap.add_argument("--out", default="dados_brutos/brfss")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    prov_path = out / "provenance_wayback.csv"
    rows = {}
    if prov_path.exists():
        with open(prov_path, newline="") as f:
            rows = {int(r["year"]): r for r in csv.DictReader(f)}

    failed = []
    for y in parse_years(a.years):
        dest = out / f"LLCP{y}XPT.zip"
        if dest.exists() and zip_ok(dest) and y in rows:
            print(f"{y}: already there, skipping")
            continue
        snap = snapshot(y)
        if not snap:
            print(f"{y}: no snapshot in the Internet Archive")
            failed.append(y)
            continue
        original, ts = snap
        raw_url = f"https://web.archive.org/web/{ts}id_/{original}"
        print(f"{y}: snapshot {ts} of {original}")
        for attempt in range(3):
            try:
                download(raw_url, dest)
                break
            except OSError as e:
                print(f"    attempt {attempt + 1} failed: {e}")
                time.sleep(10 * (attempt + 1))
        if not (dest.exists() and zip_ok(dest)):
            print(f"{y}: download is not a valid BRFSS zip")
            failed.append(y)
            continue
        rows[y] = {
            "year": y,
            "file": dest.name,
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
            "cdc_url": original,
            "wayback_timestamp": ts,
            "wayback_url": raw_url,
            "downloaded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with open(prov_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[y].keys()))
            w.writeheader()
            w.writerows(rows[k] for k in sorted(rows))
        time.sleep(2)  # be gentle with the archive

    print(f"Done. Provenance in {prov_path}. Failed years: {failed or 'none'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
