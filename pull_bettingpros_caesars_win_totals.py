#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

API_URL = "https://api.bettingpros.com/v3/offers"
OUTPUT_CSV = "market_win_totals_import.csv"
DEBUG_CSV = "bettingpros_caesars_win_totals_debug.csv"

CAESARS_BOOK_ID = 13
API_KEY_ENV = "BETTINGPROS_API_KEY"

TEAM_ALIASES = {
    "Ohio St.": "Ohio State",
    "Penn St.": "Penn State",
    "NC St.": "NC State",
    "Florida St.": "Florida State",
    "Iowa St.": "Iowa State",
    "Kansas St.": "Kansas State",
    "Oklahoma St.": "Oklahoma State",
    "Arizona St.": "Arizona State",
    "Miss St.": "Mississippi State",
    "Mississippi St.": "Mississippi State",
    "Miami (FL)": "Miami-FL",
    "Miami FL": "Miami-FL",
    "UCF": "Central Florida",
    "GA Tech": "Georgia Tech",
    "UCLA": "UCLA",
    "USC": "USC",
    "SMU": "SMU",
    "BYU": "BYU",
    "TCU": "TCU",
}

def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def clean_team(name: Any) -> str:
    s = str(name or "").strip()
    return TEAM_ALIASES.get(s, s)

def fetch_page(page: int, limit: int = 10) -> dict:
    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(
            f"Missing {API_KEY_ENV}; BettingPros/Caesars pull was not attempted."
        )
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.bettingpros.com",
        "Referer": "https://www.bettingpros.com/",
        "User-Agent": "Mozilla/5.0",
        "x-api-key": api_key,
    }
    params = {
        "sport": "NCAAF",
        "market_id": 223,
        "season": 2026,
        "limit": limit,
        "page": page,
    }
    r = requests.get(API_URL, headers=headers, params=params, timeout=60)
    print("GET page", page, "status:", r.status_code)
    if not r.ok:
        print(r.text[:1000])
        r.raise_for_status()
    return r.json()

def get_offers_from_response(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, dict):
        for key in ["offers", "data", "results"]:
            val = data.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
        # sometimes nested
        for val in data.values():
            if isinstance(val, dict):
                out = get_offers_from_response(val)
                if out:
                    return out
    elif isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []

def line_for_book(selection: Dict[str, Any], book_id: int) -> Optional[Dict[str, Any]]:
    for b in selection.get("books", []) or []:
        if not isinstance(b, dict):
            continue
        if str(b.get("id")) != str(book_id):
            continue
        lines = [ln for ln in (b.get("lines") or []) if isinstance(ln, dict)]
        if not lines:
            return None
        valid = [ln for ln in lines if ln.get("active", True) and not ln.get("is_off", False)]
        return valid[0] if valid else lines[0]
    return None

def parse_offer(offer: Dict[str, Any], season: int) -> Optional[dict]:
    if str(offer.get("market_id")) != "223":
        return None

    participants = offer.get("participants") or []
    if not participants or not isinstance(participants[0], dict):
        return None

    p0 = participants[0]
    team_obj = p0.get("team", {}) if isinstance(p0.get("team", {}), dict) else {}

    team = clean_team(team_obj.get("city") or p0.get("name") or offer.get("team_id"))
    conference = str(team_obj.get("conference") or "").strip()

    over_line = under_line = None
    over_odds = under_odds = None
    over_updated = under_updated = None

    for sel in offer.get("selections", []) or []:
        if not isinstance(sel, dict):
            continue

        side = str(sel.get("selection") or sel.get("label") or sel.get("short_label") or "").lower()
        ln = line_for_book(sel, CAESARS_BOOK_ID)
        if not ln:
            continue

        try:
            line_value = float(ln.get("line"))
            cost = int(round(float(ln.get("cost"))))
        except Exception:
            continue

        if side == "over":
            over_line = line_value
            over_odds = cost
            over_updated = ln.get("updated")
        elif side == "under":
            under_line = line_value
            under_odds = cost
            under_updated = ln.get("updated")

    if over_odds is None and under_odds is None:
        return None

    win_total = over_line if over_line is not None else under_line

    return {
        "snapshot_date": today(),
        "season": season,
        "team": team,
        "conference": conference,
        "book": "Caesars",
        "win_total": win_total,
        "over_odds": over_odds,
        "under_odds": under_odds,
        "source_url": API_URL,
        "notes": f"BettingPros API book_id=13 Caesars; offer_id={offer.get('id')}; over_updated={over_updated}; under_updated={under_updated}",
    }

def pull_all_caesars(limit: int, season: int) -> pd.DataFrame:
    rows = []
    page = 1

    while True:
        data = fetch_page(page=page, limit=limit)
        offers = get_offers_from_response(data)
        print("offers on page:", len(offers))

        if not offers:
            break

        for offer in offers:
            row = parse_offer(offer, season)
            if row:
                rows.append(row)

        if len(offers) < limit:
            break

        page += 1
        if page > 50:
            raise RuntimeError("Too many pages; stopping safety check.")

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["snapshot_date", "season", "team", "book", "win_total"], keep="last")
    return df.sort_values(["team", "book"]).reset_index(drop=True)

def merge_existing_output(new_rows: pd.DataFrame, output_csv: str) -> pd.DataFrame:
    cols = ["snapshot_date","season","team","conference","book","win_total","over_odds","under_odds","source_url","notes"]
    p = Path(output_csv)

    if p.exists() and p.stat().st_size > 0:
        existing = pd.read_csv(p)
    else:
        existing = pd.DataFrame(columns=cols)

    for c in cols:
        if c not in existing.columns:
            existing[c] = None
        if c not in new_rows.columns:
            new_rows[c] = None

    if not new_rows.empty:
        today_s = today()
        existing = existing[~((existing["book"].astype(str) == "Caesars") & (existing["snapshot_date"].astype(str) == today_s))]

    out = pd.concat([existing[cols], new_rows[cols]], ignore_index=True)
    out = out.drop_duplicates(subset=["snapshot_date","season","team","book","win_total"], keep="last")
    return out.sort_values(["team","book"]).reset_index(drop=True)

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output-csv", default=OUTPUT_CSV)
    p.add_argument("--debug-only", action="store_true")
    args = p.parse_args()

    caesars = pull_all_caesars(limit=args.limit, season=args.season)
    caesars.to_csv(DEBUG_CSV, index=False)

    print("Caesars rows:", len(caesars), "teams:", caesars["team"].nunique() if not caesars.empty else 0)
    if not caesars.empty:
        print(caesars.head(80).to_string(index=False))

    if args.debug_only:
        print("Debug only; did not merge.")
        return

    merged = merge_existing_output(caesars, args.output_csv)
    merged.to_csv(args.output_csv, index=False)
    print("Merged output:", args.output_csv, "rows:", len(merged))

if __name__ == "__main__":
    main()
