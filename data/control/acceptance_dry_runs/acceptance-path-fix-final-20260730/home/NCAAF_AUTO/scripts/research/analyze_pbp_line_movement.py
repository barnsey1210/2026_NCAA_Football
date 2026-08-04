#!/usr/bin/env python3
"""Test whether pregame PBP matchups predict Bovada opening-to-close movement."""

from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

MODEL=Path("data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv")
PROVIDERS=Path("data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv")
DRIVES=Path("data/research/drive_context_2021_2025/rolling_pregame_drive_context.csv")
OUT=Path("data/research/pbp_line_movement_2021_2024")

SPREAD_PBP=["home_rush_success_adv","home_pass_success_adv","home_explosive_rush_adv","home_explosive_pass_adv","home_qb_run_adv","home_havoc_adv","home_field_position_adv","home_opportunity_adv","home_finishing_adv","home_ppd_adv","home_overall_success_adv","home_ppa_adv"]
TOTAL_PBP=["combined_rush_success","combined_pass_success","combined_explosive_rush","combined_explosive_pass","combined_qb_run","combined_low_disruption","combined_fast_pace","combined_pass_rate","combined_field_position","combined_opportunity","combined_finishing","combined_ppd","combined_overall_success","combined_ppa"]
MARKET_FEATURES={"spread":["opening_home_spread","opening_total","opening_home_dog"],"total":["opening_total","abs_opening_spread"]}

def data(provider="Bovada", max_season=2024):
 d=pd.read_csv(MODEL,low_memory=False); p=pd.read_csv(PROVIDERS,low_memory=False);p=p[p.provider.eq(provider)].drop_duplicates("game_id")
 lines=p[["game_id","opening_home_spread","closing_home_spread","opening_total","closing_total"]]
 d=d.drop(columns=["opening_home_spread","closing_home_spread","opening_total","closing_total","provider"],errors="ignore").merge(lines,on="game_id",how="inner")
 r=pd.read_csv(DRIVES);cols=["game_id","team","pregame_off_avg_start_ytg","pregame_off_opportunity_rate","pregame_off_points_per_opportunity","pregame_off_points_per_drive","pregame_def_opponent_avg_start_ytg","pregame_def_opportunity_rate_allowed","pregame_def_points_per_opportunity_allowed","pregame_def_points_per_drive_allowed"]
 for side in ("home","away"):
  z=r[cols].rename(columns={"team":f"{side}_team",**{c:f"{side}_d_{c}" for c in cols if c not in ("game_id","team")}});d=d.merge(z,on=["game_id",f"{side}_team"],how="left")
 d=d[(d.season<=max_season)&d.eligible_week5_plus.astype(str).str.lower().eq("true")].copy()
 def pair(a,b):return (a+b)/2
 for side,opp in (("home","away"),("away","home")):
  d[f"{side}_rush"]=pair(d[f"{side}_pregame_off_rush_success_rate"],d[f"{opp}_pregame_def_rush_success_allowed"]);d[f"{side}_pass"]=pair(d[f"{side}_pregame_off_pass_success_rate"],d[f"{opp}_pregame_def_pass_success_allowed"])
  d[f"{side}_xrush"]=pair(d[f"{side}_pregame_off_explosive_rush_rate"],d[f"{opp}_pregame_def_explosive_rush_allowed"]);d[f"{side}_xpass"]=pair(d[f"{side}_pregame_off_explosive_pass_rate"],d[f"{opp}_pregame_def_explosive_pass_allowed"])
  d[f"{side}_qb"]=d[f"{side}_pregame_off_qb_run_share"]*d[f"{opp}_pregame_def_rush_success_allowed"]
  d[f"{side}_fp"]=-(d[f"{side}_d_pregame_off_avg_start_ytg"]+d[f"{opp}_d_pregame_def_opponent_avg_start_ytg"])/2
  d[f"{side}_opp"]=pair(d[f"{side}_d_pregame_off_opportunity_rate"],d[f"{opp}_d_pregame_def_opportunity_rate_allowed"]);d[f"{side}_finish"]=pair(d[f"{side}_d_pregame_off_points_per_opportunity"],d[f"{opp}_d_pregame_def_points_per_opportunity_allowed"]);d[f"{side}_ppd"]=pair(d[f"{side}_d_pregame_off_points_per_drive"],d[f"{opp}_d_pregame_def_points_per_drive_allowed"])
 for out,src in [("rush_success","rush"),("pass_success","pass"),("explosive_rush","xrush"),("explosive_pass","xpass"),("qb_run","qb"),("field_position","fp"),("opportunity","opp"),("finishing","finish"),("ppd","ppd")]:
  d[f"home_{out}_adv"]=d[f"home_{src}"]-d[f"away_{src}"];d[f"combined_{out}"]=d[f"home_{src}"]+d[f"away_{src}"]
 d["home_havoc_adv"]=d.home_matchup_expected_def_havoc-d.away_matchup_expected_def_havoc;d["combined_low_disruption"]=-(d.home_matchup_expected_def_havoc+d.away_matchup_expected_def_havoc)
 d["combined_fast_pace"]=-(d.home_matchup_expected_off_pace_seconds+d.away_matchup_expected_off_pace_seconds)/2;d["combined_pass_rate"]=(d.home_matchup_expected_off_neutral_pass+d.away_matchup_expected_off_neutral_pass)/2
 d["home_overall_success_adv"]=d.home_matchup_expected_off_success-d.away_matchup_expected_off_success;d["combined_overall_success"]=d.home_matchup_expected_off_success+d.away_matchup_expected_off_success
 d["home_ppa_adv"]=d.home_matchup_expected_off_ppa-d.away_matchup_expected_off_ppa;d["combined_ppa"]=d.home_matchup_expected_off_ppa+d.away_matchup_expected_off_ppa
 d["opening_home_dog"]=(d.opening_home_spread>0).astype(float);d["abs_opening_spread"]=d.opening_home_spread.abs();d["spread_move"]=d.opening_home_spread-d.closing_home_spread;d["total_move"]=d.closing_total-d.opening_total
 return d

