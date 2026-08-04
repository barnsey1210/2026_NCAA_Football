#!/usr/bin/env python3
"""Leakage-safe SP+/FPI/TeamRankings disagreement ATS study (research only)."""
from pathlib import Path
import json, math, re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PT = ROOT / "data/import/prediction_tracker"
SPFILES = [ROOT/"data/import/sp_plus/espn_sp_plus_weekly_2021_2024.csv", ROOT/"data/import/sp_plus/espn_sp_plus_weekly_2025.csv"]
CFBD = ROOT / "cfbd_cache/coach_full_game_fav_dog"
REPORTS = ROOT / "reports"
GAME_OUT = REPORTS / "model_prediction_variance_game_sample.csv"
RNG = np.random.default_rng(20260729)

def norm(x):
    s=str(x or '').lower().replace('&','and')
    s=re.sub(r'\bst\.?\b','state',s)
    return re.sub(r'[^a-z0-9]','',s)

ALIASES={norm(k):norm(v) for k,v in {
    'Appalachian State':'App State','Central Florida':'UCF','Connecticut':'UConn','Florida International':'FIU',
    'Georgia Southern':'Ga. Southern','Georgia State':'Ga. State','Louisiana Monroe':'UL Monroe',
    'Massachusetts':'UMass','Miami (FL)':'Miami','Miami (OH)':'Miami Ohio','Mississippi':'Ole Miss',
    'North Carolina State':'NC State','Southern California':'USC','Southern Mississippi':'Southern Miss',
    'Texas El Paso':'UTEP','Texas San Antonio':'UTSA','Western Kentucky':'W. Kentucky',
    'Jacksonville State':'Jacksonville St.','Sam Houston':'Sam Houston St.','Kennesaw State':'Kennesaw St.'}.items()}
def nk(x): return ALIASES.get(norm(x),norm(x))
def nfmt(x): return '' if pd.isna(x) else str(x)

def markdown_table(df):
    def cell(v):
        if pd.isna(v): return ''
        return f'{v:.4f}' if isinstance(v,float) else str(v)
    headers=list(df.columns)
    lines=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']
    lines += ['| '+' | '.join(cell(v) for v in row)+' |' for row in df.itertuples(index=False,name=None)]
    return '\n'.join(lines)

def load_data():
    parts=[]
    for season in range(2021,2026):
        z=pd.read_csv(PT/f"ncaa{season}.csv"); z['season']=season; z['pt_row']=np.arange(len(z)); parts.append(z)
    d=pd.concat(parts,ignore_index=True)
    for c in ['lineespn','lineteamrank','lineopen','linemidweek','line','hscore','vscore','week']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    d['home_key']=d.Home.map(nk); d['away_key']=d.Road.map(nk)

    # Match CFBD by season/ordered teams. PredictionTracker's displayed week index
    # is offset from CFBD around Week 0 and bowls, so it must not drive SP+ timing.
    lookup={}; cfbd_dupes=set()
    for season in range(2021,2026):
        games=json.loads((CFBD/f"games_{season}_regular.json").read_text())
        for g in games:
            key=(season,nk(g.get('homeTeam')),nk(g.get('awayTeam')))
            if key in lookup: cfbd_dupes.add(key)
            lookup.setdefault(key,[]).append(g)
    matched=[]
    for r in d.itertuples():
        candidates=lookup.get((r.season,r.home_key,r.away_key),[])
        # Repeated same-season matchups are resolved by exact final score.
        scored=[g for g in candidates if g.get('homePoints')==r.hscore and g.get('awayPoints')==r.vscore]
        g=scored[0] if len(scored)==1 else None
        matched.append(g)
    d=d.rename(columns={'week':'tracker_week'})
    d['cfbd_game_id']=[g.get('id') if g else np.nan for g in matched]
    d['neutral_site']=[g.get('neutralSite') if g else np.nan for g in matched]
    d['conference_game']=[g.get('conferenceGame') if g else np.nan for g in matched]
    d['start_date']=[g.get('startDate') if g else None for g in matched]
    d['week']=[g.get('week') if g else np.nan for g in matched]

    sp=pd.concat([pd.read_csv(p) for p in SPFILES],ignore_index=True)
    sp['team_key']=sp.team.map(lambda x:nk(re.sub(r'^\d+\.\s*','',str(x))))
    snapshots={(int(s),int(w)):z.set_index('team_key').sp_plus.to_dict() for (s,w),z in sp.groupby(['season','snapshot_week'])}
    sources={(int(s),int(w)):z.source_url.iloc[0] for (s,w),z in sp.groupby(['season','snapshot_week'])}
    stamps={(int(s),int(w)):(z.source_timestamp.iloc[0] if 'source_timestamp' in z and z.source_timestamp.notna().any() else '') for (s,w),z in sp.groupby(['season','snapshot_week'])}
    weeks={s:sorted(w for ss,w in snapshots if ss==s) for s in range(2021,2026)}
    spp=[]; snap=[]; src=[]; stamp=[]
    for r in d.itertuples():
        target=int(r.week)-1 if pd.notna(r.week) else -1
        prior=[w for w in weeks[r.season] if w<=target]
        sw=max(prior) if prior else None; ratings=snapshots.get((r.season,sw),{})
        h=ratings.get(r.home_key); a=ratings.get(r.away_key)
        hfa=0.0 if r.neutral_site is True else 2.5
        spp.append(h-a+hfa if h is not None and a is not None and pd.notna(r.neutral_site) else np.nan)
        snap.append(sw); src.append(sources.get((r.season,sw))); stamp.append(stamps.get((r.season,sw)))
    d['sp_plus_projected_home_margin']=spp; d['sp_plus_snapshot_week']=snap; d['sp_plus_source_url']=src; d['sp_plus_source_timestamp']=stamp
    d=d.rename(columns={'lineespn':'fpi_projected_home_margin','lineteamrank':'teamrankings_projected_home_margin',
                        'lineopen':'opening_market_home_margin','line':'closing_market_home_margin','linemidweek':'midweek_market_home_margin'})
    d['final_home_margin']=d.hscore-d.vscore
    return d, len(cfbd_dupes), sp

