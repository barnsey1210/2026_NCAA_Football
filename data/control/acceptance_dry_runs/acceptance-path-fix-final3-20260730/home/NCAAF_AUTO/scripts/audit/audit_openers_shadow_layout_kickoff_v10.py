#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")
for token in (
    "function openerDateTime",
    "America/New_York",
    "${openerDateTime(r)}",
    'id="openers-shadow-layout-kickoff-css-v10"',
    "min-width:330px",
    "table-layout:auto",
):
    assert token in p, f"Missing {token}"
print("PASS: Openers shadow layout/kickoff v10")
