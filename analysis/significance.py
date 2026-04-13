"""
Statistical significance and confidence intervals for ShockTest.

Reports both naive (treats each shock as independent) and cluster-robust
(clustered by market_id) statistics. Shocks from the same market are
autocorrelated, so naive z-stats are inflated — always cite the clustered
numbers in public claims.

Computes:
  - Wilson score 95% CI on reversion win rates (naive)
  - Bootstrap 95% CI on mean reversion values (naive)
  - Cluster-robust (Liang-Zeger) 95% CI and z-stats, clustered by market_id
  - One-sample z-test vs H0=50% (win rate) or H0=0 (mean reversion)
  - Per-category + per-source significance

Stores results in shock_results["aggregate_stats"]["significance"].

Usage:
    python analysis/significance.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import math

import numpy as np

from analysis.helpers import get_db

Z_95 = 1.96  # z* for 95% confidence
N_BOOTSTRAP = 10_000
RNG = np.random.default_rng(42)


def wilson_ci(n_success: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score confidence interval for a proportion (assumes independent obs)."""
    if n == 0:
        return (0.0, 0.0)
    p = n_success / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (round(float(center - margin), 4), round(float(center + margin), 4))


def bootstrap_ci(values: list[float], stat_fn=np.mean, z: float = Z_95) -> tuple[float, float]:
    """Percentile bootstrap 95% CI (assumes independent obs)."""
    arr = np.array(values)
    boots = [stat_fn(RNG.choice(arr, size=len(arr), replace=True)) for _ in range(N_BOOTSTRAP)]
    lo = round(float(np.percentile(boots, 2.5)), 4)
    hi = round(float(np.percentile(boots, 97.5)), 4)
    return (lo, hi)


def cluster_robust_se(values: np.ndarray, clusters: np.ndarray) -> tuple[float, int]:
    """
    Cluster-robust SE of the sample mean (Liang-Zeger sandwich with G/(G-1)
    small-cluster correction). Clusters should be market_ids so that
    autocorrelated shocks on the same market are correctly bundled.

    Returns (SE, n_clusters). SE = 0 and n_clusters = 0 if values is empty.
    """
    if len(values) == 0:
        return 0.0, 0
    xbar = float(values.mean())
    unique = np.unique(clusters)
    G = len(unique)
    if G == 0:
        return 0.0, 0
    s_sq = 0.0
    for g in unique:
        mask = clusters == g
        s_g = float(np.sum(values[mask] - xbar))
        s_sq += s_g * s_g
    n = len(values)
    V = s_sq / (n * n) * (G / max(G - 1, 1))
    return math.sqrt(V), G


def z_test_naive(n_success: int, n: int) -> float:
    """Naive z-test vs H0 = 50%, assuming independent Bernoulli obs."""
    if n == 0:
        return 0.0
    p_hat = n_success / n
    se = math.sqrt(0.5 * 0.5 / n)
    return (p_hat - 0.5) / se if se > 0 else 0.0


