"""Inference criteria (pre-registration Q22, v2 of 2026-11-14).

Confirmatory family H2, H3, H6, all with a predicted negative estimand:
  supported     one-sided test of H0: theta >= 0, Holm-adjusted p < 0.05 across the family
  contradicted  one-sided test of H0: theta <= -SESOI rejected at alpha = 0.05 (the 90% CI lies above -SESOI);
                not adjusted for multiplicity
  inconclusive  neither
H6 is inconclusive if the placebo beta_late is significantly negative (one-sided, alpha = 0.05), and leaves the
family (reported descriptively) if there are fewer than 30 initiators.

If an estimate is both supported and contradicted (significantly negative but shown to be smaller in magnitude
than the SESOI), it is classified as contradicted: the effect exists but is too small to matter (decided
by the author on 2026-11-14 and added to Q22).
"""

from dataclasses import dataclass

from scipy.stats import norm
from scipy.stats import t as t_dist

ALPHA = 0.05
SESOI = {"H2": 0.2, "H3": 0.3, "H6": 0.5}  # kg/m2, magnitudes of the negative effects (Q20)
Z90 = norm.ppf(0.95)


@dataclass
class Estimate:
    est: float
    se: float
    dof: float | None = None  # Student-t reference distribution when given (e.g. two-stage H2), else normal

    def q(self, p: float) -> float:
        return float(t_dist.ppf(p, self.dof)) if self.dof else float(norm.ppf(p))

    def cdf(self, z: float) -> float:
        return float(t_dist.cdf(z, self.dof)) if self.dof else float(norm.cdf(z))


def p_one_sided_negative(e: Estimate) -> float:
    """p-value of H0: theta >= 0 against theta < 0."""
    return e.cdf(e.est / e.se)


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjusted p-values."""
    order = sorted(pvals, key=pvals.get)
    m = len(order)
    adj, running = {}, 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvals[k]))
        adj[k] = running
    return adj


def contradicted(e: Estimate, sesoi: float) -> bool:
    return e.est - e.q(0.95) * e.se > -sesoi


def classify_family(
    estimates: dict[str, Estimate],
    h6_late: Estimate | None = None,
    h6_initiators: int | None = None,
    sesoi: dict[str, float] = SESOI,
) -> dict[str, dict]:
    est = dict(estimates)
    out: dict[str, dict] = {}
    if "H6" in est and h6_initiators is not None and h6_initiators < 30:
        out["H6"] = {"label": "descriptive", "reason": f"{h6_initiators} initiators < 30"}
        est.pop("H6")
    p = {k: p_one_sided_negative(e) for k, e in est.items()}
    padj = holm(p)
    for k, e in est.items():
        sup = padj[k] < ALPHA
        con = contradicted(e, sesoi[k])
        label = "contradicted" if con else "supported" if sup else "inconclusive"
        info = {
            "label": label,
            "p_one_sided": p[k],
            "p_holm": padj[k],
            "ci90": (e.est - e.q(0.95) * e.se, e.est + e.q(0.95) * e.se),
        }
        if k == "H6" and h6_late is not None:
            late_neg = p_one_sided_negative(h6_late) < ALPHA
            info["placebo_late_significant"] = late_neg
            if late_neg:
                info["label"], info["reason"] = "inconclusive", "placebo beta_late significantly negative"
        out[k] = info
    return out


def nc1_passes(e: Estimate, margin_cm: float = 0.5) -> bool:
    """Equivalence (TOST, alpha 0.05): the 90% CI lies inside +-margin."""
    return (e.est - e.q(0.95) * e.se > -margin_cm) and (e.est + e.q(0.95) * e.se < margin_cm)


def overall_verdict(family: dict[str, dict], nc1_pass: bool) -> str:
    labels = [v["label"] for k, v in family.items() if k in ("H2", "H3", "H6")]
    n_sup = sum(lab == "supported" for lab in labels)
    n_con = sum(lab == "contradicted" for lab in labels)
    if n_sup >= 2 and n_con == 0 and nc1_pass:
        return "GLP-1 signature present"
    if n_con >= 2 or not nc1_pass:
        return "absent"
    return "mixed"


def h1_break_present(ci_primary: tuple[float, float], signs_alternatives: list[float]) -> bool:
    """95% CrI of D_2025 excludes zero under the primary counterfactual and the sign agrees under the alternatives."""
    lo, hi = ci_primary
    if lo <= 0 <= hi:
        return False
    sign = 1 if lo > 0 else -1
    return all((s > 0) == (sign > 0) for s in signs_alternatives)


def h4_supportive(p_perm: float, rr_interval_m002: tuple[float, float]) -> bool:
    lo, hi = rr_interval_m002
    return p_perm < ALPHA and not (lo <= 0 <= hi)


def h5_compatibility(ci_d2025: tuple[float, float], sim_effects_pp) -> str:
    import numpy as np

    p5, p95 = np.percentile(sim_effects_pp, [5, 95])
    lo, hi = ci_d2025
    if hi < p5:
        return "larger than the drugs can explain"
    if lo > p95:
        return "smaller than expected"
    return "compatible" if (lo <= p95 and hi >= p5) else "not compatible"
