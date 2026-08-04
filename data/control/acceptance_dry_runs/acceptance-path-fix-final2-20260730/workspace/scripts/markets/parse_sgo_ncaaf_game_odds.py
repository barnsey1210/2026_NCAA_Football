#!/usr/bin/env python3
"""Compatibility export from canonical SGO display lines.

Raw SGO pages are intentionally rejected. Run build_sgo_daily_canonical.py first.
"""
from pathlib import Path
import json, pandas as pd
ROOT=Path(__file__).resolve().parents[2]
DISPLAY=ROOT/"data/markets/sgo/sgo_canonical_display_lines.csv"
COVERAGE=ROOT/"data/markets/sgo/sgo_canonical_coverage.json"
OUT=ROOT/"data/markets/sgo/sgo_ncaaf_game_odds.csv"
def main():
 if not DISPLAY.exists() or not COVERAGE.exists():raise SystemExit("Canonical SGO artifacts missing; raw parsing is disabled")
 coverage=json.loads(COVERAGE.read_text())
 if not coverage.get("acceptance_eligibility"):raise SystemExit("SGO coverage gate BLOCKED; legacy accepted export not modified")
 d=pd.read_csv(DISPLAY);rows=[]
 for gid,g in d.groupby("canonical_game_id"):
  base=g.iloc[0];out={"source":"SportsGameOdds","game_id":gid,"date":str(base.kickoff)[:10],"away_team":base.away_team,"home_team":base.home_team,"neutral_site":base.neutral_site,"pulled_at":base.ingestion_timestamp}
  for _,r in g.iterrows():
   if r.market_type=="spread":out.update({"market_spread_home":r.home_line,"market_spread_book":r.selected_sportsbook,"market_spread_price_home":r.home_price,"market_spread_price_away":r.away_price,"market_spread_last_update":r.source_updated_at})
   elif r.market_type=="total":out.update({"market_total":r.total_line,"market_total_book":r.selected_sportsbook,"market_total_over_price":r.over_price,"market_total_under_price":r.under_price,"market_total_last_update":r.source_updated_at})
   elif r.market_type=="moneyline":out.update({"market_away_moneyline":r.away_price,"market_home_moneyline":r.home_price,"market_moneyline_book":r.selected_sportsbook,"market_moneyline_last_update":r.source_updated_at})
  rows.append(out)
 pd.DataFrame(rows).to_csv(OUT,index=False);print(f"wrote canonical compatibility export: {OUT} rows={len(rows)}")
if __name__=="__main__":main()
