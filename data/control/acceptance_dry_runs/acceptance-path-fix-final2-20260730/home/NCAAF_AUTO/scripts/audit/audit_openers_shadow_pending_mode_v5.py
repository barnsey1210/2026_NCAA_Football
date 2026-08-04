#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")
assert "shadowButton.disabled=false" in p
assert "Show games awaiting completed-game Shadow updates" in p
assert "if(b.dataset.projectionMode==='shadow'&&!SHADOW_AVAILABLE)return;" not in p
assert "Awaiting game" in p
assert "function shadowGapAvailable" in p
print("PASS: Openers shadow pending mode v5")
