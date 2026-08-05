#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "build/public_site"
issues: list[str] = []

router = PUBLIC / "matchup_workspace.js"
if not router.exists():
    issues.append("public canonical matchup router missing")
else:
    text = router.read_text(errors="ignore")
    for marker in ("matchup.html", "openMatchupWorkspace", "openDrawer"):
        if marker not in text:
            issues.append(f"canonical matchup router missing marker: {marker}")
    for marker in ("mwBackdrop", "mwContent", "mwShell", "render(game, history"):
        if marker in text:
            issues.append(f"legacy matchup renderer remains in router: {marker}")

for page in ("index.html", "matchups.html", "openers.html", "schedule.html",
             "conferences.html", "team.html", "betting.html"):
    path = PUBLIC / page
    if not path.exists():
        continue
    text = path.read_text(errors="ignore")
    if "matchups.html?game_id=" in text:
        issues.append(f"legacy matchup route remains: {page}")
    if "mwBackdrop" in text or 'id="mwContent"' in text:
        issues.append(f"legacy matchup overlay markup remains: {page}")

home = PUBLIC / "index.html"
if home.exists() and "matchup.html?game_id=" not in home.read_text(errors="ignore"):
    issues.append("War Room Home does not emit canonical matchup links")

canonical = PUBLIC / "matchup.html"
if not canonical.exists() or canonical.stat().st_size < 1000:
    issues.append("canonical matchup.html missing or too small")

result = {"status": "PASS" if not issues else "FAIL", "issues": issues}
print(json.dumps(result, indent=2))
if issues:
    raise SystemExit(1)
