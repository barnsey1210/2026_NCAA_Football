#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
page = ROOT / "schedule_v2.html"
text = page.read_text(encoding="utf-8", errors="ignore")

for token in [
    "function kickoffFor(r)",
    "kickoff_utc",
    "kickoff_raw",
    "kickoff_et",
    "America/New_York",
    "ET</span>",
]:
    assert token in text, f"Missing {token}"

print("PASS: Schedule kickoff rendering v2")
print("The renderer now reads enriched kickoff fields and formats them in Eastern Time.")
