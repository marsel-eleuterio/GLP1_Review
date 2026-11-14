"""Pilot test: GLP-1 use vs. change in adult obesity (BRFSS), United States.

Inputs (CSV, transcribed from CDC open-data API hn4x-zwk7 and The RX Index pages):
  argv[1] = data dir with brfss_*.csv and rxindex_*.csv
  argv[2] = dir with state-abbrevs.csv (state name -> postal code); can be the same data dir
Run: python3 -I pilot_glp1_obesity.py <data_dir> <pop_dir>
"""
import sys
import numpy as np
import pandas as pd

D, P = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(20261112)
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

# ---------------------------------------------------------------- load + checksum
ob = pd.concat([pd.read_csv(f"{D}/brfss_ob_total_{a}.csv") for a in ("2011_2015", "2016_2021", "2022_2025")],
               ignore_index=True)
chk = {2011: (1434.6, 52, 941400), 2012: (1452.7, 52, 884460), 2013: (1517.4, 53, 920736),
       2014: (1575.7, 54, 859845), 2015: (1583.4, 54, 803374), 2016: (1640.5, 55, 885166),
       2017: (1657.9, 54, 822587), 2018: (1690.0, 54, 798196), 2019: (1698.8, 53, 756138),
       2020: (1732.7, 54, 714442), 2021: (1811.0, 54, 777045), 2022: (1854.1, 55, 783875),
       2023: (1782.7, 53, 777816), 2024: (1836.4, 54, 822375), 2025: (1718.3, 51, 641688)}
print("=== 1. CHECKSUMS vs server-side aggregates (sum of values, count, sum of n) ===")
ok = True
for y, (sv, cnt, sn) in chk.items():
    g = ob[ob.year == y]
    a, b, c = round(g.value.sum(), 1), int(g.value.notna().sum()), int(g.n.sum())
    flag = "OK" if (abs(a - sv) < 0.05 and b == cnt and c == sn) else "MISMATCH"
    ok &= flag == "OK"
    print(f"{y}: sum={a} (api {sv})  count={b} (api {cnt})  sum_n={c} (api {sn})  rows={len(g)}  {flag}")
print("ALL CHECKSUMS OK" if ok else "!!! CHECKSUM MISMATCH")

ob["se"] = (ob.hi - ob.lo) / 3.92
TERR = {"GU", "PR", "VI", "US"}
st = ob[~ob["loc"].isin(TERR)].copy()
us = ob[ob["loc"] == "US"].set_index("year")
states = sorted(st["loc"].unique())
assert len(states) == 51, len(states)
Y = st.pivot(index="loc", columns="year", values="value")
SE = st.pivot(index="loc", columns="year", values="se")
years = np.array(sorted(Y.columns))
print("\nmissing state-years:", [(s, int(y)) for s in states for y in years if np.isnan(Y.loc[s, y])])

# ---------------------------------------------------------------- population weights
ab = pd.read_csv(f"{P}/state-abbrevs.csv")
name2ab = dict(zip(ab["state"], ab["abbreviation"]))
cz = pd.read_csv(f"{D}/census_18plus_2024.csv")          # Census Bureau, SCPRC-EST2024-18+POP (July 1, 2024)
us18 = int(cz.loc[cz.area == "United States", "pop_18plus"].iloc[0])
cz["ab"] = cz.area.map(name2ab)
w = cz.dropna(subset=["ab"]).set_index("ab").pop_18plus.reindex(states).astype(float)
assert w.notna().all()
print(f"adult-pop weights (Census, July 2024): sum over 50 states + DC = {int(w.sum()):,} (US row {us18:,}) -> "
      f"{'OK' if int(w.sum()) == us18 else 'MISMATCH'}; total-pop check: {int(cz.dropna(subset=['ab']).total_pop.sum()):,} vs "
      f"{int(cz.loc[cz.area == 'United States', 'total_pop'].iloc[0]):,}; CA share={w['CA']/w.sum():.3f}")

