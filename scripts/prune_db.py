"""One-shot database prune.

Trims every resolved market's series down to windows around its shocks
(1h before to 24h after each shock_event). Markets with no shocks get an
empty series. Unresolved markets get a rolling-age cap applied.

Run once to free space; ongoing pruning is handled automatically by
live_monitor.py (mark_resolved_markets + cap_live_series).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

from pymongo import MongoClient

from live_monitor import (
    cap_live_series,
    prune_series_to_shock_windows,
)

MONGO_URI = os.environ.get("MONGODB_URI", "")
if not MONGO_URI:
    print("ERROR: MONGODB_URI not set.")
    sys.exit(1)

db = MongoClient(MONGO_URI)["shocktest"]


def run() -> None:
    resolved = list(
        db["market_series"].find(
            {"resolved": True}, {"market_id": 1}
        )
    )
    total = len(resolved)
    print(f"Pruning {total} resolved markets...")

    for i, m in enumerate(resolved, 1):
        prune_series_to_shock_windows(m["market_id"], m["_id"])
        if i % 200 == 0:
            print(f"  ..{i}/{total}")

    print(f"Applying rolling cap to live markets...")
    capped = cap_live_series()
    print(f"  capped series on {capped} live markets")

    stats = db.command("dbStats")
    MB = 1024 * 1024
    print(
        f"\nAfter prune: storage={stats['storageSize'] / MB:.1f}MB  "
        f"data={stats['dataSize'] / MB:.1f}MB  "
        f"indexes={stats['indexSize'] / MB:.1f}MB"
    )


if __name__ == "__main__":
    run()
