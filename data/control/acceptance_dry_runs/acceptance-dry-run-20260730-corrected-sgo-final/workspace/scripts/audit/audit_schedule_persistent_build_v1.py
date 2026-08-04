#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
builder = ROOT / "scripts/site/build_public_site.py"
persistent = ROOT / "scripts/site/build_schedule_persistent.py"
schedule = ROOT / "schedule_v2.html"
shadow_pipeline = ROOT / "scripts/site/build_market_shadow_production_layer.py"

for path in (builder, persistent, schedule):
    assert path.exists(), f"Missing {path}"

builder_text = builder.read_text(encoding="utf-8", errors="ignore")
persistent_text = persistent.read_text(encoding="utf-8", errors="ignore")
schedule_text = schedule.read_text(encoding="utf-8", errors="ignore")

assert builder_text.count("# SCHEDULE_PERSISTENT_PUBLIC_SYNC_START") == 1
assert builder_text.count("# SCHEDULE_PERSISTENT_PUBLIC_SYNC_END") == 1
assert "build_schedule_persistent.py" in builder_text

for token in [
    "Spread Impact",
    "Total Impact",
    "Next Week",
    "Data Status",
    "scheduleHeaderTipV12",
    "scheduleNativeDetail",
]:
    assert token in schedule_text, f"Schedule source missing {token}"

for token in [
    "Historical Saturday Shadow Replay",
    "Spread CLV",
    "Total CLV",
    "matchup_workspace.js",
    "MARKET_SHADOW_LAYER_START",
    "SCHEDULE_LIVE_SCOREBOARD_START",
]:
    assert token not in schedule_text, f"Legacy Schedule token remains: {token}"

assert "schedule_live_enrichment.json" in persistent_text
assert "schedule.html" in persistent_text

if shadow_pipeline.exists():
    shadow_text = shadow_pipeline.read_text(encoding="utf-8", errors="ignore")
    assert "inject_market_shadow_panels.py" not in shadow_text

print("PASS: Schedule persistent build v1")
print("Canonical source:", schedule)
print("Persistent builder:", persistent)
print("Public build hook:", builder)
