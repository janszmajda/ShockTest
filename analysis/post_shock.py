"""
Post-shock outcome computation for ShockTest.

For each detected shock, measures what happens at horizons 1h, 6h, 24h.
Computes post_move and reversion, then updates shock_events in MongoDB.

Usage:
    python analysis/post_shock.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from analysis.helpers import get_db, interpolate_price_at, load_market_series

HORIZONS_HOURS = [1, 6, 24]


def compute_post_shock_outcomes(shock: dict) -> dict:
    """
    For a detected shock, measure price at 1h, 6h, 24h after the shock peak.

    Reversion is defined as: -sign(delta) * post_move
    Positive reversion = price moved back toward pre-shock level.
    Negative reversion = price continued in shock direction.

    Args:
        shock: dict from shock_events with keys: market_id, t2, p_after, delta.

    Returns:
        dict with post_move_Xh and reversion_Xh for each horizon.
        Values are None if no data within 30 min of the target time.
    """
    try:
        df = load_market_series(shock["market_id"])
    except ValueError:
        return {}

    if df.empty:
        return {}

    t2 = pd.Timestamp(shock["t2"])
    p_at_shock = float(shock["p_after"])
    shock_direction = float(np.sign(shock["delta"]))

    results = {}
    for h in HORIZONS_HOURS:
        target_time = t2 + pd.Timedelta(hours=h)

        # Use linear interpolation for precision
        p_later = interpolate_price_at(df, target_time)

        # Fall back to nearest point if target is out of range
        if p_later is None:
            time_diffs = (df["t"] - target_time).abs()
            closest_idx = time_diffs.idxmin()
            closest_time = df.loc[closest_idx, "t"]
            # Only use if within 90 min of target (generous for sparse data)
            if abs((closest_time - target_time).total_seconds()) > 5400:
                results[f"post_move_{h}h"] = None
                results[f"reversion_{h}h"] = None
                continue
            p_later = float(df.loc[closest_idx, "p"])

        post_move = p_later - p_at_shock
        reversion = -shock_direction * post_move

        results[f"post_move_{h}h"] = round(post_move, 4)
        results[f"reversion_{h}h"] = round(reversion, 4)

    return results


def run_all_post_shock_analysis() -> int:
    """
    Compute post-shock outcomes for all shocks in shock_events and update MongoDB.

    Returns:
        Number of shocks successfully updated.
    """
    db = get_db()
    shocks = list(db["shock_events"].find({}))
    print(f"Computing post-shock outcomes for {len(shocks)} shocks...")

    updated = 0
    for i, shock in enumerate(shocks):
        outcomes = compute_post_shock_outcomes(shock)
        if not outcomes:
            continue

        db["shock_events"].update_one(
            {"_id": shock["_id"]},
            {"$set": outcomes},
        )
        updated += 1

        if (i + 1) % 100 == 0:
            rev_6h = outcomes.get("reversion_6h")
            rev_str = f"{rev_6h:+.4f}" if rev_6h is not None else "N/A"
            print(f"  [{i + 1}/{len(shocks)}] reversion_6h={rev_str}")

    print(f"Done — updated {updated}/{len(shocks)} shocks.")
    return updated


if __name__ == "__main__":
    run_all_post_shock_analysis()