# ---------------------------------------------------------------- national series
print("\n=== 2. NATIONAL SERIES ===")
# (a) published US row; (b) pop-weighted mean of available states; (c) composition-adjusted via weighted 2-way FE
rows = [(s, y, Y.loc[s, y]) for s in states for y in years if not np.isnan(Y.loc[s, y])]
si = {s: i for i, s in enumerate(states)}
yi = {y: i for i, y in enumerate(years)}
X = np.zeros((len(rows), len(states) + len(years) - 1))
yv = np.zeros(len(rows)); wv = np.zeros(len(rows))
for k, (s, y, v) in enumerate(rows):
    X[k, si[s]] = 1
    if yi[y] > 0:
        X[k, len(states) + yi[y] - 1] = 1
    yv[k] = v; wv[k] = w[s]
sw = np.sqrt(wv)
beta = np.linalg.lstsq(X * sw[:, None], yv * sw, rcond=None)[0]
alpha = beta[:len(states)]; tau = np.r_[0, beta[len(states):]]
adj = np.array([(w.values * (alpha + t)).sum() / w.sum() for t in tau])
raw = np.array([np.nansum(w.values * Y[y].values) / w.values[~np.isnan(Y[y].values)].sum() for y in years])
nat = pd.DataFrame({"us_row": us.value.reindex(years).values, "wmean_available": raw.round(2), "fe_adjusted": adj.round(2)}, index=years)
nat["n_states"] = [int(Y[y].notna().sum()) for y in years]
print(nat.to_string())


def trend_gap(series, fit_years, label):
    x = np.array(fit_years, float); yy = np.array([series[y] for y in fit_years], float)
    A = np.c_[np.ones_like(x), x - x.mean()]
    b = np.linalg.lstsq(A, yy, rcond=None)[0]
    res = yy - A @ b
    s2 = res @ res / (len(x) - 2)
    out = {}
    for y in (2023, 2024, 2025):
        a = np.array([1, y - x.mean()])
        proj = a @ b
        se_pred = np.sqrt(s2 * (1 + a @ np.linalg.inv(A.T @ A) @ a))
        out[y] = (proj, series[y] - proj, se_pred)
    print(f"{label}: slope={b[1]:.3f} pp/yr, resid SD={np.sqrt(s2):.2f} | " +
          " | ".join(f"{y}: proj={p:.2f} gap={g:+.2f} (pred SE {s:.2f})" for y, (p, g, s) in out.items()))
    return b[1], out


print("\n-- break vs trend (obesity, %) --")
ser_us = dict(zip(years, nat.us_row)); ser_adj = dict(zip(years, nat.fe_adjusted))
g = {}
g["us_1119"] = trend_gap(ser_us, range(2011, 2020), "US row, trend 2011-2019 ")
g["adj_1119"] = trend_gap(ser_adj, range(2011, 2020), "FE-adj,  trend 2011-2019 ")
g["us_1122"] = trend_gap(ser_us, range(2011, 2023), "US row, trend 2011-2022 ")
g["adj_1122"] = trend_gap(ser_adj, range(2011, 2023), "FE-adj,  trend 2011-2022 ")
slope_pre = g["adj_1119"][0]
lvl = {y: ser_adj[2022] + slope_pre * (y - 2022) for y in (2023, 2024, 2025)}
print("FE-adj, pre-2020 slope continued from the 2022 level: " + " | ".join(f"{y}: proj={lvl[y]:.2f} gap={ser_adj[y]-lvl[y]:+.2f}" for y in lvl))
ADULTS = float(us18)
for k in ("adj_1119", "adj_1122"):
    gap25 = g[k][1][2025][1]
    print(f"  {k}: 2025 gap {gap25:+.2f} pp  ~ {gap25/100*ADULTS/1e6:+.1f} million adults (using {ADULTS/1e6:.0f}M adults)")
print(f"  level-2022 + pre slope: 2025 gap {ser_adj[2025]-lvl[2025]:+.2f} pp ~ {(ser_adj[2025]-lvl[2025])/100*ADULTS/1e6:+.1f} million")

