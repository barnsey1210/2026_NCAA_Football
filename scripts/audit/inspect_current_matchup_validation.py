#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path("/Users/jameslindesmith/NCAAF_MAIN_REPO")
AUDIT = ROOT / "scripts/audit/audit_canonical_openers_drawer.py"
DAILY = ROOT / "daily_market_update.sh"

print("=== CURRENT AUDIT FILE ===")
if not AUDIT.exists():
    raise SystemExit(f"STOP: missing {AUDIT}")

text = AUDIT.read_text(errors="replace")
print(text)

print("\n=== KEY ROUTING MARKERS IN AUDIT ===")
markers = [
    "Openers drawer",
    "matchup.html",
    "matchups.html",
    "standalone",
    "legacy",
    "game_id",
]
for m in markers:
    print(f"{m!r}: {m in text}")

print("\n=== DAILY SCRIPT REFERENCES ===")
if DAILY.exists():
    for i, line in enumerate(DAILY.read_text(errors="replace").splitlines(), start=1):
        if "audit_canonical_openers_drawer.py" in line or "site_validation" in line or "audit_canonical" in line:
            print(f"{i}: {line}")
else:
    print("MISSING:", DAILY)

print("\n=== GIT STATUS FOR AUDIT ===")
import subprocess
r = subprocess.run(
    ["git", "status", "--short", "--", str(AUDIT.relative_to(ROOT))],
    cwd=ROOT, text=True, capture_output=True
)
print(r.stdout or "(clean)")

print("\nNo files were changed.")
