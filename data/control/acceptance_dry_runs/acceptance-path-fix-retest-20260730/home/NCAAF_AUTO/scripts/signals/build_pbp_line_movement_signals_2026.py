#!/usr/bin/env python3
"""Build frozen 2026 PBP line-movement alerts from rolling features and line history."""
from __future__ import annotations
from pathlib import Path
import json,re
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
HISTORY=ROOT/"data/history/matchup_line_history_clean.csv"
PBP_CANDIDATES=[ROOT/"data/research/pbp_history_2026/rolling_pregame_opponent_adjusted.csv",ROOT/"data/signals/pbp_matchup_features_2026.csv"]
DRIVE_CANDIDATES=[ROOT/"data/research/drive_context_2026/rolling_pregame_drive_context.csv",ROOT/"data/signals/drive_context_features_2026.csv"]
OUT=ROOT/"data/signals/pbp_line_movement_signals_2026.csv"
AUDIT=ROOT/"data/audit/pbp_line_movement_signals_2026.json"
COLUMNS=["game_id","week","date","away_team","home_team","signal_key","signal_label","market","side_team","direction","tier","status","reason","opening_line","opening_timestamp","opening_source","opening_book","current_line","current_timestamp","current_book","observed_move","historical_mean_clv","historical_holdout_n","feature_value_1","feature_value_2","feature_value_3"]

def norm(x):return re.sub(r"[^a-z0-9]+"," ",str(x or "").lower()).strip()
def first_existing(paths):return next((p for p in paths if p.exists() and p.stat().st_size),None)
def num(x):
 try:
  v=float(x);return v if np.isfinite(v) else np.nan
 except:return np.nan
def timestamp(r):return str(r.get("snapshot_ts") or r.get("snapshot_date") or "")

