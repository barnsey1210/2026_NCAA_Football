#!/usr/bin/env python3
"""Build the compact public Historical Betting Explorer game-state contract."""
from __future__ import annotations
import json,tempfile
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/site/historical_betting_explorer_v1.json'
SPREAD=ROOT/'data/research/historical/comprehensive_market_timing_2021_2025/game_level_spread.csv'
CAND=ROOT/'data/research/historical/early_window_standard_replacement_2021_2025/spread_candidate_game_states.csv'
TOTAL=ROOT/'data/research/historical_totals/alternate_models_2021_2025/alternate_totals_game_level.csv'
ORDER=['SAT_11PM_ET','SUN_9AM_ET','SUN_12PM_ET','SUN_2PM_ET','SUN_4PM_ET','SUN_9PM_ET','MON_9AM_ET','MON_3PM_ET','TUE_2PM_ET','WED_2PM_ET','THU_2PM_ET','FRI_2PM_ET','CLOSE']
MODELS={
 'standard_spread_4src_equal_v1':{'label':'Four-source Standard Spread','market_type':'spread'},
 'standard_spread_5src_legacy_v1':{'label':'Legacy five-source Standard Spread','market_type':'spread'},
 'total_sp50_massey50_v1':{'label':'Historical 50/50 Total','market_type':'total'},
 'standard_total_40_40_20_sagarin_legacy_v1':{'label':'Legacy Sagarin Total','market_type':'total'},
}
COLUMNS=['game_id','season','week','game_date','away_team','home_team','model_id','market_type','checkpoint','checkpoint_sort','evidence_class','selected_team','selected_side','model_value','market_line','price','sportsbook','edge','result','realized_profit','clv','beat_close','won_line_move']

def clean(v):
 if pd.isna(v):return None
 if isinstance(v,(bool,str,int)):return v
 if isinstance(v,float):return round(v,6)
 return str(v)

def main():
 if not all(p.exists() for p in (SPREAD,CAND,TOTAL)):
  if OUT.exists() and json.loads(OUT.read_text()).get('schema_version')=='historical-betting-explorer-v1':
   print(f'Preserved reviewed {OUT}: canonical research inputs are not installed in this release workspace')
   return
  raise SystemExit('canonical historical explorer inputs are missing')
 rows=[]
 c=pd.read_csv(CAND,low_memory=False)
 for r in c.to_dict('records'):
  side=r['selected_side'];rows.append([r['game_id'],int(r['season']),int(r['week']),str(r.get('start_date') or '')[:10],r['away_team'],r['home_team'],'standard_spread_4src_equal_v1','spread',r['checkpoint'],ORDER.index(r['checkpoint']),r.get('sample_status'),r['home_team'] if side=='home' else r['away_team'],side,r.get('projection'),r.get('bet_line'),r.get('bet_price'),r.get('bet_book'),r.get('edge'),r.get('result'),r.get('profit'),r.get('clv'),bool(r.get('clv',0)>0),None if pd.isna(r.get('clv')) or abs(r.get('clv',0))<1e-12 else bool(r.get('clv')>0)])
 s=pd.read_csv(SPREAD,low_memory=False);s=s[s.model.eq('Five-source equal weight')]
 for r in s.to_dict('records'):
  side=r['selected_side'];clv=r.get('closing_clv_points');rows.append([r['game_id'],int(r['season']),int(r['week']),str(r.get('start_date') or '')[:10],r['away_team'],r['home_team'],'standard_spread_5src_legacy_v1','spread',r['checkpoint'],ORDER.index(r['checkpoint']),r.get('sample_status') or 'LEGACY_COMMON_SAMPLE',r['home_team'] if side=='home' else r['away_team'],side,r.get('model_home_margin'),r.get('bet_line'),r.get('bet_price'),r.get('bet_book'),r.get('edge_points'),r.get('result'),r.get('profit_units'),clv,bool(clv>0) if not pd.isna(clv) else None,None if pd.isna(clv) or abs(clv)<1e-12 else bool(clv>0)])
 t=pd.read_csv(TOTAL,low_memory=False);tm={'CONTROL_50_SP_50_MASSEY':'total_sp50_massey50_v1','BASELINE_40_SP_40_MASSEY_20_SAGARIN':'standard_total_40_40_20_sagarin_legacy_v1'};t=t[t.model.isin(tm)]
 for r in t.to_dict('records'):
  clv=r.get('clv');rows.append([r['game_id'],int(r['season']),int(r['week']),str(r.get('game_datetime_utc') or r.get('representative_date') or '')[:10],None,None,tm[r['model']],'total',r['checkpoint'],ORDER.index(r['checkpoint']),str(r.get('source_tier') or 'PRIMARY_COMMON_SAMPLE'),r['side'],r['side'],r.get('model_total'),r.get('bet_line'),-110,None,r.get('edge'),r.get('result'),r.get('profit_flat_110'),clv,bool(clv>0) if not pd.isna(clv) else None,None if pd.isna(clv) or abs(clv)<1e-12 else bool(clv>0)])
 rows=[[clean(v) for v in row] for row in rows]
 keys=[(r[0],r[6],r[8]) for r in rows]
 if len(keys)!=len(set(keys)):raise SystemExit('duplicate game/model/checkpoint explorer states')
 encoded_columns=['game_id','game_date','away_team','home_team','model_id','market_type','checkpoint','evidence_class','selected_team','selected_side','sportsbook']
 dictionaries={}
 for name in encoded_columns:
  i=COLUMNS.index(name);values=sorted({r[i] for r in rows if r[i] is not None});lookup={v:n for n,v in enumerate(values)};dictionaries[name]=values
  for r in rows:r[i]=None if r[i] is None else lookup[r[i]]
 payload={'schema_version':'historical-betting-explorer-v1','generated_at':datetime.now(timezone.utc).isoformat(),'season_range':[2021,2025],'week_domain':list(range(17)),'columns':COLUMNS,'dictionaries':dictionaries,'checkpoint_order':ORDER,'thresholds':[.5,1,1.5,2,2.5,3,3.5,4,4.5,5,6,7,8,9,10],'models':MODELS,'default':{'model_id':'standard_spread_4src_equal_v1','threshold':3,'row_dimension':'week','column_dimension':'checkpoint','metric':'roi','mode':'checkpoint'},'sample_strength':{'NORMAL':100,'LIMITED':50,'SMALL':20,'VERY_SMALL_INSUFFICIENT':0},'records':rows,'source_contract':'corrected game/model/checkpoint states from forensic repair e13f1219','decay_contract':'data/site/historical_betting_analytics_v2.json'}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=OUT.parent,delete=False) as f:json.dump(payload,f,separators=(',',':'),allow_nan=False);f.write('\n');p=Path(f.name)
 p.replace(OUT);OUT.chmod(0o644);print(f'Wrote {OUT}: {len(rows)} states, {OUT.stat().st_size} bytes')
if __name__=='__main__':main()
