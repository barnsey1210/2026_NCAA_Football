#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

ROOT = Path.cwd()
errors = []

legacy_scripts = {
    "injuries/pull_cfbdepth_injuries.py",
    "injuries/pull_cfbdepth_article_bodies.py",
    "scripts/injuries/build_injury_alerts.py",
    "agents/prepend_injury_alerts_to_daily_betting_angles.py",
    "injuries/build_game_injury_scores.py",
}

shell_path = ROOT / "daily_market_update.sh"
shell = shell_path.read_text()

for script in sorted(legacy_scripts):
    pattern = rf'run_py\s+"{re.escape(script)}"'
    if re.search(pattern, shell):
        errors.append(f"live orchestrator still executes: {script}")

stages_path = ROOT / "config/daily_stages.json"
stages = json.loads(stages_path.read_text())

active_stage_scripts = {
    script
    for stage in stages.get("stages", [])
    for script in stage.get("scripts", [])
}

for script in sorted(legacy_scripts):
    if script in active_stage_scripts:
        errors.append(f"daily stage manifest still activates: {script}")

if any(stage.get("id") == "injury_scores" for stage in stages.get("stages", [])):
    errors.append("legacy injury_scores stage still exists")

manifest_path = ROOT / "deploy/source_manifest.txt"
manifest = {
    line.strip()
    for line in manifest_path.read_text().splitlines()
    if line.strip()
}

for script in sorted(legacy_scripts):
    if script in manifest:
        errors.append(f"deployment manifest still includes: {script}")

status_path = ROOT / "data/injuries/injury_source_status.json"
if not status_path.exists():
    errors.append("missing data/injuries/injury_source_status.json")
else:
    status = json.loads(status_path.read_text())

    if status.get("source_state") != "SOURCE_NOT_CONFIGURED":
        errors.append("source_state must be SOURCE_NOT_CONFIGURED")

    if status.get("legacy_inputs_allowed") is not False:
        errors.append("legacy_inputs_allowed must be false")

    if status.get("coverage_state") != "UNAVAILABLE":
        errors.append("coverage_state must be UNAVAILABLE")

active_consumers = {
    "scripts/site/build_matchups_view.py": {
        "data/injuries/injury_events_normalized.csv",
        "data/rosters/player_importance_2026_normalized.csv",
    },
    "scripts/site/build_page_health_status.py": {
        "data/injuries/injury_events_normalized.csv",
        "data/injuries/injury_alerts.csv",
        "data/injuries/team_injury_scores.csv",
        "data/injuries/game_injury_alerts.csv",
    },
}

for relative_path, forbidden_inputs in active_consumers.items():
    consumer_path = ROOT / relative_path
    if not consumer_path.is_file():
        errors.append(f"missing active consumer: {relative_path}")
        continue

    consumer_text = consumer_path.read_text()
    for forbidden_input in sorted(forbidden_inputs):
        if forbidden_input in consumer_text:
            errors.append(
                f"active consumer {relative_path} still reads legacy input: "
                f"{forbidden_input}"
            )

if errors:
    print("INJURY LEGACY ISOLATION: FAIL")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("INJURY LEGACY ISOLATION: PASS")
