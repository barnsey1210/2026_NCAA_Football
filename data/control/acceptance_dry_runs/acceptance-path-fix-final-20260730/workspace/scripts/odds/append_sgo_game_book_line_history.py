#!/usr/bin/env python3
"""Append canonical eligible SGO quote rows; never parse raw SGO responses."""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_INPUT=ROOT/"data/markets/sgo/sgo_accepted_quotes.csv"
DEFAULT_OUT=ROOT/"data/odds/game_book_line_history.csv"
COLS=["snapshot_ts","source","date","away_team","home_team","game_key","canonical_game_id","book","market","side","line","price","source_updated_at","ingestion_timestamp","paired_market_id","neutral_site","available","state_id"]

def state_id(row):
 fields=("canonical_game_id","book","market","side","line","price","source_updated_at","available")
 raw="|".join(str(row.get(x,"")) for x in fields)
 return hashlib.sha256(raw.encode()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument("--accepted-quotes",type=Path,default=DEFAULT_INPUT);p.add_argument("--output",type=Path,default=DEFAULT_OUT);p.add_argument("--allow-blocked-dry-run",action="store_true");a=p.parse_args()
 if not a.accepted_quotes.exists():raise SystemExit(f"Canonical SGO quote artifact missing: {a.accepted_quotes}")
 src=pd.read_csv(a.accepted_quotes,low_memory=False)
 required={"canonical_game_id","sportsbook","market_type","side","market_eligibility","available","suspended","stale_flag","paired_market_id"}
 missing=required-set(src.columns)
 if missing:raise SystemExit(f"Invalid canonical SGO quote schema; missing {sorted(missing)}")
 ok=src[(src.market_eligibility.astype(str).str.lower()=="true")&(src.available.astype(str).str.lower()=="true")&(src.suspended.astype(str).str.lower()!="true")&(src.stale_flag.astype(str).str.lower()!="true")].copy()
 if not a.allow_blocked_dry_run:
  ok=ok[ok.acceptance_eligibility.astype(str).str.lower()=="true"]
 # Every emitted pair must still contain its complete required sides.
 expected={"spread":{"away","home"},"total":{"over","under"},"moneyline":{"away","home"}}
 valid_ids=set()
 for pid,g in ok.groupby("paired_market_id"):
  market=str(g.market_type.iloc[0]);
  if market in expected and set(g.side.astype(str))==expected[market] and g.canonical_game_id.nunique()==1 and g.sportsbook.nunique()==1:valid_ids.add(pid)
 ok=ok[ok.paired_market_id.isin(valid_ids)]
 rows=[]
 for _,r in ok.iterrows():
  row={"snapshot_ts":r.get("source_updated_at") or r.get("ingestion_timestamp"),"source":"SportsGameOdds","date":str(r.get("kickoff") or "")[:10],"away_team":r.get("away_team"),"home_team":r.get("home_team"),"game_key":f"{r.get('canonical_game_id')}","canonical_game_id":r.get("canonical_game_id"),"book":r.get("sportsbook"),"market":r.get("market_type"),"side":r.get("side"),"line":r.get("line"),"price":r.get("price"),"source_updated_at":r.get("source_updated_at"),"ingestion_timestamp":r.get("ingestion_timestamp"),"paired_market_id":r.get("paired_market_id"),"neutral_site":r.get("neutral_site"),"available":True}
  row["state_id"]=state_id(row);rows.append(row)
 new=pd.DataFrame(rows,columns=COLS).drop_duplicates("state_id",keep="last")
 old=pd.read_csv(a.output,low_memory=False) if a.output.exists() else pd.DataFrame(columns=COLS)
 output_cols=list(old.columns)+[c for c in COLS if c not in old.columns]
 for c in output_cols:
  if c not in old:old[c]=""
  if c not in new:new[c]=""
 existing=set(old.state_id.dropna().astype(str));new=new[~new.state_id.astype(str).isin(existing)]
 out=pd.concat([old[output_cols],new[output_cols]],ignore_index=True);a.output.parent.mkdir(parents=True,exist_ok=True);out.to_csv(a.output,index=False)
 print(f"Canonical SGO quote rows appended: {len(new)}; total history rows: {len(out)}")
 return 0
if __name__=="__main__":raise SystemExit(main())
