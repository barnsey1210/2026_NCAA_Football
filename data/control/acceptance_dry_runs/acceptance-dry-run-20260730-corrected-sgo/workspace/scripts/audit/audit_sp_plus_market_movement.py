#!/usr/bin/env python3
"""Audit the provenance-gated SP+ market-movement research package."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
REQUIRED=["sp_plus_snapshot_audit.csv","sp_plus_snapshot_summary.json","sp_plus_game_projections.csv","market_line_audit.csv","sp_plus_game_audit.csv","sp_plus_gap_bucket_results.csv","sp_plus_gap_threshold_results.csv","sp_plus_context_results.csv","sp_plus_timing_results.csv","sp_plus_result_accuracy.csv","sp_plus_team_week_changes.csv","sp_plus_movement_predictions.csv","sp_plus_movement_model_results.csv","predicted_sp_plus_game_projections.csv","sp_plus_market_alignment.csv","holdout_2025_results.csv","model_comparison.csv","final_selection.json","summary.json"]

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="data/research/sp_plus_market_movement"); args=ap.parse_args(); d=(ROOT/args.input_dir).resolve()
 checks=[]
 def check(name,ok,detail=""): checks.append({"check":name,"passed":bool(ok),"detail":detail})
 for f in REQUIRED: check(f"output:{f}",(d/f).is_file())
 try:
  s=json.loads((d/"summary.json").read_text()); final=json.loads((d/"final_selection.json").read_text())
  snap=pd.read_csv(d/"sp_plus_snapshot_audit.csv"); proj=pd.read_csv(d/"sp_plus_game_projections.csv"); market=pd.read_csv(d/"market_line_audit.csv"); game=pd.read_csv(d/"sp_plus_game_audit.csv")
  check("stage_gate_withheld",final.get("status")=="WITHHELD" and s.get("stage_2_status","").startswith("WITHHELD"))
  check("2025_not_used_for_selection",final.get("holdout_2025_opened_for_selection") is False)
  check("no_unverified_actionable_snapshots",not snap.loc[~snap.historically_frozen.astype(bool),"eligible_for_actionable_gap_test"].astype(bool).any())
  check("no_timing_uncertain_eligible_market_rows",not market.loc[market.timing_status.eq("timing_uncertain"),"eligibility"].astype(bool).any())
  check("no_actionable_game_rows",not game.eligibility.astype(bool).any())
  z=proj.dropna(subset=["home_sp_plus_rating","away_sp_plus_rating","sp_plus_home_margin","sp_plus_home_spread"])
  formula=np.isclose(z.sp_plus_home_margin,z.home_sp_plus_rating-z.away_sp_plus_rating+z["SP+ HFA"]).all() and np.isclose(z.sp_plus_home_spread,-z.sp_plus_home_margin).all()
  check("projection_sign_and_hfa_formula",formula,f"rows={len(z)}")
  g=game.dropna(subset=["sp_plus_gap","actual_market_move","distance_to_sp_plus_at_open","distance_to_sp_plus_at_close","movement_toward_sp_plus_points"])
  calc=np.isclose(g.movement_toward_sp_plus_points,g.distance_to_sp_plus_at_open-g.distance_to_sp_plus_at_close).all()
  check("movement_toward_formula",calc,f"rows={len(g)}")
  check("protected_files_unchanged",s.get("protected_unchanged") is True)
  check("publication_repository_clean",s.get("publication_repo_clean") is True,repr(s.get("publication_repo_status_after")))
  check("local_report_exists",(ROOT/"build/research/sp_plus_market_movement/index.html").is_file())
 except Exception as exc: check("parse_and_integrity",False,repr(exc))
 failed=[x for x in checks if not x["passed"]]
 print("SP+ market-movement research audit")
 for x in checks: print(("PASS" if x["passed"] else "FAIL"),x["check"],x["detail"])
 print(f"RESULT: {'PASSED' if not failed else 'FAILED'} ({len(checks)-len(failed)}/{len(checks)} checks)")
 return 1 if failed else 0
if __name__=="__main__": raise SystemExit(main())
