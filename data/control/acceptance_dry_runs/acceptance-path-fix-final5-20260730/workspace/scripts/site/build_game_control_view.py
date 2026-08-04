#!/usr/bin/env python3
"""Publish completed-game NCAAF Game Control values for team schedules."""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/research/game_control_history_2026/team_game_game_control.csv"
OUTPUT = ROOT / "data/site/game_control_team_games_2026.json"
rows = []
if SOURCE.exists():
    for row in csv.DictReader(SOURCE.open(encoding="utf-8")):
        auc = float(row.get("control_auc") or row.get("raw_game_control") or .5)
        rows.append({"game_id":str(row.get("game_id") or ""), "team":row.get("team"), "opponent":row.get("opponent"),
                     "control_auc":round(auc,6), "game_control_index":round(float(row.get("game_control_index") or 100*(auc-.5)),2),
                     "play_states":int(float(row.get("play_states") or 0))})
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({"schema_version":"ncaaf-gc-index-v1","formula":"100 * (control_auc - .500)",
                              "proprietary_metric":False,"rows":rows}, indent=2)+"\n")
print(f"Wrote {len(rows)} team-game Game Control rows to {OUTPUT}")
