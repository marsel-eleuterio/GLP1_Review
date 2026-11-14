"""Download the BRFSS 2011-2025 annual files (LLCP<year>) as Parquet from the Hugging Face dataset
jamesjiadazhan/BRFSS, pinned to one revision.

Why: www.cdc.gov answers 403 to every automated request and web.archive.org was unreachable on
2026-11-14 (see scripts/README.md). This dataset is a column-for-column conversion of the CDC XPT files
("original public-use codes; nothing recoded, imputed or dropped"), built from the same Wayback
captures of the CDC URLs (SHA-1 verified), with the CDC source URL and the MD5 of each original zip in
metadata/FILES.parquet and the conversion code in pipeline/.

Writes into --out (default dados_brutos/brfss_hf):
  LLCP<year>.parquet         one file per year, as published
  FILES.parquet              the dataset's metadata table
  provenance_hf.csv          per year: revision, URL, bytes, sha256, rows (checked against metadata),
                             CDC source URL, MD5 of the CDC zip, Wayback capture

Usage:  uv run python scripts/brfss_hf_download.py [--years 2011-2025] [--revision <sha>]
Then:   uv run python scripts/brfss_extract_parquet.py, then brfss_microdata.py validate.
"""

import argparse
import csv
import hashlib
import time
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq

REPO = "jamesjiadazhan/BRFSS"
REVISION = "6e0af4750a9622dc297421924aab450774c00a2f"  # main on 2026-11-14 (last modified 2026-11-13)
URL = "https://huggingface.co/datasets/{repo}/resolve/{rev}/{path}"
UA = {"User-Agent": "glp1-review research script (BRFSS parquet download)"}


def fetch(url: str, dest: Path) -> None:
    part = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r, open(part, "wb") as f:
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r    {done / 1e6:6.1f}/{total / 1e6:.1f} MB", end="", flush=True)
    print()
    part.replace(dest)


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
    ap.add_argument("--revision", default=REVISION)
    ap.add_argument("--out", default="dados_brutos/brfss_hf")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    meta_path = out / "FILES.parquet"
    fetch(URL.format(repo=REPO, rev=a.revision, path="metadata/FILES.parquet"), meta_path)
    meta = pq.read_table(meta_path).to_pandas()
    meta = meta[meta["component"] == "Annual"].set_index("file")

    rows, failed = [], []
    for y in parse_years(a.years):
        name = f"LLCP{y}"
        if name not in meta.index:
            print(f"{y}: {name} not in metadata")
            failed.append(y)
            continue
        m = meta.loc[name]
        dest = out / f"{name}.parquet"
        url = URL.format(repo=REPO, rev=a.revision, path=m["path"])
        if not dest.exists():
            print(f"{y}: {url}")
            for attempt in range(3):
                try:
                    fetch(url, dest)
                    break
                except OSError as e:
                    print(f"    attempt {attempt + 1} failed: {e}")
                    time.sleep(10 * (attempt + 1))
        else:
            print(f"{y}: already there, checking")
        if not dest.exists():
            failed.append(y)
            continue
        n = pq.ParquetFile(dest).metadata.num_rows
        ok = n == int(m["rows"])
        print(f"    rows {n:,} (metadata {int(m['rows']):,}) {'ok' if ok else 'MISMATCH'}")
        if not ok:
            failed.append(y)
        rows.append(
            {
                "year": y,
                "file": dest.name,
                "bytes": dest.stat().st_size,
                "sha256": sha256(dest),
                "rows": n,
                "rows_match_metadata": ok,
                "hf_repo": REPO,
                "hf_revision": a.revision,
                "hf_url": url,
                "cdc_source_url": m["source_url"],
                "cdc_zip_md5": m["source_md5"],
                "obtained_from": m["downloaded_from"],
                "downloaded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

    with open(out / "provenance_hf.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Done. {len(rows)} files, provenance_hf.csv written. Failed: {failed or 'none'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
