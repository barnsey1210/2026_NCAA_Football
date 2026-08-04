#!/usr/bin/env python3
"""Export immutable, inference-only Shadow component model state.

This is a controlled research export.  It fits the already-selected families on
2021-2024 only and writes their complete numerical state; weekly production must
load these artifacts and must never call this exporter.
"""
from __future__ import annotations

import hashlib, importlib.util, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/research/shadow_component_bridge_v1"
TRAIN = [2021, 2022, 2023, 2024]

def module(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def sha(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,np.ndarray): return v.tolist()
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,)): return float(v)
    raise TypeError(type(v).__name__)
def selected_linear(model, family: str, features: list[str], target: str, sign: str):
    med,mu,sd=model['state']; beta=model[family]
    return {'family':family,'target':target,'target_sign':sign,'feature_order':features,
            'imputation':{'method':'training_median','values':med},
            'scaling':{'method':'training_mean_std','mean':mu,'std':sd},
            'intercept':float(beta[0]),'coefficients':beta[1:],
            'direction_calibration':{'softmax_coefficients':model['class_beta'],'threshold':float(model['threshold'])}}

def movement_artifacts(m):
    market_sel=json.loads((ROOT/'data/research/team_rating_movement_model/final_selection.json').read_text())
    market=pd.read_csv(ROOT/'data/research/team_rating_movement_model/repeatable_performance_features.csv',low_memory=False)
    market_model=m.fit_models(market,market_sel['features'],market_sel['no_move_threshold'],TRAIN)

    sp_sel=json.loads((ROOT/'data/research/sp_plus_movement_alignment/final_selection.json').read_text())['selection']
    sp=pd.read_csv(ROOT/'data/research/sp_plus_movement_alignment/sp_plus_features.csv',low_memory=False)
    sp['actual_market_rating_change']=sp.actual_sp_plus_change
    sp_model=m.fit_models(sp,sp_sel['features'],sp_sel['threshold'],TRAIN)

    comp=pd.read_csv(ROOT/'data/research/sp_plus_total_movement/sp_plus_component_features.csv',low_memory=False)
    comp['actual_defense_improvement']=-comp.actual_sp_plus_defense_change
    comp['current_sp_offense']=comp.current_sp_plus_offense; comp['current_sp_defense']=comp.current_sp_plus_defense
    common=['closing_spread','closing_total','total_residual','final_margin','gc_game_control_index','game_pace','off_plays','games_played','completed_week']
    off=[x for x in ['points_scored','off_ppa','off_pass_success_rate','off_rush_success_rate','off_success_rate','off_explosiveness','drive_off_points_per_opportunity','off_game_clock_seconds_per_play','turnover_margin','defensive_touchdowns','special_teams_touchdowns','garbage_time_scoring','repeatable_offense_performance','trailing_2_game_off_eff','trailing_3_game_off_eff','season_to_date_off_eff','recent_form_vs_season','opponent_sp_plus_rating','current_sp_offense']+common if x in comp and comp.loc[comp.season.isin([2021,2022,2023]),x].notna().any()]
    de=[x for x in ['points_allowed','def_ppa_allowed','def_pass_success_allowed','def_rush_success_allowed','def_success_allowed','def_explosiveness_allowed','drive_def_points_per_opportunity_allowed','def_havoc_rate','turnover_margin','defensive_touchdowns','garbage_time_scoring','repeatable_defense_performance','trailing_2_game_def_eff','trailing_3_game_def_eff','season_to_date_def_eff','recent_form_vs_season','opponent_sp_plus_rating','current_sp_defense']+common if x in comp and comp.loc[comp.season.isin([2021,2022,2023]),x].notna().any()]
    comp['actual_market_rating_change']=comp.actual_sp_plus_offense_change; comp['rules_repeatable_spread']=comp.repeatable_offense_performance
    off_model=m.fit_models(comp,off,1.0,TRAIN)
    comp['actual_market_rating_change']=comp.actual_defense_improvement; comp['rules_repeatable_spread']=comp.repeatable_defense_performance
    def_model=m.fit_models(comp,de,1.0,TRAIN)
    return {
      'market_rating_movement':selected_linear(market_model,market_sel['magnitude_model'],market_sel['features'],'actual_market_rating_change','positive = team market-rating upgrade'),
      'sp_plus_overall_movement':selected_linear(sp_model,sp_sel['magnitude_model'],sp_sel['features'],'actual_sp_plus_change','positive = SP+ overall upgrade'),
      'sp_plus_offense_movement':selected_linear(off_model,'huber',off,'actual_sp_plus_offense_change','positive = offense rating increase'),
      'sp_plus_defense_improvement':selected_linear(def_model,'huber',de,'actual_defense_improvement','positive = defense raw rating decrease/improvement'),
    }

