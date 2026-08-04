#!/usr/bin/env python3
"""Constrained shallow-tree discovery of market-conditioned PBP matchup rules."""

from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

MARKET=Path("data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv")
DRIVE=Path("data/research/drive_context_2021_2025/rolling_pregame_drive_context.csv")
OUT=Path("data/research/pbp_constrained_interactions_2021_2024")
MARKET_FEATURES={"ATS":["abs_spread","closing_total","dog_home"],"TOTAL":["abs_spread","closing_total"]}
ATS_PBP=["dog_rush_success","dog_pass_success","dog_explosive_rush","dog_explosive_pass","dog_qb_run_stress","dog_havoc","dog_field_position","dog_opportunity","dog_finishing","dog_points_per_drive"]
TOTAL_PBP=["total_rush_success","total_pass_success","total_explosive_rush","total_explosive_pass","total_qb_run_stress","total_low_disruption","total_fast_pace","total_pass_rate","total_field_position","total_opportunity","total_finishing","total_points_per_drive"]

def build(max_season=2024):
    d=pd.read_csv(MARKET,low_memory=False)
    r=pd.read_csv(DRIVE)
    cols=["game_id","team","pregame_off_avg_start_ytg","pregame_off_opportunity_rate","pregame_off_points_per_opportunity","pregame_off_points_per_drive","pregame_def_opponent_avg_start_ytg","pregame_def_opportunity_rate_allowed","pregame_def_points_per_opportunity_allowed","pregame_def_points_per_drive_allowed"]
    for side in ("home","away"):
        z=r[cols].rename(columns={"team":f"{side}_team",**{c:f"{side}_drive_{c}" for c in cols if c not in ("game_id","team")}})
        d=d.merge(z,on=["game_id",f"{side}_team"],how="left")
    d=d[(d.season<=max_season)&d.eligible_week5_plus.astype(str).str.lower().eq("true")].copy()
    d["abs_spread"]=d.closing_home_spread.abs(); d["dog_home"]=(d.closing_home_spread>0).astype(float)
    d=d[d.closing_home_spread.ne(0)].copy(); sign=np.where(d.dog_home.eq(1),1.0,-1.0)
    def pair(a,b): return (a+b)/2
    for side,opp in (("home","away"),("away","home")):
        d[f"{side}_rush_success"]=pair(d[f"{side}_pregame_off_rush_success_rate"],d[f"{opp}_pregame_def_rush_success_allowed"])
        d[f"{side}_pass_success"]=pair(d[f"{side}_pregame_off_pass_success_rate"],d[f"{opp}_pregame_def_pass_success_allowed"])
        d[f"{side}_explosive_rush"]=pair(d[f"{side}_pregame_off_explosive_rush_rate"],d[f"{opp}_pregame_def_explosive_rush_allowed"])
        d[f"{side}_explosive_pass"]=pair(d[f"{side}_pregame_off_explosive_pass_rate"],d[f"{opp}_pregame_def_explosive_pass_allowed"])
        d[f"{side}_qb_run_stress"]=d[f"{side}_pregame_off_qb_run_share"]*d[f"{opp}_pregame_def_rush_success_allowed"]
        d[f"{side}_field_position"]=-(d[f"{side}_drive_pregame_off_avg_start_ytg"]+d[f"{opp}_drive_pregame_def_opponent_avg_start_ytg"])/2
        d[f"{side}_opportunity"]=pair(d[f"{side}_drive_pregame_off_opportunity_rate"],d[f"{opp}_drive_pregame_def_opportunity_rate_allowed"])
        d[f"{side}_finishing"]=pair(d[f"{side}_drive_pregame_off_points_per_opportunity"],d[f"{opp}_drive_pregame_def_points_per_opportunity_allowed"])
        d[f"{side}_points_per_drive"]=pair(d[f"{side}_drive_pregame_off_points_per_drive"],d[f"{opp}_drive_pregame_def_points_per_drive_allowed"])
    for name in ["rush_success","pass_success","explosive_rush","explosive_pass","qb_run_stress","field_position","opportunity","finishing","points_per_drive"]:
        d[f"dog_{name}"]=sign*(d[f"home_{name}"]-d[f"away_{name}"])
        d[f"total_{name}"]=d[f"home_{name}"]+d[f"away_{name}"]
    d["dog_havoc"]=sign*(d.home_matchup_expected_def_havoc-d.away_matchup_expected_def_havoc)
    d["total_low_disruption"]=-(d.home_matchup_expected_def_havoc+d.away_matchup_expected_def_havoc)
    d["total_fast_pace"]=-(d.home_matchup_expected_off_pace_seconds+d.away_matchup_expected_off_pace_seconds)/2
    d["total_pass_rate"]=(d.home_matchup_expected_off_neutral_pass+d.away_matchup_expected_off_neutral_pass)/2
    d["ats_outcome"]=sign*d.closing_spread_residual; d["total_outcome"]=d.closing_total_residual
    return d

