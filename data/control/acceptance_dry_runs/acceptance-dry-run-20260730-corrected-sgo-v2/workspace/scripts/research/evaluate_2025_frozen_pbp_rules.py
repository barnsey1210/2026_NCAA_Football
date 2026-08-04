#!/usr/bin/env python3
"""One-time evaluation of the two frozen ATS rules on the 2025 holdout."""

from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from analyze_constrained_pbp_interactions import build

OUT=Path("data/research/pbp_constrained_interactions_2025_holdout")
RULES=[
 {"rule_id":"explosive_rush_underdog","action":1,"conditions":[("dog_pass_success","<=",-0.016664752379848446),("dog_explosive_rush",">",0.011315135194059411)],"parent":[]},
 {"rule_id":"favorite_neutral_pass_dog","action":-1,"conditions":[("dog_pass_success",">",-0.016664752379848446),("abs_spread",">",4.5),("dog_pass_success","<=",0.01620248994322704)],"parent":[("abs_spread",">",4.5)]},
]

def mask(d,conditions):
 m=pd.Series(True,index=d.index)
 for f,op,t in conditions:m &= d[f].le(t) if op=="<=" else d[f].gt(t)
 return m

def summarize(v,action):
 x=(action*pd.to_numeric(v,errors="coerce")).dropna();w=int((x>0).sum());l=int((x<0).sum());p=int((x==0).sum());dec=w+l
 mean=float(x.mean()) if len(x) else np.nan;sd=float(x.std(ddof=1)) if len(x)>1 else np.nan;se=sd/math.sqrt(len(x)) if len(x)>1 and sd>0 else np.nan;z=mean/se if se and not np.isnan(se) else np.nan
 net=w-1.1*l
 return {"n":len(x),"wins":w,"losses":l,"pushes":p,"raw_win_rate":w/dec if dec else np.nan,"shrunk_win_rate":(w+10)/(dec+20) if dec else np.nan,"mean_ats_residual":mean,"one_sided_p":.5*math.erfc(z/math.sqrt(2)) if not np.isnan(z) else np.nan,"net_units_risking_1_1":net,"roi_on_amount_risked":net/(1.1*dec) if dec else np.nan}

def bh(ps):
 out=[np.nan]*len(ps);v=sorted(enumerate(ps),key=lambda z:z[1]);run=1.
 for rr,(i,p) in enumerate(reversed(v),1):rank=len(v)-rr+1;run=min(run,p*len(v)/rank);out[i]=min(1.,run)
 return out

def main():
 OUT.mkdir(parents=True,exist_ok=True);d=build(max_season=2025);d=d[d.season.eq(2025)].copy();rows=[]
 for r in RULES:
  s=summarize(d.loc[mask(d,r["conditions"]),"ats_outcome"],r["action"]);p=summarize(d.loc[mask(d,r["parent"]),"ats_outcome"],r["action"])
  rows.append({"rule_id":r["rule_id"],"action":"underdog" if r["action"]==1 else "favorite","conditions":json.dumps(r["conditions"]),**s,"parent_n":p["n"],"parent_win_rate":p["raw_win_rate"],"incremental_win_rate":s["raw_win_rate"]-p["raw_win_rate"]})
 q=pd.DataFrame(rows);q["q_value"]=bh(q.one_sided_p.tolist());q["holdout_grade"]="not_confirmed"
 confirmed=q.n.ge(30)&q.incremental_win_rate.gt(0)&q.mean_ats_residual.ge(.5)&q.shrunk_win_rate.ge(.53)&q.q_value.le(.10);q.loc[confirmed,"holdout_grade"]="confirmed_2025"
 q.to_csv(OUT/"final_holdout_results.csv",index=False)
 overlap=int((mask(d,RULES[0]["conditions"])&mask(d,RULES[1]["conditions"])).sum())
 summary={"season":2025,"eligible_games":len(d),"rules_tested":2,"confirmed_2025":int(confirmed.sum()),"overlap_games":overlap,"holdout_status":"consumed; no longer available for tuning"}
 (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary,indent=2));print(q.to_string(index=False))

if __name__=="__main__":main()
