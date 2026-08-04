#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")
for token in (
    'id="projectionMode"',
    "projectionMode='standard'",
    "data/site/saturday_shadow_lines.json",
    "function activeHomeSpread",
    "function activeTotal",
    "saturday_shadow_spread",
    "saturday_shadow_total",
    "fcs_excluded",
    'data-projection-mode="shadow"',
):
    assert token in p, f"Missing {token}"
assert "Promise.all" in p
print("PASS: Openers Standard/Shadow toggle v2")
