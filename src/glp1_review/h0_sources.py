"""H0: source reconciliation (pre-registration Q19). Descriptive, no test.

Pre-registration part (published numbers only; no microdata):
  - dados_externos/published_estimates.csv: every Gallup and NHANES number used, with source, location in the
    source (text/table), derivation and whether it was verified against the source on 2026-11-14;
  - dados_externos/source_design.csv: design differences (frame, mode, measurement, sample, timing, weighting);
  - BRFSS national series as published by the CDC open-data API (piloto/dados/brfss_us_total.csv, Q036) and the
    pilot's composition-adjusted series (piloto/saidas/pilot_national_series.csv);
  - `plot_published_series`: the three sources on one axis (figure).

After registration (guarded loader): `brfss_by_gallup_groups` computes BRFSS obesity in Gallup's groups
(18-29, 30-39, 40-49, 50-64, 65+, men, women) from the microdata (5-year _AGEG5YR codes make the groups exact), and
`age_change_table` sets the BRFSS 2022->2025 changes against Gallup's. The MRP national series from H1 is added to
the comparison then.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from glp1_review.paths import PILOT_DATA, PILOT_OUTPUTS, ROOT
from glp1_review.survey import wls_design

EXT = ROOT / "dados_externos"

# _AGEG5YR codes: 1 18-24, 2 25-29, 3 30-34, 4 35-39, 5 40-44, 6 45-49, 7 50-54, 8 55-59, 9 60-64, 10-13 65+
GALLUP_AGE = {
    "age 18-29": [1, 2],
    "age 30-39": [3, 4],
    "age 40-49": [5, 6],
    "age 50-64": [7, 8, 9],
    "age 65+": [10, 11, 12, 13],
}

COLORS = {
    "BRFSS": "#2a78d6",
    "Gallup": "#eb6834",
    "NHANES": "#1baf7a",
}  # reference palette slots 1-3, validated
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def load_published() -> pd.DataFrame:
    return pd.read_csv(EXT / "published_estimates.csv")


def load_design() -> pd.DataFrame:
    return pd.read_csv(EXT / "source_design.csv").set_index("aspect")


def brfss_published_national() -> pd.DataFrame:
    """CDC open-data 'US' obesity rows (Q036) and the pilot's state-composition-adjusted series."""
    us = pd.read_csv(PILOT_DATA / "brfss_us_total.csv")
    us = us[us["q"] == "Q036"][["year", "value", "lo", "hi"]].rename(columns={"value": "brfss_cdc"})
    adj = pd.read_csv(PILOT_OUTPUTS / "pilot_national_series.csv").rename(columns={"Unnamed: 0": "year"})
    adj = adj[["year", "fe_adjusted"]].rename(columns={"fe_adjusted": "brfss_composition_adjusted"})
    return us.merge(adj, on="year", how="left")


def national_table() -> pd.DataFrame:
    """One row per year: BRFSS (CDC and composition-adjusted), Gallup; NHANES cycles listed by period."""
    b = brfss_published_national().set_index("year")
    p = load_published()
    g = p[(p.source == "Gallup") & (p.measure == "obesity") & (p.group == "total")]
    g = g.assign(year=g["period"].astype(int)).set_index("year")["value_pct"].rename("gallup")
    out = b[["brfss_cdc", "brfss_composition_adjusted"]].join(g, how="outer")
    return out.sort_index()


def nhanes_cycles() -> pd.DataFrame:
    p = load_published()
    n = p[(p.source == "NHANES") & (p.measure == "obesity (age-adjusted)") & (p.group == "total")].copy()
    span = n["period"].str.split("-", expand=True).astype(int)
    n["start"], n["end"] = span[0], span[1]
    return n[["period", "start", "end", "value_pct", "se"]]


def change_2022_2025() -> pd.DataFrame:
    """Total change 2022 -> 2025 in each source (pp)."""
    t = national_table()
    rows = [
        ("BRFSS, CDC published", t.loc[2025, "brfss_cdc"] - t.loc[2022, "brfss_cdc"]),
        (
            "BRFSS, composition-adjusted (pilot)",
            t.loc[2025, "brfss_composition_adjusted"] - t.loc[2022, "brfss_composition_adjusted"],
        ),
        ("Gallup, published", t.loc[2025, "gallup"] - t.loc[2022, "gallup"]),
    ]
    return pd.DataFrame(rows, columns=["source", "change_pp"]).round(2)


# ------------------------------------------------------------------------------- after registration
def brfss_by_gallup_groups(df: pd.DataFrame, years=(2022, 2025)) -> pd.DataFrame:
    """Weighted obesity (%) with design-based SE by Gallup group and year. df: harmonised BRFSS rows with raw
    `age5`, `sex` (Male/Female), `obese`, `wt`, `strat`, `psu`, `year` (load with data.load_brfss)."""
    d = df[df["year"].isin(years) & df["obese"].notna()]
    groups = {k: d["age5"].isin(v) for k, v in GALLUP_AGE.items()}
    groups.update(
        {"men": d["sex"] == "Male", "women": d["sex"] == "Female", "total": pd.Series(True, index=d.index)}
    )
    rows = []
    for y in years:
        for name, m in groups.items():
            g = d[m & (d["year"] == y)]
            fit = wls_design(
                pd.DataFrame({"const": np.ones(len(g))}, index=g.index),
                100 * g["obese"],
                g["wt"],
                g["strat"],
                g["psu"],
            )
            rows.append({"group": name, "year": y, "brfss_pct": fit.coef[0], "se": fit.se[0], "n": len(g)})
    return pd.DataFrame(rows)


