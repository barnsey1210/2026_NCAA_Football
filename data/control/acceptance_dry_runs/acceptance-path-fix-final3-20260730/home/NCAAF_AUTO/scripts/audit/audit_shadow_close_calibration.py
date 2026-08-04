#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path.home()/"NCAAF_AUTO"
out=ROOT/"data/research/shadow_close_calibration/summary.json"
assert out.exists(), f"Missing {out}"
data=json.loads(out.read_text())
assert data["research_priority"]["primary"].startswith("predict the next closing")
assert data["definitions"]["saturday_shadow_line"]
assert data["market_repricing_validation"]["spread"]["status"]=="ok"
print("PASS: closing-line-first shadow research")
print("official blend history audit:", data["official_blend_history_audit"]["status"])
