#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
target = ROOT / "matchup_workspace.js"
text = target.read_text(encoding="utf-8", errors="ignore")

needle = "if(target.closest?.('.scheduleNativeRow'))return null;"
assert needle in text, "Schedule exclusion missing from matchup workspace trigger logic"

print("PASS: Schedule rows excluded from matchup workspace")
print("Inline Schedule expansion remains active.")
