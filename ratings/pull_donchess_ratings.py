#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

OUTDIR = Path("data/ratings/external_sources")
OUTDIR.mkdir(parents=True, exist_ok=True)

URL = "https://www.dratings.com/sports/ncaa-fbs-football-ratings/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

TEAM_SUFFIXES = [
    "Hoosiers","Ducks","Buckeyes","Red Raiders","Bulldogs","Fighting Irish",
    "Hurricanes","Rebels","Crimson Tide","Utes","Aggies","Tigers","Longhorns",
    "Cougars","Nittany Lions","Volunteers","Sooners","Wolverines","Trojans",
    "Gamecocks","Gators","Commodores","Seminoles","Cardinals","Mustangs",
    "Yellow Jackets","Hokies","Wildcats","Hawkeyes","Horned Frogs","Bears",
    "Huskies","Cyclones","Spartans","Cavaliers","Orange","Razorbacks",
    "Golden Gophers","Demon Deacons","Bruins","Wolfpack","Jayhawks","Panthers",
    "Bearcats","Terrapins","Sun Devils","Knights","Buffaloes","Mountaineers",
    "Badgers","Scarlet Knights","Fighting Illini","Tar Heels","Cowboys",
    "Pirates","Green Wave","Owls","Blazers","Roadrunners","Black Knights",
    "Midshipmen","Broncos","Aztecs","Rams","Beavers","Cougars","Bobcats",
    "Red Wolves","Eagles","Ragin' Cajuns","Thundering Herd","Monarchs",
    "Jaguars","Golden Eagles","Warhawks","Flames","Blue Hens","Panthers",
    "Gamecocks","Owls","Blue Raiders","Bears","Hilltoppers","Miners",
    "Bison","Falcons","Rainbow Warriors","Lobos","Wolf Pack","Rebels",
    "Spartans","Cowboys","Zips","Cardinals","Falcons","Bulls","Chippewas",
    "Eagles","Golden Flashes","RedHawks","Bobcats","Rockets","Broncos"
]

TEAM_ALIASES = {
    "California Golden": "California",
    "Charlotte 49ers": "Charlotte",
    "Coastal Carolina Chanticleers": "Coastal Carolina",
    "Delaware Fightin'": "Delaware",
    "Duke Blue Devils": "Duke",
    "FIU": "Florida International",
    "MTSU": "Middle Tennessee",
    "Massachusetts Minutemen": "Massachusetts",
    "Miami (OH)": "Miami-OH",
    "Nebraska Cornhuskers": "Nebraska",
    "Purdue Boilermakers": "Purdue",
    "Sam Houston State Bearkats": "Sam Houston",
    "Stanford Cardinal": "Stanford",
    "Tulsa Golden Hurricane": "Tulsa",
    "James Madison Dukes": "James Madison",
    "North Texas Mean Green": "North Texas",
    "Miami Hurricanes": "Miami-FL",
    "Georgia Tech Yellow Jackets": "Georgia Tech",
    "Ole Miss Rebels": "Ole Miss",
    "NC State Wolfpack": "NC State",
    "UCF Knights": "Central Florida",
    "USC Trojans": "USC",
    "SMU Mustangs": "SMU",
    "TCU Horned Frogs": "TCU",
    "BYU Cougars": "BYU",
    "UTSA Roadrunners": "UTSA",
    "UAB Blazers": "UAB",
    "UNLV Rebels": "UNLV",
    "UTEP Miners": "UTEP",
    "ULM Warhawks": "UL-Monroe",
    "Louisiana Ragin' Cajuns": "Louisiana",
    "JMU Dukes": "James Madison",
    "Sacramento State Hornets": "Sacramento State",
}

def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def clean_rating(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None

def parse_rank_team(value):
    s = str(value or "").strip()
    # "1. Indiana Hoosiers (16-0)"
    rank = None
    m = re.match(r"^\s*(\d+)\.\s*(.*?)\s*(?:\([^)]*\))?\s*$", s)
    if m:
        rank = int(m.group(1))
        team_full = m.group(2).strip()
    else:
        team_full = re.sub(r"\([^)]*\)", "", s).strip()

    team = TEAM_ALIASES.get(team_full)
    if team:
        return rank, team, team_full

    # Remove common mascot suffixes, then run aliases again on the stripped base.
    for suffix in sorted(TEAM_SUFFIXES, key=len, reverse=True):
        if team_full.endswith(" " + suffix):
            base = team_full[:-(len(suffix)+1)].strip()
            base = TEAM_ALIASES.get(base, base)
            return rank, base, team_full

    team_full = TEAM_ALIASES.get(team_full, team_full)
    return rank, team_full, team_full

def main():
    r = requests.get(URL, headers=HEADERS, timeout=45)
    print("GET", r.status_code, URL)
    r.raise_for_status()

    raw_path = OUTDIR / "donchess_raw.html"
    raw_path.write_text(r.text, encoding="utf-8")

    tables = pd.read_html(r.text)
    if not tables:
        raise SystemExit("No tables found")

    df = tables[0].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df.to_csv(OUTDIR / "donchess_table_0.csv", index=False)

    rows = []
    for _, row in df.iterrows():
        rank, team, raw_team = parse_rank_team(row.get("Rank"))

        if not team or str(team).lower() == "nan":
            continue

        rows.append({
            "snapshot_date": datetime.now().date().isoformat(),
            "season": 2026,
            "source": "Donchess",
            "team": team,
            "raw_team": raw_team,
            "rank": rank,
            "rating": clean_rating(row.get("Overall")),
            "standard_rating": clean_rating(row.get("Standard (Rank)")),
            "inference_rating": clean_rating(row.get("Inference (Rank)")),
            "vegas_rating": clean_rating(row.get("Vegas (Rank)")),
            "sos": clean_rating(row.get("SOS (Rank)")),
            "source_url": URL,
            "pulled_at": now_utc(),
            "notes": "DRatings NCAA FBS ratings table; rating=Overall",
        })

    out = pd.DataFrame(rows)
    out_path = OUTDIR / "donchess_latest.csv"
    out.to_csv(out_path, index=False)

    print("Rows:", len(out))
    print(out.head(20).to_string(index=False))
    print("Wrote:", out_path)

if __name__ == "__main__":
    main()
