#!/usr/bin/env python3
"""Offline, bounded early-window Standard model replacement study."""
from pathlib import Path
import itertools,json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'data/research/historical/early_window_standard_replacement_2021_2025';OUT.mkdir(parents=True,exist_ok=True)
SPREAD=ROOT/'data/research/historical/comprehensive_market_timing_2021_2025/game_level_spread.csv'
TOTAL=ROOT/'data/research/historical_totals/alternate_models_2021_2025/alternate_totals_game_level.csv'
TH=[.5,1,1.5,2,2.5,3,3.5,4,4.5,5,6,7,8,9,10];ORDER=['SAT_11PM_ET','SUN_9AM_ET','SUN_12PM_ET','SUN_2PM_ET','SUN_4PM_ET','SUN_9PM_ET','MON_9AM_ET','MON_3PM_ET','TUE_2PM_ET','WED_2PM_ET','THU_2PM_ET','FRI_2PM_ET','CLOSE']
COMP=['SP+','FPI','TeamRankings','DRatings']
def spread_clv(entry_line,closing_line):return entry_line-closing_line
def total_clv(side,entry_line,closing_total):return closing_total-entry_line if side=='OVER' else entry_line-closing_total
def grade_spread(side,actual_home_margin,line):return np.sign(actual_home_margin+line if side=='home' else -actual_home_margin+line)
def grade_total(side,actual_total,line):return np.sign(actual_total-line if side=='OVER' else line-actual_total)
def sample_strength(n):return 'NORMAL' if n>=100 else 'LIMITED' if n>=50 else 'SMALL' if n>=20 else 'VERY_SMALL_INSUFFICIENT'
def metric(z,kind='spread'):
 w=(z.result==1).sum();l=(z.result==-1).sum();p=(z.result==0).sum();clv=z.clv.dropna();m=clv[clv.abs()>1e-12]
 err=z.error.dropna()
 return {'n':len(z),'record':f'{w}-{l}-{p}','wins':w,'losses':l,'pushes':p,'win_pct':w/(w+l) if w+l else np.nan,'roi':z.profit.sum()/len(z) if len(z) else np.nan,'avg_clv':clv.mean(),'median_clv':clv.median(),'positive_clv_pct':(clv>0).mean() if len(clv) else np.nan,'beat_close_pct':(clv>0).mean() if len(clv) else np.nan,'won_line_move_pct':(m>0).mean() if len(m) else np.nan,'clv_implied_ev':np.nan,'mae':err.abs().mean(),'rmse':np.sqrt((err**2).mean()),'bias':err.mean(),'avg_edge':z.edge.mean(),'median_edge':z.edge.median()}
def candidates():
 rows=[]
 for ws in itertools.product(range(15,41,5),repeat=4):
  if sum(ws)==100:
   rows.append({'model_id':'spread_4src_'+('_'.join(map(str,ws)))+'_v1',**{f'w_{c.lower().replace("+", "sp")}':w/100 for c,w in zip(COMP,ws)},'sp_plus_weight':ws[0]/100,'fpi_weight':ws[1]/100,'teamrankings_weight':ws[2]/100,'dratings_weight':ws[3]/100,'family':'CONTROLLED_5PT_ALL_NONZERO','complexity':'simple'})
 return pd.DataFrame(rows).drop(columns=[c for c in ['w_spsp','w_fpi','w_teamrankings','w_dratings'] if c in rows[0]])
def spread_base():
 d=pd.read_csv(SPREAD,low_memory=False);mat=pd.read_csv(ROOT/'data/research/historical/historical_game_model_market_matrix_2021_2025.csv',low_memory=False);p=mat[['game_id','season','week','actual_home_margin','home_team','away_team','start_date','theodds_event_id','sp_plus_pregame_fixed','pt_lineespn','pt_lineteamrank','pt_linedonchess']].rename(columns={'sp_plus_pregame_fixed':'SP+','pt_lineespn':'FPI','pt_lineteamrank':'TeamRankings','pt_linedonchess':'DRatings'}).dropna(subset=COMP)
 q=d.drop_duplicates(['game_id','checkpoint','model']); q=q.groupby(['game_id','checkpoint'],as_index=False).first();q=q[['game_id','checkpoint','consensus_home_spread','closing_side_spread','closing_clv_points','actual_home_margin','sample_status','raw_file']]
 side=pd.read_csv(ROOT/'data/research/historical/comprehensive_market_timing_2021_2025/atomic_spread_market_states.csv').merge(p[['game_id','theodds_event_id']],on='theodds_event_id',how='inner').rename(columns={'side':'selected_side','line':'bet_line','price':'bet_price','bookmaker':'bet_book'})
 close=d.drop_duplicates(['game_id','checkpoint','selected_side'])[['game_id','checkpoint','selected_side','closing_side_spread']]
 side=side.merge(close,on=['game_id','checkpoint','selected_side'],how='left')
 return p,q,side
