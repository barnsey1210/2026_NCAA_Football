#!/usr/bin/env python3
"""Provider-free integration checks for canonical SGO/history interfaces."""
from __future__ import annotations
import csv, subprocess, tempfile
from pathlib import Path
import pandas as pd
from scripts.odds.append_sgo_game_book_line_history import state_id

ROOT=Path(__file__).resolve().parents[2]
PY=Path(__import__('sys').executable)
def run(cmd,cwd):return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,check=True)
def main():
 # Per-book state identity ignores ingestion time but captures meaningful state.
 base={"canonical_game_id":"g1","book":"draftkings","market":"spread","side":"home","line":-3,"price":-110,"source_updated_at":"2026-07-30T00:00:00Z","available":True}
 same=dict(base,ingestion_timestamp="later");assert state_id(base)==state_id(same)
 for field,value in (("line",-3.5),("price",-115),("book","bovada"),("source_updated_at","2026-07-30T01:00:00Z")):
  assert state_id(base)!=state_id(dict(base,**{field:value}))
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);(t/"data/odds").mkdir(parents=True);(t/"data/markets").mkdir(parents=True)
  # General display history: identical replay zero, price/book/timestamp/line changes append.
  source=t/"data/odds/theodds_season_game_lines_2026.csv"
  row={"game_id":"1","date":"2026-08-29","week":0,"away_team":"A","home_team":"H","market_spread_home":-3,"market_spread_price":-110,"market_spread_book":"DraftKings","market_spread_last_update":"2026-07-30T00:00:00Z","market_total":50,"market_total_over_price":-110,"market_total_under_price":-110,"market_total_book":"DraftKings","market_total_last_update":"2026-07-30T00:00:00Z"}
  pd.DataFrame([row]).to_csv(source,index=False)
  script=ROOT/"scripts/odds/append_game_line_history.py"
  run([str(PY),str(script)],t);n1=len(pd.read_csv(t/"data/odds/game_line_history.csv"));run([str(PY),str(script)],t);assert len(pd.read_csv(t/"data/odds/game_line_history.csv"))==n1
  for field,value in (("market_spread_price",-115),("market_spread_book","Bovada"),("market_spread_last_update","2026-07-30T01:00:00Z"),("market_spread_home",-3.5)):
   row[field]=value;pd.DataFrame([row]).to_csv(source,index=False);run([str(PY),str(script)],t);n=len(pd.read_csv(t/"data/odds/game_line_history.csv"));assert n==n1+1;n1=n
  # Canonical SGO per-book appender: paired rows append once, identical replay zero.
  q=t/"quotes.csv";fields=["canonical_game_id","sportsbook","market_type","side","market_eligibility","acceptance_eligibility","available","suspended","stale_flag","paired_market_id","source_updated_at","ingestion_timestamp","kickoff","away_team","home_team","neutral_site","line","price"]
  rows=[]
  for side,line in (("away",3),("home",-3)):rows.append(dict.fromkeys(fields,"" )|{"canonical_game_id":"g1","sportsbook":"draftkings","market_type":"spread","side":side,"market_eligibility":True,"acceptance_eligibility":True,"available":True,"suspended":False,"stale_flag":False,"paired_market_id":"p1","source_updated_at":"2026-07-30T00:00:00Z","ingestion_timestamp":"x","kickoff":"2026-08-29","away_team":"A","home_team":"H","neutral_site":False,"line":line,"price":-110})
  pd.DataFrame(rows).to_csv(q,index=False);out=t/"data/odds/book.csv";sgo=ROOT/"scripts/odds/append_sgo_game_book_line_history.py"
  run([str(PY),str(sgo),"--accepted-quotes",str(q),"--output",str(out)],t);assert len(pd.read_csv(out))==2;run([str(PY),str(sgo),"--accepted-quotes",str(q),"--output",str(out)],t);assert len(pd.read_csv(out))==2
 # Source-path contract: history cannot parse raw; controller and daily share canonical builder.
 sgo_text=(ROOT/"scripts/odds/append_sgo_game_book_line_history.py").read_text();assert "events_raw.json" not in sgo_text and "--accepted-quotes" in sgo_text
 daily=(ROOT/"daily_market_update.sh").read_text();assert "build_sgo_daily_canonical.py" in daily
 parser=(ROOT/"scripts/markets/parse_sgo_ncaaf_game_odds.py").read_text();assert "sgo_canonical_display_lines.csv" in parser and "events_raw.json" not in parser
 print("Canonical SGO acceptance/history tests: PASSED")
 print("- price/line/book/source-time state, display/per-book idempotence, no raw history ingestion, shared daily path")
if __name__=="__main__":main()
