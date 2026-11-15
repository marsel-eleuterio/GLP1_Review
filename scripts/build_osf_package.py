"""Assemble the files to upload to the OSF project before registration.

Copies documents, code, pilot, download manifests/provenance and the count-only check outputs into
resultados/osf/ and zips them as resultados/osf_glp1_<date>.zip, with MANIFEST_sha256.csv listing every file.
No microdata and no BMI analysis are included (pre-registration rule): only validation against published
aggregates, codebook checks, variable coverage and case counts.

Usage:  uv run python scripts/build_osf_package.py
"""

import csv
import hashlib
import shutil
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "resultados" / "osf"

# (source relative to ROOT, destination folder inside the package)
FILES = [
    ("docs/plano_de_estudo.pdf", "1_documents"),
    ("docs/plano_de_estudo.md", "1_documents"),
    ("docs/preregistro_osf_v2.md", "1_documents"),
    ("docs/decision_log.md", "1_documents"),
    ("docs/implementation_notes.md", "1_documents"),
    ("docs/citation_check.md", "1_documents"),
    ("docs/h0_sources.md", "1_documents"),
    ("docs/figures", "1_documents"),
    ("dados_externos", "4_data_provenance"),
    ("docs/revisao_da_literatura.pdf", "1_documents"),
    ("piloto", "2_pilot"),
    ("scripts/brfss_microdata.py", "3_code"),
    ("scripts/meps_microdata.py", "3_code"),
    ("scripts/brfss_hf_download.py", "3_code"),
    ("scripts/brfss_extract_parquet.py", "3_code"),
    ("scripts/brfss_wayback_download.py", "3_code"),
    ("scripts/cms_glp1_download.py", "3_code"),
    ("scripts/census_download.py", "3_code"),
    ("scripts/README.md", "3_code"),
    ("src/glp1_review", "3_code/analysis"),
    ("tests", "3_code/analysis"),
    ("pyproject.toml", "3_code"),
    ("uv.lock", "3_code"),
    ("dados_brutos/meps/manifest_sha256.csv", "4_data_provenance/meps"),
    ("dados_brutos/brfss_hf/provenance_hf.csv", "4_data_provenance/brfss"),
    ("dados_brutos/cms/provenance_cms.csv", "4_data_provenance/cms"),
    ("dados_brutos/cms/medicaid_sdud_product_names.csv", "4_data_provenance/cms"),
    ("dados_brutos/census/provenance_census.csv", "4_data_provenance/census"),
    ("dados_limpos/brfss/validation_state_year.csv", "5_checks/brfss"),
    ("dados_limpos/brfss/validation_national.csv", "5_checks/brfss"),
    ("dados_limpos/brfss/coverage_report.csv", "5_checks/brfss"),
    ("dados_limpos/meps/checks.csv", "5_checks/meps"),
    ("dados_limpos/meps/inventory.txt", "5_checks/meps"),
    ("LICENSE", "."),
    ("LICENSE-docs", "."),
    ("CITATION.cff", "."),
]

README = """# GLP-1 and the US adult obesity trend: materials for the OSF registration

Assembled {date}. Code repository: https://github.com/marsel-eleuterio/GLP1_Review (private until publication).

| Folder | Contents |
| --- | --- |
| 1_documents | Study plan (PDF and Markdown, Portuguese), pre-registration answers (English, v2), literature review |
| 2_pilot | Pilot of 12 Nov 2026 on aggregated data: code, inputs (dados/) and original outputs (saidas/) |
| 3_code | Download and extraction scripts, environment (pyproject.toml, uv.lock); scripts/README.md documents every step. 3_code/analysis: the pre-registered analysis code (glp1_review package) and its tests, written and tested on simulated data before registration |
| 4_data_provenance | SHA-256 manifests and provenance of every downloaded file (MEPS, BRFSS, CMS, Census/ACS) |
| 5_checks | Count-only outputs: BRFSS validation against CDC aggregates and variable coverage; MEPS codebook checks and case inventory |

No microdata and no outcome analysis are included. Before registration the microdata were used only to reproduce
published aggregates and to count cases (pre-registration Q18, item 6). MANIFEST_sha256.csv lists every file.

Licenses: code MIT (LICENSE); documents CC BY 4.0 (LICENSE-docs); third-party data keep their original terms.
"""


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    missing = []
    for src, dest in FILES:
        s = ROOT / src
        d = OUT / dest
        d.mkdir(parents=True, exist_ok=True)
        if not s.exists():
            missing.append(src)
        elif s.is_dir():
            shutil.copytree(s, d / s.name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(s, d / s.name)
    date = time.strftime("%Y-%m-%d")
    (OUT / "README.md").write_text(README.format(date=date), encoding="utf-8")

    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    with open(OUT / "MANIFEST_sha256.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "bytes", "sha256"])
        for p in files:
            w.writerow([p.relative_to(OUT).as_posix(), p.stat().st_size, sha256(p)])

    zpath = OUT.parent / f"osf_glp1_{date}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(OUT).as_posix())
    n = len(files) + 1
    print(f"{n} files in {OUT}; zip {zpath.name} ({zpath.stat().st_size / 1e6:.1f} MB)")
    if missing:
        print("MISSING (run the corresponding script first):", *missing, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
