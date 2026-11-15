"""Extract the BRFSS study columns from the Parquet files (brfss_hf_download.py) into the same harmonised
files that `brfss_microdata.py extract` writes from the XPT zips.

The harmonisation is not reimplemented: CANDIDATES and harmonise() are imported from
brfss_microdata.py (unchanged, as cited in the pre-registration). Only the reader differs (Parquet
instead of XPT). After this, run the original validation:

  uv run python scripts/brfss_extract_parquet.py [--raw dados_brutos/brfss_hf] [--out dados_limpos/brfss]
  uv run python scripts/brfss_microdata.py validate --clean dados_limpos/brfss --api piloto/dados

Two columns are added here for the Q24 sensitivity analyses (not in brfss_microdata.py, which stays as cited):
  genhlth  GENHLTH, self-rated general health 1-5 (7, 9 -> missing); a covariate of the BMI imputation (Q14)
  phone    "landline" (QSTVER 10-13) or "cell" (QSTVER 20-23); interview mode (Q24)
"""

import argparse
import importlib.util
import time
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

_spec = importlib.util.spec_from_file_location(
    "brfss_microdata", Path(__file__).with_name("brfss_microdata.py")
)
bm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bm)


EXTRA = ("GENHLTH", "QSTVER")


def add_extra(res: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    g = (
        pd.to_numeric(df["GENHLTH"], errors="coerce")
        if "GENHLTH" in df
        else pd.Series(float("nan"), index=df.index)
    )
    q = (
        pd.to_numeric(df["QSTVER"], errors="coerce")
        if "QSTVER" in df
        else pd.Series(float("nan"), index=df.index)
    )
    res["genhlth"] = g.where(g.between(1, 5)).to_numpy()
    res["phone"] = pd.Series(
        pd.cut(q, [9, 19, 29], labels=["landline", "cell"]).astype(object), index=df.index
    ).to_numpy()
    return res


def read_parquet(path: Path, wanted: set[str]) -> tuple[pd.DataFrame, int]:
    pf = pq.ParquetFile(path)
    by_upper = {c.upper(): c for c in pf.schema_arrow.names}
    cols = [by_upper[c] for c in wanted if c in by_upper]
    df = pf.read(columns=cols).to_pandas()
    df.columns = [c.upper() for c in df.columns]
    return df, pf.metadata.num_rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="dados_brutos/brfss_hf")
    ap.add_argument("--out", default="dados_limpos/brfss")
    ap.add_argument("--years", default="2011-2025")
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    wanted = {c for cands in bm.CANDIDATES.values() for c in cands} | set(EXTRA)

    rows = []
    for y in bm.parse_years(a.years):
        p = raw / f"LLCP{y}.parquet"
        if not p.exists():
            print(f"{y}: {p} not found, skipping")
            continue
        t = time.time()
        df, total = read_parquet(p, wanted)
        res, used = bm.harmonise(df, y)
        res = add_extra(res, df)
        res.to_csv(out / f"brfss_{y}.csv.gz", index=False)
        rows.append({"year": y, "records": total, **used})
        miss = [k for k, v in used.items() if not v]
        print(f"{y}: {total:,} records, {time.time() - t:.0f}s; columns not found: {miss or 'none'}")
    pd.DataFrame(rows).to_csv(out / "coverage_report.csv", index=False)
    print("coverage_report.csv written (blank = column absent that year; check the codebook).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
