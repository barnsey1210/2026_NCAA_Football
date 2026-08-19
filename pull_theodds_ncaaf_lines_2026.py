#!/usr/bin/env python3
"""Pull current 2026 NCAAF odds from The Odds API.

Daily production role:
- Uses THE_ODDS_API_KEY (the 500-credit daily key loaded by the daily environment).
- Requests the 10 priority venues in one current-odds request.
- Preserves the raw provider response.
- Writes a normalized quote CSV plus explicit requested/returned coverage auditing.

Fast/Command Center ingestion should use the same venue universe and normalization
contract, but a separate THE_ODDS_API_KEY_FAST credential and fast worker.
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from time import perf_counter
from pathlib import Path

import pandas as pd
import requests


PROFILE = os.environ.get("NCAAF_THEODDS_PROFILE", "daily").strip().lower()

if PROFILE == "daily":
    KEY_ENV = "THE_ODDS_API_KEY"
    DEFAULT_MARKETS = "h2h,spreads,totals"
    OUT_DIR = Path("data/odds")
    ARCHIVE_DIR = OUT_DIR / "theodds_raw_archive"
    AUDIT_DIR = Path("data/audits")
    FILE_SUFFIX = ""

elif PROFILE == "command_center":
    KEY_ENV = "THE_ODDS_API_KEY_FAST"
    DEFAULT_MARKETS = "spreads,totals"
    OUT_DIR = Path("data/war_room/odds")
    ARCHIVE_DIR = OUT_DIR / "raw_archive"
    AUDIT_DIR = Path("data/war_room/audits")
    FILE_SUFFIX = "_fast"

else:
    raise SystemExit(
        f"Unsupported NCAAF_THEODDS_PROFILE={PROFILE!r}; "
        "expected daily or command_center."
    )

API_KEY = os.environ.get(KEY_ENV)
if not API_KEY:
    raise SystemExit(f"Missing {KEY_ENV} environment variable.")
for directory in (OUT_DIR, ARCHIVE_DIR, AUDIT_DIR):
    directory.mkdir(parents=True, exist_ok=True)

SPORT = "americanfootball_ncaaf"

# Canonical 10-venue production universe.
# The Odds API keys verified against the provider's current bookmaker registry.
PRIORITY_VENUES = [
    {"key": "pinnacle",       "name": "Pinnacle",      "venue_type": "sharp_reference"},
    {"key": "novig",          "name": "Novig",         "venue_type": "exchange"},
    {"key": "prophetx",       "name": "ProphetX",      "venue_type": "exchange"},
    {"key": "kalshi",         "name": "Kalshi",        "venue_type": "exchange"},
    {"key": "draftkings",     "name": "DraftKings",    "venue_type": "sportsbook"},
    {"key": "fanduel",        "name": "FanDuel",       "venue_type": "sportsbook"},
    {"key": "betmgm",         "name": "BetMGM",        "venue_type": "sportsbook"},
    {"key": "williamhill_us", "name": "Caesars",       "venue_type": "sportsbook"},
    {"key": "betrivers",      "name": "BetRivers",     "venue_type": "sportsbook"},
    {"key": "hardrockbet",    "name": "Hard Rock Bet", "venue_type": "sportsbook"},
]

BOOKMAKERS = [row["key"] for row in PRIORITY_VENUES]
VENUE_BY_KEY = {row["key"]: row for row in PRIORITY_VENUES}

# Defensive aliases for provider variants we have seen / may see.
BOOK_KEY_ALIASES = {
    "hardrockbet_oh": "hardrockbet",
    "hardrockbet_az": "hardrockbet",
    "hardrockbet_fl": "hardrockbet",
}
MARKETS = [
    x.strip()
    for x in os.environ.get(
        "NCAAF_THEODDS_MARKETS",
        DEFAULT_MARKETS,
    ).split(",")
    if x.strip()
]

ALLOWED_MARKETS = {"h2h", "spreads", "totals"}

unknown_markets = set(MARKETS) - ALLOWED_MARKETS
if unknown_markets:
    raise SystemExit(
        f"Unsupported The Odds API markets: {sorted(unknown_markets)}"
    )

if PROFILE == "command_center":
    if set(MARKETS) != {"spreads", "totals"}:
        raise SystemExit(
            "Command Center The Odds API profile is restricted to "
            "spreads,totals only. No API request was made."
        )


def canonical_book_key(value):
    key = str(value or "").strip().lower()
    return BOOK_KEY_ALIASES.get(key, key)


def venue_metadata(book):
    provider_key = str(book.get("key") or "").strip().lower()
    canonical_key = canonical_book_key(provider_key)
    configured = VENUE_BY_KEY.get(canonical_key)

    if configured:
        return {
            "book_key": canonical_key,
            "provider_book_key": provider_key,
            "book": configured["name"],
            "venue_type": configured["venue_type"],
            "priority_venue": True,
        }

    # Preserve unexpected returned venues instead of silently dropping them.
    return {
        "book_key": canonical_key or provider_key,
        "provider_book_key": provider_key,
        "book": book.get("title") or canonical_key or provider_key,
        "venue_type": "unclassified",
        "priority_venue": False,
    }


url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
params = {
    "apiKey": API_KEY,
    "bookmakers": ",".join(BOOKMAKERS),
    "markets": ",".join(MARKETS),
    "oddsFormat": "american",
    "dateFormat": "iso",
}

request_started_at = datetime.now(timezone.utc)
request_started_perf = perf_counter()

resp = requests.get(url, params=params, timeout=45)

response_received_perf = perf_counter()
response_received_at = datetime.now(timezone.utc)

http_latency_ms = round(
    (response_received_perf - request_started_perf) * 1000,
    1,
)

now = response_received_at
pulled_at = now.isoformat()

quota = {
    "pulled_at": pulled_at,
    "profile": PROFILE,
    "requested_markets": MARKETS,
    "request_started_at": request_started_at.isoformat(),
    "response_received_at": response_received_at.isoformat(),
    "http_latency_ms": http_latency_ms,
    "http_status": resp.status_code,
    "x_requests_last": resp.headers.get("x-requests-last"),
    "x_requests_used": resp.headers.get("x-requests-used"),
    "x_requests_remaining": resp.headers.get("x-requests-remaining"),
    "sport": SPORT,
    "requested_bookmakers": BOOKMAKERS,
    "requested_markets": MARKETS,
}
quota_path = AUDIT_DIR / f"theodds_api_quota_status{FILE_SUFFIX}.json"
quota_path.write_text(json.dumps(quota, indent=2) + "\n", encoding="utf-8")

print("Status:", resp.status_code)
print("x-requests-used:", quota["x_requests_used"])
print("x-requests-remaining:", quota["x_requests_remaining"])
print("x-requests-last:", quota["x_requests_last"])
print("wrote:", quota_path)

if resp.status_code != 200:
    print(resp.text[:2000])
    raise SystemExit(1)

data = resp.json()
if not isinstance(data, list):
    raise SystemExit(f"Unexpected response type: {type(data).__name__}")

stamp = now.strftime("%Y%m%dT%H%M%SZ")
archive_path = ARCHIVE_DIR / f"theodds_ncaaf_{stamp}.json"
raw_path = OUT_DIR / f"theodds_ncaaf_lines_2026_raw{FILE_SUFFIX}.json"

archive_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
raw_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

rows = []
events_by_book = defaultdict(set)
markets_by_book = Counter()
rows_by_book = Counter()
returned_provider_keys = set()

for game in data:
    provider_event_id = game.get("id")

    for book in game.get("bookmakers", []) or []:
        meta = venue_metadata(book)
        provider_key = meta["provider_book_key"]
        canonical_key = meta["book_key"]

        if provider_key:
            returned_provider_keys.add(provider_key)
        events_by_book[canonical_key].add(provider_event_id)

        for market in book.get("markets", []) or []:
            market_key = market.get("key")
            if market_key not in {"h2h", "spreads", "totals"}:
                continue

            markets_by_book[(canonical_key, market_key)] += 1
            market_last_update = market.get("last_update") or book.get("last_update")

            for outcome in market.get("outcomes", []) or []:
                rows.append(
                    {
                        "pulled_at": pulled_at,
                        "source": "The Odds API",
                        "game_id": provider_event_id,
                        "commence_time": game.get("commence_time"),
                        "away_team": game.get("away_team"),
                        "home_team": game.get("home_team"),
                        "book_key": canonical_key,
                        "provider_book_key": provider_key,
                        "book": meta["book"],
                        "venue_type": meta["venue_type"],
                        "priority_venue": meta["priority_venue"],
                        "market": market_key,
                        "side": outcome.get("name"),
                        "point": outcome.get("point"),
                        "price": outcome.get("price"),
                        "last_update": market_last_update,
                    }
                )
                rows_by_book[canonical_key] += 1

columns = [
    "pulled_at",
    "source",
    "game_id",
    "commence_time",
    "away_team",
    "home_team",
    "book_key",
    "provider_book_key",
    "book",
    "venue_type",
    "priority_venue",
    "market",
    "side",
    "point",
    "price",
    "last_update",
]
df = pd.DataFrame(rows, columns=columns)

csv_path = OUT_DIR / f"theodds_ncaaf_lines_2026{FILE_SUFFIX}.csv"
df.to_csv(csv_path, index=False)

coverage = []
for configured in PRIORITY_VENUES:
    key = configured["key"]
    coverage.append(
        {
            "book_key": key,
            "book": configured["name"],
            "venue_type": configured["venue_type"],
            "requested": True,
            "returned": bool(events_by_book.get(key)),
            "events_returned": len(events_by_book.get(key, set())),
            "normalized_rows": int(rows_by_book.get(key, 0)),
            "market_event_counts": {
                market: int(markets_by_book.get((key, market), 0))
                for market in MARKETS
            },
        }
    )

coverage_path = AUDIT_DIR / f"theodds_ncaaf_book_coverage{FILE_SUFFIX}.json"
coverage_path.write_text(
    json.dumps(
        {
            "pulled_at": pulled_at,
            "sport": SPORT,
            "events_returned": len(data),
            "requested_priority_venues": PRIORITY_VENUES,
            "coverage": coverage,
            "missing_requested_venues": [
                row["book"]
                for row in coverage
                if not row["returned"]
            ],
            "unexpected_provider_book_keys": sorted(
                key
                for key in returned_provider_keys
                if canonical_book_key(key) not in VENUE_BY_KEY
            ),
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

audit = dict(quota)
audit.update(
    {
        "events_returned": len(data),
        "normalized_rows": int(len(df)),
        "priority_venues_requested": len(PRIORITY_VENUES),
        "priority_venues_returned": sum(1 for row in coverage if row["returned"]),
        "missing_requested_venues": [
            row["book"] for row in coverage if not row["returned"]
        ],
        "raw_archive": str(archive_path),
        "compatibility_raw": str(raw_path),
        "normalized_csv": str(csv_path),
        "book_coverage_audit": str(coverage_path),
    }
)
audit_path = AUDIT_DIR / f"theodds_ncaaf_current_pull_audit{FILE_SUFFIX}.json"
audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

print(f"Wrote {archive_path}: {len(data):,} games")
print(f"Wrote {raw_path}: {len(data):,} games")
print(f"Wrote {csv_path}: {len(df):,} rows")
print("wrote:", audit_path)
print("wrote:", coverage_path)

print("\nPriority venue coverage:")
for row in coverage:
    status = "RETURNED" if row["returned"] else "MISSING"
    markets = ", ".join(
        f"{market}={row['market_event_counts'][market]}"
        for market in MARKETS
    )
    print(
        f"{row['book']:<16} {status:<8} "
        f"events={row['events_returned']:<4} rows={row['normalized_rows']:<5} "
        f"{markets}"
    )

if not df.empty:
    print("\nRows by market:")
    print(df.groupby("market").size().to_string())

    print("\nRows by book:")
    print(df.groupby("book").size().sort_values(ascending=False).to_string())
