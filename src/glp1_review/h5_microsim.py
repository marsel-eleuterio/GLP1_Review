"""H5: mechanical plausibility microsimulation (pre-registration Q19).

Applied to 2025 BRFSS adults with BMI. Each of the 10,000 draws samples the parameters
    national use scale  so that adult use lies in U(MEPS 2024 rate, published 2025 rate)
    persistence         U(0.30, 0.45) without diabetes, U(0.45, 0.60) with diabetes
    loss, persistent    U(8%, 16%)
    loss, stopped       U(2%, 7%)
and computes the simulated effect = observed obesity prevalence - counterfactual prevalence (pp), where a user's
counterfactual BMI is observed BMI / (1 - loss). Within a draw the expectation over who uses and who persists is
computed exactly (use probability x persistence), so the 10,000 draws carry parameter uncertainty only.
Use probabilities come from MEPS 2024 by BMI class (25-30, 30-35, 35-40, 40+; zero below 25) x diabetes.

Version 2 (if H6 has SE < 0.5 kg/m2): counterfactual BMI of a user = observed BMI - beta_H6 (a lower bound).
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

BMI_CLASSES = [25, 30, 35, 40, np.inf]


@dataclass
class Params:
    meps_rate: float  # national adult use rate, MEPS 2024
    published_rate: float  # published 2025 rate (KFF/Gallup)
    persistence_no_diab: tuple[float, float] = (0.30, 0.45)
    persistence_diab: tuple[float, float] = (0.45, 0.60)
    loss_persistent: tuple[float, float] = (0.08, 0.16)
    loss_stopped: tuple[float, float] = (0.02, 0.07)
    n_draws: int = 10_000
    seed: int = 20261114
    fixed: dict = field(default_factory=dict)  # Q24 sensitivities, e.g. {"persistence_no_diab": 0.352}


def bmi_class(bmi: np.ndarray) -> np.ndarray:
    """0 = below 25, 1 = 25-30, 2 = 30-35, 3 = 35-40, 4 = 40+."""
    return np.digitize(bmi, BMI_CLASSES[:-1])


def _collapse(bmi, diab, w) -> pd.DataFrame:
    d = pd.DataFrame({"bmi": np.round(np.asarray(bmi, float), 2), "diab": np.asarray(diab, int), "w": w})
    return d.groupby(["bmi", "diab"], as_index=False)["w"].sum()


def _draw(p: Params, name: str, rng, n):
    if name in p.fixed:
        return np.full(n, p.fixed[name])
    lo, hi = getattr(p, name)
    return rng.uniform(lo, hi, n)


def simulate(bmi, diab, w, use_prob: pd.DataFrame, p: Params) -> np.ndarray:
    """Simulated effects in pp (negative = drugs lower obesity). use_prob: index (bmi_class 1-4, diab 0/1) ->
    column 'p' (MEPS 2024 probability of use)."""
    rng = np.random.default_rng(p.seed)
    d = _collapse(bmi, diab, w)
    cls = bmi_class(d["bmi"].to_numpy())
    pu = np.array(
        [use_prob["p"].get((c, g), 0.0) if c > 0 else 0.0 for c, g in zip(cls, d["diab"], strict=True)]
    )
    W = d["w"].to_numpy() / d["w"].sum()
    b = d["bmi"].to_numpy()
    dia = d["diab"].to_numpy().astype(bool)
    obese = (b >= 30).astype(float)
    base_rate = float(np.sum(W * pu))

    n = p.n_draws
    target = p.fixed.get("national_rate", None)
    rate = np.full(n, target) if target is not None else rng.uniform(p.meps_rate, p.published_rate, n)
    scale = rate / base_rate
    pers_n = _draw(p, "persistence_no_diab", rng, n)
    pers_d = _draw(p, "persistence_diab", rng, n)
    lp = _draw(p, "loss_persistent", rng, n)
    ls = _draw(p, "loss_stopped", rng, n)

    out = np.empty(n)
    for i in range(n):
        u = np.clip(pu * scale[i], 0, 1)
        pers = np.where(dia, pers_d[i], pers_n[i])
        cf_obese = (1 - u) * obese + u * (
            pers * (b / (1 - lp[i]) >= 30) + (1 - pers) * (b / (1 - ls[i]) >= 30)
        )
        out[i] = 100 * np.sum(W * (obese - cf_obese))
    return out


def simulate_h6(bmi, diab, w, use_prob: pd.DataFrame, p: Params, beta_h6: float) -> np.ndarray:
    """Version 2: a user's counterfactual BMI is observed BMI - beta_H6 (beta negative)."""
    rng = np.random.default_rng(p.seed)
    d = _collapse(bmi, diab, w)
    cls = bmi_class(d["bmi"].to_numpy())
    pu = np.array(
        [use_prob["p"].get((c, g), 0.0) if c > 0 else 0.0 for c, g in zip(cls, d["diab"], strict=True)]
    )
    W = d["w"].to_numpy() / d["w"].sum()
    b = d["bmi"].to_numpy()
    obese = (b >= 30).astype(float)
    cf = (b - beta_h6 >= 30).astype(float)
    rate = rng.uniform(p.meps_rate, p.published_rate, p.n_draws) / float(np.sum(W * pu))
    return np.array([100 * np.sum(W * np.clip(pu * s, 0, 1) * (obese - cf)) for s in rate])
