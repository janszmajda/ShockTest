"""Add fade_pnl fields to all shock events.

fade_pnl = reversion value (positive = profit if you faded the shock).
This is a convenience field for the frontend trade simulator.
"""

import os
import sys

from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGODB_URI", "")
if not MONGO_URI:
    print("ERROR: MONGODB_URI not set.")
    sys.exit(1)

db = MongoClient(MONGO_URI)["shocktest"]


def main() -> None:
    """Copy reversion values into fade_pnl fields for all shocks."""
    shocks = list(db["shock_events"].find({}))
    print(f"Adding fade_pnl fields to {len(shocks)} shocks...")

    updated = 0
    for shock in shocks:
        update: dict = {}
        for h in ["1h", "6h", "24h"]:
            rev = shock.get(f"reversion_{h}")
            update[f"fade_pnl_{h}"] = rev  # same value, different semantic name

        db["shock_events"].update_one({"_id": shock["_id"]}, {"$set": update})
        updated += 1

    print(f"Done. Updated {updated} shocks.")


if __name__ == "__main__":
    main()
