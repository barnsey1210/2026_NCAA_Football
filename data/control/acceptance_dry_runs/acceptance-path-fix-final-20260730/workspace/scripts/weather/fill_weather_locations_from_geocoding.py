#!/usr/bin/env python3
"""
Fill data/weather/game_weather_locations.csv with lat/lon using OpenStreetMap Nominatim geocoding.

Run from ~/NCAAF_AUTO:
    python3 scripts/weather/fill_weather_locations_from_geocoding.py --limit 25
    python3 scripts/weather/fill_weather_locations_from_geocoding.py

Notes:
- Uses only Python standard library.
- Respects Nominatim with a 1.2 second delay between uncached requests.
- Writes a backup before changing the CSV.
- Leaves timezone blank intentionally; pull_open_meteo_game_weather.py uses timezone=auto.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
LOC_CSV = ROOT / "data" / "weather" / "game_weather_locations.csv"
CACHE_JSON = ROOT / "data" / "weather" / "geocode_cache_nominatim.json"
USER_AGENT = "NCAAF_AUTO weather location geocoder (local personal project; contact: local-user)"

PLACEHOLDER_RE = re.compile(r"\b(No\.\s*1|No\. 1|AAC|ACC|Big 12|Big Ten|CUSA|MAC|MWC|Pac-12|SEC|Sun Belt)\b", re.I)

DOME_OR_INDOOR = {
    "Alamodome": "dome",
    "Allegiant Stadium": "dome",
    "Ford Field": "dome",
    "Lucas Oil Stadium": "dome",
    "Mercedes-Benz Stadium": "retractable",
    "AT&T Stadium": "retractable",
    "NRG Stadium": "retractable",
    "Caesars Superdome": "dome",
    "State Farm Stadium": "retractable",
    "SoFi Stadium": "dome",
    "U.S. Bank Stadium": "dome",
}

# Helpful venue aliases when the schedule source uses a team name or generic name rather than stadium name.
VENUE_ALIASES = {
    "Appalachian State": "Kidd Brewer Stadium",
    "Arkansas State": "Centennial Bank Stadium",
    "Coastal Carolina": "Brooks Stadium Conway South Carolina",
    "Colorado State": "Canvas Stadium",
    "Delaware": "Delaware Stadium",
    "JMU": "Bridgeforth Stadium",
    "Miami-FL": "Hard Rock Stadium",
    "Miami (FL)": "Hard Rock Stadium",
    "Massachusetts": "Warren McGuirk Alumni Stadium",
    "Missouri State": "Robert W. Plaster Stadium Springfield Missouri",
    "North Dakota State": "Fargodome",
    "Sacramento State": "Hornet Stadium Sacramento",
    "San Diego State": "Snapdragon Stadium",
    "ULM": "Malone Stadium Monroe Louisiana",
}


def load_cache() -> dict:
    if CACHE_JSON.exists():
        try:
            return json.loads(CACHE_JSON.read_text())
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)
    CACHE_JSON.write_text(json.dumps(cache, indent=2, sort_keys=True))


def is_missing(row: dict) -> bool:
    return not str(row.get("latitude") or "").strip() or not str(row.get("longitude") or "").strip()


def should_skip(row: dict) -> bool:
    venue = str(row.get("venue") or "").strip()
    home = str(row.get("home_team") or "").strip()
    if not venue and not home:
        return True
    if PLACEHOLDER_RE.search(venue) and PLACEHOLDER_RE.search(home):
        return True
    return False


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def candidate_queries(row: dict) -> list[str]:
    venue = clean(row.get("venue"))
    home = clean(row.get("home_team"))
    alias = VENUE_ALIASES.get(venue) or VENUE_ALIASES.get(home)
    queries = []
    if alias:
        queries.append(f"{alias} {home} football stadium United States")
        queries.append(f"{alias} stadium United States")
    if venue:
        queries.append(f"{venue} {home} football stadium United States")
        queries.append(f"{venue} stadium United States")
        queries.append(f"{venue} {home} United States")
    if home:
        queries.append(f"{home} football stadium United States")
    # De-dupe while preserving order.
    out = []
    seen = set()
    for q in queries:
        q = clean(q)
        if q and q.lower() not in seen:
            out.append(q); seen.add(q.lower())
    return out


def nominatim_search(query: str, cache: dict, sleep_s: float) -> dict | None:
    key = query.lower()
    if key in cache:
        return cache[key]
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
    }
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    time.sleep(sleep_s)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        result = data[0] if data else None
    except Exception as e:
        result = {"error": str(e)}
    cache[key] = result
    save_cache(cache)
    return result


def set_roof_type(row: dict) -> None:
    venue = clean(row.get("venue"))
    for name, roof in DOME_OR_INDOOR.items():
        if name.lower() in venue.lower():
            row["roof_type"] = roof
            return
    if not row.get("roof_type"):
        row["roof_type"] = "outdoor"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="max missing rows to attempt this run; 0 = no limit")
    ap.add_argument("--sleep", type=float, default=1.2, help="seconds between uncached geocoder requests")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not LOC_CSV.exists():
        raise SystemExit(f"ERROR: {LOC_CSV} not found. Run pull_open_meteo_game_weather.py --init-locations first.")

    rows = list(csv.DictReader(LOC_CSV.open(newline="", encoding="utf-8")))
    fields = list(rows[0].keys()) if rows else []
    for f in ["latitude", "longitude", "timezone", "roof_type", "notes"]:
        if f not in fields:
            fields.append(f)
            for r in rows: r[f] = ""

    cache = load_cache()
    attempted = filled = skipped = failed = 0

    for row in rows:
        set_roof_type(row)
        if not is_missing(row):
            continue
        if should_skip(row):
            row["notes"] = "skipped placeholder/conference TBD venue"
            skipped += 1
            continue
        if args.limit and attempted >= args.limit:
            continue
        attempted += 1
        result = None
        used_query = ""
        for q in candidate_queries(row):
            r = nominatim_search(q, cache, args.sleep)
            if r and not r.get("error") and r.get("lat") and r.get("lon"):
                result = r
                used_query = q
                break
        if result:
            row["latitude"] = str(round(float(result["lat"]), 6))
            row["longitude"] = str(round(float(result["lon"]), 6))
            # Leave timezone blank; Open-Meteo forecast call will use timezone=auto.
            row["timezone"] = row.get("timezone") or ""
            display = result.get("display_name", "")
            row["notes"] = f"geocoded via Nominatim: {used_query} | {display}"[:500]
            filled += 1
            print(f"FILLED: {row.get('venue')} / {row.get('home_team')} -> {row['latitude']},{row['longitude']}")
        else:
            row["notes"] = (row.get("notes") or "") + " | geocode failed"
            failed += 1
            print(f"FAILED: {row.get('venue')} / {row.get('home_team')}")

    missing_after = sum(1 for r in rows if is_missing(r) and not should_skip(r))
    print({"attempted": attempted, "filled": filled, "failed": failed, "skipped_placeholders": skipped, "missing_after_non_placeholder": missing_after})

    if args.dry_run:
        print("dry run; not writing CSV")
        return

    backup = LOC_CSV.with_name(f"{LOC_CSV.stem}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    backup.write_text(LOC_CSV.read_text())
    with LOC_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"backup: {backup}")
    print(f"wrote: {LOC_CSV}")


if __name__ == "__main__":
    main()
