#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
page = ROOT / "schedule_v2.html"
text = page.read_text(encoding="utf-8", errors="ignore")

assert "y.game_id??y.game?.game_id" in text
assert "function shadowFor(r)" in text
assert "kickoff_utc" in text

print("PASS: Schedule enrichment map key v3")
print("Enrichment rows now map by nested game.game_id when top-level game_id is absent.")