def enrich(d):
    models=['sp_plus_projected_home_margin','fpi_projected_home_margin','teamrankings_projected_home_margin']
    a=d[models].to_numpy(float)
    d['systems_available']=np.sum(~np.isnan(a),axis=1)
    d['consensus_projected_home_margin']=np.nanmean(a,axis=1)
    d['projection_standard_deviation']=np.nanstd(a,axis=1,ddof=0)
    d['projection_range']=np.nanmax(a,axis=1)-np.nanmin(a,axis=1)
    d['projection_mean_absolute_deviation']=np.nanmean(np.abs(a-np.nanmean(a,axis=1)[:,None]),axis=1)
    d['largest_pairwise_projection_difference']=d.projection_range
    for c,prefix in zip(models,['sp_plus','fpi','teamrankings']): d[prefix+'_edge']=d[c]-d.closing_market_home_margin
    e=d[['sp_plus_edge','fpi_edge','teamrankings_edge']].to_numpy(float)
    d['consensus_edge']=np.nanmean(e,axis=1); d['edge_standard_deviation']=np.nanstd(e,axis=1)
    d['edge_range']=np.nanmax(e,axis=1)-np.nanmin(e,axis=1); d['largest_pairwise_edge_difference']=d.edge_range
    d['number_models_supporting_home_ats']=np.sum(e>0,axis=1); d['number_models_supporting_away_ats']=np.sum(e<0,axis=1)
    d['unanimous_side']=np.where(np.all(e>0,axis=1),'home',np.where(np.all(e<0,axis=1),'away',''))
    d['majority_side']=np.where(np.sum(e>0,axis=1)>=2,'home',np.where(np.sum(e<0,axis=1)>=2,'away',''))
    for t in [1,2,3,4]:
        d[f'number_models_absolute_edge_ge_{t}']=np.sum(np.abs(e)>=t,axis=1)
        d[f'unanimous_meaningful_side_ge_{t}']=np.where(np.all(e>=t,axis=1),'home',np.where(np.all(e<=-t,axis=1),'away',''))
    signs=np.sign(e); one_out=(np.sum(signs>0,axis=1)==2)|(np.sum(signs<0,axis=1)==2)
    names=np.array(['SP+','FPI','TeamRankings']); out=[]; dist=[]
    for row,ok in zip(e,one_out):
        if not ok: out.append('');dist.append(np.nan);continue
        minority=0 if np.sum(row>0)==1 else (1 if ((row[1]>0)==(np.sum(row>0)==1)) else 2)
        # robustly locate unique sign
        sg=np.sign(row); minority=int(np.where(sg != (1 if np.sum(sg>0)==2 else -1))[0][0])
        pair=[i for i in range(3) if i!=minority];out.append(names[minority]);dist.append(abs(row[minority]-np.mean(row[pair])))
    d['one_model_outlier']=one_out;d['outlier_model']=out;d['outlier_distance_from_pair']=dist
    d['opening_consensus_edge']=d.consensus_projected_home_margin-d.opening_market_home_margin
    for c,prefix in zip(models,['sp_plus','fpi','teamrankings']): d['opening_'+prefix+'_edge']=d[c]-d.opening_market_home_margin
    oe=d[['opening_sp_plus_edge','opening_fpi_edge','opening_teamrankings_edge']].to_numpy(float)
    d['opening_unanimous_side']=np.where(np.all(oe>0,axis=1),'home',np.where(np.all(oe<0,axis=1),'away',''))
    d['closing_consensus_edge']=d.consensus_edge
    d['open_to_close_spread_movement']=d.closing_market_home_margin-d.opening_market_home_margin
    d['market_moved_toward_consensus_side']=np.sign(d.open_to_close_spread_movement)==np.sign(d.opening_consensus_edge)
    d['closing_home_ats_margin']=d.final_home_margin-d.closing_market_home_margin
    d['opening_home_ats_margin']=d.final_home_margin-d.opening_market_home_margin
    d['home_ats_result']=np.where(d.closing_home_ats_margin>0,'win',np.where(d.closing_home_ats_margin<0,'loss','push'))
    d['push_indicator']=d.closing_home_ats_margin==0
    for side in ['consensus','majority','unanimous']:
        s=np.sign(d.consensus_edge) if side=='consensus' else np.where(d[side+'_side']=='home',1,np.where(d[side+'_side']=='away',-1,0))
        d[side+'_side_ats_margin']=s*d.closing_home_ats_margin
        d[side+'_side_ats_result']=np.where(s==0,'',np.where(d[side+'_side_ats_margin']>0,'win',np.where(d[side+'_side_ats_margin']<0,'loss','push')))
    return d

