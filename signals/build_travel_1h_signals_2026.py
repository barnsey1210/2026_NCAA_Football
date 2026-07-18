#!/usr/bin/env python3
from pathlib import Path
import json, re, html
import pandas as pd
import numpy as np

INDEX = Path("index.html")
OUT = Path("data/signals/travel_1h_signals_2026.csv")

TEAM_TZ = {
    "Hawaii": -10,

    # Pacific
    "Washington": -8, "Washington State": -8, "Oregon": -8, "Oregon State": -8,
    "USC": -8, "UCLA": -8, "Stanford": -8, "California": -8, "Cal": -8,
    "San Jose State": -8, "Fresno State": -8, "San Diego State": -8, "Nevada": -8, "UNLV": -8,
    "Sacramento State": -8,

    # Mountain
    "Arizona": -7, "Arizona State": -7, "Boise State": -7, "BYU": -7,
    "Utah": -7, "Utah State": -7, "Colorado": -7, "Colorado State": -7,
    "Air Force": -7, "Wyoming": -7, "New Mexico": -7, "New Mexico State": -7, "UTEP": -7,

    # Central
    "Nebraska": -6, "Iowa": -6, "Minnesota": -6, "Wisconsin": -6, "Illinois": -6,
    "Northwestern": -6, "Texas": -6, "Texas A&M": -6, "Baylor": -6, "TCU": -6,
    "SMU": -6, "Houston": -6, "Oklahoma": -6, "Oklahoma State": -6, "Kansas": -6,
    "Kansas State": -6, "Missouri": -6, "Arkansas": -6, "LSU": -6, "Tulane": -6,
    "Memphis": -6, "Alabama": -6, "Auburn": -6, "Mississippi State": -6, "Ole Miss": -6,
    "Eastern Michigan": -5,  # school is Eastern, kept explicit below too

    # Eastern
    "Michigan": -5, "Michigan State": -5, "Ohio State": -5, "Penn State": -5,
    "Rutgers": -5, "Maryland": -5, "Indiana": -5, "Purdue": -5,
    "Boston College": -5, "Syracuse": -5, "Pittsburgh": -5, "Virginia": -5,
    "Virginia Tech": -5, "North Carolina": -5, "NC State": -5, "Duke": -5,
    "Wake Forest": -5, "Clemson": -5, "Georgia Tech": -5, "Florida State": -5,
    "Miami-FL": -5, "Miami": -5, "Louisville": -5,
    "Florida": -5, "UCF": -5, "South Florida": -5, "Florida Atlantic": -5, "FIU": -5,
    "Georgia": -5, "Georgia State": -5, "Georgia Southern": -5,
    "Tennessee": -5, "Kentucky": -5, "West Virginia": -5, "Marshall": -5,
    "Cincinnati": -5, "Ohio": -5, "Miami-OH": -5, "Toledo": -5, "Bowling Green": -5,
    "Akron": -5, "Kent State": -5, "Ball State": -5, "Buffalo": -5,
    "Eastern Michigan": -5, "Central Michigan": -5, "Western Michigan": -5,
}

ALIASES = {
    "Hawai'i": "Hawaii",
    "Miami (FL)": "Miami-FL",
    "California": "Cal",
}

BIG_TEN_2024 = {
    "Illinois", "Indiana", "Iowa", "Maryland", "Michigan", "Michigan State",
    "Minnesota", "Nebraska", "Northwestern", "Ohio State", "Oregon", "Penn State",
    "Purdue", "Rutgers", "UCLA", "USC", "Washington", "Wisconsin"
}

ACC_2024 = {
    "Boston College", "Cal", "California", "Clemson", "Duke", "Florida State",
    "Georgia Tech", "Louisville", "Miami-FL", "Miami", "NC State", "North Carolina",
    "Pittsburgh", "SMU", "Stanford", "Syracuse", "Virginia", "Virginia Tech",
    "Wake Forest"
}

WESTERN_EXPANSION = {"USC", "UCLA", "Oregon", "Washington", "Stanford", "Cal", "California"}

def clean_team(x):
    if pd.isna(x):
        return ""
    x = str(x).strip()
    return ALIASES.get(x, x)

def num(x):
    try:
        n = float(x)
        return n if np.isfinite(n) else None
    except Exception:
        return None

def read_db():
    s = INDEX.read_text(errors="ignore")
    m = re.search(r"""<script[^>]+id=["']db["'][^>]*>([\s\S]*?)</script>""", s, flags=re.I)
    if not m:
        raise SystemExit("Could not find DB script in index.html")
    return json.loads(html.unescape(m.group(1)))

