#!/usr/bin/env python3
"""Document the minimum frozen Shadow inference dependency graph."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'data/research/shadow_production_integration'
def classify(f):
 if 'prior_fpi_team_margin' in f or 'prior_tr_team_margin' in f: return 'required model input','missing: timestamped prior-game FPI/TR projection'
 if f.startswith(('home_','away_','diff_')) or f in {'predicted_market_spread','predicted_updated_sp_spread','saturday_baseline','source_coverage','feature_coverage','feature_week_gap_home','feature_week_gap_away'}: return 'required deterministic intermediate','pair completed team rows into genuine next game'
 return 'required model input','covered by base constructor or canonical schedule/projection state'
def main():
 a=json.load(open(ROOT/'data/research/shadow_component_bridge_v1/model_artifacts.json')); rows=[]
 for model,state in a['models'].items():
  for f in state['feature_order']:
   category,missing=classify(f); rows.append({'prediction':model,'frozen_model_artifact':'model_artifacts.json','feature':f,'classification':category,'upstream_canonical_source':'validated team-game features / ratings history / schedule mapping','deterministic_transformation':'home-away pairing and differences' if category.endswith('intermediate') else 'none or frozen imputation','join_keys':'season,next_game_id,team','cutoff_timing':'after prior game final; before target Saturday','missing_value_behavior':'frozen training median only after honest availability flag','covered_by_validated_42':f in set(pd.read_csv(ROOT/'data/research/shadow_live_feature_constructor/feature_parity_results.csv').query('passed').feature),'smallest_missing_downstream_transformation':missing})
 for f in a['sp_plus_component_total']['feature_order']: rows.append({'prediction':'sp_plus_component_total','frozen_model_artifact':'model_artifacts.json','feature':f,'classification':'required deterministic intermediate','upstream_canonical_source':'predicted updated SP+ offense/defense','deterministic_transformation':'pair four updated component ratings','join_keys':'season,next_game_id,team','cutoff_timing':'before target Saturday','missing_value_behavior':'unavailable if component prediction absent','covered_by_validated_42':False,'smallest_missing_downstream_transformation':'apply frozen component changes then pair'})
 d=pd.DataFrame(rows).drop_duplicates(['prediction','feature']); OUT.mkdir(parents=True,exist_ok=True); d.to_csv(OUT/'minimum_feature_dependency.csv',index=False)
 unresolved=pd.read_csv(ROOT/'data/research/shadow_live_feature_constructor/feature_parity_results.csv'); unresolved=unresolved[~unresolved.passed]
 summary={'status':'BLOCKED_REQUIRED_INPUT','features_by_classification':d.classification.value_counts().to_dict(),'previous_unresolved_fields':int(len(unresolved)),'genuinely_unavailable_upstream_fields':['home_prior_fpi_team_margin','away_prior_fpi_team_margin','home_prior_tr_team_margin','away_prior_tr_team_margin'],'cause':'No canonical timestamped prior-game FPI or TeamRankings game-projection history exists for prospective 2026. game_projection_sources_2026.csv currently contains Massey only.','unsafe_substitution_rejected':'Current FPI/TR team ratings are not equivalent to the Prediction Tracker game projections used during training.','production_integration_performed':False}
 (OUT/'minimum_feature_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 parity=json.load(open(ROOT/'data/research/shadow_component_bridge_v1/parity_report.json')); pd.DataFrame(parity['checks']).to_csv(OUT/'targeted_parity.csv',index=False); (OUT/'targeted_parity_summary.json').write_text(json.dumps({'status':parity['status'],'scope':'frozen prediction replay; production upstream gate remains blocked','checks':parity['checks']},indent=2)+'\n'); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
