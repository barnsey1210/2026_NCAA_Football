#!/usr/bin/env python3
"""Predict the next game's market total innovation from both teams' prior games."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
GAMES=ROOT/"data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
PBP=ROOT/"data/research/pbp_history_2021_2025/team_game_tendencies.csv"
OUT=ROOT/"data/research/postgame_total_market_update_2021_2025"
WINDOW,SHRINK=6,10.0
SCORE=["home_prev_scored_vs_implied","home_prev_allowed_vs_implied","home_prev_total_residual","home_prev_ats_margin","away_prev_scored_vs_implied","away_prev_allowed_vs_implied","away_prev_total_residual","away_prev_ats_margin"]
PBPV=["off_success_rate","off_ppa","off_explosiveness","def_success_allowed","def_ppa_allowed","def_explosiveness_allowed","off_drive_elapsed_seconds_per_play","off_plays"]

def total_predictions(g):
 out={}
 for season,d in g.groupby("season"):
  teams=sorted(set(d.home_team)|set(d.away_team));ix={t:i for i,t in enumerate(teams)};n=len(teams)
  for week in sorted(d.week.unique()):
   h=d[(d.week<week)&(d.week>=week-WINDOW)]
   if h.empty: out[(season,week)]={"intercept":54.0,"off":{},"def":{}};continue
   obs=[]
   for _,r in h.iterrows():
    obs += [(r.home_team,r.away_team,(r.closing_total-r.closing_home_spread)/2),(r.away_team,r.home_team,(r.closing_total+r.closing_home_spread)/2)]
   x=np.zeros((len(obs),1+2*n));y=np.zeros(len(obs));x[:,0]=1
   for j,(tm,op,pts) in enumerate(obs):x[j,1+ix[tm]]=1;x[j,1+n+ix[op]]=1;y[j]=pts
   pen=SHRINK*np.eye(x.shape[1]);pen[0,0]=0;b=np.linalg.solve(x.T@x+pen,x.T@y)
   out[(season,week)]={"intercept":float(b[0]),"off":{t:float(b[1+ix[t]]) for t in teams},"def":{t:float(b[1+n+ix[t]]) for t in teams}}
 return out

def fit_predict(train,test,features):
 x=train[features].apply(pd.to_numeric,errors="coerce").to_numpy(float);xt=test[features].apply(pd.to_numeric,errors="coerce").to_numpy(float);med=np.nanmedian(x,axis=0);med=np.where(np.isfinite(med),med,0);x=np.where(np.isnan(x),med,x);xt=np.where(np.isnan(xt),med,xt);mu=x.mean(0);sd=np.where(x.std(0)>1e-9,x.std(0),1);x=(x-mu)/sd;xt=(xt-mu)/sd;x=np.c_[np.ones(len(x)),x];xt=np.c_[np.ones(len(xt)),xt];p=20*np.eye(x.shape[1]);p[0,0]=0;b=np.linalg.solve(x.T@x+p,x.T@train.target_total_innovation);pred=xt@b;y=test.target_total_innovation.to_numpy();mae=lambda z:float(np.mean(np.abs(y-z)));base=mae(np.zeros(len(y)));m=mae(pred)
 return {"n":len(y),"baseline_mae":base,"model_mae":m,"mae_improvement_pct":100*(base-m)/base,"direction_accuracy":float(np.mean(np.sign(pred)==np.sign(y))),"correlation":float(np.corrcoef(pred,y)[0,1]),"prediction":pred}

def main():
 OUT.mkdir(parents=True,exist_ok=True);g=pd.read_csv(GAMES,low_memory=False);g=g[g.closing_total.notna()&g.closing_home_spread.notna()].copy();models=total_predictions(g);innov=[]
 for _,r in g.iterrows():
  m=models[(r.season,r.week)];hp=m["intercept"]+m["off"].get(r.home_team,0)+m["def"].get(r.away_team,0);ap=m["intercept"]+m["off"].get(r.away_team,0)+m["def"].get(r.home_team,0);innov.append(r.closing_total-(hp+ap))
 g["target_total_innovation"]=innov
 pbp=pd.read_csv(PBP,low_memory=False)
 team=[]
 for _,r in g.iterrows():
  hi=(r.closing_total-r.closing_home_spread)/2;ai=(r.closing_total+r.closing_home_spread)/2
  team += [{"season":r.season,"week":r.week,"game_id":r.game_id,"team":r.home_team,"scored_vs_implied":r.home_score-hi,"allowed_vs_implied":r.away_score-ai,"total_residual":r.actual_total_points-r.closing_total,"ats_margin":r.closing_spread_residual},
           {"season":r.season,"week":r.week,"game_id":r.game_id,"team":r.away_team,"scored_vs_implied":r.away_score-ai,"allowed_vs_implied":r.home_score-hi,"total_residual":r.actual_total_points-r.closing_total,"ats_margin":-r.closing_spread_residual}]
 t=pd.DataFrame(team).merge(pbp[["season","week","game_id","team"]+PBPV],on=["season","week","game_id","team"],how="left").sort_values(["season","team","week"]);t["next_game_id"]=t.groupby(["season","team"]).game_id.shift(-1);t["next_week"]=t.groupby(["season","team"]).week.shift(-1);t=t[(t.next_week-t.week).between(1,3)]
 base=g[["season","week","game_id","home_team","away_team","target_total_innovation"]].copy()
 for side in ["home","away"]:
  z=t.rename(columns={c:f"{side}_prev_{c}" for c in ["scored_vs_implied","allowed_vs_implied","total_residual","ats_margin"]+PBPV});z=z.rename(columns={"team":f"{side}_prior_team"})
  keep=["season","next_game_id",f"{side}_prior_team"]+[f"{side}_prev_{c}" for c in ["scored_vs_implied","allowed_vs_implied","total_residual","ats_margin"]+PBPV]
  base=base.merge(z[keep],left_on=["season","game_id",f"{side}_team"],right_on=["season","next_game_id",f"{side}_prior_team"],how="inner").drop(columns=["next_game_id",f"{side}_prior_team"])
 train=base[base.season<=2023];val=base[base.season==2024];s=fit_predict(train,val,SCORE);f=fit_predict(train,val,SCORE+[f"{side}_prev_{c}" for side in ["home","away"] for c in PBPV]);summary={"design":{"development":"2021-23","validation":"2024","holdout":"2025 opened only after validation pass"},"score_only":{k:v for k,v in s.items() if k!="prediction"},"score_plus_pbp":{k:v for k,v in f.items() if k!="prediction"}};summary["pbp_incremental_mae_vs_score_pct"]=100*(s["model_mae"]-f["model_mae"])/s["model_mae"];summary["validation_pass"]=bool(f["mae_improvement_pct"]>=2 and summary["pbp_incremental_mae_vs_score_pct"]>0 and f["correlation"]>.05)
 if summary["validation_pass"]:
  tr=base[base.season<=2024];ho=base[base.season==2025];hs=fit_predict(tr,ho,SCORE);hf=fit_predict(tr,ho,SCORE+[f"{side}_prev_{c}" for side in ["home","away"] for c in PBPV]);summary["holdout_score_only"]={k:v for k,v in hs.items() if k!="prediction"};summary["holdout_score_plus_pbp"]={k:v for k,v in hf.items() if k!="prediction"};summary["holdout_pbp_incremental_mae_vs_score_pct"]=100*(hs["model_mae"]-hf["model_mae"])/hs["model_mae"]
 base.to_csv(OUT/"modeling_rows.csv",index=False);(OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");(OUT/"README.md").write_text("# Postgame prediction of next market total\n\nClosing totals and spreads are decomposed into market-implied team scores. Rolling offense and defense market components form the no-change expectation. Both teams' prior score surprises and garbage-filtered PBP are tested on the next closing-total innovation.\n\n```json\n"+json.dumps(summary,indent=2)+"\n```\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
