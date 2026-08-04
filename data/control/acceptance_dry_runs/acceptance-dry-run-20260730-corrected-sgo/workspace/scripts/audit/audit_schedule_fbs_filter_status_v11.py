#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
page=(ROOT/"schedule_v2.html").read_text(errors="ignore")
persistent=(ROOT/"scripts/site/build_schedule_persistent.py").read_text(errors="ignore")
guard=(ROOT/"scripts/site/enforce_fbs_shadow_exclusions.py").read_text(errors="ignore")
for token in ('id="fbsOnly"','id="allGames"','fbsOnlyMode=true',"label:'Ready'","label:'Excluded'",'PREGAME READY'):
    assert token in page, f"Missing {token}"
assert "enforce_fbs_shadow_exclusions.py" in persistent
assert "fcs_excluded" in guard
print("PASS: Schedule FBS filter/status v11")