def gini(y):
    if len(y)==0:return 0
    p=float((y>0).mean()); return 2*p*(1-p)

def grow(d,features,outcome,depth=0,path=None):
    path=path or []; node={"n":len(d),"path":path,"action":1 if float((d[outcome]>0).mean())>=.5 else -1}
    if depth>=3 or len(d)<200:return node
    base=gini(d[outcome]); best=None
    for f in features:
        for t in sorted(set(d[f].quantile([.2,.3,.4,.5,.6,.7,.8]).dropna())):
            left=d[d[f]<=t]; right=d[d[f]>t]
            if len(left)<100 or len(right)<100:continue
            gain=base-(len(left)*gini(left[outcome])+len(right)*gini(right[outcome]))/len(d)
            if best is None or gain>best[0]:best=(gain,f,float(t),left,right)
    if best is None or best[0]<=0:return node
    _,f,t,left,right=best; node.update({"feature":f,"threshold":t})
    node["left"]=grow(left,features,outcome,depth+1,path+[(f,"<=",t)])
    node["right"]=grow(right,features,outcome,depth+1,path+[(f,">",t)])
    return node

def leaves(n):
    if "feature" not in n:return [n]
    return leaves(n["left"])+leaves(n["right"])

def mask(d,path,market_only=False):
    m=pd.Series(True,index=d.index)
    for f,op,t in path:
        if market_only and f not in MARKET_FEATURES[CURRENT_MARKET]:continue
        m &= d[f].le(t) if op=="<=" else d[f].gt(t)
    return m

def summary(v,action):
    x=(action*pd.to_numeric(v,errors="coerce")).dropna(); w=int((x>0).sum());l=int((x<0).sum());p=int((x==0).sum());n=w+l
    mean=float(x.mean()) if len(x) else np.nan;sd=float(x.std(ddof=1)) if len(x)>1 else np.nan;se=sd/math.sqrt(len(x)) if len(x)>1 and sd>0 else np.nan;z=mean/se if se and not np.isnan(se) else np.nan
    return {"n":len(x),"wins":w,"losses":l,"pushes":p,"raw_win_rate":w/n if n else np.nan,"shrunk_win_rate":(w+10)/(n+20) if n else np.nan,"mean_residual":mean,"p":.5*math.erfc(z/math.sqrt(2)) if not np.isnan(z) else np.nan}

def bh(ps):
    out=[np.nan]*len(ps);v=sorted(((i,p) for i,p in enumerate(ps) if not pd.isna(p)),key=lambda z:z[1]);run=1.
    for rr,(i,p) in enumerate(reversed(v),1):rank=len(v)-rr+1;run=min(run,p*len(v)/rank);out[i]=min(1.,run)
    return out

def path_text(path):return " AND ".join(f"{f} {op} {t:.6g}" for f,op,t in path) or "all games"