# overweight mirror
ust = pd.read_csv(f"{D}/brfss_us_total.csv")
ow = ust[ust.q == "Q037"].set_index("year").value
obn = ust[ust.q == "Q036"].set_index("year").value
print("\n-- overweight (BMI 25-29.9), US row --")
trend_gap(dict(ow), range(2011, 2020), "overweight, trend 2011-2019")
trend_gap(dict(ow), range(2011, 2023), "overweight, trend 2011-2022")
rest = 100 - ow - obn
trend_gap(dict(rest), range(2011, 2020), "not overweight/obese, trend 2011-2019")
trend_gap(dict(rest), range(2011, 2023), "not overweight/obese, trend 2011-2022")
print(pd.DataFrame({"obese": obn, "overweight": ow, "neither": rest.round(1)}).loc[2019:].T.to_string())

# ---------------------------------------------------------------- age and sex
print("\n=== 3. AGE AND SEX (US rows; 2025 lacks CA/MS/NV, 2024 lacks TN) ===")
age = pd.read_csv(f"{D}/brfss_us_ob_by_age.csv").pivot(index="age", columns="year", values="value")
agw = pd.read_csv(f"{D}/brfss_us_ow_by_age.csv").pivot(index="age", columns="year", values="value")
gallup_use = {"18 - 24": 6.7, "25 - 34": (6.7 + 9.6) / 2, "35 - 44": (9.6 + 16.2) / 2, "45 - 54": (16.2 + 17.0) / 2,
              "55 - 64": 17.0, "65 or older": 11.1}   # Gallup Q2-Q3 2025, weight-loss GLP-1 injectables; bands mapped
kff_use = {"18 - 24": 4, "25 - 34": (4 + 11) / 2, "35 - 44": 11, "45 - 54": (11 + 22) / 2, "55 - 64": 22, "65 or older": 9}  # KFF Nov 2025, any GLP-1
tab = []
for a in age.index:
    x = np.arange(2011, 2020, dtype=float); yy = age.loc[a, 2011:2019].values
    b1, b0 = np.polyfit(x, yy, 1)
    x2 = np.arange(2011, 2023, dtype=float); b1b, b0b = np.polyfit(x2, age.loc[a, 2011:2022].values, 1)
    xo = np.arange(2011, 2020, dtype=float); c1, c0 = np.polyfit(xo, agw.loc[a, 2011:2019].values, 1)
    tab.append(dict(age=a, ob2022=age.loc[a, 2022], ob2024=age.loc[a, 2024], ob2025=age.loc[a, 2025],
                    d22_24=age.loc[a, 2024] - age.loc[a, 2022], d22_25=age.loc[a, 2025] - age.loc[a, 2022],
                    d2122_2425=age.loc[a, [2024, 2025]].mean() - age.loc[a, [2021, 2022]].mean(),
                    slope_pre=b1, gap24_tr1119=age.loc[a, 2024] - (b0 + b1 * 2024), gap25_tr1119=age.loc[a, 2025] - (b0 + b1 * 2025),
                    gap2425_tr1122=age.loc[a, [2024, 2025]].mean() - (b0b + b1b * 2024.5),
                    ow_gap2425_tr1119=agw.loc[a, [2024, 2025]].mean() - (c0 + c1 * 2024.5),
                    gallup_use=gallup_use[a], kff_use=kff_use[a]))
tab = pd.DataFrame(tab).set_index("age")
print(tab.round(2).to_string())
for col in ("d22_24", "d22_25", "d2122_2425", "gap24_tr1119", "gap25_tr1119", "gap2425_tr1122"):
    r1 = np.corrcoef(tab[col], tab.gallup_use)[0, 1]; r2 = np.corrcoef(tab[col], tab.kff_use)[0, 1]
    print(f"  corr({col}, use): Gallup-mapped r={r1:+.2f} | KFF-mapped r={r2:+.2f}   (n=6 age groups)")
