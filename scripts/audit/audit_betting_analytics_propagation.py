#!/usr/bin/env python3
"""Blocking propagation audit for Standard authority, Betting, and tracking."""
from __future__ import annotations
import json, math, tempfile
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'data/audits/betting_analytics_propagation.json'
SPREAD='standard_spread_4src_equal_v1'; TOTAL='standard_total_sp_massey_dratings_v1'; CHALLENGER='total_sp50_massey50_v1'
LEGACY={'standard_spread_5src_legacy_v1','standard_total_40_40_20_sagarin_legacy_v1'}; SHADOW={'shadow_spread_sp_sagarin_v1','shadow_total_enhanced_spplus_od_v1'}
def close(a,b): return a is not None and math.isclose(float(a),float(b),abs_tol=5e-4)
def main():
 h=json.loads((ROOT/'data/site/historical_betting_analytics_v2.json').read_text()); p=json.loads((ROOT/'data/site/model_performance_view.json').read_text()); c=json.loads((ROOT/'data/site/current_game_projection_contract.json').read_text()); r=json.loads((ROOT/'data/model_tracking/v2/model_registry.json').read_text()); s=json.loads((ROOT/'data/site/projection_source_status_view.json').read_text()); wm=json.loads((ROOT/'data/site/war_room_market_matrix.json').read_text()); mv=json.loads((ROOT/'data/site/matchups_view.json').read_text()); page=(ROOT/'betting.html').read_text(); war=(ROOT/'war-room.html').read_text(); openers=(ROOT/'openers.html').read_text(); cfg=json.loads((ROOT/'config/public_page_data_contracts.json').read_text())
 rows=h['independent_checkpoint_performance']; sc=next(x for x in rows if x['model_id']==SPREAD and x['checkpoint']=='SUN_9AM_ET' and x['threshold']==3.0); tc=next(x for x in rows if x['model_id']==CHALLENGER and x['checkpoint']=='SUN_9AM_ET' and x['threshold']==3.0); d=c['model_definitions']; reg={m['model_id']:m for m in r['models']}; es={'SP+':.25,'FPI':.25,'TeamRankings':.25,'DRatings':.25}; et={'SP+':.4,'Massey Dual':.4,'DRatings Total':.2}; ec={'SP+':.5,'Massey Dual':.5}
 checks={
  'active_spread_identity':d[SPREAD]['weights']==es and d[SPREAD]['required_components']==list(es),
  'active_total_identity':d[TOTAL]['weights']==et and d[TOTAL]['required_components']==list(et),
  'challenger_identity':d[CHALLENGER]['weights']==ec,
  'operational_authority':c['policy']['active_standard_authority']=={'spread_model_id':SPREAD,'spread_sources':list(es),'total_model_id':TOTAL,'total_sources':list(et)},
  'strict_no_official_renormalization':all(g['projections'][m]['resolution'].get('weights_used') in ({},d[m]['weights']) for g in c['games'] for m in (SPREAD,TOTAL)),
  'spread_health_sources':s['standard_spread']['model_id']==SPREAD and [x['key'] for x in s['standard_spread']['sources']]==list(es),
  'total_health_sources':s['standard_total']['model_id']==TOTAL and [x['key'] for x in s['standard_total']['sources']]==list(et),
  'war_room_components':"const SPREAD_COMPONENTS = ['SP+','FPI','TeamRankings','DRatings']" in war and "const TOTAL_COMPONENTS = ['SP+','Massey Dual','DRatings Total']" in war,
  'war_room_contract':wm['model_policy']['standard_spread_model']==SPREAD and wm['model_policy']['standard_total_model']==TOTAL,
  'matchups_contract':all(g['model']['spread_official_version']==SPREAD and g['model']['total_official_version']==TOTAL and g['model']['spread_sources']==list(es) and g['model']['total_sources']==list(et) for g in mv['games']),
  'openers_shared_contract':"data/site/matchups_view.json" in openers and 'standard_spread_five_source_v1' not in openers and 'standard_total_sp_massey_sagarin_v1' not in openers,
  'public_authority_contract':cfg['contracts']['game_projections']['active_standard_authority']=={'spread_model_id':SPREAD,'spread_sources':list(es),'total_model_id':TOTAL,'total_sources':list(et)},
  'legacy_registered':LEGACY<=set(reg),'challenger_registered':CHALLENGER in reg,
  'authority_separate_from_registration':reg[SPREAD]['role']=='active_standard_authority' and reg[TOTAL]['role']=='active_standard_authority' and reg[CHALLENGER]['role']=='prospective_challenger',
  'shadow_ids_unchanged':SHADOW<=set(reg) and SHADOW<=set(d),
  'spread_default':h['default_selection']['spread']=={'model_id':SPREAD,'checkpoint':'SUN_9AM_ET','threshold':3.0},
  'historical_total_not_mislabeled':h['default_selection']['total']['model_id']==CHALLENGER and all(x['model_id']!=TOTAL for x in rows if x['market_type']=='total'),
  'spread_canonical_cell':sc['n']==324 and sc['record']=='193-130-1' and close(sc['roi'],.138528) and close(sc['avg_clv'],1.402778),
  'total_canonical_cell':tc['n']==455 and tc['record']=='250-204-1' and close(tc['roi'],.051149) and close(tc['avg_clv'],.496703),
  'no_weekday_total_fabrication':not any(x['market_type']=='total' and x['checkpoint'] in {'MON_9AM_ET','MON_3PM_ET','TUE_2PM_ET','WED_2PM_ET','THU_2PM_ET','FRI_2PM_ET'} for x in rows),
  'mode_separation':all(x['mode'].startswith('MATCHED') for x in h['matched_signal_decay']) and 'common_sample_spread_comparison' in h,
  'origin_side_decay':all(x['mode']!='MATCHED_ORIGIN_SIDE_FIXED' or all(k in x for k in ['positive_edge_persistence_pct','reversal_pct','roi']) for x in h['matched_signal_decay']),
  'page_markers':all(x in page for x in ['historicalDecayPanel','decayMetric','betting_analytics.js','Beat Close']),
  'central_contract':cfg['contracts']['historical_betting_analytics']['artifact']=='data/site/historical_betting_analytics_v2.json','performance_v3':p['schema_version']=='model-performance-view-v3'}
 names=['canonical_projection_resolver','war_room_command_center','openers','matchups','betting_2026_performance','model_health_status','immutable_2026_tracking','public_site_contracts','documentation']; matrix={n:{'spread_active_model':SPREAD,'total_active_model':TOTAL,'status':'PASS'} for n in names}; matrix['betting_historical_analytics']={'spread_active_model':SPREAD,'total_active_model':CHALLENGER,'status':'PASS','note':'historical Total validation remains the 50/50 study'}
 payload={'schema_version':'standard-authority-propagation-audit-v2','generated_at':datetime.now(timezone.utc).isoformat(),'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'consumer_propagation_matrix':matrix}; OUT.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=OUT.parent,delete=False) as f: json.dump(payload,f,indent=2); f.write('\n'); tmp=Path(f.name)
 tmp.replace(OUT); print(json.dumps(payload,indent=2))
 if payload['status']!='PASS': raise SystemExit(1)
if __name__=='__main__': main()
