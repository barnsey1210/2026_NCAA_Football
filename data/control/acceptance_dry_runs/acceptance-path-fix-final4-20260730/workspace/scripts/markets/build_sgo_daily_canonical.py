#!/usr/bin/env python3
"""Provider-free daily bridge from an existing SGO raw file to canonical artifacts."""
from __future__ import annotations
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser();p.add_argument("--raw",type=Path,default=ROOT/"data/markets/sgo/sgo_ncaaf_events_raw.json");a=p.parse_args()
 if not a.raw.exists():raise SystemExit(f"No existing SGO raw response: {a.raw}")
 run="daily-sgo-normalize-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
 subprocess.run([sys.executable,str(ROOT/"scripts/control/sgo_preview_adapter.py"),"--run-id",run,"--fixture",str(a.raw)],cwd=ROOT,check=True)
 stage=ROOT/"data/control/staging"/run;raw=ROOT/"data/control/raw/sports_game_odds"/run/"response.json"
 out=ROOT/"data/markets/sgo"
 cmd=[sys.executable,str(ROOT/"scripts/markets/build_sgo_canonical_artifacts.py"),"--observations",str(stage/"quote_observations.csv"),"--manifest",str(stage/"manifest.json"),"--raw",str(raw),"--quotes-out",str(out/"sgo_accepted_quotes.csv"),"--display-out",str(out/"sgo_canonical_display_lines.csv"),"--coverage-out",str(out/"sgo_canonical_coverage.json"),"--exclusions-out",str(out/"sgo_canonical_exclusions.csv")]
 subprocess.run(cmd,cwd=ROOT,check=True)
 coverage=json.loads((out/"sgo_canonical_coverage.json").read_text())
 if not coverage["acceptance_eligibility"]:
  print("SGO canonical artifacts are preview-only; accepted data/history unchanged")
 return 0
if __name__=="__main__":raise SystemExit(main())
