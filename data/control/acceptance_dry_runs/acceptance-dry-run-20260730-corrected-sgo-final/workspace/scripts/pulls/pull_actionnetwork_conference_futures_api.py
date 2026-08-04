#!/usr/bin/env python3
"""
pull_actionnetwork_conference_futures_api.py

SAFE Action Network conference futures puller.

Reads:
- Action Network public API endpoints for conference winner futures
- Action Network books endpoint for verified book_id -> sportsbook metadata

Writes:
- actionnetwork_conference_futures_raw_<conference>.json
- actionnetwork_conference_futures_all_brand_rows.csv
- actionnetwork_conference_futures_book_audit.csv
- market_conference_futures_import.csv

Does NOT touch 2026_NCAA _Season.xlsm.

Default behavior:
- Pulls ACC, Big 12, Big Ten, SEC, American, Conference USA, Mid-American,
  Mountain West, Pac-12, and Sun Belt.
- Uses Ohio books when available:
  DraftKings = DK OH / draftkingsoh
  BetMGM     = BetMGM OH / betmgmoh
- Leaves FanDuel/Caesars blank unless Action's API response actually includes them.
- If Ohio is missing for a team/brand, falls back to best same-brand price.

Usage:
  python3 pull_actionnetwork_conference_futures_api.py

Optional:
  python3 pull_actionnetwork_conference_futures_api.py --prefer-state OH
  python3 pull_actionnetwork_conference_futures_api.py --brand-mode best
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests


BOOKS_URL = "https://api.actionnetwork.com/web/v1/books"

# Action Network conference-title futures endpoints.
# Note: Action uses a 2027 slug for the market name even though the user-facing
# market is the 2026 NCAAF conference winner market. This matches the existing
# working ACC / Big 12 / Big Ten / SEC endpoints.
CONFERENCE_URLS = {
    "American": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10987_2027_ncaaf_american_athletic_conference_to_win",
    "ACC": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10988_2027_ncaaf_acc_conference_to_win",
    "Big 12": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10989_2027_ncaaf_big_12_conference_to_win",
    "Big Ten": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10990_2027_ncaaf_big_ten_conference_to_win",
    "Conference USA": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10991_2027_ncaaf_conference_usa_conference_to_win",
    "Mid-American": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_11017_2027_ncaaf_mid-american_conference_to_win",
    "Mountain West": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10993_2027_ncaaf_mountain_west_conference_to_win",
    "Pac-12": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10994_2027_ncaaf_pac-12_conference_to_win",
    "SEC": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10995_2027_ncaaf_sec_conference_to_win",
    "Sun Belt": "https://api.actionnetwork.com/web/v1/leagues/2/futures/ncaaf_futures_special_fixture_10996_2027_ncaaf_sun_belt_conference_to_win",
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
    "App St": "Appalachian State",
    "App State": "Appalachian State",
    "Arkansas St": "Arkansas State",
    "Boise St": "Boise State",
    "Colorado St": "Colorado State",
    "Fresno St": "Fresno State",
    "Georgia So": "Georgia Southern",
    "Georgia St": "Georgia State",
    "JMU": "James Madison",
    "J Madison": "James Madison",
    "Jacksonville St": "Jacksonville State",
    "Kennesaw St": "Kennesaw State",
    "LA Tech": "Louisiana Tech",
    "Louisiana-Lafayette": "Louisiana",
    "Miami (OH)": "Miami-OH",
    "New Mexico St": "New Mexico State",
    "North Texas": "North Texas",
    "N Texas": "North Texas",
    "Sam Houston St": "Sam Houston State",
    "San Diego St": "San Diego State",
    "San Jose St": "San Jose State",
    "Texas St": "Texas State",
    "Utah St": "Utah State",
    "Wash St": "Washington State",
    "Wazzu": "Washington State",
    "Western Ky": "Western Kentucky",
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
    if r.status_code != 200:
        print(f"WARNING: skipping Action Network URL with status {r.status_code}: {url}")
        return None
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
        "Gamecocks", "Commodores", "Owls", "Bulls", "Pirates", "Green Wave",
        "Golden Hurricane", "Roadrunners", "Mean Green", "Black Knights",
        "Midshipmen", "Blazers", "Flames", "Blue Raiders", "Hilltoppers",
        "Gamecocks", "Bearkats", "Aggies", "Miners", "Bulldogs", "RedHawks",
        "Bobcats", "Golden Flashes", "Zips", "Cardinals", "Falcons", "Rockets",
        "Huskies", "Broncos", "Chippewas", "Eagles", "Bison", "Rams",
        "Lobos", "Wolf Pack", "Rebels", "Aztecs", "Spartans", "Aggies",
        "Beavers", "Cougars", "Bulldogs", "Trojans", "Ragin' Cajuns",
        "Warhawks", "Red Wolves", "Mountaineers", "Eagles", "Thundering Herd",
        "Monarchs", "Chanticleers", "Dukes", "Panthers",
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

    for token in display.split():
        if len(token) == 2 and token.isalpha():
            return token

    for st in ["OH", "NJ", "PA", "IN", "WV", "CO", "IL", "MI", "IA", "VA", "AZ", "NY", "LA", "ON", "MD", "KS", "MA", "KY", "ME", "VT", "NC", "MO", "TN", "CT", "OR", "WY", "DC"]:
        if source.endswith(st.lower()):
            return st
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


def parse_all_brand_rows(conference: str, data: Dict[str, Any], books_map: Dict[int, Dict[str, Any]], source_url: str, season: int) -> pd.DataFrame:
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

        if brand not in {"DraftKings", "BetMGM", "FanDuel", "Caesars"}:
            continue

        for odd in book_obj.get("odds", []):
            team_id = odd.get("team_id")
            money = odd.get("money")
            if team_id is None or money is None or int(team_id) not in teams:
                continue

            rows.append({
                "snapshot_date": today(),
                "season": season,
                "conference": conference,
                "team": teams[int(team_id)],
                "book": brand,
                "american_odds": int(money),
                "source_url": source_url,
                "_action_book_id": int(book_id),
                "_action_book_display": display_name,
                "_action_book_state": state,
                "_action_book_source_name": book_info.get("source_name"),
            })

    return pd.DataFrame(rows)


def choose_brand_rows(df: pd.DataFrame, prefer_state: str, brand_mode: str) -> pd.DataFrame:
    """
    One row per conference/team/brand.

    brand_mode:
    - state: prefer selected state-specific book, fallback to best same-brand price.
    - best: best same-brand price across all available state books.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "snapshot_date", "season", "conference", "team", "book", "american_odds", "source_url", "notes"
        ])

    prefer_state = prefer_state.upper().strip()

    final_rows = []
    group_cols = ["snapshot_date", "season", "conference", "team", "book", "source_url"]

    for keys, g in df.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, keys))
        g = g.copy()

        if brand_mode == "state":
            sg = g[g["_action_book_state"].astype(str).str.upper() == prefer_state]
            if not sg.empty:
                row = sg.sort_values("american_odds", ascending=False).iloc[0]
                rec = {
                    **base,
                    "american_odds": int(row["american_odds"]),
                    "notes": f"preferred_state={prefer_state}; action_book_id={row.get('_action_book_id')}; action_book_display={row.get('_action_book_display')}",
                }
                final_rows.append(rec)
                continue

        row = g.sort_values("american_odds", ascending=False).iloc[0]
        final_rows.append({
            **base,
            "american_odds": int(row["american_odds"]),
            "notes": f"brand_mode={brand_mode}; selected={row.get('_action_book_display')} {row.get('_action_book_state')}; action_book_id={row.get('_action_book_id')}",
        })

    out = pd.DataFrame(final_rows)
    cols = ["snapshot_date", "season", "conference", "team", "book", "american_odds", "source_url", "notes"]
    return out[cols].sort_values(["conference", "team", "book"]).reset_index(drop=True)


