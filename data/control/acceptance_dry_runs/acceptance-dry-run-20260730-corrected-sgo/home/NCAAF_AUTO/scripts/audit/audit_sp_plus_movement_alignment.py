#!/usr/bin/env python3
"""Integrity audit for the isolated SP+ movement-alignment study."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
REQUIRED=['sp_plus_team_week_targets.csv','sp_plus_features.csv','sp_plus_direction_predictions.csv','sp_plus_magnitude_predictions.csv','sp_plus_model_comparison.csv','team_rating_alignment.csv','alignment_category_results.csv','saturday_fair_spreads.csv','fair_spread_model_comparison.csv','confidence_results.csv','holdout_2025_results.csv','game_level_audit.csv','final_selection.json','summary.json']
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--input-dir',default='data/research/sp_plus_movement_alignment'); args=ap.parse_args(); p=ROOT/args.input_dir; checks=[]
 def ck(name,ok,detail=''): checks.append({'check':name,'passed':bool(ok),'detail':detail})
 ck('all required outputs parse',all((p/x).exists() for x in REQUIRED),','.join(x for x in REQUIRED if not (p/x).exists()))
 t=pd.read_csv(p/'sp_plus_team_week_targets.csv'); f=pd.read_csv(p/'sp_plus_features.csv',low_memory=False); pred=pd.read_csv(p/'sp_plus_direction_predictions.csv',low_memory=False); a=pd.read_csv(p/'team_rating_alignment.csv',low_memory=False); fair=pd.read_csv(p/'saturday_fair_spreads.csv'); s=json.loads((p/'summary.json').read_text()); final=json.loads((p/'final_selection.json').read_text())
 eligible=t[t.eligibility.astype(str).str.lower().eq('true')]
 ck('eligible snapshots adjacent',((eligible.target_sp_plus_week-eligible.current_snapshot_week)==1).all())
 ck('SP+ target arithmetic',np.allclose(eligible.next_sp_plus_overall-eligible.current_sp_plus_overall,eligible.actual_sp_plus_change,equal_nan=True))
 ck('completed game week equals SP+ target week',(f.completed_week==f.target_sp_plus_week).all())
 ck('no future SP+ feature names',not any(c.startswith('next_sp_plus') or c.startswith('actual_sp_plus') for c in s['selection']['features']))
 ck('SP+ predictions out of sample',pred.prediction_oos.astype(str).str.lower().eq('true').all())
 ck('2025 excluded from selection',s['selection']['selected_without_2025'] and 2025 not in [int(x) for x in pred.loc[pred.season==2025,'fit_seasons'].iloc[0].split(',')])
 ck('alignment based on predictions',all(c in a for c in ['predicted_market_direction','predicted_sp_plus_direction','alignment_category']))
 expected=(fair.frozen_away_market_rating+fair.predicted_away_market_move)-(fair.frozen_home_market_rating+fair.predicted_home_market_move)-2.5
 ck('market fair sign/HFA',np.allclose(expected,fair.market_fair_spread,equal_nan=True))
 expected2=(fair.current_away_sp_plus+fair.predicted_away_sp_plus_move)-(fair.current_home_sp_plus+fair.predicted_home_sp_plus_move)-2.5
 ck('SP+ fair sign/HFA',np.allclose(expected2,fair.sp_plus_fair_spread,equal_nan=True))
 ck('neutral-site uncertainty explicit',fair.neutral_site_uncertainty.notna().all())
 ck('opening field labeled timing unknown',fair.timing_limitation_flag.str.contains('TIMING-UNKNOWN',na=False).all())
 ck('protected production unchanged',s['protected_unchanged'])
 ck('publication repository clean',s['publication_repo_clean'])
 ck('holdout opened only after lock',final['holdout_opened_after_selection'])
 failed=[x for x in checks if not x['passed']]; out={'status':'PASSED' if not failed else 'FAILED','checks':checks,'failed':len(failed),'targets':len(t),'eligible':len(f),'holdout_rows':int((pred.season==2025).sum())}; (p/'audit_results.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())
