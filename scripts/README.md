# scripts/

| Script | Purpose |
| --- | --- |
| `brfss_microdata.py` | From the original work package: download, extract and validate BRFSS 2011-2025 microdata |
| `meps_microdata.py` | From the original work package: download and extract the 16 MEPS files, link the panels, check against the codebooks |
| `brfss_hf_download.py` | **Route used for BRFSS:** downloads the annual files as Parquet (Hugging Face, pinned revision) |
| `brfss_extract_parquet.py` | Extracts the study columns from the Parquet files using the logic of `brfss_microdata.py` |
| `brfss_wayback_download.py` | Alternative route: downloads the XPT zips from Internet Archive captures of cdc.gov |
| `cms_glp1_download.py` | Medicare Part D by state (2019-2024), Medicaid SDUD GLP-1 rows (2021-2025) and Medicaid enrollment (H4) |
| `census_download.py` | Adult population by state (Census, Vintage 2025) and ACS PUMS 2011-2024 post-stratification cells (H1) |
| `nhanes_download.py` | NHANES measured BMI, 2011-2023 cycles, for the Q24 self-report correction; reproduces the published age-adjusted prevalence |
| `run_analysis.py` | **After registration:** runs all pre-registered analyses and writes tables, draws, verdicts and a summary (`--quick` for a smoke test) |
| `make_figures.py` | **After the full run:** draws the preprint figures into `paper/figures/` from `resultados/analysis/full_20261125/`; `--recompute` first derives, from the microdata, the figure-only quantities the run did not keep (NC1 by year, H4 event-study SEs and state departures, all H5 draws) and checks them against the registered results |
| `build_osf_package.py` | Assembles `resultados/osf/` and the zip to upload to OSF, with a sha256 manifest |
| `run_pilot.py` | Re-runs the 12 November 2026 pilot into `resultados/piloto/` |

`brfss_microdata.py` and `meps_microdata.py` come from the original work package (`projeto_glp1.zip`) and are the
scripts cited in the pre-registration. Do not reformat them. Any later fix goes in a separate commit with its
reason, because they are part of the OSF package. The one change made so far is documented below.

Both `selftest` commands pass in this environment (`.venv`, Python 3.12, with `pyreadstat`). In the MEPS selftest
the "not found" and MISMATCH lines are expected, because it runs on synthetic files.

## Run order (from the repository root), as run on 14 November 2026

    # 1. test the logic, no network
    uv run python scripts/brfss_microdata.py selftest
    uv run python scripts/meps_microdata.py selftest

    # 2. MEPS: download and extract (original script)
    uv run python scripts/meps_microdata.py download --out dados_brutos/meps --yes
    uv run python scripts/meps_microdata.py extract  --raw dados_brutos/meps --out dados_limpos/meps

    # 3. BRFSS: download as Parquet, extract, validate with the original script
    uv run python scripts/brfss_hf_download.py                     # dados_brutos/brfss_hf/ + provenance_hf.csv
    uv run python scripts/brfss_extract_parquet.py                 # dados_limpos/brfss/ + coverage_report.csv
    uv run python scripts/brfss_microdata.py validate --clean dados_limpos/brfss --api piloto/dados

    # 4. CMS and Census (H4 and H1), then the OSF package
    uv run python scripts/cms_glp1_download.py     # dados_brutos/cms/ + provenance_cms.csv
    uv run python scripts/census_download.py       # dados_brutos/census/, dados_limpos/{census,acs}/ + provenance_census.csv
    uv run python scripts/nhanes_download.py       # dados_brutos/nhanes/, dados_limpos/nhanes/ + provenance_nhanes.csv (15 Nov 2026)
    uv run python scripts/build_osf_package.py     # resultados/osf/ and resultados/osf_glp1_<date>.zip

## Why BRFSS was not downloaded from cdc.gov

Attempts on 14 November 2026, in order:

1. **`brfss_microdata.py download`:** HTTP 403 for all 15 years, from the first request. www.cdc.gov (Akamai)
   refuses every automated client, HTML pages included. The file URLs are correct (checked on
   `annual_2024.html`). We did not try to circumvent the block (e.g. by changing the User-Agent).
2. **`ftp.cdc.gov`:** does not host BRFSS.
3. **Internet Archive (`brfss_wayback_download.py`):** captures of all 15 zips exist, but `web.archive.org` was
   unreachable (connections timed out).
4. **Hugging Face, `jamesjiadazhan/BRFSS` (used):** a column-for-column conversion of the CDC XPT files ("original
   public-use codes; nothing recoded, imputed or dropped"), built from **the same Wayback captures** (the capture
   timestamps match those of attempt 3), verified by its author by SHA-1. `metadata/FILES.parquet` records the CDC
   URL and the MD5 of each original zip, and `pipeline/` holds the conversion code.

Traceability: `dados_brutos/brfss_hf/provenance_hf.csv` records, per year, the repository revision (`6e0af47…`),
URL, size and sha256 of the Parquet file, the row count checked against the metadata, the CDC URL, the MD5 of the
CDC zip and the capture used. It is part of the OSF package.

