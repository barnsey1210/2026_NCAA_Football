#!/bin/bash
set -euo pipefail

cd "/Users/jameslindesmith/Library/Mobile Documents/com~apple~CloudDocs/NCAAF"

TODAY=$(date +%Y-%m-%d)
STAMP=$(date +%Y%m%d_%H%M%S)

echo "======================================"
echo " Sunday Ratings Refresh"
echo " Date: $TODAY"
echo "======================================"

mkdir -p data/ratings/snapshots
mkdir -p data/ratings/run_logs

LOG="data/ratings/run_logs/sunday_refresh_${STAMP}.log"

{
  echo "Step 1: Pull/test source pages..."
  python3 scripts/ratings/test_rating_sources.py

  echo
  echo "Step 2: Parse source tables..."
  python3 scripts/ratings/parse_rating_source_tables.py

  echo
  echo "Step 3: Build weighted Power Ratings..."
  python3 scripts/ratings/build_power_ratings.py

  echo
  echo "Step 4: Confirm validation PASS..."
  if ! grep -q "Validation status: PASS" data/ratings/ratings_validation_report.txt; then
    echo "ERROR: ratings validation did not PASS."
    cat data/ratings/ratings_validation_report.txt
    exit 1
  fi

  echo
  echo "Step 5: Save dated rating snapshots..."
  cp data/ratings/ratings_master_latest.csv "data/ratings/snapshots/ratings_master_${TODAY}.csv"
  cp data/ratings/ratings_validation_report.txt "data/ratings/snapshots/ratings_validation_${TODAY}.txt"

  if [ -f data/ratings/spplus_2026_from_espn_latest.csv ]; then
    cp data/ratings/spplus_2026_from_espn_latest.csv "data/ratings/snapshots/spplus_2026_${TODAY}.csv"
  fi

  if [ -f data/ratings/teamrankings_2025_test_latest.csv ]; then
    cp data/ratings/teamrankings_2025_test_latest.csv "data/ratings/snapshots/teamrankings_test_${TODAY}.csv"
  fi

  if [ -f data/ratings/fpi_2025_test_latest.csv ]; then
    cp data/ratings/fpi_2025_test_latest.csv "data/ratings/snapshots/fpi_test_${TODAY}.csv"
  fi

  echo
  echo "Step 6: Rebuild website..."
  python3 build_site_from_workbook_safe_with_movement.py

  echo
  echo "Step 7: Verify index.html matches Python ratings..."
  python3 - <<'PY'
from pathlib import Path
import re, json
import pandas as pd

html = Path("index.html").read_text(encoding="utf-8", errors="ignore")
m = re.search(r'<script[^>]+id=["\']db["\'][^>]*>(.*?)</script>', html, flags=re.S)
if not m:
    raise SystemExit("Could not find <script id='db'> in index.html")

db = json.loads(m.group(1))
site = pd.DataFrame(db["teams"])[["team","combo","rank"]]
ratings = pd.read_csv("data/ratings/ratings_master_latest.csv")[["team","power_rating","power_rank"]]

merged = site.merge(ratings, on="team", how="outer")
merged["diff"] = merged["combo"] - merged["power_rating"]

bad = merged[merged["diff"].abs().fillna(999) > 0.000001]

print("site teams:", len(site))
print("ratings teams:", len(ratings))
print("differences:", len(bad))

if len(bad):
    print(bad.sort_values("team").to_string(index=False))
    raise SystemExit("ERROR: index.html ratings do not match ratings_master_latest.csv")

print("PASS: index.html Power Rating combo matches Python ratings_master_latest.csv exactly.")
print()
print(site.sort_values("rank").head(15).to_string(index=False))
PY

  echo
  echo "Step 8: Copy current website to organized site folder..."
  cp index.html site/index.html

  echo
  echo "======================================"
  echo "SUNDAY RATINGS REFRESH PASS"
  echo "Upload/push these files:"
  echo "  index.html"
  echo "  site/index.html"
  echo "  data/ratings/ratings_master_latest.csv"
  echo "  data/ratings/ratings_validation_report.txt"
  echo "  data/ratings/ratings_history.csv"
  echo "  data/ratings/snapshots/ratings_master_${TODAY}.csv"
  echo "======================================"

} 2>&1 | tee "$LOG"

echo
echo "Run log saved to: $LOG"
