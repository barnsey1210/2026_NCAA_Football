#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"data/site/current_market_contract.json"
FAST_MATRIX=ROOT/"data/site/war_room_market_matrix.json"
OUT=ROOT/"data/odds/game_book_line_history.csv"

COLS=["snapshot_ts","source","date","away_team","home_team","game_key","book","market","line","price",
"provider_open_line","provider_open_price","provider_close_line","provider_close_price","book_last_updated",
"available","canonical_game_id","side","source_updated_at","ingestion_timestamp","paired_market_id",
"neutral_site","state_id"]

def sid(r):
    keys=("canonical_game_id","book","market","side","line","price","source_updated_at","source","available")
    return hashlib.sha256("|".join(str(r.get(k,"")) for k in keys).encode()).hexdigest()

def fast_matrix_rows():
    """Convert the canonical matched fast matrix into durable quote history."""
    if not FAST_MATRIX.exists():
        return []
    payload=json.loads(FAST_MATRIX.read_text())
    refresh=payload.get("fast_market_refresh") or {}
    pulled_at=refresh.get("last_fast_pull_at") or payload.get("built_at")
    rows=[]
    for game in payload.get("games",[]):
        gid=str(game.get("game_id") or "")
        books=((game.get("market") or {}).get("primary_sportsbooks") or {})
        for book,markets in books.items():
            for market,sides in (markets or {}).items():
                for side,quote in (sides or {}).items():
                    if market not in {"spread","total"} or not isinstance(quote,dict):
                        continue
                    source_updated_at=quote.get("last_update") or pulled_at
                    row={
                        "snapshot_ts":quote.get("pulled_at") or pulled_at,
                        "source":quote.get("source") or refresh.get("source") or "The Odds API",
                        "date":str(game.get("date") or game.get("kickoff_time") or "")[:10],
                        "away_team":game.get("away_team"),"home_team":game.get("home_team"),
                        "game_key":gid,"book":book,"market":market,"line":quote.get("line"),
                        "price":quote.get("price"),"provider_open_line":"","provider_open_price":"",
                        "provider_close_line":"","provider_close_price":"",
                        "book_last_updated":source_updated_at,"available":True,"canonical_game_id":gid,
                        "side":side,"source_updated_at":source_updated_at,
                        "ingestion_timestamp":quote.get("pulled_at") or pulled_at,
                        "paired_market_id":f"{gid}|{book}|{market}|{source_updated_at or pulled_at}",
                        "neutral_site":game.get("neutral_site"),
                    }
                    row["state_id"]=sid(row); rows.append(row)
    return rows

def main():
    d=json.loads(CONTRACT.read_text())
    built=d.get("built_at") or datetime.now(timezone.utc).isoformat()
    rows=[]
    for g in d.get("games",[]):
        gid=str(g.get("game_id") or "")
        for book,markets in (g.get("quotes") or {}).items():
            for market,sides in (markets or {}).items():
                for side,q in (sides or {}).items():
                    if not isinstance(q,dict) or q.get("freshness_status") not in {"LIVE","BACKUP_SOURCE"}:
                        continue
                    r={"snapshot_ts":built,"source":q.get("source"),"date":str(g.get("date") or g.get("commence_time") or "")[:10],
                       "away_team":g.get("away_team"),"home_team":g.get("home_team"),"game_key":gid,"book":book,
                       "market":market,"line":q.get("line"),"price":q.get("price"),"provider_open_line":"",
                       "provider_open_price":"","provider_close_line":"","provider_close_price":"",
                       "book_last_updated":q.get("source_updated_at"),"available":True,"canonical_game_id":gid,
                       "side":side,"source_updated_at":q.get("source_updated_at"),"ingestion_timestamp":built,
                       "paired_market_id":f"{gid}|{book}|{market}|{q.get('source_updated_at') or built}",
                       "neutral_site":g.get("neutral_site")}
                    r["state_id"]=sid(r); rows.append(r)
    fast_rows=fast_matrix_rows()
    rows.extend(fast_rows)
    if fast_rows:
        print(f"Canonical fast-matrix quote rows prepared: {len(fast_rows)}")
    new=pd.DataFrame(rows)
    if new.empty:
        print("No fresh canonical current-market quotes to append."); return
    new=new.drop_duplicates("state_id",keep="last")
    old=pd.read_csv(OUT,low_memory=False) if OUT.exists() and OUT.stat().st_size else pd.DataFrame(columns=COLS)
    cols=list(old.columns)+[c for c in COLS if c not in old.columns]
    for c in cols:
        if c not in old.columns: old[c]=""
        if c not in new.columns: new[c]=""
    existing=set(old["state_id"].dropna().astype(str)) if "state_id" in old.columns else set()
    add=new[~new["state_id"].astype(str).isin(existing)]
    if add.empty:
        print("Canonical per-book market state already present; no rows appended."); return
    out=pd.concat([old[cols],add[cols]],ignore_index=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    temporary=OUT.with_suffix(OUT.suffix+".tmp")
    out.to_csv(temporary,index=False)
    temporary.replace(OUT)
    print(f"Canonical current-market book rows appended: {len(add)}")
    print(f"Total durable book-history rows: {len(out)}")
if __name__=="__main__": main()
