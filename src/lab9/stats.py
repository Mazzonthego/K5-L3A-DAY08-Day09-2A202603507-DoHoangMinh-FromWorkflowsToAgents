"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

import math

try:
    import numpy as np
    from scipy.stats import bootstrap
except Exception:
    np = None
    bootstrap = None

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    tp = fp = fn = tn = 0
    for h, j in zip(human, judge):
        h_pos = h == POS
        j_pos = j == POS
        if j_pos and h_pos:
            tp += 1
        elif j_pos and not h_pos:
            fp += 1
        elif not j_pos and h_pos:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    """precision = tp/(tp+fp), recall = tp/(tp+fn); return 0.0 when the denominator is 0"""
    c = confusion(human, judge)
    p = c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else 0.0
    r = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else 0.0
    return p, r


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    c = confusion(human, judge)
    n = sum(c.values())
    if not n:
        raise ValueError("no samples")
    p_o = (c["tp"] + c["tn"]) / n
    p_h_pos = (c["tp"] + c["fn"]) / n
    p_j_pos = (c["tp"] + c["fp"]) / n
    p_e = p_h_pos * p_j_pos + (1 - p_h_pos) * (1 - p_j_pos)
    if p_e == 1:
        raise ValueError("undefined kappa for a constant judge")
    return (p_o - p_e) / (1 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denom = sensitivity + specificity - 1
    if denom == 0:
        return observed_rate
    val = (observed_rate + specificity - 1) / denom
    return max(0.0, min(1.0, val))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    if all(x == y for x, y in zip(a, b)):
        return 0.0, 0.0, 0.0
    d = float(sum(x - y for x, y in zip(a, b))) / len(a)
    if bootstrap is None or np is None:
        raise RuntimeError("scipy and numpy required for paired_bootstrap")
    res = bootstrap((np.asarray(a, dtype=float), np.asarray(b, dtype=float)),
                    statistic=lambda x, y: np.mean(x) - np.mean(y),
                    paired=True, method="percentile",
                    n_resamples=n_resamples, rng=np.random.default_rng(rng))
    conf_int = res.confidence_interval
    lo = float(conf_int.low)
    hi = float(conf_int.high)
    return d, lo, hi


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    if k <= 0 or k > n or c < 0 or c > n:
        raise ValueError(f"invalid args: n={n}, c={c}, k={k}")
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    if k <= 0 or k > n or c < 0 or c > n:
        raise ValueError(f"invalid args: n={n}, c={c}, k={k}")
    return math.comb(c, k) / math.comb(n, k)
