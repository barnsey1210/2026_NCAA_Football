#!/usr/bin/env python3
"""
pull_fanduel_win_totals.py

SAFE FanDuel win totals puller.

1. Pulls FanDuel NCAAF page metadata from content-managed-page.
2. Finds win-total markets and maps marketId -> team/line/selection IDs.
3. Pulls live prices from getMarketPrices.
4. Writes/merges FanDuel rows into market_win_totals_import.csv.

Does NOT touch 2026_NCAA _Season.xlsm.

Usage:
  python3 pull_fanduel_win_totals.py --debug-only
  python3 pull_fanduel_win_totals.py
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests

META_URL = "https://api.sportsbook.fanduel.com/sbapi/content-managed-page?page=CUSTOM&customPageId=ncaaf&pbHorizontal=false&_ak=FhMFpcPWXMeyZxOx&timezone=America%2FNew_York"
PRICE_URL = "https://smp.oh.sportsbook.fanduel.com/api/sports/fixedodds/readonly/v1/getMarketPrices?priceHistory=0"
OUTPUT_CSV = "market_win_totals_import.csv"
META_RAW = "fanduel_win_totals_metadata_raw.json"
PRICES_RAW = "fanduel_win_totals_prices_raw.json"
DEBUG_MARKETS = "fanduel_win_totals_markets_debug.csv"

TEAM_ALIASES = {
    "VA Tech": "Virginia Tech", "Boston Col": "Boston College", "Florida St": "Florida State",
    "Miss State": "Mississippi State", "Kansas St": "Kansas State", "Arizona St": "Arizona State",
    "Oklahoma St": "Oklahoma State", "Iowa St": "Iowa State", "UCF": "Central Florida",
    "Miami (FL)": "Miami-FL",
}


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def clean(x: Any) -> str:
    return re.sub(r"\s+", " ", str(x or "")).strip()


def norm(x: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(x or "").lower())


def fetch_json(url: str, method: str = "GET", payload: Optional[dict] = None) -> Any:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://sportsbook.fanduel.com",
        "Referer": "https://sportsbook.fanduel.com/",
        "User-Agent": "Mozilla/5.0",
        "X-Application": "FhMFpcPWXMeyZxOx",
        "X-Sportsbook-Region": "OH",
    }
    if method.upper() == "POST":
        r = requests.post(url, headers=headers, json=payload, timeout=60)
    else:
        r = requests.get(url, headers=headers, timeout=60)
    print(method.upper(), url, "status:", r.status_code)
    if not r.ok:
        print(r.text[:2000])
        r.raise_for_status()
    return r.json()


def walk(obj: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def collect_dicts(obj: Any) -> List[Dict[str, Any]]:
    return [v for _, v in walk(obj) if isinstance(v, dict)]


def find_key(d: Dict[str, Any], names: List[str]) -> Any:
    lookup = {norm(k): v for k, v in d.items()}
    for name in names:
        if norm(name) in lookup:
            return lookup[norm(name)]
    for k, v in d.items():
        nk = norm(k)
        for name in names:
            if norm(name) in nk:
                return v
    return None


def extract_texts(d: Dict[str, Any]) -> str:
    vals = []
    for _, v in walk(d):
        if isinstance(v, str):
            vals.append(v)
    return " | ".join(vals)


def as_american(runner: Dict[str, Any]) -> Optional[int]:
    odds = runner.get("winRunnerOdds") or {}
    amer = odds.get("americanDisplayOdds") or {}
    val = amer.get("americanOddsInt")
    if val is None:
        val = amer.get("americanOdds")
    try:
        return int(round(float(val)))
    except Exception:
        return None


def team_clean(raw: str) -> str:
    s = clean(raw)
    s = re.sub(r"(?i)\b(total regular season wins|regular season wins|win total|total wins|over/under|over under)\b", "", s)
    s = re.sub(r"(?i)\b2026\b|\bNCAAF\b|\bCollege Football\b", "", s)
    s = re.sub(r"[-:|]", " ", s)
    mascots = [
        "Boilermakers","Buckeyes","Wolverines","Nittany Lions","Ducks","Hoosiers","Hawkeyes","Badgers",
        "Spartans","Cornhuskers","Trojans","Bruins","Scarlet Knights","Terrapins","Golden Gophers",
        "Longhorns","Red Raiders","Horned Frogs","Cyclones","Cowboys","Sun Devils","Jayhawks","Wildcats",
        "Bears","Mountaineers","Bearcats","Knights","Cougars","Utes","Cardinals","Hokies","Demon Deacons",
        "Eagles","Orange","Tigers","Seminoles","Hurricanes","Cavaliers","Blue Devils","Tar Heels","Wolfpack",
        "Panthers","Yellow Jackets","Mustangs","Aggies","Rebels","Razorbacks","Bulldogs","Crimson Tide",
        "Volunteers","Gators","Gamecocks","Commodores","Sooners"
    ]
    for m in sorted(mascots, key=len, reverse=True):
        s = re.sub(rf"\b{re.escape(m)}\b", "", s).strip()
    s = clean(s)
    return TEAM_ALIASES.get(s, s)


def parse_metadata(meta: Any) -> pd.DataFrame:
    """
    Parse FanDuel NCAAF regular-season win total markets.

    Important:
    FanDuel pages can contain conference grouping text around a market.
    Do NOT skip a market just because the surrounding JSON mentions "conference".
    Instead, identify win-total markets by runner names like:
      "UNLV Over 7.5 Wins"
      "UNLV Under 7.5 Wins"
    """
    rows = []
    seen = set()

    def parse_runner_name(name: str):
        txt = clean(name)
        m = re.search(r"^(.+?)\s+(Over|Under)\s+(\d+(?:\.\d+)?)\s+Wins\b", txt, flags=re.I)
        if not m:
            return None
        team = team_clean(m.group(1))
        side = m.group(2).lower()
        line = float(m.group(3))
        return team, side, line

    for d in collect_dicts(meta):
        market_id = find_key(d, ["marketId"])
        if not market_id:
            continue
        market_id = str(market_id)

        runners = d.get("runnerDetails") or d.get("runners") or d.get("marketRunners") or []
        if not isinstance(runners, list) or len(runners) < 2:
            nested = []
            for _, v in walk(d):
                if isinstance(v, list) and any(
                    isinstance(x, dict) and ("selectionId" in x or "runnerName" in x or "name" in x)
                    for x in v
                ):
                    nested = v
                    break
            runners = nested

        if not isinstance(runners, list) or len(runners) < 2:
            continue

        parsed_runners = []
        for r in runners:
            if not isinstance(r, dict):
                continue
            rid = r.get("selectionId") or r.get("runnerId") or r.get("id")
            rname = clean(find_key(r, ["runnerName", "selectionName", "name", "displayName"]))
            parsed = parse_runner_name(rname)
            if parsed and rid is not None:
                team, side, line = parsed
                parsed_runners.append({
                    "selection_id": str(rid),
                    "runner_name": rname,
                    "team": team,
                    "side": side,
                    "line": line,
                })

        if len(parsed_runners) < 2:
            continue

        overs = [x for x in parsed_runners if x["side"] == "over"]
        unders = [x for x in parsed_runners if x["side"] == "under"]
        if not overs or not unders:
            continue

        # Pair over/under by same team and same line.
        for over in overs:
            under = next(
                (
                    u for u in unders
                    if norm(u["team"]) == norm(over["team"]) and float(u["line"]) == float(over["line"])
                ),
                None,
            )
            if not under:
                continue

            team = TEAM_ALIASES.get(over["team"], over["team"])
            line = float(over["line"])

            # Avoid true conference/championship futures.
            bad = f"{over['runner_name']} {under['runner_name']}".lower()
            if "conference championship" in bad or "to win" in bad:
                continue

            title = clean(find_key(d, ["marketName", "name", "title", "eventName", "competitionName"]))
            if not title:
                title = f"{team} Regular Season Wins 2026"

            key = (market_id, team, line, over["selection_id"], under["selection_id"])
            if key in seen:
                continue
            seen.add(key)

            rows.append({
                "market_id": market_id,
                "team": team,
                "win_total": line,
                "over_selection_id": over["selection_id"],
                "under_selection_id": under["selection_id"],
                "over_name": over["runner_name"],
                "under_name": under["runner_name"],
                "metadata_title": title[:300],
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df[df["team"].astype(str).str.len().between(2, 40)]
    df = df[df["win_total"].notna()]

    # Keep unique market/team/line pairs. Do not dedupe only by market_id because
    # FanDuel can nest multiple runner groups near similar market structures.
    return df.drop_duplicates(
        subset=["market_id", "team", "win_total", "over_selection_id", "under_selection_id"]
    ).reset_index(drop=True)


def parse_prices(prices: Any) -> pd.DataFrame:
    rows = []
    if not isinstance(prices, list):
        return pd.DataFrame(rows)
    for m in prices:
        if not isinstance(m, dict):
            continue
        market_id = str(m.get("marketId") or "")
        for r in m.get("runnerDetails", []) or []:
            if not isinstance(r, dict):
                continue
            sid = r.get("selectionId")
            odds = as_american(r)
            if market_id and sid is not None and odds is not None:
                rows.append({"market_id": market_id, "selection_id": str(sid), "american_odds": odds})
    return pd.DataFrame(rows)


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
        existing = existing[~((existing["book"].astype(str) == "FanDuel") & (existing["snapshot_date"].astype(str) == today_s))]
    out = pd.concat([existing[cols], new_rows[cols]], ignore_index=True)
    out = out.drop_duplicates(subset=["snapshot_date","season","team","book","win_total"], keep="last")
    out = out.sort_values(["team","book"]).reset_index(drop=True)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--output-csv", default=OUTPUT_CSV)
    p.add_argument("--debug-only", action="store_true")
    args = p.parse_args()

    meta = fetch_json(META_URL, "GET")
    Path(META_RAW).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    md = parse_metadata(meta)
    md.to_csv(DEBUG_MARKETS, index=False)
    print("Metadata markets parsed:", len(md), "->", DEBUG_MARKETS)
    if md.empty:
        print("No usable metadata rows found. Check", META_RAW, "and", DEBUG_MARKETS)
        return

    market_ids = md["market_id"].dropna().astype(str).unique().tolist()
    prices = fetch_json(PRICE_URL, "POST", {"marketIds": market_ids})
    Path(PRICES_RAW).write_text(json.dumps(prices, indent=2), encoding="utf-8")
    px = parse_prices(prices)
    print("Price rows parsed:", len(px))

    rows = []
    price_lookup = {(r.market_id, r.selection_id): r.american_odds for r in px.itertuples(index=False)}
    for r in md.itertuples(index=False):
        over = price_lookup.get((str(r.market_id), str(r.over_selection_id)))
        under = price_lookup.get((str(r.market_id), str(r.under_selection_id)))
        if over is None and under is None:
            continue
        rows.append({
            "snapshot_date": today(),
            "season": args.season,
            "team": r.team,
            "conference": "",
            "book": "FanDuel",
            "win_total": r.win_total,
            "over_odds": over,
            "under_odds": under,
            "source_url": META_URL,
            "notes": f"FanDuel OH; market_id={r.market_id}; over_selection={r.over_selection_id}; under_selection={r.under_selection_id}",
        })
    out_new = pd.DataFrame(rows)
    print("FanDuel usable rows:", len(out_new))
    if not out_new.empty:
        print(out_new.head(30).to_string(index=False))
    if args.debug_only:
        out_new.to_csv("fanduel_win_totals_import_debug.csv", index=False)
        print("Debug only wrote fanduel_win_totals_import_debug.csv")
        return
    merged = merge_existing_output(out_new, args.output_csv)
    merged.to_csv(args.output_csv, index=False)
    print("Merged output:", args.output_csv, "rows:", len(merged))


if __name__ == "__main__":
    main()
