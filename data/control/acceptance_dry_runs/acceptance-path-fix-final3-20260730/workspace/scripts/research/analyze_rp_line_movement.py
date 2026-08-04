#!/usr/bin/env python3
"""Frozen early-season returning-production line-movement test."""
from pathlib import Path
import math,json,numpy as np,pandas as pd
from analyze_pbp_line_movement import signed_stats,bh
P=Path("data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv");R=Path("data/import/sp_plus/sp_plus_returning_production_2023_2025.csv");O=Path("data/research/rp_line_movement_2023_2024")
SPECS=[("home_overall_rp_adv","spread",-1,1),("home_off_vs_def_rp_adv","spread",-1,1),("home_def_vs_off_rp_adv","spread",-1,1),("combined_overall_rp","total",-1,1),("combined_offense_rp","total",-1,1),("combined_defense_rp","total",-1,1)]
def main():
 O.mkdir(parents=True,exist_ok=True);p=pd.read_csv(P,low_memory=False);p=p[(p.provider=="Bovada")&(p.week<=4)&(p.season.between(2023,2024))].drop_duplicates("game_id");r=pd.read_csv(R)
 h=r.add_prefix("home_").rename(columns={"home_season":"season","home_team":"home_team"});a=r.add_prefix("away_").rename(columns={"away_season":"season","away_team":"away_team"});d=p.merge(h,on=["season","home_team"]).merge(a,on=["season","away_team"])
 d["spread_move"]=d.opening_home_spread-d.closing_home_spread;d["total_move"]=d.closing_total-d.opening_total
 d["home_overall_rp_adv"]=d.home_overall-d.away_overall;d["home_off_vs_def_rp_adv"]=d.home_offense-d.away_defense;d["home_def_vs_off_rp_adv"]=d.home_defense-d.away_offense;d["combined_overall_rp"]=d.home_overall+d.away_overall;d["combined_offense_rp"]=d.home_offense+d.away_offense;d["combined_defense_rp"]=d.home_defense+d.away_defense
 dev=d[d.season==2023];val=d[d.season==2024];rows=[]
 for f,mkt,lo_dir,hi_dir in SPECS:
  lo,hi=dev[f].quantile([.25,.75]);target=f"{mkt}_move";minimum=.5 if mkt=="spread" else .75
  for tail,t,direction in [("low",lo,lo_dir),("high",hi,hi_dir)]:
   dm=dev[f].le(t) if tail=="low" else dev[f].ge(t);vm=val[f].le(t) if tail=="low" else val[f].ge(t);ds=signed_stats(dev.loc[dm,target],direction);vs=signed_stats(val.loc[vm,target],direction)
   rows.append({"feature":f,"market":mkt,"tail":tail,"threshold":t,"predicted_direction":direction,**{f"development_{k}":v for k,v in ds.items()},**{f"validation_{k}":v for k,v in vs.items()},"validation_threshold":minimum})
 q=pd.DataFrame(rows);q["validation_q_value"]=bh(q.validation_one_sided_p.tolist());q["evidence_grade"]="rejected_or_inconclusive";ok=q.validation_n.ge(15)&q.development_signed_mean_move.gt(0)&q.validation_signed_mean_move.ge(q.validation_threshold)&q.validation_q_value.le(.10);q.loc[ok,"evidence_grade"]="validated_2024";q.to_csv(O/"feature_validation.csv",index=False)
 s={"development_games":len(dev),"validation_games":len(val),"tests":len(q),"validated_2024":int((q.evidence_grade=="validated_2024").sum()),"holdout_2025":"not used"};(O/"summary.json").write_text(json.dumps(s,indent=2)+"\n");print(json.dumps(s,indent=2));print(q.to_string(index=False))
if __name__=="__main__":main()
