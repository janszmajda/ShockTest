"""
Aggregate statistics computation for ShockTest.

Reads all shock_events (with post-shock outcomes + categories) and
computes headline metrics, writing one document to shock_results.

Usage:
    python analysis/aggregate.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from analysis.helpers import get_db


def compute_aggregate_stats() -> dict | None:
    """
    Compute and store aggregate statistics across all shock events.

    Reads from shock_events, writes one document to shock_results
    with _id="aggregate_stats". Idempotent — safe to re-run.

    Returns:
        The stats dict written to MongoDB, or None if no shocks found.
    """
    db = get_db()
    shocks = list(db["shock_events"].find({}))

    if not shocks:
        print("No shocks in shock_events — run shock_detector.py first.")
        return None

    def reversion_rate(values: list[float]) -> float | None:
        return round(float(np.mean([v > 0 for v in values])), 4) if values else None

    def mean_val(values: list[float]) -> float | None:
        return round(float(np.mean(values)), 4) if values else None

    def std_val(values: list[float]) -> float | None:
        return round(float(np.std(values)), 4) if values else None

    # Collect reversion values per horizon
    rev_1h = [s["reversion_1h"] for s in shocks if s.get("reversion_1h") is not None]
    rev_6h = [s["reversion_6h"] for s in shocks if s.get("reversion_6h") is not None]
    rev_24h = [s["reversion_24h"] for s in shocks if s.get("reversion_24h") is not None]

    stats: dict = {
        "_id": "aggregate_stats",
        "total_shocks": len(shocks),
        "total_markets": len({s["market_id"] for s in shocks}),
        # 1h horizon
        "reversion_rate_1h": reversion_rate(rev_1h),
        "mean_reversion_1h": mean_val(rev_1h),
        "std_reversion_1h": std_val(rev_1h),
        "sample_size_1h": len(rev_1h),
        # 6h horizon (headline metric)
        "reversion_rate_6h": reversion_rate(rev_6h),
        "mean_reversion_6h": mean_val(rev_6h),
        "std_reversion_6h": std_val(rev_6h),
        "sample_size_6h": len(rev_6h),
        # 24h horizon
        "reversion_rate_24h": reversion_rate(rev_24h),
        "mean_reversion_24h": mean_val(rev_24h),
        "std_reversion_24h": std_val(rev_24h),
        "sample_size_24h": len(rev_24h),
        # Category breakdown
        "by_category": {},
    }

    # Per-category breakdown
    categories = {s.get("category") for s in shocks if s.get("category")}
    for cat in sorted(categories):
        cat_shocks = [s for s in shocks if s.get("category") == cat]
        cat_rev_6h = [s["reversion_6h"] for s in cat_shocks if s.get("reversion_6h") is not None]
        stats["by_category"][cat] = {
            "count": len(cat_shocks),
            "reversion_rate_6h": reversion_rate(cat_rev_6h),
            "mean_reversion_6h": mean_val(cat_rev_6h),
            "sample_size_6h": len(cat_rev_6h),
        }

    # Upsert into shock_results
    db["shock_results"].update_one(
        {"_id": "aggregate_stats"},
        {"$set": stats},
        upsert=True,
    )

    # Print headline results
    print("=" * 60)
    print("SHOCKTEST RESULTS")
    print("=" * 60)
    print(f"Total shocks:    {stats['total_shocks']}")
    print(f"Total markets:   {stats['total_markets']}")
    print()
    for h, label in [(1, "1h"), (6, "6h"), (24, "24h")]:
        rate = stats[f"reversion_rate_{label}"]
        mean = stats[f"mean_reversion_{label}"]
        n = stats[f"sample_size_{label}"]
        if rate is not None:
            print(f"{label} reversion rate: {rate:.1%}  (mean={mean:+.4f}, n={n})")
        else:
            print(f"{label} reversion rate: N/A (no data)")

    print()
    print("By category:")
    for cat, data in stats["by_category"].items():
        rate = data.get("reversion_rate_6h")
        n = data.get("sample_size_6h", 0)
        rate_str = f"{rate:.1%}" if rate is not None else "N/A"
        print(f"  {cat:15s}: {data['count']:3d} shocks  6h_rate={rate_str}  (n={n})")

    return stats


if __name__ == "__main__":
    compute_aggregate_stats()
