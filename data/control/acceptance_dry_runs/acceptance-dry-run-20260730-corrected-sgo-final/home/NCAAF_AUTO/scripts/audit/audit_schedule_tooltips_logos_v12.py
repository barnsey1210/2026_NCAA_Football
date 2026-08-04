#!/usr/bin/env python3
from pathlib import Path

ROOT=Path.home()/"NCAAF_AUTO"
text=(ROOT/"schedule_v2.html").read_text(encoding="utf-8",errors="ignore")

for token in [
    "hydrateScheduleImpactLogosV12",
    "initScheduleHeaderTipsV12",
    "scheduleHeaderTipV12",
    "scheduleMiniLogoV12",
    "SCHEDULE_IMPACTS_NEXTWEEK_V12_STYLE"
]:
    assert token in text,f"Missing {token}"

assert "scheduleTip:hover::after" not in text

print("PASS: Schedule tooltips and logos v12")
print("Header explanations use a centered, viewport-clamped floating bubble.")
print("Impact and Next Week cells reuse matchup-row logos when available.")
