#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
target = ROOT / "scripts/site/build_schedule_persistent.py"
text = target.read_text(encoding="utf-8", errors="ignore")

assert "def publicize_schedule_html" in text
assert '"openers_v2.html": "openers.html"' in text
assert '<a class="active" href="schedule.html">Schedule</a>' in text
assert "Prototype link leaked into public Schedule page" in text

print("PASS: Schedule public-link transform v3")
print("Public schedule.html will use canonical navigation and Openers links.")