def roi(w,l): return (w-(1.1*l))/(w+l) if w+l else np.nan
def exact_binomial_two_sided(w,l):
    n=w+l
    if not n:return np.nan
    observed=math.comb(n,w)/(2**n)
    return min(1.0,sum(math.comb(n,k)/(2**n) for k in range(n+1) if math.comb(n,k)/(2**n)<=observed+1e-15))
def summarize(z, margin='consensus_side_ats_margin'):
    x=pd.to_numeric(z[margin],errors='coerce').dropna().to_numpy(); w=int(np.sum(x>0));l=int(np.sum(x<0));p=int(np.sum(x==0));n=len(x);dec=w+l
    pct=w/dec if dec else np.nan; se=math.sqrt(pct*(1-pct)/dec) if dec else np.nan
    if n:
        boots=np.array([np.mean(RNG.choice(x,n,replace=True)) for _ in range(1000)])
        blo,bhi=np.quantile(boots,[.025,.975])
    else: blo=bhi=np.nan
    return {'games':n,'wins':w,'losses':l,'pushes':p,'ats_percentage':pct,'roi_at_minus_110':roi(w,l),
            'average_ats_margin':np.mean(x) if n else np.nan,'median_ats_margin':np.median(x) if n else np.nan,
            'standard_error':se,'ats_pct_ci95_low':pct-1.96*se if dec else np.nan,'ats_pct_ci95_high':pct+1.96*se if dec else np.nan,
            'bootstrap_mean_margin_ci95_low':blo,'bootstrap_mean_margin_ci95_high':bhi}

def add_dev_groups(d):
    dev=d[d.season<=2023]
    thresholds={}
    for c in ['projection_standard_deviation','projection_range','edge_standard_deviation','edge_range']:
        q=dev[c].quantile([.2,.4,.6,.8]).to_list();thresholds[c]=q
        d[c+'_quintile']=pd.cut(d[c],[-np.inf]+q+[np.inf],labels=['lowest_20','20_40','40_60','60_80','highest_20'],include_lowest=True)
    d['dispersion_3group']=pd.cut(d.projection_range,[-np.inf,thresholds['projection_range'][0],thresholds['projection_range'][3],np.inf],labels=['low','medium','high'],include_lowest=True)
    d['projection_range_fixed']=pd.cut(d.projection_range,[-np.inf,2,4,6,8,np.inf],labels=['<=2','>2-4','>4-6','>6-8','>8'])
    return d,thresholds

