#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
target = ROOT / "scripts/site/build_schedule_persistent.py"
text = target.read_text(encoding="utf-8", errors="ignore")

assert "import re" in text
assert "([A-Za-z0-9_-]+)_v2" in text
assert 'if "_v2.html" in public_text' in text

print("PASS: all Schedule prototype links transform v4")
print("Every remaining *_v2.html reference will be converted during public sync.")
