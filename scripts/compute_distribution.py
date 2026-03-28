"""Compute distribution parameters and backtest stats for the trade simulator.

Stores histogram bins, percentiles, and backtest summary in shock_results.
This data powers the frontend trade simulator's payoff charts and scenario analysis.
"""

import os
import sys

import numpy as np
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGODB_URI", "")
if not MONGO_URI:
    print("ERROR: MONGODB_URI not set.")
    sys.exit(1)

db = MongoClient(MONGO_URI)["shocktest"]


def compute_distributions() -> None:
    """Compute histogram bins + percentiles for each horizon."""
    shocks = list(db["shock_events"].find({}))
    print(f"Computing distributions from {len(shocks)} shocks...")

    for horizon in ["1h", "6h", "24h"]:
        key = f"reversion_{horizon}"
        values = [s[key] for s in shocks if s.get(key) is not None]

        if not values:
            print(f"  {horizon}: no data")
            continue

        arr = np.array(values)

        # Histogram bins for the frontend payoff chart
        bin_edges = np.linspace(float(arr.min()) - 0.01, float(arr.max()) + 0.01, 20)
        bin_counts, _ = np.histogram(arr, bins=bin_edges)

        # Percentiles for scenario analysis
        percentiles = {
            "p10": round(float(np.percentile(arr, 10)), 4),
            "p25": round(float(np.percentile(arr, 25)), 4),
            "p50": round(float(np.percentile(arr, 50)), 4),
            "p75": round(float(np.percentile(arr, 75)), 4),
            "p90": round(float(np.percentile(arr, 90)), 4),
        }

        dist_data = {
            f"distribution_{horizon}": {
                "bin_edges": [round(float(x), 4) for x in bin_edges],
                "bin_counts": [int(x) for x in bin_counts],
                "percentiles": percentiles,
                "mean": round(float(arr.mean()), 4),
                "std": round(float(arr.std()), 4),
                "min": round(float(arr.min()), 4),
                "max": round(float(arr.max()), 4),
            }
        }

        db["shock_results"].update_one(
            {"_id": "aggregate_stats"},
            {"$set": dist_data},
            upsert=True,
        )

        print(f"  {horizon}: {len(values)} samples, mean={arr.mean():.4f}, std={arr.std():.4f}")


def compute_backtest() -> None:
    """Compute backtest summary stats (win rate, avg P&L, drawdown) overall and by category."""
    shocks = list(db["shock_events"].find({}))

    backtest: dict = {
        "total_trades": 0,
        "win_rate_1h": None,
        "win_rate_6h": None,
        "win_rate_24h": None,
        "avg_pnl_per_dollar_6h": None,
        "max_drawdown_6h": None,
        "by_category": {},
    }

    # Overall stats per horizon
    for h in ["1h", "6h", "24h"]:
        key = f"reversion_{h}"
        vals = [s[key] for s in shocks if s.get(key) is not None]
        if vals:
            arr = np.array(vals)
            backtest[f"win_rate_{h}"] = round(float(np.mean(arr > 0)), 4)
            if h == "6h":
                backtest["avg_pnl_per_dollar_6h"] = round(float(arr.mean()), 4)
                backtest["max_drawdown_6h"] = round(float(arr.min()), 4)
                backtest["total_trades"] = len(vals)

    # By category
    categories = set(s.get("category") for s in shocks if s.get("category"))
    for cat in categories:
        by_cat: dict = {}
        for h in ["1h", "6h", "24h"]:
            key = f"reversion_{h}"
            cat_vals = [s[key] for s in shocks if s.get("category") == cat and s.get(key) is not None]
            if cat_vals:
                cat_arr = np.array(cat_vals)
                by_cat[f"win_rate_{h}"] = round(float(np.mean(cat_arr > 0)), 4)
                by_cat[f"avg_pnl_{h}"] = round(float(cat_arr.mean()), 4)
                by_cat["sample_size"] = len(cat_vals)
        if by_cat:
            backtest["by_category"][cat] = by_cat

    db["shock_results"].update_one(
        {"_id": "aggregate_stats"},
        {"$set": {"backtest": backtest}},
        upsert=True,
    )

    print("\nBacktest summary:")
    print(f"  Total trades: {backtest['total_trades']}")
    print(f"  6h win rate: {backtest['win_rate_6h']}")
    print(f"  6h avg P&L per $1: {backtest['avg_pnl_per_dollar_6h']}")
    print(f"  6h max drawdown: {backtest['max_drawdown_6h']}")
    if backtest["by_category"]:
        print(f"  Categories: {list(backtest['by_category'].keys())}")


def main() -> None:
    """Run distribution computation and backtest stats."""
    compute_distributions()
    compute_backtest()
    print("\nDone. Distribution + backtest data stored in shock_results.")


if __name__ == "__main__":
    main()
