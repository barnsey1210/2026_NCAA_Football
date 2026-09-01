#!/usr/bin/env python3
"""Build the compact 2026 performance view from immutable v2 evidence."""
from __future__ import annotations
import json,math,tempfile
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];STORE=ROOT/'data/model_tracking/v2';OUT=ROOT/'data/site/model_performance_view.json'
def load(name):
 p=STORE/name
 return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
def atomic(payload):
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=OUT.parent,delete=False) as f:json.dump(payload,f,separators=(',',':'),allow_nan=False);f.write('\n');p=Path(f.name)
 p.replace(OUT)
def median(v):
 if not v:return None
 x=sorted(v);n=len(x);return x[n//2] if n%2 else (x[n//2-1]+x[n//2])/2
def main():
 registry=json.loads((STORE/'model_registry.json').read_text())['models'];pred=load('prediction_observations.jsonl');decisions=load('decision_observations.jsonl');scores=load('scores.jsonl');latest={};pred_by_id={x['observation_id']:x for x in pred}
 for p in pred:latest[(p['model_id'],p.get('model_version'))]=p
 grouped=defaultdict(list)
 for s in scores:grouped[(s.get('model_id'),s.get('model_version'))].append(s)
 matrices={'spread':[],'total':[]}
 for spec in registry:
  key=(spec['model_id'],spec['model_version']);rows=grouped[key];p=latest.get(key,{});wins=sum(x.get('result')==1 for x in rows);loss=sum(x.get('result')==-1 for x in rows);push=sum(x.get('result')==0 for x in rows);clv=[x['clv'] for x in rows if x.get('clv') is not None];ae=[x['absolute_error'] for x in rows if x.get('absolute_error') is not None];se=[x['squared_error'] for x in rows if x.get('squared_error') is not None];bias=[x['signed_error'] for x in rows if x.get('signed_error') is not None]
  observed=[x for x in pred if x['model_id']==spec['model_id'] and x.get('model_version')==spec['model_version']];available=[x for x in observed if x.get('availability_status')=='AVAILABLE'];role=spec.get('role','individual');mtype='individual' if role=='individual' else 'shadow' if 'shadow' in role else 'composite';n=len(rows)
  matrices[spec['market_type']].append({'model':spec['model_id'],'model_id':spec['model_id'],'model_version':spec['model_version'],'display_name':spec['model_id'].replace('_',' ').title(),'market_type':spec['market_type'],'model_type':mtype,'role':role,'status':p.get('availability_status','NOT_YET_CAPTURED'),'tracking_status':'ACTIVE_PROSPECTIVE_V2','latest_source_timestamp':p.get('source_updated_at'),'default_visible':role in {'active_standard_authority','prospective_challenger','shadow_production_unchanged'},'rank':None,'ranking_status':'UNRANKED — SMALL SAMPLE' if n<30 else 'ELIGIBLE','games':n,'availability_pct':len(available)/len(observed) if observed else None,'record':f'{wins}-{loss}-{push}','win_pct':wins/(wins+loss) if wins+loss else None,'ats_or_ou_pct':wins/(wins+loss) if wins+loss else None,'roi':sum(x.get('profit') or 0 for x in rows)/n if n else None,'average_point_clv':sum(clv)/len(clv) if clv else None,'median_clv':median(clv),'positive_clv_pct':sum(x>0 for x in clv)/len(clv) if clv else None,'beat_close_pct':sum(bool(x.get('beat_close')) for x in rows if x.get('beat_close') is not None)/sum(x.get('beat_close') is not None for x in rows) if any(x.get('beat_close') is not None for x in rows) else None,'won_line_move_pct':sum(bool(x.get('won_line_move')) for x in rows if x.get('won_line_move') is not None)/sum(x.get('won_line_move') is not None for x in rows) if any(x.get('won_line_move') is not None for x in rows) else None,'mae':sum(ae)/len(ae) if ae else None,'bias':sum(bias)/len(bias) if bias else None,'rmse':math.sqrt(sum(se)/len(se)) if se else None})
 for market in matrices:
  eligible=sorted([x for x in matrices[market] if x['games']>=30],key=lambda x:(-(x['roi'] if x['roi'] is not None else -999),x['mae'] if x['mae'] is not None else 999))
  for i,row in enumerate(eligible,1):row['rank']=i;row['ranking_status']='RANKED'
 opportunities=[]
 for d in decisions:
  p=pred_by_id.get(d.get('prediction_observation_id'),{});opportunities.append({**d,'site_week':p.get('week'),'away_team':p.get('away_team'),'home_team':p.get('home_team'),'consensus_versions':[p.get('model_id')] if p else [],'opener_market_observation_id':d.get('market_observation_id'),'estimated_ev_pct':None,'qualification_status':'TRACKED_NOT_QUALIFIED','opener_provenance_grade':d.get('market_provenance',{}).get('freshness_status')})
 payload={'schema_version':'model-performance-view-v3','built_at':datetime.now(timezone.utc).isoformat(),'season':2026,'status':'ACTIVE_PROSPECTIVE' if pred else 'READY_NOT_YET_CAPTURED','tracking_started':bool(pred),'ranking_minimum':30,'summary':{'opportunities':len(decisions),'predictions':len(pred),'settled':len(scores),'spread':{'opportunities':sum(x.get('market_type')=='spread' for x in decisions),'settled_selections':sum(x.get('market_type')=='spread' for x in scores)},'totals':{'opportunities':sum(x.get('market_type')=='total' for x in decisions),'settled_selections':sum(x.get('market_type')=='total' for x in scores)}},'spread_matrix':matrices['spread'],'total_matrix':matrices['total'],'opportunities':opportunities,'methodology':{'source':'immutable-model-tracking-v2','prediction_contract':'data/site/current_game_projection_contract.json','market_contract':'data/site/current_market_contract.json','results_contract':'data/canonical/game_results_2026.json','no_fake_backfill':True,'clv':'null until canonical close exists','spread_projection_formula':'named canonical projection contract models','hfa':{'non_neutral':None,'neutral':None,'method':'owned by each named model contract'},'spread_core_v1':{'models':['SP+','FPI','TeamRankings','DRatings'],'model_id':'standard_spread_4src_equal_v1'},'total':{'baseline':'standard_total_sp_massey_dratings_v1','challenger':'total_sp50_massey50_v1','minimum_independent_sources':2}},'periods':['W0']+[f'W{i}' for i in range(1,15)]+['Conference Championships','Bowl / Playoff','All']};atomic(payload);print(f'Wrote {OUT} ({len(pred)} immutable predictions, {len(scores)} scores)')
if __name__=='__main__':main()