def fpi_tr_artifacts(m):
    f=module(ROOT/'scripts/research/build_predicted_fpi_tr_saturday.py','fpi_tr_export')
    rows=f.build_rows(); features=f.feature_columns()
    eligible=rows[rows.cutoff_valid&rows.game_identity_valid&rows.fpi_target.notna()&rows.tr_target.notna()&rows.saturday_baseline.notna()].copy()
    out={}
    for label,target in [('fpi_next_game_spread','fpi_target'),('teamrankings_next_game_spread','tr_target')]:
        train=eligible[eligible.season.isin(TRAIN)].dropna(subset=[target]); state,x=f.standardize_fit(train,features); beta=m.elastic_fit(x,train[target].to_numpy(float),.06,5)
        out[label]={'family':'elastic_net','target':target,'target_sign':'canonical home spread; negative = home favorite','feature_order':features,
                    'imputation':{'method':'training_median','values':state[0]},'scaling':{'method':'training_mean_std','mean':state[1],'std':state[2]},
                    'intercept':float(beta[0]),'coefficients':beta[1:]}
    return out

def sp_total_conversion_artifact():
    t=module(ROOT/'scripts/research/build_sp_plus_total_movement.py','sp_total_export')
    games=pd.read_csv(ROOT/'data/research/sp_plus_total_movement/game_total_projections.csv',low_memory=False)
    features=['predicted_updated_home_offense','predicted_updated_away_offense','predicted_updated_home_defense','predicted_updated_away_defense']
    fit=games[games.season.isin([2021,2022,2023])]
    state=t.fit_linear(fit[features],fit.actual_close,10)
    return {'family':'ridge_linear','target':'next_game_closing_total','feature_order':features,
            'imputation':{'method':'training_median','values':state['med']},
            'scaling':{'method':'training_mean_std','mean':state['mu'],'std':state['sd']},
            'intercept':float(state['b'][0]),'coefficients':state['b'][1:],
            'selection':'pure_sp_plus_total selected on 2024; conversion fitted on 2021-2023 only'}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=module(ROOT/'scripts/research/build_team_rating_movement_model.py','movement_export')
    models={**movement_artifacts(m),**fpi_tr_artifacts(m)}
    total_sel=json.loads((ROOT/'data/research/sp_plus_total_movement/final_selection.json').read_text())['total_selection']
    payload={'schema_version':'shadow-component-model-artifacts-v1','artifact_version':'shadow-components-2026.1',
      'exported_at':datetime.now(timezone.utc).isoformat(),'fit_seasons':TRAIN,'holdout_excluded':[2025,2026],
      'normal_weekly_use':'load-only; never run this exporter from production automation','models':models,
      'sp_plus_component_total':sp_total_conversion_artifact(),
      'sp_plus_team_points_diagnostic':total_sel['team_points_formula'],
      'approved_ensembles':{'spread':{'market':.25,'sp_plus':.25,'fpi':.40,'teamrankings':.10},'total':{'sp_plus_component':.60,'existing_projected_total':.40,'correction':-1.1573}},
      'source_selection_files':{p:sha(ROOT/p) for p in ['data/research/team_rating_movement_model/final_selection.json','data/research/sp_plus_movement_alignment/final_selection.json','data/research/sp_plus_total_movement/final_selection.json','data/research/predicted_fpi_tr_saturday/final_selection.json']}}
    path=OUT/'model_artifacts.json'; path.write_text(json.dumps(payload,indent=2,default=clean)+'\n')
    inventory=[]
    for name,state in {**models,'sp_plus_component_total':payload['sp_plus_component_total']}.items():
        inventory.append({
          'model':name,
          'coefficients_or_serialized_estimator':'exported coefficients',
          'intercept':'exported',
          'feature_order':'exported',
          'imputation_state':'training medians exported',
          'scaling_state':'training means/std exported',
          'calibration':'direction softmax exported' if state.get('direction_calibration') else 'not applicable',
          'thresholds':state.get('direction_calibration',{}).get('threshold','not applicable'),
          'transformations':state.get('target_sign',state.get('selection','linear conversion')),
          'state_before_bridge':'selection metadata only; insufficient for exact inference'
        })
    pd.DataFrame(inventory).to_csv(OUT/'model_state_inventory.csv',index=False)
    manifest={'artifact':str(path.relative_to(ROOT)),'sha256':sha(path),'models':list(models),'fit_seasons':TRAIN,'holdout_excluded':True}
    (OUT/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
