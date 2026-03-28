"""
Keyword-based market categorization for ShockTest.

Classifies each market title into: politics, sports, crypto,
entertainment, science, or other.

No API keys required — runs instantly.

Usage:
    python analysis/categorize.py
    python analysis/categorize.py --force   # re-categorize all
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.helpers import get_db

VALID_CATEGORIES = {"politics", "sports", "crypto", "entertainment", "science", "other"}

# Keyword lists — checked in priority order (first match wins)
_KEYWORDS: dict[str, list[str]] = {
    "crypto": [
        "bitcoin",
        " btc ",
        "ethereum",
        " eth ",
        "crypto",
        "blockchain",
        "token",
        " coin ",
        "defi",
        "nft",
        "solana",
        " sol ",
        "dogecoin",
        "doge",
        " xrp ",
        "ripple",
        "binance",
        " bnb ",
        "cardano",
        " ada ",
        "avalanche",
        " avax ",
        "polygon",
        " matic ",
        "chainlink",
        " ltc ",
        "stablecoin",
        " usdc ",
        " usdt ",
        "tether",
        "altcoin",
        "memecoin",
        " dao ",
        "web3",
        "layer 2",
        "layer2",
        " l2 ",
        "base chain",
        "arbitrum",
        "optimism",
        "uniswap",
    ],
    "sports": [
        " nfl ",
        " nba ",
        " mlb ",
        " nhl ",
        " mls ",
        " ufc ",
        " f1 ",
        "super bowl",
        "world cup",
        "world series",
        "stanley cup",
        "champions league",
        "premier league",
        "la liga",
        "bundesliga",
        "serie a",
        "ligue 1",
        "playoffs",
        "championship",
        "tournament",
        "grand slam",
        "wimbledon",
        "us open",
        "french open",
        "australian open",
        "masters",
        "pga",
        "soccer",
        "football",
        "basketball",
        "baseball",
        "hockey",
        "tennis",
        "golf",
        "boxing",
        "mma",
        "wrestling",
        "rugby",
        "cricket",
        "cycling",
        "formula 1",
        "formula one",
        "motogp",
        "daytona",
        "kentucky derby",
        " mvp ",
        "quarterback",
        "touchdown",
        "goal",
        "hat trick",
        " vs ",
        " vs. ",
        "match",
        "game 7",
        "series",
        "patriots",
        "lakers",
        "warriors",
        "cowboys",
        "chiefs",
        "eagles",
        "celtics",
        "bucks",
        "nuggets",
        "heat",
        "knicks",
        "nets",
        "suns",
        "yankees",
        "dodgers",
        "astros",
        "mets",
        "cubs",
        "braves",
        "manchester",
        "arsenal",
        "chelsea",
        "liverpool",
        "barcelona",
        "madrid",
        "liverpool",
        "bayern",
        "psg",
        "juventus",
        "inter milan",
        "ac milan",
    ],
    "politics": [
        "trump",
        "biden",
        "harris",
        "obama",
        "clinton",
        "desantis",
        "newsom",
        "pelosi",
        "mcconnell",
        "schumer",
        "musk",
        "zelensky",
        "putin",
        "xi ",
        "modi",
        "macron",
        "scholz",
        "sunak",
        "trudeau",
        "netanyahu",
        "election",
        "vote",
        "ballot",
        "poll",
        "primary",
        "caucus",
        "midterm",
        "senate",
        "congress",
        "house",
        "republican",
        "democrat",
        "gop",
        "white house",
        "oval office",
        "president",
        "vice president",
        "governor",
        "mayor",
        "legislation",
        "bill passes",
        "filibuster",
        "impeach",
        "indicted",
        "conviction",
        "verdict",
        "supreme court",
        "federal reserve",
        "fed rate",
        "interest rate",
        "inflation",
        "ukraine",
        "russia",
        "iran",
        "china",
        "taiwan",
        "north korea",
        "nato",
        "g7",
        "g20",
        "un vote",
        "sanctions",
        "tariff",
        "trade war",
        "israel",
        "gaza",
        "hamas",
        "war",
        "ceasefire",
        "coup",
        "cia",
        "fbi",
        "doj",
        "sec ",
        "fda approval",
        "executive order",
    ],
    "entertainment": [
        "oscar",
        "academy award",
        "emmy",
        "grammy",
        "golden globe",
        "bafta",
        "box office",
        "box-office",
        "movie",
        "film",
        "series finale",
        "album",
        "song",
        "chart",
        "billboard",
        "spotify",
        "streaming",
        "netflix",
        "disney",
        "hbo",
        "prime video",
        "apple tv",
        "taylor swift",
        "beyonce",
        "kanye",
        "drake",
        "rihanna",
        "ariana",
        "celebrity",
        "actor",
        "actress",
        "director",
        "superhero",
        "marvel",
        "dc comics",
        "star wars",
        "avengers",
        "grammy",
        "tour",
        "concert",
        "ticket sales",
        "social media",
        "viral",
        "tiktok",
        "youtube",
        "tweet",
        "instagram",
        "podcast",
        "reality tv",
        "game show",
    ],
    "science": [
        "ai ",
        " ai,",
        "artificial intelligence",
        "machine learning",
        "gpt",
        "chatgpt",
        "openai",
        "anthropic",
        "llm",
        "model release",
        "climate",
        "temperature",
        "emission",
        "carbon",
        "renewable",
        "nasa",
        "spacex",
        "space",
        "rocket",
        "mars",
        "moon",
        "asteroid",
        "vaccine",
        "cancer",
        "fda",
        "drug trial",
        "clinical trial",
        "covid",
        "pandemic",
        "virus",
        "outbreak",
        "quantum",
        "fusion",
        "nuclear",
        "cern",
        "discovery",
        "experiment",
        "research study",
    ],
}


def categorize_market(question: str) -> str:
    """
    Classify a prediction market question by keyword matching.

    Checks each category's keyword list in priority order:
    crypto → sports → politics → entertainment → science → other.

    Args:
        question: The market title/question string.

    Returns:
        One of: politics, sports, crypto, entertainment, science, other.
    """
    # Pad with spaces so boundary-padded tokens (e.g. " eth ") match at start/end
    text = " " + question.lower() + " "

    for category, keywords in _KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category

    return "other"


def categorize_all_markets(force: bool = False) -> None:
    """
    Categorize all uncategorized markets in market_series by keyword matching.

    Updates both market_series (category field) and all matching
    shock_events documents. Runs instantly — no API calls.

    Args:
        force: If True, re-categorize markets that already have a category.
    """
    db = get_db()

    # Only categorize markets that have shock events
    shock_market_ids = set(db["shock_events"].distinct("market_id"))
    base_query: dict = {"market_id": {"$in": list(shock_market_ids)}}
    if not force:
        base_query["category"] = None
    markets = list(db["market_series"].find(base_query, {"market_id": 1, "question": 1}))

    if not markets:
        print("All markets already categorized. Use --force to re-run.")
        return

    print(f"Categorizing {len(markets)} markets...")

    for i, market in enumerate(markets):
        question = market["question"]
        category = categorize_market(question)

        db["market_series"].update_one(
            {"_id": market["_id"]},
            {"$set": {"category": category}},
        )
        db["shock_events"].update_many(
            {"market_id": market["market_id"]},
            {"$set": {"category": category}},
        )

        print(f"  [{i + 1}/{len(markets)}] {category:15s} | {question[:60]}")

    # Print category summary
    print("\nCategory breakdown:")
    pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    for doc in db["shock_events"].aggregate(pipeline):
        print(f"  {doc['_id'] or 'uncategorized':20s}: {doc['count']} shocks")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Categorize shock markets by keyword")
    parser.add_argument("--force", action="store_true", help="Re-categorize already-categorized markets")
    args = parser.parse_args()
    categorize_all_markets(force=args.force)
