#!/usr/bin/env python3
"""Offline extension of frozen historical models across owned market checkpoints."""
from pathlib import Path
import csv,json,math,re,unicodedata
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'research/historical/the_odds_api/odds_snapshots_openers_2021_2025'
SRC=ROOT/'data/research/historical/timestamped_spread_edge_study_2021_2025_v2/timestamped_spread_bets_key_aware_ev.csv'
MAT=ROOT/'data/research/historical/historical_game_model_market_matrix_2021_2025.csv'
OUT=ROOT/'data/research/historical/comprehensive_market_timing_2021_2025'
TH=[.5,1,1.5,2,2.5,3,3.5,4,4.5,5,6,7,8,10]
ORDER=['SAT_11PM_ET','SUN_9AM_ET','SUN_12PM_ET','SUN_2PM_ET','SUN_4PM_ET','SUN_9PM_ET','MON_9AM_ET','MON_3PM_ET','TUE_2PM_ET','WED_2PM_ET','THU_2PM_ET','FRI_2PM_ET','CLOSE']
MODELS=['SP+','FPI','TeamRankings','Sagarin','DRatings','Five-source equal weight','SP+ + FPI + TR + DRatings']
BOOK_ORDER={b:i for i,b in enumerate(['draftkings','fanduel','betmgm','williamhill_us','pinnacle'])}

def basic_norm(value):
 s=unicodedata.normalize('NFKD',str(value or '').replace('’',"'").replace('`',"'"))
 s=''.join(c for c in s if not unicodedata.combining(c)).replace("'",'').lower()
 return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',s)).strip()

def team_resolver(canonical_names):
 aliases={}
 p=ROOT/'data/reference/historical_team_name_aliases.csv'
 if p.exists():
  for r in csv.DictReader(p.open()):aliases[basic_norm(r['alias'])]=basic_norm(r['canonical'])
 universe={aliases.get(basic_norm(x),basic_norm(x)) for x in canonical_names if str(x).strip()}
 def resolve(raw):
  value=basic_norm(raw)
  if value in aliases:return aliases[value]
  if value in universe:return value
  candidates=[]
  for team in universe:
   if value.startswith(team+' '):candidates.append((len(team),team))
  for alias,team in aliases.items():
   if value.startswith(alias+' '):candidates.append((len(alias),team))
  return max(candidates)[1] if candidates else value
 return resolve

def profit_at_price(result,price):
 if result<0:return -1.0
 if result==0:return 0.0
 if pd.isna(price):price=-110.0
 return 100.0/abs(price) if price<0 else price/100.0

def raw_states():
 rows=[]
 for p in RAW.glob('*.json'):
  try:s=json.loads(p.read_text()); cp=s.get('checkpoint'); data=s.get('payload',{}).get('data',[])
  except:continue
  if cp not in ORDER or not data:continue
  for g in data:
   eid=g.get('id'); home=g.get('home_team'); away=g.get('away_team')
   for b in g.get('bookmakers',[]):
    for m in b.get('markets',[]):
     if m.get('key')!='spreads':continue
     for o in m.get('outcomes',[]):
      rows.append({'theodds_event_id':eid,'checkpoint':cp,'requested_timestamp':s.get('requested_timestamp'),'provider_timestamp':s.get('returned_timestamp') or s.get('payload',{}).get('timestamp'),'commence_time':g.get('commence_time'),'provider_home_team':home,'provider_away_team':away,'outcome_team':o.get('name'),'bookmaker':b.get('key'),'provider_side':'home' if o.get('name')==home else 'away','line':o.get('point'),'price':o.get('price'),'raw_file':str(p.relative_to(ROOT))})
 return pd.DataFrame(rows)

def base_models():
 d=pd.read_csv(SRC);d=d[d.model.isin(MODELS)].copy()
 cols=['season','week','game_id','theodds_event_id','start_date','away_team','home_team','model','model_home_margin','model_home_spread','actual_home_margin','closing_home_spread','closing_provider']
 return d[cols].drop_duplicates(['game_id','model'])

