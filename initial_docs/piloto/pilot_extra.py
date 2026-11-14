"""Extra pilot checks: event-study slopes by year and robustness of the state gradient.
Run: python3 -I pilot_extra.py <data_dir>   (needs pilot_state_table.csv written by pilot_glp1_obesity.py)
"""
import sys
import numpy as np
import pandas as pd

D = sys.argv[1]
rng = np.random.default_rng(7)
ob = pd.concat([pd.read_csv(f"{D}/brfss_ob_total_{a}.csv") for a in ("2011_2015", "2016_2021", "2022_2025")], ignore_index=True)
st = ob[~ob["loc"].isin({"GU", "PR", "VI", "US"})]
Y = st.pivot(index="loc", columns="year", values="value")
T = pd.read_csv(f"{D}/pilot_state_table.csv", index_col=0)   # 50 states with all-payer measure


def ols(y, x, w=None):
    X = np.c_[np.ones(len(y)), x]
    if w is None:
        w = np.ones(len(y))
    sw = np.sqrt(w)
    b = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]
    r = (y - X @ b) * sw
    V = (r @ r / (len(y) - X.shape[1])) * np.linalg.inv((X * sw[:, None]).T @ (X * sw[:, None]))
    return b[1], np.sqrt(V[1, 1])


print("=== event study: slope of (obesity_t - mean 2015-19) on z(exposure), by year ===")
for en in ("allpayer_rx_per100", "medicare_claims_per_adult", "medicaid_per1000"):
    e = T[en]; z = (e - e.mean()) / e.std(ddof=1)
    base = Y.loc[T.index, list(range(2015, 2020))].mean(axis=1)
    out = []
    for y in Y.columns:
        d = (Y.loc[T.index, y] - base).dropna()
        b, se = ols(d.values, z[d.index].values)
        out.append((int(y), round(b, 2), round(se, 2), len(d)))
    print(en, "\n  " + "  ".join(f"{y}:{b:+.2f}±{se:.2f}" for y, b, se, n in out))
    # linear pre-trend in the slopes (2011-2019) extrapolated
    yrs = np.array([o[0] for o in out], float); bs = np.array([o[1] for o in out])
    m = yrs <= 2019
    c1, c0 = np.polyfit(yrs[m], bs[m], 1)
    print("  pre-trend of slopes 2011-19: %.3f per year; detrended slopes 2023-25: " % c1 +
          ", ".join(f"{int(y)}:{b-(c0+c1*y):+.2f}" for y, b in zip(yrs, bs) if y >= 2023))

print("\n=== robustness of main spec: d_2122_2425 ~ z(all-payer Rx per 100 residents, 2024) ===")
e = T.allpayer_rx_per100; z = (e - e.mean()) / e.std(ddof=1)
y = T.d_2122_2425


def perm_p(yv, zv, B=20000, w=None):
    b, se = ols(yv, zv, w)
    cnt = 0
    for _ in range(B):
        bb, ss = ols(yv, rng.permutation(zv), w)
        cnt += abs(bb / ss) >= abs(b / se)
    return b, se, (cnt + 1) / (B + 1)


def show(label, idx, w=None):
    zz = z[idx].values; zz = (zz - zz.mean()) / zz.std(ddof=1)
    b, se, p = perm_p(y[idx].values, zz, w=None if w is None else w[idx].values)
    print(f"{label:55s} n={len(idx):2d} slope={b:+.2f} (SE {se:.2f}) perm p={p:.3f}")


allidx = T.index
show("all 50 states", allidx)
show("drop WV", allidx.drop("WV"))
show("drop WV, KY, LA, OK (4 highest-use with big drops)", allidx.drop(["WV", "KY", "LA", "OK"]))
show("drop states with a missing post year (CA, MS, NV, TN)", allidx.drop(["CA", "MS", "NV", "TN"]))
show("precision-weighted (1/se^2)", allidx, w=1 / T.se_d ** 2)
# exposure residualized on lagged obesity level (use beyond what the obesity level predicts)
bl, _ = ols(e.values, T.lag_1519.values)
res = e - (e.mean() + bl * (T.lag_1519 - T.lag_1519.mean()))
zr = (res - res.mean()) / res.std(ddof=1)
b, se, p = perm_p(y.values, zr.values)
print(f"{'exposure residualized on 2015-19 obesity level':55s} n={len(y):2d} slope={b:+.2f} (SE {se:.2f}) perm p={p:.3f}")
b, se, p = perm_p(T.dev_2425_tr1119.values, zr.values)
print(f"{'  same, outcome = deviation from own 2011-19 trend':55s} n={len(y):2d} slope={b:+.2f} (SE {se:.2f}) perm p={p:.3f}")
b, se, p = perm_p(T.pl_d_1516_1819.values, zr.values)
print(f"{'  same, placebo outcome (2015-16 -> 2018-19)':55s} n={len(y):2d} slope={b:+.2f} (SE {se:.2f}) perm p={p:.3f}")
print("corr(residualized exposure, lag level) =", round(np.corrcoef(res, T.lag_1519)[0, 1], 3))

print("\n=== scatter data for the doc (state, use, change) ===")
print(T[["allpayer_rx_per100", "d_2122_2425", "lag_1519"]].round(2).sort_values("allpayer_rx_per100").to_csv())
