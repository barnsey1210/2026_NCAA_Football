#!/usr/bin/env python3
"""Audit canonical 2026 kickoff quality against the accepted CFBD schedule."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.schedule.kickoff_quality import game_kickoff_status, parse_kickoff
DB=ROOT/"data/snapshots/preseason/preseason_db.json"
SCHEDULE=ROOT/"data/canonical/cfbd_schedule_2026.json"
OUT=ROOT/"data/audits/cfbd_kickoff_quality_2026.json"


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+"," ",str(value or "").lower()).strip()


def main() -> int:
    canonical=json.loads(DB.read_text())["games"]
    provider=json.loads(SCHEDULE.read_text())["games"]
    by_id={str(r["cfbd_game_id"]):r for r in provider if r.get("cfbd_game_id") is not None}
    by_match={(str(r.get("date") or "")[:10],norm(r.get("away_team")),norm(r.get("home_team"))):r for r in provider}
    rows=[]
    for game in canonical:
        match=by_id.get(str(game.get("cfbd_game_id"))) if game.get("cfbd_game_id") is not None else None
        method="cfbd_game_id" if match else None
        if not match:
            match=by_match.get((str(game.get("date") or "")[:10],norm(game.get("away_team")),norm(game.get("home_team"))))
            method="exact_date_teams" if match else None
        evidence=match or game
        status=game_kickoff_status(evidence)
        kickoff=parse_kickoff(evidence.get("start_date") or evidence.get("cfbd_start_date"))
        rows.append({"game_id":game.get("game_id"),"week":game.get("week"),"date":game.get("date"),"away_team":game.get("away_team"),"home_team":game.get("home_team"),"canonical_cfbd_game_id":game.get("cfbd_game_id"),"provider_cfbd_game_id":match.get("cfbd_game_id") if match else None,"match_method":method,"start_date":evidence.get("start_date") or evidence.get("cfbd_start_date"),"start_time_tbd":evidence.get("start_time_tbd") if "start_time_tbd" in evidence else evidence.get("cfbd_start_time_tbd"),"kickoff_status":status,"kickoff_time_verified":status=="VERIFIED_KICKOFF","kickoff_et":kickoff.isoformat() if kickoff and status=="VERIFIED_KICKOFF" else None})
    counts=Counter(r["kickoff_status"] for r in rows); by_date=defaultdict(Counter); by_week=defaultdict(Counter)
    for row in rows: by_date[str(row["date"])][row["kickoff_status"]]+=1; by_week[str(row["week"])][row["kickoff_status"]]+=1
    day_safety=[]
    for date, group in sorted(by_date.items()):
        verified=group["VERIFIED_KICKOFF"]; unresolved=sum(group[s] for s in ("TBD","DATE_PLACEHOLDER","MISSING","UNRESOLVED"))
        day_safety.append({"date":date,"verified_kickoffs":verified,"unresolved_kickoffs":unresolved,"safe_to_activate":verified>0,"policy":"VERIFIED_WINDOW_WITH_BOUNDED_MIXED_DAY_EXTENSION" if verified and unresolved else ("VERIFIED_WINDOW" if verified else "GAME_DAY_TIME_UNRESOLVED")})
    payload={"schema_version":"cfbd-kickoff-quality-audit-v1","generated_at":datetime.now(timezone.utc).isoformat(),"definitions":{"VERIFIED_KICKOFF":"startDate parses, startTimeTBD is false, and ET time is not midnight","TBD":"startTimeTBD is true with a non-midnight provisional time","DATE_PLACEHOLDER":"date exists at local midnight without verified time evidence","MISSING":"no kickoff timestamp","UNRESOLVED":"timestamp is invalid or midnight despite startTimeTBD=false"},"summary":{"total_canonical_games":len(rows),"mapped_cfbd_games":sum(r["match_method"] is not None for r in rows),**{status:counts[status] for status in ("VERIFIED_KICKOFF","TBD","DATE_PLACEHOLDER","MISSING","UNRESOLVED")}},"counts_by_week":{k:dict(v) for k,v in sorted(by_week.items())},"counts_by_date":{k:dict(v) for k,v in sorted(by_date.items())},"game_day_safety":day_safety,"week_0_games":[r for r in rows if r.get("week")==0],"sample_problematic_rows":[r for r in rows if r["kickoff_status"]!="VERIFIED_KICKOFF"][:40],"games":rows}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload["summary"],indent=2)); print(f"Wrote {OUT}"); return 0

if __name__=="__main__":raise SystemExit(main())
