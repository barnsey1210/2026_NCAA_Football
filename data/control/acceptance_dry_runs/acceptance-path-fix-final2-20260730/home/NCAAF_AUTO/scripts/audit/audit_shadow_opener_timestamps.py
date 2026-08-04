#!/usr/bin/env python3
"""Audit book and timestamp provenance for the locked 2025 Shadow opener study.

This reads the completed study artifacts only. It does not fit, select, or
recalculate a model. The source CFBD records have opening values but no line
timestamps, so timing-dependent fields intentionally remain unknown.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
STUDY=ROOT/'data/research/shadow_opener_incorporation'
GAME_AUDIT=STUDY/'game_level_audit.csv'
CORE=ROOT/'data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv'
RAW=ROOT/'cfbd_cache/coach_full_game_fav_dog/lines_2025_regular.json'
ET=ZoneInfo('America/New_York')

FIELDS=['season','week','game_id','away_team','home_team','kickoff_timestamp','spread_opener',
 'spread_opener_sportsbook','spread_opener_timestamp_utc','spread_opener_timestamp_eastern',
 'spread_opener_weekday','spread_opener_local_time','total_opener','total_opener_sportsbook',
 'total_opener_timestamp_utc','total_opener_timestamp_eastern','total_opener_weekday',
 'total_opener_local_time','spread_total_same_sportsbook','spread_total_same_timestamp','source_file',
 'spread_source_column_or_json_path','total_source_column_or_json_path','spread_opener_definition',
 'total_opener_definition','timestamp_certainty','missing_reason','preceding_saturday_date',
 'spread_hours_after_saturday_noon_et','spread_hours_after_saturday_7pm_et',
 'spread_hours_after_saturday_1159pm_et','spread_first_recorded_bucket',
 'total_hours_after_saturday_noon_et','total_hours_after_saturday_7pm_et',
 'total_hours_after_saturday_1159pm_et','total_first_recorded_bucket']

def nid(v):
 s=str(v).strip(); return s[:-2] if s.endswith('.0') else s

def book_group(v):
 s=str(v or '').lower().replace(' ','')
 if 'draftking' in s: return 'DraftKings'
 if 'fanduel' in s: return 'FanDuel'
 if 'circa' in s: return 'Circa'
 if 'betmgm' in s or s=='mgm': return 'BetMGM'
 if 'caesar' in s or 'williamhill' in s: return 'Caesars'
 if not s or s in ('nan','consensus','unknown'): return 'consensus or unknown'
 return 'other sportsbooks'

def previous_saturday(kickoff):
 if pd.isna(kickoff): return None
 dt=pd.Timestamp(kickoff).tz_convert(ET)
 days=(dt.weekday()-5)%7
 if days==0: days=7
 return (dt-timedelta(days=days)).date()

def timing_fields(ts, sat):
 # The raw CFBD record has no observation/posting timestamp.
 if not ts or sat is None: return [None,None,None,'unknown']
 x=pd.Timestamp(ts).tz_convert(ET); base=pd.Timestamp(datetime.combine(sat,datetime.min.time()),tz=ET)
 return [(x-(base+pd.Timedelta(hours=12))).total_seconds()/3600,
         (x-(base+pd.Timedelta(hours=19))).total_seconds()/3600,
         (x-(base+pd.Timedelta(hours=23,minutes=59))).total_seconds()/3600,
         time_bucket(x)]

def time_bucket(x):
 wd=x.weekday(); h=x.hour+x.minute/60
 if wd==5:
  if h<19: return 'Saturday afternoon'
  if h<22: return 'Saturday evening before 10 PM ET'
  return 'Saturday late night at or after 10 PM ET'
 if wd==6:
  if h<8: return 'Sunday before 8 AM ET'
  if h<12: return 'Sunday 8 AM–12 PM ET'
  if h<18: return 'Sunday afternoon'
  return 'Sunday evening'
 if wd>=0: return 'Monday or later'
 return 'unknown'

def pct(n,d): return float(n/d) if d else None

def market_summary(df,market):
 op=f'{market}_opener'; ts=f'{market}_opener_timestamp_utc'; book=f'{market}_opener_sportsbook'; bucket=f'{market}_first_recorded_bucket'
 z=df[df[op].notna()].copy(); valid=z[ts].notna(); valid_n=int(valid.sum()); groups=z[book].map(book_group).value_counts().to_dict(); raw_groups=z[book].value_counts().to_dict()
 sat=z[bucket].astype(str).str.startswith('Saturday')
 sat_night=z[bucket].isin(['Saturday evening before 10 PM ET','Saturday late night at or after 10 PM ET'])
 sun_am=z[bucket].isin(['Sunday before 8 AM ET','Sunday 8 AM–12 PM ET'])
 sun_pm=z[bucket].isin(['Sunday afternoon','Sunday evening'])
 mon=z[bucket].eq('Monday or later')
 return {'total_games':len(z),'games_with_valid_timestamp':valid_n,
  'median_first_recorded_time_et':None,'earliest_recorded_opener':None,'latest_recorded_opener':None,
  'percentage_recorded_saturday':pct(int(sat.sum()),len(z)),
  'percentage_recorded_saturday_night':pct(int(sat_night.sum()),len(z)),
  'percentage_recorded_sunday_morning':pct(int(sun_am.sum()),len(z)),
  'percentage_recorded_sunday_afternoon_evening':pct(int(sun_pm.sum()),len(z)),
  'percentage_recorded_monday_or_later':pct(int(mon.sum()),len(z)),
  'sportsbook_counts':groups,'raw_sportsbook_counts':raw_groups,'percentage_from_draftkings':pct(groups.get('DraftKings',0),len(z)),
  'percentage_from_fanduel':pct(groups.get('FanDuel',0),len(z)),
  'percentage_from_dk_or_fanduel':pct(groups.get('DraftKings',0)+groups.get('FanDuel',0),len(z)),
  'percentage_consensus_derived':0.0,
  'percentage_with_unknown_book':pct(groups.get('consensus or unknown',0),len(z)),
  'percentage_with_unknown_timestamp':pct(len(z)-valid_n,len(z))}

def timing_metrics(study,market):
 z=study[(study.season.eq(2025))&study.market.eq(market)].copy()
 op=f'{market}_opener'; close=f'{market}_close'; move=z[close]-z[op]
 signal=z.predicted_residual_move
 projected=z[op]+signal
 clv=np.sign(signal)*move
 return {'timing_bucket':'timestamp unknown','sample_size':len(z),
  'opener_to_close_mae':float(move.abs().mean()),'average_absolute_movement':float(move.abs().mean()),
  'percentage_moving_at_least_0_5':float(move.abs().ge(.5).mean()),
  'percentage_moving_at_least_1_0':float(move.abs().ge(1).mean()),
  'percentage_moving_at_least_2_0':float(move.abs().ge(2).mean()),
  'team_rating_model_positive_clv_rate':float(clv.gt(0).mean()),
  'team_rating_model_average_clv':float(clv.mean()),
  'projected_close_mae':float((projected-z[close]).abs().mean()),
  'model_definition':'completed-study predicted_residual_move; projected close = opener + predicted residual move'}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',default=str(STUDY)); args=ap.parse_args(); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
 study=pd.read_csv(GAME_AUDIT); study['game_id']=study.game_id.map(nid); held=study[study.season.eq(2025)]
 spread=set(held.loc[held.market.eq('spread'),'game_id']); total=set(held.loc[held.market.eq('total'),'game_id']); sample=spread|total
 core=pd.read_csv(CORE,low_memory=False); core['game_id']=core.game_id.map(nid); core=core[(core.season.eq(2025))&core.game_id.isin(sample)].drop_duplicates('game_id').set_index('game_id')
 raw=json.loads(RAW.read_text()); raw_by={nid(x['id']):x for x in raw}
 rows=[]; source_mismatches=[]
 for gid in sorted(sample,key=int):
  c=core.loc[gid]; event=raw_by.get(gid,{}); provider=str(c.provider)
  candidates=[x for x in event.get('lines',[]) if str(x.get('provider'))==provider]
  line=candidates[0] if candidates else {}
  so=float(c.opening_home_spread) if gid in spread and pd.notna(c.opening_home_spread) else np.nan
  to=float(c.opening_total) if gid in total and pd.notna(c.opening_total) else np.nan
  if pd.notna(so) and line.get('spreadOpen')!=so: source_mismatches.append({'game_id':gid,'market':'spread','core':so,'raw':line.get('spreadOpen')})
  if pd.notna(to) and line.get('overUnderOpen')!=to: source_mismatches.append({'game_id':gid,'market':'total','core':to,'raw':line.get('overUnderOpen')})
  kickoff=pd.to_datetime(c.start_date,utc=True,errors='coerce'); sat=previous_saturday(kickoff)
  sf=timing_fields(None,sat); tf=timing_fields(None,sat)
  missing='CFBD event/provider line contains no opening observation or sportsbook posting timestamp; actual public posting time cannot be established'
  src=str(RAW.relative_to(ROOT)); base=f"$[id={gid}].lines[provider={provider!r}]"
  rows.append(dict(zip(FIELDS,[2025,int(c.week),gid,c.away_team,c.home_team,kickoff.isoformat() if pd.notna(kickoff) else '',so,
   provider if pd.notna(so) else '',None,None,None,None,to,provider if pd.notna(to) else '',None,None,None,None,
   bool(provider==provider) if pd.notna(so) and pd.notna(to) else None,None,src,
   f'{base}.spreadOpen -> full_game_modeling_rows.opening_home_spread' if pd.notna(so) else '',
   f'{base}.overUnderOpen -> full_game_modeling_rows.opening_total' if pd.notna(to) else '',
   'book-specific CFBD retained opening field; not earliest-across-books and not consensus-derived' if pd.notna(so) else '',
   'book-specific CFBD retained opening field; not earliest-across-books and not consensus-derived' if pd.notna(to) else '',
   'unknown: no timestamp field',missing,sat.isoformat() if sat else '',*sf,*tf])))
 audit=pd.DataFrame(rows,columns=FIELDS); audit.to_csv(out/'opener_timestamp_audit.csv',index=False)
 summary={'schema_version':'shadow-opener-timestamp-audit-v1','generated_at':datetime.now(timezone.utc).isoformat(),
  'scope':{'spread_game_ids':len(spread),'total_game_ids':len(total),'union_game_ids':len(sample),
   'source_study':str(GAME_AUDIT.relative_to(ROOT)),'model_selection_rerun':False},
  'provenance':{'original_source_file':str(RAW.relative_to(ROOT)),
   'intermediate_source_file':str(CORE.relative_to(ROOT)),
   'selection_logic':'build_pbp_market_modeling_dataset.py selects one event provider row with both closing spread and total, ordered by fixed provider priority: consensus, ESPN Bet, DraftKings, Draft Kings, William Hill (New Jersey), Bovada, teamrankings, Caesars Sportsbook (Colorado), Caesars (Pennsylvania).',
   'opening_fields':'spreadOpen and overUnderOpen on that selected provider row',
   'source_is_sgo':False,'source_is_cfbd':True,'book_specific':True,'earliest_across_books':False,'consensus_derived':False,
   'timestamp_field_available':False,'first_record_retained_by_sgo':'not used by this study',
   'first_observation_in_local_collection':'not retained per event; cache file mtime is not a line observation timestamp',
   'sportsbook_actual_initial_posting_time':'not available',
   'warning':'CFBD opening fields identify a provider-specific retained opener value, but do not prove when that book first posted it or when CFBD first observed it.'},
  'spreads':market_summary(audit,'spread'),'totals':market_summary(audit,'total'),
  'timing_bucket_comparison':{'spread':[timing_metrics(study,'spread')],'total':[timing_metrics(study,'total')],
   'empty_buckets':['Saturday recorded','Sunday before noon ET','Sunday after noon ET','Monday or later']},
  'source_value_mismatches':source_mismatches,
  'central_answer':'No. The prior study cannot be characterized as using Saturday-night DraftKings/FanDuel low-limit lines. Its 2025 sample uses provider-specific CFBD retained opener fields, overwhelmingly ESPN Bet, with no timestamps. It also is not a later-Sunday consensus dataset: consensus was not selected. Timing relative to early movement is unobservable from the retained source.',
  'limitations':['No line-level UTC timestamps','No book posting timestamps','No historical observation sequence','No first-across-books calculation','No consensus methodology','No SGO records used','Local cache modification time postdates the season and is not evidence of market timing']}
 (out/'opener_timestamp_summary.json').write_text(json.dumps(summary,indent=2)+"\n")
 print(json.dumps({'spread_games':len(spread),'total_games':len(total),'union_games':len(sample),'spread_books':summary['spreads']['sportsbook_counts'],'total_books':summary['totals']['sportsbook_counts'],'valid_timestamps':0,'source_value_mismatches':len(source_mismatches),'model_selection_rerun':False},indent=2))
if __name__=='__main__': main()
