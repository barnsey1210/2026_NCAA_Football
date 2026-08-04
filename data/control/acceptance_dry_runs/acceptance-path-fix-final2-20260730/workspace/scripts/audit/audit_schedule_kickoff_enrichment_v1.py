#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path.home() / "NCAAF_AUTO"
path = ROOT / "data/site/schedule_live_enrichment.json"
data = json.loads(path.read_text())
meta = data.get("kickoff_enrichment", {})

assert meta.get("games") == len(data.get("games", []))
assert "games_with_kickoff" in meta
assert "games_tbd" in meta
assert meta.get("timezone_display") == "America/New_York"

print("PASS: Schedule kickoff enrichment v1")
print(json.dumps(meta, indent=2))
