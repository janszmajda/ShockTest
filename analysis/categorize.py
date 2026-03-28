"""
Gemini-powered market categorization for ShockTest.

Classifies each market title into: politics, sports, crypto,
entertainment, science, or other.

Requires GEMINI_API_KEY in .env
Free tier: 10 RPM, 250 req/day — sufficient for 231 markets.

Usage:
    python analysis/categorize.py
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from google import genai

from analysis.helpers import get_db

load_dotenv()

VALID_CATEGORIES = {"politics", "sports", "crypto", "entertainment", "science", "other"}
REQUESTS_PER_MINUTE = 10
SLEEP_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE  # 6 seconds


def get_client() -> genai.Client:
    """Configure and return the Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not set — add it to .env")
    return genai.Client(api_key=api_key)


def categorize_market(question: str, client: genai.Client) -> str:
    """
    Classify a single market question using Gemini.

    Args:
        question: The market title/question string.
        client:   Configured Gemini Client instance.

    Returns:
        One of: politics, sports, crypto, entertainment, science, other.
        Falls back to "other" on any error.
    """
    prompt = (
        "Classify this prediction market into exactly one category: "
        "politics, sports, crypto, entertainment, science, or other. "
        f"Market: '{question}'. "
        "Respond with only the category name in lowercase, nothing else."
    )

    try:
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        category = resp.text.strip().lower()
        return category if category in VALID_CATEGORIES else "other"
    except Exception as e:
        print(f"  Gemini error: {e}")
        return "other"


def categorize_all_markets(force: bool = False) -> None:
    """
    Categorize all uncategorized markets in market_series using Gemini.

    Updates both market_series (category field) and all matching
    shock_events documents.

    Args:
        force: If True, re-categorize markets that already have a category.
    """
    db = get_db()
    query = {} if force else {"category": None}
    markets = list(db["market_series"].find(query, {"market_id": 1, "question": 1}))

    if not markets:
        print("All markets already categorized. Use force=True to re-run.")
        return

    print(f"Categorizing {len(markets)} markets with Gemini (~{len(markets) * SLEEP_BETWEEN_REQUESTS / 60:.1f} min)...")
    client = get_client()

    for i, market in enumerate(markets):
        question = market["question"]
        category = categorize_market(question, client)

        db["market_series"].update_one(
            {"_id": market["_id"]},
            {"$set": {"category": category}},
        )
        db["shock_events"].update_many(
            {"market_id": market["market_id"]},
            {"$set": {"category": category}},
        )

        print(f"  [{i + 1}/{len(markets)}] {category:15s} | {question[:60]}")

        if i < len(markets) - 1:
            time.sleep(SLEEP_BETWEEN_REQUESTS)

    # Print category summary
    print("\nCategory breakdown:")
    pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    for doc in db["market_series"].aggregate(pipeline):
        print(f"  {doc['_id'] or 'uncategorized':20s}: {doc['count']} markets")


if __name__ == "__main__":
    categorize_all_markets()
