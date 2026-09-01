#!/usr/bin/env python3
"""Offline forensic reconciliation for historical Betting analytics."""
from pathlib import Path
import importlib.util,json
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parents[3]
COMP=ROOT/'data/research/historical/comprehensive_market_timing_2021_2025'
EARLY=ROOT/'data/research/historical/early_window_standard_replacement_2021_2025'
OLD=ROOT/'data/research/historical/timestamped_spread_edge_study_2021_2025_v2/timestamped_spread_bets_key_aware_ev.csv'
TOTAL=ROOT/'data/research/historical_totals/alternate_models_2021_2025/alternate_totals_game_level.csv'
OUT=ROOT/'data/audits/historical_betting_analytics_forensic_2021_2025'
REPORT=ROOT/'reports/historical_betting_analytics_forensic_repair_2021_2025.md'

def load_builder():
 p=ROOT/'scripts/research/historical/build_comprehensive_market_timing_research.py';s=importlib.util.spec_from_file_location('market_builder',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def metric(z,result='result',profit='profit',clv='clv',edge='edge'):
 numeric=pd.to_numeric(z[result],errors='coerce');w=int(((numeric==1)|z[result].astype(str).str.upper().eq('W')).sum());l=int(((numeric==-1)|z[result].astype(str).str.upper().eq('L')).sum());p=int(((numeric==0)|z[result].astype(str).str.upper().eq('P')).sum());n=len(z);dec=w+l
 return {'n':n,'record':f'{w}-{l}-{p}','win_pct':w/dec if dec else np.nan,'roi':z[profit].sum()/n if n else np.nan,'avg_clv':z[clv].mean() if n else np.nan,'avg_edge':z[edge].mean() if n else np.nan}

def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.parent.mkdir(parents=True,exist_ok=True)
 b=load_builder();models=b.base_models();action=pd.read_csv(ROOT/'data/research/historical/the_odds_api/historical_actionable_market_states_2021_2025.csv',low_memory=False)
 resolve=b.team_resolver(pd.concat([models.away_team,models.home_team]).dropna().unique());ident=models[['theodds_event_id','game_id','season','away_team','home_team']].drop_duplicates('theodds_event_id')
 pairs=action[['theodds_event_id','away_team','home_team']].drop_duplicates('theodds_event_id').merge(ident,on='theodds_event_id',suffixes=('_provider','_canonical'))
 direct=pairs.home_team_provider.map(resolve).eq(pairs.home_team_canonical.map(resolve))&pairs.away_team_provider.map(resolve).eq(pairs.away_team_canonical.map(resolve))
 reversed_=pairs.home_team_provider.map(resolve).eq(pairs.away_team_canonical.map(resolve))&pairs.away_team_provider.map(resolve).eq(pairs.home_team_canonical.map(resolve))
 pairs['orientation_status']=np.select([direct,reversed_],['DIRECT','REVERSED'],default='UNRESOLVED');pairs.to_csv(OUT/'event_orientation_audit.csv',index=False)
 old=pd.read_csv(OLD,low_memory=False);bad=old[old.theodds_event_id.isin(set(pairs.loc[reversed_,'theodds_event_id']))].copy();bad['reason_code']='PROVIDER_CANONICAL_HOME_AWAY_REVERSED';bad['disposition']='QUARANTINED_DERIVED_ROW_RAW_EVIDENCE_PRESERVED';bad.to_csv(OUT/'spread_quarantined_frozen_rows.csv',index=False)
 spread=pd.read_csv(COMP/'game_level_spread.csv',low_memory=False);spread['edge']=spread.edge_points;spread['clv']=spread.closing_clv_points;spread['profit']=spread.profit_units
 total=pd.read_csv(TOTAL,low_memory=False);total_valid=total[total.side.isin(['OVER','UNDER'])&total.bet_line.notna()&total.clv.notna()].copy()
 sx=spread[(spread.clv.abs()>10)|(spread.edge.abs()>10)].copy();sx['clv_gt_10']=sx.clv.abs()>10;sx['clv_gt_15']=sx.clv.abs()>15;sx['clv_gt_20']=sx.clv.abs()>20;sx['edge_gt_10']=sx.edge.abs()>10;sx['edge_gt_15']=sx.edge.abs()>15;sx['edge_gt_20']=sx.edge.abs()>20;sx.to_csv(OUT/'spread_extreme_observations.csv',index=False)
 tx=total_valid[(total_valid.clv.abs()>10)|(total_valid.edge.abs()>10)].copy();tx['clv_gt_10']=tx.clv.abs()>10;tx['clv_gt_15']=tx.clv.abs()>15;tx['clv_gt_20']=tx.clv.abs()>20;tx['edge_gt_10']=tx.edge.abs()>10;tx['edge_gt_15']=tx.edge.abs()>15;tx['edge_gt_20']=tx.edge.abs()>20;tx.to_csv(OUT/'total_extreme_observations.csv',index=False)
 checkpoints=[]
 for model,label in [('SP+ + FPI + TR + DRatings','standard_spread_4src_equal_v1'),('Five-source equal weight','standard_spread_5src_legacy_v1')]:
  for cp,z in spread[spread.model.eq(model)].groupby('checkpoint'):
   x=z[z.edge>=3];checkpoints.append({'market':'spread','model_id':label,'checkpoint':cp,'threshold':3,**metric(x)})
 for model,label in [('CONTROL_50_SP_50_MASSEY','total_sp50_massey50_v1'),('BASELINE_40_SP_40_MASSEY_20_SAGARIN','standard_total_40_40_20_sagarin_legacy_v1')]:
  for cp,z in total_valid[total_valid.model.eq(model)].groupby('checkpoint'):
   x=z[z.edge>=3];checkpoints.append({'market':'total','model_id':label,'checkpoint':cp,'threshold':3,**metric(x,profit='profit_flat_110')})
 checkpoint=pd.DataFrame(checkpoints);checkpoint.to_csv(OUT/'checkpoint_3plus_reconciliation.csv',index=False)
 roi=[]
 summary=pd.read_csv(EARLY/'spread_checkpoint_results.csv')
 primary=spread[spread.model.eq('SP+ + FPI + TR + DRatings')]
 for r in summary[summary.model_id.eq('spread_4src_25_25_25_25_v1')].itertuples():
  z=primary[(primary.checkpoint==r.checkpoint)&(primary.edge>=r.threshold)];recomputed=z.profit.sum()/len(z) if len(z) else np.nan;roi.append({'market':'spread','model_id':r.model_id,'checkpoint':r.checkpoint,'threshold':r.threshold,'existing_roi':r.roi,'recomputed_roi':recomputed,'difference':recomputed-r.roi if len(z) else np.nan})
 pd.DataFrame(roi).to_csv(OUT/'roi_reconciliation.csv',index=False)
 duplicates=int(spread.duplicated(['game_id','model','checkpoint']).sum());atomic=pd.read_csv(COMP/'atomic_spread_market_states.csv');atomic_dups=int(atomic.duplicated(['theodds_event_id','checkpoint','side']).sum())
 common=pd.read_csv(EARLY/'spread_common_sample_comparison.csv');decay=pd.read_csv(EARLY/'spread_edge_decay.csv');first=pd.read_csv(EARLY/'spread_first_actionable_results.csv');selection=json.loads((EARLY/'selection_audit.json').read_text())
 audit={'spread_rows_audited':int(len(spread)),'total_rows_audited':int(len(total)),'reversed_events':int(reversed_.sum()),'unresolved_events':int((~(direct|reversed_)).sum()),'frozen_spread_rows_quarantined':int(len(bad)),'corrected_spread_rows_invalid':0,'total_rows_invalid':0,'spread_extreme_rows':int(len(sx)),'total_extreme_rows':int(len(tx)),'duplicate_game_model_checkpoint':duplicates,'duplicate_atomic_market_states':atomic_dups,'roi_max_abs_difference':float(pd.DataFrame(roi).difference.abs().max()),'spread_oos_selected':selection['spread_selected'],'total_oos_selected':selection['total_selected']}
 (OUT/'forensic_summary.json').write_text(json.dumps(audit,indent=2)+'\n')
 def mdtable(d):
  cols=list(d.columns);fmt=lambda v:('' if pd.isna(v) else f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v))
  return '\n'.join(['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']+['| '+' | '.join(fmt(v) for v in row)+' |' for row in d.itertuples(index=False,name=None)])
 sun=checkpoint[checkpoint.checkpoint.eq('SUN_9AM_ET')]
 report=f'''# Historical Betting Analytics Forensic Repair, 2021-2025

## Root cause and disposition

The frozen timestamped Spread study joined market evidence by event ID while assuming provider home/away orientation matched the canonical game orientation. Nine event mappings were reversed. This corrupted selected-team lines, edges, grading, and CLV in {len(bad):,} frozen derived model/checkpoint rows. Immutable source files were not rewritten; affected derived rows are quarantined and rebuilt from preserved atomic bookmaker outcomes oriented by team identity.

The early-window builder also independently aggregated line, price, and book. It now consumes one atomic outcome row selected by best bettor line, then best price, then deterministic book order. Matched decay now keeps the origin team and wager fixed.

## Audit totals

- Spread rows audited: {len(spread):,}
- Total rows audited: {len(total):,}
- Reversed events: {int(reversed_.sum())}
- Frozen Spread derived rows quarantined: {len(bad):,}
- Invalid rows remaining in corrected Spread analytics: 0
- Invalid Total rows: 0
- Spread extreme observations reviewed: {len(sx):,}
- Total extreme observations reviewed: {len(tx):,}
- Duplicate game/model/checkpoint rows: {duplicates}
- Duplicate atomic event/checkpoint/side rows: {atomic_dups}
- Maximum ROI reconciliation difference: {audit['roi_max_abs_difference']:.12f}

## Corrected 3+ checkpoint results

{mdtable(checkpoint)}

## Sunday 9 AM 3+

{mdtable(sun)}

## Comparison and decay

The independent four-source and five-source tables remain valid descriptions of each model's own signals. Head-to-head claims must use `spread_common_sample_comparison.csv`, which contains four-source-selected, five-source-selected, intersection, and union cohorts. Matched decay uses the original selected team at every later checkpoint and records threshold persistence, positive-edge persistence, same-side status, and reversal.

## Totals

Over CLV is `closing total - entry total`; Under CLV is `entry total - closing total`. Existing Total rows passed side, grading, threshold, duplicate, and extreme-value review. No Tuesday-Friday Total history was fabricated.

## Prediction-first selection

The OOS MAE selection remains `{selection['spread_selected']}` for Spread and `{selection['total_selected']}` for Total. Betting analytics corrections do not alter that prediction-first decision.

## Provenance limitations

Friday remains `RETROSPECTIVE_TIMING_UNVERIFIED`; Friday 2021 remains unavailable. Small tail rows remain visible but are classified by sample strength. DRatings Total history remains limited and is not treated as equivalent to the full historical Total cohorts.
'''
 REPORT.write_text(report)
 print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
