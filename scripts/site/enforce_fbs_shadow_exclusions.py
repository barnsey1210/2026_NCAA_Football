#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
INDEX = ROOT / "v1.html"
TARGETS = [
    ROOT / "data/site/schedule_live_enrichment.json",
    ROOT / "data/site/saturday_shadow_lines.json",
]

ALIASES = {
    "uconn": "connecticut",
    "massachusetts": "umass",
    "appalachian state": "app state",
    "southern california": "usc",
    "central florida": "ucf",
    "texas san antonio": "utsa",
    "texas el paso": "utep",
    "louisiana state": "lsu",
    "brigham young": "byu",
    "southern methodist": "smu",
    "texas christian": "tcu",
    "florida international": "fiu",
    "florida atlantic": "fau",
}

NULL_FIELDS = [
    "spread_impact","total_impact",
    "away_spread_impact","home_spread_impact",
    "away_total_impact","home_total_impact",
    "raw_spread_delta","raw_total_delta",
    "next_projection_spread","next_projection_total",
    "shadow_home_spread","shadow_total",
]

def norm(v):
    s = str(v or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\s+", " ", s)
    return ALIASES.get(s, s)

def load_fbs():
    text = INDEX.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<script[^>]+id=["\']db["\'][^>]*>(.*?)</script>', text, re.S|re.I)
    if not m:
        raise RuntimeError("Could not locate embedded DB in v1.html")
    data = json.loads(m.group(1))
    teams = {norm(x.get("team")) for x in data.get("teams", []) if x.get("team")}
    if len(teams) < 130:
        raise RuntimeError(f"FBS membership unexpectedly small: {len(teams)}")
    return teams

def sanitize(path, teams):
    if not path.exists():
        return 0
    data = json.loads(path.read_text())
    rows = data.get("games", data if isinstance(data, list) else [])
    if not isinstance(rows, list):
        return 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        game = row.get("game", row)
        away = norm(game.get("away_team") or row.get("away_team"))
        home = norm(game.get("home_team") or row.get("home_team"))
        is_fbs = bool(away and home and away in teams and home in teams)
        row["fbs_matchup"] = is_fbs
        row["fcs_excluded"] = not is_fbs
        if isinstance(game, dict):
            game["fbs_matchup"] = is_fbs
            game["fcs_excluded"] = not is_fbs
        if not is_fbs:
            for field in NULL_FIELDS:
                if field in row:
                    row[field] = None
                if isinstance(game, dict) and field in game:
                    game[field] = None
            row["data_status"] = "Excluded — FCS matchup"
            row["spread_status"] = "Excluded — FCS matchup"
            row["total_status"] = "Excluded — FCS matchup"
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    return len(rows)

def main():
    teams = load_fbs()
    print({"fbs_teams": len(teams), "rows": {str(p.relative_to(ROOT)): sanitize(p, teams) for p in TARGETS}})

if __name__ == "__main__":
    main()
