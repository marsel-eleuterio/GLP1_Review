"""Figures of the preprint (paper/figures/), drawn from the outputs of the full run.

One visual language for all figures (title, one-line takeaway, lettered panels separated by rules, notes at the
foot). Colors follow the entity: BRFSS blue, NHANES green, Gallup orange (validated with the data-viz palette
checks for the pairs that share a panel: BRFSS-NHANES and BRFSS-Gallup); projections, simulations and reference
zones are neutral. Every number printed in a figure is read from the run outputs, none is typed in.

Entry point: `draw_all(run_dir, sens_dir, out_dir)`; scripts/make_figures.py.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter, MultipleLocator
from scipy import stats

from glp1_review import decision as dec
from glp1_review import h0_sources

INK, INK2, RULE, GRID, SURF = "#17324a", "#4b6272", "#d3dde2", "#e4eaed", "#ffffff"
BLUE, GREEN, ORANGE = "#2a6cb0", "#2e8540", "#b8511f"  # BRFSS, NHANES, Gallup
GRAY, BAND, ZONE = "#7d8b95", "#edf1f3", "#e6eff8"
W, DPI, LM, RM = 10.0, 220, 0.65, 0.55  # width and margins in inches
matplotlib.rcParams["text.color"] = INK  # text ink by default
MINUS = "−"
TOP4 = ("WV", "KY", "LA", "OK")


def num(x: float, d: int = 1, sign: bool = False) -> str:
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    if s.lstrip("+-").strip("0.") == "":  # avoid "-0.0"
        s = s.lstrip("+-")
    return s.replace("-", MINUS)


def _style(ax, grid: str = "y") -> None:
    ax.set_facecolor(SURF)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, labelsize=10.5, colors=INK2, pad=5)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.9)
        ax.set_axisbelow(True)


def _signed(v, _pos=None) -> str:
    return num(v, 0, sign=v > 0) if float(v).is_integer() else num(v, 1, sign=v > 0)


class Sheet:
    """A figure laid out in inches from the top-left corner."""

    def __init__(self, height: float):
        self.h = height
        self.fig = plt.figure(figsize=(W, height), dpi=DPI)
        self.fig.patch.set_facecolor(SURF)

    def y(self, top: float) -> float:
        return 1 - top / self.h

    def text(self, x: float, top: float, s: str, **kw):
        kw.setdefault("color", INK)
        kw.setdefault("va", "baseline")
        return self.fig.text(x / W, self.y(top), s, **kw)

    def header(self, title: str, subtitle: str) -> None:
        self.text(LM, 0.62, title, size=21, weight="bold")
        self.text(LM, 0.98, subtitle, size=11, color=INK2)
        self.rule(1.25)

    def rule(self, top: float) -> None:
        self.fig.add_artist(Line2D([LM / W, 1 - RM / W], [self.y(top)] * 2, color=RULE, lw=1.3))

    def panel(self, top: float, letter: str, title: str, x: float = LM) -> None:
        self.text(x, top, letter, size=14, weight="bold", color=INK2)
        self.text(x + 0.36, top, title, size=14.5, weight="bold")

    def key(self, x: float, top: float, glyph: str, color: str, label: str, size: float = 10.5) -> float:
        """Legend entry: a colored glyph and a label in text ink. Returns the x after the entry."""
        self.text(x, top, glyph, color=color, size=size + 1)
        self.text(x + 0.22, top, label, color=INK2, size=size)
        return x + 0.22 + 0.0105 * size * len(label) + 0.35

    def axes(self, left: float, top: float, right: float, bottom: float, grid: str = "y"):
        ax = self.fig.add_axes([left / W, self.y(bottom), (right - left) / W, (bottom - top) / self.h])
        _style(ax, grid)
        ax.geom = (left, right)
        return ax

    def notes(self, top: float, lines: list[str], step: float = 0.235) -> None:
        for i, s in enumerate(lines):
            self.text(LM, top + i * step, s, size=9.3, color=INK2)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, facecolor=SURF)
        plt.close(self.fig)
        return path


def _xin(ax, x_in: float) -> float:
    """Axes-fraction x of a position given in inches from the left edge of the figure."""
    left, right = ax.geom
    return (x_in - left) / (right - left)


# ------------------------------------------------------------------------------------------ Figure 1, sources
def fig_sources(
    national: pd.DataFrame, adjusted: pd.Series, nhanes: pd.DataFrame, ages: pd.DataFrame, path: Path
) -> Path:
    """national: index year, columns brfss_cdc and gallup (%); adjusted: primary H1 series (%) by year;
    nhanes: period, value_pct, se; ages: index group ('age 30-39', ...), brfss_change, brfss_change_se,
    gallup_change."""
    s = Sheet(10.9)
    s.header(
        "US adult obesity across three surveys",
        "Gallup reported a decline from 2022 to 2025. BRFSS estimates changed little over the same period.",
    )
    # A: long-run series
    s.panel(1.72, "A", "Historical prevalence of obesity")
    s.key(LM, 2.07, "●", BLUE, "BRFSS · self-reported, ages 18+")
    s.key(5.0, 2.07, "◆", GREEN, "NHANES · measured, age-adjusted, ages 20+")
    ax = s.axes(LM + 0.62, 2.3, W - RM - 0.05, 3.95)
    b = national["brfss_cdc"].dropna()
    ax.plot(b.index, b.values, color=BLUE, lw=2.4, zorder=3)
    ax.plot(b.index, b.values, "o", ms=5.5, color=BLUE, mec=SURF, mew=1.2, zorder=4)
    ax.text(
        b.index[-1] + 0.2, b.iloc[-1], f"{b.iloc[-1]:.1f}%", color=BLUE, weight="bold", size=11, va="center"
    )
    centre = {"2013-2014": 2013.5, "2015-2016": 2015.5, "2017-2020": 2018.1, "2021-2023": 2022.1}
    period = {
        "2013-2014": "2013–14",
        "2015-2016": "2015–16",
        "2017-2020": "2017–Mar 2020",
        "2021-2023": "Aug 2021–Aug 2023",
    }
    for _, r in nhanes.iterrows():
        x, v, h = centre[r["period"]], r["value_pct"], 1.96 * r["se"]
        ax.errorbar(
            x,
            v,
            yerr=h,
            fmt="D",
            ms=7.5,
            color=GREEN,
            mec=SURF,
            mew=1.2,
            elinewidth=1.6,
            capsize=4,
            capthick=1.6,
            zorder=4,
        )
        ax.text(x + 0.22, v, f"{v:.1f}%", color=GREEN, weight="bold", size=10.5, va="center")
        ax.text(x, v + h + 0.55, period[r["period"]], color=INK2, size=9.3, ha="center", va="bottom")
    ax.set_xlim(2010.6, 2026.4)
    ax.set_ylim(25, 46.5)
    ax.set_xticks(range(2011, 2026, 2))
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    s.rule(4.45)

    # B: national change 2022 to 2025
    s.panel(4.92, "B", "National change from 2022 to 2025")
    ax_left = 4.5
    s.text(LM, 5.28, "Survey estimate", weight="bold", size=11)
    s.text(LM + 2.3, 5.28, "2022 → 2025", weight="bold", size=11)
    s.text(ax_left, 5.28, "Change in percentage points", weight="bold", size=11)
    rows = [
        ("Gallup", national.loc[2022, "gallup"], national.loc[2025, "gallup"], ORANGE),
        ("BRFSS, published", national.loc[2022, "brfss_cdc"], national.loc[2025, "brfss_cdc"], BLUE),
        ("BRFSS, adjusted*", adjusted.loc[2022], adjusted.loc[2025], BLUE),
    ]
    ax = s.axes(ax_left, 5.42, W - RM - 0.05, 6.4, grid="x")
    for i, (name, a, z, col) in enumerate(rows):
        y, ch = len(rows) - 1 - i, round(z, 1) - round(a, 1)
        ax.barh(y, ch, height=0.42, color=col, zorder=3)
        ax.text(
            ch + (-0.12 if ch < 0 else 0.12),
            y,
            num(ch, 1, sign=ch > 0),
            color=col,
            weight="bold",
            size=12,
            ha="right" if ch < 0 else "left",
            va="center",
        )
        ax.text(
            _xin(ax, LM),
            y,
            name,
            transform=ax.get_yaxis_transform(),
            weight="bold",
            size=11.5,
            va="center",
            clip_on=False,
        )
        ax.text(
            _xin(ax, LM + 2.3),
            y,
            f"{a:.1f}% → {z:.1f}%",
            transform=ax.get_yaxis_transform(),
            size=11.5,
            va="center",
            clip_on=False,
        )
    _change_axis(ax, len(rows))
    s.rule(6.92)

    # C: change by age group
    s.panel(7.4, "C", "Change by age group from 2022 to 2025")
    s.key(LM + 0.0, 7.76, "●", ORANGE, "Gallup")
    s.key(LM + 1.25, 7.76, "■", BLUE, "BRFSS (95% CI)")
    s.text(ax_left, 7.76, "Change in percentage points", weight="bold", size=11)
    groups = [g for g in ("age 30-39", "age 40-49", "age 50-64") if g in ages.index]
    ax = s.axes(ax_left, 7.9, W - RM - 0.05, 8.95, grid="x")
    for i, g in enumerate(groups):
        y, r = len(groups) - 1 - i, ages.loc[g]
        gc, bc, h = r["gallup_change"], r["brfss_change"], 1.96 * r["brfss_change_se"]
        ax.plot(gc, y, "o", ms=10, color=ORANGE, zorder=4)
        ax.text(gc - 0.17, y, num(gc, 1), color=ORANGE, weight="bold", size=12, ha="right", va="center")
        ax.errorbar(
            bc, y, xerr=h, fmt="s", ms=8.5, color=BLUE, elinewidth=1.6, capsize=4, capthick=1.6, zorder=4
        )
        ax.text(
            bc + 0.1,
            y + 0.2,
            num(bc, 1, sign=bc > 0),
            color=BLUE,
            weight="bold",
            size=12,
            ha="left",
            va="bottom",
        )
        label = g.replace("age ", "").replace("-", "–") + " years"
        ax.text(
            _xin(ax, LM),
            y,
            label,
            transform=ax.get_yaxis_transform(),
            weight="bold",
            size=12.5,
            va="center",
            clip_on=False,
        )
    _change_axis(ax, len(groups))
    s.rule(9.45)
    s.notes(
        9.78,
        [
            "Obesity is BMI ≥ 30. BRFSS and Gallup use self-reported height and weight; NHANES measures them.",
            "* The published 2025 BRFSS estimate omits California, Mississippi and Nevada. The adjusted series (the primary H1 series) uses",
            "   state and year effects on the state estimates, weighted by the 2024 adult population, so that every state counts in every year.",
            "Whiskers: 95% intervals (estimate ± 1.96 SE), NHANES in A and BRFSS in C. Gallup did not publish age-specific standard errors.",
        ],
    )
    return s.save(path)


def _change_axis(ax, n: int) -> None:
    ax.axvline(0, color=INK2, lw=1.4, zorder=2)
    ax.set_xlim(-6.3, 2.3)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xticks([-6, -4, -2, 0, 2])
    ax.xaxis.set_major_formatter(FuncFormatter(_signed))
    ax.set_yticks([])


# ------------------------------------------------------------------------------------------ Figure 2, H1
def trajectory(series: pd.Series, pre=tuple(range(2011, 2020)), prob: float = 0.95) -> pd.DataFrame:
    """Linear trend in the logit of prevalence fitted to `pre`, with the Student-t predictive interval (H1 Stage
    2 for a series without posterior draws). Columns in %: observed, fitted, lo, hi; departure in pp with its
    interval (dlo, dhi)."""
    years = np.array(series.index, float)
    lg = np.log(series.to_numpy() / (1 - series.to_numpy()))
    ip = np.isin(series.index, pre)
    X = np.column_stack([np.ones(ip.sum()), years[ip] - 2015])
    XtX_inv = np.linalg.inv(X.T @ X)
    coef = XtX_inv @ X.T @ lg[ip]
    dof = ip.sum() - 2
    s = np.sqrt(np.sum((lg[ip] - X @ coef) ** 2) / dof)
    X0 = np.column_stack([np.ones(len(years)), years - 2015])
    loc = X0 @ coef
    scl = s * np.sqrt(1 + np.einsum("ij,jk,ik->i", X0, XtX_inv, X0))
    q = stats.t.ppf(0.5 + prob / 2, dof)

    def expit(v):
        return 100 / (1 + np.exp(-v))

    obs = 100 * series.to_numpy()
    out = pd.DataFrame(
        {"observed": obs, "fitted": expit(loc), "lo": expit(loc - q * scl), "hi": expit(loc + q * scl)},
        index=series.index,
    )
    out["departure"] = obs - out["fitted"]
    out["dlo"], out["dhi"] = obs - out["hi"], obs - out["lo"]
    return out


def fig_h1(
    series: pd.Series,
    registered: pd.DataFrame,
    nc2: dict,
    nc1_years: pd.DataFrame,
    nc1: dict,
    path: Path,
) -> Path:
    """series: primary H1 national prevalence (proportion) by year; registered: h1_departures.csv rows of the
    primary counterfactual (year, median_pp, lo95, hi95), used for 2023-2025 so that the figure shows the
    registered numbers; nc2: year -> (median, lo, hi); nc1_years: year -> departure, se (cm); nc1: estimate, se."""
    tr = trajectory(series)
    reg = registered.set_index("year")
    for y in reg.index:  # registered 2023-2025 departures (4,000 draws) instead of the closed form
        tr.loc[y, ["departure", "dlo", "dhi"]] = reg.loc[y, ["median_pp", "lo95", "hi95"]].to_numpy(float)
    d25 = tr.loc[2025, "departure"]
    s = Sheet(9.4)
    s.header(
        "Adult obesity departed from its 2011–2019 trajectory",
        f"In 2025 obesity was {num(-d25)} percentage points below the projected trajectory; "
        "self-reported height did not depart.",
    )
    s.panel(1.72, "A", "Obesity and its projected trajectory")
    x = s.key(LM, 2.07, "●", BLUE, "BRFSS, composition-adjusted (primary H1 series)")
    s.key(x - 0.2, 2.07, "━", GRAY, "2011–2019 trend, projected (95% interval)")
    ax = s.axes(LM + 0.62, 2.3, W - RM - 0.05, 4.55)
    post = tr.index >= 2019
    ax.axvspan(2022.5, 2025.6, color=BAND, lw=0, zorder=0)
    ax.text(2024.05, 26.9, "2023–2025", color=INK2, size=9.5, ha="center")
    ax.fill_between(tr.index[post], tr["lo"][post], tr["hi"][post], color=RULE, alpha=0.75, lw=0, zorder=1)
    ax.plot(tr.index[tr.index <= 2019], tr["fitted"][tr.index <= 2019], color=GRAY, lw=1.8, zorder=2)
    ax.plot(tr.index[post], tr["fitted"][post], color=GRAY, lw=1.8, ls=(0, (4, 3)), zorder=2)
    ax.plot(tr.index, tr["observed"], color=BLUE, lw=2.4, zorder=3)
    ax.plot(tr.index, tr["observed"], "o", ms=5.5, color=BLUE, mec=SURF, mew=1.2, zorder=4)
    o25, f25 = tr.loc[2025, "observed"], tr.loc[2025, "fitted"]
    ax.annotate(
        "",
        xy=(2025.35, o25),
        xytext=(2025.35, f25),
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.3, mutation_scale=11),
    )
    ax.text(2025.5, (o25 + f25) / 2, f"{num(d25, 2)} pp", color=INK, weight="bold", size=11, va="center")
    ax.set_xlim(2010.6, 2026.6)
    ax.set_ylim(26.5, 37.5)
    ax.set_xticks(range(2011, 2026, 2))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    s.rule(5.05)

    mid = W / 2
    # B: departures and placebo
    s.panel(5.5, "B", "Departure from the trajectory")
    x = s.key(LM, 5.84, "●", BLUE, "departure, 95% interval", size=9.5)
    s.key(x - 0.1, 5.84, "○", BLUE, "2011–2019 residual", size=9.5)
    s.key(LM, 6.07, "□", INK, "placebo: trend 2011–2015, projected to 2017–2019", size=9.5)
    ax = s.axes(LM + 0.55, 6.25, mid - 0.25, 7.95)
    ax.axvspan(2022.5, 2025.6, color=BAND, lw=0, zorder=0)
    ax.axhline(0, color=INK2, lw=1.1, zorder=1)
    pre = tr.index <= 2019
    ax.plot(tr.index[pre], tr["departure"][pre], "o", ms=5.5, mfc=SURF, mec=BLUE, mew=1.4, zorder=3)
    p = tr[tr.index >= 2020]
    ax.errorbar(
        p.index,
        p["departure"],
        yerr=[p["departure"] - p["dlo"], p["dhi"] - p["departure"]],
        fmt="o",
        ms=6,
        color=BLUE,
        mec=SURF,
        mew=1,
        elinewidth=1.8,
        capsize=0,
        zorder=3,
    )
    for y, (m, lo, hi) in sorted(nc2.items()):
        ax.errorbar(
            int(y) + 0.3,
            m,
            yerr=[[m - lo], [hi - m]],
            fmt="s",
            ms=5.5,
            mfc=SURF,
            mec=INK,
            color=INK,
            elinewidth=1.2,
            capsize=0,
            zorder=3,
        )
    lo_all = min(tr["dlo"].min(), min(v[1] for v in nc2.values()) if nc2 else 0)
    hi_all = max(tr["dhi"].max(), max(v[2] for v in nc2.values()) if nc2 else 0)
    ax.set_ylim(lo_all - 0.25, hi_all + 0.25)
    ax.set_xlim(2010.4, 2025.8)
    ax.set_xticks(range(2011, 2026, 2))
    ax.tick_params(axis="x", labelsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(_signed))
    ax.set_ylabel("percentage points", color=INK2, size=10)

    # C: height
    s.panel(5.5, "C", "Negative control: height (NC1)", x=mid + 0.25)
    x = s.key(mid + 0.25, 5.84, "◆", BLUE, "departure, 95% interval", size=9.5)
    s.key(x - 0.1, 5.84, "◇", BLUE, "2011–2019 residual", size=9.5)
    s.key(mid + 0.25, 6.07, "▬", "#c9d3d9", "equivalence margin ±0.5 cm (2023–2025 mean)", size=9.5)
    ax = s.axes(mid + 0.25 + 0.55, 6.25, W - RM - 0.05, 7.95)
    ax.axhspan(-0.5, 0.5, color=BAND, lw=0, zorder=0)
    ax.axhline(0, color=INK2, lw=1.1, zorder=1)
    h = nc1_years
    pre = h.index <= 2019
    ax.plot(h.index[pre], h["departure"][pre], "D", ms=5, mfc=SURF, mec=BLUE, mew=1.4, zorder=3)
    ax.errorbar(
        h.index[~pre],
        h["departure"][~pre],
        yerr=1.96 * h["se"][~pre],
        fmt="D",
        ms=5.5,
        color=BLUE,
        mec=SURF,
        mew=1,
        elinewidth=1.8,
        capsize=0,
        zorder=3,
    )
    e, se = nc1["estimate"], nc1["se"]
    ax.text(
        2010.7,
        -0.88,
        f"2023–2025 mean {num(e, 2)} cm (90% CI {num(e - 1.645 * se, 2)} to {num(e + 1.645 * se, 3)})",
        color=INK2,
        size=9.3,
    )
    ax.set_ylim(-1.0, 1.0)
    ax.set_xlim(2010.4, 2025.8)
    ax.set_xticks(range(2011, 2026, 2))
    ax.tick_params(axis="x", labelsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(_signed))
    ax.set_ylabel("cm", color=INK2, size=10)
    s.rule(8.4)
    s.notes(
        8.7,
        [
            "Trajectory: linear trend in the logit of prevalence, 2011–2019, projected with its Student-t predictive interval. "
            "The multilevel model failed",
            "the registered convergence rule, so the composition-adjusted direct series is the primary series (Methods). "
            "Height: adults 25–64, mean of",
            "men and women, composition-adjusted as in H3; whiskers ± 1.96 SE from 500 Rao–Wu bootstrap replicates.",
        ],
    )
    return s.save(path)


# ------------------------------------------------------------------------------------------ Figure 3, signatures
def fig_signatures(rows: list[dict], path: Path) -> Path:
    """rows: key, title, sub, est, se, dof (or None), ci90, p_holm, label; SESOI from decision.SESOI."""
    s = Sheet(5.55)
    s.header(
        "The three signatures: predicted sign, not decisive",
        "None was supported after the Holm adjustment, and none was contradicted.",
    )
    x = s.key(LM, 1.68, "▬", INK, "90% CI (decision rule)")
    x = s.key(x, 1.68, "─", INK2, "95% CI")
    s.key(x, 1.68, "■", "#c3d6ea", "above −SESOI: a 90% CI entirely here = contradicted")
    left, right = 3.55, 7.45
    ax = s.axes(left, 1.95, right, 4.35, grid="x")
    xmin, xmax = -2.6, 1.0
    for i, r in enumerate(rows):
        y = len(rows) - 1 - i
        sesoi = dec.SESOI[r["key"]]
        ax.add_patch(Rectangle((-sesoi, y - 0.36), xmax + sesoi, 0.72, color=ZONE, lw=0, zorder=0))
        ax.plot([-sesoi] * 2, [y - 0.36, y + 0.36], color=BLUE, lw=1.3, ls=(0, (2, 2)), zorder=1)
        ax.text(-sesoi, y + 0.4, f"{MINUS}{sesoi}", color=BLUE, size=9, ha="center", va="bottom")
        q95 = stats.t.ppf(0.975, r["dof"]) if r.get("dof") else 1.96
        ax.plot(
            [r["est"] - q95 * r["se"], r["est"] + q95 * r["se"]],
            [y, y],
            color=INK2,
            lw=1.4,
            solid_capstyle="round",
            zorder=2,
        )
        ax.plot(r["ci90"], [y, y], color=INK, lw=4.2, solid_capstyle="round", zorder=3)
        ax.plot(r["est"], y, "o", ms=9.5, color=INK, mec=SURF, mew=1.6, zorder=4)
        tr = ax.get_yaxis_transform()
        ax.text(_xin(ax, LM), y + 0.08, r["title"], transform=tr, weight="bold", size=12, clip_on=False)
        ax.text(_xin(ax, LM), y - 0.08, r["sub"], transform=tr, color=INK2, size=9.8, va="top", clip_on=False)
        ax.text(
            _xin(ax, right + 0.25), y + 0.08, r["label"], transform=tr, weight="bold", size=12, clip_on=False
        )
        ax.text(
            _xin(ax, right + 0.25),
            y - 0.08,
            f"p (Holm) {r['p_holm']:.2f}",
            transform=tr,
            color=INK2,
            size=9.8,
            va="top",
            clip_on=False,
        )
    ax.axvline(0, color=INK2, lw=1.3, zorder=1)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.6, len(rows) - 0.35)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(FuncFormatter(_signed))
    ax.set_xlabel(
        "Estimate, kg/m² (negative = larger decrease where GLP-1 use is expected)", color=INK2, size=10
    )
    s.rule(4.95)
    s.notes(
        5.25,
        [
            "One-sided tests in the predicted direction with Holm's adjustment (supported if p < 0.05). "
            "SESOI: smallest effect size of interest.",
        ],
    )
    return s.save(path)


# ------------------------------------------------------------------------------------------ Figure 4, H4
def fig_h4(betas: pd.DataFrame, states: pd.DataFrame, h4: dict, path: Path) -> Path:
    """betas: index year, beta, se (posterior-mean exposure); states: index state, E, departure; h4: h4.json."""
    est, rr = h4["beta_star_rubin"], h4["rr_intervals"]["0.02"]
    s = Sheet(6.8)
    s.header(
        "Higher state GLP-1 use, larger departure (H4)",
        f"β* = {num(est, 2)} pp per SD of use, permutation p < 0.001; with the registered pre-trend bound, "
        f"{num(rr[0], 2)} to {num(rr[1], 2)}.",
    )
    mid = 5.55
    s.panel(1.72, "A", "Event study, by year")
    x = s.key(LM, 2.07, "●", BLUE, "coefficient, 95% CI", size=9.8)
    s.key(x, 2.07, "━", GRAY, "trend 2011–2019, projected", size=9.8)
    ax = s.axes(LM + 0.62, 2.3, mid - 0.3, 5.0)
    ax.axvspan(2022.5, 2025.6, color=BAND, lw=0, zorder=0)
    ax.axhline(0, color=INK2, lw=1.1, zorder=1)
    yrs = betas.index.to_numpy(float)
    pre = yrs <= 2019
    c = np.polyfit(yrs[pre] - 2015, betas["beta"].to_numpy()[pre], 1)
    ax.plot(yrs[yrs <= 2019], np.polyval(c, yrs[yrs <= 2019] - 2015), color=GRAY, lw=1.6, zorder=2)
    ax.plot(
        yrs[yrs >= 2019], np.polyval(c, yrs[yrs >= 2019] - 2015), color=GRAY, lw=1.6, ls=(0, (4, 3)), zorder=2
    )
    ax.errorbar(
        yrs,
        betas["beta"],
        yerr=1.96 * betas["se"],
        fmt="o",
        ms=6,
        color=BLUE,
        mec=SURF,
        mew=1,
        elinewidth=1.8,
        capsize=0,
        zorder=3,
    )
    ax.set_xlim(2010.4, 2025.8)
    ax.set_xticks(range(2011, 2026, 2))
    ax.tick_params(axis="x", labelsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(_signed))
    ax.set_ylabel("pp per SD of use", color=INK2, size=10)

    s.panel(1.72, "B", "States: use and departure", x=mid + 0.1)
    s.key(mid + 0.1, 2.07, "●", BLUE, "state; line: least squares (descriptive)", size=9.8)
    ax = s.axes(mid + 0.72, 2.3, W - RM - 0.05, 5.0, grid="both")
    ax.axhline(0, color=INK2, lw=1.1, zorder=1)
    ax.scatter(states["E"], states["departure"], s=34, color=BLUE, edgecolor=SURF, lw=1, zorder=3)
    xx = np.linspace(states["E"].min(), states["E"].max(), 10)
    ax.plot(xx, np.polyval(np.polyfit(states["E"], states["departure"], 1), xx), color=INK, lw=1.6, zorder=2)
    for st in TOP4:
        if st in states.index:
            ax.text(
                states.loc[st, "E"] + 0.07, states.loc[st, "departure"], st, color=INK2, size=9, va="center"
            )
    ax.set_xlabel("GLP-1 use (SD)", color=INK2, size=10)
    ax.set_ylabel("2023–2025 departure (pp)", color=INK2, size=10)
    ax.xaxis.set_major_formatter(FuncFormatter(_signed))
    ax.yaxis.set_major_formatter(FuncFormatter(_signed))
    s.rule(5.6)
    s.notes(
        5.9,
        [
            f"A: coefficients with the posterior-mean exposure (β* = {num(h4['beta_star_posterior_mean_E'], 2)}); "
            f"the registered estimate combines 200 exposure draws ({num(est, 2)}).",
            "Normalized to a 2015–2019 mean of zero; 95% CIs cluster-robust by state.",
            "B: each state's mean 2023–2025 departure from its own 2011–2019 line. Use: one-factor model of Medicare "
            "Part D claims,",
            "Medicaid and all-payer GLP-1 prescriptions per person.",
        ],
    )
    return s.save(path)


# ------------------------------------------------------------------------------------------ Figure 5, H5
def fig_h5(draws: np.ndarray, d2025: tuple, meps_rate: float, published_rate: float, path: Path) -> Path:
    med, lo, hi = np.median(draws), np.percentile(draws, 5), np.percentile(draws, 95)
    dm, dlo, dhi = d2025
    s = Sheet(5.45)
    s.header(
        "A departure the size GLP-1 use could produce (H5)",
        f"Simulated effect {num(med, 2)} pp (90% range {num(lo, 2)} to {num(hi, 2)}); "
        f"observed 2025 departure {num(dm, 2)} pp.",
    )
    x = s.key(LM, 1.68, "■", "#b7c2c9", "simulated effect (10,000 draws); band: 90% range")
    s.key(x, 1.68, "●", BLUE, "observed departure, 95% interval")
    ax = s.axes(LM + 0.2, 1.9, W - RM - 0.05, 4.25, grid="x")
    hist, edges = np.histogram(draws, bins=45, density=True)
    mids = (edges[:-1] + edges[1:]) / 2
    ax.axvspan(lo, hi, ymin=0.22, color=BAND, lw=0, zorder=0)
    ax.fill_between(mids, 0, hist, color="#b7c2c9", lw=0, zorder=1)
    ax.plot(mids, hist, color=GRAY, lw=1.3, zorder=2)
    yb = -0.22 * hist.max()
    ax.plot([dlo, dhi], [yb, yb], color=BLUE, lw=3.2, solid_capstyle="round", zorder=3)
    ax.plot(dm, yb, "o", ms=9.5, color=BLUE, mec=SURF, mew=1.6, zorder=4)
    ax.axvline(0, color=INK2, lw=1.2, zorder=1)
    ax.set_ylim(yb * 1.6, hist.max() * 1.08)
    ax.set_xlim(min(dlo, draws.min()) - 0.3, 0.3)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(FuncFormatter(_signed))
    ax.set_xlabel("Change in adult obesity in 2025, percentage points", color=INK2, size=10)
    s.rule(4.68)
    s.notes(
        4.97,
        [
            f"Use by BMI class and diabetes from MEPS 2024, scaled to a national rate between {100 * meps_rate:.1f}% "
            f"(MEPS 2024) and {100 * published_rate:.0f}% (2025);",
            "one-year persistence and per-user weight loss drawn from published ranges.",
        ],
    )
    return s.save(path)


# ------------------------------------------------------------------------------------------ Figure 6, Q24
def fig_q24(panels: list[dict], path: Path) -> Path:
    """panels: title, rows [(label, est, lo, hi, kind)], kind in {'primary', 'variant', 'post'}; optional
    'sesoi' (dashed line at -SESOI) or 'margin' (shaded +-margin), 'column' 0 or 1."""
    row_h, head = 0.205, 0.62
    cols = [[p for p in panels if p.get("column", 0) == c] for c in (0, 1)]
    heights = [sum(head + row_h * (len(p["rows"]) + 0.6) for p in c) for c in cols]
    top0 = 1.95
    H = top0 + max(heights) + 1.05
    s = Sheet(H)
    s.header(
        "Pre-registered sensitivity analyses (Q24)",
        "Primary estimate and every variant with the same estimand; intervals where the variant has one.",
    )
    x = s.key(LM, 1.68, "◆", BLUE, "primary estimate", size=9.8)
    x = s.key(x, 1.68, "●", INK, "variant (dot only: point estimate)", size=9.8)
    s.key(x, 1.68, "○", INK, "added after registration", size=9.8)
    for c, col in enumerate(cols):
        x0 = LM if c == 0 else 5.25
        lab_w, ax_w = 2.15, 2.1
        top = top0
        for p in col:
            n = len(p["rows"])
            s.text(x0, top + 0.3, p["title"], weight="bold", size=11.2)
            ax = s.axes(x0 + lab_w, top + 0.45, x0 + lab_w + ax_w, top + 0.45 + row_h * (n + 0.6), grid="x")
            if "margin" in p:
                ax.axvspan(-p["margin"], p["margin"], color=BAND, lw=0, zorder=0)
            if "sesoi" in p:
                ax.axvline(-p["sesoi"], color=BLUE, lw=1.1, ls=(0, (2, 2)), zorder=1)
            ax.axvline(0, color=INK2, lw=1.1, zorder=1)
            prim = next(r for r in p["rows"] if r[4] == "primary")
            ax.axvline(prim[1], color=BLUE, lw=0.9, alpha=0.45, zorder=1)
            for i, (label, est, lo, hi, kind) in enumerate(p["rows"]):
                y = n - 1 - i
                col_ = BLUE if kind == "primary" else INK
                if np.isfinite(lo) and np.isfinite(hi) and hi > lo:
                    ax.plot(
                        [lo, hi],
                        [y, y],
                        color=col_,
                        lw=2.2 if kind == "primary" else 1.3,
                        solid_capstyle="round",
                        zorder=2,
                    )
                mk = {"primary": "D", "variant": "o", "post": "o"}[kind]
                ax.plot(
                    est,
                    y,
                    mk,
                    ms=6.5 if kind == "primary" else 5,
                    color=col_,
                    mfc=SURF if kind == "post" else col_,
                    mec=col_ if kind == "post" else SURF,
                    mew=1.2,
                    zorder=3,
                )
                ax.text(
                    _xin(ax, x0),
                    y,
                    label,
                    transform=ax.get_yaxis_transform(),
                    size=8.6,
                    va="center",
                    color=INK if kind != "primary" else BLUE,
                    weight="bold" if kind == "primary" else "normal",
                    clip_on=False,
                )
            ax.set_ylim(-0.7, n - 0.3)
            ax.set_yticks([])
            ax.tick_params(axis="x", labelsize=8.6)
            ax.xaxis.set_major_formatter(FuncFormatter(_signed))
            top += head + row_h * (n + 0.6)
    s.rule(H - 0.85)
    s.notes(
        H - 0.55,
        [
            "Intervals 95%, except H5 (90% simulation range) and the Rambachan–Roth rows (bounds). Dashed line: "
            "minus the smallest effect of interest;",
            "shaded: NC1 equivalence margin. External comparisons and dose–response contrasts have other estimands "
            "and are in Table 4 only.",
        ],
    )
    return s.save(path)


# ------------------------------------------------------------------------------------------ data and entry point
def _json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


Q24_LABELS = {
    "primary (direct weighted series, for comparison)": "direct weighted series",
    "balanced panel of states (direct series)": "  balanced panel (direct)",
    "interview mode: cell only (direct series)": "  cell phone only (direct)",
    "interview mode: landline only (direct series)": "  landline only (direct)",
    "multiple imputation of BMI (20), direct series": "  BMI imputed (direct)",
    "self-report correction (NHANES-calibrated, by sex and period, as in Ward et al. 2019), direct series": "  self-report corr., by period",
    "self-report correction (NHANES-calibrated, calibration fixed at 2011-2020), direct series": "  self-report corr., fixed",
    "without age and sex interactions": "no age/sex interactions",
    "ages 45-74 only": "ages 45–74 only",
    "diabetes group reweighted to its 2017-2019 age x sex composition": "diabetes group reweighted",
    "single regression, wild cluster bootstrap by state (Webb)": "wild cluster bootstrap",
    "item-change term off": "item-change term off",
    "pandemic years removed": "pandemic years removed",
    "balanced panel of states": "balanced panel of states",
    "interview mode: cell only": "cell phone only",
    "interview mode: landline only": "landline only",
    "multiple imputation of BMI (20)": "BMI imputed (20 sets)",
    "75th percentile in place of the 90th": "75th percentile",
    "95th percentile in place of the 90th": "95th percentile",
    "reweighting to the 2011 composition": "2011 composition",
    "reweighting to the 2022 composition": "2022 composition",
    "RIF regression with covariates instead of reweighting": "RIF regression",
    "all adults 18+": "all adults 18+",
    "by sex: Female": "women",
    "by sex: Male": "men",
    "indicator alone: medicare_claims_per100_adults_2024": "Medicare indicator alone",
    "indicator alone: medicaid_rx_per1000_enrollees_2025": "Medicaid indicator alone",
    "indicator alone: allpayer_rx_per100_2024": "all-payer indicator alone",
    "population weights": "population weights",
    "precision weights (1 / sampling variance, Kish n)": "precision weights",
    "leave-one-state-out (range)": "leave one state out (range)",
    "without WV, KY, LA and OK": "without WV, KY, LA, OK",
    "without states missing a post-period year": "without states missing a year",
    "Rambachan-Roth relative magnitude, Mbar = 0.5": "Rambachan–Roth, M̄ = 0.5",
    "Rambachan-Roth relative magnitude, Mbar = 1.0": "Rambachan–Roth, M̄ = 1.0",
    "loss of non-persistent users U(0%, 4%)": "loss of stoppers U(0, 4%)",
    "persistence fixed at 35.2% and 53.5%": "persistence fixed",
    "national use fixed at the MEPS 2024 rate": "use fixed at MEPS 2024 rate",
    "prevalent users as a third group": "prevalent users as a group",
    "LONGWT instead of LSAQWT": "LONGWT weights",
    "persons not present in all rounds included": "all-round attrition kept",
    "changes larger than 10 kg/m2 excluded": "changes > 10 kg/m² excluded",
    "by diabetes status: with diabetes": "with diabetes",
    "by diabetes status: without diabetes": "without diabetes",
    "Panel 23 only": "Panel 23 only",
    "Panel 24 only": "Panel 24 only",
}
H1_ALTERNATIVES = {
    "linear 2011-2021": "trend 2011–2021",
    "linear 2015-2019": "trend 2015–2019",
    "quadratic 2011-2019": "quadratic trend",
    "2022 level, 2011-2019 slope": "2022 level, 2011–2019 slope",
}


def q24_panels(run: Path, sens: Path | None) -> list[dict]:
    q = pd.read_csv(run / "q24.csv")
    nan = float("nan")

    def variants(h):
        out = []
        for _, r in q[q["hypothesis"] == h].iterrows():
            if r["variant"] not in Q24_LABELS or pd.isna(r["estimate"]):
                continue
            lo, hi = r["lo"], r["hi"]
            if pd.isna(lo) and pd.notna(r["se"]) and "point estimate" not in str(r["note"]) and h != "H1":
                lo, hi = r["estimate"] - 1.96 * r["se"], r["estimate"] + 1.96 * r["se"]
            out.append(
                (
                    Q24_LABELS[r["variant"]],
                    r["estimate"],
                    lo if pd.notna(lo) else nan,
                    hi if pd.notna(hi) else nan,
                    "variant",
                )
            )
        return out

    def normal(label, e, se, q975=1.96):
        return (label, e, e - q975 * se, e + q975 * se, "primary")

    h1 = _json(run / "h1.json")
    dep = pd.read_csv(run / "h1_departures.csv")
    d25 = dep[dep["year"] == 2025].set_index("counterfactual")
    m, lo, hi = h1["D2025_pp"]
    rows1 = [("primary (adjusted series)", m, lo, hi, "primary")]
    rows1 += [
        (lab, *d25.loc[k, ["median_pp", "lo95", "hi95"]].to_numpy(float), "variant")
        for k, lab in H1_ALTERNATIVES.items()
        if k in d25.index
    ]
    if sens is not None and (sens / "h1.json").exists():
        sm, slo, shi = _json(sens / "h1.json")["D2025_pp"]
        rows1.append(("MRP, no convergence gate", sm, slo, shi, "post"))
    rows1 += variants("H1")

    h2 = pd.read_csv(run / "h2.csv", index_col=0).loc["primary, two-stage"]
    h3, h6, nc1, h4, h5 = (_json(run / f"{k}.json") for k in ("h3", "h6", "nc1", "h4", "h5"))
    rows4 = [normal("primary β*", h4["beta_star_rubin"], h4["se_rubin"])]
    rr = h4["rr_intervals"]["0.02"]
    rows4.append(("registered bound, M = 0.02", h4["beta_star_rubin"], rr[0], rr[1], "variant"))
    sim = h5["simulated_effect_pp"]
    return [
        {"title": "H1 · departure in 2025, pp", "rows": rows1, "column": 0},
        {
            "title": "H2 · diabetes contrast, kg/m²",
            "column": 0,
            "sesoi": dec.SESOI["H2"],
            "rows": [normal("primary (two-stage)", h2["estimate"], h2["se"], stats.t.ppf(0.975, h2["dof"]))]
            + variants("H2"),
        },
        {
            "title": "H3 · upper tail, kg/m²",
            "column": 0,
            "sesoi": dec.SESOI["H3"],
            "rows": [normal("primary", h3["estimate"], h3["se"])] + variants("H3"),
        },
        {"title": "H4 · states, pp per SD of use", "column": 1, "rows": rows4 + variants("H4")},
        {
            "title": "H5 · simulated effect, pp",
            "column": 1,
            "rows": [("primary", sim["median"], sim["p5"], sim["p95"], "primary")] + variants("H5"),
        },
        {
            "title": "H6 · initiators, kg/m²",
            "column": 1,
            "sesoi": dec.SESOI["H6"],
            "rows": [normal("primary", h6["primary"]["estimate"], h6["primary"]["se"])] + variants("H6"),
        },
        {
            "title": "NC1 · height, cm",
            "column": 1,
            "margin": 0.5,
            "rows": [normal("primary (ages 25–64)", nc1["estimate"], nc1["se"])] + variants("NC1"),
        },
    ]


def draw_all(run: Path, sens: Path | None, out: Path) -> list[Path]:
    fd = run / "figdata"
    if not (fd / "nc1_yearly.csv").exists():
        raise FileNotFoundError(f"{fd} is missing; run scripts/make_figures.py --recompute first")
    h1 = _json(run / "h1.json")
    series = pd.Series({int(k): v for k, v in h1["national_prevalence_median"].items()}).sort_index()
    nat = pd.read_csv(run / "h0_national.csv", index_col=0)
    v = _json(run / "verdicts.json")["family"]
    h2 = pd.read_csv(run / "h2.csv", index_col=0).loc["primary, two-stage"]
    h3, h6, nc1, h4, h5 = (_json(run / f"{k}.json") for k in ("h3", "h6", "nc1", "h4", "h5"))
    dep = pd.read_csv(run / "h1_departures.csv")
    sig = [
        {
            "key": "H2",
            "title": "H2  Diabetes contrast",
            "sub": "departure of the diabetes gap in mean BMI",
            "est": h2["estimate"],
            "se": h2["se"],
            "dof": h2["dof"],
        },
        {
            "key": "H3",
            "title": "H3  Upper tail",
            "sub": "90th percentile minus median",
            "est": h3["estimate"],
            "se": h3["se"],
            "dof": None,
        },
        {
            "key": "H6",
            "title": "H6  Individual change",
            "sub": f"initiators minus never-users ({h6['initiators']} initiators)",
            "est": h6["primary"]["estimate"],
            "se": h6["primary"]["se"],
            "dof": None,
        },
    ]
    for r in sig:
        r.update(ci90=v[r["key"]]["ci90"], p_holm=v[r["key"]]["p_holm"], label=v[r["key"]]["label"])
    states = pd.read_csv(fd / "h4_state_departures.csv", index_col=0).iloc[:, 0].rename("departure")
    E = pd.read_csv(run / "h4_exposure.csv", index_col=0)["E"]
    from glp1_review.run import Config

    return [
        fig_sources(
            nat,
            100 * series,
            h0_sources.nhanes_cycles(),
            pd.read_csv(run / "h0_age_changes.csv", index_col=0),
            out / "fig1_sources.png",
        ),
        fig_h1(
            series,
            dep[dep["counterfactual"] == "primary: linear 2011-2019"],
            {int(k): tuple(x) for k, x in h1["nc2_departures_pp"].items()},
            pd.read_csv(fd / "nc1_yearly.csv", index_col=0),
            nc1,
            out / "fig2_h1.png",
        ),
        fig_signatures(sig, out / "fig3_signatures.png"),
        fig_h4(
            pd.read_csv(fd / "h4_event_betas_se.csv", index_col=0),
            pd.concat([E, states], axis=1).dropna(),
            h4,
            out / "fig4_h4.png",
        ),
        fig_h5(
            np.load(fd / "h5_draws.npy"),
            tuple(h1["D2025_pp"]),
            h5["meps_2024_adult_rate"],
            Config().published_rate_2025,
            out / "fig5_h5.png",
        ),
        fig_q24(q24_panels(run, sens), out / "fig6_q24.png"),
    ]