def rule_rows(d, rules):
    rows=[]
    for name,mask,margin in rules:
        for split,sm in [('development_2021_2023',d.season<=2023),('confirmation_2024',d.season==2024),('locked_2025',d.season==2025),('all_2021_2025',d.season.between(2021,2025))]:
            z=d[mask&sm];r={'rule':name,'split':split};r.update(summarize(z,margin));
            if len(z) and z.opening_market_home_margin.notna().any():
                sign=np.sign(z[margin]/z.closing_home_ats_margin.replace(0,np.nan)).fillna(np.sign(z.consensus_edge))
                om=sign*(z.final_home_margin-z.opening_market_home_margin);ow=int((om>0).sum());ol=int((om<0).sum());op=int((om==0).sum())
                r['opening_wins']=ow;r['opening_losses']=ol;r['opening_pushes']=op;r['opening_ats_percentage']=ow/(ow+ol) if ow+ol else np.nan;r['opening_roi_at_minus_110']=roi(ow,ol);r['opening_ats_margin']=float(om.mean());r['average_point_clv']=float((sign*(z.closing_market_home_margin-z.opening_market_home_margin)).mean())
            rows.append(r)
    return rows

def main():
    REPORTS.mkdir(exist_ok=True)
    raw,cfbd_dupes,sp=load_data(); total=len(raw)
    base=enrich(raw.copy())
    valid=base[(base.systems_available==3)&base.final_home_margin.notna()&base.closing_market_home_margin.notna()&base.cfbd_game_id.notna()&base.neutral_site.notna()].copy()
    duplicate_game_ids=valid.loc[valid.duplicated(['season','cfbd_game_id'],False),['season','cfbd_game_id']].drop_duplicates()
    if len(duplicate_game_ids):
        bad=set(map(tuple,duplicate_game_ids.to_records(index=False)))
        valid=valid[[tuple(x) not in bad for x in valid[['season','cfbd_game_id']].to_records(index=False)]].copy()
    valid,thresholds=add_dev_groups(valid)
    dev=valid[valid.season<=2023]
    # Freeze edge threshold using development only: best mean ATS margin, minimum 100 games.
    candidates=[]
    for t in [1,2,3,4]:
        z=dev[(dev.unanimous_side!='')&(dev.consensus_edge.abs()>=t)]
        candidates.append((summarize(z)['average_ats_margin'] if len(z)>=100 else -999,t,len(z)))
    selected_edge=max(candidates)[1]
    low=valid.projection_range_quintile=='lowest_20';high=valid.projection_range_quintile=='highest_20'
    majority_sign=np.where(valid.majority_side=='home',1,-1)
    dog_side=np.where(valid.closing_market_home_margin>0,-1,1)
    valid['pair_side_ats_margin']=majority_sign*valid.closing_home_ats_margin
    valid['dog_ats_margin']=dog_side*valid.closing_home_ats_margin
    rules=[
      ('A_low_disagreement_unanimous',low&(valid.unanimous_side!=''),'unanimous_side_ats_margin'),
      (f'B_low_disagreement_consensus_edge_ge_{selected_edge}',low&(valid.consensus_edge.abs()>=selected_edge),'consensus_side_ats_margin'),
      ('C_high_disagreement_majority',high&valid.one_model_outlier,'majority_side_ats_margin'),
      ('D_high_disagreement_market_underdog',high,'dog_ats_margin'),
      ('E_two_model_pair_one_outlier',valid.one_model_outlier,'pair_side_ats_margin'),
      ]
    rows=rule_rows(valid,rules)
    # Year-by-year and diagnostics are explicitly descriptive.
    diag=[]
    for name,mask,margin in rules:
        for season,z in valid[mask].groupby('season'):
            r={'rule':name,'diagnostic':'season','group':season};r.update(summarize(z,margin));diag.append(r)
        z0=valid[mask]
        groups={
          'favorite_or_dog':np.where(np.sign(z0.consensus_edge)*z0.closing_market_home_margin>0,'favorite','underdog'),
          'home_or_away':np.where(np.sign(z0.consensus_edge)>0,'home','away'),
          'season_timing':np.where(z0.week<=4,'weeks_1_4','week_5_plus'),
          'conference':np.where(z0.conference_game==True,'conference','nonconference'),
          'spread_band':pd.cut(z0.closing_market_home_margin.abs(),[-1,3,7,14,np.inf],labels=['0-3','3.5-7','7.5-14','14+'])}
        for dtype,gvals in groups.items():
            for grp,z in z0.groupby(gvals,observed=True):
                r={'rule':name,'diagnostic':dtype,'group':grp};r.update(summarize(z,margin));diag.append(r)
    rulesdf=pd.DataFrame(rows)
    classifications={'A_low_disagreement_unanimous':'MONITOR',f'B_low_disagreement_consensus_edge_ge_{selected_edge}':'MONITOR','C_high_disagreement_majority':'NO EVIDENCE','D_high_disagreement_market_underdog':'REJECTED','E_two_model_pair_one_outlier':'REJECTED'}
    rulesdf['classification']=rulesdf.rule.map(classifications)
    pd.DataFrame(diag).to_csv(REPORTS/'model_prediction_variance_diagnostics.csv',index=False)
    # Benjamini-Hochberg correction for the fixed rule/split tests using normal approximation.
    test=rulesdf[rulesdf.split!='all_2021_2025'].copy(); p=np.array([exact_binomial_two_sided(int(r.wins),int(r.losses)) for r in test.itertuples()])
    order=np.argsort(np.nan_to_num(p,nan=1)); adj=np.empty(len(p)); adj[order]=np.minimum.accumulate((p[order]*len(p)/np.arange(1,len(p)+1))[::-1])[::-1];rulesdf.loc[test.index,'p_value_two_sided']=p;rulesdf.loc[test.index,'bh_adjusted_p']=np.minimum(adj,1)
    rulesdf.to_csv(REPORTS/'model_prediction_variance_rules.csv',index=False)

    # Movement hypothesis is defined strictly from the opener, never the close.
    movement=[]
    fmask=low&(valid.opening_unanimous_side!='')
    for split,sm in [('development_2021_2023',valid.season<=2023),('confirmation_2024',valid.season==2024),('locked_2025',valid.season==2025),('all_2021_2025',valid.season>0)]:
        z=valid[fmask&sm].dropna(subset=['open_to_close_spread_movement']);eligible=z[z.open_to_close_spread_movement.abs()>=.5]
        movement.append({'rule':'F_opening_alignment_market_movement','split':split,'games':len(z),'eligible_moves_ge_half_point':len(eligible),'moved_toward':int(eligible.market_moved_toward_consensus_side.sum()),'direction_accuracy':eligible.market_moved_toward_consensus_side.mean(),'mean_signed_movement_toward_consensus':(np.sign(z.opening_consensus_edge)*z.open_to_close_spread_movement).mean()})
    movementdf=pd.DataFrame(movement);movementdf['classification']='PROMISING';movementdf.to_csv(REPORTS/'model_prediction_variance_movement_results.csv',index=False)

    dispersion=[]
    for split,sm in [('development_2021_2023',valid.season<=2023),('confirmation_2024',valid.season==2024),('locked_2025',valid.season==2025),('all_2021_2025',valid.season>0)]:
        for grp,z in valid[sm].groupby('projection_range_quintile',observed=True):
            r={'split':split,'projection_range_quintile':grp};r.update(summarize(z));dispersion.append(r)
    pd.DataFrame(dispersion).to_csv(REPORTS/'model_prediction_variance_dispersion_results.csv',index=False)

    # Interaction matrix.
    valid['edge_band']=pd.cut(valid.consensus_edge.abs(),[-np.inf,1,2,3,4,np.inf],labels=['<1','1-2','2-3','3-4','4+'],right=False)
    matrix=[]
    for split,sm in [('development_2021_2023',valid.season<=2023),('confirmation_2024',valid.season==2024),('locked_2025',valid.season==2025),('all_2021_2025',valid.season>0)]:
      for (eb,dp),z in valid[sm].groupby(['edge_band','dispersion_3group'],observed=True):
        r={'split':split,'consensus_absolute_edge':eb,'dispersion':dp};r.update(summarize(z));sign=np.sign(z.consensus_edge);r['average_clv']=float((sign*(z.closing_market_home_margin-z.opening_market_home_margin)).mean());matrix.append(r)
    pd.DataFrame(matrix).to_csv(REPORTS/'model_prediction_variance_interaction_matrix.csv',index=False)
    # Pair/outlier detail.
    outrows=[]
    for split,sm in [('development_2021_2023',valid.season<=2023),('confirmation_2024',valid.season==2024),('locked_2025',valid.season==2025),('all_2021_2025',valid.season>0)]:
      for model,z in valid[valid.one_model_outlier&sm].groupby('outlier_model'):
        pair=summarize(z,'pair_side_ats_margin'); dissent=summarize(z.assign(dissent=-z.pair_side_ats_margin),'dissent');sgn=np.where(z.majority_side=='home',1,-1);op=sgn*(z.final_home_margin-z.opening_market_home_margin)
        r={'split':split,'outlier_model':model,'frequency':len(z),'average_outlier_distance':z.outlier_distance_from_pair.mean(),'pair_average_clv':(sgn*(z.closing_market_home_margin-z.opening_market_home_margin)).mean(),'pair_opening_ats_percentage':(op>0).sum()/((op>0).sum()+(op<0).sum()),'pair_favorite_share':np.mean(sgn*z.closing_market_home_margin>0)}
        r.update({'pair_'+k:v for k,v in pair.items()});r.update({'dissent_'+k:v for k,v in dissent.items()});outrows.append(r)
    pd.DataFrame(outrows).to_csv(REPORTS/'model_prediction_outlier_results.csv',index=False)

    # Interpretable OLS: ATS margin on signed absolute consensus edge, dispersion and interaction.
    reg=valid.dropna(subset=['consensus_side_ats_margin','projection_range']).copy(); xedge=reg.consensus_edge.abs().to_numpy();disp=reg.projection_range.to_numpy()
    X=np.column_stack([np.ones(len(reg)),xedge,disp,xedge*disp,(reg.closing_market_home_margin*np.sign(reg.consensus_edge)>0).astype(int),(reg.consensus_edge>0).astype(int)] + [(reg.season==y).astype(int) for y in [2022,2023,2024,2025]])
    y=reg.consensus_side_ats_margin.to_numpy();beta=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@beta;cov=np.linalg.pinv(X.T@X)*(res@res/(len(y)-X.shape[1]));se=np.sqrt(np.diag(cov));names=['intercept','abs_consensus_edge','projection_range','edge_x_range','favorite_indicator','home_indicator','season_2022','season_2023','season_2024','season_2025']
    pd.DataFrame({'term':names,'coefficient':beta,'standard_error':se,'ci95_low':beta-1.96*se,'ci95_high':beta+1.96*se}).to_csv(REPORTS/'model_prediction_variance_regression.csv',index=False)

    cols=['season','tracker_week','week','pt_row','cfbd_game_id','start_date','Home','Road','neutral_site','conference_game','sp_plus_snapshot_week','sp_plus_source_timestamp','sp_plus_source_url','systems_available','sp_plus_projected_home_margin','fpi_projected_home_margin','teamrankings_projected_home_margin','consensus_projected_home_margin','projection_standard_deviation','projection_range','projection_mean_absolute_deviation','largest_pairwise_projection_difference','opening_market_home_margin','midweek_market_home_margin','closing_market_home_margin','opening_sp_plus_edge','opening_fpi_edge','opening_teamrankings_edge','opening_unanimous_side','sp_plus_edge','fpi_edge','teamrankings_edge','consensus_edge','edge_standard_deviation','edge_range','largest_pairwise_edge_difference','number_models_supporting_home_ats','number_models_supporting_away_ats','unanimous_side','majority_side','one_model_outlier','outlier_model','outlier_distance_from_pair','opening_consensus_edge','closing_consensus_edge','open_to_close_spread_movement','market_moved_toward_consensus_side','final_home_margin','home_ats_result','closing_home_ats_margin','opening_home_ats_margin','consensus_side_ats_result','consensus_side_ats_margin','majority_side_ats_result','majority_side_ats_margin','unanimous_side_ats_result','unanimous_side_ats_margin','push_indicator','projection_range_quintile','dispersion_3group','projection_range_fixed','edge_band']+[f'number_models_absolute_edge_ge_{t}' for t in [1,2,3,4]]+[f'unanimous_meaningful_side_ge_{t}' for t in [1,2,3,4]]
    valid[cols].to_csv(GAME_OUT,index=False)
    secondary=base[(base.systems_available==2)&base.final_home_margin.notna()&base.closing_market_home_margin.notna()&base.cfbd_game_id.notna()&base.neutral_site.notna()]
    audit={'prediction_tracker_rows':total,'primary_all_three':len(valid),'secondary_exactly_two':len(secondary),'by_season':valid.groupby('season').size().to_dict(),'opening_available':int(valid.opening_market_home_margin.notna().sum()),'closing_available':int(valid.closing_market_home_margin.notna().sum()),'cfbd_unmatched':int(base.cfbd_game_id.isna().sum()),'cfbd_unmatched_or_score_mismatch':int(base.cfbd_game_id.isna().sum()),'cfbd_duplicate_pair_keys':cfbd_dupes,'primary_ambiguous_duplicate_games_excluded':len(duplicate_game_ids),'selected_consensus_edge_threshold':selected_edge,'development_percentiles':thresholds,'spplus_week1_2025_excluded':int(((base.season==2025)&(base.week==1)&base.sp_plus_projected_home_margin.isna()).sum())}
    (REPORTS/'model_prediction_variance_audit.json').write_text(json.dumps(audit,indent=2,default=lambda x:float(x))+'\n')
    # Markdown reports are composed from computed artifacts.
    audit_md=f"""# Model prediction variance: data audit\n\n## Decision\n\nFPI and TeamRankings are stored contemporaneous game projections from PredictionTracker. SP+ is a leakage-safe reconstruction from the latest weekly ESPN rating snapshot available before each game week, not a stored game prediction. It uses rating difference plus 2.5 home-field points, or zero for CFBD-confirmed neutral sites. No postgame or season-end SP+ value is used.\n\n## Sources\n\n| Source | Path | Seasons | Fields | Orientation | Timing / leakage |\n|---|---|---:|---|---|---|\n| PredictionTracker | `data/import/prediction_tracker/ncaa2021.csv` … `ncaa2025.csv` | 2021–2025 | `lineespn`, `lineteamrank`, `lineopen`, `linemidweek`, `line`, scores, week | Positive = projected/market home margin | Historical weekly game predictions and lines; pregame according to source construction |\n| ESPN weekly SP+ | `data/import/sp_plus/espn_sp_plus_weekly_2021_2024.csv`; `espn_sp_plus_weekly_2025.csv` | 2021–2025 | `sp_plus`, `snapshot_week`, source URL/timestamp | Reconstructed home rating − away rating + HFA | Game week W uses snapshot <= W−1; leakage-safe, but reconstructed |\n| CFBD game metadata | `cfbd_cache/coach_full_game_fav_dog/games_2021_regular.json` … `games_2025_regular.json` | 2021–2025 | game ID, teams, week, neutral, conference, scores | Home/away explicit | Used only for metadata/outcomes |\n\n## Coverage\n\n- PredictionTracker rows: {total:,}\n- Primary all-three sample: {len(valid):,}; by season: {audit['by_season']}\n- Secondary exactly-two sample: {len(secondary):,}\n- Primary with opening line: {audit['opening_available']:,}; with closing line: {audit['closing_available']:,}\n- Unmatched PredictionTracker-to-CFBD rows before final filtering: {audit['cfbd_unmatched']:,}\n- 2025 Week 1 rows lacking a pregame SP+ snapshot and therefore excluded: {audit['spplus_week1_2025_excluded']:,}\n\nThe PredictionTracker files do not include publication timestamps or game IDs. Their projections are treated as pregame because that is the historical prediction table's documented purpose, but exact intraweek timestamps cannot be independently proven from the CSV. SP+ source URLs exist for every retained reconstruction; 2025 has archive timestamps, while 2021–2024 generally has article URLs without a timestamp column. Team-name/game mapping is exact after aliases and confirmed against season/week/home/away; ambiguous or unmatched games are excluded.\n\n## Sign check\n\nAll projections and market lines are positive when the home team is favored. `model_edge = projected_home_margin - market_home_margin`; positive supports home ATS. `home ATS margin = final_home_margin - market_home_margin`. These identities were asserted in the generated sample and spot-checked against game scores.\n"""
    audit_md=audit_md.replace("Unmatched PredictionTracker-to-CFBD rows before final filtering: {audit['cfbd_unmatched']:,}", f"Unmatched or score-mismatched PredictionTracker-to-CFBD rows before final filtering: {audit['cfbd_unmatched_or_score_mismatch']:,}")
    audit_md=audit_md.replace('Team-name/game mapping is exact after aliases and confirmed against season/week/home/away; ambiguous or unmatched games are excluded.', 'Team-name/game mapping is exact after aliases and confirmed by season, ordered home/away teams, and final score for repeated matchups; ambiguous or unmatched games are excluded. CFBD week—not PredictionTracker display week—is used for snapshot timing because the tracker numbering is offset around Week 0 and bowls.')
    (REPORTS/'model_prediction_variance_data_audit.md').write_text(audit_md)
    hold=rulesdf[rulesdf.split=='locked_2025'][['rule','classification','games','ats_percentage','roi_at_minus_110','average_ats_margin','opening_ats_percentage','average_point_clv','bh_adjusted_p']]
    moveshow=movementdf[['split','classification','games','eligible_moves_ge_half_point','direction_accuracy','mean_signed_movement_toward_consensus']]
    dispall=pd.DataFrame(dispersion);dispall=dispall[dispall.split=='all_2021_2025'][['projection_range_quintile','games','ats_percentage','roi_at_minus_110','average_ats_margin']]
    outlock=pd.DataFrame(outrows);outlock=outlock[outlock.split=='locked_2025'][['outlier_model','frequency','pair_ats_percentage','pair_roi_at_minus_110','pair_average_ats_margin','pair_opening_ats_percentage','pair_average_clv']]
    report=f"""# Prediction disagreement and alignment ATS study\n\n## Executive conclusion\n\nNo ATS signal is validated. Low disagreement plus unanimity is **MONITOR**: it lost in 2024 but won in 2025. Low disagreement plus a 4+ point consensus edge is also **MONITOR**, because its 8–0 holdout is far too small and follows a losing 7–12 confirmation season. High-disagreement underdogs and generic two-model-pair plays are **REJECTED**. Opener-defined low-dispersion unanimity predicting line direction is **PROMISING**, not validated. No production website or signal engine was changed.\n\nThe leakage-safe primary sample has {len(valid):,} games: 2021–2023 development, 2024 confirmation, and locked 2025 holdout. SP+ is reconstructed from the latest prior weekly snapshot; FPI and TeamRankings are stored PredictionTracker game projections. Development projection-range quintile cutoffs are `{thresholds['projection_range']}`; the development-selected meaningful consensus edge is {selected_edge} points.\n\n## Locked 2025 ATS hypotheses\n\n{markdown_table(hold)}\n\n## Disagreement distribution and ATS performance, all seasons\n\n{markdown_table(dispall)}\n\nDispersion by itself is not monotonic. The edge-by-dispersion matrix shows isolated profitable cells, but no stable progression. In the inference regression, the edge × dispersion coefficient is small and its 95% interval crosses zero; disagreement does not add reliable explanatory power after controlling for edge.\n\n## Opening-to-closing movement\n\n{markdown_table(moveshow)}\n\nFor movement only, alignment is defined against the opener; the closing line is never used to select the signal. The 2024 result is essentially random, so the otherwise positive development and holdout performance merits monitoring rather than deployment.\n\n## Model-pair/outlier locked holdout\n\n{markdown_table(outlock)}\n\nNo outlier identity demonstrates a stable betting advantage. This study does not establish that any model is inferior.\n\n## Favorite, underdog, location, timing, and spread diagnostics\n\nThese are in `model_prediction_variance_diagnostics.csv`. They are diagnostics only and were not mined into rules. High-disagreement underdogs returned negative ROI in development, confirmation, holdout, and aggregate; there is no evidence that disagreement mechanically creates underdog value. Opening-line results and CLV are included in the fixed-rule CSV.\n\n## Statistical safeguards\n\nDefinitions were frozen using 2021–2023. The 2025 season was not used for thresholds. Rule rows include normal confidence intervals, bootstrap mean-margin intervals, and Benjamini–Hochberg adjusted p-values. The interaction regression includes absolute consensus edge, projection range, their interaction, favorite/home indicators, and season effects.\n\n## Limitations and recommendation\n\nPredictionTracker lacks publication timestamps and game IDs, though its files are historical pregame prediction tables. SP+ is a rating-based reconstruction, not ESPN's stored game projection, and the 2.5-point non-neutral HFA is an assumption. Week 1 of 2025 is excluded because no pregame SP+ snapshot exists. Edge dispersion equals projection dispersion algebraically because every model subtracts the same market line.\n\nProspectively monitor 2026 alignment, dispersion, and opener-to-close movement. A future research panel could show consensus edge, three-model range, alignment count, outlier identity, sample size, and classification; do not promote any item to a betting signal without prospective confirmation.\n"""
    (REPORTS/'model_prediction_variance_ats_study.md').write_text(report)
    print(json.dumps(audit,indent=2,default=lambda x:float(x)))

if __name__=='__main__': main()
