#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "build/public_site"
issues = []

for page in ("index.html","matchups.html","schedule.html","conferences.html","team.html","betting.html"):
    path = PUBLIC / page
    if not path.exists():
        continue
    text = path.read_text(errors="ignore")
    if "matchup.html?game_id=" in text:
        issues.append(f"standalone matchup route remains in {page}")
    if "matchups.html?game_id=" in text:
        issues.append(f"legacy matchups route remains in {page}")

home = PUBLIC / "index.html"
if home.exists() and "openers.html?game_id=" not in home.read_text(errors="ignore"):
    issues.append("Home does not route games to the canonical Openers drawer")

matchups = PUBLIC / "matchups.html"
if matchups.exists():
    text = matchups.read_text(errors="ignore")
    if 'onclick="openDrawer(\'${r.game.game_id}\')"' in text:
        issues.append("Matchups rows still invoke the old Matchups drawer")
    if "openers.html?game_id=" not in text:
        issues.append("Matchups rows do not route to the canonical Openers drawer")

openers = PUBLIC / "openers.html"
if not openers.exists() or openers.stat().st_size < 1000:
    issues.append("canonical Openers page missing or too small")
else:
    text = openers.read_text(errors="ignore")
    for marker in ("function drawerMarkup(r)", "function openDrawer(id)", "new URLSearchParams(location.search).get('game_id')"):
        if marker not in text:
            issues.append(f"Openers canonical drawer marker missing: {marker}")

renderer = PUBLIC / "matchup_workspace.js"
if not renderer.exists():
    issues.append("canonical rich matchup renderer is missing")
else:
    renderer_text = renderer.read_text(errors="ignore")

    if renderer.stat().st_size < 50000:
        issues.append(
            f"canonical matchup renderer is unexpectedly small: "
            f"{renderer.stat().st_size} bytes"
        )

    required_renderer_markers = (
        "function fiveFactorTable",
        "function marketCards",
        "function injuries",
        "function coachingDetail",
        "function spotsTable",
        "function render(game, history, section)",
        "window.openMatchupWorkspace=open",
        "window.openDrawer=open",
    )

    for marker in required_renderer_markers:
        if marker not in renderer_text:
            issues.append(
                f"canonical rich matchup renderer marker missing: {marker}"
            )

print(json.dumps({"status":"PASS" if not issues else "FAIL","issues":issues}, indent=2))
if issues:
    raise SystemExit(1)
