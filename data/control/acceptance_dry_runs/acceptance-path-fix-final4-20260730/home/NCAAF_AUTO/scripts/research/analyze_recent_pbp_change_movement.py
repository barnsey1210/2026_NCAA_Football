#!/usr/bin/env python3
"""Test whether last-two-game PBP changes anticipate line movement."""
from pathlib import Path
import json,numpy as np,pandas as pd
from analyze_pbp_line_movement import data,ridge_fit,ridge_predict,metrics,grow,leaves,mask,signed_stats,bh,MARKET_FEATURES
GAME=Path("data/research/pbp_history_2021_2025/team_game_tendencies.csv");DRIVE=Path("data/research/drive_context_2021_2025/team_game_drive_context.csv");OUT=Path("data/research/recent_pbp_change_movement_2021_2024")
RAW=["off_success_rate","off_rush_success_rate","off_pass_success_rate","off_explosive_rush_rate","off_explosive_pass_rate","off_neutral_pass_rate","off_qb_run_share","off_drive_elapsed_seconds_per_play","def_success_allowed","def_havoc_rate","off_points_per_drive"]
SPREAD=["home_change_success_adv","home_change_rush_adv","home_change_pass_adv","home_change_xrush_adv","home_change_xpass_adv","home_change_neutral_pass_adv","home_change_qb_adv","home_change_def_improve_adv","home_change_havoc_adv","home_change_ppd_adv"]
TOTAL=["combined_change_success","combined_change_rush","combined_change_pass","combined_change_xrush","combined_change_xpass","combined_change_neutral_pass","combined_change_qb","combined_pace_acceleration","combined_change_def_allowed","combined_change_havoc","combined_change_ppd"]
def trends():
 g=pd.read_csv(GAME);v=pd.read_csv(DRIVE,usecols=["season","game_id","team","off_points_per_drive"]);g=g.merge(v,on=["season","game_id","team"],how="left");rows=[]
 for (season,team),z in g.sort_values(["season","team","week","game_id"]).groupby(["season","team"]):
  hist=[]
  for r in z.to_dict("records"):
   o={"season":season,"game_id":r["game_id"],"team":team,"prior_games":len(hist)}
   for c in RAW:
    recent=pd.to_numeric(pd.Series([x.get(c) for x in hist[-2:]]),errors="coerce").mean();earlier=pd.to_numeric(pd.Series([x.get(c) for x in hist[:-2]]),errors="coerce").mean();o[f"change_{c}"]=recent-earlier
   rows.append(o);hist.append(r)
 return pd.DataFrame(rows)
def main():
 OUT.mkdir(parents=True,exist_ok=True);d=data();t=trends()
 for side in ("home","away"):
  z=t.add_prefix(f"{side}_t_").rename(columns={f"{side}_t_game_id":"game_id",f"{side}_t_team":f"{side}_team"});d=d.merge(z,on=["game_id",f"{side}_team"],how="left")
 src={"success":"off_success_rate","rush":"off_rush_success_rate","pass":"off_pass_success_rate","xrush":"off_explosive_rush_rate","xpass":"off_explosive_pass_rate","neutral_pass":"off_neutral_pass_rate","qb":"off_qb_run_share","havoc":"def_havoc_rate","ppd":"off_points_per_drive"}
 for label,col in src.items():
  h=d[f"home_t_change_{col}"];a=d[f"away_t_change_{col}"];d[f"home_change_{label}_adv"]=h-a;d[f"combined_change_{label}"]=h+a
 d["home_change_def_improve_adv"]=-d.home_t_change_def_success_allowed+d.away_t_change_def_success_allowed;d["combined_change_def_allowed"]=d.home_t_change_def_success_allowed+d.away_t_change_def_success_allowed;d["combined_pace_acceleration"]=-(d.home_t_change_off_drive_elapsed_seconds_per_play+d.away_t_change_off_drive_elapsed_seconds_per_play)
 dev=d[d.season<=2023];val=d[d.season==2024];models=[];rules=[]
 for market,pbp,target,min_dev,min_val in [("spread",SPREAD,"spread_move",.75,.5),("total",TOTAL,"total_move",1.,.75)]:
  mf=MARKET_FEATURES[market];features=mf+pbp;tr=dev.dropna(subset=features+[target]);te=val.dropna(subset=features+[target]);p0=np.zeros(len(te));pm=ridge_predict(te,mf,ridge_fit(tr,mf,target));pp=ridge_predict(te,features,ridge_fit(tr,features,target))
  for name,pred in [("opener_zero_move",p0),("market_only",pm),("market_plus_recent_pbp",pp)]:models.append({"market":market,"model":name,**metrics(te[target],pred)})
  tree=grow(tr,features,target);(OUT/f"{market}_tree.json").write_text(json.dumps(tree,indent=2)+"\n")
  for i,l in enumerate(leaves(tree),1):
   has=any(f in pbp for f,_,_ in l["path"]);dm=mask(tr,l["path"],market);parent=mask(tr,l["path"],market,True);mean=float(tr.loc[dm,target].mean());pmean=float(tr.loc[parent,target].mean());direction=1 if mean>=0 else -1
   if has and dm.sum()>=100 and abs(mean)>=min_dev and abs(mean-pmean)>=.5:
    vm=mask(te,l["path"],market);s=signed_stats(te.loc[vm,target],direction);rules.append({"market":market,"rule_id":f"{market}_{i}","rule":" AND ".join(f"{f} {op} {x:.6g}" for f,op,x in l["path"]),"direction":direction,"development_n":int(dm.sum()),"development_mean_move":mean,"development_parent_mean":pmean,**{f"validation_{k}":v for k,v in s.items()},"validation_threshold":min_val})
 m=pd.DataFrame(models);m.to_csv(OUT/"incremental_model_validation.csv",index=False);q=pd.DataFrame(rules)
 if len(q):q["validation_q_value"]=bh(q.validation_one_sided_p.tolist());q["evidence_grade"]="rejected_or_inconclusive";ok=q.validation_n.ge(30)&q.validation_signed_mean_move.ge(q.validation_threshold)&q.validation_q_value.le(.10);q.loc[ok,"evidence_grade"]="validated_2024"
 q.to_csv(OUT/"interaction_validation.csv",index=False);s={"development_complete":int(sum((dev.season<=2023)&dev[SPREAD].notna().all(axis=1))),"validation_complete":int(val[SPREAD].notna().all(axis=1).sum()),"submitted_rules":len(q),"validated_2024":int((q.evidence_grade=="validated_2024").sum()) if len(q) else 0,"holdout_2025":"not used"};(OUT/"summary.json").write_text(json.dumps(s,indent=2)+"\n");print(json.dumps(s,indent=2));print(m.to_string(index=False));print(q.to_string(index=False))
if __name__=="__main__":main()
