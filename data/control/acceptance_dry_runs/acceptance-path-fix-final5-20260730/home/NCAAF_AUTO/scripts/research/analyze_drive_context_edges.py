#!/usr/bin/env python3
"""Run the frozen drive-context matchup edge validation."""

from __future__ import annotations

import json, math
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path("data/research/drive_context_edges_2021_2024")
MARKETS = Path("data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv")
DRIVES = Path("data/research/drive_context_2021_2025/rolling_pregame_drive_context.csv")

SPECS = [
    ("ats_field_position_advantage", "ATS", "away", "home"),
    ("ats_opportunity_creation_advantage", "ATS", "away", "home"),
    ("ats_finishing_points_advantage", "ATS", "away", "home"),
    ("ats_finishing_td_advantage", "ATS", "away", "home"),
    ("ats_points_per_drive_advantage", "ATS", "away", "home"),
    ("total_field_position_environment", "TOTAL", "under", "over"),
    ("total_opportunity_creation_environment", "TOTAL", "under", "over"),
    ("total_finishing_points_environment", "TOTAL", "under", "over"),
    ("total_finishing_td_environment", "TOTAL", "under", "over"),
    ("total_points_per_drive_environment", "TOTAL", "under", "over"),
]

def stats(s):
    v=pd.to_numeric(s,errors="coerce").dropna().to_numpy(float); w=int((v>0).sum()); l=int((v<0).sum()); p=int((v==0).sum()); n=w+l
    mean=float(v.mean()) if len(v) else np.nan; sd=float(v.std(ddof=1)) if len(v)>1 else np.nan
    se=sd/math.sqrt(len(v)) if len(v)>1 and sd>0 else np.nan; z=mean/se if se and not np.isnan(se) else np.nan
    return {"n":len(v),"wins":w,"losses":l,"pushes":p,"raw_win_rate":w/n if n else np.nan,
            "shrunk_win_rate":(w+10)/(n+20) if n else np.nan,"mean_market_residual":mean,
            "one_sided_positive_p":.5*math.erfc(z/math.sqrt(2)) if not np.isnan(z) else np.nan}

