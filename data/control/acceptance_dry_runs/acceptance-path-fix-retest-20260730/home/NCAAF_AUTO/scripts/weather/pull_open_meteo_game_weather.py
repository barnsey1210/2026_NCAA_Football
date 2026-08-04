#!/usr/bin/env python3
"""
Pull per-game weather forecasts for the 2026 NCAAF site using Open-Meteo.

Run from ~/NCAAF_AUTO:
    python3 scripts/weather/pull_open_meteo_game_weather.py --init-locations
    # fill latitude/longitude/timezone in data/weather/game_weather_locations.csv
    python3 scripts/weather/pull_open_meteo_game_weather.py

Outputs:
    data/weather/game_weather_locations.csv   # seed/input location table
    data/weather/game_weather_latest.csv      # latest weather row per game
    data/weather/game_weather_history.csv     # appended daily snapshots when forecast is available

Notes:
    - Weather forecasts are only available close to gameday. Open-Meteo generally supports up to ~16 days.
    - Games outside forecast range are kept with status=not_in_forecast_window.
    - Indoor/dome games can be marked roof_type=indoor/dome/retractable to suppress wind/weather impact.
    - stadium_orientation_deg is optional. If provided, the script estimates cross/head/tail wind.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.ncaaf_config import is_neutral_site

ROOT = Path.cwd()
INDEX_PATH = ROOT / "index.html"
WEATHER_DIR = ROOT / "data" / "weather"
LOCATIONS_CSV = WEATHER_DIR / "game_weather_locations.csv"
LATEST_CSV = WEATHER_DIR / "game_weather_latest.csv"
HISTORY_CSV = WEATHER_DIR / "game_weather_history.csv"

FORECAST_DAYS = 16
USER_AGENT = "NCAAF_AUTO weather pipeline (local personal project)"

LOCATION_FIELDS = [
    "venue_key", "venue", "home_team", "latitude", "longitude", "timezone",
    "roof_type", "stadium_orientation_deg", "notes",
]

WEATHER_FIELDS = [
    "snapshot_utc", "status", "reason", "game_id", "cfbd_game_id", "season", "week", "date",
    "start_time_utc", "start_time_local", "away_team", "home_team", "venue", "neutral_site",
    "latitude", "longitude", "timezone", "roof_type", "stadium_orientation_deg",
    "temperature_f", "precip_probability_pct", "precip_in", "weather_code",
    "wind_speed_mph", "wind_gust_mph", "wind_direction_deg", "wind_type", "wind_angle_deg",
    "weather_edge_score", "weather_flags", "source",
]


def load_db() -> dict:
    html = INDEX_PATH.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("ERROR: embedded DB not found in index.html")
    return json.loads(m.group(1))


def boolish(x) -> bool:
    if isinstance(x, bool): return x
    if x is None: return False
    return str(x).strip().lower() in {"1", "true", "yes", "y"}


def fnum(x):
    try:
        if x is None or x == "": return None
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def venue_key_for_game(g: dict) -> str:
    venue = str(g.get("cfbd_venue") or g.get("venue") or "").strip()
    if venue:
        return venue.lower()
    return str(g.get("home_team") or "").strip().lower()


def venue_for_game(g: dict) -> str:
    return str(g.get("cfbd_venue") or g.get("venue") or g.get("home_team") or "").strip()


def parse_game_start_utc(g: dict):
    raw = g.get("cfbd_start_date") or g.get("start_date") or g.get("start_time")
    if raw:
        s = str(raw).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    d = g.get("date") or g.get("cfbd_date")
    if d:
        try:
            # fallback noon UTC if exact kickoff time is unknown
            return datetime.fromisoformat(str(d)).replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def init_locations(games: list[dict]) -> None:
    WEATHER_DIR.mkdir(parents=True, exist_ok=True)
    existing = {}
    if LOCATIONS_CSV.exists():
        with LOCATIONS_CSV.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                existing[r.get("venue_key", "")] = r

    rows = dict(existing)
    for g in games:
        key = venue_key_for_game(g)
        if not key or key in rows:
            continue
        rows[key] = {
            "venue_key": key,
            "venue": venue_for_game(g),
            "home_team": g.get("home_team", ""),
            "latitude": "",
            "longitude": "",
            "timezone": "",
            "roof_type": "outdoor",
            "stadium_orientation_deg": "",
            "notes": "fill lat/lon/timezone; roof_type outdoor/indoor/dome/retractable",
        }

    with LOCATIONS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOCATION_FIELDS)
        w.writeheader()
        for key in sorted(rows):
            row = {k: rows[key].get(k, "") for k in LOCATION_FIELDS}
            w.writerow(row)
    print(f"wrote: {LOCATIONS_CSV} ({len(rows)} venue rows)")


def read_locations() -> dict[str, dict]:
    if not LOCATIONS_CSV.exists():
        return {}
    with LOCATIONS_CSV.open(newline="", encoding="utf-8") as f:
        return {r.get("venue_key", ""): r for r in csv.DictReader(f)}


def fetch_open_meteo(lat: float, lon: float, tz: str | None) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "forecast_days": FORECAST_DAYS,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": tz or "auto",
        "hourly": ",".join([
            "temperature_2m", "precipitation_probability", "precipitation", "weather_code",
            "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m",
        ]),
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def nearest_hour_weather(payload: dict, start_local: datetime) -> dict | None:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        return None
    best_i = None
    best_delta = None
    for i, ts in enumerate(times):
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        delta = abs((dt - start_local.replace(tzinfo=None)).total_seconds())
        if best_delta is None or delta < best_delta:
            best_i, best_delta = i, delta
    if best_i is None:
        return None
    def get(name):
        arr = hourly.get(name) or []
        return arr[best_i] if best_i < len(arr) else None
    return {
        "temperature_f": get("temperature_2m"),
        "precip_probability_pct": get("precipitation_probability"),
        "precip_in": get("precipitation"),
        "weather_code": get("weather_code"),
        "wind_speed_mph": get("wind_speed_10m"),
        "wind_gust_mph": get("wind_gusts_10m"),
        "wind_direction_deg": get("wind_direction_10m"),
    }


def wind_type(direction_deg, orientation_deg):
    wd = fnum(direction_deg)
    od = fnum(orientation_deg)
    if wd is None or od is None:
        return "", ""
    angle = abs(((wd - od + 180) % 360) - 180)
    # 0/180 aligned with field; 90 cross-field.
    if 60 <= angle <= 120:
        typ = "crosswind"
    elif angle < 60:
        typ = "head/tail wind"
    else:
        typ = "tail/head wind"
    return typ, round(angle, 1)


def weather_flags(row: dict) -> tuple[int, list[str]]:
    roof = str(row.get("roof_type") or "").lower()
    if roof in {"indoor", "dome"}:
        return 0, ["indoor"]
    score = 0
    flags = []
    wind = fnum(row.get("wind_speed_mph"))
    gust = fnum(row.get("wind_gust_mph"))
    pop = fnum(row.get("precip_probability_pct"))
    precip = fnum(row.get("precip_in"))
    temp = fnum(row.get("temperature_f"))
    if wind is not None:
        if wind >= 20: score += 3; flags.append("20+ mph wind")
        elif wind >= 15: score += 2; flags.append("15+ mph wind")
        elif wind >= 10: score += 1; flags.append("10+ mph wind")
    if gust is not None:
        if gust >= 30: score += 2; flags.append("30+ mph gust")
        elif gust >= 25: score += 1; flags.append("25+ mph gust")
    if pop is not None and pop >= 50: score += 1; flags.append("rain risk")
    if precip is not None and precip >= 0.05: score += 1; flags.append("measurable precip")
    if temp is not None:
        if temp <= 35: score += 1; flags.append("cold")
        elif temp >= 90: score += 1; flags.append("heat")
    return score, flags


def blank_weather_row(snapshot, g, loc, status, reason):
    return {
        "snapshot_utc": snapshot,
        "status": status,
        "reason": reason,
        "game_id": g.get("game_id", ""),
        "cfbd_game_id": g.get("cfbd_game_id", ""),
        "season": g.get("season", 2026),
        "week": g.get("week", g.get("cfbd_week", "")),
        "date": g.get("date", g.get("cfbd_date", "")),
        "start_time_utc": str(parse_game_start_utc(g) or ""),
        "start_time_local": "",
        "away_team": g.get("away_team", ""),
        "home_team": g.get("home_team", ""),
        "venue": venue_for_game(g),
        "neutral_site": is_neutral_site(g),
        "latitude": loc.get("latitude", "") if loc else "",
        "longitude": loc.get("longitude", "") if loc else "",
        "timezone": loc.get("timezone", "") if loc else "",
        "roof_type": loc.get("roof_type", "") if loc else "",
        "stadium_orientation_deg": loc.get("stadium_orientation_deg", "") if loc else "",
        "temperature_f": "",
        "precip_probability_pct": "",
        "precip_in": "",
        "weather_code": "",
        "wind_speed_mph": "",
        "wind_gust_mph": "",
        "wind_direction_deg": "",
        "wind_type": "",
        "wind_angle_deg": "",
        "weather_edge_score": "",
        "weather_flags": "",
        "source": "Open-Meteo",
    }


def write_csv(path: Path, rows: list[dict], append=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    mode = "a" if append else "w"
    with path.open(mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=WEATHER_FIELDS)
        if not append or not exists:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in WEATHER_FIELDS})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init-locations", action="store_true", help="create/update the venue location seed CSV")
    args = ap.parse_args()

    if not INDEX_PATH.exists():
        raise SystemExit("ERROR: index.html not found. Run from ~/NCAAF_AUTO.")

    db = load_db()
    games = db.get("games", []) or []
    WEATHER_DIR.mkdir(parents=True, exist_ok=True)
    init_locations(games)
    if args.init_locations:
        return

    locations = read_locations()
    snapshot = datetime.now(timezone.utc).isoformat()
    today = date.today()
    latest_rows = []
    history_rows = []
    cache = {}

    for g in games:
        start_utc = parse_game_start_utc(g)
        key = venue_key_for_game(g)
        loc = locations.get(key)
        if not loc:
            latest_rows.append(blank_weather_row(snapshot, g, {}, "missing_location", "venue row missing"))
            continue

        lat, lon = fnum(loc.get("latitude")), fnum(loc.get("longitude"))
        if lat is None or lon is None:
            latest_rows.append(blank_weather_row(snapshot, g, loc, "missing_location", "latitude/longitude missing"))
            continue
        if not start_utc:
            latest_rows.append(blank_weather_row(snapshot, g, loc, "missing_start_time", "game start time/date missing"))
            continue
        if start_utc.date() < today:
            latest_rows.append(blank_weather_row(snapshot, g, loc, "past_game", "game date is in the past"))
            continue
        if start_utc.date() > today + timedelta(days=FORECAST_DAYS):
            latest_rows.append(blank_weather_row(snapshot, g, loc, "not_in_forecast_window", f"forecast available about {FORECAST_DAYS} days out"))
            continue

        tzname = loc.get("timezone") or None
        try:
            payload = cache.get(key)
            if payload is None:
                payload = fetch_open_meteo(lat, lon, tzname)
                cache[key] = payload
            api_tz = payload.get("timezone") or tzname or "UTC"
            local_tz = ZoneInfo(api_tz)
            start_local = start_utc.astimezone(local_tz)
            wx = nearest_hour_weather(payload, start_local)
            if not wx:
                latest_rows.append(blank_weather_row(snapshot, g, loc, "no_hourly_match", "forecast returned no hourly data"))
                continue
            row = blank_weather_row(snapshot, g, loc, "forecast", "")
            row.update(wx)
            row["timezone"] = api_tz
            row["start_time_local"] = start_local.isoformat()
            wtype, wangle = wind_type(row.get("wind_direction_deg"), loc.get("stadium_orientation_deg"))
            row["wind_type"] = wtype
            row["wind_angle_deg"] = wangle
            score, flags = weather_flags(row)
            row["weather_edge_score"] = score
            row["weather_flags"] = ";".join(flags)
            latest_rows.append(row)
            history_rows.append(row)
        except Exception as e:
            latest_rows.append(blank_weather_row(snapshot, g, loc, "error", str(e)))

    write_csv(LATEST_CSV, latest_rows, append=False)
    if history_rows:
        write_csv(HISTORY_CSV, history_rows, append=True)

    print(f"wrote: {LATEST_CSV} ({len(latest_rows)} rows)")
    print(f"appended forecast rows: {len(history_rows)} to {HISTORY_CSV}")
    status_counts = {}
    for r in latest_rows:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    print("status counts:", status_counts)


if __name__ == "__main__":
    main()
