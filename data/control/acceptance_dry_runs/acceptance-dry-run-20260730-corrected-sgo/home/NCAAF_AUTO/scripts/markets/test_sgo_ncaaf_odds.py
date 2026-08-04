#!/usr/bin/env python3
from pathlib import Path
import os, json, urllib.parse, urllib.request, datetime

OUT_DIR = Path("data/markets/sgo")
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = (
    os.getenv("SGO_API_KEY")
    or os.getenv("SPORTSGAMEODDS_API_KEY")
    or os.getenv("SPORTS_GAME_ODDS_API_KEY")
)

if not API_KEY:
    raise SystemExit("Missing SGO_API_KEY. Run: export SGO_API_KEY='your_key'")

BASE = "https://api.sportsgameodds.com/v2/events"

params = {
    "leagueID": "NCAAF",
    "oddsAvailable": "true",
    "includeAltLines": "false",
    "limit": "250",
}

url = BASE + "?" + urllib.parse.urlencode(params)

headers = {
    "Accept": "application/json",
    # SGO docs/accounts vary by auth style; try common x-api-key first.
    "X-API-Key": API_KEY,
}

req = urllib.request.Request(url, headers=headers)

print("GET", url)

try:
    with urllib.request.urlopen(req, timeout=30) as r:
        status = r.status
        raw = r.read().decode("utf-8", errors="replace")
        hdrs = dict(r.headers)
except urllib.error.HTTPError as e:
    status = e.code
    raw = e.read().decode("utf-8", errors="replace")
    hdrs = dict(e.headers)
except Exception as e:
    raise SystemExit(f"Request failed: {e}")

ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
raw_path = OUT_DIR / "sgo_ncaaf_events_raw.json"
meta_path = OUT_DIR / "sgo_ncaaf_events_meta.json"

raw_path.write_text(raw)
meta_path.write_text(json.dumps({
    "pulled_at": ts,
    "url": url,
    "status": status,
    "headers": hdrs,
    "raw_len": len(raw),
}, indent=2))

print("status:", status)
print("raw_len:", len(raw))
print("wrote:", raw_path)
print("wrote:", meta_path)

print("\nFirst 1000 chars:")
print(raw[:1000])
