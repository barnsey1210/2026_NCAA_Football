#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")
for token in (
    "visible games have Shadow updates",
    "Spread<br>impact",
    "Total<br>impact",
    'id="openers-shadow-width-status-css-v9"',
    "960px",
    "postgame updates",
):
    assert token in p, f"Missing {token}"
print("PASS: Openers shadow width/status v9")