def build_game_level():
 q=raw_states(); b=base_models(); out=[]
 q['line']=pd.to_numeric(q.line,errors='coerce');q['price']=pd.to_numeric(q.price,errors='coerce');q=q.dropna(subset=['line'])
 resolve=team_resolver(pd.concat([b.away_team,b.home_team]).dropna().unique())
 ident=b[['theodds_event_id','away_team','home_team']].drop_duplicates('theodds_event_id').copy()
 ident['canonical_away_key']=ident.away_team.map(resolve);ident['canonical_home_key']=ident.home_team.map(resolve)
 q=q.merge(ident,on='theodds_event_id',how='inner')
 q['provider_away_key']=q.provider_away_team.map(resolve);q['provider_home_key']=q.provider_home_team.map(resolve);q['outcome_key']=q.outcome_team.map(resolve)
 same=q.provider_home_key.eq(q.canonical_home_key)&q.provider_away_key.eq(q.canonical_away_key)
 reversed_=q.provider_home_key.eq(q.canonical_away_key)&q.provider_away_key.eq(q.canonical_home_key)
 q['orientation_status']=np.select([same,reversed_],['DIRECT','REVERSED'],default='UNRESOLVED')
 q['side']=np.where(q.outcome_key.eq(q.canonical_home_key),'home',np.where(q.outcome_key.eq(q.canonical_away_key),'away','unresolved'))
 q['reason_code']=np.where(q.orientation_status.eq('UNRESOLVED'),'EVENT_TEAM_ORIENTATION_UNRESOLVED',np.where(q.side.eq('unresolved'),'OUTCOME_TEAM_UNRESOLVED','VALID'))
 quarantine=q[q.reason_code.ne('VALID')].copy()
 valid=q[q.reason_code.eq('VALID')].copy()
 raw_pair=valid.pivot_table(index=['theodds_event_id','checkpoint','bookmaker'],columns='side',values='line',aggfunc='first').reset_index()
 raw_pair['opposite_delta']=(raw_pair.get('home')+raw_pair.get('away')).abs()
 bad_pairs=raw_pair[raw_pair.opposite_delta.gt(1e-9)].copy();bad_pairs['reason_code']='BOOK_SPREADS_NOT_EXACT_OPPOSITES'
 valid=valid.merge(bad_pairs[['theodds_event_id','checkpoint','bookmaker','reason_code']],on=['theodds_event_id','checkpoint','bookmaker'],how='left',suffixes=('','_pair'))
 valid=valid[valid.reason_code_pair.isna()].copy()
 q=valid
 keys=['theodds_event_id','checkpoint']; cons=q[q.side.eq('home')].groupby(keys).line.median().rename('consensus_home_spread').reset_index()
 q['book_order']=q.bookmaker.map(BOOK_ORDER).fillna(9999)
 best=q.sort_values(keys+['side','line','price','book_order','bookmaker'],ascending=[True,True,True,False,False,True,True],kind='mergesort').drop_duplicates(keys+['side'])
 market_states=best[['theodds_event_id','checkpoint','side','line','price','bookmaker','requested_timestamp','provider_timestamp','raw_file','orientation_status']].merge(ident,on='theodds_event_id',how='left')
 audit_cols=['theodds_event_id','checkpoint','bookmaker','provider_home_team','provider_away_team','outcome_team','line','price','raw_file','orientation_status','reason_code']
 quarantined=[]
 if len(quarantine):quarantined.append(quarantine[audit_cols])
 if len(bad_pairs):
  bp=bad_pairs.merge(valid.drop_duplicates(['theodds_event_id','checkpoint','bookmaker'])[['theodds_event_id','checkpoint','bookmaker','provider_home_team','provider_away_team','raw_file','orientation_status']],on=['theodds_event_id','checkpoint','bookmaker'],how='left');bp['outcome_team']='';bp['line']=np.nan;bp['price']=np.nan;quarantined.append(bp[audit_cols])
 qa=pd.concat(quarantined,ignore_index=True) if quarantined else pd.DataFrame(columns=audit_cols)
 qa.to_csv(OUT/'spread_market_quarantine.csv',index=False)
 wide=best.pivot(index=keys,columns='side',values=['line','price','bookmaker','requested_timestamp','provider_timestamp','raw_file']).reset_index();wide.columns=['_'.join([str(x) for x in c if x]) for c in wide.columns]
 wide=wide.merge(cons,on=keys);x=b.merge(wide,on='theodds_event_id')
 x['home_edge']=x.model_home_margin+x.line_home;x['away_edge']=-x.model_home_margin+x.line_away
 x['selected_side']=np.where(x.home_edge>=x.away_edge,'home','away')
 for col in ['line','price','bookmaker','requested_timestamp','provider_timestamp','raw_file']:x['bet_'+col if col in ['line','price','bookmaker'] else col]=np.where(x.selected_side.eq('home'),x[f'{col}_home'],x[f'{col}_away'])
 x=x.rename(columns={'bet_bookmaker':'bet_book'});x['bet_price']=pd.to_numeric(x.bet_price,errors='coerce').fillna(-110);x['bet_line']=pd.to_numeric(x.bet_line)
 x['model_side_spread']=np.where(x.selected_side.eq('home'),-x.model_home_margin,x.model_home_margin);x['edge_points']=pd.to_numeric(pd.Series(np.where(x.selected_side.eq('home'),x.home_edge,x.away_edge),index=x.index),errors='coerce').round(10)
 score=np.where(x.selected_side.eq('home'),x.actual_home_margin+x.bet_line,-x.actual_home_margin+x.bet_line);x['result']=np.sign(score);x['profit_units']=np.where(x.result.eq(1),np.where(x.bet_price<0,100/x.bet_price.abs(),x.bet_price/100),np.where(x.result.eq(-1),-1,0))
 x['closing_side_spread']=np.where(x.selected_side.eq('home'),x.closing_home_spread,-x.closing_home_spread);x['closing_clv_points']=x.bet_line-x.closing_side_spread;x['sample_status']=np.where(x.checkpoint.isin(['SAT_11PM_ET','SUN_9AM_ET','SUN_2PM_ET','SUN_9PM_ET']),'ESTABLISHED_EXISTING_STUDY','RETROSPECTIVE_TIMING_UNVERIFIED')
 keep=['season','week','game_id','theodds_event_id','start_date','away_team','home_team','model','model_home_margin','actual_home_margin','checkpoint','requested_timestamp','provider_timestamp','selected_side','bet_line','bet_price','bet_book','consensus_home_spread','model_side_spread','edge_points','result','profit_units','closing_side_spread','closing_clv_points','raw_file','sample_status'];out=x[keep].to_dict('records')
 # The original established study is frozen evidence, but some event rows used
 # provider home/away as canonical home/away. Rebuild its market states from
 # the preserved actionable book rows and orient them by team identity.
 action=pd.read_csv(ROOT/'data/research/historical/the_odds_api/historical_actionable_market_states_2021_2025.csv',low_memory=False)
 action=action[action.market_state_slot.isin(['SAT_11PM_ET','SUN_9AM_ET','SUN_2PM_ET','SUN_9PM_ET'])].merge(ident,on='theodds_event_id',how='inner')
 action['provider_home_key']=action.home_team_x.map(resolve);action['provider_away_key']=action.away_team_x.map(resolve)
 direct=action.provider_home_key.eq(action.canonical_home_key)&action.provider_away_key.eq(action.canonical_away_key)
 rev=action.provider_home_key.eq(action.canonical_away_key)&action.provider_away_key.eq(action.canonical_home_key)
 action=action[direct|rev].copy();action['orientation_status']=np.where(direct[direct|rev],'DIRECT','REVERSED')
 for stem in ['spread','spread_price','spread_book']:
  hp='best_us_home_'+stem;ap='best_us_away_'+stem
  action['canonical_home_'+stem]=np.where(action.orientation_status.eq('DIRECT'),action[hp],action[ap])
  action['canonical_away_'+stem]=np.where(action.orientation_status.eq('DIRECT'),action[ap],action[hp])
 action=action.rename(columns={'market_state_slot':'checkpoint'})
 action_atomic=[]
 for side in ['home','away']:
  for r in action.to_dict('records'):
   action_atomic.append({'theodds_event_id':r['theodds_event_id'],'checkpoint':r['checkpoint'],'side':side,'line':r[f'canonical_{side}_spread'],'price':r[f'canonical_{side}_spread_price'],'bookmaker':r[f'canonical_{side}_spread_book'],'requested_timestamp':'','provider_timestamp':'','raw_file':'data/research/historical/the_odds_api/historical_actionable_market_states_2021_2025.csv','orientation_status':r['orientation_status'],'away_team':r['away_team_y'],'home_team':r['home_team_y']})
 market_states=pd.concat([market_states,pd.DataFrame(action_atomic)],ignore_index=True).drop_duplicates(['theodds_event_id','checkpoint','side'],keep='last')
 market_states.to_csv(OUT/'atomic_spread_market_states.csv',index=False)
 eb=b.merge(action,on='theodds_event_id',suffixes=('','_provider'))
 eb['canonical_home_spread']=pd.to_numeric(eb.canonical_home_spread,errors='coerce');eb['canonical_away_spread']=pd.to_numeric(eb.canonical_away_spread,errors='coerce')
 eb['home_edge']=eb.model_home_margin+eb.canonical_home_spread;eb['away_edge']=-eb.model_home_margin+eb.canonical_away_spread
 eb['selected_side']=np.where(eb.home_edge>=eb.away_edge,'home','away')
 eb['bet_line']=np.where(eb.selected_side.eq('home'),eb.canonical_home_spread,eb.canonical_away_spread)
 eb['bet_price']=pd.to_numeric(pd.Series(np.where(eb.selected_side.eq('home'),eb.canonical_home_spread_price,eb.canonical_away_spread_price),index=eb.index),errors='coerce').fillna(-110)
 eb['bet_book']=np.where(eb.selected_side.eq('home'),eb.canonical_home_spread_book,eb.canonical_away_spread_book)
 eb['consensus_home_spread']=eb.canonical_home_spread;eb['model_side_spread']=np.where(eb.selected_side.eq('home'),-eb.model_home_margin,eb.model_home_margin);eb['edge_points']=pd.to_numeric(pd.Series(np.where(eb.selected_side.eq('home'),eb.home_edge,eb.away_edge),index=eb.index),errors='coerce').round(10)
 score=np.where(eb.selected_side.eq('home'),eb.actual_home_margin+eb.bet_line,-eb.actual_home_margin+eb.bet_line);eb['result']=np.sign(score);eb['profit_units']=[profit_at_price(r,p) for r,p in zip(eb.result,eb.bet_price)]
 eb['closing_side_spread']=np.where(eb.selected_side.eq('home'),eb.closing_home_spread,-eb.closing_home_spread);eb['closing_clv_points']=eb.bet_line-eb.closing_side_spread
 eb['requested_timestamp']='';eb['provider_timestamp']='';eb['raw_file']='data/research/historical/the_odds_api/historical_actionable_market_states_2021_2025.csv';eb['sample_status']='ESTABLISHED_EXISTING_STUDY'
 out.extend(eb[keep].to_dict('records'))
 # Materialize the canonical closing spread as a reference checkpoint. This is
 # not a new provider observation: it comes from the frozen canonical matrix,
 # and therefore has zero CLV by definition.
 close=b.dropna(subset=['closing_home_spread']).copy();close['checkpoint']='CLOSE'
 close['home_edge']=close.model_home_margin+close.closing_home_spread;close['away_edge']=-close.model_home_margin-close.closing_home_spread
 close['selected_side']=np.where(close.home_edge>=close.away_edge,'home','away')
 close['bet_line']=np.where(close.selected_side.eq('home'),close.closing_home_spread,-close.closing_home_spread);close['bet_price']=-110.0;close['bet_book']=close.closing_provider
 close['consensus_home_spread']=close.closing_home_spread;close['model_side_spread']=np.where(close.selected_side.eq('home'),-close.model_home_margin,close.model_home_margin)
 close['edge_points']=pd.to_numeric(pd.Series(np.where(close.selected_side.eq('home'),close.home_edge,close.away_edge),index=close.index),errors='coerce').round(10)
 score=np.where(close.selected_side.eq('home'),close.actual_home_margin+close.bet_line,-close.actual_home_margin+close.bet_line);close['result']=np.sign(score);close['profit_units']=[profit_at_price(r,p) for r,p in zip(close.result,close.bet_price)]
 close['closing_side_spread']=close.bet_line;close['closing_clv_points']=0.0;close['requested_timestamp']='';close['provider_timestamp']='';close['raw_file']='data/research/historical/historical_game_model_market_matrix_2021_2025.csv';close['sample_status']='CANONICAL_REFERENCE_CLOSE'
 out.extend(close[keep].to_dict('records'))
 close_atomic=[]
 for r in b.drop_duplicates('theodds_event_id').dropna(subset=['closing_home_spread']).to_dict('records'):
  for side,line in [('home',r['closing_home_spread']),('away',-r['closing_home_spread'])]:close_atomic.append({'theodds_event_id':r['theodds_event_id'],'checkpoint':'CLOSE','side':side,'line':line,'price':-110.0,'bookmaker':r['closing_provider'],'requested_timestamp':'','provider_timestamp':'','raw_file':'data/research/historical/historical_game_model_market_matrix_2021_2025.csv','orientation_status':'CANONICAL','away_team':r['away_team'],'home_team':r['home_team']})
 market_states=pd.concat([market_states,pd.DataFrame(close_atomic)],ignore_index=True).drop_duplicates(['theodds_event_id','checkpoint','side'],keep='last')
 market_states.to_csv(OUT/'atomic_spread_market_states.csv',index=False)
 d=pd.DataFrame(out).drop_duplicates(['game_id','model','checkpoint'],keep='last');d['checkpoint_order']=d.checkpoint.map({x:i for i,x in enumerate(ORDER)})
 d=d[d.edge_points.gt(1e-12)].copy();d['profit_units']=[profit_at_price(r,p) for r,p in zip(d.result,d.bet_price)]
 return d

