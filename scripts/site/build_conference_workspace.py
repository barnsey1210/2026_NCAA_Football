#!/usr/bin/env python3
"""Build current conference workspaces from canonical schedule, simulations, and markets."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.lib.ncaaf_config import canonical_team
DB_PATH=ROOT/"data/snapshots/preseason/preseason_db.json"
SIM_PATH=ROOT/"data/site/season_simulations_2026.json"
FUTURES_PATH=ROOT/"data/site/futures_view.json"
OUT_PATH=ROOT/"data/site/conference_workspace.json"

def number(x):
    try: return None if x is None or x=="" else float(x)
    except Exception: return None

def main():
    for p in (DB_PATH,SIM_PATH,FUTURES_PATH):
        if not p.exists(): raise SystemExit(f"Missing required conference workspace input: {p}")
    db=json.loads(DB_PATH.read_text()); sims=json.loads(SIM_PATH.read_text()); fv=json.loads(FUTURES_PATH.read_text())
    sim_by_team={canonical_team(x.get("team")):x for x in sims.get("teams",[]) if x.get("team")}
    markets={canonical_team(x.get("team")):x for x in fv.get("rows",[]) if x.get("team")}
    teams={canonical_team(x.get("team")):x for x in db.get("teams",[]) if x.get("team")}; games=db.get("games",[]); rows=[]
    for key,base in teams.items():
        sim=sim_by_team.get(key,{}); played=[g for g in games if g.get("cfbd_completed") and key in {canonical_team(g.get("away_team")),canonical_team(g.get("home_team"))}]; remaining=[g for g in games if not g.get("cfbd_completed") and key in {canonical_team(g.get("away_team")),canonical_team(g.get("home_team"))}]
        wins=losses=cwins=closses=0
        for g in played:
            home=canonical_team(g.get("home_team"))==key; tp=g.get("home_points") if home else g.get("away_points"); op=g.get("away_points") if home else g.get("home_points")
            if tp is None or op is None: continue
            won=float(tp)>float(op); wins+=int(won); losses+=int(not won)
            if g.get("is_conference_game"): cwins+=int(won); closses+=int(not won)
        opp=[]; conf_opp=[]; remaining_conf_opp=[]
        for g in played+remaining:
            other=g.get("away_team") if canonical_team(g.get("home_team"))==key else g.get("home_team"); rating=number(teams.get(canonical_team(other),{}).get("combo"))
            if rating is not None:
                opp.append(rating)
                if g.get("is_conference_game"): conf_opp.append(rating)
        for g in remaining:
            other=g.get("away_team") if canonical_team(g.get("home_team"))==key else g.get("home_team"); rating=number(teams.get(canonical_team(other),{}).get("combo"))
            if rating is not None and g.get("is_conference_game"): remaining_conf_opp.append(rating)
        projected_wins=number(sim.get("avg_total_wins")); projected_conf_wins=number(sim.get("avg_conference_wins")); title_pct=number(sim.get("conference_title_pct")); make_title_pct=number(sim.get("make_title_game_pct")); total_games=len(played)+len(remaining); total_conf_games=sum(bool(g.get("is_conference_game")) for g in played+remaining); m=markets.get(key,{}); market_win_total=number(m.get("market_win_total")); title_market_prob=number(m.get("title_market_prob"))
        rows.append({"team":base.get("team"),"slug":base.get("slug"),"conference":base.get("conference"),"rank":base.get("rank"),"rating":base.get("combo"),"current_wins":wins,"current_losses":losses,"current_conf_wins":cwins,"current_conf_losses":closses,"projected_wins":projected_wins,"projected_conf_wins":projected_conf_wins,"projected_losses":total_games-projected_wins if projected_wins is not None else None,"projected_conf_losses":total_conf_games-projected_conf_wins if projected_conf_wins is not None else None,"make_title_game_pct":make_title_pct,"title_pct":title_pct,"bowl_eligibility_pct":sim.get("bowl_eligibility_pct"),"overall_sos":sum(opp)/len(opp) if opp else None,"conf_sos":sum(conf_opp)/len(conf_opp) if conf_opp else None,"remaining_sos":sum(remaining_conf_opp)/len(remaining_conf_opp) if remaining_conf_opp else None,"market_win_total":market_win_total,"win_edge":projected_wins-market_win_total if projected_wins is not None and market_win_total is not None else None,"title_market_prob":title_market_prob,"title_edge":title_pct-title_market_prob if title_pct is not None and title_market_prob is not None else None,"title_price":m.get("title_price"),"title_book":m.get("title_book"),"open_wagers":m.get("open_wagers",[])})
    conferences=[]
    for c in db.get("conferences",[]):
        conf_name=c.get("conference"); cr=[x for x in rows if x.get("conference")==conf_name]; cr.sort(key=lambda x:(x.get("projected_conf_wins") is not None,x.get("projected_conf_wins") if x.get("projected_conf_wins") is not None else -999,x.get("rating") if x.get("rating") is not None else -999),reverse=True)
        for i,x in enumerate(cr,1): x["projected_finish"]=i
        for field,rank_field in [("conf_sos","conf_sos_rank"),("remaining_sos","remaining_sos_rank")]:
            ranked=[x for x in cr if x.get(field) is not None]; ranked.sort(key=lambda x:x[field],reverse=True)
            for i,x in enumerate(ranked,1): x[rank_field]=i
        ratings=[number(x.get("rating")) for x in cr]; ratings=[x for x in ratings if x is not None]
        conferences.append({"conference":conf_name,"slug":c.get("slug"),"average_strength":c.get("average_strength"),"average_team_rating":sum(ratings)/len(ratings) if ratings else None,"championship_game":c.get("championship_game"),"teams":cr})
    ranked_confs=sorted(conferences,key=lambda x:x.get("average_team_rating") if x.get("average_team_rating") is not None else -999,reverse=True)
    for i,c in enumerate(ranked_confs,1): c["conference_rank"]=i
    out={"schema_version":"conference-workspace-v2","built_at":datetime.now(timezone.utc).isoformat(),"simulation_built_at":sims.get("built_at"),"simulation_trials":sims.get("trials"),"simulation_source":"data/site/season_simulations_2026.json","schedule_source":"data/snapshots/preseason/preseason_db.json","market_source":"data/site/futures_view.json","conferences":conferences}
    OUT_PATH.write_text(json.dumps(out,separators=(",",":"))+"\n"); print(len(conferences),sum(len(x["teams"]) for x in conferences)); print("simulation_built_at:",sims.get("built_at")); print("simulation_trials:",sims.get("trials"))
if __name__=="__main__": main()
