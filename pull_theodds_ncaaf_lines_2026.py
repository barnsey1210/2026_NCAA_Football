#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API_KEY = os.environ.get("THE_ODDS_API_KEY")
if not API_KEY:
    raise SystemExit("Missing THE_ODDS_API_KEY environment variable.")

OUT_DIR = Path("data/odds")
ARCHIVE_DIR = OUT_DIR / "theodds_raw_archive"
AUDIT_DIR = Path("data/audits")
for directory in (OUT_DIR, ARCHIVE_DIR, AUDIT_DIR):
    directory.mkdir(parents=True, exist_ok=True)

SPORT = "americanfootball_ncaaf"
BOOKMAKERS = [
    "pinnacle",
    "novig",
    "prophetx",
    "kalshi",
    "draftkings",
    "fanduel",
    "betmgm",
    "williamhill_us",
    "fanatics",
    "hardrockbet_oh",
]
MARKETS = ["h2h", "spreads", "totals"]

url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
params = {
    "apiKey": API_KEY,
    "bookmakers": ",".join(BOOKMAKERS),
    "markets": ",".join(MARKETS),
    "oddsFormat": "american",
    "dateFormat": "iso",
}

resp = requests.get(url, params=params, timeout=45)
now = datetime.now(timezone.utc)
pulled_at = now.isoformat()

quota = {
    "pulled_at": pulled_at,
    "http_status": resp.status_code,
    "x_requests_last": resp.headers.get("x-requests-last"),
    "x_requests_used": resp.headers.get("x-requests-used"),
    "x_requests_remaining": resp.headers.get("x-requests-remaining"),
    "sport": SPORT,
    "bookmakers": BOOKMAKERS,
    "markets": MARKETS,
}
quota_path = AUDIT_DIR / "theodds_api_quota_status.json"
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
raw_path = OUT_DIR / "theodds_ncaaf_lines_2026_raw.json"

archive_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
raw_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

rows = []
for game in data:
    for book in game.get("bookmakers", []) or []:
        for market in book.get("markets", []) or []:
            market_key = market.get("key")
            if market_key not in {"h2h", "spreads", "totals"}:
                continue

            canonical_market = market_key

            for outcome in market.get("outcomes", []) or []:
                rows.append(
                    {
                        "pulled_at": pulled_at,
                        "source": "The Odds API",
                        "game_id": game.get("id"),
                        "commence_time": game.get("commence_time"),
                        "away_team": game.get("away_team"),
                        "home_team": game.get("home_team"),
                        "book_key": book.get("key"),
                        "book": book.get("title"),
                        "market": canonical_market,
                        "side": outcome.get("name"),
                        "point": outcome.get("point"),
                        "price": outcome.get("price"),
                        "last_update": book.get("last_update"),
                    }
                )

df = pd.DataFrame(rows)
csv_path = OUT_DIR / "theodds_ncaaf_lines_2026.csv"
df.to_csv(csv_path, index=False)

audit = dict(quota)
audit.update(
    {
        "events_returned": len(data),
        "normalized_rows": int(len(df)),
        "raw_archive": str(archive_path),
        "compatibility_raw": str(raw_path),
        "normalized_csv": str(csv_path),
    }
)
audit_path = AUDIT_DIR / "theodds_ncaaf_current_pull_audit.json"
audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

print(f"Wrote {archive_path}: {len(data):,} games")
print(f"Wrote {raw_path}: {len(data):,} games")
print(f"Wrote {csv_path}: {len(df):,} rows")
print("wrote:", audit_path)

if not df.empty:
    print("\nRows by market:")
    print(df.groupby("market").size().to_string())

    print("\nRows by book:")
    print(df.groupby("book").size().sort_values(ascending=False).to_string())
