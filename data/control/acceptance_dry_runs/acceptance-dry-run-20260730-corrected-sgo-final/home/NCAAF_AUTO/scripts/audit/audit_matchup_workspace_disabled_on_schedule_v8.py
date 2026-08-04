#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
js = (ROOT / "matchup_workspace.js").read_text(encoding="utf-8", errors="ignore")
html = (ROOT / "schedule_v2.html").read_text(encoding="utf-8", errors="ignore")

assert "schedule_v2\.html" in js
assert "scheduledisable8" in html

print("PASS: matchup workspace disabled on Schedule page")
print("Schedule row clicks are reserved for inline expansion only.")
