#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
page=ROOT/"schedule_v2.html"
text=page.read_text(encoding="utf-8",errors="ignore")
checks=["Date / Time","Spread CLV","Total CLV","Spread Impact","Total Impact","Next Projection","Data Status","schedule_live_enrichment.json","scheduleNativeDetail","SCHEDULE_NATIVE_RENDERER_V3_STYLE"]
for x in checks:
    assert x in text,f"Missing {x}"
assert "Historical Saturday Shadow Replay" not in text
print("PASS: native Schedule renderer v3")
for x in checks: print(x)
