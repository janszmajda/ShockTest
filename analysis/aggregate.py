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

    In addition to total shock counts, records the distinct-market count
    per horizon (clusters_Xh). Shocks on the same market are autocorrelated,
    so cluster counts are the right denominator for honest claims —
    sample_size_Xh is inflated by repeat shocks within a market.

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

    def horizon_rows(horizon: str, predicate=None) -> list[dict]:
        rows = [s for s in shocks if s.get(f"reversion_{horizon}") is not None]
        if predicate is not None:
            rows = [s for s in rows if predicate(s)]
        return rows

    def summarize(rows: list[dict], horizon: str) -> dict:
        vals = [s[f"reversion_{horizon}"] for s in rows]
        clusters = {s["market_id"] for s in rows}
        return {
            "reversion_rate": reversion_rate(vals),
            "mean_reversion": mean_val(vals),
            "std_reversion": std_val(vals),
            "sample_size": len(vals),
            "n_clusters": len(clusters),
        }

    rev_1h_rows = horizon_rows("1h")
    rev_6h_rows = horizon_rows("6h")
    rev_24h_rows = horizon_rows("24h")

    rev_1h = [s["reversion_1h"] for s in rev_1h_rows]
    rev_6h = [s["reversion_6h"] for s in rev_6h_rows]
    rev_24h = [s["reversion_24h"] for s in rev_24h_rows]

    stats: dict = {
        "_id": "aggregate_stats",
        "total_shocks": len(shocks),
        "total_markets": len({s["market_id"] for s in shocks}),
        # 1h horizon
        "reversion_rate_1h": reversion_rate(rev_1h),
        "mean_reversion_1h": mean_val(rev_1h),
        "std_reversion_1h": std_val(rev_1h),
        "sample_size_1h": len(rev_1h),
        "clusters_1h": len({s["market_id"] for s in rev_1h_rows}),
        # 6h horizon (headline metric)
        "reversion_rate_6h": reversion_rate(rev_6h),
        "mean_reversion_6h": mean_val(rev_6h),
        "std_reversion_6h": std_val(rev_6h),
        "sample_size_6h": len(rev_6h),
        "clusters_6h": len({s["market_id"] for s in rev_6h_rows}),
        # 24h horizon
        "reversion_rate_24h": reversion_rate(rev_24h),
        "mean_reversion_24h": mean_val(rev_24h),
        "std_reversion_24h": std_val(rev_24h),
        "sample_size_24h": len(rev_24h),
        "clusters_24h": len({s["market_id"] for s in rev_24h_rows}),
        # Breakdowns
        "by_source": {},
        "by_category": {},
    }

    # Per-source breakdown (polymarket vs manifold) — critical since the
    # public framing is Polymarket-specific.
    sources = {s.get("source") for s in shocks if s.get("source")}
    for src in sorted(sources):
        src_total = [s for s in shocks if s.get("source") == src]
        stats["by_source"][src] = {
            "count": len(src_total),
            "markets": len({s["market_id"] for s in src_total}),
            "1h": summarize(horizon_rows("1h", lambda s, src=src: s.get("source") == src), "1h"),
            "6h": summarize(horizon_rows("6h", lambda s, src=src: s.get("source") == src), "6h"),
            "24h": summarize(horizon_rows("24h", lambda s, src=src: s.get("source") == src), "24h"),
        }

    # Per-category breakdown
    categories = {s.get("category") for s in shocks if s.get("category")}
    for cat in sorted(categories):
        cat_rows_6h = horizon_rows("6h", lambda s, cat=cat: s.get("category") == cat)
        cat_shocks = [s for s in shocks if s.get("category") == cat]
        stats["by_category"][cat] = {
            "count": len(cat_shocks),
            "reversion_rate_6h": reversion_rate([s["reversion_6h"] for s in cat_rows_6h]),
            "mean_reversion_6h": mean_val([s["reversion_6h"] for s in cat_rows_6h]),
            "sample_size_6h": len(cat_rows_6h),
            "clusters_6h": len({s["market_id"] for s in cat_rows_6h}),
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
        G = stats[f"clusters_{label}"]
        if rate is not None:
            print(f"{label} reversion rate: {rate:.1%}  (mean={mean:+.4f}, n={n} from G={G} markets)")
        else:
            print(f"{label} reversion rate: N/A (no data)")

    print()
    print("By source (6h):")
    for src, data in stats["by_source"].items():
        h6 = data["6h"]
        rate = h6.get("reversion_rate")
        rate_str = f"{rate:.1%}" if rate is not None else "N/A"
        print(
            f"  {src:12s}: {data['count']:4d} shocks total, "
            f"6h_rate={rate_str}  (n={h6['sample_size']} from G={h6['n_clusters']} markets)"
        )

    print()
    print("By category (6h):")
    for cat, data in stats["by_category"].items():
        rate = data.get("reversion_rate_6h")
        n = data.get("sample_size_6h", 0)
        G = data.get("clusters_6h", 0)
        rate_str = f"{rate:.1%}" if rate is not None else "N/A"
        print(f"  {cat:15s}: {data['count']:4d} shocks  6h_rate={rate_str}  (n={n} from G={G} markets)")

    return stats


if __name__ == "__main__":
    compute_aggregate_stats()
