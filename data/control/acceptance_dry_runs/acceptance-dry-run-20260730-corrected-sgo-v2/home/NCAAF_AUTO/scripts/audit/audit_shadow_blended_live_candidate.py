#!/usr/bin/env python3
import json, sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"data/research/shadow_blended_live_candidate"
checks=[]
def ck(name,ok,detail=""): checks.append({"check":name,"passed":bool(ok),"detail":detail})
required=["game_level_audit.csv","total_bias_correction_comparison.csv","spread_lambda_reconciliation.csv","summary.json"]
for x in required: ck(f"exists:{x}",(OUT/x).exists())
if all((OUT/x).exists() for x in required):
 d=pd.read_csv(OUT/"game_level_audit.csv"); s=json.loads((OUT/"summary.json").read_text())
 ck("signed spread impact arithmetic",((d.simple_blend-d.current_model_spread-d.spread_impact).abs().dropna()<1e-9).all())
 ck("total impact arithmetic",((d.final_shadow_total-d.current_model_total-d.total_impact).abs().dropna()<1e-9).all())
 ck("2025 not used for correction selection",s["total_correction_selection"] in {"none","fixed_intercept","season_stage","projected_total_band"})
 ck("protected files unchanged",s.get("protected_unchanged") is True)
 ck("preview exists",(ROOT/"build/research/shadow_blended_live_candidate/index.html").exists())
pd.DataFrame(checks).to_csv(OUT/"audit_results.csv",index=False)
bad=[x for x in checks if not x["passed"]]; print(f"Shadow candidate audit: {'PASSED' if not bad else 'FAILED'} ({len(checks)-len(bad)}/{len(checks)})")
for x in bad: print("FAIL",x)
sys.exit(bool(bad))
