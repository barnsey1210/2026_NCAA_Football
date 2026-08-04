#!/usr/bin/env python3
"""Compare auditable CFP resume blends with causal and descriptive Top-25 inputs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'data/models/cfp_weekly_rankings_history.csv'
OUT=ROOT/'data/models/cfp_resume_variant_backtest.json'
VARIANTS={
 'control_qw_t25':['game_control','quality_wins','TOP25'],
 'control_qw_t25_losses':['game_control','quality_wins','TOP25','losses'],
 'control_qw_t25_bad_losses':['game_control','quality_wins','TOP25','bad_losses'],
 'control_qw_t25_losses_bad_losses':['game_control','quality_wins','TOP25','losses','bad_losses'],
 'full_resume_no_separate_sos':['game_control','quality_wins','TOP25','losses','bad_losses','avg_capped_mov','avg_weighted_mol'],
}
NEG={'losses','bad_losses','avg_weighted_mol'}

def score_metrics(frame, cols, w, details=True):
    x=frame[[c+'_p' for c in cols]].to_numpy(); frame=frame.copy(); frame['score']=x@w
    frame['model_rank']=frame.groupby(['season','week']).score.rank(ascending=False,method='first')
    ranked=frame[frame.actual_cfp_rank<=25]; top12=frame[frame.actual_cfp_rank<=12]
    top4=frame[frame.actual_cfp_rank<=4]
    rho=ranked[['model_rank','actual_cfp_rank']].corr(method='spearman').iloc[0,1] if details else 0.0
    return {'top4_recall':float((top4.model_rank<=4).mean()),
            'top12_recall':float((top12.model_rank<=12).mean()),'top25_recall':float((ranked.model_rank<=25).mean()),
            'top25_mae':float((ranked.model_rank-ranked.actual_cfp_rank).abs().mean()),
            'spearman':float(rho) if pd.notna(rho) else 0.0,'ranked_rows':len(ranked)}

def prep(frame,cols):
    f=frame.copy()
    for c in cols:
        p=f.groupby(['season','week'])[c].rank(pct=True,method='average')
        f[c+'_p']=1-p if c in NEG else p
    return f

def candidates(k,seed):
    rng=np.random.default_rng(seed); a=[np.ones(k)/k]
    a.extend(rng.dirichlet(np.ones(k),800)); return a

def fit(train,cols,seed):
    best=None
    for w in candidates(len(cols),seed):
        m=score_metrics(train,cols,w,False); key=(m['top12_recall'],m['top25_recall'],-m['top25_mae'])
        if best is None or key>best[0]: best=(key,w,m)
    return best[1],best[2]

def run(frame,name,template,top25_col):
    cols=[top25_col if c=='TOP25' else c for c in template]
    data=prep(frame,cols); folds=[]
    for season in sorted(data.season.unique()):
        w,tr=fit(data[data.season!=season],cols,int(season)+len(cols)); te=score_metrics(data[data.season==season],cols,w)
        folds.append({'held_out_season':int(season),'weights':dict(zip(cols,map(lambda x:round(float(x),3),w))), 'test':te})
    total=sum(x['test']['ranked_rows'] for x in folds)
    keys=['top4_recall','top12_recall','top25_recall','top25_mae','spearman']
    agg={k:sum(x['test'][k]*x['test']['ranked_rows'] for x in folds)/total for k in keys}
    bands={}
    for label,subset in [('early',data[data.week<=3]),('late',data[data.week>3])]:
        w,_=fit(data,cols,991+len(cols))
        bands[label]=score_metrics(subset,cols,w) if len(subset) else None
    return {'name':name,'metrics':cols,'top25_definition':top25_col,
            'prospective':top25_col!='top25_wins',
            'sos_handling':'embedded only in schedule-adjusted game_control',
            'held_out_aggregate':agg,'week_band_diagnostics':bands,'folds':folds}

frame=pd.read_csv(SRC)
if 'losses' not in frame: raise SystemExit('Rebuild cfp_weekly_rankings_history.csv first')
result={'method':'leave-one-season-out; weights trained on other seasons; within-week percentiles','championship_flags_used':False,
        'selection_objective':'maximize Top-12 recall, then Top-25 recall, then minimize Top-25 MAE',
        'warning':'same-week top25_wins is descriptive/circular; prior_top25_wins is the preferred live-prediction input.',
        'variants':[run(frame,n,c,t) for t in ['prior_top25_wins','provisional_top25_wins','top25_wins'] for n,c in VARIANTS.items()]}
OUT.write_text(json.dumps(result,indent=2)+'\n')
for x in result['variants']: print(x['name'],x['held_out_aggregate'])
print('Wrote',OUT)
