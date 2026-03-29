"""
K2-powered market categorization for ShockTest.

Classifies each market title into one of 12 categories using
the MBZUAI K2-Think-v2 model, with keyword matching as fallback.

Usage:
    python analysis/categorize.py
    python analysis/categorize.py --force   # re-categorize all
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.helpers import get_db

K2_API_URL = "https://api.k2think.ai/v1/chat/completions"
K2_MODEL = "MBZUAI-IFM/K2-Think-v2"
K2_API_KEY = os.environ.get("K2_API_KEY", "")

VALID_CATEGORIES = {
    "politics", "elections", "geopolitics", "sports", "esports",
    "crypto", "finance", "tech", "science", "culture",
    "weather", "other",
}

# Keyword lists — checked in priority order (first match wins).
# Sports/esports MUST come before geopolitics/politics because sports titles
# frequently contain player/country names that would false-positive
# (e.g. "Israel Adesanya" matching geopolitics "israel").
_KEYWORDS: dict[str, list[str]] = {
    # --- 1. Esports (most specific, fewest false positives) ---
    "esports": [
        " lol ",
        "league of legends",
        "dota",
        "valorant",
        "counter-strike",
        " csgo ",
        " cs2 ",
        "overwatch",
        "fortnite",
        "apex legends",
        " lec ",
        " lck ",
        " lpl ",
        " vct ",
        " esl ",
        " iem ",
        "esport",
        "e-sport",
        " bo3 ",
        " bo5 ",
        "natus vincere",
        " navi ",
        "fnatic",
        "g2 esports",
        "t1 ",
        "cloud9",
        "team liquid",
        "faze clan",
    ],
    # --- 2. Sports (before geopolitics/politics to avoid false positives) ---
    "sports": [
        # Leagues
        " nfl ",
        " nba ",
        " mlb ",
        " nhl ",
        " mls ",
        " ufc ",
        " f1 ",
        " afl ",
        " ipl ",
        " wwe ",
        " wnba ",
        " ncaa ",
        # Tournaments / events
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
        "grand slam",
        "wimbledon",
        "us open",
        "french open",
        "australian open",
        "pga",
        "copa ",
        "kentucky derby",
        "march madness",
        "all-star game",
        # UFC / MMA / combat sports
        "fight night",
        "main card",
        "main event",
        "undercard",
        "octagon",
        "submission",
        "knockout",
        " ko ",
        " tko ",
        "split decision",
        "unanimous decision",
        "title fight",
        "title bout",
        " bout ",
        "bellator",
        " pfl ",
        "one championship",
        "lightweight",
        "heavyweight",
        "middleweight",
        "welterweight",
        "featherweight",
        "bantamweight",
        "flyweight",
        "pound for pound",
        " mma",
        "boxing",
        "wrestling",
        # Betting patterns (strong sports signal)
        " o/u ",
        "over/under",
        "spread:",
        "spread ",
        "moneyline",
        "point spread",
        " -1.5 ",
        " +1.5 ",
        " -2.5 ",
        " +2.5 ",
        " -3.5 ",
        " +3.5 ",
        " -4.5 ",
        " +4.5 ",
        " -5.5 ",
        " +5.5 ",
        " -6.5 ",
        " +6.5 ",
        " -7.5 ",
        " +7.5 ",
        " vs. ",
        " vs ",
        # Sports (generic terms)
        "soccer",
        "football",
        "basketball",
        "baseball",
        "hockey",
        "tennis",
        "golf",
        "rugby",
        "cricket",
        "cycling",
        "formula 1",
        "motogp",
        "quarterback",
        "touchdown",
        "hat trick",
        "home run",
        "strikeout",
        "three-pointer",
        "free throw",
        "penalty kick",
        # NBA teams
        "lakers",
        "warriors",
        "celtics",
        "bucks",
        "nuggets",
        "knicks",
        "nets",
        "suns",
        "76ers",
        "cavaliers",
        "pacers",
        "hawks",
        "raptors",
        "pistons",
        "wizards",
        "hornets",
        "magic",
        "timberwolves",
        "pelicans",
        "thunder",
        "blazers",
        "spurs",
        "kings",
        "clippers",
        "wolves",
        "bulls",
        "grizzlies",
        "heat",
        "rockets",
        # NFL teams
        "patriots",
        "cowboys",
        "chiefs",
        "eagles",
        "packers",
        "steelers",
        "49ers",
        "seahawks",
        "ravens",
        "bills",
        "dolphins",
        "bengals",
        "lions",
        "vikings",
        "saints",
        "buccaneers",
        "chargers",
        "broncos",
        "colts",
        "texans",
        "titans",
        "jaguars",
        "commanders",
        "bears",
        "falcons",
        "panthers",
        "rams",
        "cardinals",
        # MLB teams
        "yankees",
        "dodgers",
        "astros",
        "mets",
        "cubs",
        "braves",
        "red sox",
        "blue jays",
        "phillies",
        "reds",
        "rangers",
        "athletics",
        "angels",
        "padres",
        "royals",
        "orioles",
        "guardians",
        "nationals",
        "marlins",
        "rockies",
        "diamondbacks",
        "brewers",
        "pirates",
        "twins",
        "tigers",
        "white sox",
        "rays",
        "mariners",
        # NHL teams
        "flyers",
        "red wings",
        "penguins",
        "bruins",
        "canadiens",
        "hurricanes",
        "devils",
        "islanders",
        "oilers",
        "flames",
        "canucks",
        "jets",
        "senators",
        "predators",
        "blue jackets",
        "blackhawks",
        "kraken",
        "wild",
        "avalanche",
        "stars",
        "ducks",
        "sharks",
        "sabres",
        "capitals",
        "lightning",
        "maple leafs",
        "golden knights",
        # College / other
        "illini",
        "hawkeyes",
        "fighting ",
        "pigossi",
        "zavatska",
        "colsanitas",
    ],
    # --- 3. Weather ---
    "weather": [
        "hurricane",
        "tornado",
        "earthquake",
        "wildfire",
        "flood",
        "drought",
        "heat wave",
        "heatwave",
        "cold snap",
        "snowfall",
        "blizzard",
        "cyclone",
        "typhoon",
        "storm",
        "rainfall",
        "temperature record",
        "hottest",
        "coldest",
        "category 5",
        "el nino",
        "la nina",
        "weather",
        "noaa",
    ],
    # --- 4. Crypto ---
    "crypto": [
        "bitcoin",
        " btc ",
        "ethereum",
        " eth ",
        "crypto",
        "blockchain",
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
        " token ",
        " coin ",
    ],
    # --- 5. Finance ---
    "finance": [
        "stock",
        "s&p 500",
        " s&p ",
        "nasdaq",
        "dow jones",
        " spy ",
        " qqq ",
        "treasury",
        "bond yield",
        "yield curve",
        " ipo ",
        "earnings",
        "revenue",
        "market cap",
        "share price",
        "bull market",
        "bear market",
        "recession",
        "gdp ",
        " cpi ",
        "unemployment",
        "jobs report",
        "nonfarm",
        "payroll",
        "forex",
        " usd ",
        " eur ",
        "gold price",
        "oil price",
        "crude oil",
        " wti ",
        "brent",
        "commodity",
        "hedge fund",
        "wall street",
        "berkshire",
        "federal reserve",
        "fed rate",
        "interest rate",
        "rate cut",
        "rate hike",
        "inflation",
        "deflation",
        "bank of america",
        "jpmorgan",
        "goldman",
        "citadel",
    ],
    # --- 6. Elections ---
    "elections": [
        "election",
        "ballot",
        "primary",
        "caucus",
        "midterm",
        "runoff",
        "electoral college",
        "electoral vote",
        "swing state",
        "will win the",
        "nominee",
        "nomination",
        "presidential race",
        "senate race",
        "gubernatorial",
        "house seat",
        "redistrict",
        "gerrymandering",
        "voter turnout",
        "polling",
        "approval rating",
    ],
    # --- 7. Geopolitics (AFTER sports — tightened keywords) ---
    "geopolitics": [
        "ukraine",
        "russia",
        "iran",
        "gaza",
        "hamas",
        "hezbollah",
        "israel-",
        "israeli",
        "yemen",
        "houthi",
        "taiwan strait",
        "south china sea",
        "north korea",
        " nato ",
        "ceasefire",
        "invasion",
        " coup ",
        "sanctions",
        "tariff",
        "trade war",
        "missile",
        "airstrike",
        "air strike",
        "nuclear weapon",
        "peace deal",
        "peace agreement",
        "un resolution",
        "un vote",
        "security council",
        "g7 ",
        "g20",
        "diplomatic",
        "embassy",
        "refugee",
        "annex",
        "occupation",
        "border conflict",
        "military operation",
        "military action",
        " war in ",
        " war on ",
        " war with ",
        "armed conflict",
    ],
    # --- 8. Politics ---
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
        "zelensky",
        "putin",
        "xi jinping",
        "modi",
        "macron",
        "scholz",
        "sunak",
        "trudeau",
        "netanyahu",
        "vote",
        "senate",
        "congress",
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
        "executive order",
        "cia",
        "fbi",
        "doj",
        "sec ",
        "policy",
        "partisan",
        "bipartisan",
    ],
    # --- 9. Tech ---
    "tech": [
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
        "apple",
        "google",
        "microsoft",
        "amazon",
        "meta ",
        "nvidia",
        "tesla",
        "spacex",
        "startup",
        "silicon valley",
        "semiconductor",
        "chip",
        "quantum computing",
        "autonomous",
        "self-driving",
        "robot",
        "iphone",
        "android",
        "software",
        "app store",
        "cloud computing",
        "data center",
        "cybersecurity",
        "hack ",
        "breach",
        "encryption",
    ],
    # --- 10. Science ---
    "science": [
        "nasa",
        "space",
        "rocket",
        "mars",
        "moon landing",
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
        "climate",
        "emission",
        "carbon",
        "renewable",
        "species",
        "genome",
        "crispr",
    ],
    # --- 11. Culture ---
    "culture": [
        "oscar",
        "academy award",
        "emmy",
        "grammy",
        "golden globe",
        "box office",
        "movie",
        "film",
        "album",
        "song",
        "billboard",
        "spotify",
        "streaming",
        "netflix",
        "disney",
        "hbo",
        "taylor swift",
        "beyonce",
        "kanye",
        "drake",
        "celebrity",
        "viral",
        "tiktok",
        "youtube",
        "instagram",
        "podcast",
        "reality tv",
        "concert",
        "tour",
        "social media",
        "influencer",
        "meme",
        "trending",
    ],
}


def _categorize_keyword(question: str) -> str:
    """Fallback: classify by keyword matching."""
    text = " " + question.lower() + " "
    for category, keywords in _KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return "other"


def _categorize_k2_batch(questions: list[str]) -> list[str]:
    """
    Classify a batch of market questions using K2-Think-v2.

    Sends all questions in one prompt and parses the JSON array response.
    Falls back to keyword matching for any that fail.
    """
    categories_str = ", ".join(sorted(VALID_CATEGORIES))
    prompt = (
        "You are a prediction market categorizer. For each market question below, "
        f"respond with ONLY a JSON array of categories. Valid categories: {categories_str}.\n\n"
        "Rules:\n"
        "- Return exactly one category per question\n"
        "- Output ONLY the JSON array, no other text\n"
        "- Example: [\"politics\", \"sports\", \"crypto\"]\n\n"
        "Questions:\n"
    )
    for i, q in enumerate(questions):
        prompt += f"{i + 1}. {q}\n"

    try:
        resp = requests.post(
            K2_API_URL,
            headers={
                "Authorization": f"Bearer {K2_API_KEY}",
                "Content-Type": "application/json",
                "accept": "application/json",
            },
            json={
                "model": K2_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Extract JSON array from response (may have thinking tags or extra text)
        # Find the first [ and last ]
        start = content.find("[")
        end = content.rfind("]")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON array found in response: {content[:200]}")
        categories = json.loads(content[start:end + 1])

        # Validate and map results
        results = []
        for i, cat in enumerate(categories):
            cat_lower = cat.strip().lower()
            if cat_lower in VALID_CATEGORIES:
                results.append(cat_lower)
            else:
                results.append(_categorize_keyword(questions[i]))

        # If K2 returned fewer results than questions, fill with keyword fallback
        while len(results) < len(questions):
            results.append(_categorize_keyword(questions[len(results)]))

        return results

    except Exception as e:
        print(f"  K2 API error: {e} — falling back to keyword matching for batch")
        return [_categorize_keyword(q) for q in questions]


def categorize_market(question: str) -> str:
    """
    Classify a prediction market question using K2-Think-v2 model.

    Falls back to keyword matching if the API call fails.

    Args:
        question: The market title/question string.

    Returns:
        One of the VALID_CATEGORIES.
    """
    results = _categorize_k2_batch([question])
    return results[0]


def categorize_all_markets(force: bool = False) -> None:
    """
    Categorize markets that have shock events.

    Uses the API-provided category (from Polymarket tags) when available,
    falling back to keyword matching. Updates both market_series and all
    matching shock_events documents.

    Args:
        force: If True, re-categorize markets that already have a category.
    """
    db = get_db()

    # Only categorize markets that have shock events
    shock_market_ids = set(db["shock_events"].distinct("market_id"))
    base_query: dict = {"market_id": {"$in": list(shock_market_ids)}}
    if not force:
        base_query["category"] = None
    markets = list(db["market_series"].find(base_query, {"market_id": 1, "question": 1, "category": 1}))

    if not markets:
        print("All markets already categorized. Use --force to re-run.")
        return

    # Split into markets with API categories and those needing K2
    needs_k2 = []
    has_api_cat = []
    for market in markets:
        api_cat = market.get("category")
        if api_cat and api_cat in VALID_CATEGORIES and not force:
            has_api_cat.append((market, api_cat))
        else:
            needs_k2.append(market)

    total = len(markets)
    done = 0

    # Apply API-provided categories first
    for market, category in has_api_cat:
        db["market_series"].update_one(
            {"_id": market["_id"]},
            {"$set": {"category": category}},
        )
        db["shock_events"].update_many(
            {"market_id": market["market_id"]},
            {"$set": {"category": category}},
        )
        done += 1
        print(f"  [{done}/{total}] {category:15s} | {market['question'][:60]}  (API tag)")

    # Batch K2 calls (10 at a time to stay within token limits)
    BATCH_SIZE = 10
    print(f"\nCategorizing {len(needs_k2)} markets via K2-Think-v2...")

    for batch_start in range(0, len(needs_k2), BATCH_SIZE):
        batch = needs_k2[batch_start:batch_start + BATCH_SIZE]
        questions = [m["question"] for m in batch]
        categories = _categorize_k2_batch(questions)

        for market, category in zip(batch, categories):
            db["market_series"].update_one(
                {"_id": market["_id"]},
                {"$set": {"category": category}},
            )
            db["shock_events"].update_many(
                {"market_id": market["market_id"]},
                {"$set": {"category": category}},
            )
            done += 1
            print(f"  [{done}/{total}] {category:15s} | {market['question'][:60]}")

        # Small delay between batches to be polite to the API
        if batch_start + BATCH_SIZE < len(needs_k2):
            time.sleep(1)

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
