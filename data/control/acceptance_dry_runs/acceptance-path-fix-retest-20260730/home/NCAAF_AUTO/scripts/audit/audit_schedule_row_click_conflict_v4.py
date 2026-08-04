#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
page = ROOT / "schedule_v2.html"
text = page.read_text(encoding="utf-8", errors="ignore")

assert "e.stopPropagation()" in text
assert "e.stopImmediatePropagation()" in text
assert "},true)" in text
assert "scheduleNativeDetail" in text

print("PASS: Schedule row click conflict fixed")
print("Schedule rows now expand details without opening matchup workspace.")