That the data are the CDC's is established by `validate`, run with the original script. Result on 14 November 2026:
792 state-years compared with the CDC open-data API, mean absolute difference 0.025 pp, maximum 0.12 pp, none above
0.2 pp. The national series matches the CDC's within 0.05 pp in every year.

Caveat (pre-registration Q8): the captures date from 26 July 2026 (2011-2024) and 18 September 2026 (2025). A later
re-release of a file by the CDC would not be reflected.

## Variable coverage (coverage_report.csv, 14 November 2026)

| Variable | Finding | Consequence |
| --- | --- | --- |
| diabetes | `DIABETE3` in 2011-2018, `DIABETE4` from 2019 | Answer for Q12, Q19 and Q23: the item changes in 2019 |
| sex | Empty in 2011-2018: the source names were `SEX` (2011-2017) and `SEX1` (2018) | **Fixed** (below) |
| health plan | Empty in 2024-2025: renamed `_HLTHPL2` | **Fixed** (below) |
| race | Empty in 2015-2016: `_IMPRACE` does not exist in those years | **Left empty** (below) |

### Change to `brfss_microdata.py` (14 November 2026, before registration)

The `CANDIDATES` list of the original script did not cover these names. Differences from
`initial_docs/scripts/brfss_microdata.py`:

- **`sex`:** added `SEX1` and `SEX`. Their codes, checked in the CDC dictionary, match `_SEX` (1 male, 2 female).
  `SEX` and `SEX1` also have 7 and 9 (don't know, refused), to be treated as missing.
- **`plan_raw`:** added `_HLTHPL2`. Same codes and shares as `_HLTHPL1`/`_HLTHPLN` (1 insured, 2 not insured, 9
  don't know or missing). Through 2020 the source is the raw item `HLTHPLN1` (1, 2, 7, 9), as in the original.
- **`race`:** unchanged. In 2015-2016 only `_RACE` exists, with 9 non-imputed categories, whereas `_IMPRACE` has 6
  imputed categories; mixing them would break the series. Race is not a hypothesis variable; models that adjust
  for it use a "not available" category in 2015-2016 (Q12).

After the change: selftest passes, extraction has no missing columns (except race 2015-2016), validation unchanged
(792 state-years, maximum 0.12 pp).

## CMS and Census details

- **Medicare Part D** (data.cms.gov, one dataset per year; 2024 = `c8ea3f8e…`, the one cited in Q7): every row with
  `Prscrbr_Geo_Lvl = State` is kept and the count is checked against the `stats` endpoint. The GLP-1 selection
  (by `Gnrc_Name`) is done in the analysis and can be audited.
- **Medicaid SDUD** (data.medicaid.gov, versions of 13 July 2026): the API filters on the server by prefix of
  `product_name`, which is truncated to 10 characters (GLP-1 brands and generics, including tirzepatide and the
  insulin combinations). `medicaid_sdud_product_names.csv` lists every name kept, for review (14 November: 60
  names, all GLP-1). Monthly enrollment 2021-2025 comes from the Medicaid and CHIP enrollment dataset, in pages of
  500 rows (`--only-enrollment` redoes that step alone).
- Run of 14 November 2026: Medicare 2019-2024 with 111,000-114,000 state rows a year; Medicaid SDUD with 6,574
  (2021) to 12,867 (2025) GLP-1 rows; enrollment with 6,120 state-month rows. Every count matches the API. A first
  version of the script re-requested the first page forever when a query exceeded 5,000 rows (missing offset
  increment); this affected only the enrollment step and was fixed before the final run.
- **Census:** `sc-est2025-alldata6.csv` (resident population, Vintage 2025) is kept whole;
  `adult_pop_state_2020_2025.csv` holds the 18+ totals.
- **ACS 1-year PUMS:** 2011-2019, the experimental 2020 file and 2021-2024 (2025 not yet released; Q19 uses 2024
  instead). Each zip (~600 MB) is downloaded, hashed, reduced to the H1 cells (state × age 6 × sex × race 5 ×
  education 4, adults outside institutional group quarters) and deleted. Mapping to BRFSS: race = Hispanic first,
  then White, Black, Asian, other (as `_IMPRACE`); education `SCHL` ≤ 15 / 16-17 / 18-20 / ≥ 21 (as `_EDUCAG`).
  Institutional exclusion: `RELP == 16` through 2018, `RELSHIPP == 37` from 2019. In 2024 the column `ST` was
  renamed `STATE`.

## Extra BRFSS columns for Q24 (14 November 2026)

`brfss_extract_parquet.py` also writes `genhlth` (`GENHLTH`, 1-5; 7 and 9 missing), a covariate of the BMI
imputation (Q14), and `phone` (`QSTVER` 10-13 landline, 20-23 cell), for the interview-mode sensitivity (Q24). They
are added in that script, not in `brfss_microdata.py`, which stays as cited in the pre-registration. After the
re-extraction the validation is unchanged (792 state-years, maximum 0.12 pp).
