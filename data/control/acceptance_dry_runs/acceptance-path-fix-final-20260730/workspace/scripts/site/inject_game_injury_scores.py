#!/usr/bin/env python3
import json
import re
from pathlib import Path

import pandas as pd

INDEX = Path("index.html")
TEAM_SCORES = Path("data/injuries/team_injury_scores.csv")
GAME_ALERTS = Path("data/injuries/game_injury_alerts.csv")

def clean_records(df):
    return json.loads(df.where(pd.notnull(df), None).to_json(orient="records"))

def main():
    txt = INDEX.read_text(errors="ignore")
    m = re.search(r'(<script id="db" type="application/json">)(.*?)(</script>)', txt, flags=re.S)
    if not m:
        raise SystemExit("Could not find DB script in index.html")

    db = json.loads(m.group(2))

    team_scores = pd.read_csv(TEAM_SCORES) if TEAM_SCORES.exists() else pd.DataFrame()
    game_alerts = pd.read_csv(GAME_ALERTS) if GAME_ALERTS.exists() else pd.DataFrame()

    db["team_injury_scores"] = clean_records(team_scores) if not team_scores.empty else []
    db["game_injury_alerts"] = clean_records(game_alerts) if not game_alerts.empty else []

    alert_map = {}
    if not game_alerts.empty and "game_id" in game_alerts.columns:
        for _, r in game_alerts.iterrows():
            alert_map[str(r["game_id"])] = r.to_dict()

    updated_games = []
    for g in db.get("games", []):
        gid = str(g.get("game_id"))
        a = alert_map.get(gid, {})

        g["away_injury_score"] = a.get("away_injury_score", 0)
        g["home_injury_score"] = a.get("home_injury_score", 0)
        g["game_injury_score"] = a.get("game_injury_score", 0)
        g["game_injury_tier"] = a.get("game_injury_tier", "None")
        g["injury_edge_home"] = a.get("injury_edge_home", 0)
        g["injury_summary"] = a.get("injury_summary", "")

        updated_games.append(g)

    db["games"] = updated_games

    new_json = json.dumps(db, separators=(",", ":"), ensure_ascii=False)
    out = txt[:m.start(2)] + new_json + txt[m.end(2):]

    INDEX.write_text(out)

    print("injected team_injury_scores:", len(db["team_injury_scores"]))
    print("injected game_injury_alerts:", len(db["game_injury_alerts"]))
    print("updated games:", len(updated_games))
    print("wrote:", INDEX)

if __name__ == "__main__":
    main()
