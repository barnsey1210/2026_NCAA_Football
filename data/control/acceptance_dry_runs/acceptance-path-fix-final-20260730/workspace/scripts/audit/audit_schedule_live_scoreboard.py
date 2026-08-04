#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path.home()/"NCAAF_AUTO"
page=ROOT/"schedule_v2.html"; data=ROOT/"data/site/schedule_live_enrichment.json"
assert page.exists(); assert data.exists()
text=page.read_text(encoding="utf-8",errors="ignore")
assert text.count("<!-- SCHEDULE_LIVE_SCOREBOARD_START -->")==1
assert text.count("<!-- SCHEDULE_LIVE_SCOREBOARD_END -->")==1
payload=json.loads(data.read_text()); assert payload.get("games")
print("PASS: schedule live scoreboard installed")
print("games:",len(payload["games"]))
print("games with kickoff:",sum(bool(g.get("kickoff_raw")) for g in payload["games"]))
print("source hits:",payload.get("source_hits",[]))
