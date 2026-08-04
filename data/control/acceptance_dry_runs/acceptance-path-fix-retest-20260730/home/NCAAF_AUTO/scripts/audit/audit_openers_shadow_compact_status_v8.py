#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")
for token in (
    'id="shadowCoverageStatus"',
    "shadow ready",
    'id="openers-shadow-compact-status-css-v8"',
    "title=\"${esc(a)}\"",
):
    assert token in p, f"Missing {token}"
assert "<th>Status</th>" not in p
print("PASS: Openers shadow compact impacts/status v8")
