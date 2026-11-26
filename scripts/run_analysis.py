"""Run the pre-registered analyses (after the OSF registration).

Usage:
  uv run python scripts/run_analysis.py                       # all steps, primary configuration
  uv run python scripts/run_analysis.py --steps h2 h3         # selected steps
  uv run python scripts/run_analysis.py --quick               # small draws/replicates (smoke test)
  uv run python scripts/run_analysis.py --steps h1 --no-q23-gate   # declared sensitivity (decision_log 11): MRP
                                                              # primary model in every year, no Q23 convergence gate

Writes to resultados/analysis/<UTC timestamp>/ (or --out): tables (.csv), results (.json), H1 draws (.npz),
verdicts.json and summary.md. Refuses to run before docs/osf_registration.txt exists (guard.py).
"""

import argparse
import time
from pathlib import Path

from glp1_review import run
from glp1_review.paths import RESULTS


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--steps", nargs="+", default=list(run.STEPS), choices=list(run.STEPS))
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--no-q23-gate", action="store_true", help="sensitivity only: skip the Q23 convergence rule"
    )
    a = ap.parse_args()
    out = a.out or RESULTS / "analysis" / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    cfg = run.Config.quick() if a.quick else run.Config()
    if a.no_q23_gate:
        cfg.mrp_q23 = False
    res = run.run(out, cfg, steps=a.steps)
    print((out / "summary.md").read_text(encoding="utf-8"))
    print(f"Outputs in {out}")
    return 0 if res else 1


if __name__ == "__main__":
    raise SystemExit(main())