def make_spread_states(p,q,side,c):
 key={'SP+':'sp_plus_weight','FPI':'fpi_weight','TeamRankings':'teamrankings_weight','DRatings':'dratings_weight'};proj=sum(p[x]*c[key[x]] for x in COMP)
 x=p.assign(projection=proj,model_id=c.model_id).merge(q,on=['game_id','actual_home_margin']);wide=side.pivot(index=['game_id','checkpoint'],columns='selected_side',values='bet_line').reset_index();x=x.merge(wide,on=['game_id','checkpoint']);x['home_edge']=x.projection+x.home;x['away_edge']=-x.projection+x.away;x['selected_side']=np.where(x.home_edge>=x.away_edge,'home','away');x=x.merge(side,on=['game_id','checkpoint','selected_side'],suffixes=('','_side'))
 x['model_side']=np.where(x.selected_side.eq('home'),-x.projection,x.projection);x['edge']=np.round(np.where(x.selected_side.eq('home'),x.home_edge,x.away_edge),10);score=np.where(x.selected_side.eq('home'),x.actual_home_margin+x.bet_line,-x.actual_home_margin+x.bet_line);x['result']=np.sign(score);x['profit']=np.where(x.result.eq(1),np.where(x.bet_price<0,100/x.bet_price.abs(),x.bet_price/100),np.where(x.result.eq(-1),-1,0));x['clv']=x.bet_line-x.closing_side_spread_side;x['error']=x.projection-x.actual_home_margin;x['checkpoint_order']=x.checkpoint.map({v:i for i,v in enumerate(ORDER)});return x[x.edge>1e-12].copy()
