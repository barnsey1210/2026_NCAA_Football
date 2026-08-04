#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")
for token in (
    "SHADOW_AVAILABLE=false",
    "completed_team_update_count",
    "Saturday Shadow · Awaiting completed games · 0 postgame updates",
    "Awaiting completed game",
    "postgame_shadow_updates.json",
    "shadowButton.disabled=false",
    "shadow_display_ready===true",
):
    assert token in p, f"Missing {token}"
print("PASS: Openers shadow preseason gating v4")
