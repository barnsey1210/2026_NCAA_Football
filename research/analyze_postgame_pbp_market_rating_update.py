#!/usr/bin/env python3
"""Test whether a completed game's PBP predicts the team's next market valuation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GAMES = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
PBP = ROOT / "data/research/pbp_history_2021_2025/team_game_tendencies.csv"
OUT = ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024"
HFA, WINDOW, SHRINK = 2.5, 6, 8.0

SCORE = ["team_margin", "team_closing_spread", "team_ats_margin", "abs_team_closing_spread"]
PBP_FEATURES = [
    "off_success_rate", "off_ppa", "off_explosiveness", "off_rush_success_rate",
    "off_pass_success_rate", "off_neutral_pass_rate", "off_qb_run_share",
    "def_success_allowed", "def_ppa_allowed", "def_explosiveness_allowed",
    "def_havoc_rate", "off_drive_elapsed_seconds_per_play", "off_plays",
]

def weekly_ratings(games):
    """Rolling ridge solution of closing spreads available before each week."""
    out = {}
    for season, season_games in games.groupby("season"):
        teams = sorted(set(season_games.home_team) | set(season_games.away_team)); idx = {t:i for i,t in enumerate(teams)}
        for week in sorted(season_games.week.unique()):
            hist = season_games[(season_games.week < week) & (season_games.week >= week-WINDOW)]
            if hist.empty:
                out[(season, week)] = {t:0.0 for t in teams}; continue
            x=np.zeros((len(hist),len(teams))); y=np.zeros(len(hist))
            for j,(_,r) in enumerate(hist.iterrows()):
                x[j,idx[r.home_team]]=1; x[j,idx[r.away_team]]=-1
                y[j]=-float(r.closing_home_spread)-HFA
            a=x.T@x+SHRINK*np.eye(len(teams)); b=x.T@y
            rating=np.linalg.solve(a,b); rating-=rating.mean()
            out[(season,week)]={t:float(rating[idx[t]]) for t in teams}
    return out

def team_rows(g, ratings):
    rows=[]
    for _,r in g.iterrows():
        rt=ratings[(r.season,r.week)]; predicted=rt.get(r.home_team,0)-rt.get(r.away_team,0)+HFA
        actual=-float(r.closing_home_spread); innovation=actual-predicted
        for side in ("home","away"):
            home=side=="home"; team=r.home_team if home else r.away_team; opp=r.away_team if home else r.home_team
            margin=(r.home_score-r.away_score)*(1 if home else -1); spread=float(r.closing_home_spread)*(1 if home else -1)
            rows.append({"season":r.season,"week":r.week,"game_id":r.game_id,"team":team,"opponent":opp,
                         "team_margin":margin,"team_closing_spread":spread,"team_ats_margin":margin+spread,
                         "abs_team_closing_spread":abs(spread),"market_innovation":innovation*(1 if home else -1)})
    d=pd.DataFrame(rows).sort_values(["season","team","week"])
    d["next_week"]=d.groupby(["season","team"]).week.shift(-1)
    d["target_next_market_innovation"]=d.groupby(["season","team"]).market_innovation.shift(-1)
    d["weeks_to_next_game"]=d.next_week-d.week
    return d

def evaluate(train, test, features):
    x=train[features].apply(pd.to_numeric,errors="coerce").to_numpy(float); xt=test[features].apply(pd.to_numeric,errors="coerce").to_numpy(float)
    med=np.nanmedian(x,axis=0); med=np.where(np.isfinite(med),med,0.0); x=np.where(np.isnan(x),med,x);xt=np.where(np.isnan(xt),med,xt)
    mean=x.mean(axis=0);std=x.std(axis=0);std=np.where(std>1e-9,std,1.0);x=(x-mean)/std;xt=(xt-mean)/std
    x=np.column_stack([np.ones(len(x)),x]);xt=np.column_stack([np.ones(len(xt)),xt]);penalty=20*np.eye(x.shape[1]);penalty[0,0]=0
    beta=np.linalg.solve(x.T@x+penalty,x.T@train.target_next_market_innovation.to_numpy());pred=xt@beta;y=test.target_next_market_innovation.to_numpy(); base=np.zeros(len(y))
    mae=lambda a,b:float(np.mean(np.abs(a-b))); base_mae=mae(y,base);model_mae=mae(y,pred)
    return {"n":len(y),"baseline_mae":base_mae,"model_mae":model_mae,
            "mae_improvement_pct":100*(base_mae-model_mae)/base_mae,
            "direction_accuracy":float(np.mean(np.sign(pred)==np.sign(y))),"prediction_target_correlation":float(np.corrcoef(pred,y)[0,1]),
            "prediction":pred}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    g=pd.read_csv(GAMES,low_memory=False); g=g[g.closing_home_spread.notna()].copy()
    ratings=weekly_ratings(g); rows=team_rows(g,ratings)
    pbp=pd.read_csv(PBP,low_memory=False); rows=rows.merge(pbp[["season","week","game_id","team"]+PBP_FEATURES],on=["season","week","game_id","team"],how="left")
    rows=rows[(rows.weeks_to_next_game>=1)&(rows.weeks_to_next_game<=3)&rows.target_next_market_innovation.notna()].copy()
    train=rows[rows.season<=2023]; val=rows[rows.season==2024]
    score=evaluate(train,val,SCORE); full=evaluate(train,val,SCORE+PBP_FEATURES)
    summary={"design":{"development":"2021-2023","validation":"2024","holdout":"2025 untouched unless validation passes","hfa":HFA,"rating_window_weeks":WINDOW,"rating_ridge":SHRINK,"model_ridge":20.0},
             "score_only":{k:v for k,v in score.items() if k!="prediction"},"score_plus_pbp":{k:v for k,v in full.items() if k!="prediction"}}
    summary["pbp_incremental_mae_vs_score_pct"]=100*(score["model_mae"]-full["model_mae"])/score["model_mae"]
    summary["validation_pass"] = bool(full["mae_improvement_pct"]>=2 and summary["pbp_incremental_mae_vs_score_pct"]>0 and full["prediction_target_correlation"]>0.05)
    valout=val[["season","week","game_id","team","opponent","target_next_market_innovation"]].copy();valout["score_prediction"]=score["prediction"];valout["score_pbp_prediction"]=full["prediction"];valout.to_csv(OUT/"validation_2024_predictions.csv",index=False)
    if summary["validation_pass"]:
        hold_train=rows[rows.season<=2024];hold=rows[rows.season==2025]
        hs=evaluate(hold_train,hold,SCORE);hf=evaluate(hold_train,hold,SCORE+PBP_FEATURES)
        summary["holdout_2025_score_only"]={k:v for k,v in hs.items() if k!="prediction"}
        summary["holdout_2025_score_plus_pbp"]={k:v for k,v in hf.items() if k!="prediction"}
        summary["holdout_2025_pbp_incremental_mae_vs_score_pct"]=100*(hs["model_mae"]-hf["model_mae"])/hs["model_mae"]
        summary["holdout_pass"]=bool(hf["mae_improvement_pct"]>=2 and summary["holdout_2025_pbp_incremental_mae_vs_score_pct"]>0 and hf["prediction_target_correlation"]>0.05)
        hout=hold[["season","week","game_id","team","opponent","target_next_market_innovation"]].copy();hout["score_prediction"]=hs["prediction"];hout["score_pbp_prediction"]=hf["prediction"];hout.to_csv(OUT/"holdout_2025_predictions.csv",index=False)
    rows.to_csv(OUT/"modeling_rows_2021_2025.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"README.md").write_text("# Postgame PBP -> next market rating update\n\nTarget: team-perspective innovation in its next closing spread after removing 2.5 points of home field and both teams' rolling six-week market ratings. Garbage-time-filtered PBP is tested incrementally over final score and the prior closing spread. Development is 2021-23; 2024 is validation; 2025 remains untouched unless the frozen validation rule passes.\n\n```json\n"+json.dumps(summary,indent=2)+"\n```\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
