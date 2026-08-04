#!/usr/bin/env python3
"""Build canonical SGO accepted-quote candidates and display lines.

Input must be controller-normalized quote observations. Raw provider responses
are deliberately not accepted here. Global acceptance remains blocked unless
the coverage manifest proves the requested canonical scope is complete.
"""
from __future__ import annotations

import argparse, csv, hashlib, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PAIR_SIDES={"spread":("away","home"),"total":("over","under"),"moneyline":("away","home")}
BOOK_PRIORITY=("draftkings","bovada")
QUOTE_FIELDS=[
 "provider","provider_event_id","canonical_game_id","season","canonical_site_week","kickoff",
 "away_team","home_team","neutral_site","game_classification","sportsbook","market_type","side",
 "line","price","paired_market_id","available","suspended","source_updated_at","ingestion_timestamp",
 "quote_age_seconds","stale_flag","source_run_id","source_page","coverage_status","mapping_status",
 "market_eligibility","acceptance_eligibility","exclusion_reason","payload_hash",
]
DISPLAY_FIELDS=[
 "provider","canonical_game_id","season","canonical_site_week","kickoff","away_team","home_team",
 "neutral_site","game_classification","market_type","selected_sportsbook","away_line","home_line",
 "away_price","home_price","total_line","over_price","under_price","source_updated_at","available",
 "stale_flag","selection_reason","fallback_reason","paired_market_id","source_run_id","coverage_status",
 "acceptance_eligibility","ingestion_timestamp","payload_hash",
]

def truth(v): return str(v).lower() in {"true","1","yes"}
def number(v):
 try:return float(v)
 except (TypeError,ValueError):return None
def read_csv(path):
 with path.open(newline="") as h:return list(csv.DictReader(h))
