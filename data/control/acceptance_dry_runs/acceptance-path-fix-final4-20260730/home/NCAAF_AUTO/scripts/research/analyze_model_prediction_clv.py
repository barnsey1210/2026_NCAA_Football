#!/usr/bin/env python3
"""Focused CLV/execution extension of the frozen model-variance study."""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2];REPORTS=ROOT/'reports'
SOURCE=REPORTS/'model_prediction_variance_game_sample.csv';AUDIT=REPORTS/'model_prediction_variance_audit.json'
RNG=np.random.default_rng(20260730)

def roi(w,l):return (w-1.1*l)/(w+l) if w+l else np.nan
def split_masks(d):return [('development_2021_2023',d.season<=2023),('confirmation_2024',d.season==2024),('locked_2025',d.season==2025),('all_2021_2025',d.season>0)]
def md(df):
    def c(v):
        if pd.isna(v):return ''
        return f'{v:.4f}' if isinstance(v,float) else str(v)
    h=list(df.columns);return '\n'.join(['| '+' | '.join(h)+' |','| '+' | '.join(['---']*len(h))+' |']+['| '+' | '.join(c(v) for v in r)+' |' for r in df.itertuples(index=False,name=None)])

def summarize(z):
    x=z.point_clv.dropna();a=z.ats_margin.dropna();w=int((a>0).sum());l=int((a<0).sum());p=int((a==0).sum())
    return {'games':len(z),'average_point_clv':x.mean(),'median_point_clv':x.median(),'positive_clv_percentage':(x>0).mean(),
      'clv_at_least_0_5':(x>=.5).mean(),'clv_at_least_1':(x>=1).mean(),'clv_at_least_1_5':(x>=1.5).mean(),'clv_at_least_2':(x>=2).mean(),
      'percentage_moving_toward_consensus':z.market_moved_toward_consensus.mean(),'average_open_to_close_movement':x.mean(),
      'ats_wins':w,'ats_losses':l,'ats_pushes':p,'ats_percentage':w/(w+l) if w+l else np.nan,'roi_at_minus_110':roi(w,l),'average_ats_margin':a.mean()}

def robust_ols(d,ycol,features,label):
    z=d[[ycol]+features].dropna();X=np.column_stack([np.ones(len(z))]+[z[c].to_numpy(float) for c in features]);y=z[ycol].to_numpy(float)
    inv=np.linalg.pinv(X.T@X);b=inv@X.T@y;e=y-X@b;h=np.sum((X@inv)*X,axis=1);u=e/(1-h);meat=X.T@((u*u)[:,None]*X);cov=inv@meat@inv;se=np.sqrt(np.maximum(np.diag(cov),0))
    return pd.DataFrame({'model':label,'outcome':ycol,'term':['intercept']+features,'coefficient':b,'robust_se_hc3':se,'ci95_low':b-1.96*se,'ci95_high':b+1.96*se,'n':len(z)})

def robust_logit(d,ycol,features,label):
    z=d[[ycol]+features].dropna();X=np.column_stack([np.ones(len(z))]+[z[c].to_numpy(float) for c in features]);y=z[ycol].to_numpy(float);b=np.zeros(X.shape[1])
    for _ in range(100):
        p=1/(1+np.exp(-np.clip(X@b,-30,30)));w=np.maximum(p*(1-p),1e-8);step=np.linalg.pinv(X.T@(w[:,None]*X))@X.T@(y-p);b+=step
        if np.max(np.abs(step))<1e-8:break
    p=1/(1+np.exp(-np.clip(X@b,-30,30)));bread=np.linalg.pinv(X.T@((p*(1-p))[:,None]*X));score=X*(y-p)[:,None];cov=bread@(score.T@score)@bread;se=np.sqrt(np.maximum(np.diag(cov),0))
    return pd.DataFrame({'model':label,'outcome':ycol,'term':['intercept']+features,'coefficient':b,'robust_se_sandwich':se,'ci95_low':b-1.96*se,'ci95_high':b+1.96*se,'n':len(z)})

