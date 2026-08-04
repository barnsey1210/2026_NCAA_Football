#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
page = ROOT / "schedule_v2.html"
text = page.read_text(encoding="utf-8", errors="ignore")

for token in [
    "function scheduleLookupKeys(r)",
    "id:${String(g.game_id)}",
    "match:${date}|${away}|${home}",
    "cache:'no-store'",
    "schedule_live_enrichment.json?v=${Date.now()}",
]:
    assert token in text, f"Missing {token}"

print("PASS: Schedule kickoff lookup/cache v4")
print("Lookup now supports game ID and matchup fallback, with JSON cache disabled.")
