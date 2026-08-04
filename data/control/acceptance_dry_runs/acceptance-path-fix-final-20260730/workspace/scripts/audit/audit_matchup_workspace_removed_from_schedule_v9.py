#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
page = ROOT / "schedule_v2.html"
text = page.read_text(encoding="utf-8", errors="ignore")

assert "matchup_workspace.js" not in text
assert "scheduleNativeRow" in text
assert "scheduleNativeDetail" in text

print("PASS: matchup workspace removed from Schedule page")
print("Inline Schedule expansion remains available.")
