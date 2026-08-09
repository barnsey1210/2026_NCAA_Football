#!/usr/bin/env python3
"""Validate the current canonical matchup routing contract."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "build/public_site"
issues = []

PAGES = (
    "index.html",
    "matchups.html",
    "schedule.html",
    "conferences.html",
    "team.html",
    "betting.html",
    "openers.html",
    "matchup.html",
)

texts = {}
for page in PAGES:
    path = PUBLIC / page
    if not path.exists():
        issues.append(f"canonical public page missing: {page}")
        texts[page] = ""
        continue
    texts[page] = path.read_text(errors="ignore")

matchup = PUBLIC / "matchup.html"
if matchup.exists():
    if matchup.stat().st_size < 1000:
        issues.append("canonical standalone matchup page is unexpectedly small")
    text = texts["matchup.html"]
    if "game_id" not in text:
        issues.append("canonical standalone matchup page has no game_id route marker")

matchups_text = texts["matchups.html"]
if matchups_text and "matchup.html?game_id=" not in matchups_text:
    issues.append("Matchups rows do not route to canonical standalone matchup.html?game_id=...")

legacy_routes = (
    "matchups_v2.html",
    "matchup_v2.html",
    "openers_v2.html",
    "betting_v2.html",
    "team_v2.html",
)
for page, text in texts.items():
    if not text:
        continue
    for legacy in legacy_routes:
        if legacy in text:
            issues.append(f"legacy prototype route {legacy} remains in {page}")

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
    )
    for marker in required_renderer_markers:
        if marker not in renderer_text:
            issues.append(f"canonical rich matchup renderer marker missing: {marker}")

print(json.dumps({"status": "PASS" if not issues else "FAIL", "issues": issues}, indent=2))
if issues:
    raise SystemExit(1)

print("CANONICAL STANDALONE MATCHUP ROUTING AUDIT PASSED")
