#!/usr/bin/env python3
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

IMPORTANCE = Path("data/rosters/player_importance_2026.csv")
MISSING = Path("data/rosters/ourlads_missing_depth_charts.csv")
OUT = Path("data/rosters/team_name_crosswalk_ourlads_to_site.csv")

TEAM_SOURCE_CANDIDATES = [
    Path("ratings_latest.csv"),
    Path("data/ratings/ratings_latest.csv"),
    Path("market_win_totals_import.csv"),
    Path("data/import/market_win_totals_import.csv"),
    Path("data/odds/actionnetwork_ncaaf_game_lines_2026.csv"),
]

MANUAL = {
    "Alabama Crimson Tide": "Alabama",
    "Air Force Falcons": "Air Force",
    "Akron Zips": "Akron",
    "Appalachian State Mountaineers": "Appalachian State",
    "Arizona Wildcats": "Arizona",
    "Arizona State Sun Devils": "Arizona State",
    "Arkansas Razorbacks": "Arkansas",
    "Arkansas State Red Wolves": "Arkansas State",
    "Army Black Knights": "Army",
    "Auburn Tigers": "Auburn",
    "Ball State Cardinals": "Ball State",
    "Baylor Bears": "Baylor",
    "Boise State Broncos": "Boise State",
    "Boston College Eagles": "Boston College",
    "Bowling Green Falcons": "Bowling Green",
    "Buffalo Bulls": "Buffalo",
    "BYU Cougars": "BYU",
    "California Golden Bears": "California",
    "Central Florida Knights": "UCF",
    "Central Michigan Chippewas": "Central Michigan",
    "Charlotte 49ers": "Charlotte",
    "Cincinnati Bearcats": "Cincinnati",
    "Clemson Tigers": "Clemson",
    "Coastal Carolina Chanticleers": "Coastal Carolina",
    "Colorado Buffaloes": "Colorado",
    "Colorado State Rams": "Colorado State",
    "Connecticut Huskies": "Connecticut",
    "Delaware Fightin' Blue Hens": "Delaware",
    "Duke Blue Devils": "Duke",
    "East Carolina Pirates": "East Carolina",
    "Eastern Michigan Eagles": "Eastern Michigan",
    "Florida Atlantic Owls": "Florida Atlantic",
    "Florida Gators": "Florida",
    "Florida International Panthers": "FIU",
    "Florida State Seminoles": "Florida State",
    "Fresno State Bulldogs": "Fresno State",
    "Georgia Bulldogs": "Georgia",
    "Georgia Southern Eagles": "Georgia Southern",
    "Georgia State Panthers": "Georgia State",
    "Georgia Tech Yellow Jackets": "Georgia Tech",
    "Hawaii Rainbow Warriors": "Hawaii",
    "Houston Cougars": "Houston",
    "Illinois Fighting Illini": "Illinois",
    "Indiana Hoosiers": "Indiana",
    "Iowa Hawkeyes": "Iowa",
    "Iowa State Cyclones": "Iowa State",
    "Jacksonville State Gamecocks": "Jacksonville State",
    "James Madison Dukes": "James Madison",
    "Kansas Jayhawks": "Kansas",
    "Kansas State Wildcats": "Kansas State",
    "Kennesaw State Owls": "Kennesaw State",
    "Kent State Golden Flashes": "Kent State",
    "Kentucky Wildcats": "Kentucky",
    "Liberty Flames": "Liberty",
    "Louisiana Ragin' Cajuns": "Louisiana",
    "Louisiana Tech Bulldogs": "Louisiana Tech",
    "Louisiana-Monroe Warhawks": "Louisiana-Monroe",
    "Louisville Cardinals": "Louisville",
    "LSU Tigers": "LSU",
    "Marshall Thundering Herd": "Marshall",
    "Maryland Terrapins": "Maryland",
    "Massachusetts Minutemen": "UMass",
    "Memphis Tigers": "Memphis",
    "Miami Hurricanes": "Miami FL",
    "Miami (Ohio) RedHawks": "Miami OH",
    "Michigan Wolverines": "Michigan",
    "Michigan State Spartans": "Michigan State",
    "Middle Tennessee Blue Raiders": "Middle Tennessee",
    "Minnesota Golden Gophers": "Minnesota",
    "Mississippi Rebels": "Ole Miss",
    "Mississippi State Bulldogs": "Mississippi State",
    "Missouri Tigers": "Missouri",
    "Missouri State Bears": "Missouri State",
    "Navy Midshipmen": "Navy",
    "Nebraska Cornhuskers": "Nebraska",
    "Nevada Wolf Pack": "Nevada",
    "New Mexico Lobos": "New Mexico",
    "New Mexico State Aggies": "New Mexico State",
    "North Carolina Tar Heels": "North Carolina",
    "North Carolina State Wolfpack": "NC State",
    "North Dakota State Bison": "North Dakota State",
    "North Texas Mean Green": "North Texas",
    "Northern Illinois Huskies": "Northern Illinois",
    "Northwestern Wildcats": "Northwestern",
    "Notre Dame Fighting Irish": "Notre Dame",
    "Ohio Bobcats": "Ohio",
    "Ohio State Buckeyes": "Ohio State",
    "Ohio State": "Ohio State",
    "Oklahoma Sooners": "Oklahoma",
    "Oklahoma State Cowboys": "Oklahoma State",
    "Old Dominion Monarchs": "Old Dominion",
    "Oregon Ducks": "Oregon",
    "Oregon State Beavers": "Oregon State",
    "Penn State Nittany Lions": "Penn State",
    "Pittsburgh Panthers": "Pittsburgh",
    "Purdue Boilermakers": "Purdue",
    "Rice Owls": "Rice",
    "Rutgers Scarlet Knights": "Rutgers",
    "Sacramento State Hornets": "Sacramento State",
    "Sam Houston Bearkats": "Sam Houston",
    "San Diego State Aztecs": "San Diego State",
    "San Jose State Spartans": "San Jose State",
    "SMU Mustangs": "SMU",
    "South Alabama Jaguars": "South Alabama",
    "South Carolina Gamecocks": "South Carolina",
    "South Florida Bulls": "South Florida",
    "Southern Miss Golden Eagles": "Southern Miss",
    "Stanford Cardinal": "Stanford",
    "Syracuse Orange": "Syracuse",
    "TCU Horned Frogs": "TCU",
    "Temple Owls": "Temple",
    "Tennessee Volunteers": "Tennessee",
    "Texas Longhorns": "Texas",
    "Texas A&M Aggies": "Texas A&M",
    "Texas State Bobcats": "Texas State",
    "Texas Tech Red Raiders": "Texas Tech",
    "Toledo Rockets": "Toledo",
    "Troy Trojans": "Troy",
    "Tulane Green Wave": "Tulane",
    "Tulsa Golden Hurricane": "Tulsa",
    "UAB Blazers": "UAB",
    "UCLA Bruins": "UCLA",
    "UNLV Rebels": "UNLV",
    "USC Trojans": "USC",
    "Utah Utes": "Utah",
    "Utah State Aggies": "Utah State",
    "UTEP Miners": "UTEP",
    "UTSA Roadrunners": "UTSA",
    "Vanderbilt Commodores": "Vanderbilt",
    "Virginia Cavaliers": "Virginia",
    "Virginia Tech Hokies": "Virginia Tech",
    "Wake Forest Demon Deacons": "Wake Forest",
    "Washington Huskies": "Washington",
    "Washington State Cougars": "Washington State",
    "West Virginia Mountaineers": "West Virginia",
    "Western Kentucky Hilltoppers": "Western Kentucky",
    "Western Michigan Broncos": "Western Michigan",
    "Wisconsin Badgers": "Wisconsin",
    "Wyoming Cowboys": "Wyoming",
}

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def load_site_teams():
    teams = set()

    for p in TEAM_SOURCE_CANDIDATES:
        if not p.exists():
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue

        for col in ["team", "home_team", "away_team", "Team"]:
            if col in df.columns:
                teams.update(str(x).strip() for x in df[col].dropna().unique() if str(x).strip())

    html = Path("index.html")
    if html.exists():
        txt = html.read_text(errors="ignore")
        m = re.search(r'<script id="db" type="application/json">(.*?)</script>', txt, flags=re.S)
        if m:
            try:
                db = json.loads(m.group(1))
                for key, val in db.items():
                    if isinstance(val, list):
                        for row in val:
                            if isinstance(row, dict):
                                for col in ["team", "home_team", "away_team"]:
                                    if row.get(col):
                                        teams.add(str(row[col]).strip())
            except Exception:
                pass

    return sorted(teams)

