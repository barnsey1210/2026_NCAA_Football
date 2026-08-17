#!/usr/bin/env python3
from pathlib import Path
import subprocess
import json

ROOT = Path("/Users/jameslindesmith/NCAAF_MAIN_REPO")

TERMS = [
    "Brad Powers",
    "bradpowers",
    "spread_core_v1",
    "SP+",
    "TeamRankings",
    "Sagarin",
    "DRatings",
    "weights",
    "production_model",
]

SEARCH_DIRS = [
    "ratings",
    "scripts",
    "data/model_tracking",
    "config",
]

def section(title):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

section("CURRENT TRACKING CONFIG")
cfg = ROOT / "data/model_tracking/config.json"
if cfg.exists():
    print(cfg.read_text())
else:
    print("MISSING:", cfg)

section("PRODUCTION-BLEND REFERENCES")
for term in TERMS:
    print(f"\n--- {term} ---")
    cmd = ["grep", "-RIn", "--exclude-dir=.git", "--exclude=*.bak", term, *SEARCH_DIRS]
    r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    print((r.stdout or "(no matches)")[:30000])

section("LIKELY RATING / PROJECTION OWNERS")
for rel in [
    "scripts/projections/build_game_projection_sources_2026.py",
    "scripts/projections/build_game_projection_blend_2026.py",
    "scripts/site/build_ratings_view.py",
    "ratings/build_ratings_movement.py",
]:
    p = ROOT / rel
    print(f"\n===== {rel} =====")
    if not p.exists():
        print("MISSING")
        continue
    text = p.read_text(errors="replace")
    for i, line in enumerate(text.splitlines(), start=1):
        if any(t.lower() in line.lower() for t in [
            "brad", "sp+", "spplus", "fpi", "teamrank", "sagarin", "drating",
            "weight", "blend", "composite", "production"
        ]):
            print(f"{i}: {line}")

section("RATINGS MASTER COLUMNS")
for rel in [
    "data/ratings/ratings_master_latest.csv",
    "data/ratings/ratings_source_status.csv",
    "data/projections/game_projection_sources_2026.csv",
    "data/projections/game_projection_blend_2026.csv",
]:
    p = ROOT / rel
    print(f"\n{rel}")
    if not p.exists():
        print("MISSING")
        continue
    with p.open(errors="replace") as fh:
        print(fh.readline().rstrip())

section("DESIRED TARGET CONTRACT")
print(json.dumps({
    "production_spread_model_version": "spread_core_v2",
    "models": ["SP+", "FPI", "TeamRankings", "Sagarin", "DRatings"],
    "weights": {
        "SP+": 0.20,
        "FPI": 0.20,
        "TeamRankings": 0.20,
        "Sagarin": 0.20,
        "DRatings": 0.20
    },
    "require_all": True,
    "Brad Powers": "TRACKING_ONLY_INDIVIDUAL",
    "historical_thresholds": {
        "WATCH": "3.0-3.49",
        "ACTIONABLE": "3.5-3.99",
        "STRONG": "4.0+"
    }
}, indent=2))

print("\nRead-only audit complete. No files were changed.")
