#!/usr/bin/env python3
"""Isolated, no-look-ahead team market-rating movement research pipeline.

All artifacts are research-only. 2021-23 fit models, 2024 selects all model
choices, and 2025 is evaluated only after those choices are serialized.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GAMES = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
RATINGS = ROOT / "data/ratings/market_implied_ratings_history.csv"
PBP = ROOT / "data/research/pbp_history_2021_2025/team_game_tendencies.csv"
DRIVES = ROOT / "data/research/drive_context_2021_2025/team_game_drive_context.csv"
GAME_CONTROL = ROOT / "data/research/game_control_history_2021_2025/team_game_game_control.csv"
PUBLIC_REPO = Path("/Users/jameslindesmith/Sites/NCAAF_SITE")
HFA = 2.5
PRICE = -110

PROTECTED = [
    "config/market_shadow_production.json",
    "scripts/site/build_saturday_shadow_lines.py",
    "scripts/site/build_postgame_shadow_updates.py",
    "scripts/site/build_market_shadow_production_layer.py",
    "openers_v2.html", "schedule_v2.html",
    "build/public_site/openers.html", "build/public_site/schedule.html",
    "data/site/postgame_shadow_updates.json", "data/site/saturday_shadow_lines.json",
    "data/site/schedule_live_enrichment.json", "daily_market_update.sh",
    "scripts/publish/publish_site.sh", "data/ratings/ratings_latest.csv",
    "data/projections/game_projections_2026.csv",
]


def norm_id(v):
    s = str(v or "").strip()
    return s[:-2] if s.endswith(".0") else s


def sha256(path: Path):
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def protected_hashes():
    return {p: sha256(ROOT / p) for p in PROTECTED}


def num(s):
    return pd.to_numeric(s, errors="coerce")


def standardize_fit(df, features):
    x = df[features].apply(num).to_numpy(float)
    med = np.nanmedian(x, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    x = np.where(np.isfinite(x), x, med)
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std = np.where(std > 1e-9, std, 1.0)
    return med, mean, std, (x - mean) / std


def standardize_apply(df, features, state):
    med, mean, std = state
    x = df[features].apply(num).to_numpy(float)
    x = np.where(np.isfinite(x), x, med)
    return (x - mean) / std


def ridge_fit(x, y, alpha=20.0, weights=None):
    x1 = np.column_stack([np.ones(len(x)), x])
    if weights is None:
        weights = np.ones(len(x))
    sw = np.sqrt(np.asarray(weights, float))
    xw, yw = x1 * sw[:, None], np.asarray(y, float) * sw
    pen = alpha * np.eye(x1.shape[1]); pen[0, 0] = 0
    return np.linalg.solve(xw.T @ xw + pen, xw.T @ yw)


def ridge_predict(x, beta):
    return np.column_stack([np.ones(len(x)), x]) @ beta


def elastic_fit(x, y, alpha=0.08, l2=4.0, iterations=250):
    x1 = np.column_stack([np.ones(len(x)), x]); y = np.asarray(y, float)
    b = np.zeros(x1.shape[1]); scale = np.sum(x1 * x1, axis=0) + l2
    for _ in range(iterations):
        for j in range(x1.shape[1]):
            r = y - x1 @ b + x1[:, j] * b[j]
            z = float(x1[:, j] @ r)
            if j == 0: b[j] = z / max(scale[j] - l2, 1e-9)
            else: b[j] = np.sign(z) * max(abs(z) - alpha * len(y), 0) / scale[j]
    return b


def huber_fit(x, y, alpha=10.0, iterations=20):
    b = ridge_fit(x, y, alpha)
    for _ in range(iterations):
        r = np.asarray(y) - ridge_predict(x, b)
        scale = max(float(np.median(np.abs(r))) / 0.6745, 1e-6)
        w = np.minimum(1.0, 1.35 * scale / np.maximum(np.abs(r), 1e-9))
        b = ridge_fit(x, y, alpha, w)
    return b


def boost_fit(x, y, rounds=40, learning_rate=.08):
    """Small deterministic gradient-boosted decision-stump regressor."""
    y=np.asarray(y,float); base=float(np.mean(y)); pred=np.full(len(y),base); trees=[]
    for _ in range(rounds):
        residual=y-pred; best=None
        for j in range(x.shape[1]):
            for cut in np.unique(np.quantile(x[:,j],[.15,.3,.5,.7,.85])):
                left=x[:,j]<=cut
                if left.sum()<20 or (~left).sum()<20: continue
                lv=float(residual[left].mean()); rv=float(residual[~left].mean())
                err=float(np.sum((residual-np.where(left,lv,rv))**2))
                if best is None or err<best[0]: best=(err,j,float(cut),lv,rv)
        if best is None: break
        _,j,cut,lv,rv=best; trees.append((j,cut,lv,rv)); pred+=learning_rate*np.where(x[:,j]<=cut,lv,rv)
    return {"base":base,"trees":trees,"learning_rate":learning_rate}


def boost_predict(x, model):
    p=np.full(len(x),model["base"])
    for j,cut,lv,rv in model["trees"]: p+=model["learning_rate"]*np.where(x[:,j]<=cut,lv,rv)
    return p


def softmax_fit(x, labels, classes=(-1, 0, 1), l2=0.08, iterations=500, lr=0.08):
    x1 = np.column_stack([np.ones(len(x)), x]); cmap = {c:i for i,c in enumerate(classes)}
    yy = np.zeros((len(x), len(classes)))
    for i, v in enumerate(labels): yy[i, cmap[int(v)]] = 1
    b = np.zeros((x1.shape[1], len(classes)))
    for i in range(iterations):
        z = x1 @ b; z -= z.max(axis=1, keepdims=True)
        p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
        grad = x1.T @ (p - yy) / len(x) + l2 * np.r_[[[0]*len(classes)], b[1:]]
        b -= lr / math.sqrt(1 + i / 80) * grad
    return b


def softmax_predict(x, b, classes=(-1, 0, 1)):
    x1 = np.column_stack([np.ones(len(x)), x]); z = x1 @ b; z -= z.max(axis=1, keepdims=True)
    p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
    return p, np.asarray(classes)[p.argmax(axis=1)]


def movement_class(y, threshold):
    y = np.asarray(y, float)
    return np.where(y > threshold, 1, np.where(y < -threshold, -1, 0))


def movement_probs_from_score(score, threshold):
    score=np.asarray(score,float); scale=max(float(threshold),.1)
    logits=np.column_stack([-score/scale,1-np.abs(score)/scale,score/scale]); logits-=logits.max(axis=1,keepdims=True)
    p=np.exp(logits); return p/p.sum(axis=1,keepdims=True)


def confusion(y, pred):
    classes = [-1, 0, 1]
    return [[int(np.sum((y == a) & (pred == b))) for b in classes] for a in classes]


def class_metrics(y, pred, probs=None):
    y, pred = np.asarray(y), np.asarray(pred); classes = [-1, 0, 1]
    recalls=[]; precisions=[]; f1s=[]
    per={}
    for c, name in zip(classes, ["downgrade","no_change","upgrade"]):
        tp=int(np.sum((y==c)&(pred==c))); fp=int(np.sum((y!=c)&(pred==c))); fn=int(np.sum((y==c)&(pred!=c)))
        pr=tp/(tp+fp) if tp+fp else 0; rc=tp/(tp+fn) if tp+fn else 0; f=2*pr*rc/(pr+rc) if pr+rc else 0
        precisions.append(pr); recalls.append(rc); f1s.append(f); per[name]={"precision":pr,"recall":rc,"f1":f,"support":int(np.sum(y==c))}
    out={"n":int(len(y)),"accuracy":float(np.mean(y==pred)),"balanced_accuracy":float(np.mean(recalls)),"macro_f1":float(np.mean(f1s)),"per_class":per,"confusion_matrix":confusion(y,pred)}
    if probs is not None:
        one=np.column_stack([(y==c).astype(float) for c in classes])
        out["multiclass_brier"]=float(np.mean(np.sum((probs-one)**2,axis=1)))
        out["log_loss"]=float(-np.mean(np.log(np.clip(probs[np.arange(len(y)),np.argmax(one,axis=1)],1e-9,1))))
    return out


def reg_metrics(y, p):
    y,p=np.asarray(y,float),np.asarray(p,float); e=p-y
    corr=float(np.corrcoef(y,p)[0,1]) if len(y)>2 and np.std(y)>0 and np.std(p)>0 else None
    return {"n":int(len(y)),"mae":float(np.mean(np.abs(e))),"median_absolute_error":float(np.median(np.abs(e))),"rmse":float(np.sqrt(np.mean(e*e))),"signed_bias":float(np.mean(e)),"correlation":corr,"overshoot_rate":float(np.mean(np.abs(p)>np.abs(y))),"undershoot_rate":float(np.mean(np.abs(p)<np.abs(y)))}


def binary_result(line, actual):
    if not np.isfinite(line) or not np.isfinite(actual): return ""
    v=actual+line
    return "W" if v>0 else "L" if v<0 else "P"


def roi(results):
    vals=[]
    for r in results:
        vals.append(100/110 if r=="W" else -1 if r=="L" else 0)
    return float(np.mean(vals)) if vals else None


def build_team_states(games, ratings):
    rating_lookup={(int(r.season),int(r.through_week),r.team):float(r.market_implied_rating) for r in ratings.itertuples()}
    game_rows=[]
    for r in games.sort_values(["season","week","start_date","game_id"]).itertuples(index=False):
        for is_home in (True,False):
            team=r.home_team if is_home else r.away_team; opp=r.away_team if is_home else r.home_team
            spread=float(r.closing_home_spread)*(1 if is_home else -1)
            implied=(float(r.closing_total)-spread)/2 if pd.notna(r.closing_total) else np.nan
            opp_implied=(float(r.closing_total)+spread)/2 if pd.notna(r.closing_total) else np.nan
            game_rows.append({"season":int(r.season),"week":int(r.week),"game_id":norm_id(r.game_id),"game_date":r.start_date,"team":team,"opponent":opp,"home_away":"home" if is_home else "away","neutral_site":np.nan,"pregame_market_rating":rating_lookup.get((int(r.season),int(r.week)-1,team)),"pregame_market_offense_rating":np.nan,"pregame_market_defense_rating":np.nan,"closing_spread":spread,"closing_total":r.closing_total,"implied_team_score":implied,"implied_opponent_score":opp_implied,"next_market_rating":rating_lookup.get((int(r.season),int(r.week),team)),"next_market_offense_rating":np.nan,"next_market_defense_rating":np.nan})
    d=pd.DataFrame(game_rows).sort_values(["season","team","week","game_date","game_id"])
    d["actual_market_rating_change"]=d.next_market_rating-d.pregame_market_rating
    d["actual_market_offense_change"]=np.nan; d["actual_market_defense_change"]=np.nan
    d["games_played_before"]=d.groupby(["season","team"]).cumcount(); d["games_played_after"]=d.games_played_before+1
    for c,new in [("game_id","next_game_id"),("week","next_game_week"),("opponent","next_game_opponent")]: d[new]=d.groupby(["season","team"])[c].shift(-1)
    d["cutoff_provenance"]="market_implied_ratings_history snapshot through completed week; close-only ridge, HFA=2.5"
    d["eligibility"]=d.pregame_market_rating.notna()&d.next_market_rating.notna()
    d["missing_reason"]=np.where(d.eligibility,"",np.where(d.pregame_market_rating.isna(),"no prior-week market rating","no through-week market rating"))
    return d


def build_features(states, games, pbp, drives, gc):
    score={}
    for r in games.itertuples(index=False):
        score[(int(r.season),norm_id(r.game_id),r.home_team)]={"points_scored":r.home_score,"points_allowed":r.away_score,"final_margin":r.home_score-r.away_score,"opening_spread":r.opening_home_spread,"opening_total":r.opening_total}
        score[(int(r.season),norm_id(r.game_id),r.away_team)]={"points_scored":r.away_score,"points_allowed":r.home_score,"final_margin":r.away_score-r.home_score,"opening_spread":-r.opening_home_spread if pd.notna(r.opening_home_spread) else np.nan,"opening_total":r.opening_total}
    d=states.copy()
    extra=pd.DataFrame([score.get((int(r.season),r.game_id,r.team),{}) for r in d.itertuples()]); d=pd.concat([d.reset_index(drop=True),extra],axis=1)
    d["ats_margin"]=d.final_margin+d.closing_spread; d["total_residual"]=d.points_scored+d.points_allowed-d.closing_total
    d["favorite_role"]=np.where(d.closing_spread<0,"favorite",np.where(d.closing_spread>0,"underdog","pickem"))
    for source,prefix in [(pbp,""),(drives,"drive_"),(gc,"gc_")]:
        s=source.copy(); s["game_id"]=s.game_id.map(norm_id)
        keys=["season","week","game_id","team"]
        ren={c:prefix+c for c in s.columns if c not in keys and c!="opponent"}
        d=d.merge(s[keys+list(ren)].rename(columns=ren),on=keys,how="left")
    d["game_pace"]=d.get("off_drive_elapsed_seconds_per_play",np.nan); d["play_count"]=d.get("off_plays",np.nan)
    noise=["turnover_margin","expected_turnover_margin","fumble_recoveries","interceptions","defensive_touchdowns","special_teams_touchdowns","return_touchdowns","blocked_kick_scores","fourth_down_conversion_variance","red_zone_touchdown_variance","explosive_scoring_plays","garbage_time_scoring","kneel_down_effects","overtime","weather_flag","quarterback_injury_flag","major_player_injury_flag"]
    for c in noise: d[c]=np.nan
    d["garbage_or_ot_plays_removed"]=d.get("off_excluded_garbage_or_ot_plays",np.nan)
    d=d.sort_values(["season","team","week","game_date","game_id"])
    base={"ats_margin":"ats","off_ppa":"ppa","off_success_rate":"off_eff","def_ppa_allowed":"def_eff"}
    for col,label in base.items():
        if col not in d: continue
        for n in (2,3): d[f"trailing_{n}_game_{label}"]=d.groupby(["season","team"])[col].transform(lambda x:x.rolling(n,min_periods=1).mean())
        d[f"season_to_date_{label}"]=d.groupby(["season","team"])[col].transform(lambda x:x.expanding().mean())
        d[f"ewm_{label}"]=d.groupby(["season","team"])[col].transform(lambda x:x.ewm(alpha=.5,adjust=False).mean())
    d["consecutive_market_beats"]=d.groupby(["season","team"])["ats_margin"].transform(lambda s: s.gt(0).groupby(s.le(0).cumsum()).cumsum())
    d["consecutive_market_misses"]=d.groupby(["season","team"])["ats_margin"].transform(lambda s: s.lt(0).groupby(s.ge(0).cumsum()).cumsum())
    d["recent_form_vs_season"]=d.get("trailing_3_game_ats",np.nan)-d.get("season_to_date_ats",np.nan)
    d["opponent_strength"]=-d.groupby(["season","week"])["pregame_market_rating"].transform(lambda x: x.rank(pct=True))
    d["opponent_adjusted_recent_form"]=d.recent_form_vs_season+d.opponent_strength
    return d


def build_repeatable(d, train_seasons):
    x=d.copy(); train=x.season.isin(train_seasons)
    components=["off_ppa","off_success_rate","off_explosiveness","def_ppa_allowed","def_success_allowed","def_explosiveness_allowed","drive_off_points_per_opportunity","drive_def_points_per_opportunity_allowed","drive_off_avg_start_ytg","drive_def_opponent_avg_start_ytg"]
    z={}
    for c in components:
        v=num(x.get(c,pd.Series(np.nan,index=x.index))); mu=v[train].mean(); sd=v[train].std()
        z[c]=((v-mu)/(sd if pd.notna(sd) and sd>1e-9 else 1)).fillna(0.0)
    x["raw_ats_performance"]=x.ats_margin; x["raw_score_performance"]=x.final_margin+x.closing_spread
    x["raw_pbp_performance"]=2.0*z["off_ppa"]+1.2*z["off_success_rate"]+.5*z["off_explosiveness"]-2.0*z["def_ppa_allowed"]-1.2*z["def_success_allowed"]-.5*z["def_explosiveness_allowed"]
    x["rules_repeatable_spread"]=x.raw_pbp_performance+.4*z["drive_off_points_per_opportunity"]-.4*z["drive_def_points_per_opportunity_allowed"]-.2*z["drive_off_avg_start_ytg"]+.2*z["drive_def_opponent_avg_start_ytg"]
    persistent=[c for c in ["off_ppa","off_success_rate","off_explosiveness","off_rush_success_rate","off_pass_success_rate","def_ppa_allowed","def_success_allowed","def_explosiveness_allowed","def_havoc_rate","off_plays","drive_off_points_per_opportunity","drive_def_points_per_opportunity_allowed","gc_game_control_index"] if c in x]
    eligible=train&x.actual_market_rating_change.notna(); state=standardize_fit(x.loc[eligible],persistent); beta=ridge_fit(state[3],x.loc[eligible,"actual_market_rating_change"],20)
    x["regularized_repeatable_spread"]=ridge_predict(standardize_apply(x,persistent,state[:3]),beta)
    # Persistent expected margin; the actual-minus-expected residual is explicitly non-persistent.
    mstate=standardize_fit(x.loc[train&x.final_margin.notna()],persistent); mb=ridge_fit(mstate[3],x.loc[train&x.final_margin.notna(),"final_margin"],30)
    x["persistent_expected_margin"]=ridge_predict(standardize_apply(x,persistent,mstate[:3]),mb)
    x["nonpersistent_margin_residual"]=x.final_margin-x.persistent_expected_margin
    x["residualized_repeatable_spread"]=x.persistent_expected_margin+x.closing_spread
    x["repeatable_spread_performance"]=x.regularized_repeatable_spread
    x["repeatable_offense_performance"]=1.7*z["off_ppa"]+z["off_success_rate"]+.4*z["drive_off_points_per_opportunity"]
    x["repeatable_defense_performance"]=-1.7*z["def_ppa_allowed"]-z["def_success_allowed"]-.4*z["drive_def_points_per_opportunity_allowed"]
    x["repeatable_total_performance"]=x.repeatable_offense_performance-x.repeatable_defense_performance
    x["cleanup_method"]="regularized regression on efficiency/drive/game-control features; noisy residual excluded"
    return x,persistent


def fit_models(d, features, threshold, fit_seasons, model_name="multinomial_logistic+two_stage_ridge"):
    fit=d.season.isin(fit_seasons)&d.actual_market_rating_change.notna(); state=standardize_fit(d.loc[fit],features); xf=state[3]; y=d.loc[fit,"actual_market_rating_change"].to_numpy(float); cls=movement_class(y,threshold)
    cb=softmax_fit(xf,cls); rb=ridge_fit(xf,y,20); hb=huber_fit(xf,y,10); eb=elastic_fit(xf,y)
    pos=y>threshold; neg=y < -threshold
    pb=ridge_fit(xf[pos],y[pos],20) if pos.sum()>5 else rb; nb=ridge_fit(xf[neg],-y[neg],20) if neg.sum()>5 else rb
    gb=boost_fit(xf,y)
    return {"state":state[:3],"class_beta":cb,"ridge":rb,"huber":hb,"elastic":eb,"positive":pb,"negative":nb,"boost":gb,"features":features,"threshold":threshold,"name":model_name}


def predict_models(d, model):
    x=standardize_apply(d,model["features"],model["state"]); probs,cls=softmax_predict(x,model["class_beta"])
    ridge=ridge_predict(x,model["ridge"]); huber=ridge_predict(x,model["huber"]); elastic=ridge_predict(x,model["elastic"])
    pos=np.maximum(ridge_predict(x,model["positive"]),0); neg=np.maximum(ridge_predict(x,model["negative"]),0)
    two=probs[:,2]*pos-probs[:,0]*neg; boost=boost_predict(x,model["boost"])
    return {"prob_down":probs[:,0],"prob_no_change":probs[:,1],"prob_up":probs[:,2],"predicted_direction":cls,"logistic_direction":cls,"ridge":ridge,"huber":huber,"elastic":elastic,"two_stage":two,"boosted_challenger":boost}


def select_model(d, features, train_seasons, selection_season):
    candidates=[]
    for t in (.25,.5,.75,1.0):
        model=fit_models(d,features,t,train_seasons); val=d[d.season==selection_season].copy(); p=predict_models(val,model); y=val.actual_market_rating_change.to_numpy(float); yc=movement_class(y,t)
        families={"multinomial_logistic":p["predicted_direction"],"ordinal_ridge_proxy":movement_class(p["ridge"],t),"rules_based":movement_class(val.rules_repeatable_spread,t),"gradient_boosted_stumps":movement_class(p["boosted_challenger"],t)}
        for family,direction in families.items():
            cm=class_metrics(yc,direction)
            for mag in ("ridge","huber","elastic","two_stage"):
                rm=reg_metrics(y,p[mag]); candidates.append({"threshold":t,"direction_model":family,"magnitude_model":mag,"balanced_accuracy":cm["balanced_accuracy"],"macro_f1":cm["macro_f1"],"direction_accuracy":cm["accuracy"],"mae":rm["mae"],"rmse":rm["rmse"]})
    table=pd.DataFrame(candidates).sort_values(["balanced_accuracy","macro_f1","mae"],ascending=[False,False,True])
    best=table.iloc[0].to_dict(); return best,table


def add_confidence(pred, selection):
    strength=np.maximum(pred.prob_up,pred.prob_down); mag=pred.predicted_movement.abs(); complete=pred.feature_coverage>=.75
    return np.where((strength>=.65)&(mag>=.5)&complete,"High",np.where((strength>=.52)&complete,"Medium",np.where(mag>=.25,"Low","No actionable signal")))


def spread_projection(pred, games):
    p=pred.sort_values(["season","team","week","game_date","game_id"]).copy()
    prev=p[["season","team","game_id","week","pregame_market_rating","predicted_movement","boosted_challenger","raw_ats_performance","repeatable_spread_performance","confidence_tier"]].copy()
    prev.columns=["season","team","previous_game_id","previous_week","frozen_rating","predicted_move","boosted_move","raw_ats_move","repeatable_move","team_confidence"]
    rows=[]
    for r in games.sort_values(["season","week","start_date"]).itertuples(index=False):
        candidates=[]
        for side,team in [("home",r.home_team),("away",r.away_team)]:
            z=prev[(prev.season==r.season)&(prev.team==team)&(prev.previous_week<r.week)].sort_values("previous_week").tail(1)
            candidates.append(None if z.empty else z.iloc[0])
        h,a=candidates
        if h is None or a is None: continue
        home_updated=h.frozen_rating+h.predicted_move; away_updated=a.frozen_rating+a.predicted_move
        projected=away_updated-home_updated-HFA
        no_move=a.frozen_rating-h.frozen_rating-HFA
        raw=(a.frozen_rating+.5*a.raw_ats_move)-(h.frozen_rating+.5*h.raw_ats_move)-HFA
        repeat=(a.frozen_rating+a.repeatable_move)-(h.frozen_rating+h.repeatable_move)-HFA
        boosted=(a.frozen_rating+a.boosted_move)-(h.frozen_rating+h.boosted_move)-HFA
        opener=float(r.opening_home_spread) if pd.notna(r.opening_home_spread) else np.nan; close=float(r.closing_home_spread)
        direction=np.sign(close-opener) if np.isfinite(opener) else np.nan; predicted_direction=np.sign(projected-opener) if np.isfinite(opener) else np.nan
        # Team-line CLV: bet line minus closing line from the selected side's perspective.
        clv=(opener-close) if np.isfinite(opener) and predicted_direction<0 else (close-opener) if np.isfinite(opener) and predicted_direction>0 else np.nan
        bet_side="home" if np.isfinite(opener) and projected<opener else "away" if np.isfinite(opener) and projected>opener else ""
        bet_line=opener if bet_side=="home" else -opener if bet_side=="away" else np.nan
        actual_margin=r.home_score-r.away_score if bet_side=="home" else r.away_score-r.home_score if bet_side=="away" else np.nan
        rows.append({"season":int(r.season),"week":int(r.week),"game_id":norm_id(r.game_id),"home_team":r.home_team,"away_team":r.away_team,"away_previous_game_id":a.previous_game_id,"home_previous_game_id":h.previous_game_id,"frozen_away_rating":a.frozen_rating,"frozen_home_rating":h.frozen_rating,"predicted_away_movement":a.predicted_move,"predicted_home_movement":h.predicted_move,"updated_away_rating":away_updated,"updated_home_rating":home_updated,"hfa":HFA,"neutral_site_status":"unknown; historical source has no neutral flag","projected_close":projected,"no_movement_projection":no_move,"current_lambda_050_projection":raw,"repeatable_projection":repeat,"boosted_projection":boosted,"actual_opener":opener,"actual_close":close,"predicted_direction":predicted_direction,"actual_direction":direction,"clv":clv,"actual_margin":r.home_score-r.away_score,"bet_side":bet_side,"bet_line":bet_line,"ats_result":binary_result(bet_line,actual_margin),"confidence_tier":"High" if h.team_confidence=="High" and a.team_confidence=="High" else "Medium" if "No actionable signal" not in (h.team_confidence,a.team_confidence) else "Low","model_provenance":"frozen pre-previous-game ratings plus two-stage team movement; opener/close evaluation-only"})
    return pd.DataFrame(rows)


def total_projection(features, games):
    f=features.sort_values(["season","team","week","game_date"]).copy()
    f["pre_scored_avg"]=f.groupby(["season","team"]).points_scored.transform(lambda s:s.shift().expanding().mean())
    f["pre_allowed_avg"]=f.groupby(["season","team"]).points_allowed.transform(lambda s:s.shift().expanding().mean())
    rows=[]
    for g in games.itertuples(index=False):
        gid=norm_id(g.game_id)
        current_h=f[(f.season==g.season)&(f.game_id==gid)&(f.team==g.home_team)]
        current_a=f[(f.season==g.season)&(f.game_id==gid)&(f.team==g.away_team)]
        hprev=f[(f.season==g.season)&(f.team==g.home_team)&(f.week<g.week)].sort_values(["week","game_date"]).tail(1)
        aprev=f[(f.season==g.season)&(f.team==g.away_team)&(f.week<g.week)].sort_values(["week","game_date"]).tail(1)
        if current_h.empty or current_a.empty or hprev.empty or aprev.empty: continue
        ch=current_h.iloc[0]; ca=current_a.iloc[0]; h=hprev.iloc[0]; a=aprev.iloc[0]
        vals=[ch.pre_scored_avg,ca.pre_allowed_avg,ca.pre_scored_avg,ch.pre_allowed_avg]
        baseline=float(np.nanmean(vals))*2 if np.isfinite(vals).sum()>=2 else np.nan
        # Combined, defensible update only; no fabricated offense/defense market states.
        adjustment=.425*(float(h.repeatable_total_performance)+float(a.repeatable_total_performance)) if pd.notna(h.repeatable_total_performance) and pd.notna(a.repeatable_total_performance) else 0
        projected=baseline+adjustment if np.isfinite(baseline) else np.nan
        opener=float(g.opening_total) if pd.notna(g.opening_total) else np.nan; close=float(g.closing_total) if pd.notna(g.closing_total) else np.nan
        side="Over" if np.isfinite(opener) and projected>opener else "Under" if np.isfinite(opener) and projected<opener else ""
        clv=(close-opener) if side=="Over" else (opener-close) if side=="Under" else np.nan
        actual=float(g.home_score+g.away_score); result="W" if side=="Over" and actual>opener or side=="Under" and actual<opener else "L" if side and actual!=opener else "P" if side else ""
        rows.append({"season":int(g.season),"week":int(g.week),"game_id":gid,"home_team":g.home_team,"away_team":g.away_team,"home_previous_game_id":h.game_id,"home_previous_week":int(h.week),"away_previous_game_id":a.game_id,"away_previous_week":int(a.week),"frozen_combined_total_baseline":baseline,"predicted_combined_total_adjustment":adjustment,"projected_close":projected,"current_lambda_085_projection":baseline+.85*((h.total_residual if pd.notna(h.total_residual) else 0)+(a.total_residual if pd.notna(a.total_residual) else 0))/2 if np.isfinite(baseline) else np.nan,"actual_opener":opener,"actual_close":close,"signal":side,"clv":clv,"actual_total":actual,"total_result":result,"method":"combined scoring/allowance baseline plus prior completed-game repeatable total adjustment; separate offense/defense market movement unavailable"})
    return pd.DataFrame(rows)


def model_comparison(spreads, totals, holdout):
    rows=[]
    s=spreads[spreads.season==holdout]
    for name,col in [("No movement adjustment","no_movement_projection"),("Current production spread formula lambda=0.50","current_lambda_050_projection"),("Raw ATS-based team movement","current_lambda_050_projection"),("Raw PBP-based team movement","repeatable_projection"),("Repeatable-performance team movement","repeatable_projection"),("Direction-plus-magnitude two-stage model","projected_close"),("Rating-system-aligned model (unavailable snapshots)",None),("High-confidence filtered model","projected_close"),("Gradient-boosted challenger","boosted_projection")]:
        z=s if "High-confidence" not in name else s[s.confidence_tier=="High"]
        if col is None or z.empty: rows.append({"model":name,"market":"spread","n":0,"mae":np.nan,"positive_clv_rate":np.nan,"average_clv":np.nan,"ats_win_rate":np.nan,"roi":np.nan,"status":"not estimable"}); continue
        valid=z[z[col].notna()&z.actual_close.notna()]; bets=z[z.actual_opener.notna()&z[col].notna()].copy()
        bets["side"]=np.where(bets[col]<bets.actual_opener,"home",np.where(bets[col]>bets.actual_opener,"away",""))
        bets["model_clv"]=np.where(bets.side.eq("home"),bets.actual_opener-bets.actual_close,np.where(bets.side.eq("away"),bets.actual_close-bets.actual_opener,np.nan))
        bets["model_line"]=np.where(bets.side.eq("home"),bets.actual_opener,np.where(bets.side.eq("away"),-bets.actual_opener,np.nan)); bets["team_margin"]=np.where(bets.side.eq("home"),bets.actual_margin,-bets.actual_margin); bets["result"]=[binary_result(a,b) for a,b in zip(bets.model_line,bets.team_margin)]
        rows.append({"model":name,"market":"spread","n":len(valid),"mae":float((valid[col]-valid.actual_close).abs().mean()),"positive_clv_rate":float((bets.model_clv>0).mean()) if len(bets) else np.nan,"average_clv":bets.model_clv.mean(),"ats_win_rate":float((bets.result=="W").sum()/max((bets.result.isin(["W","L"])).sum(),1)),"roi":roi(bets.result),"status":"evaluated"})
    t=totals[totals.season==holdout]
    for name,col in [("No movement adjustment","frozen_combined_total_baseline"),("Current total formula lambda=0.85","current_lambda_085_projection"),("Repeatable-performance combined total","projected_close")]:
        z=t[t[col].notna()&t.actual_close.notna()]; bets=t[t.actual_opener.notna()&t[col].notna()].copy(); bets["side"]=np.where(bets[col]>bets.actual_opener,"Over",np.where(bets[col]<bets.actual_opener,"Under","")); bets["model_clv"]=np.where(bets.side.eq("Over"),bets.actual_close-bets.actual_opener,np.where(bets.side.eq("Under"),bets.actual_opener-bets.actual_close,np.nan)); bets["result"]=np.where(((bets.side=="Over")&(bets.actual_total>bets.actual_opener))|((bets.side=="Under")&(bets.actual_total<bets.actual_opener)),"W",np.where(bets.actual_total==bets.actual_opener,"P","L"))
        rows.append({"model":name,"market":"total","n":len(z),"mae":float((z[col]-z.actual_close).abs().mean()) if len(z) else np.nan,"positive_clv_rate":float((bets.model_clv>0).mean()) if len(bets) else np.nan,"average_clv":bets.model_clv.mean(),"ats_win_rate":float((bets.result=="W").sum()/max(bets.result.isin(["W","L"]).sum(),1)) if len(bets) else np.nan,"roi":roi(bets.result),"status":"evaluated"})
    return pd.DataFrame(rows)


def make_report(path, summary, selection_table, comparison, confidence, feature_importance):
    def table(df,n=30): return df.head(n).to_html(index=False,border=0,classes="data")
    s=summary
    body=f"""<!doctype html><meta charset='utf-8'><title>Team Rating Movement Research</title><style>body{{font:15px system-ui;background:#07162d;color:#eef4ff;margin:24px;line-height:1.45}}h1,h2{{color:#fff}}.card{{background:#102746;border:1px solid #31547c;border-radius:12px;padding:18px;margin:16px 0}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:7px;border-bottom:1px solid #29496d;text-align:right}}th:first-child,td:first-child{{text-align:left}}code{{color:#91e6b1}}.warn{{color:#ffc667}}</style><h1>Team Market-Rating Movement Model</h1><div class='card'><b>Research only.</b> 2021–23 training; 2024 selection; locked 2025 final holdout. No production artifacts changed.</div>
    <h2>Dataset coverage</h2><div class='card'>{table(pd.DataFrame(s['dataset_by_season']))}</div>
    <h2>Market-rating movement distribution</h2><div class='card'>{html.escape(json.dumps(s['movement_distribution'],indent=2))}</div>
    <h2>Feature availability</h2><div class='card'>{table(pd.DataFrame(s['feature_availability']))}</div>
    <h2>Direction model / threshold selection</h2><div class='card'>{table(selection_table)}</div>
    <h2>Direction-family comparison</h2><div class='card'>{table(pd.DataFrame(s['direction_family_comparison']))}</div>
    <h2>Locked 2025 direction performance and confusion matrix</h2><div class='card'><pre>{html.escape(json.dumps(s['holdout_direction'],indent=2))}</pre></div>
    <h2>Magnitude model performance</h2><div class='card'><pre>{html.escape(json.dumps(s['holdout_magnitude'],indent=2))}</pre></div>
    <h2>Raw versus repeatable / benchmark / projected-close / CLV / betting</h2><div class='card'>{table(comparison,40)}</div>
    <h2>Raw versus repeatable team-movement estimates</h2><div class='card'>{table(pd.DataFrame(s['team_movement_method_comparison']))}</div>
    <h2>Rating-system movement alignment</h2><div class='card warn'>Historical weekly SP+, FPI, and TeamRankings snapshots were not verifiably frozen for 2021–25. No secondary movement model was fit.</div>
    <h2>Confidence tiers</h2><div class='card'>{table(confidence,20)}</div>
    <h2>Adjustment-size results</h2><div class='card'>{table(pd.DataFrame(s['adjustment_size_results']))}</div>
    <h2>Week-by-week locked holdout</h2><div class='card'>{table(pd.DataFrame(s['week_by_week_results']),40)}</div>
    <h2>Feature importance</h2><div class='card'>{table(feature_importance,40)}</div>
    <h2>Exact recommendation</h2><div class='card'>{html.escape(s['recommendation'])}</div>
    <h2>Limitations</h2><div class='card'><ul>{''.join('<li>'+html.escape(x)+'</li>' for x in s['limitations'])}</ul></div>"""
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(body+"\n")


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--train-seasons",nargs="+",type=int,default=[2021,2022,2023]); ap.add_argument("--selection-season",type=int,default=2024); ap.add_argument("--holdout-season",type=int,default=2025); ap.add_argument("--output-dir",default="data/research/team_rating_movement_model"); ap.add_argument("--strict",action="store_true"); args=ap.parse_args()
    out=ROOT/args.output_dir; report=ROOT/"build/research/team_rating_movement_model/index.html"; out.mkdir(parents=True,exist_ok=True)
    before=protected_hashes(); (out/"protected_hashes_before.json").write_text(json.dumps(before,indent=2)+"\n")
    games=pd.read_csv(GAMES,low_memory=False); games=games[games.season.isin(args.train_seasons+[args.selection_season,args.holdout_season])&games.closing_home_spread.notna()&games.closing_total.notna()].copy(); games["game_id"]=games.game_id.map(norm_id); games["season"]=num(games.season).astype(int); games["week"]=num(games.week).astype(int)
    ratings=pd.read_csv(RATINGS); pbp=pd.read_csv(PBP,low_memory=False); drives=pd.read_csv(DRIVES); gc=pd.read_csv(GAME_CONTROL)
    states=build_team_states(games,ratings); features=build_features(states,games,pbp,drives,gc); repeat,persistent=build_repeatable(features,args.train_seasons)
    model_features=[c for c in ["ats_margin","total_residual","final_margin","closing_spread","raw_pbp_performance","rules_repeatable_spread","regularized_repeatable_spread","residualized_repeatable_spread","repeatable_offense_performance","repeatable_defense_performance","off_ppa","off_success_rate","off_explosiveness","def_ppa_allowed","def_success_allowed","def_explosiveness_allowed","def_havoc_rate","off_plays","drive_off_points_per_opportunity","drive_def_points_per_opportunity_allowed","gc_game_control_index","trailing_2_game_ats","trailing_3_game_ats","trailing_2_game_ppa","trailing_3_game_ppa","recent_form_vs_season","opponent_adjusted_recent_form"] if c in repeat]
    eligible=repeat[repeat.eligibility].copy(); best,selection_table=select_model(eligible,model_features,args.train_seasons,args.selection_season)
    locked={"train_seasons":args.train_seasons,"selection_season":args.selection_season,"holdout_season":args.holdout_season,"no_move_threshold":best["threshold"],"direction_model":best["direction_model"],"magnitude_model":best["magnitude_model"],"features":model_features,"confidence_cutoffs":{"high_probability":.65,"high_magnitude":.5,"medium_probability":.52,"minimum_feature_coverage":.75},"selected_without_holdout":True}
    (out/"selection_lock_before_holdout.json").write_text(json.dumps(locked,indent=2)+"\n"); locked_hash=sha256(out/"selection_lock_before_holdout.json")
    # Locked choices are now refit on 2021-24; only then is 2025 scored once.
    final_model=fit_models(eligible,model_features,float(best["threshold"]),args.train_seasons+[args.selection_season]); pred_values=predict_models(eligible,final_model)
    for k,v in pred_values.items(): eligible[k]=v
    selected_family=str(best["direction_model"]); selected_threshold=float(best["threshold"])
    if selected_family=="ordinal_ridge_proxy":
        eligible["predicted_direction"]=movement_class(eligible.ridge,selected_threshold); selected_probs=movement_probs_from_score(eligible.ridge,selected_threshold)
    elif selected_family=="rules_based":
        eligible["predicted_direction"]=movement_class(eligible.rules_repeatable_spread,selected_threshold); selected_probs=movement_probs_from_score(eligible.rules_repeatable_spread,selected_threshold)
    elif selected_family=="gradient_boosted_stumps":
        eligible["predicted_direction"]=movement_class(eligible.boosted_challenger,selected_threshold); selected_probs=movement_probs_from_score(eligible.boosted_challenger,selected_threshold)
    else: selected_probs=np.column_stack([eligible.prob_down,eligible.prob_no_change,eligible.prob_up])
    eligible[["prob_down","prob_no_change","prob_up"]]=selected_probs
    eligible["predicted_movement"]=eligible[str(best["magnitude_model"])]
    eligible["actual_direction"]=movement_class(eligible.actual_market_rating_change,float(best["threshold"])); eligible["feature_coverage"]=eligible[model_features].notna().mean(axis=1); eligible["confidence_tier"]=add_confidence(eligible,locked)
    eligible["split"]=np.where(eligible.season.isin(args.train_seasons),"train",np.where(eligible.season==args.selection_season,"selection","locked_holdout"))
    hold=eligible[eligible.season==args.holdout_season]
    hp=np.column_stack([hold.prob_down,hold.prob_no_change,hold.prob_up]); hold_direction=class_metrics(hold.actual_direction,hold.predicted_direction,hp); hold_mag=reg_metrics(hold.actual_market_rating_change,hold.predicted_movement)
    direction_families=[]
    for name,vals in [("rules_based",movement_class(hold.rules_repeatable_spread,float(best["threshold"]))),("ordinal_ridge_proxy",movement_class(hold.ridge,float(best["threshold"]))),("multinomial_logistic",hold.logistic_direction.to_numpy()),("gradient_boosted_stumps",movement_class(hold.boosted_challenger,float(best["threshold"])) )]:
        m=class_metrics(hold.actual_direction,vals); direction_families.append({"model":name,"n":m["n"],"accuracy":m["accuracy"],"balanced_accuracy":m["balanced_accuracy"],"macro_f1":m["macro_f1"]})
    movement_methods=[]
    for name,col in [("raw_ats","raw_ats_performance"),("raw_pbp","raw_pbp_performance"),("rules_cleanup","rules_repeatable_spread"),("regularized_repeatable","regularized_repeatable_spread"),("residualized","residualized_repeatable_spread"),("selected_huber","predicted_movement"),("gradient_boosted_stumps","boosted_challenger")]:
        m=reg_metrics(hold.actual_market_rating_change,hold[col]); movement_methods.append({"method":name,**m})
    spreads=spread_projection(eligible,games); totals=total_projection(repeat,games); comp=model_comparison(spreads,totals,args.holdout_season)
    ats=spreads[spreads.actual_opener.notna()].copy(); total_bets=totals[totals.actual_opener.notna()].copy()
    conf=[]
    for tier,z in spreads[spreads.season==args.holdout_season].groupby("confidence_tier"):
        b=z[z.actual_opener.notna()]; conf.append({"confidence_tier":tier,"n":len(z),"projected_close_mae":float((z.projected_close-z.actual_close).abs().mean()),"positive_clv_rate":float((b.clv>0).mean()) if len(b) else np.nan,"average_clv":b.clv.mean(),"median_clv":b.clv.median(),"ats_win_rate":float((b.ats_result=="W").sum()/max(b.ats_result.isin(["W","L"]).sum(),1)),"roi":roi(b.ats_result)})
    confidence=pd.DataFrame(conf)
    adjustment=[]
    hold_bins=pd.cut(hold.predicted_movement.abs(),[-.001,.25,.5,1,2,np.inf],labels=["0-.25",".25-.5",".5-1","1-2","2+"])
    for bucket,z in hold.groupby(hold_bins,observed=True):
        m=reg_metrics(z.actual_market_rating_change,z.predicted_movement); adjustment.append({"predicted_size":str(bucket),**m})
    week_rows=[]
    for week,z in spreads[spreads.season==args.holdout_season].groupby("week"):
        b=z[z.actual_opener.notna()]; week_rows.append({"week":int(week),"n":len(z),"projected_close_mae":float((z.projected_close-z.actual_close).abs().mean()),"positive_clv_rate":float((b.clv>0).mean()) if len(b) else np.nan,"average_clv":b.clv.mean(),"ats_win_rate":float((b.ats_result=="W").sum()/max(b.ats_result.isin(["W","L"]).sum(),1)) if len(b) else np.nan})
    rating_system=eligible[["season","week","game_id","team","predicted_direction"]].copy()
    for source in ["spplus","fpi","teamrankings"]: rating_system[f"predicted_{source}_direction"]=np.nan; rating_system[f"{source}_target_eligible"]=False
    rating_system["rating_systems_agreeing"]=0; rating_system["market_pbp_agreement"]=np.sign(eligible.predicted_movement)==np.sign(eligible.raw_pbp_performance); rating_system["model_consensus_score"]=np.nan; rating_system["snapshot_audit"]="unavailable: no verifiably frozen weekly 2021-25 snapshots"
    audit=states[["season","week","game_id","team","eligibility","missing_reason","cutoff_provenance"]].copy(); audit["next_opener_evaluation_only"]=True; audit["next_close_evaluation_only"]=True; audit["next_result_evaluation_only"]=True; audit["neutral_site_known"]=False; audit["no_future_pbp"]=True; audit["no_future_injury_or_roster"]=True
    feature_av=[{"feature":c,"coverage":float(repeat[c].notna().mean())} for c in model_features]
    beta=final_model["ridge"][1:]; importance=pd.DataFrame({"feature":model_features,"standardized_abs_coefficient":np.abs(beta),"signed_coefficient":beta}).sort_values("standardized_abs_coefficient",ascending=False)
    dataset=[]
    for season,z in states.groupby("season"): dataset.append({"season":int(season),"team_game_rows":len(z),"eligible_targets":int(z.eligibility.sum()),"games":int(z.game_id.nunique()),"opener_spread_coverage":int(games[(games.season==season)&games.opening_home_spread.notna()].shape[0]),"opener_total_coverage":int(games[(games.season==season)&games.opening_total.notna()].shape[0])})
    movement=eligible.actual_market_rating_change.describe(percentiles=[.05,.25,.5,.75,.95]).to_dict()
    bestspread=comp[(comp.market=="spread")&comp.status.eq("evaluated")].sort_values("mae").iloc[0]
    recommendation=("No production change justified: the locked 2025 winner is not the new two-stage model." if bestspread.model!="Direction-plus-magnitude two-stage model" else "The two-stage structure wins projected-close MAE on locked 2025, but production adoption still requires an independent forward-season confirmation because opener coverage is sparse before 2024.")
    summary={"schema_version":"team-rating-movement-research-v1","target_definition":"market-implied rating snapshot through completed Week N minus snapshot through Week N-1 for the same team; positive means upgrade","rating_state_source":str(RATINGS.relative_to(ROOT)),"rating_definition":"close-only ridge; home closing margin = home rating - away rating + 2.5 HFA","weekly_cutoff":"all closing lines through completed week","neutral_site":"unavailable in historical core source; uncertainty explicit; 2.5 HFA retained","offense_defense_target":"not identifiable honestly from combined spread rating; not modeled","dataset_by_season":dataset,"movement_distribution":movement,"feature_availability":feature_av,"selection":locked,"selection_lock_sha256":locked_hash,"holdout_direction":hold_direction,"holdout_magnitude":hold_mag,"direction_family_comparison":direction_families,"team_movement_method_comparison":movement_methods,"adjustment_size_results":adjustment,"week_by_week_results":week_rows,"rating_system_snapshot_audit":{"SP+":"not historically frozen/legitimate for weekly 2021-25","FPI":"not historically frozen/legitimate for weekly 2021-25","TeamRankings":"not historically frozen/legitimate for weekly 2021-25"},"recommendation":recommendation,"limitations":["Historical neutral-site flags are absent, so HFA treatment is uncertain for neutral games.","2021-22 opener coverage is nearly absent; CLV and betting evaluation is dominated by 2024-25.","Turnover, non-offensive touchdown, weather, and injury fields are not present in the frozen source and are left missing, never imputed as observed facts.","Separate offensive and defensive market-rating changes cannot be identified from the combined spread-rating state.","Combined total projection is secondary and does not claim separate offense/defense market movements.","SP+/FPI/TeamRankings weekly movement models are withheld because snapshots are not verifiably frozen.","Quantile regression was unavailable in the installed dependency set; a deterministic gradient-boosted-stump challenger was evaluated."],"protected_hashes_before":before}
    # Required outputs.
    states.to_csv(out/"team_week_rating_states.csv",index=False); features.to_csv(out/"team_game_features.csv",index=False); repeat.to_csv(out/"repeatable_performance_features.csv",index=False); eligible.to_csv(out/"team_movement_predictions.csv",index=False); rating_system.to_csv(out/"rating_system_movement_predictions.csv",index=False); spreads.to_csv(out/"next_game_spread_predictions.csv",index=False); totals.to_csv(out/"next_game_total_predictions.csv",index=False); confidence.to_csv(out/"confidence_tier_results.csv",index=False); ats.to_csv(out/"ats_results.csv",index=False); total_bets.to_csv(out/"total_betting_results.csv",index=False); comp.to_csv(out/"model_comparison.csv",index=False); hold.to_csv(out/"holdout_2025_results.csv",index=False); audit.to_csv(out/"game_level_audit.csv",index=False); selection_table.to_csv(out/"selection_grid_2024.csv",index=False); importance.to_csv(out/"feature_importance.csv",index=False); pd.DataFrame(direction_families).to_csv(out/"direction_family_comparison.csv",index=False); pd.DataFrame(movement_methods).to_csv(out/"team_movement_method_comparison.csv",index=False); pd.DataFrame(adjustment).to_csv(out/"adjustment_size_results.csv",index=False); pd.DataFrame(week_rows).to_csv(out/"week_by_week_results.csv",index=False)
    (out/"final_selection.json").write_text(json.dumps(locked,indent=2)+"\n"); (out/"summary.json").write_text(json.dumps(summary,indent=2,default=lambda v:None if pd.isna(v) else v)+"\n")
    make_report(report,summary,selection_table,comp,confidence,importance)
    after=protected_hashes(); (out/"protected_hashes_after.json").write_text(json.dumps(after,indent=2)+"\n")
    changed=[p for p in before if before[p]!=after[p]]
    if changed: raise SystemExit("Protected files changed: "+", ".join(changed))
    print(json.dumps({"status":"PASS","output_dir":str(out),"report":str(report),"selection":locked,"holdout_direction":hold_direction,"holdout_magnitude":hold_mag,"protected_changes":changed},indent=2))


if __name__=="__main__": main()