def main():
    db = read_db()
    games = db.get("games", [])
    rows = []

    for g in games:
        away = clean_team(g.get("away_team"))
        home = clean_team(g.get("home_team"))
        away_tz = TEAM_TZ.get(away)
        home_tz = TEAM_TZ.get(home)

        if away_tz is None or home_tz is None:
            continue

        tz_delta = home_tz - away_tz
        tz_abs = abs(tz_delta)
        if tz_abs < 3:
            continue

        is_b10 = away in BIG_TEN_2024 and home in BIG_TEN_2024
        is_acc = away in ACC_2024 and home in ACC_2024
        if not (is_b10 or is_acc):
            continue

        direction = "Eastbound" if tz_delta > 0 else "Westbound" if tz_delta < 0 else "Same"
        conf_family = "Big Ten" if is_b10 else "ACC"

        # Away role for the 1H travel badge.
        # Prefer current full-game market if available, otherwise projection.
        market_home = num(g.get("market_spread_home"))
        proj_home = num(g.get("projected_margin_home"))

        basis = "market"
        if market_home is not None:
            # home spread negative => home favored => away dog
            away_role = "Underdog" if market_home < 0 else "Favorite" if market_home > 0 else "Pick"
        elif proj_home is not None:
            basis = "projection"
            away_role = "Underdog" if proj_home > 0 else "Favorite" if proj_home < 0 else "Pick"
        else:
            basis = "unknown"
            away_role = "Unknown"

        western_away = away in WESTERN_EXPANSION
        western_home = home in WESTERN_EXPANSION
        nonwest_to_west = (not western_away) and western_home and direction == "Westbound"
        west_to_east = western_away and (not western_home) and direction == "Eastbound"

        spread_badge = ""
        spread_title = ""
        spread_side = ""

        if away_role == "Underdog":
            spread_side = home
            if nonwest_to_west:
                spread_badge = "1H Travel: fade road dog"
                spread_title = "2024-25 Big Ten/ACC 3+ TZ: non-west teams traveling west as 1H dogs went 2-13 ATS, 13.3%, -3.90 ATS margin. Supports home 1H side only."
            else:
                spread_badge = "1H Travel: road dog fade"
                spread_title = "2024-25 Big Ten/ACC 3+ TZ traveler underdogs went 9-22 1H ATS, 29.0%, -3.89 ATS margin. Supports opponent 1H side only."
        elif away_role == "Favorite":
            spread_side = away
            if west_to_east:
                spread_badge = "1H Travel: road fav start"
                spread_title = "2024-25 Big Ten/ACC 3+ TZ western expansion teams traveling east as 1H favorites went 10-2 ATS, 83.3%, +3.71 ATS margin. Supports traveler 1H favorite only."
            else:
                spread_badge = "1H Travel: road fav start"
                spread_title = "2024-25 Big Ten/ACC 3+ TZ traveler favorites went 17-7 1H ATS, 70.8%, +3.73 ATS margin. Supports traveler 1H favorite only."

        total_badge = ""
        total_title = ""
        total_side = ""

        if nonwest_to_west:
            total_badge = "1H Travel O: 17-10"
            total_side = "Over"
            total_title = "2024-25 Big Ten/ACC non-west teams traveling 3+ TZ west: 1H totals went 17 O / 10 U, 63.0% over, +2.46 avg 1H total margin."
        elif tz_abs >= 3:
            total_badge = "1H Travel O: 32-23"
            total_side = "Over"
            total_title = "2024-25 Big Ten/ACC 3+ TZ travel games: 1H totals went 32 O / 23 U, 58.2% over. Context only; direction split is stronger westbound."

        if not spread_badge and not total_badge:
            continue

        rows.append({
            "game_id": g.get("game_id", ""),
            "date": g.get("date", ""),
            "away_team": g.get("away_team", ""),
            "home_team": g.get("home_team", ""),
            "away_clean": away,
            "home_clean": home,
            "conference_family": conf_family,
            "away_tz": away_tz,
            "home_tz": home_tz,
            "tz_delta": tz_delta,
            "tz_abs": tz_abs,
            "travel_direction": direction,
            "away_role_basis": basis,
            "away_role": away_role,
            "spread_badge": spread_badge,
            "spread_side": spread_side,
            "spread_title": spread_title,
            "total_badge": total_badge,
            "total_side": total_side,
            "total_title": total_title,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)

    print("travel 1H signal games:", len(rows))
    print("wrote:", OUT)
    if rows:
        print(pd.DataFrame(rows)[[
            "date", "away_team", "home_team", "travel_direction", "away_role",
            "spread_badge", "spread_side", "total_badge"
        ]].to_string(index=False))

if __name__ == "__main__":
    main()