def age_change_table(brfss_groups: pd.DataFrame) -> pd.DataFrame:
    """BRFSS 2022->2025 change by Gallup group next to Gallup's published change."""
    w = brfss_groups.pivot(index="group", columns="year", values="brfss_pct")
    se = brfss_groups.pivot(index="group", columns="year", values="se")
    out = pd.DataFrame(
        {"brfss_change": w[2025] - w[2022], "brfss_change_se": np.sqrt(se[2025] ** 2 + se[2022] ** 2)}
    )
    p = load_published()
    gc = p[
        (p.source == "Gallup") & (p.measure == "obesity change 2022-2025") & (p.verified == "yes")
    ].set_index("group")["value_pct"]
    lv = p[(p.source == "Gallup") & (p.measure == "obesity")].pivot_table(
        index="group", columns="period", values="value_pct"
    )
    if {"2022", "2025"} <= set(lv.columns):
        gc = gc.combine_first((lv["2025"] - lv["2022"]).round(1))
    out["gallup_change"] = gc
    return out


# ------------------------------------------------------------------------------- figure
def plot_published_series(path: Path) -> Path:
    """Static figure (paper): BRFSS lines, Gallup points, NHANES cycle segments with 95% CI. Light theme."""
    import matplotlib
    import matplotlib.ticker

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    t = national_table()
    nh = nhanes_cycles()
    fig, ax = plt.subplots(figsize=(8.0, 4.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    b = t["brfss_cdc"].dropna()
    ax.plot(
        b.index, b.values, color=COLORS["BRFSS"], lw=2, marker="o", ms=4, solid_capstyle="round", zorder=3
    )
    a = t["brfss_composition_adjusted"].dropna()
    ax.plot(a.index, a.values, color=COLORS["BRFSS"], lw=1.4, ls=(0, (4, 3)), zorder=2)
    g = t["gallup"].dropna()
    ax.plot(g.index, g.values, color=COLORS["Gallup"], lw=0, marker="s", ms=8, mec=SURFACE, mew=2, zorder=4)
    fieldwork = {
        "2017-2020": (2017.0, 2020.2),
        "2021-2023": (2021.6, 2023.7),
    }  # to Mar 2020; Aug 2021-Aug 2023
    for _, r in nh.iterrows():
        x0, x1 = fieldwork.get(r["period"], (r["start"], r["end"] + 0.9))
        ax.fill_between(
            [x0, x1],
            r["value_pct"] - 1.96 * r["se"],
            r["value_pct"] + 1.96 * r["se"],
            color=COLORS["NHANES"],
            alpha=0.15,
            lw=0,
            zorder=1,
        )
        ax.plot(
            [x0, x1], [r["value_pct"]] * 2, color=COLORS["NHANES"], lw=2, solid_capstyle="round", zorder=2
        )

    # direct labels (identity never by color alone)
    ax.annotate(
        "BRFSS (CDC, self-report, phone)",
        (b.index[-1], b.values[-1]),
        xytext=(6, -12),
        textcoords="offset points",
        color=INK,
        fontsize=8.5,
    )
    ax.annotate(
        "BRFSS, state composition fixed",
        (a.index[-1], a.values[-1]),
        xytext=(6, -24),
        textcoords="offset points",
        color=INK2,
        fontsize=8,
    )
    ax.annotate(
        "Gallup (self-report, web panel)",
        (g.index[-1], g.values[-1]),
        xytext=(8, 4),
        textcoords="offset points",
        color=INK,
        fontsize=8.5,
    )
    ax.annotate(
        f"{g.loc[2022]:.1f}",
        (2022, g.loc[2022]),
        xytext=(-24, -3),
        textcoords="offset points",
        color=INK2,
        fontsize=7.5,
    )
    last = nh.iloc[-1]
    ax.annotate(
        "NHANES (measured, age 20+, age-adjusted)",
        (last["start"], last["value_pct"] + 1.96 * last["se"]),
        xytext=(0, 4),
        textcoords="offset points",
        color=INK,
        fontsize=8.5,
    )

    ax.set_xlim(2010.5, 2029.5)
    ax.set_ylim(25, 48)
    ax.set_xticks(range(2011, 2027, 1))
    ax.set_xticklabels([str(y) if y % 2 == 1 else "" for y in range(2011, 2027)], fontsize=8, color=INK2)
    ax.tick_params(axis="y", labelsize=8, colors=INK2, length=0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    handles = [
        Line2D([], [], color=COLORS["BRFSS"], lw=2, marker="o", ms=4, label="BRFSS"),
        Line2D([], [], color=COLORS["BRFSS"], lw=1.4, ls=(0, (4, 3)), label="BRFSS, state composition fixed"),
        Line2D([], [], color=COLORS["Gallup"], lw=0, marker="s", ms=7, label="Gallup"),
        Line2D([], [], color=COLORS["NHANES"], lw=2, label="NHANES (band = 95% CI)"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=7.5, frameon=False, ncol=2, labelcolor=INK2)
    ax.tick_params(axis="x", length=0)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.set_ylabel("Adults with obesity (%)", fontsize=9, color=INK2)
    ax.set_title(
        "US adult obesity by source: published estimates", loc="left", fontsize=11, color=INK, pad=10
    )
    fig.text(
        0.01,
        0.01,
        "Sources: CDC BRFSS open data (hn4x-zwk7); Gallup (Oct 2025, Jul 2026); NCHS Data Brief 508. NHANES band = 95% CI.",
        fontsize=7,
        color=INK2,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    return path
