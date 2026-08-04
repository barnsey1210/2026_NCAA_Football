#!/usr/bin/env python3
from pathlib import Path

ROOT=Path.home()/"NCAAF_AUTO"
page=(ROOT/"schedule_v2.html").read_text(encoding="utf-8",errors="ignore")
builder=(ROOT/"scripts/site/build_schedule_live_enrichment.py").read_text(encoding="utf-8",errors="ignore")

for token in [
 "Spread Impact","Total Impact","Next Week","Data Status",
 "scheduleImpactPairV11","scheduleNextWeekV11","scheduleTip",
 "openers_v2.html?week=","view=shadow"
]:
    assert token in page,f"Missing {token}"

assert "Spread CLV" not in page
assert "Total CLV" not in page
assert "away_spread_impact" in builder
assert "home_spread_impact" in builder

print("PASS: Schedule impacts and next-week links v11")
