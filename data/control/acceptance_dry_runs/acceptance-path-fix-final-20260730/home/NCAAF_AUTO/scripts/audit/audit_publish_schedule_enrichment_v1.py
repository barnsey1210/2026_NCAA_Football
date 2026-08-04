#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
script = ROOT / "scripts/publish/publish_site.sh"
text = script.read_text(encoding="utf-8", errors="ignore")

assert text.count("# SCHEDULE_ENRICHMENT_PUBLISH_START") == 1
assert text.count("# SCHEDULE_ENRICHMENT_PUBLISH_END") == 1
assert "schedule_live_enrichment.json" in text
assert 'cp -L "$SCHEDULE_ENRICHMENT_SRC" "$SCHEDULE_ENRICHMENT_DST"' in text
assert "confirmed_kickoffs" in text
assert "fbs_tagged" in text

print("PASS: Schedule enrichment publish hook v1")
print("Future publishes will include the Schedule runtime JSON.")
