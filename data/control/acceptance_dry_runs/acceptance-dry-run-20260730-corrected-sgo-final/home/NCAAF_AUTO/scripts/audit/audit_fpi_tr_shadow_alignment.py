#!/usr/bin/env python3
import json,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/"data/research/fpi_tr_shadow_alignment"
req=["source_audit.csv","source_summary.json","game_predictions.csv","team_mapping_audit.csv","direct_model_comparison.csv","reconstruction_audit.csv","reconstructed_weekly_ratings.csv","movement_predictions.csv","model_correlations.csv","incremental_value.csv","ensemble_comparison.csv","confidence_results.csv","holdout_2025_results.csv","game_level_audit.csv","final_selection.json","summary.json"]
checks=[]
def ck(n,v,d=""):checks.append({"check":n,"passed":bool(v),"detail":d})
for f in req:ck("exists:"+f,(OUT/f).exists())
if all((OUT/f).exists() for f in req):
 s=json.loads((OUT/"summary.json").read_text());g=pd.read_csv(OUT/"game_predictions.csv");h=pd.read_csv(OUT/"holdout_2025_results.csv")
 ck("2025 locked",set(h.season.dropna().astype(int))=={2025})
 ck("canonical sign conversion",((g.fpi_home_spread+g.fpi_home_margin).abs().dropna()<1e-10).all())
 ck("source columns explicit",s["exact_archive_columns"]["FPI"]=="lineespn" and s["exact_archive_columns"]["TeamRankings"]=="lineteamrank")
 ck("timing limitation explicit","cannot be independently established" in s["timing_conclusion"])
 ck("reconstruction refused",not pd.read_csv(OUT/"reconstruction_audit.csv").reconstruction_allowed.any())
 ck("identical holdout sample",len(h)==s["identical_holdout_n"])
 ck("local report exists",(ROOT/"build/research/fpi_tr_shadow_alignment/index.html").exists())
pd.DataFrame(checks).to_csv(OUT/"audit_results.csv",index=False);bad=[x for x in checks if not x["passed"]];print(f"FPI/TR audit: {'PASSED' if not bad else 'FAILED'} ({len(checks)-len(bad)}/{len(checks)})");[print("FAIL",x) for x in bad];sys.exit(bool(bad))