def spread_study():
 cand=candidates();p,q,side=spread_base();cand.to_csv(OUT/'spread_weight_candidates.csv',index=False);states=[];wf=[]
 for _,c in cand.iterrows():
  x=make_spread_states(p,q,side,c);states.append(x)
  pred=x.drop_duplicates('game_id')
  for train_end,test in [(2023,2024),(2024,2025)]:
   dev=pred[pred.season<=train_end];t=pred[pred.season==test]
   for edge_threshold in [2,3,4,5]:
    bet=x[(x.season==test)&(x.checkpoint=='SUN_9AM_ET')&(x.edge>=edge_threshold)];wf.append({'model_id':c.model_id,'develop_seasons':f'2021-{train_end}','test_season':test,'checkpoint':'SUN_9AM_ET','edge_threshold':edge_threshold,**{f'dev_{k}':v for k,v in metric(dev).items() if k in ['n','mae','rmse','bias']},**{f'test_{k}':v for k,v in metric(t).items() if k in ['n','mae','rmse','bias']},**{f'test_bet_{k}':v for k,v in metric(bet).items() if k in ['n','record','win_pct','roi','avg_clv','median_clv','positive_clv_pct','beat_close_pct','won_line_move_pct']}})
 allx=pd.concat(states,ignore_index=True);pd.DataFrame(wf).to_csv(OUT/'spread_walk_forward_results.csv',index=False)
 # Prediction-first leader: lowest mean OOS MAE, with equal weight retained unless improvement >=0.05 points.
 w=pd.DataFrame(wf);rank=w.groupby('model_id').test_mae.mean().sort_values();eq='spread_4src_25_25_25_25_v1';best=rank.index[0];chosen=best if rank[eq]-rank[best]>=.05 else eq
 leaders=list(dict.fromkeys([eq,chosen]));z=allx[allx.model_id.isin(leaders)].copy();z.to_csv(OUT/'spread_candidate_game_states.csv',index=False)
 rows=[]
 for (m,cp),a in z.groupby(['model_id','checkpoint']):
  for t in TH:rows.append({'model_id':m,'checkpoint':cp,'threshold':t,'sample_classification':a.sample_status.mode().iloc[0],**metric(a[a.edge>=t])})
 pd.DataFrame(rows).to_csv(OUT/'spread_threshold_results.csv',index=False);pd.DataFrame(rows).to_csv(OUT/'spread_checkpoint_results.csv',index=False)
 # First market-qualifying state; classification remains descriptive unless source timing is proven.
 fa=[]
 for (m,g),a in z.sort_values('checkpoint_order').groupby(['model_id','game_id']):
  for t in TH:
   b=a[a.edge>=t]
   if len(b):r=b.iloc[0].to_dict();r['threshold']=t;r['beat_close']=r['clv']>0;r['won_line_move']=r['clv']>0;fa.append(r)
 f=pd.DataFrame(fa);f.to_csv(OUT/'spread_first_actionable_game_level.csv',index=False)
 sums=[]
 for keys,a in f.groupby(['model_id','threshold','checkpoint']):sums.append({'model_id':keys[0],'threshold':keys[1],'checkpoint':keys[2],**metric(a)})
 pd.DataFrame(sums).to_csv(OUT/'spread_first_actionable_results.csv',index=False)
 season=[];week=[]
 for (m,t,y),a in f.groupby(['model_id','threshold','season']):season.append({'model_id':m,'threshold':t,'season':y,**metric(a)})
 for m in leaders:
  a=f[f.model_id==m]
  for t in TH:
   b=a[a.threshold==t]
   for scope,mask in [('W0',b.week==0),('W1',b.week==1),('W2',b.week==2),('W0-2',b.week<=2),('W0-4',b.week<=4),('W5+',b.week>=5)]:week.append({'model_id':m,'threshold':t,'week_scope':scope,**metric(b[mask])})
 pd.DataFrame(season).to_csv(OUT/'spread_season_results.csv',index=False);pd.DataFrame(week).to_csv(OUT/'spread_week_results.csv',index=False)
 dec=[]
 for (m,g,t),a in f.groupby(['model_id','game_id','threshold']):
  origin=a.sort_values('checkpoint_order').iloc[0];later=z[(z.model_id==m)&(z.game_id==g)&(z.checkpoint_order>origin.checkpoint_order)]
  for _,r in later.iterrows():
   later_line=r.home if origin.selected_side=='home' else r.away;model_side=r.projection if origin.selected_side=='home' else -r.projection;later_edge=model_side+later_line
   dec.append({'model_id':m,'game_id':g,'threshold':t,'origin_checkpoint':origin.checkpoint,'later_checkpoint':r.checkpoint,'origin_side':origin.selected_side,'origin_line':origin.bet_line,'origin_edge':origin.edge,'later_origin_side_line':later_line,'later_edge':later_edge,'mean_edge_remaining':later_edge,'remaining_edge_pct':later_edge/origin.edge if origin.edge else np.nan,'same_side':r.selected_side==origin.selected_side,'threshold_persisted':later_edge>=t,'positive_edge_persisted':later_edge>0,'reversal':later_edge<0,'strengthened':later_edge>origin.edge,'absorbed_pct':1-later_edge/origin.edge if origin.edge else np.nan,'clv':origin.clv,'result':origin.result,'profit':origin.profit})
 dd=pd.DataFrame(dec);dd.to_csv(OUT/'spread_edge_decay.csv',index=False);ds=[]
 for (m,t,origin,later),a in dd.groupby(['model_id','threshold','origin_checkpoint','later_checkpoint']):
  ds.append({'model_id':m,'threshold':t,'origin_checkpoint':origin,'later_checkpoint':later,'n':len(a),'avg_origin_edge':a.origin_edge.mean(),'mean_remaining_edge':a.later_edge.mean(),'remaining_edge_pct':a.remaining_edge_pct.mean(),'edge_persistence_pct':a.threshold_persisted.mean(),'positive_edge_persistence_pct':a.positive_edge_persisted.mean(),'same_side_persistence_pct':a.same_side.mean(),'reversal_pct':a.reversal.mean(),'strengthened_pct':a.strengthened.mean(),'avg_clv':a.clv.mean(),'roi':a.profit.sum()/len(a)})
 pd.DataFrame(ds).to_csv(OUT/'spread_edge_decay_summary.csv',index=False)
 common=[]
 primary=z[z.model_id.eq(eq)];legacy=pd.read_csv(SPREAD,low_memory=False);legacy=legacy[legacy.model.eq('Five-source equal weight')].copy()
 legacy=legacy.rename(columns={'edge_points':'edge','profit_units':'profit','closing_clv_points':'clv','model':'model_id'})
 for cp in ORDER:
  a=primary[primary.checkpoint.eq(cp)];b=legacy[legacy.checkpoint.eq(cp)]
  pair=a.merge(b[['game_id','selected_side','edge','result','profit','clv']],on='game_id',suffixes=('_4src','_5src'))
  for t in TH:
   q4=pair.edge_4src.ge(t);q5=pair.edge_5src.ge(t)
   for cohort,mask in [('FOUR_SOURCE_SELECTED',q4),('FIVE_SOURCE_SELECTED',q5),('BOTH_QUALIFY',q4&q5),('UNION',q4|q5)]:
    x=pair[mask]
    for label,suffix in [('4src','4src'),('5src','5src')]:
     y=x.rename(columns={f'result_{suffix}':'result',f'profit_{suffix}':'profit',f'clv_{suffix}':'clv',f'edge_{suffix}':'edge'})
     common.append({'checkpoint':cp,'threshold':t,'cohort':cohort,'evaluated_model':label,'side_agreement_n':int((x.selected_side_4src==x.selected_side_5src).sum()),'side_disagreement_n':int((x.selected_side_4src!=x.selected_side_5src).sum()),**metric(y)})
 pd.DataFrame(common).to_csv(OUT/'spread_common_sample_comparison.csv',index=False)
 # Shadow agreement uses preserved early Shadow side; no blending.
 sh=pd.read_csv(ROOT/'data/research/historical/shadow/early_vs_updated/early_vs_updated_overlap_states.csv');sh=sh[(sh.market=='SPREAD')&(sh.threshold=='3+')&(sh.early_side!=0)][['game_id','early_side','early_edge','early_grade','early_clv']].drop_duplicates('game_id');std=f[(f.model_id==chosen)&(f.threshold==3)].merge(sh,on='game_id',how='outer',indicator=True);std['agreement_class']=np.where(std._merge=='left_only','STANDARD_ONLY',np.where(std._merge=='right_only','SHADOW_ONLY',np.where(std.selected_side.map({'home':1,'away':-1})==std.early_side,'AGREE_SAME_SIDE','DISAGREE')));std['comparison_result']=np.where(std._merge=='right_only',std.early_grade,std.result);std['comparison_clv']=np.where(std._merge=='right_only',std.early_clv,std.clv);std['comparison_profit']=np.where(std.comparison_result==1,100/110,np.where(std.comparison_result==-1,-1,0));std.to_csv(OUT/'spread_shadow_agreement_game_level.csv',index=False)
 summary=[]
 for cls,a in std.groupby('agreement_class'):
  a=a.assign(result=a.comparison_result,profit=a.comparison_profit,clv=a.comparison_clv,error=np.nan,edge=np.where(a._merge=='right_only',a.early_edge,a.edge))
  summary.append({'agreement_class':cls,**metric(a)})
 pd.DataFrame(summary).to_csv(OUT/'spread_shadow_agreement.csv',index=False)
 return chosen,rank.to_dict()