def compute_significance(
    values: list[float],
    clusters: list,
    label: str,
) -> dict:
    """Compute naive + cluster-robust stats for a list of reversion values.

    Args:
        values:   reversion_Xh floats (one per shock).
        clusters: market_id per shock (same length as values).
        label:    printed label.
    """
    arr = np.array(values, dtype=float)
    cl = np.array(clusters)
    n = len(arr)
    if n == 0:
        return {
            "n": 0,
            "n_clusters": 0,
            "win_rate": 0.0,
            "mean_reversion": 0.0,
        }
    n_pos = int(np.sum(arr > 0))
    win_rate = n_pos / n
    mean_rev = float(arr.mean())

    # naive (assumes independent shocks)
    win_rate_ci_naive = wilson_ci(n_pos, n)
    mean_rev_ci_naive = bootstrap_ci(values)
    z_winrate_naive = round(float(z_test_naive(n_pos, n)), 3)
    se_mean_naive = float(arr.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    z_mean_naive = round(mean_rev / se_mean_naive, 3) if se_mean_naive > 0 else 0.0

    # cluster-robust (clustered by market_id)
    wins = (arr > 0).astype(float)
    se_wr_cl, G = cluster_robust_se(wins, cl)
    se_mean_cl, _ = cluster_robust_se(arr, cl)
    z_winrate_cl = round((win_rate - 0.5) / se_wr_cl, 3) if se_wr_cl > 0 else 0.0
    z_mean_cl = round(mean_rev / se_mean_cl, 3) if se_mean_cl > 0 else 0.0
    wr_ci_cl = (
        round(win_rate - Z_95 * se_wr_cl, 4),
        round(win_rate + Z_95 * se_wr_cl, 4),
    )
    mean_ci_cl = (
        round(mean_rev - Z_95 * se_mean_cl, 4),
        round(mean_rev + Z_95 * se_mean_cl, 4),
    )

    result = {
        "n": n,
        "n_clusters": G,
        "win_rate": round(win_rate, 4),
        "win_rate_ci_95_naive": list(win_rate_ci_naive),
        "win_rate_ci_95_clustered": list(wr_ci_cl),
        "mean_reversion": round(mean_rev, 4),
        "mean_reversion_ci_95_naive": list(mean_rev_ci_naive),
        "mean_reversion_ci_95_clustered": list(mean_ci_cl),
        "z_winrate_naive": z_winrate_naive,
        "z_winrate_clustered": z_winrate_cl,
        "z_mean_naive": z_mean_naive,
        "z_mean_clustered": z_mean_cl,
        "significant_vs_50pct_clustered": bool(abs(z_winrate_cl) > Z_95),
    }

    sig_str = "YES ***" if result["significant_vs_50pct_clustered"] else "no"
    print(
        f"  {label:30s}  n={n:4d} G={G:3d}  "
        f"win={win_rate:.1%} clust95%[{wr_ci_cl[0]:.1%}, {wr_ci_cl[1]:.1%}]  "
        f"mean={mean_rev:+.4f} clust95%[{mean_ci_cl[0]:+.4f}, {mean_ci_cl[1]:+.4f}]  "
        f"z_naive={z_winrate_naive:+.2f} z_clust={z_winrate_cl:+.2f}  sig>50%: {sig_str}"
    )
    return result


def _subset(shocks: list[dict], horizon: str, predicate=None) -> tuple[list[float], list]:
    """Extract (reversion_Xh values, market_ids) for shocks matching predicate."""
    vals: list[float] = []
    clusters: list = []
    for s in shocks:
        v = s.get(f"reversion_{horizon}")
        if v is None:
            continue
        if predicate is not None and not predicate(s):
            continue
        vals.append(v)
        clusters.append(s["market_id"])
    return vals, clusters


def run_significance_analysis() -> dict:
    db = get_db()
    shocks = list(db["shock_events"].find({}))
    print(f"Loaded {len(shocks)} shocks\n")

    significance: dict = {}

    # ── Overall by horizon ────────────────────────────────────────────────
    print("Overall significance by horizon (clustered by market_id):")
    for h in ["1h", "6h", "24h"]:
        vals, cl = _subset(shocks, h)
        significance[f"overall_{h}"] = compute_significance(vals, cl, f"overall {h}")

    # ── By source at 6h ───────────────────────────────────────────────────
    print("\nBy source (6h):")
    significance["by_source_6h"] = {}
    for src in sorted({s.get("source") for s in shocks if s.get("source")}):
        vals, cl = _subset(shocks, "6h", lambda s, src=src: s.get("source") == src)
        if vals:
            significance["by_source_6h"][src] = compute_significance(vals, cl, src)

    # ── Per category at 6h ────────────────────────────────────────────────
    print("\nPer-category significance (6h):")
    categories = sorted({s["category"] for s in shocks if s.get("category")})
    significance["by_category_6h"] = {}
    for cat in categories:
        vals, cl = _subset(shocks, "6h", lambda s, cat=cat: s.get("category") == cat)
        if vals:
            significance["by_category_6h"][cat] = compute_significance(vals, cl, cat)

    # ── Store in MongoDB ──────────────────────────────────────────────────
    db["shock_results"].update_one(
        {"_id": "aggregate_stats"},
        {"$set": {"significance": significance}},
        upsert=True,
    )

    print("\nStored significance data in shock_results.")
    return significance


if __name__ == "__main__":
    run_significance_analysis()
