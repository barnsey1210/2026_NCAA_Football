#!/usr/bin/env python3
"""Append verified settlements and score enrichments without rewriting observations."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from immutable_tracking import append_unique,stable_id
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'data/model_tracking/v2';RESULTS=ROOT/'data/canonical/game_results_2026.json'
def load_jsonl(name):
 p=D/name
 return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
def profit(result,price):
 if result<=0:return -1.0 if result<0 else 0.0
 p=float(price or -110);return p/100 if p>0 else 100/abs(p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--accept',action='store_true');a=ap.parse_args();payload=json.loads(RESULTS.read_text());games={str(x['game_id']):x for x in payload.get('games',[]) if x.get('completed') is True};pred={x['observation_id']:x for x in load_jsonl('prediction_observations.jsonl')};markets={x['observation_id']:x for x in load_jsonl('market_observations.jsonl')};settlements=[];scores=[]
 for game_id,g in games.items():
  sid=stable_id('settlement',game_id,g.get('home_score'),g.get('away_score'),g.get('source_updated_at'));settlements.append({'settlement_id':sid,'canonical_game_id':game_id,'status':'VERIFIED_FINAL','final_home_score':g['home_score'],'final_away_score':g['away_score'],'completed_at':g.get('source_updated_at') or payload.get('generated_at'),'source':g.get('source'),'source_artifact':'data/canonical/game_results_2026.json','revision':1})
  for d in (x for x in load_jsonl('decision_observations.jsonl') if x['canonical_game_id']==game_id):
   pr=pred.get(d['prediction_observation_id']);mo=markets.get(d['market_observation_id'])
   if not pr or not mo:continue
   market=d['market_type'];side=d['bet_side'];line=float(mo['line']);projection=float(pr['projection']);home_margin=float(g['home_margin_actual']);actual_total=float(g['total_points_actual'])
   if market=='spread':
    score=home_margin+line if side=='home' else -home_margin+line;close_home=g.get('closing_home_spread');closing_line=close_home if side=='home' else (-float(close_home) if close_home is not None else None);clv=line-closing_line if closing_line is not None else None;error=projection-home_margin
   else:
    score=(actual_total-line)*(1 if side=='over' else -1);closing_line=g.get('closing_total');clv=((float(closing_line)-line) if side=='over' else (line-float(closing_line))) if closing_line is not None else None;error=projection-actual_total
   result=1 if score>0 else -1 if score<0 else 0;scid=stable_id('score',pr['observation_id'],mo['observation_id'],sid,'settlement_v2')
   scores.append({'score_id':scid,'prediction_observation_id':pr['observation_id'],'market_observation_id':mo['observation_id'],'decision_id':d['decision_id'],'settlement_id':sid,'model_id':pr['model_id'],'model_version':pr.get('model_version'),'market_type':market,'season':pr.get('season'),'week':pr.get('week'),'checkpoint':d.get('checkpoint'),'lifecycle_state':pr.get('lifecycle_state'),'edge_threshold':d.get('edge'),'closing_line':closing_line,'closing_price':None,'result':result,'profit':profit(result,mo.get('price')),'clv':clv,'median_clv':clv,'positive_clv':clv>0 if clv is not None else None,'beat_close':clv>0 if clv is not None else None,'won_line_move':clv>0 if clv not in (None,0) else None,'absolute_error':abs(error),'signed_error':error,'squared_error':error*error,'clv_implied_ev':None,'scoring_version':'settlement_v2_verified_final'})
 report={'schema_version':'settlement-preview-v2','generated_at':datetime.now(timezone.utc).isoformat(),'verified_games':len(games),'settlements':append_unique(D/'settlements.jsonl',settlements,'settlement_id',a.accept),'scores':append_unique(D/'scores.jsonl',scores,'score_id',a.accept)};print(json.dumps(report,indent=2))
if __name__=='__main__':main()
