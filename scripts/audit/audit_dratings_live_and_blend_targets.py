#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path("/Users/jameslindesmith/NCAAF_MAIN_REPO")

TARGETS = [
    "scripts/projections/build_game_projection_sources_2026.py",
    "scripts/projections/build_game_projection_blend_2026.py",
    "data/projections/game_projection_blend_config.json",
    "data/ratings/external_sources/dratings_ncaaf_predictions_latest.csv",
]

def section(title):
    print("\n" + "=" * 110)
    print(title)
    print("=" * 110)

section("TARGET FILE PRESENCE")
for rel in TARGETS:
    p = ROOT / rel
    print(f"{rel}: {'YES' if p.exists() else 'NO'}"
          + (f" ({p.stat().st_size:,} bytes)" if p.exists() else ""))

section("DRATINGS-RELATED FILES")
r = subprocess.run(
    ["find", ".", "-type", "f", "-iname", "*drating*", "-o", "-iname", "*dratings*"],
    cwd=ROOT, text=True, capture_output=True
)
print(r.stdout or "(none)")

section("DRATINGS REFERENCES IN CODE")
r = subprocess.run(
    ["grep", "-RIn", "--exclude-dir=.git", "--exclude=*.bak",
     "dratings", "scripts", "ratings", "data/projections", "config"],
    cwd=ROOT, text=True, capture_output=True
)
print((r.stdout or "(none)")[:40000])

section("PROJECTION SOURCE BUILDER")
p = ROOT / "scripts/projections/build_game_projection_sources_2026.py"
if p.exists():
    print(p.read_text(errors="replace"))

section("PROJECTION BLEND BUILDER")
p = ROOT / "scripts/projections/build_game_projection_blend_2026.py"
if p.exists():
    print(p.read_text(errors="replace"))

section("BLEND CONFIG")
p = ROOT / "data/projections/game_projection_blend_config.json"
if p.exists():
    print(p.read_text(errors="replace"))
else:
    print("MISSING")

section("CURRENT DRATINGS CANONICAL OUTPUT")
p = ROOT / "data/ratings/external_sources/dratings_ncaaf_predictions_latest.csv"
if p.exists():
    lines = p.read_text(errors="replace").splitlines()
    print("rows excluding header:", max(0, len(lines)-1))
    for line in lines[:15]:
        print(line)
else:
    print("MISSING")

section("CURRENT PROJECTION SOURCES SAMPLE")
p = ROOT / "data/projections/game_projection_sources_2026.csv"
if p.exists():
    lines = p.read_text(errors="replace").splitlines()
    print("rows excluding header:", max(0, len(lines)-1))
    for line in lines[:15]:
        print(line)
else:
    print("MISSING")

section("CURRENT PROJECTION BLEND SAMPLE")
p = ROOT / "data/projections/game_projection_blend_2026.csv"
if p.exists():
    lines = p.read_text(errors="replace").splitlines()
    print("rows excluding header:", max(0, len(lines)-1))
    for line in lines[:10]:
        print(line)
else:
    print("MISSING")

section("TARGET CONTRACT")
print(json.dumps({
    "spread_current_state": {
        "active_sources": ["SP+", "FPI", "TeamRankings", "DRatings"],
        "weights": {
            "SP+": 0.25,
            "FPI": 0.25,
            "TeamRankings": 0.25,
            "DRatings": 0.25,
            "Sagarin": 0.0
        },
        "label": "4/5 ACTIVE"
    },
    "spread_future_state": {
        "active_sources": ["SP+", "FPI", "TeamRankings", "DRatings", "Sagarin"],
        "weights": {
            "SP+": 0.20,
            "FPI": 0.20,
            "TeamRankings": 0.20,
            "DRatings": 0.20,
            "Sagarin": 0.20
        },
        "label": "5/5 ACTIVE"
    },
    "total_current_state": {
        "active_sources": ["SP+", "DRatings"],
        "weights": {
            "SP+": 0.50,
            "DRatings": 0.50
        },
        "label": "2-SOURCE TOTAL"
    },
    "Brad Powers": "display/individual tracking only; zero production spread weight"
}, indent=2))

print("\nRead-only audit complete. No files were changed.")
