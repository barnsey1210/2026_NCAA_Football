#!/usr/bin/env python3
"""Build centralized, non-invented historical validation and decay contracts."""
from __future__ import annotations
import json,tempfile
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/site/historical_betting_analytics_v2.json';EARLY=ROOT/'data/research/historical/early_window_standard_replacement_2021_2025';COMP=ROOT/'data/research/historical/comprehensive_market_timing_2021_2025';TOTAL=ROOT/'data/research/historical_totals/alternate_models_2021_2025/alternate_totals_threshold_performance.csv'
TH=[.5,1,1.5,2,2.5,3,3.5,4,4.5,5,6,7,8,9,10];ORDER=['SAT_11PM_ET','SUN_9AM_ET','SUN_12PM_ET','SUN_2PM_ET','SUN_4PM_ET','SUN_9PM_ET','MON_9AM_ET','MON_3PM_ET','TUE_2PM_ET','WED_2PM_ET','THU_2PM_ET','FRI_2PM_ET','CLOSE']
def records(d): return json.loads(d.replace({float('nan'):None}).to_json(orient='records'))
def atomic(payload):
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=OUT.parent,delete=False) as f: json.dump(payload,f,indent=2,allow_nan=False);f.write('\n');p=Path(f.name)
 p.replace(OUT)
def normalize(rows,model_id,market,legacy=False):
 out=[]
 for r in rows:
  n=int(r['n']);strength='NORMAL' if n>=100 else 'LIMITED' if n>=50 else 'SMALL' if n>=20 else 'VERY_SMALL_INSUFFICIENT'
  out.append({'model_id':model_id,'model_version':'v1','market_type':market,'checkpoint':r['checkpoint'],'threshold':float(r['threshold']),'n':n,'record':r['record'],'win_pct':r.get('win_pct'),'roi':r.get('roi'),'beat_close_pct':r.get('beat_close_pct'),'won_line_move_pct':r.get('won_line_move_pct'),'avg_clv':r.get('avg_clv'),'median_clv':r.get('median_clv'),'positive_clv_pct':r.get('positive_clv_pct'),'clv_implied_ev':r.get('clv_implied_ev'),'avg_edge':r.get('avg_edge'),'median_edge':r.get('median_edge'),'sample_strength':strength,'sample_classification':r.get('sample_classification') or ('LEGACY_COMMON_SAMPLE' if legacy else 'RETROSPECTIVE_TIMING_UNVERIFIED')})
 return out
