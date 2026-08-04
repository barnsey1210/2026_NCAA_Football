#!/usr/bin/env python3
"""Append granular per-book NCAAF spread/total snapshots for stale-line research."""
from datetime import datetime,timezone
from pathlib import Path
import re,pandas as pd
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/odds/game_book_line_history.csv"
FILES=[ROOT/"data/odds/actionnetwork_ncaaf_game_lines_2026.csv",ROOT/"data/odds/theodds_ncaaf_lines_2026.csv"]
COLS=["snapshot_ts","source","date","away_team","home_team","game_key","book","market","line","price"]
def norm(x):return re.sub(r"[^a-z0-9]+"," ",str(x or "").lower()).strip()
def main():
 now=datetime.now(timezone.utc).isoformat(timespec="seconds");rows=[]
 for path in FILES:
  if not path.exists():continue
  d=pd.read_csv(path,low_memory=False)
  for _,r in d.iterrows():
   market=str(r.get("market") or "").lower();side=norm(r.get("side"));home=norm(r.get("home_team"));line=pd.to_numeric(pd.Series([r.get("point")]),errors="coerce").iloc[0]
   if pd.isna(line):continue
   if market in ("spread","spreads"):
    if side not in ("home",home):continue
    kind="spread"
   elif market in ("total","totals"):
    if side not in ("over",):continue
    kind="total"
   else:continue
   date=str(r.get("date") or str(r.get("commence_time") or "")[:10]);away=str(r.get("away_team") or "");ht=str(r.get("home_team") or "");key=f"{date}|{norm(away)}|{norm(ht)}"
   rows.append({"snapshot_ts":r.get("pulled_at") or now,"source":r.get("source"),"date":date,"away_team":away,"home_team":ht,"game_key":key,"book":r.get("book"),"market":kind,"line":line,"price":r.get("price")})
 new=pd.DataFrame(rows,columns=COLS).drop_duplicates(["game_key","book","market"],keep="last");old=pd.read_csv(OUT) if OUT.exists() else pd.DataFrame(columns=COLS);out=pd.concat([old,new],ignore_index=True).drop_duplicates(["snapshot_ts","game_key","book","market","line","price"],keep="last");OUT.parent.mkdir(parents=True,exist_ok=True);out.to_csv(OUT,index=False);print(f"appended {len(new)} per-book rows; total {len(out)}")
if __name__=="__main__":main()
