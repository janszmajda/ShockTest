"""
Manual verification of detected shocks — Hour 6-10.

Prints price context around the top 5 largest shocks so you can
confirm they represent real market moves, not data artifacts.

Usage:
    python analysis/verify_shocks.py
    python analysis/verify_shocks.py --n 10         # show top 10
    python analysis/verify_shocks.py --theta 0.15   # only large shocks
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from analysis.helpers import get_db, load_market_series


def verify_shocks(n: int = 5, theta: float = 0.0) -> None:
    """
    Print price context around the top N shocks by abs_delta.

    Args:
        n:     Number of shocks to inspect.
        theta: Optional minimum abs_delta filter (0 = no filter).
    """
    db = get_db()

    query = {"abs_delta": {"$gte": theta}} if theta > 0 else {}
    shocks = list(db["shock_events"].find(query).sort("abs_delta", -1).limit(n))

    if not shocks:
        print("No shocks found in shock_events. Run shock_detector.py first.")
        return

    print(f"Top {len(shocks)} shocks by magnitude (theta>={theta}):\n")

    for i, shock in enumerate(shocks, 1):
        print("=" * 65)
        print(f"[{i}] {shock.get('question', shock['market_id'])[:60]}")
        print(f"     source={shock.get('source', '?')}  market_id={shock['market_id']}")
        print(f"     {shock['t1']} -> {shock['t2']}")
        print(
            f"     p: {shock['p_before']:.3f} -> {shock['p_after']:.3f}  delta={shock['delta']:+.3f}  abs={shock['abs_delta']:.3f}"
        )

        # Load full series and show ±2h context around shock peak
        try:
            df = load_market_series(shock["market_id"])
        except ValueError:
            print("     [series not found in MongoDB]")
            continue

        t2 = pd.Timestamp(shock["t2"])
        window = df[(df["t"] >= t2 - pd.Timedelta(hours=2)) & (df["t"] <= t2 + pd.Timedelta(hours=2))]

        if window.empty:
            print("     [no data in +-2h window]")
            continue

        print(f"\n     Price context (+-2h around shock peak, {len(window)} points):")
        for _, row in window.iterrows():
            secs_from_shock = (row["t"] - t2).total_seconds()
            marker = " <<< SHOCK" if abs(secs_from_shock) <= 60 else ""
            print(f"       {row['t'].strftime('%m-%d %H:%M')}  p={row['p']:.4f}{marker}")

        print()

    # Summary
    total = db["shock_events"].count_documents({})
    print("=" * 65)
    print(f"Total shocks in shock_events: {total}")
    print()
    print("Checklist:")
    print("  [ ] Do the price moves look like real market reactions?")
    print("  [ ] Any shocks that are just market resolution (p -> 0 or 1)?")
    print("  [ ] Any obvious data gaps causing false positives?")
    print()
    print("If you see too many resolution artifacts, re-run detection with:")
    print("  from analysis.shock_detector import run_detection")
    print("  run_detection(theta=0.08)  # artifacts usually have abs_delta near 1.0")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify top detected shocks")
    parser.add_argument("--n", type=int, default=5, help="Number of shocks to inspect")
    parser.add_argument("--theta", type=float, default=0.0, help="Min abs_delta filter")
    args = parser.parse_args()
    verify_shocks(n=args.n, theta=args.theta)
