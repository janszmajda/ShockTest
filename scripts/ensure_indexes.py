"""Create MongoDB indexes for fast shock queries.

Run once:  python scripts/ensure_indexes.py
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING

uri = os.environ.get("MONGODB_URI")
if not uri:
    raise SystemExit("Set MONGODB_URI first")

db = MongoClient(uri)["shocktest"]

# shock_events — covers the similar-stats filter fields + sort
db.shock_events.create_index(
    [("category", ASCENDING), ("abs_delta", ASCENDING), ("delta", ASCENDING)],
    name="idx_similar_filter",
)
db.shock_events.create_index(
    [("abs_delta", DESCENDING)],
    name="idx_abs_delta_desc",
)

# market_series — covers dashboard list + single-market lookup
db.market_series.create_index(
    [("market_id", ASCENDING)],
    name="idx_market_id",
    unique=True,
)

print("Indexes created ✓")
for coll_name in ["shock_events", "market_series"]:
    for idx in db[coll_name].list_indexes():
        print(f"  {coll_name}.{idx['name']}")
