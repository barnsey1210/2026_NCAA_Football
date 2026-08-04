#!/usr/bin/env python3
"""Append settlements for completed games already present in accepted opportunities."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from model_tracking import append_jsonl, read_jsonl, settle_spread, settle_total, stable_id

ROOT=Path(__file__).resolve().parents[2]; STORE=ROOT/"data/model_tracking"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--accept",action="store_true"); args=ap.parse_args()
    games={x["game"]["game_id"]:x["game"] for x in json.loads((ROOT/"data/site/matchups_view.json").read_text())["games"]}
    opps={x["opportunity_id"]:x for x in read_jsonl(STORE/"model_opportunities.jsonl")}
    preds=read_jsonl(STORE/"model_predictions.jsonl"); observations={x["market_observation_id"]:x for x in read_jsonl(STORE/"market_observations.jsonl")}
    scores=[]; results=[]; now=datetime.now(timezone.utc).isoformat()
    for oid,o in opps.items():
        g=games.get(o["canonical_game_id"])
        if not g or not g.get("completed") or g.get("home_score") is None or g.get("away_score") is None: continue
        margin=float(g["home_score"])-float(g["away_score"]); total=float(g["home_score"])+float(g["away_score"])
        result_id=stable_id(g["game_id"],g["home_score"],g["away_score"])
        results.append({"result_id":result_id,"canonical_game_id":g["game_id"],"final_away_score":g["away_score"],"final_home_score":g["home_score"],"final_home_margin":margin,"final_total":total,"status":"completed","completed_at":now,"source":"matchups_view","revision":1})
        obs=observations.get(o["opener_market_observation_id"]); line=obs.get("line") if obs else None
        if line is None: continue
        for p in (x for x in preds if x["opportunity_id"]==oid):
            settled=settle_spread(p["predicted_home_margin"],line,margin) if o["market_type"]=="spread" else settle_total(p["predicted_total"],line,total)
            scores.append({"score_id":stable_id(p["prediction_id"],result_id,"opener"),"prediction_id":p["prediction_id"],"opportunity_id":oid,"benchmark_type":"opener","result":settled,"point_clv":None,"absolute_error":settled["absolute_error"],"signed_error":settled["signed_error"],"squared_error":settled["squared_error"],"hypothetical_profit":settled["hypothetical_profit"],"settlement_version":"settlement_v1","revision":1})
    if args.accept:
        for r in results: append_jsonl(STORE/"game_results.jsonl",r,["result_id"])
        for r in scores: append_jsonl(STORE/"model_prediction_scores.jsonl",r,["score_id"])
    print(f"{'Accepted' if args.accept else 'Previewed'} {len(results)} result records and {len(scores)} scores")

if __name__=="__main__": main()

