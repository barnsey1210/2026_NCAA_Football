#!/usr/bin/env python3
import os
import json
from pathlib import Path
from datetime import datetime, timezone

import requests
import pandas as pd

API_KEY = os.environ.get("THE_ODDS_API_KEY")
if not API_KEY:
    raise SystemExit("Missing THE_ODDS_API_KEY environment variable.")

OUT_DIR = Path("data/odds")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SPORT = "americanfootball_ncaaf"
REGIONS = "us,us2"
MARKETS = "spreads,totals"
ODDS_FORMAT = "american"
DATE_FORMAT = "iso"

url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
params = {
    "apiKey": API_KEY,
    "regions": REGIONS,
    "markets": MARKETS,
    "oddsFormat": ODDS_FORMAT,
    "dateFormat": DATE_FORMAT,
}

resp = requests.get(url, params=params, timeout=30)

print("Status:", resp.status_code)
print("x-requests-used:", resp.headers.get("x-requests-used"))
print("x-requests-remaining:", resp.headers.get("x-requests-remaining"))
print("x-requests-last:", resp.headers.get("x-requests-last"))

if resp.status_code != 200:
    print(resp.text[:1000])
    raise SystemExit(1)

data = resp.json()
pulled_at = datetime.now(timezone.utc).isoformat()

raw_path = OUT_DIR / "theodds_ncaaf_lines_2026_raw.json"
raw_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

rows = []
for game in data:
    game_id = game.get("id")
    commence_time = game.get("commence_time")
    home_team = game.get("home_team")
    away_team = game.get("away_team")

    for book in game.get("bookmakers", []) or []:
        book_key = book.get("key")
        book_title = book.get("title")
        last_update = book.get("last_update")

        for market in book.get("markets", []) or []:
            mkey = market.get("key")
            outcomes = market.get("outcomes", []) or []

            if mkey == "spreads":
                for o in outcomes:
                    team = o.get("name")
                    rows.append({
                        "pulled_at": pulled_at,
                        "source": "The Odds API",
                        "game_id": game_id,
                        "commence_time": commence_time,
                        "away_team": away_team,
                        "home_team": home_team,
                        "book_key": book_key,
                        "book": book_title,
                        "market": "spreads",
                        "side": team,
                        "point": o.get("point"),
                        "price": o.get("price"),
                        "last_update": last_update,
                    })

            elif mkey == "totals":
                for o in outcomes:
                    rows.append({
                        "pulled_at": pulled_at,
                        "source": "The Odds API",
                        "game_id": game_id,
                        "commence_time": commence_time,
                        "away_team": away_team,
                        "home_team": home_team,
                        "book_key": book_key,
                        "book": book_title,
                        "market": "totals",
                        "side": o.get("name"),  # Over / Under
                        "point": o.get("point"),
                        "price": o.get("price"),
                        "last_update": last_update,
                    })

df = pd.DataFrame(rows)
csv_path = OUT_DIR / "theodds_ncaaf_lines_2026.csv"
df.to_csv(csv_path, index=False)

print(f"Wrote {raw_path}: {len(data):,} games")
print(f"Wrote {csv_path}: {len(df):,} rows")

if not df.empty:
    print("\nRows by market:")
    print(df.groupby("market").size().to_string())

    print("\nRows by book:")
    print(df.groupby("book").size().sort_values(ascending=False).head(25).to_string())

    print("\nSample:")
    print(df.head(30).to_string(index=False))