def total_study():
 d=pd.read_csv(TOTAL);base=d.drop_duplicates(['game_id','checkpoint','model']);weights=[.4,.45,.5,.55,.6];cands=pd.DataFrame([{'model_id':f'total_sp{round(w*100)}_massey{round((1-w)*100)}_v1','sp_plus_weight':w,'massey_weight':1-w} for w in weights]);cands.to_csv(OUT/'total_weight_candidates.csv',index=False);allx=[];wf=[]
 for _,c in cands.iterrows():
  x=base[base.model=='CONTROL_50_SP_50_MASSEY'].copy();x['model_id']=c.model_id;x['model_total']=c.sp_plus_weight*x.sp_plus+c.massey_weight*x.massey_dual;x['side']=np.where(x.model_total>x.best_us_over_total,'OVER','UNDER');x['bet_line']=np.where(x.side.eq('OVER'),x.best_us_over_total,x.best_us_under_total);x['edge']=(x.model_total-x.bet_line).abs();x['result']=np.where((x.actual_total_points-x.bet_line)*np.where(x.side.eq('OVER'),1,-1)>0,1,np.where((x.actual_total_points-x.bet_line)==0,0,-1));x['profit']=np.where(x.result==1,100/110,np.where(x.result==-1,-1,0));x['clv']=np.where(x.side.eq('OVER'),x.closing_total-x.bet_line,x.bet_line-x.closing_total);x['error']=x.model_total-x.actual_total_points;allx.append(x)
  pred=x.drop_duplicates('game_id')
  for train_end,test in [(2023,2024),(2024,2025)]:
   for edge_threshold in [2,3,4,5]:
    bet=x[(x.season==test)&(x.checkpoint=='SUN_9AM_ET')&(x.edge>=edge_threshold)];wf.append({'model_id':c.model_id,'develop_seasons':f'2021-{train_end}','test_season':test,'checkpoint':'SUN_9AM_ET','edge_threshold':edge_threshold,**{f'test_{k}':v for k,v in metric(pred[pred.season==test],'total').items() if k in ['n','mae','rmse','bias']},**{f'test_bet_{k}':v for k,v in metric(bet,'total').items() if k in ['n','record','win_pct','roi','avg_clv','median_clv','positive_clv_pct','beat_close_pct','won_line_move_pct']}})
 z=pd.concat(allx);pd.DataFrame(wf).to_csv(OUT/'total_walk_forward_results.csv',index=False);rank=pd.DataFrame(wf).groupby('model_id').test_mae.mean().sort_values();eq='total_sp50_massey50_v1';best=rank.index[0];chosen=best if rank[eq]-rank[best]>=.05 else eq;z=z[z.model_id.isin([eq,chosen])]
 rows=[]
 for (m,cp),a in z.groupby(['model_id','checkpoint']):
  for t in TH:rows.append({'model_id':m,'checkpoint':cp,'threshold':t,**metric(a[a.edge>=t],'total')})
 rr=pd.DataFrame(rows);rr.to_csv(OUT/'total_threshold_results.csv',index=False);rr.to_csv(OUT/'total_checkpoint_results.csv',index=False)
 fa=[]
 order={'SUN_9AM_ET':0,'SUN_9PM_ET':1,'CLOSE':2};z['ord']=z.checkpoint.map(order)
 for (m,g),a in z.sort_values('ord').groupby(['model_id','game_id']):
  for t in TH:
   b=a[a.edge>=t]
   if len(b):r=b.iloc[0].to_dict();r['threshold']=t;fa.append(r)
 f=pd.DataFrame(fa);pd.DataFrame([{'model_id':m,'threshold':t,'checkpoint':cp,**metric(a,'total')} for (m,t,cp),a in f.groupby(['model_id','threshold','checkpoint'])]).to_csv(OUT/'total_first_actionable_results.csv',index=False)
 pd.DataFrame([{'model_id':m,'threshold':t,'season':y,**metric(a,'total')} for (m,t,y),a in f.groupby(['model_id','threshold','season'])]).to_csv(OUT/'total_season_results.csv',index=False)
 wk=[]
 for (m,t),a in f.groupby(['model_id','threshold']):
  for scope,mask in [('W0-2',a.week<=2),('W0-4',a.week<=4),('W5+',a.week>=5)]:wk.append({'model_id':m,'threshold':t,'week_scope':scope,**metric(a[mask],'total')})
 pd.DataFrame(wk).to_csv(OUT/'total_week_results.csv',index=False);return chosen,rank.to_dict()
if __name__=='__main__':
 s,sr=spread_study();t,tr=total_study();(OUT/'selection_audit.json').write_text(json.dumps({'spread_selected':s,'spread_oos_mae_rank':sr,'total_selected':t,'total_oos_mae_rank':tr,'selection_rule':'lowest mean 2024/2025 OOS MAE only if >=0.05 better than equal weight; otherwise equal weight'},indent=2)+'\n');print(s,t)