def summary(z):
 w=(z.result==1).sum();l=(z.result==-1).sum();p=(z.result==0).sum();dec=w+l;clv=z.closing_clv_points.dropna();moved=clv[clv.abs()>1e-12]
 return {'games':len(z),'record':f'{w}-{l}-{p}','wins':w,'losses':l,'pushes':p,'ats_pct':w/dec if dec else np.nan,'roi':z.profit_units.sum()/len(z) if len(z) else np.nan,'beat_closing_line_pct':(clv>0).mean() if len(clv) else np.nan,'won_line_move_pct':(moved>0).mean() if len(moved) else np.nan,'avg_clv':clv.mean(),'median_clv':clv.median(),'positive_clv_pct':(clv>0).mean() if len(clv) else np.nan,'clv_implied_ev':np.nan,'avg_edge':z.edge_points.mean(),'median_edge':z.edge_points.median()}

def main():
 OUT.mkdir(parents=True,exist_ok=True);g=build_game_level();g.to_csv(OUT/'game_level_spread.csv',index=False)
 g[g.model.isin(['Five-source equal weight','SP+ + FPI + TR + DRatings'])].head(2000).to_csv(OUT/'game_level_spread_workbook_excerpt.csv',index=False)
 rows=[]
 for (model,cp),z in g.groupby(['model','checkpoint']):
  for t in TH:
   x=z[z.edge_points>=t];rows.append({'model':model,'checkpoint':cp,'threshold':t,'season_scope':'POOLED','week_scope':'ALL',**summary(x)})
   for y in sorted(z.season.unique()):rows.append({'model':model,'checkpoint':cp,'threshold':t,'season_scope':str(int(y)),'week_scope':'ALL',**summary(x[x.season==y])})
   for name,mask in [('W0',x.week==0),('W1',x.week==1),('W0-1',x.week<=1),('W0-2',x.week<=2),('W0-4',x.week<=4),('W5+',x.week>=5)]:rows.append({'model':model,'checkpoint':cp,'threshold':t,'season_scope':'POOLED','week_scope':name,**summary(x[mask])})
 s=pd.DataFrame(rows);s.to_csv(OUT/'spread_threshold_checkpoint_summary.csv',index=False)
 # Formula direct common-sample deltas.
 a=s[s.model=='Five-source equal weight'];c=s[s.model=='SP+ + FPI + TR + DRatings'];keys=['checkpoint','threshold','season_scope','week_scope'];d=c.merge(a,on=keys,suffixes=('_candidate','_baseline'))
 for col in ['games','ats_pct','roi','beat_closing_line_pct','won_line_move_pct','avg_clv','median_clv','positive_clv_pct','avg_edge','median_edge']:d[col+'_delta']=d[col+'_candidate']-d[col+'_baseline']
 d.to_csv(OUT/'spread_candidate_minus_baseline.csv',index=False)
 # Forward cohort persistence/decay using same qualifying game-side.
 dec=[]
 for (model,origin),z in g.groupby(['model','checkpoint']):
  for t in TH:
   cohort=z[z.edge_points>=t][['game_id','selected_side','edge_points']].rename(columns={'edge_points':'origin_edge'});
   if cohort.empty:continue
   later=g[(g.model==model)&(g.checkpoint_order>ORDER.index(origin))].merge(cohort,on=['game_id','selected_side'])
   for cp,x in later.groupby('checkpoint'):
    dec.append({'model':model,'origin_checkpoint':origin,'later_checkpoint':cp,'threshold':t,'n':len(x),'avg_origin_edge':x.origin_edge.mean(),'avg_later_edge':x.edge_points.mean(),'remaining_edge_pct':x.edge_points.mean()/x.origin_edge.mean() if x.origin_edge.mean() else np.nan,'threshold_persistence_pct':(x.edge_points>=t).mean(),'signal_disappearance_pct':(x.edge_points<t).mean(),'signal_reversal_pct':0.0,'avg_clv':x.closing_clv_points.mean(),'median_clv':x.closing_clv_points.median(),'positive_clv_pct':(x.closing_clv_points>0).mean(),'ats_pct':(x.result==1).sum()/max(1,(x.result!=0).sum()),'roi':x.profit_units.sum()/len(x)})
 pd.DataFrame(dec).to_csv(OUT/'spread_forward_cohort_decay.csv',index=False)
 cov=g.groupby(['checkpoint','season']).game_id.nunique().reset_index(name='games_with_market_and_model');cov.to_csv(OUT/'coverage.csv',index=False)
 print(json.dumps({'game_level_rows':len(g),'summary_rows':len(s),'decay_rows':len(dec),'coverage':cov.to_dict('records')},indent=2))
if __name__=='__main__':main()