# Gallup's own gradient (Oct 2025 article): change in obesity 2022->2025 vs weight-loss GLP-1 use
gd = np.array([-1.0, -2.2, -4.3, -5.0, 0.8]); gu = np.array([6.7, 9.6, 16.2, 17.0, 11.1])
print(f"  Gallup's own 5 age groups: corr(change 2022-25, use 2025) r={np.corrcoef(gd, gu)[0,1]:+.2f}; without 65+: r={np.corrcoef(gd[:4], gu[:4])[0,1]:+.2f}")
sx = pd.read_csv(f"{D}/brfss_us_by_sex.csv")
sxo = sx[sx.q == "Q036"].pivot(index="sex", columns="year", values="value")
print("\nobesity by sex (US row):"); print(sxo.loc[:, 2019:].to_string())
for s_ in sxo.index:
    b1, b0 = np.polyfit(np.arange(2011, 2020, dtype=float), sxo.loc[s_, 2011:2019].values, 1)
    print(f"  {s_}: change 2022->2025 {sxo.loc[s_,2025]-sxo.loc[s_,2022]:+.1f}; 2022->2024 {sxo.loc[s_,2024]-sxo.loc[s_,2022]:+.1f}; "
          f"gap vs 2011-19 trend: 2024 {sxo.loc[s_,2024]-(b0+b1*2024):+.2f}, 2025 {sxo.loc[s_,2025]-(b0+b1*2025):+.2f} (slope {b1:.2f})")

# ---------------------------------------------------------------- state dose-response
print("\n=== 4. STATE DOSE-RESPONSE ===")
mc = pd.read_csv(f"{D}/rxindex_medicaid_2025.csv")
mc["ab"] = mc.state.map(name2ab)
assert mc.ab.notna().all(), mc[mc.ab.isna()]
mc = mc.set_index("ab")
# internal consistency of the transcribed Medicaid table
rate = mc.medicaid_rx_2025 / mc.avg_monthly_medicaid_enrollment_2025 * 1000
print("Medicaid table: max |rate - recomputed| =", round((rate - mc.medicaid_rx_per_1000_enrollees_2025).abs().max(), 2),
      "| sum Rx =", int(mc.medicaid_rx_2025.sum()), "(page: 11,193,556)")
md = pd.read_csv(f"{D}/rxindex_medicare_2024.csv"); md["ab"] = md.state.map(name2ab); md = md.set_index("ab")
ts = pd.read_csv(f"{D}/rxindex_medicare_claims_2019_2024.csv"); ts["ab"] = ts.state.map(name2ab); ts = ts.set_index("ab")
print("Medicare tables: claims_2024 equal across the two tables:", bool((md.included_claims == ts.claims_2024.reindex(md.index)).all()),
      "| share col equal to Medicaid-page col:", bool((md.share_of_published_state_part_d_claims_pct.round(3) == mc.medicare_glp1_claim_share_2024_pct.reindex(md.index).round(3)).all()),
      "| national share sums to", round(md.share_of_national_included_claims_pct.sum(), 2))
cagr = ((ts.claims_2024 / ts.claims_2019) ** (1 / 5) - 1) * 100
print("Medicare CAGR recomputed vs page: max abs diff =", round((cagr - ts.cagr_2019_2024_pct).abs().max(), 2))

E = pd.DataFrame(index=states)
E["allpayer_rx_per100"] = mc.publisher_map_audit_per_100_residents_2024.reindex(states)      # PurpleLab via GLP-1 Newsroom, 2024
E["medicare_share"] = mc.medicare_glp1_claim_share_2024_pct.reindex(states)                  # % of Part D claims, 2024
E["medicaid_per1000"] = mc.medicaid_rx_per_1000_enrollees_2025.reindex(states)               # 2025
E["medicare_claims_per_adult"] = (ts.claims_2024.reindex(states) / w) * 100                  # claims per 100 adults (approx denominators)


def mean_avail(yrs):
    return Y[list(yrs)].mean(axis=1, skipna=True)


def se_mean(yrs):
    v = SE[list(yrs)] ** 2
    k = v.notna().sum(axis=1)
    return np.sqrt(v.sum(axis=1, skipna=True)) / k


