#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path("/Users/jameslindesmith/NCAAF_MAIN_REPO")

def section(title):
    print("\n" + "=" * 110)
    print(title)
    print("=" * 110)

section("RATINGS PAGE OWNERS")
for rel in [
    "scripts/site/build_ratings_view.py",
    "scripts/ratings/build_all_ratings_latest.py",
    "ratings/ratings_master_latest.csv",
]:
    p = ROOT / rel
    print(f"\n===== {rel} =====")
    if not p.exists():
        print("MISSING")
        continue
    if p.suffix == ".csv":
        with p.open(errors="replace") as fh:
            for _ in range(4):
                line = fh.readline()
                if not line:
                    break
                print(line.rstrip())
    else:
        text = p.read_text(errors="replace")
        for i, line in enumerate(text.splitlines(), start=1):
            if any(k in line.lower() for k in [
                "brad", "spplus", "sp+", "fpi", "teamrank", "kford",
                "power_rating", "columns", "source", "rating"
            ]):
                print(f"{i}: {line}")

section("CURRENT DRATINGS RATING REFERENCES")
r = subprocess.run(
    ["grep", "-RIn", "--exclude-dir=.git", "--exclude=*.bak",
     "ncaa-fbs-football-ratings\\|DRatings", "scripts/ratings", "ratings", "scripts/site"],
    cwd=ROOT, text=True, capture_output=True
)
print((r.stdout or "(none)")[:40000])

section("PROJECTION COVERAGE DISPLAY REFERENCES")
r = subprocess.run(
    ["grep", "-RIn", "--exclude-dir=.git", "--exclude=*.bak",
     "source_count_spread\\|source_count_total\\|spread_sources_used\\|total_sources_used",
     "scripts/site", "index.html"],
    cwd=ROOT, text=True, capture_output=True
)
print((r.stdout or "(none)")[:40000])

section("MODEL / PROJECTION DISPLAY REFERENCES")
r = subprocess.run(
    ["grep", "-RIn", "--exclude-dir=.git", "--exclude=*.bak",
     "blend_spread\\|blend_total\\|model.total\\|projected_total\\|projected_margin_home",
     "scripts/site"],
    cwd=ROOT, text=True, capture_output=True
)
print((r.stdout or "(none)")[:40000])

section("DAILY RATINGS / PROJECTIONS BLOCK")
p = ROOT / "daily_market_update.sh"
if p.exists():
    lines = p.read_text(errors="replace").splitlines()
    for i in range(270, min(len(lines), 305)):
        print(f"{i+1}: {lines[i]}")

print("\nRead-only audit complete. No files were changed.")
