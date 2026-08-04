#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
page = ROOT / "schedule_v2.html"
js = ROOT / "matchup_workspace.js"

html = page.read_text(encoding="utf-8", errors="ignore")
code = js.read_text(encoding="utf-8", errors="ignore")

assert "scheduleexclude7" in html
assert "if(target.closest?.('.scheduleNativeRow'))return null;" in code

print("PASS: Schedule matchup workspace cache bust")
print("schedule_v2.html loads the patched matchup_workspace.js URL.")
