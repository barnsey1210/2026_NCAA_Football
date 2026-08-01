#!/usr/bin/env python3
"""
pull_actionnetwork_win_totals_api.py

SAFE Action Network win totals puller.

Reads:
- Action Network public API endpoint for NCAAF regular-season win totals
- Action Network books endpoint for book_id -> sportsbook metadata

Writes:
- actionnetwork_win_totals_raw.json
- actionnetwork_book_id_mapping.csv
- market_win_totals_import.csv

Does NOT touch 2026_NCAA _Season.xlsm.

Default behavior:
- Uses Ohio books when available:
  DraftKings = DK OH / draftkingsoh
  BetMGM     = BetMGM OH / betmgmoh
- Leaves FanDuel and Caesars blank because they are not present on this Action win-total endpoint.
- If Ohio book is missing for a team, falls back to best available same-brand price across Action books.

Usage:
  python3 pull_actionnetwork_win_totals_api.py

Optional:
  python3 pull_actionnetwork_win_totals_api.py --prefer-state OH
  python3 pull_actionnetwork_win_totals_api.py --brand-mode best
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests


DEFAULT_URL = "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10997_2027_ncaaf_regular_season_total_wins"
BOOKS_URL = "https://api.actionnetwork.com/web/v1/books"

OPTION_TYPE_MAP = {
    72: "over",
    73: "under",
}

TEAM_ALIASES = {
    "VA Tech": "Virginia Tech",
    "Boston Col": "Boston College",
    "Florida St": "Florida State",
    "Miss State": "Mississippi State",
    "Kansas St": "Kansas State",
    "Arizona St": "Arizona State",
    "Oklahoma St": "Oklahoma State",
    "Iowa St": "Iowa State",
    "UCF": "Central Florida",
    "Miami (FL)": "Miami-FL",
}


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def clean_text(x: Any) -> str:
    return re.sub(r"\s+", " ", str(x or "")).strip()


def fetch_json(url: str) -> Any:
    headers = {
        "Accept": "application/json",
        "Origin": "https://www.actionnetwork.com",
        "Referer": "https://www.actionnetwork.com/ncaaf/futures",
        "User-Agent": "Mozilla/5.0",
    }
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


def team_name(t: Dict[str, Any]) -> str:
    display = clean_text(t.get("display_name"))
    full = clean_text(t.get("full_name"))
    if display:
        return TEAM_ALIASES.get(display, display)
    for mascot in [
        "Hokies", "Cardinals", "Demon Deacons", "Eagles", "Orange", "Tigers",
        "Seminoles", "Hurricanes", "Cavaliers", "Blue Devils", "Tar Heels",
        "Wolfpack", "Panthers", "Yellow Jackets", "Mustangs", "Utes", "Cougars",
        "Horned Frogs", "Cyclones", "Cowboys", "Red Raiders", "Sun Devils",
        "Jayhawks", "Wildcats", "Bears", "Mountaineers", "Bearcats", "Knights",
        "Buckeyes", "Wolverines", "Nittany Lions", "Ducks", "Hoosiers",
        "Hawkeyes", "Badgers", "Spartans", "Cornhuskers", "Trojans", "Bruins",
        "Scarlet Knights", "Terrapins", "Golden Gophers", "Boilermakers",
        "Fighting Illini", "Sooners", "Longhorns", "Aggies", "Rebels",
        "Razorbacks", "Bulldogs", "Crimson Tide", "Volunteers", "Gators",
        "Gamecocks", "Commodores",
    ]:
        full = full.replace(" " + mascot, "")
    return TEAM_ALIASES.get(full, full)


def brand_from_book(book: Dict[str, Any]) -> str:
    display = clean_text(book.get("display_name")).lower()
    source = clean_text(book.get("source_name")).lower()
    abbr = clean_text(book.get("abbr")).lower()
    combined = " ".join([display, source, abbr])

    if "draftkings" in combined or re.search(r"\bdk\b", combined):
        return "DraftKings"
    if "betmgm" in combined or "playmgm" in combined or re.search(r"\bmg\b", combined):
        return "BetMGM"
    if "fanduel" in combined or "fan duel" in combined:
        return "FanDuel"
    if "caesars" in combined:
        return "Caesars"
    if "betrivers" in combined or "bet rivers" in combined or re.search(r"\bbr\b", combined):
        return "BetRivers"
    if "bally" in combined:
        return "Bally Bet"
    if "bet365" in combined:
        return "bet365"
    if "hard rock" in combined:
        return "Hard Rock"
    if "consensus" in combined:
        return "Consensus"
    return ""


def state_from_book(book: Dict[str, Any]) -> str:
    display = clean_text(book.get("display_name")).upper()
    abbr = clean_text(book.get("abbr")).upper()
    source = clean_text(book.get("source_name")).lower()

    # Prefer explicit display suffixes like "DK OH", "BetMGM OH".
    for token in display.split():
        if len(token) == 2 and token.isalpha():
            return token

    # Common source suffixes.
    for st in ["OH", "NJ", "PA", "IN", "WV", "CO", "IL", "MI", "IA", "VA", "AZ", "NY", "LA", "ON", "MD", "KS", "MA", "KY", "ME", "VT", "NC", "MO", "TN", "CT", "OR", "WY", "DC"]:
        if source.endswith(st.lower()):
            return st

    # abbr examples: DKOH, MG OH, BR PA.
    for st in ["OH", "NJ", "PA", "IN", "WV", "CO", "IL", "MI", "IA", "VA", "AZ", "NY", "LA", "ON", "MD", "KS", "MA", "KY", "ME", "VT", "NC", "MO", "TN", "CT", "OR", "WY", "DC"]:
        if abbr.endswith(st):
            return st

    return ""


def build_books_map() -> Dict[int, Dict[str, Any]]:
    payload = fetch_json(BOOKS_URL)
    books = payload.get("books", [])
    out = {}
    for b in books:
        bid = b.get("id")
        if bid is None:
            continue
        out[int(bid)] = {
            "book_id": int(bid),
            "display_name": b.get("display_name"),
            "abbr": b.get("abbr"),
            "source_name": b.get("source_name"),
            "brand": brand_from_book(b),
            "state": state_from_book(b),
        }
    return out


def parse_all_book_rows(data: Dict[str, Any], books_map: Dict[int, Dict[str, Any]], source_url: str, season: int) -> pd.DataFrame:
    teams = {int(t["id"]): team_name(t) for t in data.get("teams", []) if t.get("id") is not None}

    rows = []
    for book_obj in data.get("books", []):
        book_id = book_obj.get("book_id")
        if book_id is None:
            continue
        book_info = books_map.get(int(book_id), {})
        brand = book_info.get("brand") or ""
        state = book_info.get("state") or ""
        display_name = book_info.get("display_name") or f"Action Book {book_id}"

        # Keep only target/currently useful books for the import.
        if brand not in {"DraftKings", "BetMGM", "FanDuel", "Caesars"}:
            continue

        paired: Dict[Tuple[str, float], Dict[str, Any]] = {}

        for odd in book_obj.get("odds", []):
            team_id = odd.get("team_id")
            if team_id is None or int(team_id) not in teams:
                continue

            side = OPTION_TYPE_MAP.get(int(odd.get("option_type_id"))) if odd.get("option_type_id") is not None else None
            if side not in {"over", "under"}:
                continue

            line = odd.get("value")
            money = odd.get("money")
            if line is None or money is None:
                continue

            key = (teams[int(team_id)], float(line))
            rec = paired.setdefault(key, {
                "snapshot_date": today(),
                "season": season,
                "team": teams[int(team_id)],
                "conference": "",
                "book": brand,
                "win_total": float(line),
                "over_odds": None,
                "under_odds": None,
                "source_url": source_url,
                "_action_book_id": int(book_id),
                "_action_book_display": display_name,
                "_action_book_state": state,
                "_action_book_source_name": book_info.get("source_name"),
            })

            if side == "over":
                rec["over_odds"] = int(money)
            else:
                rec["under_odds"] = int(money)

        rows.extend(paired.values())

    return pd.DataFrame(rows)


def choose_brand_rows(df: pd.DataFrame, prefer_state: str, brand_mode: str) -> pd.DataFrame:
    """
    Convert state-specific book rows to one row per team/brand/line.

    brand_mode:
    - state: use preferred state if available; fallback to best over/under row for that brand/team.
    - best: use best available over and under odds across all same-brand state books.
    """
    if df.empty:
        return df

    prefer_state = prefer_state.upper().strip()

    final_rows = []
    group_cols = ["snapshot_date", "season", "team", "conference", "book", "win_total", "source_url"]

    for keys, g in df.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, keys))
        g = g.copy()

        selected_note = ""

        if brand_mode == "state":
            sg = g[g["_action_book_state"].astype(str).str.upper() == prefer_state]
            if not sg.empty:
                # If multiple state rows somehow exist, use first complete row.
                row = sg.iloc[0]
                rec = {**base, "over_odds": row.get("over_odds"), "under_odds": row.get("under_odds")}
                selected_note = f"preferred_state={prefer_state}; action_book_id={row.get('_action_book_id')}; action_book_display={row.get('_action_book_display')}"
                rec["notes"] = selected_note
                final_rows.append(rec)
                continue

        # Fallback/best mode: best price by side across same-brand books.
        over_rows = g[g["over_odds"].notna()].sort_values("over_odds", ascending=False)
        under_rows = g[g["under_odds"].notna()].sort_values("under_odds", ascending=False)

        rec = {**base}
        if not over_rows.empty:
            r = over_rows.iloc[0]
            rec["over_odds"] = int(r["over_odds"])
            rec["_best_over_book_id"] = r.get("_action_book_id")
            rec["_best_over_display"] = r.get("_action_book_display")
            rec["_best_over_state"] = r.get("_action_book_state")
        else:
            rec["over_odds"] = None

        if not under_rows.empty:
            r = under_rows.iloc[0]
            rec["under_odds"] = int(r["under_odds"])
            rec["_best_under_book_id"] = r.get("_action_book_id")
            rec["_best_under_display"] = r.get("_action_book_display")
            rec["_best_under_state"] = r.get("_action_book_state")
        else:
            rec["under_odds"] = None

        rec["notes"] = (
            f"brand_mode={brand_mode}; "
            f"best_over={rec.get('_best_over_display')} {rec.get('_best_over_state')}; "
            f"best_under={rec.get('_best_under_display')} {rec.get('_best_under_state')}"
        )
        final_rows.append(rec)

    out = pd.DataFrame(final_rows)

    cols = [
        "snapshot_date", "season", "team", "conference", "book", "win_total",
        "over_odds", "under_odds", "source_url", "notes"
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = None
    return out[cols].sort_values(["team", "book", "win_total"]).reset_index(drop=True)


def build_book_audit(data: Dict[str, Any], books_map: Dict[int, Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for b in data.get("books", []):
        bid = b.get("book_id")
        info = books_map.get(int(bid), {}) if bid is not None else {}
        rows.append({
            "book_id": bid,
            "display_name": info.get("display_name"),
            "abbr": info.get("abbr"),
            "source_name": info.get("source_name"),
            "brand": info.get("brand"),
            "state": info.get("state"),
            "target_brand": info.get("brand") in {"DraftKings", "BetMGM", "FanDuel", "Caesars"},
            "odds_rows": len(b.get("odds", [])),
            "sample_team_id": b.get("odds", [{}])[0].get("team_id") if b.get("odds") else None,
            "sample_value": b.get("odds", [{}])[0].get("value") if b.get("odds") else None,
            "sample_money": b.get("odds", [{}])[0].get("money") if b.get("odds") else None,
            "sample_option_type_id": b.get("odds", [{}])[0].get("option_type_id") if b.get("odds") else None,
        })
    return pd.DataFrame(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--prefer-state", default="OH", help="Preferred state-specific book, e.g. OH.")
    p.add_argument("--brand-mode", choices=["state", "best"], default="state")
    p.add_argument("--raw-json", default="actionnetwork_win_totals_raw.json")
    p.add_argument("--output-csv", default="market_win_totals_import.csv")
    p.add_argument("--all-brand-rows-csv", default="actionnetwork_win_totals_all_brand_rows.csv")
    p.add_argument("--book-audit-csv", default="actionnetwork_book_id_mapping.csv")
    args = p.parse_args()

    data = fetch_json(args.url)
    books_map = build_books_map()

    Path(args.raw_json).write_text(json.dumps(data, indent=2), encoding="utf-8")

    audit = build_book_audit(data, books_map)
    audit.to_csv(args.book_audit_csv, index=False)

    all_rows = parse_all_book_rows(data, books_map, args.url, args.season)
    all_rows.to_csv(args.all_brand_rows_csv, index=False)

    out = choose_brand_rows(all_rows, args.prefer_state, args.brand_mode)
    out.to_csv(args.output_csv, index=False)

    print("Done.")
    print("Raw JSON:", args.raw_json)
    print("Book audit:", args.book_audit_csv)
    print("All brand rows:", args.all_brand_rows_csv)
    print("Output CSV:", args.output_csv)
    print("Rows:", len(out))
    if not out.empty:
        print("Teams:", out["team"].nunique())
        print("Books:")
        print(out["book"].value_counts().to_string())
        print("\nSample:")
        print(out.head(40).to_string(index=False))


if __name__ == "__main__":
    main()
