"""Flag recent shocks as potentially actionable live signals.

Adds 'is_recent' and 'hours_ago' fields to all shock_events.
Shocks from the last 48h with active markets are flagged — these are
shocks a trader could still act on.
"""

import os
import sys
from datetime import datetime, timezone

from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGODB_URI", "")
if not MONGO_URI:
    print("ERROR: MONGODB_URI not set.")
    sys.exit(1)

db = MongoClient(MONGO_URI)["shocktest"]


def main() -> None:
    """Flag shocks from the last 48 hours as recent/live."""
    now = datetime.now(timezone.utc)
    shocks = list(db["shock_events"].find({}))
    print(f"Flagging recent shocks ({len(shocks)} total)...\n")

    recent_count = 0
    for shock in shocks:
        t2_raw = shock.get("t2", "")
        try:
            t2 = datetime.fromisoformat(t2_raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            # If t2 can't be parsed, mark as not recent
            db["shock_events"].update_one(
                {"_id": shock["_id"]},
                {"$set": {"is_recent": False, "hours_ago": None}},
            )
            continue

        hours_ago = (now - t2).total_seconds() / 3600
        is_recent = hours_ago <= 48

        db["shock_events"].update_one(
            {"_id": shock["_id"]},
            {"$set": {"is_recent": is_recent, "hours_ago": round(hours_ago, 1)}},
        )

        if is_recent:
            recent_count += 1
            delta = shock.get("delta", 0)
            question = shock.get("question", "")[:50]
            print(f"  LIVE: {question}... ({hours_ago:.0f}h ago, delta={delta:+.2f})")

    print(f"\n{recent_count} recent shocks flagged out of {len(shocks)} total")


if __name__ == "__main__":
    main()