def main():
 s=pd.read_csv(EARLY/'spread_checkpoint_results.csv');s=s[s.model_id.eq('spread_4src_25_25_25_25_v1')];spread=normalize(records(s),'standard_spread_4src_equal_v1','spread')
 old=pd.read_csv(COMP/'spread_threshold_checkpoint_summary.csv');old=old[(old.model.eq('Five-source equal weight'))&(old.season_scope.eq('POOLED'))&(old.week_scope.eq('ALL'))];old=old.rename(columns={'games':'n','ats_pct':'win_pct','beat_closing_line_pct':'beat_close_pct'})
 spread+=normalize(records(old),'standard_spread_5src_legacy_v1','spread',True)
 t=pd.read_csv(EARLY/'total_checkpoint_results.csv');t=t[t.model_id.eq('total_sp50_massey50_v1')];totals=normalize(records(t),'total_sp50_massey50_v1','total')
 alt=pd.read_csv(TOTAL);alt=alt[(alt['sample'].eq('PRIMARY_COMMON_SAMPLE'))&(alt.model.eq('BASELINE_40_SP_40_MASSEY_20_SAGARIN'))&(alt.season_scope.eq('2021-2025'))&(alt.week_scope.eq('ALL_WEEKS'))];alt=alt.rename(columns={'edge_threshold':'threshold','ou_win_pct':'win_pct','flat_110_roi':'roi','beat_closing_line_pct':'beat_close_pct','average_clv':'avg_clv','average_edge':'avg_edge'})
 totals+=normalize(records(alt),'standard_total_40_40_20_sagarin_legacy_v1','total',True)
 decay=pd.read_csv(EARLY/'spread_edge_decay_summary.csv');decay=decay[decay.model_id.eq('spread_4src_25_25_25_25_v1')];sd=[]
 for r in records(decay):
  sd.append({'model_id':'standard_spread_4src_equal_v1','model_version':'v1','market_type':'spread','threshold':float(r['threshold']),'origin_checkpoint':r['origin_checkpoint'],'checkpoint':r['later_checkpoint'],'n':int(r['n']),'avg_origin_edge':r['avg_origin_edge'],'mean_remaining_edge':r['mean_remaining_edge'],'remaining_edge_pct':r['remaining_edge_pct'],'edge_persistence_pct':r['edge_persistence_pct'],'positive_edge_persistence_pct':r['positive_edge_persistence_pct'],'same_side_persistence_pct':r['same_side_persistence_pct'],'reversal_pct':r['reversal_pct'],'strengthened_pct':r['strengthened_pct'],'avg_clv':r['avg_clv'],'roi':r['roi'],'mode':'MATCHED_ORIGIN_SIDE_FIXED'})
 td=[]
 control=pd.read_csv(TOTAL);control=control[(control['sample'].eq('PRIMARY_COMMON_SAMPLE'))&(control.model.eq('CONTROL_50_SP_50_MASSEY'))&(control.season_scope.eq('2021-2025'))&(control.week_scope.eq('ALL_WEEKS'))]
 for r in records(control):
  if not r.get('next_checkpoint'):continue
  td.append({'model_id':'total_sp50_massey50_v1','model_version':'v1','market_type':'total','threshold':float(r['edge_threshold']),'origin_checkpoint':r['checkpoint'],'checkpoint':r['next_checkpoint'],'n':int(r['n']),'avg_origin_edge':r['average_edge'],'mean_remaining_edge':None,'remaining_edge_pct':None,'edge_persistence_pct':r['edge_persistence_pct'],'same_side_persistence_pct':1-(r['signal_reversed']/r['n']) if r.get('n') else None,'strengthened_pct':r['signal_strengthened']/r['n'] if r.get('n') else None,'avg_clv':r['average_clv'],'mode':'MATCHED_NEXT_CHECKPOINT_COHORT'})
 models=[
  {'model_id':'standard_spread_4src_equal_v1','model_version':'v1','market_type':'spread','label':'Standard Spread · 4-source equal','role':'PRIMARY_HISTORICAL_BASELINE','weights':{'SP+':.25,'FPI':.25,'TeamRankings':.25,'DRatings':.25},'historical_validation':'2021-2025'},
  {'model_id':'standard_spread_5src_legacy_v1','model_version':'v1','market_type':'spread','label':'Legacy Standard Spread · 5-source','role':'LEGACY_COMPARISON','weights':{'SP+':.2,'FPI':.2,'TeamRankings':.2,'Sagarin':.2,'DRatings':.2},'historical_validation':'2021-2025'},
  {'model_id':'total_sp50_massey50_v1','model_version':'v1','market_type':'total','label':'Total challenger · SP+/Massey 50/50','role':'PRIMARY_DEPLOYABLE_HISTORICAL_COMPARISON','weights':{'SP+':.5,'Massey Dual':.5},'historical_validation':'2021-2025'},
  {'model_id':'standard_total_40_40_20_sagarin_legacy_v1','model_version':'v1','market_type':'total','label':'Legacy Standard Total · Sagarin','role':'LEGACY_COMPARISON','weights':{'SP+':.4,'Massey Dual':.4,'Sagarin Total':.2},'historical_validation':'2021-2025'},
  {'model_id':'standard_total_sp_massey_dratings_v1','model_version':'v1','market_type':'total','label':'2026 Standard Total · DRatings','role':'PROSPECTIVE_ONLY','weights':{'SP+':.4,'Massey Dual':.4,'DRatings Total':.2},'historical_validation':'LIMITED_PROVENANCE_NOT_EQUIVALENT'}]
 common=pd.read_csv(EARLY/'spread_common_sample_comparison.csv')
 payload={'schema_version':'historical-betting-analytics-v2','generated_at':datetime.now(timezone.utc).isoformat(),'season_range':'2021-2025','default_selection':{'spread':{'model_id':'standard_spread_4src_equal_v1','checkpoint':'SUN_9AM_ET','threshold':3.0},'total':{'model_id':'total_sp50_massey50_v1','checkpoint':'SUN_9AM_ET','threshold':3.0}},'metric_definitions':{'win_pct':'ATS for spread; O/U win percentage for total','roi':'total realized profit divided by units risked; preserved American price where available','avg_clv':'Spread CLV is points from the selected wager team perspective: entry line minus closing line. Positive means the bettor beat the close.','beat_close_pct':'positive point CLV including unchanged closes in denominator','won_line_move_pct':'positive CLV among nonzero moves','clv_implied_ev':'null unless a validated market-specific conversion exists','independent_checkpoint':'fresh signals selected independently at each checkpoint','matched_decay':'same origin game, side, wager, and threshold followed through later checkpoints'},'sample_strength_policy':{'NORMAL':'N >= 100','LIMITED':'N 50-99','SMALL':'N 20-49','VERY_SMALL_INSUFFICIENT':'N < 20'},'checkpoint_order':ORDER,'thresholds':TH,'models':models,'independent_checkpoint_performance':spread+totals,'common_sample_spread_comparison':records(common),'matched_signal_decay':sd+td,'coverage':{'spread':'Saturday 11 PM is partial; Friday 2021 absent; checkpoint samples differ.','total':'Only preserved Sunday and close checkpoints; no Monday-Friday Total history.','dratings_total':'Prospective 2026 identity; historical cohort too limited for equivalent validation.'},'source_references':[str((EARLY/'spread_checkpoint_results.csv').relative_to(ROOT)),str((EARLY/'spread_common_sample_comparison.csv').relative_to(ROOT)),str((EARLY/'spread_edge_decay.csv').relative_to(ROOT)),str((EARLY/'total_checkpoint_results.csv').relative_to(ROOT)),str((COMP/'spread_threshold_checkpoint_summary.csv').relative_to(ROOT)),str(TOTAL.relative_to(ROOT))]};atomic(payload);print(f'Wrote {OUT}')
if __name__=='__main__':main()