O = pd.DataFrame(index=states)
O["base_2122"] = mean_avail((2021, 2022)); O["post_2425"] = mean_avail((2024, 2025))
O["d_2122_2425"] = O.post_2425 - O.base_2122
O["se_d"] = np.sqrt(se_mean((2021, 2022)) ** 2 + se_mean((2024, 2025)) ** 2)
O["d_1922_2425"] = O.post_2425 - mean_avail(range(2019, 2023))
O["lag_1519"] = mean_avail(range(2015, 2020))
O["d_22_25"] = Y[2025] - Y[2022]


def dev_from_trend(fit, post):
    out = {}
    for s in states:
        x = np.array([y for y in fit if not np.isnan(Y.loc[s, y])], float)
        yy = Y.loc[s, x.astype(int)].values
        b1, b0 = np.polyfit(x, yy, 1)
        d = [Y.loc[s, y] - (b0 + b1 * y) for y in post if not np.isnan(Y.loc[s, y])]
        out[s] = np.mean(d) if d else np.nan
    return pd.Series(out)


O["dev_2425_tr1119"] = dev_from_trend(range(2011, 2020), (2024, 2025))
O["dev_2425_tr1122"] = dev_from_trend(range(2011, 2023), (2024, 2025))
O["dev_25_tr1119"] = dev_from_trend(range(2011, 2020), (2025,))
# placebos (before the GLP-1 boom)
O["pl_d_1516_1819"] = mean_avail((2018, 2019)) - mean_avail((2015, 2016))
O["pl_dev_1819_tr1116"] = dev_from_trend(range(2011, 2017), (2018, 2019))
O["pl_d_1213_1516"] = mean_avail((2015, 2016)) - mean_avail((2012, 2013))

print("\nstate outcomes, summary (pp):")
print(O[["d_2122_2425", "se_d", "d_1922_2425", "d_22_25", "dev_2425_tr1119", "dev_2425_tr1122", "pl_d_1516_1819", "pl_dev_1819_tr1116"]].describe().loc[["count", "mean", "std", "min", "max"]].round(2).to_string())
print("pop-weighted mean of d_2122_2425:", round(np.average(O.d_2122_2425, weights=w), 2),
      "| of dev_2425_tr1119:", round(np.average(O.dev_2425_tr1119, weights=w), 2),
      "| of dev_2425_tr1122:", round(np.average(O.dev_2425_tr1122, weights=w), 2))
print("\nexposures, summary:")
print(E.describe().loc[["count", "mean", "std", "min", "max"]].round(2).to_string())
print("\ncorrelations among exposures and with lagged obesity level (2015-19):")
print(pd.concat([E, O[["lag_1519"]]], axis=1).corr(method="pearson").round(2).to_string())


def fit(y, Xc):
    n, k = Xc.shape
    XtX_inv = np.linalg.inv(Xc.T @ Xc)
    b = XtX_inv @ Xc.T @ y
    r = y - Xc @ b
    h = np.einsum("ij,jk,ik->i", Xc, XtX_inv, Xc)
    meat = (Xc * (r / (1 - h))[:, None]).T @ (Xc * (r / (1 - h))[:, None])
    V = XtX_inv @ meat @ XtX_inv                      # HC3
    s2 = r @ r / (n - k)
    return b, np.sqrt(np.diag(V)), np.sqrt(np.diag(s2 * XtX_inv)), r


def test(yname, ename, covs=(), B=20000):
    df = pd.concat([O[[yname] + list(covs)], E[[ename]]], axis=1).dropna()
    y = df[yname].values; e = df[ename].values
    z = (e - e.mean()) / e.std(ddof=1)
    Z = np.c_[np.ones(len(y))] if not covs else np.c_[np.ones(len(y)), (df[list(covs)] - df[list(covs)].mean()).values]
    Xf = np.c_[z, Z]
    b, se_hc3, se_ols, r = fit(y, Xf)
    t_obs = b[0] / se_ols[0]
    # Freedman-Lane permutation
    b0 = np.linalg.lstsq(Z, y, rcond=None)[0]; fit0 = Z @ b0; r0 = y - fit0
    XtX_inv = np.linalg.inv(Xf.T @ Xf); Hrow = (XtX_inv @ Xf.T)[0]
    cnt = 0
    for _ in range(B):
        ys = fit0 + rng.permutation(r0)
        bs = Hrow @ ys
        rs = ys - Xf @ (XtX_inv @ Xf.T @ ys)
        ts_ = bs / np.sqrt(rs @ rs / (len(y) - Xf.shape[1]) * XtX_inv[0, 0])
        cnt += abs(ts_) >= abs(t_obs)
    p = (cnt + 1) / (B + 1)
    rk = lambda v: pd.Series(v).rank().values
    rho = np.corrcoef(rk(y), rk(e))[0, 1]
    cv = e.std(ddof=1) / e.mean()
    return dict(outcome=yname, exposure=ename, covs="+".join(covs) or "-", n=len(y), slope_per_sd=b[0], se_hc3=se_hc3[0],
                se_ols=se_ols[0], perm_p=p, pearson=np.corrcoef(y, e)[0, 1], spearman=rho, cv_exposure=cv)


