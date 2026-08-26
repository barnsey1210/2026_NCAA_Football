#!/usr/bin/env python3
from __future__ import annotations
import json, math, re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import pandas as pd

ROOT=Path.home()/"NCAAF_AUTO"
# Canonical schedule truth comes from the structured preseason DB, refreshed
# from CFBD before projections and site builds.
PRESEASON_DB=ROOT/"data/snapshots/preseason/preseason_db.json"
SHADOW=ROOT/"data/site/saturday_shadow_lines.json"

# Explicit bounded inputs for the live Schedule/Postgame surface.
# Do not recursively scan data/** during an operational Postgame refresh.
LIVE_ENRICHMENT_SOURCES = (
    ROOT/"data/canonical/cfbd_schedule_2026.json",
    ROOT/"data/canonical/game_results_2026.json",
    ROOT/"data/projections/game_projection_sources_2026.csv",
    ROOT/"data/weather/game_weather_latest.csv",
    ROOT/"data/site/war_room_market_matrix.json",
)

ET=ZoneInfo("America/New_York")
OUT=ROOT/"data/site/schedule_live_enrichment.json"
TIME_KEYS=["start_time","start_date","start_datetime","kickoff","kickoff_time","scheduled","date_time","datetime"]
ID_KEYS=["game_id","id","event_id","sgo_game_id"]
HOME_KEYS=["home_team","home","home_name"]
AWAY_KEYS=["away_team","away","away_name"]

def num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception: return None

def first(row,keys):
    for k in keys:
        if k in row and row.get(k) not in (None,""): return row.get(k)
    return None

def norm_id(v):
    s=str(v or "").strip()
    return s[:-2] if s.endswith(".0") else s

def projected_market_value(score, market):
    value=num(score)
    if value is None: return "Unavailable"
    if market=="spread":
      return "Neutral"
    if value>=1.0561331175166497: return "Strongest"
    if value>=0.37464212056867763: return "Moderate"
    return "Weak or negative"

def canonical_games():
    if not PRESEASON_DB.exists():
        raise SystemExit(f"Missing canonical preseason DB: {PRESEASON_DB}")
    data=json.loads(PRESEASON_DB.read_text(encoding="utf-8",errors="ignore"))
    games=data.get("games",[])
    if not isinstance(games,list) or not games:
        raise SystemExit("Canonical preseason DB contains no games")
    return games

def et_datetime(value):
    if value in (None,""):
        return None
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if dt.tzinfo is None:
            dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(ET)
    except Exception:
        return None

def et_display(value):
    dt=et_datetime(value)
    return dt.strftime("%b %-d, %-I:%M %p ET") if dt else None

def et_iso(value):
    dt=et_datetime(value)
    return dt.isoformat() if dt else None

def row_key(r):
    gid=norm_id(first(r,ID_KEYS)); home=first(r,HOME_KEYS); away=first(r,AWAY_KEYS)
    if gid: return ("id",gid)
    if home and away: return ("teams",str(away).strip().lower(),str(home).strip().lower())
    return None

def canon(r):
    return {
      "game_id":norm_id(first(r,ID_KEYS)),"home_team":first(r,HOME_KEYS),"away_team":first(r,AWAY_KEYS),
      "season":int(num(r.get("season")) or 2026),"week":int(num(r.get("week")) or 0),
      "date":r.get("date"),"kickoff_raw":first(r,["cfbd_start_date"]+TIME_KEYS),"status":r.get("status") or r.get("cfbd_status"),
      "home_score":num(r.get("home_score") or r.get("home_points")),
      "away_score":num(r.get("away_score") or r.get("away_points")),
      "opening_spread":num(r.get("opening_spread") or r.get("open_spread")),
      "closing_spread":num(r.get("closing_spread") or r.get("close_spread")),
      "opening_total":num(r.get("opening_total") or r.get("open_total")),
      "closing_total":num(r.get("closing_total") or r.get("close_total"))
    }

def load_rows(path):
    try:
      if path.suffix==".csv": return pd.read_csv(path,low_memory=False).to_dict("records")
      data=json.loads(path.read_text(encoding="utf-8",errors="ignore"))
      if isinstance(data,list): return data
      if isinstance(data,dict):
        for v in data.values():
          if isinstance(v,list) and v and isinstance(v[0],dict): return v
    except Exception: pass
    return []

