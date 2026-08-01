#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


YEAR = 2026
BASE_URL = "https://api.collegefootballdata.com/lines"
OUT_DIR = Path("data/odds")
RAW_JSON = OUT_DIR / "cfbd_lines_2026_raw.json"
OUT_CSV = OUT_DIR / "cfbd_lines_2026.csv"
AUDIT_CSV = OUT_DIR / "cfbd_lines_2026_audit.csv"


def require_key() -> str:
    key = os.environ.get("CFBD_API_KEY")
    if not key:
        raise SystemExit("Missing CFBD_API_KEY. Run: export CFBD_API_KEY='your_key_here'")
    return key


def fetch_lines(year: int) -> list[dict]:
    key = require_key()
    headers = {"Authorization": f"Bearer {key}"}
    params = {"year": year}

    response = requests.get(BASE_URL, headers=headers, params=params, timeout=45)

    if response.status_code != 200:
        raise SystemExit(
            f"CFBD lines request failed: HTTP {response.status_code}\n"
            f"URL: {response.url}\n"
            f"Body: {response.text[:800]}"
        )

    data = response.json()
    if not isinstance(data, list):
        raise SystemExit(f"Unexpected CFBD response type: {type(data)}")
    return data


def american_to_implied_prob(odds):
    if odds is None or pd.isna(odds):
        return None
    try:
        odds = float(odds)
    except Exception:
        return None
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    return 100 / (odds + 100)


def normalize_line_rows(data: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    pulled_at = datetime.now(timezone.utc).isoformat()

    rows = []
    audit = []

    for game in data:
        game_id = game.get("id")
        season = game.get("season")
        week = game.get("week")
        season_type = game.get("seasonType")
        start_date = game.get("startDate")
        home_team = game.get("homeTeam")
        away_team = game.get("awayTeam")

        lines = game.get("lines") or []
        audit.append({
            "game_id": game_id,
            "season": season,
            "week": week,
            "date": start_date,
            "away_team": away_team,
            "home_team": home_team,
            "books": len(lines),
            "has_lines": bool(lines),
        })

        for line in lines:
            provider = line.get("provider")
            spread = line.get("spread")
            formatted_spread = line.get("formattedSpread")
            spread_open = line.get("spreadOpen")
            over_under = line.get("overUnder")
            over_under_open = line.get("overUnderOpen")
            home_moneyline = line.get("homeMoneyline")
            away_moneyline = line.get("awayMoneyline")

            rows.append({
                "pulled_at": pulled_at,
                "season": season,
                "week": week,
                "season_type": season_type,
                "date": start_date,
                "game_id": game_id,
                "away_team": away_team,
                "home_team": home_team,
                "book": provider,
                "spread": spread,
                "formatted_spread": formatted_spread,
                "spread_open": spread_open,
                "total": over_under,
                "total_open": over_under_open,
                "home_moneyline": home_moneyline,
                "away_moneyline": away_moneyline,
                "home_moneyline_implied": american_to_implied_prob(home_moneyline),
                "away_moneyline_implied": american_to_implied_prob(away_moneyline),
                "source": "CFBD Lines",
            })

    return pd.DataFrame(rows), pd.DataFrame(audit)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = fetch_lines(YEAR)
    RAW_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")

    lines_df, audit_df = normalize_line_rows(data)

    lines_df.to_csv(OUT_CSV, index=False)
    audit_df.to_csv(AUDIT_CSV, index=False)

    print(f"Wrote {RAW_JSON}: {len(data):,} games")
    print(f"Wrote {OUT_CSV}: {len(lines_df):,} book line rows")
    print(f"Wrote {AUDIT_CSV}: {len(audit_df):,} games audited")

    if not lines_df.empty:
        print("\nRows by book:")
        print(lines_df.groupby("book").size().sort_values(ascending=False).head(30))

        print("\nSample:")
        show_cols = ["week", "date", "away_team", "home_team", "book", "formatted_spread", "spread", "total", "home_moneyline", "away_moneyline"]
        show_cols = [c for c in show_cols if c in lines_df.columns]
        print(lines_df[show_cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