def best_match(our, site_teams):
    if our in MANUAL:
        return MANUAL[our], 1.0, "manual"

    n = norm(our)
    best = ("", 0.0)

    for st in site_teams:
        score = SequenceMatcher(None, n, norm(st)).ratio()
        if score > best[1]:
            best = (st, score)

    return best[0], best[1], "fuzzy"

def main():
    if not IMPORTANCE.exists():
        raise SystemExit(f"Missing {IMPORTANCE}")

    imp = pd.read_csv(IMPORTANCE)
    ourlads = set(imp["team"].dropna().astype(str).str.strip().unique())

    if MISSING.exists():
        miss = pd.read_csv(MISSING)
        if "team" in miss.columns:
            ourlads.update(miss["team"].dropna().astype(str).str.strip().unique())

    site_teams = load_site_teams()

    rows = []
    for team in sorted(ourlads):
        site_team, score, method = best_match(team, site_teams)
        rows.append({
            "ourlads_team": team,
            "site_team": site_team,
            "match_score": round(score, 3),
            "method": method,
            "needs_review": bool(method != "manual" and score < 0.90),
        })

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print("ourlads teams:", len(out))
    print("site teams loaded:", len(site_teams))
    print("needs review:", int(out["needs_review"].sum()))
    print("wrote:", OUT)

    review = out[out["needs_review"]].copy()
    if not review.empty:
        print("\nREVIEW")
        print(review.to_string(index=False))

if __name__ == "__main__":
    main()