def build_book_audit(all_data: Dict[str, Dict[str, Any]], books_map: Dict[int, Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for conference, data in all_data.items():
        for b in data.get("books", []):
            bid = b.get("book_id")
            info = books_map.get(int(bid), {}) if bid is not None else {}
            rows.append({
                "conference": conference,
                "book_id": bid,
                "display_name": info.get("display_name"),
                "abbr": info.get("abbr"),
                "source_name": info.get("source_name"),
                "brand": info.get("brand"),
                "state": info.get("state"),
                "target_brand": info.get("brand") in {"DraftKings", "BetMGM", "FanDuel", "Caesars"},
                "odds_rows": len(b.get("odds", [])),
                "sample_team_id": b.get("odds", [{}])[0].get("team_id") if b.get("odds") else None,
                "sample_money": b.get("odds", [{}])[0].get("money") if b.get("odds") else None,
            })
    return pd.DataFrame(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--prefer-state", default="OH")
    p.add_argument("--brand-mode", choices=["state", "best"], default="state")
    p.add_argument("--output-csv", default="market_conference_futures_import.csv")
    p.add_argument("--all-brand-rows-csv", default="actionnetwork_conference_futures_all_brand_rows.csv")
    p.add_argument("--book-audit-csv", default="actionnetwork_conference_futures_book_audit.csv")
    p.add_argument("--only", nargs="*", choices=list(CONFERENCE_URLS.keys()), default=None, help="Optional list of conferences to pull.")
    args = p.parse_args()

    books_map = build_books_map()
    selected = args.only if args.only else list(CONFERENCE_URLS.keys())

    all_data = {}
    all_brand_rows = []
    endpoint_audit_rows = []

    for conference in selected:
        url = CONFERENCE_URLS[conference]
        data = fetch_json(url)
        if data is None:
            endpoint_audit_rows.append({"conference": conference, "ok": False, "url": url})
            continue

        endpoint_audit_rows.append({"conference": conference, "ok": True, "url": url})
        all_data[conference] = data
        safe_conf = conference.lower().replace(" ", "_").replace("-", "_")
        Path(f"actionnetwork_conference_futures_raw_{safe_conf}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        rows = parse_all_brand_rows(conference, data, books_map, url, args.season)
        all_brand_rows.append(rows)

    pd.DataFrame(endpoint_audit_rows).to_csv("actionnetwork_conference_futures_endpoint_audit.csv", index=False)
    all_rows = pd.concat(all_brand_rows, ignore_index=True) if all_brand_rows else pd.DataFrame()
    all_rows.to_csv(args.all_brand_rows_csv, index=False)

    audit = build_book_audit(all_data, books_map)
    audit.to_csv(args.book_audit_csv, index=False)

    out = choose_brand_rows(all_rows, args.prefer_state, args.brand_mode)
    out.to_csv(args.output_csv, index=False)

    print("Done.")
    print("Conferences:", ", ".join(selected))
    print("Book audit:", args.book_audit_csv)
    print("All brand rows:", args.all_brand_rows_csv)
    print("Output CSV:", args.output_csv)
    print("Rows:", len(out))
    if not out.empty:
        print("Teams:", out["team"].nunique())
        print("Rows by conference:")
        print(out["conference"].value_counts().to_string())
        print("Rows by book:")
        print(out["book"].value_counts().to_string())
        print("\nSample:")
        print(out.head(60).to_string(index=False))


if __name__ == "__main__":
    main()
