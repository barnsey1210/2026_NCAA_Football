#!/usr/bin/env python3
from pathlib import Path
import csv
import json

ROOT = Path.home() / "NCAAF_AUTO"
manifest_paths = sorted(
    ROOT.glob("data/replay/cfbd_shadow/**/*_manifest.json"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
if not manifest_paths:
    raise SystemExit("No replay manifest found.")

manifest = json.loads(manifest_paths[0].read_text())
gid = str(manifest["game_id"])
teams = {manifest["away_team"], manifest["home_team"]}

print("REPLAY GAME:", gid, manifest["away_team"], "at", manifest["home_team"])

files = [
    ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024/holdout_2025_predictions.csv",
    ROOT / "data/research/postgame_total_market_update_2021_2025/modeling_rows.csv",
]

for path in files:
    print("\nFILE:", path)
    if not path.exists():
        print("MISSING")
        continue

    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        print("COLUMNS:")
        print(fields)

        exact = []
        team_rows = []
        for row in reader:
            values = {str(v) for v in row.values() if v is not None}
            if gid in values:
                exact.append(row)
            row_teams = {
                row.get("team"),
                row.get("home_team"),
                row.get("away_team"),
                row.get("home_prior_team"),
                row.get("away_prior_team"),
            }
            if teams & {x for x in row_teams if x}:
                team_rows.append(row)

        print("EXACT ROWS CONTAINING GAME ID:", len(exact))
        for row in exact[:10]:
            print(json.dumps(row, indent=2)[:8000])

        print("TEAM ROWS:", len(team_rows))
        for row in team_rows[:3]:
            print(json.dumps(row, indent=2)[:4000])

print("\nInterpretation:")
print("- Spread replay must match both exact completed game_id and team.")
print("- Total replay must identify the next-game modeling row whose prior-game id equals the replay game.")
print("- Do not trust predictions selected only by team name.")
