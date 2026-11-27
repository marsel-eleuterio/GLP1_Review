"""Figures of the preprint (paper/figures/) from the outputs of the full run.

Usage:
  uv run python scripts/make_figures.py --recompute   # derive the figure-only quantities, then draw
  uv run python scripts/make_figures.py               # draw from the saved outputs
  uv run python scripts/make_figures.py --recompute-only

--recompute loads the BRFSS microdata and saves, in <run>/figdata/, the quantities that the run computed but did not
keep (glp1_review.figure_data): NC1 height departure by year, H4 event-study SEs and state departures, and all H5
draws. Each is checked against the registered result it must reproduce. No estimate or classification changes.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from glp1_review.paths import RESULTS, ROOT

RUN = RESULTS / "analysis" / "full_20261125"
SENS = RESULTS / "analysis" / "sens_mrp_nogate_20261126"
OUT = ROOT / "paper" / "figures"


def recompute(run: Path) -> None:
    from glp1_review import figure_data, prepare
    from glp1_review.run import Config

    cfg = Config()
    fd = run / "figdata"
    fd.mkdir(exist_ok=True)
    t0 = time.time()
    b = prepare.brfss()
    print(f"BRFSS loaded: {len(b):,} rows ({time.time() - t0:.0f} s)", flush=True)

    E = pd.read_csv(run / "h4_exposure.csv", index_col=0)["E"]
    betas, dep = figure_data.h4_event_and_states(b, E)
    saved = pd.read_csv(run / "h4_event_betas.csv", index_col=0)["beta"]
    assert np.allclose(betas["beta"].to_numpy(), saved.to_numpy(), atol=1e-9), "H4 betas differ from the run"
    betas.to_csv(fd / "h4_event_betas_se.csv")
    dep.to_csv(fd / "h4_state_departures.csv")
    print(f"H4: event-study SEs and {len(dep)} state departures ({time.time() - t0:.0f} s)", flush=True)

    sim = figure_data.h5_draws(b, prepare.DEFAULT, cfg.published_rate_2025, cfg.h5_draws, cfg.seed)
    h5 = json.loads((run / "h5.json").read_text(encoding="utf-8"))["simulated_effect_pp"]
    for k, q in (("p5", 5), ("median", 50), ("p95", 95)):
        assert abs(np.percentile(sim, q) - h5[k]) < 1e-9, f"H5 {k} differs from the run"
    np.save(fd / "h5_draws.npy", sim)
    print(f"H5: {len(sim):,} draws, percentiles match the run ({time.time() - t0:.0f} s)", flush=True)

    nc = figure_data.nc1_yearly(b, n_rep=cfg.nc1_reps, seed=cfg.seed + 1)
    reg = json.loads((run / "nc1.json").read_text(encoding="utf-8"))["estimate"]
    mean_post = nc.loc[[2023, 2024, 2025], "departure"].mean()
    assert abs(mean_post - reg) < 1e-9, f"NC1 2023-2025 mean {mean_post} differs from the run {reg}"
    nc.to_csv(fd / "nc1_yearly.csv")
    print(
        f"NC1: yearly departures, 2023-2025 mean {mean_post:.4f} = run ({time.time() - t0:.0f} s)", flush=True
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, default=RUN)
    ap.add_argument("--sens", type=Path, default=SENS)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--recompute", action="store_true")
    ap.add_argument("--recompute-only", action="store_true")
    a = ap.parse_args()
    if a.recompute or a.recompute_only:
        recompute(a.run)
    if a.recompute_only:
        return 0
    from glp1_review import figures

    for p in figures.draw_all(a.run, a.sens, a.out):
        print(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
