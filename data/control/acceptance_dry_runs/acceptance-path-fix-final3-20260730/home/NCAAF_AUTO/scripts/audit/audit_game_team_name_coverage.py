#!/usr/bin/env python3
"""Summarize game teams that do not exactly match DB.teams names."""
from __future__ import annotations
import csv, json, re
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
INDEX_PATH = ROOT / "index.html"
OUT_DIR = ROOT / "data" / "audits"
OUT = OUT_DIR / "game_team_name_coverage_audit.csv"

html = INDEX_PATH.read_text(errors="ignore")
m = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
if not m:
    raise SystemExit("ERROR: embedded DB not found in index.html")
db = json.loads(m.group(1))
team_set = {str(t.get("team", "")) for t in db.get("teams", []) if t.get("team")}
missing = Counter()
examples = {}

for g in db.get("games", []) or []:
    for side in ["away_team", "home_team"]:
        team = str(g.get(side) or "")
        if team and team not in team_set:
            missing[team] += 1
            examples.setdefault(team, f"{g.get('date','')} W{g.get('week',g.get('cfbd_week',''))}: {g.get('away_team')} at {g.get('home_team')}")

OUT_DIR.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["missing_team_name", "games", "example"])
    w.writeheader()
    for team, count in missing.most_common():
        w.writerow({"missing_team_name": team, "games": count, "example": examples.get(team, "")})

print(f"wrote: {OUT}")
print(f"missing unique team names: {len(missing)}")
for team, count in missing.most_common(30):
    print(f"{team}: {count} | {examples.get(team,'')}")