def bh(ps):
    out=[np.nan]*len(ps); valid=sorted(((i,p) for i,p in enumerate(ps) if not pd.isna(p)),key=lambda x:x[1]); run=1.0
    for rr,(i,p) in enumerate(reversed(valid),1):
        rank=len(valid)-rr+1; run=min(run,p*len(valid)/rank); out[i]=min(1.0,run)
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=pd.read_csv(MARKETS,usecols=["game_id","season","week","split","eligible_week5_plus","closing_spread_residual","closing_total_residual"])
    r=pd.read_csv(DRIVES)
    keep=["game_id","team","prior_games","pregame_off_avg_start_ytg","pregame_off_opportunity_rate",
          "pregame_off_points_per_opportunity","pregame_off_td_rate_per_opportunity","pregame_off_points_per_drive",
          "pregame_def_opponent_avg_start_ytg","pregame_def_opportunity_rate_allowed",
          "pregame_def_points_per_opportunity_allowed","pregame_def_td_rate_per_opportunity_allowed",
          "pregame_def_points_per_drive_allowed"]
    # Recover home/away identities from the existing market table's joined tendency columns.
    ids=pd.read_csv(MARKETS,usecols=["game_id","home_team","away_team"]).drop_duplicates("game_id")
    d=m.merge(ids,on="game_id")
    for side in ("home","away"):
        z=r[keep].rename(columns={c:f"{side}_{c}" for c in keep if c not in ("game_id",)})
        d=d.merge(z,left_on=["game_id",f"{side}_team"],right_on=["game_id",f"{side}_team"],how="left")
    d=d[(d.season<=2024)&d.eligible_week5_plus.astype(str).str.lower().eq("true")].copy()

    for side,opp in (("home","away"),("away","home")):
        d[f"{side}_start"]=(d[f"{side}_pregame_off_avg_start_ytg"]+d[f"{opp}_pregame_def_opponent_avg_start_ytg"])/2
        for short in ("opportunity_rate","points_per_opportunity","td_rate_per_opportunity","points_per_drive"):
            defensive={"opportunity_rate":"opportunity_rate_allowed","points_per_opportunity":"points_per_opportunity_allowed",
                       "td_rate_per_opportunity":"td_rate_per_opportunity_allowed","points_per_drive":"points_per_drive_allowed"}[short]
            d[f"{side}_{short}"]=(d[f"{side}_pregame_off_{short}"]+d[f"{opp}_pregame_def_{defensive}"])/2
    d["ats_field_position_advantage"]=d.away_start-d.home_start
    d["ats_opportunity_creation_advantage"]=d.home_opportunity_rate-d.away_opportunity_rate
    d["ats_finishing_points_advantage"]=d.home_points_per_opportunity-d.away_points_per_opportunity
    d["ats_finishing_td_advantage"]=d.home_td_rate_per_opportunity-d.away_td_rate_per_opportunity
    d["ats_points_per_drive_advantage"]=d.home_points_per_drive-d.away_points_per_drive
    d["total_field_position_environment"]=-(d.home_start+d.away_start)
    d["total_opportunity_creation_environment"]=d.home_opportunity_rate+d.away_opportunity_rate
    d["total_finishing_points_environment"]=d.home_points_per_opportunity+d.away_points_per_opportunity
    d["total_finishing_td_environment"]=d.home_td_rate_per_opportunity+d.away_td_rate_per_opportunity
    d["total_points_per_drive_environment"]=d.home_points_per_drive+d.away_points_per_drive
    dev=d[d.split.eq("development")]; val=d[d.split.eq("validation")]; rows=[]
    for key,market,low_action,high_action in SPECS:
        lo,hi=dev[key].quantile([.2,.8]).tolist()
        for tail,t,action in (("low",lo,low_action),("high",hi,high_action)):
            dm=dev[key].le(t) if tail=="low" else dev[key].ge(t); vm=val[key].le(t) if tail=="low" else val[key].ge(t)
            col="closing_spread_residual" if market=="ATS" else "closing_total_residual"; dv=dev.loc[dm,col]; vv=val.loc[vm,col]
            if action in ("away","under"): dv=-dv; vv=-vv
            sign=-1 if action in ("away","under") else 1
            pos=sum(int((sign*dev.loc[dm&dev.season.eq(s),col]).mean()>0) for s in (2021,2022,2023))
            row={"feature":key,"market":market,"tail":tail,"threshold":t,"action":action,"development_positive_seasons":pos}
            row.update({f"development_{k}":v for k,v in stats(dv).items()}); row.update({f"validation_{k}":v for k,v in stats(vv).items()}); rows.append(row)
    q=pd.DataFrame(rows); q["validation_q_value"]=bh(q.validation_one_sided_positive_p.tolist()); q["evidence_grade"]="rejected_or_inconclusive"
    promising=(q.development_mean_market_residual.ge(.5)&q.validation_mean_market_residual.ge(.5)&q.development_shrunk_win_rate.ge(.51)&q.validation_shrunk_win_rate.ge(.51)&q.validation_n.ge(30)&q.development_positive_seasons.ge(2))
    q.loc[promising,"evidence_grade"]="promising_unconfirmed"; validated=promising&q.validation_q_value.le(.10)&q.validation_shrunk_win_rate.ge(.53); q.loc[validated,"evidence_grade"]="validated_2024"
    q=q.sort_values(["evidence_grade","validation_q_value"]); q.to_csv(OUT/"feature_edge_validation.csv",index=False)
    summary={"protocol":"Frozen drive-context features; 2021-2023 development; 2024 validation; 2025 excluded","feature_families":10,"tail_tests":20,"development_rows":len(dev),"validation_rows":len(val),"validated_2024":int((q.evidence_grade=="validated_2024").sum()),"promising_unconfirmed":int((q.evidence_grade=="promising_unconfirmed").sum()),"rejected_or_inconclusive":int((q.evidence_grade=="rejected_or_inconclusive").sum())}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n"); print(json.dumps(summary,indent=2)); print(q[["feature","tail","action","development_n","development_mean_market_residual","validation_n","validation_mean_market_residual","validation_shrunk_win_rate","validation_q_value","evidence_grade"]].to_string(index=False))

if __name__=="__main__": main()