def main():
    records={}
    for raw in canonical_games():
      r=canon(raw)
      if r["season"]==2026 and row_key(r): records[row_key(r)]=r
    hits=[]
    for path in LIVE_ENRICHMENT_SOURCES:
      if not path.exists() or path in (OUT,SHADOW): continue
      rows=load_rows(path)
      if not rows or not isinstance(rows[0],dict): continue
      matched=0
      for raw in rows:
        k=row_key(raw)
        if k not in records: continue
        t=records[k]; changed=False
        pairs=[
          ("kickoff_raw",TIME_KEYS),("status",["status"]),
          ("opening_spread",["opening_spread","open_spread"]),("closing_spread",["closing_spread","close_spread"]),
          ("opening_total",["opening_total","open_total"]),("closing_total",["closing_total","close_total"]),
          ("home_score",["home_score","home_points"]),("away_score",["away_score","away_points"])
        ]
        for field,keys in pairs:
          val=first(raw,keys)
          if t.get(field) in (None,"") and val not in (None,""): t[field]=val; changed=True
        if changed: matched+=1
      if matched: hits.append({"source":str(path.relative_to(ROOT)),"matched_rows":matched})
    shadow={}
    if SHADOW.exists():
      d=json.loads(SHADOW.read_text())
      shadow={norm_id(r.get("game_id")):r for r in d.get("games",[]) if norm_id(r.get("game_id"))}
    games=[]
    for r in records.values():
      s=shadow.get(norm_id(r.get("game_id")),{})
      spread=s.get("spread_status"); total=s.get("total_status")
      status="Complete" if str(spread).startswith("Complete") and str(total).startswith("Complete") else ("Partial" if spread or total else "Pending")
      kickoff_raw=r.get("kickoff_raw")
      games.append({**r,
        "kickoff_et":et_display(kickoff_raw),
        "kickoff_iso_et":et_iso(kickoff_raw),
        "time_zone_display":"ET",
        "spread_impact":s.get("applied_spread_delta"),"total_impact":s.get("applied_total_delta"),
        "away_spread_impact":s.get("away_spread_impact"),
        "home_spread_impact":s.get("home_spread_impact"),
        "away_total_impact":s.get("away_total_impact"),
        "home_total_impact":s.get("home_total_impact"),
        "next_projection_spread":s.get("saturday_shadow_spread"),"next_projection_total":s.get("saturday_shadow_total"),
        "spread_projected_market_value":s.get("spread_value_label") or projected_market_value(s.get("spread_projected_market_value_score"),"spread"),
        "total_projected_market_value":s.get("total_value_label") or projected_market_value(s.get("total_projected_market_value_score"),"total"),
        "spread_status":spread,"total_status":total,"data_status":status,
        "cfbd_status":s.get("cfbd_status"),"pbp_status":s.get("pbp_status"),
        "raw_spread_delta":s.get("raw_matchup_spread_delta"),"raw_total_delta":s.get("raw_total_delta"),
        "market_baseline_spread":s.get("market_baseline_spread"),"market_baseline_total":s.get("market_baseline_total"),
        "away_update_state":s.get("away_update_state","baseline_only"),"home_update_state":s.get("home_update_state","baseline_only"),
        "completed_team_update_count":s.get("completed_team_update_count",0),"has_genuine_postgame_update":s.get("has_genuine_postgame_update",False),
        "shadow_display_ready":s.get("shadow_display_ready",False),"shadow_activation_reason":s.get("shadow_activation_reason","awaiting_completed_game"),
        "shadow_status":s.get("shadow_status","Awaiting completed game"),"shadow_missing_reasons":s.get("shadow_missing_reasons",[]),
        "spread_value_tier":s.get("spread_value_tier"),"spread_value_label":s.get("spread_value_label","Unavailable"),
        "total_value_tier":s.get("total_value_tier"),"total_value_label":s.get("total_value_label","Unavailable"),
        "current_model_spread":s.get("current_model_spread"),"current_model_total":s.get("current_model_total"),
        "current_market_spread":s.get("current_market_spread"),"current_market_total":s.get("current_market_total"),
        "predicted_market_rating_spread":s.get("predicted_market_rating_spread"),
        "predicted_updated_sp_plus_spread":s.get("predicted_updated_sp_plus_spread"),
        "predicted_sp_plus_component_total":s.get("predicted_sp_plus_component_total"),
        "raw_60_40_total":s.get("raw_60_40_total"),"total_bias_correction":s.get("total_bias_correction"),
        "feature_cutoff":s.get("feature_cutoff"),"leave_one_out_component_size":s.get("leave_one_out_component_size"),
        **{
          f"{side}_{field}":s.get(f"{side}_{field}")
          for side in ("away","home")
          for field in (
            "all_board_market_rating","all_board_market_rank","market_games_in_rating","market_sample_status",
            "sp_plus_entering","sp_plus_offense_entering","sp_plus_defense_entering",
            "predicted_sp_plus_offense_change","predicted_sp_plus_defense_change"
          )
        }
      })
    now_utc=datetime.now(timezone.utc)
    payload={
        "schema_version":"schedule-live-enrichment-v2",
        "built_at":now_utc.isoformat(),
        "built_at_et":now_utc.astimezone(ET).isoformat(),
        "time_zone":"America/New_York",
        "time_zone_display":"ET",
        "schedule_source":"data/snapshots/preseason/preseason_db.json",
        "source_hits":hits,
        "games":games
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps({
        "games":len(games),
        "games_with_kickoff":sum(bool(g.get("kickoff_raw")) for g in games),
        "source_hits":hits
    },indent=2))
    print("wrote:",OUT)

if __name__=="__main__":
    main()
