#!/usr/bin/env python3
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import requests

YEAR = 2026
BASE_URL = "https://api.collegefootballdata.com/games"
OUT_DIR = Path("data/canonical")
RAW_JSON = OUT_DIR / "cfbd_schedule_2026_raw.json"
OUT_JSON = OUT_DIR / "cfbd_schedule_2026.json"
AUDIT_JSON = Path("data/audits/cfbd_schedule_2026_audit.json")

def require_key():
    key = os.environ.get("CFBD_API_KEY")
    if not key:
        raise SystemExit("Missing CFBD_API_KEY")
    return key

def main():
    pulled_at = datetime.now(timezone.utc).isoformat()
    r = requests.get(
        BASE_URL,
        headers={"Authorization": f"Bearer {require_key()}"},
        params={"year": YEAR, "seasonType": "regular"},
        timeout=45,
    )
    if r.status_code != 200:
        raise SystemExit(f"CFBD games request failed: HTTP {r.status_code}\\n{r.text[:800]}")
    raw = r.json()
    if not isinstance(raw, list):
        raise SystemExit(f"Unexpected CFBD response type: {type(raw)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    RAW_JSON.write_text(json.dumps(raw, indent=2) + "\n")

    games = []
    for g in raw:
        start = g.get("startDate")
        local_date = None
        if start:
            try:
                dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
                local_date = dt.astimezone(ZoneInfo("America/New_York")).date().isoformat()
            except Exception:
                local_date = str(start)[:10]

        provider_week = g.get("week")

        # Canonical 2026 site week convention:
        # Saturday, Aug. 29 is Week 0 even though CFBD currently labels it
        # Week 1. Normalize here so every downstream consumer receives the
        # same canonical week numbering.
        canonical_week = provider_week
        if local_date == "2026-08-29":
            canonical_week = 0

        games.append({
            "cfbd_game_id": g.get("id"),
            "season": g.get("season"),
            "week": canonical_week,
            "provider_week": provider_week,
            "season_type": g.get("seasonType"),
            "date": local_date,
            "start_date": start,
            "start_time_tbd": g.get("startTimeTBD"),
            "completed": g.get("completed"),
            "neutral_site": g.get("neutralSite"),
            "conference_game": g.get("conferenceGame"),
            "home_team": g.get("homeTeam"),
            "away_team": g.get("awayTeam"),
            "home_points": g.get("homePoints"),
            "away_points": g.get("awayPoints"),
            "status": g.get("status"),
            "cfbd_last_updated": g.get("lastUpdated"),
            "pulled_at": pulled_at,
        })
    games = [g for g in games if g["cfbd_game_id"] and g["home_team"] and g["away_team"]]
    games.sort(key=lambda g: (g["date"] or "", g["week"] or 0, g["away_team"], g["home_team"]))

    OUT_JSON.write_text(json.dumps({
        "schema_version": "cfbd-schedule-2026-v1",
        "season": YEAR,
        "source": "CollegeFootballData /games",
        "pulled_at": pulled_at,
        "games": games,
    }, indent=2) + "\n")

    audit = {
        "schema_version": "cfbd-schedule-2026-audit-v1",
        "pulled_at": pulled_at,
        "raw_rows": len(raw),
        "normalized_rows": len(games),
        "dated_rows": sum(bool(g["date"]) for g in games),
        "tbd_rows": sum(bool(g["start_time_tbd"]) for g in games),
        "canonical_week_overrides": sum(
            g.get("week") != g.get("provider_week") for g in games
        ),
        "first_date": min((g["date"] for g in games if g["date"]), default=None),
        "last_date": max((g["date"] for g in games if g["date"]), default=None),
    }
    AUDIT_JSON.write_text(json.dumps(audit, indent=2) + "\n")
    print(f"Wrote {OUT_JSON}: {len(games)} games")
    print(json.dumps(audit, indent=2))

if __name__ == "__main__":
    main()