def main():
    global CURRENT_MARKET
    OUT.mkdir(parents=True,exist_ok=True);d=build();dev=d[d.season<=2023];val=d[d.season.eq(2024)];rules=[];walk=[]
    for market,pbp,outcome in (("ATS",ATS_PBP,"ats_outcome"),("TOTAL",TOTAL_PBP,"total_outcome")):
        CURRENT_MARKET=market;features=MARKET_FEATURES[market]+pbp
        for test_year in (2022,2023,2024):
            tr=d[d.season.lt(test_year)].dropna(subset=features+[outcome]);te=d[d.season.eq(test_year)].dropna(subset=features+[outcome]);tree=grow(tr,features,outcome)
            bets=[]
            for leaf in leaves(tree):
                z=te.loc[mask(te,leaf["path"]),outcome];bets.extend((leaf["action"]*z).tolist())
            s=summary(pd.Series(bets),1);walk.append({"market":market,"train_through":test_year-1,"test_year":test_year,**s})
        train=dev.dropna(subset=features+[outcome]);test=val.dropna(subset=features+[outcome]);tree=grow(train,features,outcome)
        (OUT/f"{market.lower()}_tree.json").write_text(json.dumps(tree,indent=2)+"\n")
        for i,leaf in enumerate(leaves(tree),1):
            dm=mask(train,leaf["path"]);pm=mask(train,leaf["path"],True);action=leaf["action"];ds=summary(train.loc[dm,outcome],action);parent=summary(train.loc[pm,outcome],action);lift=ds["raw_win_rate"]-parent["raw_win_rate"]
            if ds["n"]>=100 and ds["shrunk_win_rate"]>=.53 and ds["mean_residual"]>=.5 and lift>=.015:
                vm=mask(test,leaf["path"]);vpm=mask(test,leaf["path"],True);vs=summary(test.loc[vm,outcome],action);vp=summary(test.loc[vpm,outcome],action)
                annual={}
                for year in (2021,2022,2023,2024):
                    yd=d[d.season.eq(year)].dropna(subset=features+[outcome]); ys=summary(yd.loc[mask(yd,leaf["path"]),outcome],action)
                    annual.update({f"year_{year}_n":ys["n"],f"year_{year}_wins":ys["wins"],f"year_{year}_losses":ys["losses"],f"year_{year}_win_rate":ys["raw_win_rate"],f"year_{year}_mean_residual":ys["mean_residual"]})
                rules.append({"market":market,"rule_id":f"{market.lower()}_{i}","rule":path_text(leaf["path"]),"action":("underdog" if action==1 else "favorite") if market=="ATS" else ("over" if action==1 else "under"),**{f"development_{k}":v for k,v in ds.items()},"development_parent_win_rate":parent["raw_win_rate"],"development_incremental_lift":lift,**{f"validation_{k}":v for k,v in vs.items()},"validation_parent_win_rate":vp["raw_win_rate"],"validation_incremental_lift":vs["raw_win_rate"]-vp["raw_win_rate"],**annual})
    pd.DataFrame(walk).to_csv(OUT/"walk_forward_audit.csv",index=False)
    q=pd.DataFrame(rules)
    if len(q):
        q["validation_q_value"]=bh(q.validation_p.tolist());q["evidence_grade"]="rejected_or_inconclusive"
        promising=q.validation_mean_residual.ge(.5)&q.validation_shrunk_win_rate.ge(.51)&q.validation_incremental_lift.gt(0)&q.validation_n.ge(30);q.loc[promising,"evidence_grade"]="promising_unconfirmed"
        valid=promising&q.validation_shrunk_win_rate.ge(.53)&q.validation_q_value.le(.10);q.loc[valid,"evidence_grade"]="validated_2024"
    else:q=pd.DataFrame(columns=["market","rule_id","rule","action","evidence_grade"])
    q.to_csv(OUT/"admitted_rule_validation.csv",index=False)
    result={"development_rows":len(dev),"validation_rows":len(val),"admitted_rules":len(q),"validated_2024":int((q.evidence_grade=="validated_2024").sum()) if len(q) else 0,"promising_unconfirmed":int((q.evidence_grade=="promising_unconfirmed").sum()) if len(q) else 0,"locked_2025":"excluded"}
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2));print(q.to_string(index=False));print(pd.DataFrame(walk).to_string(index=False))

if __name__=="__main__":main()