def ridge_fit(train,features,target,lam=1.0):
 x=train[features].to_numpy(float);y=train[target].to_numpy(float);mu=np.nanmean(x,0);sd=np.nanstd(x,0);sd[sd==0]=1;x=(x-mu)/sd;x=np.column_stack([np.ones(len(x)),x]);pen=np.eye(x.shape[1])*lam;pen[0,0]=0;b=np.linalg.solve(x.T@x+pen,x.T@y);return mu,sd,b
def ridge_predict(d,features,fit):mu,sd,b=fit;x=(d[features].to_numpy(float)-mu)/sd;return np.column_stack([np.ones(len(x)),x])@b
def metrics(y,p):
 e=np.asarray(y)-np.asarray(p);return {"n":len(e),"mae":float(np.mean(abs(e))),"rmse":float(np.sqrt(np.mean(e**2))),"direction_accuracy":float(np.mean(np.sign(p)==np.sign(y))),"mean_predicted_move":float(np.mean(p))}
def variance(y):return float(np.var(y)) if len(y) else 0
def grow(d,features,target,depth=0,path=None):
 path=path or [];n={"n":len(d),"path":path,"prediction":float(d[target].mean())}
 if depth>=3 or len(d)<200:return n
 best=None;base=variance(d[target])
 for f in features:
  for t in sorted(set(d[f].quantile([.2,.3,.4,.5,.6,.7,.8]).dropna())):
   l=d[d[f]<=t];r=d[d[f]>t]
   if len(l)<100 or len(r)<100:continue
   gain=base-(len(l)*variance(l[target])+len(r)*variance(r[target]))/len(d)
   if best is None or gain>best[0]:best=(gain,f,float(t),l,r)
 if best is None or best[0]<=0:return n
 _,f,t,l,r=best;n.update({"feature":f,"threshold":t,"left":grow(l,features,target,depth+1,path+[(f,"<=",t)]),"right":grow(r,features,target,depth+1,path+[(f,">",t)])});return n
def leaves(n):return [n] if "feature" not in n else leaves(n["left"])+leaves(n["right"])
def mask(d,path,market,market_only=False):
 m=pd.Series(True,index=d.index)
 for f,op,t in path:
  if market_only and f not in MARKET_FEATURES[market]:continue
  m &= d[f].le(t) if op=="<=" else d[f].gt(t)
 return m