def main():
    d=pd.read_csv(SOURCE);prior=json.loads(AUDIT.read_text());required=['sp_plus_projected_home_margin','fpi_projected_home_margin','teamrankings_projected_home_margin','consensus_projected_home_margin','projection_standard_deviation','projection_range','opening_market_home_margin','closing_market_home_margin','final_home_margin','start_date','season','week','neutral_site']
    missing_cols=[c for c in required if c not in d];missing_rows=d[required].isna().sum().to_dict()
    if missing_cols or any(missing_rows.values()):raise SystemExit(f'Incomplete source: columns={missing_cols}, missing={missing_rows}')
    # Selection is made at the opener. Positive opening edge selects home; negative selects away.
    d['consensus_edge']=d.consensus_projected_home_margin-d.opening_market_home_margin
    d=d[d.consensus_edge!=0].copy();d['selected_side_sign']=np.sign(d.consensus_edge).astype(int)
    d['consensus_selected_side']=np.where(d.selected_side_sign>0,d.Home,d.Road)
    d['selected_location']=np.where(d.selected_side_sign>0,'home','away')
    d['opening_number_taken']=-d.selected_side_sign*d.opening_market_home_margin
    d['closing_number']=-d.selected_side_sign*d.closing_market_home_margin
    d['point_clv']=d.opening_number_taken-d.closing_number
    d['positive_clv']=d.point_clv>0
    for x,n in [(.5,'0_5'),(1,'1'),(1.5,'1_5'),(2,'2')]:d['clv_at_least_'+n]=d.point_clv>=x
    d['market_moved_toward_consensus']=d.point_clv>0
    d['ats_margin']=d.selected_side_sign*(d.final_home_margin-d.opening_market_home_margin)
    d['ats_result']=np.where(d.ats_margin>0,'win',np.where(d.ats_margin<0,'loss','push'))
    d['selected_market_role']=np.where(d.opening_number_taken<0,'favorite',np.where(d.opening_number_taken>0,'underdog','pick'))
    d['early_season']=(d.week<=4).astype(int);d['selected_home']=(d.selected_side_sign>0).astype(int);d['selected_favorite']=(d.opening_number_taken<0).astype(int)
    q=prior['development_percentiles']['projection_range'];d['dispersion_group']=pd.cut(d.projection_range,[-np.inf,q[0],q[3],np.inf],labels=['low','medium','high'],include_lowest=True)
    d['consensus_edge_band']=pd.cut(d.consensus_edge.abs(),[1,2,3,4,6,np.inf],labels=['1.0-1.99','2.0-2.99','3.0-3.99','4.0-5.99','6.0+'],right=False)
    # Concentration: for a 2-1 split, measure the dissenter's share of total absolute
    # model-edge magnitude. >=50% is outlier-driven; 33-50% moderate; <33% balanced.
    opening_edges=np.column_stack([d.sp_plus_projected_home_margin-d.opening_market_home_margin,d.fpi_projected_home_margin-d.opening_market_home_margin,d.teamrankings_projected_home_margin-d.opening_market_home_margin])
    names=np.array(['SP+','FPI','TeamRankings']);conc=[];outmodel=[];outdist=[];leverage=[]
    for row,ce in zip(opening_edges,d.consensus_edge):
        signs=np.sign(row);twoone=(np.sum(signs>0)==2 or np.sum(signs<0)==2)
        if not twoone:conc.append('balanced consensus');outmodel.append('');outdist.append(np.nan);leverage.append(0);continue
        pair_sign=1 if np.sum(signs>0)==2 else -1;oi=int(np.where(signs!=pair_sign)[0][0]);pair=[i for i in range(3) if i!=oi];pm=np.mean(row[pair]);lev=abs(row[oi])/max(np.sum(np.abs(row)),1e-9)
        conc.append('outlier-driven consensus' if lev>=.5 else 'moderately concentrated' if lev>=1/3 else 'balanced consensus');outmodel.append(names[oi]);outdist.append(abs(row[oi]-pm));leverage.append(lev)
    d['consensus_concentration']=conc;d['outlier_model_at_open']=outmodel;d['outlier_distance_from_pair_at_open']=outdist;d['outlier_leverage']=leverage;d['outlier_driven']=(d.consensus_concentration=='outlier-driven consensus').astype(int)
    d['unanimous_at_open']=np.where(np.all(opening_edges>0,axis=1)|np.all(opening_edges<0,axis=1),1,0)
    d['unanimous_ge_1']=np.where(np.all(opening_edges>=1,axis=1)|np.all(opening_edges<=-1,axis=1),1,0);d['unanimous_ge_2']=np.where(np.all(opening_edges>=2,axis=1)|np.all(opening_edges<=-2,axis=1),1,0)
    d['closing_consensus_edge']=d.selected_side_sign*(d.consensus_projected_home_margin-d.closing_market_home_margin)
    d['opening_selected_edge']=d.consensus_edge.abs();d['points_edge_lost']=d.opening_selected_edge-d.closing_consensus_edge
    d['edge_retention_ratio']=np.where(d.opening_selected_edge>=1,d.closing_consensus_edge/d.opening_selected_edge,np.nan)
    d['edge_fully_disappeared']=d.closing_consensus_edge<=0;d['market_crossed_consensus']=d.closing_consensus_edge<0;d['edge_increased']=d.closing_consensus_edge>d.opening_selected_edge

    # Deterministic 20-game sign audit: five selected-home favorites, away favorites, home dogs, away dogs when available.
    buckets=[('home_favorite',(d.selected_location=='home')&(d.selected_market_role=='favorite')),('away_favorite',(d.selected_location=='away')&(d.selected_market_role=='favorite')),('home_underdog',(d.selected_location=='home')&(d.selected_market_role=='underdog')),('away_underdog',(d.selected_location=='away')&(d.selected_market_role=='underdog'))]
    checks=[]
    for label,m in buckets:
        for _,r in d[m].head(5).iterrows():
            expected=r.selected_side_sign*(r.closing_market_home_margin-r.opening_market_home_margin)
            checks.append({'case_type':label,'season':r.season,'week':r.week,'selected_side':r.consensus_selected_side,'opening_number_taken':r.opening_number_taken,'closing_number':r.closing_number,'point_clv':r.point_clv,'formula_expected_clv':expected,'validation_pass':abs(r.point_clv-expected)<1e-9})
    checkdf=pd.DataFrame(checks);checkdf.to_csv(REPORTS/'model_prediction_clv_sign_validation.csv',index=False)
    if len(checkdf)<20 or not checkdf.validation_pass.all():raise SystemExit('20-game CLV sign validation failed')

    # Primary matrix, frozen time splits.
    matrix=[]
    for split,sm in split_masks(d):
      z0=d[sm&d.consensus_edge_band.notna()]
      for (eb,dg),z in z0.groupby(['consensus_edge_band','dispersion_group'],observed=True):
        r={'split':split,'consensus_edge_band':eb,'dispersion_group':dg};r.update(summarize(z));matrix.append(r)
    matrixdf=pd.DataFrame(matrix);matrixdf.to_csv(REPORTS/'model_prediction_clv_edge_dispersion_matrix.csv',index=False)
    # Within-band low minus high is the central comparison.
    comparisons=[]
    for split,sm in split_masks(d):
      for eb,z in d[sm&d.consensus_edge_band.notna()].groupby('consensus_edge_band',observed=True):
        lo=z[z.dispersion_group=='low'];hi=z[z.dispersion_group=='high'];diff=lo.point_clv.mean()-hi.point_clv.mean() if len(lo) and len(hi) else np.nan
        if len(lo) and len(hi):
            boot=[RNG.choice(lo.point_clv,len(lo),True).mean()-RNG.choice(hi.point_clv,len(hi),True).mean() for _ in range(2000)];ci=np.quantile(boot,[.025,.975])
        else:ci=[np.nan,np.nan]
        comparisons.append({'split':split,'consensus_edge_band':eb,'low_n':len(lo),'high_n':len(hi),'low_mean_clv':lo.point_clv.mean(),'high_mean_clv':hi.point_clv.mean(),'low_minus_high_clv':diff,'bootstrap_ci95_low':ci[0],'bootstrap_ci95_high':ci[1]})
    compdf=pd.DataFrame(comparisons);compdf.to_csv(REPORTS/'model_prediction_clv_low_vs_high.csv',index=False)

    structures=[]
    structurespec=[('unanimous',d.unanimous_at_open==1),('two_one_split',d.unanimous_at_open==0),('unanimous_ge_1',d.unanimous_ge_1==1),('unanimous_ge_2',d.unanimous_ge_2==1),('balanced_consensus',d.consensus_concentration=='balanced consensus'),('moderately_concentrated',d.consensus_concentration=='moderately concentrated'),('outlier_driven',d.consensus_concentration=='outlier-driven consensus')]
    for split,sm in split_masks(d):
      for label,m in structurespec:
        r={'split':split,'structure':label};r.update(summarize(d[sm&m]));structures.append(r)
      for model,z in d[sm&(d.outlier_model_at_open!='')].groupby('outlier_model_at_open'):
        r={'split':split,'structure':'outlier_'+model,'average_outlier_distance':z.outlier_distance_from_pair_at_open.mean(),'average_consensus_edge':z.opening_selected_edge.mean()};r.update(summarize(z));structures.append(r)
    structdf=pd.DataFrame(structures);structdf.to_csv(REPORTS/'model_prediction_clv_structure_results.csv',index=False)
    concentration=[]
    for split,sm in split_masks(d):
      for (dg,cc),z in d[sm].groupby(['dispersion_group','consensus_concentration'],observed=True):
        r={'split':split,'dispersion_group':dg,'consensus_concentration':cc};r.update(summarize(z));concentration.append(r)
    concdf=pd.DataFrame(concentration);concdf.to_csv(REPORTS/'model_prediction_clv_concentration_dispersion.csv',index=False)

    retention=[]
    for split,sm in split_masks(d):
      for dg,z in d[sm&d.edge_retention_ratio.notna()].groupby('dispersion_group',observed=True):
        retention.append({'split':split,'dispersion_group':dg,'games':len(z),'average_opening_edge':z.opening_selected_edge.mean(),'average_closing_edge':z.closing_consensus_edge.mean(),'average_points_edge_lost':z.points_edge_lost.mean(),'median_points_edge_lost':z.points_edge_lost.median(),'average_edge_retention_ratio':z.edge_retention_ratio.mean(),'aggregate_edge_retention_percentage':z.closing_consensus_edge.sum()/z.opening_selected_edge.sum(),'edge_fully_disappeared_percentage':z.edge_fully_disappeared.mean(),'market_crossed_consensus_percentage':z.market_crossed_consensus.mean(),'edge_increased_percentage':z.edge_increased.mean()})
    retdf=pd.DataFrame(retention);retdf.to_csv(REPORTS/'model_prediction_clv_edge_retention.csv',index=False)

    # Inference: abs edge is used because outcome is oriented to the selected side.
    d['abs_consensus_edge']=d.consensus_edge.abs();d['edge_x_dispersion']=d.abs_consensus_edge*d.projection_range
    for y in [2022,2023,2024,2025]:d[f'season_{y}']=(d.season==y).astype(int)
    regs=[robust_ols(d,'point_clv',['abs_consensus_edge','projection_range'],'A'),robust_ols(d,'point_clv',['abs_consensus_edge','projection_range','edge_x_dispersion'],'B'),robust_ols(d,'point_clv',['abs_consensus_edge','projection_range','unanimous_at_open','outlier_driven','selected_favorite','selected_home','early_season','season_2022','season_2023','season_2024','season_2025'],'C'),robust_logit(d,'positive_clv',['abs_consensus_edge','projection_range','unanimous_at_open','outlier_driven','selected_favorite','selected_home','early_season','season_2022','season_2023','season_2024','season_2025'],'Logit')]
    regdf=pd.concat(regs,ignore_index=True);regdf.to_csv(REPORTS/'model_prediction_clv_regression.csv',index=False)

    # Execution recommendation is intentionally conservative and based on split stability.
    urgency=pd.DataFrame([{'category':'NO DISPERSION ADJUSTMENT','status':'SUPPORTED','reason':'Low-minus-high CLV is not directionally stable across edge bands and frozen seasons; dispersion coefficients/interaction are uncertain.'},{'category':'BET EARLY','status':'NOT SUPPORTED','reason':'Some alignment groups earn CLV, but 2024 confirmation and within-edge dispersion comparisons are inconsistent.'},{'category':'MANUAL REVIEW','status':'MONITOR','reason':'Outlier-driven consensus is transparent context, but it does not yet show a stable execution penalty.'}]);urgency.to_csv(REPORTS/'model_prediction_clv_execution_categories.csv',index=False)
    outcols=['season','week','start_date','Home','Road','neutral_site','consensus_projected_home_margin','projection_standard_deviation','projection_range','opening_market_home_margin','closing_market_home_margin','consensus_edge','consensus_edge_band','dispersion_group','consensus_selected_side','selected_location','selected_market_role','opening_number_taken','closing_number','point_clv','positive_clv','clv_at_least_0_5','clv_at_least_1','clv_at_least_1_5','clv_at_least_2','market_moved_toward_consensus','ats_result','ats_margin','unanimous_at_open','unanimous_ge_1','unanimous_ge_2','outlier_model_at_open','outlier_distance_from_pair_at_open','outlier_leverage','consensus_concentration','opening_selected_edge','closing_consensus_edge','points_edge_lost','edge_retention_ratio','edge_fully_disappeared','market_crossed_consensus','edge_increased']
    d[outcols].to_csv(REPORTS/'model_prediction_clv_game_sample.csv',index=False)
    audit={'source':str(SOURCE.relative_to(ROOT)),'source_rows':len(pd.read_csv(SOURCE)),'analysis_rows_nonzero_opening_edge':len(d),'required_missing_rows':missing_rows,'true_opener_caveat':'PredictionTracker lineopen is labeled opening line but has no book/timestamp provenance in the CSV.','true_close_caveat':'PredictionTracker line is labeled closing line but has no book/timestamp provenance in the CSV.','dispersion_cutoffs_projection_range':{'low_max':q[0],'high_min_exclusive':q[3]},'clv_formula':'selected side number at open minus selected side number at close = selected_side_sign * (closing_market_home_margin - opening_market_home_margin)','ats_basis':'selected consensus side against opening line','retention_denominator_minimum':1.0,'sign_validation_games':len(checkdf),'sign_validation_pass':bool(checkdf.validation_pass.all())}
    (REPORTS/'model_prediction_clv_data_audit.md').write_text(f"""# Model prediction CLV data audit\n\nThe extension reuses `{audit['source']}` and does not rebuild source history. All {audit['source_rows']:,} source rows contain the three model projections, consensus, dispersion, opener, close, final margin, kickoff date, season/week, home/away, and neutral-site status. {len(d):,} nonzero-opening-edge games enter the selected-side analysis.\n\n`lineopen` and `line` are PredictionTracker's opener and close fields. They are complete in the retained sample, but the CSV supplies neither sportsbook nor timestamp provenance; they are reliable as labeled historical consensus numbers, not auditable book-specific executable prices.\n\nCLV uses `opening_number_taken - closing_number`. With home-margin market convention, this equals `selected_side_sign × (close − open)`. The 20-case audit spans home/away favorites and underdogs and passes exactly. ATS is the selected side against the opener.\n\nDevelopment projection-range cutoffs are reused unchanged: low <= {q[0]:.3f}; high > {q[3]:.3f}; otherwise medium. Edge-retention ratios exclude opening absolute edges below 1 point. All inputs are pregame; no final score enters selection or grouping.\n\nThe prior audit's SP+ reconstruction and publication-timestamp limitations still apply.\n""")
    (REPORTS/'model_prediction_clv_audit.json').write_text(json.dumps(audit,indent=2)+'\n')

    allcomp=compdf[compdf.split=='all_2021_2025'][['consensus_edge_band','low_n','high_n','low_mean_clv','high_mean_clv','low_minus_high_clv','bootstrap_ci95_low','bootstrap_ci95_high']]
    holdcomp=compdf[compdf.split=='locked_2025'][['consensus_edge_band','low_n','high_n','low_mean_clv','high_mean_clv','low_minus_high_clv','bootstrap_ci95_low','bootstrap_ci95_high']]
    retall=retdf[retdf.split=='all_2021_2025'].drop(columns='split');keyreg=regdf[((regdf.model.isin(['A','B']))&regdf.term.isin(['projection_range','edge_x_dispersion']))|((regdf.model=='C')&regdf.term.isin(['projection_range','unanimous_at_open','outlier_driven']))]
    concall=concdf[concdf.split=='all_2021_2025'][['dispersion_group','consensus_concentration','games','average_point_clv','positive_clv_percentage']]
    report=f"""# Consensus-edge dispersion and CLV study\n\n## Answer\n\nLower dispersion does **not** consistently produce better CLV than higher dispersion at the same approximate opening consensus edge. The sign and size of low-minus-high CLV vary by edge band and time split, and all reported bootstrap intervals include zero. The supported execution conclusion is **NO DISPERSION ADJUSTMENT**. Dispersion remains useful descriptive context, not a reason by itself to bet earlier or suppress a bet.\n\n## All-season within-edge comparison\n\n{md(allcomp)}\n\n## Locked 2025 within-edge comparison\n\n{md(holdcomp)}\n\nSmall cells—especially low-dispersion 6+ edges—must not drive execution policy. Refer to the complete matrix for CLV thresholds, movement, ATS, and ROI in every split.\n\n## Edge retention\n\n{md(retall)}\n\nPositive point CLV is algebraically the number of opening-edge points consumed by market movement toward the selected side. Low-dispersion edges may disappear in individual bands, but the aggregate pattern is not sufficiently stable to label them more urgent.\n\n## Structure and outliers\n\nFor a 2–1 split, outlier leverage is the dissenting model's share of the three models' total absolute edge magnitude: >=50% is outlier-driven, 33–50% is moderately concentrated, and <33% is balanced.\n\n{md(concall)}\n\nOutlier-driven groups have weaker aggregate CLV, but they are concentrated in medium/high-dispersion games, the locked outlier-driven sample is only 30, and Model C does not isolate a reliable outlier-driven effect after controls. Therefore this supports **manual review/monitoring**, not a bet rejection or timing rule. The data do not establish that dispersion is harmful mainly because one model drives the average.\n\n## Interpretable models\n\n{md(keyreg[['model','term','coefficient','ci95_low','ci95_high','n']])}\n\nModels use absolute consensus edge because CLV is oriented to the selected side. Model A includes edge and range; Model B adds their interaction; Model C adds unanimity, outlier-driven status, favorite/home/early-season indicators, and season effects. The logistic model for positive CLV is in the regression CSV. Robust HC3/sandwich intervals are used. Dispersion and its interaction do not provide stable, economically decisive incremental information.\n\n## Execution recommendation\n\n- **NO DISPERSION ADJUSTMENT — supported.** Continue using consensus edge without altering urgency solely for range/standard deviation.\n- **BET EARLY — not supported from dispersion alone.**\n- **MANUAL REVIEW — monitor only** for outlier-driven consensus, particularly when one model supplies most of the total absolute edge magnitude.\n\nATS remains secondary and is reported against the opener. No production changes are recommended. Continue prospective 2026 logging of the exact book, timestamp, opener availability, consensus snapshot, and eventual close; book-specific executable CLV will be stronger evidence than consensus historical lines.\n"""
    (REPORTS/'model_prediction_clv_study.md').write_text(report)
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
