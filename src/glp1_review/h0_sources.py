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
    `age5`, `sex` (Male/Female), `obese`, `wt`, `strat`, `psu`, `year` (as returned by prepare.brfss)."""
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
    """Static two-panel figure (paper, light theme).

    A: long-run series - BRFSS (CDC published, annual) and NHANES (measured; point at the middle of each cycle,
       95% CI whisker, cycle written below).
    B: change from 2022 to 2025 - one row per source (Gallup; BRFSS with a constant state mix; BRFSS as published),
       hollow dot = 2022, filled dot = 2025, arrow between them, change written at the right; the measured NHANES
       level of Aug 2021-Aug 2023 as a reference line.
    """
    import matplotlib
    import matplotlib.ticker

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    t = national_table()
    nh = nhanes_cycles()
    blue, orange, aqua = COLORS["BRFSS"], COLORS["Gallup"], COLORS["NHANES"]

    fig = plt.figure(figsize=(11.0, 5.4), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    gs = fig.add_gridspec(
        1, 2, width_ratios=[1.25, 1], left=0.07, right=0.93, top=0.76, bottom=0.17, wspace=0.42
    )
    axA, axB = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

    def style(ax):
        ax.set_facecolor(SURFACE)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(length=0, labelsize=8.5, colors=INK2)

    # ------------------------------------------------------------------ A: long-run series
    style(axA)
    axA.axvspan(2021.5, 2025.5, color="#f0efec", lw=0, zorder=0)
    axA.text(2023.5, 45.6, "2022-2025 and\nGallup: panel B", ha="center", va="top", fontsize=7.5, color=INK2)
    b = t["brfss_cdc"].dropna()
    axA.plot(b.index, b.values, color=blue, lw=2, zorder=3)
    axA.plot(b.index, b.values, ls="none", marker="o", ms=5, color=blue, mec=SURFACE, mew=1.5, zorder=4)
    axA.text(2013.2, 26.3, "BRFSS\ntelephone, self-reported, 18+", fontsize=8.5, color=INK, va="bottom")
    centres = {"2013-2014": 2013.5, "2015-2016": 2015.5, "2017-2020": 2018.1, "2021-2023": 2022.1}
    short = {
        "2013-2014": "2013-14",
        "2015-2016": "2015-16",
        "2017-2020": "2017-\nMar 20",
        "2021-2023": "Aug 21-\nAug 23",
    }
    for _, r in nh.iterrows():
        x, y, h = centres[r["period"]], r["value_pct"], 1.96 * r["se"]
        axA.plot([x, x], [y - h, y + h], color=aqua, lw=2, solid_capstyle="round", zorder=3)
        axA.plot(x, y, marker="D", ms=7, color=aqua, mec=SURFACE, mew=1.5, zorder=4)
        axA.text(x, y - h - 0.35, short[r["period"]], ha="center", va="top", fontsize=7, color=INK2)
    axA.text(
        2011.0, 44.6, "NHANES\nmeasured, 20+, age-adjusted\n(bars: 95% CI)", fontsize=8.5, color=INK, va="top"
    )
    axA.set_xlim(2010.5, 2025.8)
    axA.set_ylim(25, 46)
    axA.set_xticks(range(2011, 2026, 2))
    axA.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5))
    axA.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    axA.yaxis.grid(True, color=GRID, lw=0.8)
    axA.set_axisbelow(True)
    axA.set_ylabel("Adults with obesity (%)", fontsize=8.5, color=INK2)
    axA.set_title("A. Long-run series", loc="left", fontsize=10, color=INK, pad=8)

    # ------------------------------------------------------------------ B: change 2022 -> 2025
    style(axB)
    adj = t["brfss_composition_adjusted"]
    rows = [
        ("Gallup\nweb panel, self-reported", orange, t.loc[2022, "gallup"], t.loc[2025, "gallup"]),
        ("BRFSS\nadjusted for missing states", blue, adj.loc[2022], adj.loc[2025]),
        (
            "BRFSS as published\n(2025 omits CA, MS, NV)",
            blue,
            t.loc[2022, "brfss_cdc"],
            t.loc[2025, "brfss_cdc"],
        ),
    ]
    ys = [2, 1, 0]
    nh_last = nh.iloc[-1]["value_pct"]
    axB.axvline(nh_last, color=aqua, lw=1.2, ls=(0, (2, 2)), zorder=1)
    axB.text(
        nh_last - 0.15,
        3.1,
        f"NHANES Aug 2021-Aug 2023\n(measured): {nh_last:.1f}",
        ha="right",
        va="top",
        fontsize=7.5,
        color=INK2,
    )
    for (_label, col, v0, v1), y in zip(rows, ys, strict=True):
        if abs(v1 - v0) >= 0.6:  # the arrow is only visible when the dots do not overlap
            axB.annotate(
                "",
                xy=(v1, y),
                xytext=(v0, y),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": col,
                    "lw": 2,
                    "shrinkA": 5,
                    "shrinkB": 5,
                    "mutation_scale": 12,
                },
                zorder=3,
            )
        axB.plot(v0, y, marker="o", ms=9, mfc=SURFACE, mec=col, mew=2, zorder=4)
        axB.plot(v1, y, marker="o", ms=9, color=col, mec=SURFACE, mew=1.5, zorder=4)
        if abs(v1 - v0) > 1.0:  # far apart: labels above the dots
            for v in (v0, v1):
                axB.annotate(
                    f"{v:.1f}",
                    (v, y),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                    color=INK2,
                )
        else:  # close together: smaller value labelled on the left, larger on the right
            lo, hi = sorted((v0, v1))
            axB.annotate(
                f"{lo:.1f}",
                (lo, y),
                xytext=(-9, 0),
                textcoords="offset points",
                ha="right",
                va="center",
                fontsize=8,
                color=INK2,
            )
            axB.annotate(
                f"{hi:.1f}",
                (hi, y),
                xytext=(9, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=8,
                color=INK2,
            )
        d = round(v1, 1) - round(v0, 1)
        axB.annotate(
            f"{d:+.1f}".replace("-", "−"),
            xy=(1.0, y),
            xycoords=("axes fraction", "data"),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            color=INK,
            fontweight="bold",
        )
    axB.annotate(
        "change\n(pts)",
        xy=(1.0, 2.55),
        xycoords=("axes fraction", "data"),
        xytext=(8, 0),
        textcoords="offset points",
        va="bottom",
        fontsize=7.5,
        color=INK2,
    )
    axB.set_yticks(ys)
    axB.set_yticklabels([r[0] for r in rows], fontsize=8.5, color=INK)
    axB.set_ylim(-0.6, 3.2)
    axB.set_xlim(31.5, 42)
    axB.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2))
    axB.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    axB.xaxis.grid(True, color=GRID, lw=0.8)
    axB.set_axisbelow(True)
    axB.set_xlabel("Adults with obesity (%)", fontsize=8.5, color=INK2)
    axB.set_title("B. 2022 to 2025: level and change", loc="left", fontsize=10, color=INK, pad=8)
    handles = [
        Line2D([], [], ls="none", marker="o", ms=8, mfc=SURFACE, mec=INK2, mew=2, label="2022"),
        Line2D([], [], ls="none", marker="o", ms=8, color=INK2, label="2025"),
    ]
    axB.legend(
        handles=handles,
        loc="upper left",
        ncol=2,
        frameon=False,
        fontsize=8,
        labelcolor=INK2,
        handletextpad=0.3,
        columnspacing=1.0,
        borderaxespad=0,
    )

    # ------------------------------------------------------------------ titles and source
    fig.text(
        0.06,
        0.955,
        "Self-reported obesity fell 2.9 points in Gallup from 2022 to 2025 but stayed flat in BRFSS",
        fontsize=12.5,
        color=INK,
        va="top",
    )
    fig.text(
        0.06,
        0.905,
        "Adults with obesity (BMI ≥ 30), %, published estimates. Levels differ by method: NHANES measures height and weight;\nBRFSS and Gallup use self-reports, which run lower. The comparison of interest is the change after 2022 (panel B).",
        fontsize=8.5,
        color=INK2,
        va="top",
    )
    fig.text(
        0.06,
        0.02,
        "Sources: CDC BRFSS open data (hn4x-zwk7); Gallup (Oct 2025; 2026 estimate after a weighting revision: 36.8); NCHS Data Brief 508.\n"
        "BRFSS adjusted for missing states: state and year fixed effects on the published state estimates, weighted by 2024 adult population (pilot).",
        fontsize=7,
        color=INK2,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    return path
