#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

URL = "https://api.actionnetwork.com/web/v2/scoreboard/ncaaf"

# Confirmed from Action live endpoint/browser:
# 2031 = DraftKings, 2028 = FanDuel, 1665 = BetMGM, 2029 = Caesars
BOOK_MAP = {
    "2031": "DraftKings",
    "2028": "FanDuel",
    "1665": "BetMGM",
    "2029": "Caesars",
}

BOOK_IDS = ",".join(BOOK_MAP.keys())
WEEKS = list(range(1, 15))

RAW_JSON_DIR = Path("data/odds/actionnetwork_scoreboard_raw")
OUT_CSV = Path("data/odds/actionnetwork_ncaaf_game_lines_2026.csv")


def team_name(game: dict, side: str) -> str:
    tid = game.get(f"{side}_team_id")
    for t in game.get("teams", []) or []:
        if str(t.get("id")) == str(tid):
            return t.get("location") or t.get("display_name") or t.get("full_name") or ""
    return ""


def flatten_outcome(game: dict, book_id: str, book: str, market: str, outcome: dict, pulled_at: str) -> dict:
    return {
        "pulled_at": pulled_at,
        "source": "Action Network",
        "game_id": game.get("id"),
        "core_id": game.get("core_id"),
        "event_id": outcome.get("event_id"),
        "market_id": outcome.get("market_id"),
        "season": game.get("season"),
        "week": game.get("week"),
        "commence_time": game.get("start_time"),
        "date": str(game.get("start_time") or "")[:10],
        "away_team": team_name(game, "away"),
        "home_team": team_name(game, "home"),
        "book_id": book_id,
        "book": book,
        "market": market,
        "side": outcome.get("side"),
        "team_id": outcome.get("team_id"),
        "point": outcome.get("value"),
        "price": outcome.get("odds"),
        "line_status": outcome.get("line_status"),
        "period": outcome.get("period"),
        "book_parent_id": outcome.get("book_parent_id"),
    }


def main() -> None:
    RAW_JSON_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    pulled_at = datetime.now(timezone.utc).isoformat()
    rows = []

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://www.actionnetwork.com/ncaaf/odds",
    }

    for week in WEEKS:
        params = {
            "bookIds": BOOK_IDS,
            "division": "FBS",
            "periods": "event",
            "seasonType": "reg",
            "week": week,
        }

        r = requests.get(URL, params=params, headers=headers, timeout=30)
        print(f"week={week} status={r.status_code} bytes={len(r.text)}")
        r.raise_for_status()

        raw_path = RAW_JSON_DIR / f"week_{week:02d}.json"
        raw_path.write_text(r.text, encoding="utf-8")

        data = r.json()
        games = data.get("games", []) or []

        market_rows = 0
        for g in games:
            for book_id, market_obj in (g.get("markets") or {}).items():
                book_id = str(book_id)
                if book_id not in BOOK_MAP:
                    continue

                book = BOOK_MAP[book_id]
                event = (market_obj or {}).get("event") or {}

                for market in ["spread", "total", "moneyline"]:
                    outcomes = event.get(market) or []
                    if isinstance(outcomes, dict):
                        outcomes = [outcomes]
                    for outcome in outcomes:
                        if isinstance(outcome, dict):
                            rows.append(flatten_outcome(g, book_id, book, market, outcome, pulled_at))
                            market_rows += 1

        print(f"  games={len(games)} market_rows={market_rows}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"\nWrote {OUT_CSV}: {len(df):,} rows")
    if not df.empty:
        print("\nRows by book:")
        print(df.groupby(["book_id", "book"]).size().sort_values(ascending=False).to_string())
        print("\nRows by market:")
        print(df.groupby("market").size().to_string())
        print("\nGames by week with odds:")
        print(df.groupby("week")["game_id"].nunique().to_string())


if __name__ == "__main__":
    main()
