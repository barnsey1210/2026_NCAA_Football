#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")
assert "function shadowMissingLabel" in p
assert "Awaiting game" in p
assert "Unavailable" in p
assert "shadow_display_ready===true" in p
assert "fcs_excluded||s.fbs_matchup===false" in p
print("PASS: Openers shadow unavailable labels v3")
