"""Re-run the 2026-11-12 pilot without touching piloto/ (outputs go to resultados/piloto/).

Usage:  uv run python scripts/run_pilot.py
"""

import shutil
import subprocess
import sys

from glp1_review.paths import PILOT, PILOT_DATA, RESULTS

OUT = RESULTS / "piloto"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for f in PILOT_DATA.glob("*.csv"):
        shutil.copy(f, OUT)
    runs = [
        ("pilot_glp1_obesity.py", [OUT, OUT], "pilot_output.txt"),
        ("pilot_extra.py", [OUT], "pilot_extra_output.txt"),
    ]
    for script, args, log in runs:
        print(f"> {script}")
        res = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", str(PILOT / script), *map(str, args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        (OUT / log).write_text(res.stdout, encoding="utf-8")
        if res.returncode != 0:
            print(res.stderr, file=sys.stderr)
            return res.returncode
    print(f"Done. Outputs in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
