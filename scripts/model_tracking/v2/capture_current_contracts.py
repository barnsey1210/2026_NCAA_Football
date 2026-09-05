#!/usr/bin/env python3
"""Preview or accept immutable observations from accepted canonical MAIN contracts."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from immutable_tracking import append_unique,stable_id
ROOT=Path(__file__).resolve().parents[3]; DEST=ROOT/'data/model_tracking/v2'
COMPONENT_IDS={('spread','SP+'):('sp_plus_spread','v1'),('spread','FPI'):('fpi_spread','v1'),('spread','TeamRankings'):('teamrankings_spread','v1'),('spread','Sagarin Rating'):('sagarin_spread','v1'),('spread','DRatings'):('dratings_spread','v1'),('total','SP+'):('sp_plus_total','v1'),('total','Massey Dual'):('massey_dual_total','v1'),('total','Sagarin Total'):('sagarin_total','v1'),('total','DRatings Total'):('dratings_total','v1')}
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def future_trackable(g,now):
 if str(g.get('availability_status') or '').upper() in {'CLOSING','CLOSED','FINAL'}:return False
 kickoff=g.get('kickoff_at')
 if not kickoff:return False
 try:return datetime.fromisoformat(str(kickoff).replace('Z','+00:00'))>now
 except (TypeError,ValueError):return False
def prediction_row(g,model_id,x,market,projection,component_values=None,model_version=None,source_updated=None):
 state={'projection':projection,'components':component_values if component_values is not None else x.get('component_values',{}),'weights':x.get('weights',{}),'availability':x.get('component_status',{}),'missing':x.get('missing_sources',[]),'lifecycle':x.get('formula_status'),'status':x.get('availability_status'),'source_updated':source_updated or x.get('freshness_timestamp')}
 oid=stable_id('prediction',g['game_id'],model_id,model_version or x.get('formula_version'),market,canonical(state))
 return {'observation_id':oid,'season':g.get('season'),'week':g.get('week'),'canonical_game_id':g['game_id'],'away_team':g.get('away_team'),'home_team':g.get('home_team'),'kickoff_at':g.get('kickoff_at') or g.get('date'),'model_id':model_id,'model_version':model_version or x.get('formula_version'),'market_type':market,'observed_at':datetime.now(timezone.utc).isoformat(),'model_calculated_at':x.get('build_timestamp'),'source_updated_at':source_updated or x.get('freshness_timestamp'),'source_snapshot_timestamps':x.get('component_source_timestamps',{}),'projection':projection,'component_values':component_values if component_values is not None else x.get('component_values',{}),'component_weights':x.get('weights',{}),'component_availability':x.get('component_status',{}),'missing_components':x.get('missing_sources',[]),'lifecycle_state':x.get('formula_status'),'source_artifacts':x.get('source_artifacts',[]),'contract_id':x.get('contract_build_id'),'formula_version':x.get('formula_version'),'availability_status':x.get('availability_status'),'provenance_flags':{'authority':x.get('authority'),'validation_status':x.get('validation_status')}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--accept',action='store_true');args=ap.parse_args();pc=ROOT/'data/site/current_game_projection_contract.json';mc=ROOT/'data/site/current_market_contract.json';p=json.loads(pc.read_text());m=json.loads(mc.read_text());pred=[];markets=[];decisions=[];market_index={};now=datetime.now(timezone.utc);eligible={str(g['game_id']) for g in m.get('games',[]) if future_trackable(g,now)}
 for g in p.get('games',[]):
  if str(g['game_id']) not in eligible:continue
  for model_id,x in g.get('projections',{}).items():
   market='spread' if x.get('value_home_margin') is not None or 'spread' in model_id else 'total';projection=x.get('value_home_margin') if market=='spread' else x.get('value_total');pred.append(prediction_row(g,model_id,x,market,projection))
   for component,value in x.get('component_values',{}).items():
    if (market,component) in COMPONENT_IDS:
     cid,version=COMPONENT_IDS[(market,component)];pred.append(prediction_row(g,cid,x,market,value,{component:value},version,x.get('component_source_timestamps',{}).get(component)))
 for g in m.get('games',[]):
  if str(g['game_id']) not in eligible:continue
  for book,markets_by_type in g.get('quotes',{}).items():
   for market,sides in markets_by_type.items():
    if market not in {'spread','total'}: continue
    for side,q in sides.items():
     state=[q.get('source_updated_at'),q.get('line'),q.get('price'),q.get('freshness_status'),q.get('market_lifecycle_state')];oid=stable_id('market',g['game_id'],market,book,side,canonical(state));row={'observation_id':oid,'canonical_game_id':g['game_id'],'market_type':market,'sportsbook':book,'side':side,'observed_at':datetime.now(timezone.utc).isoformat(),'source_updated_at':q.get('source_updated_at'),'line':q.get('line'),'price':q.get('price'),'source':q.get('source'),'freshness_status':q.get('freshness_status'),'lifecycle_state':q.get('market_lifecycle_state'),'kickoff_at':q.get('kickoff_at'),'contract_id':m.get('built_at')};markets.append(row);market_index[(g['game_id'],market,book,side)]=row
 registry_ids={x['model_id'] for x in json.loads((DEST/'model_registry.json').read_text())['models']};projection_by_game={}
 for row in pred:
  if row['model_id'] in registry_ids and row.get('projection') is not None: projection_by_game.setdefault((row['canonical_game_id'],row['market_type']),[]).append(row)
 for g in m.get('games',[]):
  if str(g['game_id']) not in eligible:continue
  for market in ('spread','total'):
   reference=(g.get('reference') or {}).get(market) or {};book=reference.get('sportsbook')
   if not book: continue
   for pr in projection_by_game.get((g['game_id'],market),[]):
    quote=(reference.get('home') if market=='spread' else reference.get('over')) or {};line=quote.get('line')
    if line is None: continue
    side=('home' if pr['projection']+float(line)>=0 else 'away') if market=='spread' else ('over' if pr['projection']-float(line)>=0 else 'under');mo=market_index.get((g['game_id'],market,book,side))
    if not mo or mo.get('line') is None: continue
    edge=abs(float(pr['projection'])+float(mo['line'])) if market=='spread' else abs(float(pr['projection'])-float(mo['line']));did=stable_id('decision',pr['observation_id'],mo['observation_id'],side,edge);decisions.append({'decision_id':did,'prediction_observation_id':pr['observation_id'],'market_observation_id':mo['observation_id'],'canonical_game_id':g['game_id'],'market_type':market,'checkpoint':mo.get('lifecycle_state') or 'CURRENT_ACCEPTED','bet_side':side,'edge':edge,'market_provenance':{'sportsbook':book,'source':mo.get('source'),'freshness_status':mo.get('freshness_status')},'created_at':datetime.now(timezone.utc).isoformat()})
 report={'schema_version':'tracking-capture-preview-v2','generated_at':datetime.now(timezone.utc).isoformat(),'accept_requested':args.accept,'eligible_future_games':len(eligible),'eligibility_policy':'accepted market game, future exact kickoff, not closing/final','source_contracts':[str(pc.relative_to(ROOT)),str(mc.relative_to(ROOT))],'predictions':append_unique(DEST/'prediction_observations.jsonl',pred,'observation_id',args.accept),'markets':append_unique(DEST/'market_observations.jsonl',markets,'observation_id',args.accept),'decisions':append_unique(DEST/'decision_observations.jsonl',decisions,'decision_id',args.accept)};print(json.dumps(report,indent=2))
if __name__=='__main__':main()