def signed_stats(v,direction):
 x=direction*pd.to_numeric(v,errors="coerce").dropna().to_numpy(float);mean=float(x.mean()) if len(x) else np.nan;sd=float(x.std(ddof=1)) if len(x)>1 else np.nan;se=sd/math.sqrt(len(x)) if len(x)>1 and sd>0 else np.nan;z=mean/se if se and not np.isnan(se) else np.nan
 return {"n":len(x),"signed_mean_move":mean,"direction_accuracy":float(np.mean(x>0)) if len(x) else np.nan,"one_sided_p":.5*math.erfc(z/math.sqrt(2)) if not np.isnan(z) else np.nan}
def bh(ps):
 out=[np.nan]*len(ps);v=sorted(((i,p) for i,p in enumerate(ps) if not pd.isna(p)),key=lambda z:z[1]);run=1.
 for rr,(i,p) in enumerate(reversed(v),1):rank=len(v)-rr+1;run=min(run,p*len(v)/rank);out[i]=min(1.,run)
 return out
def main():
 OUT.mkdir(parents=True,exist_ok=True);d=data();dev=d[d.season<=2023];val=d[d.season.eq(2024)];model_rows=[];rule_rows=[]
 for market,pbp,target,min_dev,min_val in [("spread",SPREAD_PBP,"spread_move",.75,.5),("total",TOTAL_PBP,"total_move",1.,.75)]:
  mf=MARKET_FEATURES[market];allf=mf+pbp;tr=dev.dropna(subset=allf+[target]);te=val.dropna(subset=allf+[target])
  pred0=np.zeros(len(te));pm=ridge_predict(te,mf,ridge_fit(tr,mf,target));pp=ridge_predict(te,allf,ridge_fit(tr,allf,target))
  for name,pred in [("opener_zero_move",pred0),("market_only",pm),("market_plus_pbp",pp)]:model_rows.append({"market":market,"model":name,**metrics(te[target],pred)})
  tree=grow(tr,allf,target);(OUT/f"{market}_movement_tree.json").write_text(json.dumps(tree,indent=2)+"\n")
  for i,l in enumerate(leaves(tree),1):
   has_pbp=any(f in pbp for f,_,_ in l["path"]);dm=mask(tr,l["path"],market);pmask=mask(tr,l["path"],market,True);mean=float(tr.loc[dm,target].mean());parent=float(tr.loc[pmask,target].mean());direction=1 if mean>=0 else -1
   if has_pbp and dm.sum()>=100 and abs(mean)>=min_dev and abs(mean-parent)>=.5:
    vm=mask(te,l["path"],market);s=signed_stats(te.loc[vm,target],direction)
    rule_rows.append({"market":market,"rule_id":f"{market}_{i}","rule":" AND ".join(f"{f} {op} {t:.6g}" for f,op,t in l["path"]),"predicted_direction":"home_upgrade" if market=="spread" and direction==1 else "away_upgrade" if market=="spread" else "up" if direction==1 else "down","development_n":int(dm.sum()),"development_mean_move":mean,"development_parent_mean_move":parent,"development_incremental_move":mean-parent,**{f"validation_{k}":v for k,v in s.items()},"validation_threshold":min_val})
 models=pd.DataFrame(model_rows);models.to_csv(OUT/"incremental_model_validation.csv",index=False);q=pd.DataFrame(rule_rows)
 if len(q):
  q["validation_q_value"]=bh(q.validation_one_sided_p.tolist());q["evidence_grade"]="rejected_or_inconclusive";ok=q.validation_n.ge(30)&q.validation_signed_mean_move.ge(q.validation_threshold)&q.validation_q_value.le(.10);q.loc[ok,"evidence_grade"]="validated_2024"
 q.to_csv(OUT/"interaction_rule_validation.csv",index=False)
 summary={"provider":"Bovada","development_rows":len(dev),"validation_rows":len(val),"spread_complete_development":int(dev.opening_home_spread.notna().sum()),"spread_complete_validation":int(val.opening_home_spread.notna().sum()),"total_complete_development":int(dev.opening_total.notna().sum()),"total_complete_validation":int(val.opening_total.notna().sum()),"submitted_rules":len(q),"validated_rules":int((q.evidence_grade=="validated_2024").sum()) if len(q) else 0,"movement_holdout_2025":"not read"}
 (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary,indent=2));print(models.to_string(index=False));print(q.to_string(index=False))
if __name__=="__main__":main()