res = []
for en in E.columns:
    for yn, cv_ in (("d_2122_2425", ()), ("d_2122_2425", ("lag_1519",)), ("d_1922_2425", ()), ("d_22_25", ()),
                    ("dev_2425_tr1119", ()), ("dev_2425_tr1119", ("lag_1519",)), ("dev_2425_tr1122", ()), ("dev_25_tr1119", ()),
                    ("pl_d_1516_1819", ()), ("pl_dev_1819_tr1116", ()), ("pl_d_1213_1516", ())):
        res.append(test(yn, en, cv_))
R = pd.DataFrame(res)
print("\nregressions: outcome ~ z(exposure) [+ covariate]; slope = pp of obesity per 1 SD of exposure; permutation p (Freedman-Lane, 20,000)")
print(R.round(3).to_string(index=False))

# expected slope if the national gap were entirely due to GLP-1 and proportional to state exposure
print("\npower check: expected slope if the whole national gap were proportional to exposure (slope = G x CV)")
for G in (-1.0, -1.5, -2.0):
    for en in E.columns:
        row = R[(R.exposure == en) & (R.outcome == "dev_2425_tr1119") & (R.covs == "-")].iloc[0]
        exp = G * row.cv_exposure
        zexp = abs(exp) / row.se_ols
        from math import erf, sqrt
        Phi = lambda v: 0.5 * (1 + erf(v / sqrt(2)))
        power = 1 - Phi(1.96 - zexp) + Phi(-1.96 - zexp)
        print(f"  G={G:+.1f} pp, {en:26s}: expected slope {exp:+.2f} pp/SD vs SE {row.se_ols:.2f} -> expected z={zexp:.2f}, power~{100*power:.0f}%")

# terciles of the all-payer measure
print("\nterciles of all-payer Rx per 100 residents (2024):")
d = pd.concat([O, E], axis=1).dropna(subset=["allpayer_rx_per100"])
d["terc"] = pd.qcut(d.allpayer_rx_per100, 3, labels=["low use", "mid use", "high use"])
print(d.groupby("terc", observed=True).agg(n=("d_2122_2425", "size"), use=("allpayer_rx_per100", "mean"), lag_level=("lag_1519", "mean"),
                                            base_2122=("base_2122", "mean"), post_2425=("post_2425", "mean"), d_2122_2425=("d_2122_2425", "mean"),
                                            dev_tr1119=("dev_2425_tr1119", "mean"), dev_tr1122=("dev_2425_tr1122", "mean"),
                                            placebo_d=("pl_d_1516_1819", "mean")).round(2).to_string())
print("\nstates sorted by all-payer use: top 10 and bottom 10")
cols = ["allpayer_rx_per100", "base_2122", "post_2425", "d_2122_2425", "dev_2425_tr1119"]
print(d.sort_values("allpayer_rx_per100", ascending=False)[cols].head(10).round(2).to_string())
print(d.sort_values("allpayer_rx_per100")[cols].head(10).round(2).to_string())
d.to_csv(f"{D}/pilot_state_table.csv")
nat.to_csv(f"{D}/pilot_national_series.csv")
tab.to_csv(f"{D}/pilot_age_table.csv")
R.to_csv(f"{D}/pilot_regressions.csv", index=False)