def write_csv(path,rows,fields):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",newline="") as h:
  w=csv.DictWriter(h,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
def pair_valid(market,pair):
 if set(pair)!=set(PAIR_SIDES[market]):return False,"missing_paired_side"
 if market=="spread":
  vals=[number(pair[s].get("line")) for s in PAIR_SIDES[market]]
  if None in vals or abs(sum(vals))>.001:return False,"conflicting_paired_line"
 if market=="total":
  vals=[number(pair[s].get("line")) for s in PAIR_SIDES[market]]
  if None in vals or abs(vals[0]-vals[1])>.001:return False,"conflicting_paired_line"
 if market=="moneyline" and any(number(pair[s].get("price")) is None for s in PAIR_SIDES[market]):
  return False,"missing_paired_price"
 return True,""

def build(observations,manifest,canonical_games,payload_hash,ingested_at):
 games={str(g["game"]["game_id"]):g for g in canonical_games.get("games",[])}
 coverage=manifest.get("coverage_status","UNKNOWN")
 global_ok=coverage=="COMPLETE" and not manifest.get("next_cursor_present") and not manifest.get("events_ambiguous")
 grouped=defaultdict(dict); exclusions=[]
 for q in observations:
  gid=str(q.get("canonical_game_id") or ""); game=games.get(gid)
  market=q.get("market");side=q.get("side");book=q.get("sportsbook")
  reason=""
  if not game:reason="canonical_game_missing"
  elif int(q.get("canonical_week",-99))!=int(manifest.get("resolved_canonical_week",-98)):reason="outside_selected_canonical_week"
  elif not truth(q.get("available")):reason="unavailable"
  elif truth(q.get("suspended")):reason="suspended"
  elif truth(q.get("stale")):reason="stale"
  elif market not in PAIR_SIDES or side not in PAIR_SIDES[market]:reason="unsupported_market_side"
  if reason: exclusions.append({"quote_id":q.get("quote_id"),"canonical_game_id":gid,"reason":reason});continue
  grouped[(gid,book,market)][side]=q
 accepted=[]
 for (gid,book,market),pair in sorted(grouped.items()):
  valid,reason=pair_valid(market,pair)
  if not valid:
   exclusions.append({"canonical_game_id":gid,"sportsbook":book,"market_type":market,"reason":reason});continue
  game=games[gid];g=game["game"];teams=game.get("teams",{})
  pair_id=hashlib.sha256(f"sports_game_odds|{gid}|{book}|{market}|".encode()+"|".join(str(pair[s].get("quote_id")) for s in PAIR_SIDES[market]).encode()).hexdigest()
  for side in PAIR_SIDES[market]:
   q=pair[side];age=q.get("quote_age_hours");age_sec=round(float(age)*3600,3) if number(age) is not None else ""
   accepted.append({
    "provider":"sports_game_odds","provider_event_id":q.get("provider_event_id"),"canonical_game_id":gid,
    "season":2026,"canonical_site_week":g.get("week"),"kickoff":g.get("kickoff_utc") or g.get("date"),
    "away_team":g.get("away_team"),"home_team":g.get("home_team"),"neutral_site":g.get("neutral_site"),
    "game_classification":"FBS_vs_FBS" if all((teams.get(x)or{}).get("overall_rank") is not None for x in ("away","home")) else "mixed_or_FCS",
    "sportsbook":book,"market_type":market,"side":side,"line":q.get("line"),"price":q.get("price"),
    "paired_market_id":pair_id,"available":True,"suspended":False,"source_updated_at":q.get("provider_last_updated_at"),
    "ingestion_timestamp":ingested_at,"quote_age_seconds":age_sec,"stale_flag":False,
    "source_run_id":manifest.get("run_id"),"source_page":1,"coverage_status":coverage,"mapping_status":"canonical_mapped",
    "market_eligibility":True,"acceptance_eligibility":global_ok,"exclusion_reason":"" if global_ok else "coverage_partial",
    "payload_hash":payload_hash,
   })
 by=defaultdict(lambda:defaultdict(lambda:defaultdict(dict)))
 for q in accepted:by[q["canonical_game_id"]][q["market_type"]][q["sportsbook"]][q["side"]]=q
 display=[]
 for gid,markets in sorted(by.items()):
  for market,books in sorted(markets.items()):
   selected=next((b for b in BOOK_PRIORITY if b in books),None)
   if not selected:continue
   pair=books[selected]; first=pair[PAIR_SIDES[market][0]]
   row={k:first.get(k,"") for k in ("provider","canonical_game_id","season","canonical_site_week","kickoff","away_team","home_team","neutral_site","game_classification","source_run_id","coverage_status","acceptance_eligibility","ingestion_timestamp","payload_hash")}
   row.update({"market_type":market,"selected_sportsbook":selected,"source_updated_at":max(str(x.get("source_updated_at")or"") for x in pair.values()),"available":True,"stale_flag":False,"selection_reason":"DraftKings priority" if selected=="draftkings" else "Bovada priority","fallback_reason":"" if selected=="draftkings" else "DraftKings paired quote unavailable","paired_market_id":first["paired_market_id"]})
   if market=="spread":row.update({"away_line":pair["away"]["line"],"home_line":pair["home"]["line"],"away_price":pair["away"]["price"],"home_price":pair["home"]["price"]})
   elif market=="total":row.update({"total_line":pair["over"]["line"],"over_price":pair["over"]["price"],"under_price":pair["under"]["price"]})
   else:row.update({"away_price":pair["away"]["price"],"home_price":pair["home"]["price"]})
   display.append(row)
 return accepted,display,exclusions,global_ok

def main():
 p=argparse.ArgumentParser();p.add_argument("--observations",type=Path,required=True);p.add_argument("--manifest",type=Path,required=True);p.add_argument("--canonical-games",type=Path,default=ROOT/"data/site/matchups_view.json");p.add_argument("--raw",type=Path,required=True);p.add_argument("--quotes-out",type=Path,required=True);p.add_argument("--display-out",type=Path,required=True);p.add_argument("--coverage-out",type=Path,required=True);p.add_argument("--exclusions-out",type=Path,required=True)
 a=p.parse_args();manifest=json.loads(a.manifest.read_text());raw=a.raw.read_bytes();payload_hash=hashlib.sha256(raw).hexdigest();canonical=json.loads(a.canonical_games.read_text());obs=read_csv(a.observations);now=datetime.now(timezone.utc).isoformat()
 quotes,display,excluded,global_ok=build(obs,manifest,canonical,payload_hash,now)
 write_csv(a.quotes_out,quotes,QUOTE_FIELDS);write_csv(a.display_out,display,DISPLAY_FIELDS);write_csv(a.exclusions_out,excluded,sorted({k for r in excluded for k in r}) or ["reason"])
 expected=manifest.get("events_staged_for_canonical_week",0);mapped=len({q["canonical_game_id"] for q in quotes});coverage={"schema_version":"canonical-market-coverage-v1","provider":"sports_game_odds","scope":"FBS-vs-FBS canonical site week","selected_week":manifest.get("resolved_canonical_week"),"expected_canonical_games":expected,"mapped_canonical_games":mapped,"missing_canonical_games":max(int(expected)-mapped,0),"raw_pages_fetched":manifest.get("page_count",1),"next_cursor_remaining":manifest.get("next_cursor_present",False),"coverage_status":manifest.get("coverage_status"),"request_unit_estimate":0,"request_unit_actual":0,"acceptance_eligibility":global_ok,"acceptance_block_reason":"" if global_ok else "partial coverage or remaining cursor","unmatched_events":manifest.get("events_unmatched",0),"ambiguous_events":manifest.get("events_ambiguous",0),"accepted_quote_rows":len(quotes),"display_rows":len(display),"payload_hash":payload_hash}
 a.coverage_out.parent.mkdir(parents=True,exist_ok=True);a.coverage_out.write_text(json.dumps(coverage,indent=2,sort_keys=True)+"\n")
 print(json.dumps(coverage,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
