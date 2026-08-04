#!/usr/bin/env python3
"""Flag the largest stale opener versus cross-book opening consensus."""
from pathlib import Path
import json,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];H=ROOT/"data/odds/game_book_line_history.csv";OUT=ROOT/"data/signals/cross_book_opener_signals_2026.csv";AUDIT=ROOT/"data/audit/cross_book_opener_signals_2026.json"
COLS=["game_id","week","date","away_team","home_team","signal_key","signal_label","market","side_team","direction","tier","status","reason","book","opening_line","opening_timestamp","consensus_open","current_line","current_timestamp","deviation_from_consensus","observed_move_toward_consensus","historical_mean_move","historical_holdout_n"]
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True);AUDIT.parent.mkdir(parents=True,exist_ok=True)
 if not H.exists():pd.DataFrame(columns=COLS).to_csv(OUT,index=False);AUDIT.write_text(json.dumps({"status":"waiting_for_book_history","signals":0},indent=2)+"\n");return
 h=pd.read_csv(H,low_memory=False);h["_ts"]=pd.to_datetime(h.snapshot_ts,errors="coerce",utc=True);h=h.sort_values("_ts");first=h.drop_duplicates(["game_key","book","market"],keep="first");last=h.drop_duplicates(["game_key","book","market"],keep="last");rows=[]
 for (key,market),z in first.groupby(["game_key","market"]):
  if z.book.nunique()<3:continue
  median=float(z.line.median());z=z.assign(dev=z.line-median);r=z.loc[z.dev.abs().idxmax()];threshold=1. if market=="spread" else 1.5
  if abs(r.dev)<threshold:continue
  cur=last[(last.game_key==key)&(last.market==market)&(last.book==r.book)];current=float(cur.iloc[-1].line) if len(cur) else float(r.line);direction=np.sign(median-float(r.line));toward=direction*(current-float(r.line));already=toward>=threshold/2;away=r.away_team;home=r.home_team
  if market=="spread":side=home if direction>0 else away;signal="cross_book_spread_outlier";label="Stale opener: spread";hist=1.91;n=436
  else:side="Over" if direction>0 else "Under";signal="cross_book_total_outlier";label="Stale opener: total";hist=1.50;n=73
  rows.append({"game_id":"","week":"","date":r.date,"away_team":away,"home_team":home,"signal_key":signal,"signal_label":label,"market":"Spread" if market=="spread" else "Game Total","side_team":side,"direction":f"Expect {r.book} line toward consensus {median:g}","tier":"confirmed_movement","status":"expected_move_already_started" if already else "active_price_available","reason":f"{r.book} opened {float(r.line):g}, {abs(float(r.dev)):.1f} points from the {int(z.book.nunique())}-book opening median {median:g}.","book":r.book,"opening_line":r.line,"opening_timestamp":r.snapshot_ts,"consensus_open":median,"current_line":current,"current_timestamp":cur.iloc[-1].snapshot_ts if len(cur) else r.snapshot_ts,"deviation_from_consensus":r.dev,"observed_move_toward_consensus":toward,"historical_mean_move":hist,"historical_holdout_n":n})
 out=pd.DataFrame(rows,columns=COLS);out.to_csv(OUT,index=False);audit={"status":"ready","book_history_rows":len(h),"signals":len(out),"active":int((out.status=="active_price_available").sum()) if len(out) else 0};AUDIT.write_text(json.dumps(audit,indent=2)+"\n");print(json.dumps(audit,indent=2))
if __name__=="__main__":main()