def line_views(h,market):
 col="market_spread_home" if market=="spread" else "market_total";z=h[pd.to_numeric(h[col],errors="coerce").notna()].copy();z["_line"]=pd.to_numeric(z[col],errors="coerce");z["_ts"]=pd.to_datetime(z.get("snapshot_ts").fillna(z.get("snapshot_date")),errors="coerce",utc=True);z=z.sort_values("_ts")
 first=z.drop_duplicates("game_id",keep="first").set_index("game_id");last=z.drop_duplicates("game_id",keep="last").set_index("game_id");return first,last

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True);AUDIT.parent.mkdir(parents=True,exist_ok=True);pbp_path=first_existing(PBP_CANDIDATES);drive_path=first_existing(DRIVE_CANDIDATES)
 audit={"status":"waiting_for_inputs","pbp_file":str(pbp_path or ""),"drive_file":str(drive_path or ""),"active_signals":0}
 if not HISTORY.exists() or pbp_path is None or drive_path is None:
  pd.DataFrame(columns=COLUMNS).to_csv(OUT,index=False);AUDIT.write_text(json.dumps(audit,indent=2)+"\n");print(json.dumps(audit,indent=2));return
 h=pd.read_csv(HISTORY,low_memory=False);h=h[h.game_id.notna()].copy();pbp=pd.read_csv(pbp_path,low_memory=False);drv=pd.read_csv(drive_path,low_memory=False)
 sf,sl=line_views(h,"spread");tf,tl=line_views(h,"total");games=h.sort_values("snapshot_date").drop_duplicates("game_id",keep="last")
 pbp["_key"]=pbp.apply(lambda r:(str(r.get("week")),norm(r.get("team")),norm(r.get("opponent"))),axis=1);drv["_key"]=drv.apply(lambda r:(str(r.get("week")),norm(r.get("team")),norm(r.get("opponent"))),axis=1);pm={k:r for k,r in pbp.set_index("_key").iterrows()};dm={k:r for k,r in drv.set_index("_key").iterrows()};rows=[]
 for _,g in games.iterrows():
  week=str(g.get("week"));away=norm(g.get("away_team"));home=norm(g.get("home_team"));ar=pm.get((week,away,home));hr=pm.get((week,home,away));ad=dm.get((week,away,home));hd=dm.get((week,home,away));gid=g.get("game_id")
  if any(x is None for x in (ar,hr,ad,hd)) or num(g.get("week"))<5:continue
  home_success=num(hr.get("matchup_expected_off_success"));away_success=num(ar.get("matchup_expected_off_success"));success_adv=home_success-away_success;combined_success=home_success+away_success
  pace=-(num(hr.get("matchup_expected_off_pace_seconds"))+num(ar.get("matchup_expected_off_pace_seconds")))/2
  home_fp=-(num(hd.get("pregame_off_avg_start_ytg"))+num(ad.get("pregame_def_opponent_avg_start_ytg")))/2;away_fp=-(num(ad.get("pregame_off_avg_start_ytg"))+num(hd.get("pregame_def_opponent_avg_start_ytg")))/2;combined_fp=home_fp+away_fp
  base={"game_id":gid,"week":g.get("week"),"date":g.get("game_date"),"away_team":g.get("away_team"),"home_team":g.get("home_team")}
  if gid in sf.index:
   o=sf.loc[gid];c=sl.loc[gid];open_line=num(o.get("_line"));current=num(c.get("_line"))
   if success_adv<=-0.0001814671671235002 and open_line<=-3:
    move=open_line-current;status="active_price_available" if move>-.5 else "expected_move_already_started"
    rows.append({**base,"signal_key":"pbp_away_dog_move","signal_label":"PBP opener move: away dog","market":"Spread","side_team":g.get("away_team"),"direction":"Away underdog / expect line toward away","tier":"confirmed_movement","status":status,"reason":f"Home opened {open_line:+.1f} without a positive success-matchup advantage ({success_adv:+.3f}); frozen signal expects movement toward {g.get('away_team')}.","opening_line":open_line,"opening_timestamp":timestamp(o),"opening_source":o.get("source"),"opening_book":o.get("market_spread_book"),"current_line":current,"current_timestamp":timestamp(c),"current_book":c.get("market_spread_book"),"observed_move":-move,"historical_mean_clv":.79,"historical_holdout_n":56,"feature_value_1":success_adv,"feature_value_2":np.nan,"feature_value_3":np.nan})
  if gid in tf.index:
   o=tf.loc[gid];c=tl.loc[gid];open_line=num(o.get("_line"));current=num(c.get("_line"))
   if combined_success<=0.9310875830918766 and combined_fp>-139.80758013111537 and pace<=-26.013869254679115:
    move=current-open_line;status="active_price_available" if move>-.75 else "expected_move_already_started"
    rows.append({**base,"signal_key":"pbp_under_move","signal_label":"PBP opener move: under","market":"Game Total","side_team":"Under","direction":"Under / expect total down","tier":"confirmed_movement","status":status,"reason":f"Low combined success ({combined_success:.3f}) and slow expected pace ({-pace:.1f} sec/play); frozen signal expects the total to fall.","opening_line":open_line,"opening_timestamp":timestamp(o),"opening_source":o.get("source"),"opening_book":o.get("market_total_book"),"current_line":current,"current_timestamp":timestamp(c),"current_book":c.get("market_total_book"),"observed_move":-move,"historical_mean_clv":.85,"historical_holdout_n":46,"feature_value_1":combined_success,"feature_value_2":combined_fp,"feature_value_3":pace})
 out=pd.DataFrame(rows,columns=COLUMNS);out.to_csv(OUT,index=False);audit.update({"status":"ready","games_with_history":int(h.game_id.nunique()),"active_signals":len(out),"spread_signals":int((out.signal_key=="pbp_away_dog_move").sum()) if len(out) else 0,"total_signals":int((out.signal_key=="pbp_under_move").sum()) if len(out) else 0});AUDIT.write_text(json.dumps(audit,indent=2)+"\n");print(json.dumps(audit,indent=2))
if __name__=="__main__":main()
