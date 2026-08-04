#!/usr/bin/env python3
"""Append current and provider-supplied open/close SGO prices by sportsbook."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_CANDIDATES = [
    ROOT / "data/markets/sgo/sgo_ncaaf_events_raw.json",
    ROOT / "data/markets/sgo/sgo_ncaaf_events_curl_raw.json",
]
OUT = ROOT / "data/odds/game_book_line_history.csv"
COLS = ["snapshot_ts", "source", "date", "away_team", "home_team", "game_key",
        "book", "market", "line", "price", "provider_open_line", "provider_open_price",
        "provider_close_line", "provider_close_price", "book_last_updated", "available"]

def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

def number(value):
    try:
        return float(str(value).replace("+", ""))
    except (TypeError, ValueError):
        return None

def body(path):
    raw = path.read_text(errors="ignore")
    if "\r\n\r\n" in raw:
        raw = raw.split("\r\n\r\n", 1)[1]
    elif "\n\n" in raw and raw.lstrip().startswith("HTTP/"):
        raw = raw.split("\n\n", 1)[1]
    return json.loads(raw)

def team(event, side):
    return (((event.get("teams") or {}).get(side) or {}).get("names") or {}).get("long") or ""

def main():
    existing = [p for p in RAW_CANDIDATES if p.exists()]
    if not existing:
        raise SystemExit("No SGO event response found")
    path = max(existing, key=lambda p: p.stat().st_mtime)
    payload = body(path)
    events = payload.get("data", []) if isinstance(payload, dict) else payload
    pulled_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    rows = []
    market_specs = [
        ("points-home-game-sp-home", "spread", "spread", "openSpread", "closeSpread"),
        ("points-all-game-ou-over", "total", "overUnder", "openOverUnder", "closeOverUnder"),
    ]
    for event in events:
        if event.get("leagueID") != "NCAAF":
            continue
        away, home = team(event, "away"), team(event, "home")
        starts = ((event.get("status") or {}).get("startsAt") or "")
        date = starts[:10]
        key = f"{date}|{norm(away)}|{norm(home)}"
        odds = event.get("odds") or {}
        for odd_id, market, line_field, open_field, close_field in market_specs:
            item = odds.get(odd_id) or {}
            for book, quote in (item.get("byBookmaker") or {}).items():
                line = number(quote.get(line_field))
                if line is None:
                    continue
                rows.append({
                    "snapshot_ts": pulled_at, "source": "SportsGameOdds", "date": date,
                    "away_team": away, "home_team": home, "game_key": key, "book": book,
                    "market": market, "line": line, "price": number(quote.get("odds")),
                    "provider_open_line": number(quote.get(open_field)),
                    "provider_open_price": number(quote.get("openOdds")),
                    "provider_close_line": number(quote.get(close_field)),
                    "provider_close_price": number(quote.get("closeOdds")),
                    "book_last_updated": quote.get("lastUpdatedAt"),
                    "available": bool(quote.get("available")),
                })
    new = pd.DataFrame(rows, columns=COLS)
    if len(new):
        new = new.drop_duplicates(["snapshot_ts", "game_key", "book", "market", "line", "price"])
    old = pd.read_csv(OUT, low_memory=False) if OUT.exists() else pd.DataFrame(columns=COLS)
    for col in COLS:
        if col not in old:
            old[col] = None
    combined = pd.concat([old[COLS], new], ignore_index=True)
    combined = combined.drop_duplicates(["snapshot_ts", "game_key", "book", "market", "line", "price"], keep="last")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT, index=False)
    print(f"SGO per-book rows appended: {len(new)}; total history rows: {len(combined)}")

if __name__ == "__main__":
    main()
