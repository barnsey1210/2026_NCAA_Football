#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path.home() / "NCAAF_AUTO"
SCHEDULE = ROOT / "data/site/schedule_live_enrichment.json"

ALIASES = {
    "massachusetts": "umass",
    "connecticut": "uconn",
    "miami florida": "miami",
    "miami fl": "miami",
    "miami ohio": "miami oh",
    "north carolina state": "nc state",
    "nc state wolfpack": "nc state",
    "southern california": "usc",
    "central florida": "ucf",
    "texas san antonio": "utsa",
    "texas el paso": "utep",
    "louisiana state": "lsu",
    "brigham young": "byu",
    "southern methodist": "smu",
    "texas christian": "tcu",
    "bowling green state": "bowling green",
    "middle tennessee state": "middle tennessee",
    "appalachian state": "app state",
    "florida international": "fiu",
    "florida atlantic": "fau",
    "nevada las vegas": "unlv",
    "hawai i": "hawaii",
    "hawai’i": "hawaii",
    "hawaiʻi": "hawaii",
}

def norm(value: object) -> str:
    s = str(value or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\s+", " ", s)
    return ALIASES.get(s, s)

def parse_iso(value: object):
    s = str(value or "").strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None

def date_key(value: object) -> str:
    dt = parse_iso(value)
    if dt:
        # Match the site schedule date in Eastern Time. Late-night games
        # can fall on the following UTC date while still being the prior ET date.
        return dt.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    s = str(value or "")
    return s[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", s) else ""

def is_placeholder(dt, explicit_tbd=None) -> bool:
    if not dt:
        return True
    if explicit_tbd is True or str(explicit_tbd).lower() == "true":
        return True
    utc = dt.astimezone(timezone.utc)
    return utc.hour == 4 and utc.minute == 0 and utc.second == 0

def add_candidate(store, away, home, start, source, explicit_tbd=None):
    dt = parse_iso(start)
    if not dt:
        return
    key = (norm(away), norm(home), date_key(start))
    if not all(key):
        return
    store[key].append({
        "dt": dt.astimezone(timezone.utc),
        "source": source,
        "placeholder": is_placeholder(dt, explicit_tbd),
    })

def load_candidates():
    store = defaultdict(list)

    path = ROOT / "data/odds/cfbd_lines_2026_raw.json"
    if path.exists():
        data = json.loads(path.read_text())
        rows = data if isinstance(data, list) else data.get("games", [])
        for row in rows:
            add_candidate(
                store,
                row.get("awayTeam") or row.get("away_team"),
                row.get("homeTeam") or row.get("home_team"),
                row.get("startDate") or row.get("commence_time"),
                "CFBD lines",
                row.get("startTimeTBD"),
            )

    path = ROOT / "data/odds/theodds_ncaaf_lines_2026_raw.json"
    if path.exists():
        data = json.loads(path.read_text())
        rows = data if isinstance(data, list) else data.get("data", [])
        for row in rows:
            add_candidate(
                store,
                row.get("away_team"),
                row.get("home_team"),
                row.get("commence_time"),
                "The Odds API",
            )

    for source, path in [
        ("The Odds CSV", ROOT / "data/odds/theodds_ncaaf_lines_2026.csv"),
        ("Action", ROOT / "data/odds/action_ncaaf_game_lines_2026.csv"),
        ("Action Network", ROOT / "data/odds/actionnetwork_ncaaf_game_lines_2026.csv"),
    ]:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
            for row in csv.DictReader(handle):
                add_candidate(
                    store,
                    row.get("away_team"),
                    row.get("home_team"),
                    row.get("commence_time") or row.get("startDate"),
                    source,
                )
    return store

def choose(candidates):
    real = [x for x in candidates if not x["placeholder"]]
    if not real:
        return None
    priority = {"CFBD lines": 0, "The Odds API": 1, "The Odds CSV": 2, "Action Network": 3, "Action": 4}
    return sorted(real, key=lambda x: (priority.get(x["source"], 99), x["dt"]))[0]

def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value

def main():
    if not SCHEDULE.exists():
        raise SystemExit(f"Missing: {SCHEDULE}")

    payload = json.loads(SCHEDULE.read_text())
    games = payload.get("games", [])
    candidates = load_candidates()

    matched = 0
    tbd = 0
    source_counts = defaultdict(int)

    for row in games:
        game = row.get("game", row)
        away = game.get("away_team")
        home = game.get("home_team")
        game_date = str(game.get("date") or row.get("date") or "")[:10]
        key = (norm(away), norm(home), game_date)
        picked = choose(candidates.get(key, []))

        if picked:
            utc_dt = picked["dt"]
            et_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))
            row["kickoff_raw"] = utc_dt.isoformat().replace("+00:00", "Z")
            row["kickoff_utc"] = row["kickoff_raw"]
            row["kickoff_et"] = et_dt.isoformat()
            row["kickoff_status"] = "confirmed"
            row["kickoff_source"] = picked["source"]
            game["start_time"] = row["kickoff_utc"]
            game["kickoff_status"] = "confirmed"
            matched += 1
            source_counts[picked["source"]] += 1
        else:
            row["kickoff_raw"] = None
            row["kickoff_utc"] = None
            row["kickoff_et"] = None
            row["kickoff_status"] = "TBD"
            row["kickoff_source"] = None
            game["kickoff_status"] = "TBD"
            tbd += 1

    payload["kickoff_enrichment"] = {
        "games": len(games),
        "games_with_kickoff": matched,
        "games_tbd": tbd,
        "sources": dict(sorted(source_counts.items())),
        "timezone_display": "America/New_York",
    }
    payload = json_safe(payload)
    SCHEDULE.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(json.dumps(payload["kickoff_enrichment"], indent=2))
    print("wrote:", SCHEDULE)

if __name__ == "__main__":
    main()
