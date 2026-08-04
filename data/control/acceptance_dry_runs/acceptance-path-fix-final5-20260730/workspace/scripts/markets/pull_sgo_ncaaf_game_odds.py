#!/usr/bin/env python3
from pathlib import Path
import os
import subprocess
import datetime
import json
import re

OUT_DIR = Path("data/markets/sgo")
OUT_DIR.mkdir(parents=True, exist_ok=True)

api_key = (
    os.getenv("SGO_API_KEY")
    or os.getenv("SPORTSGAMEODDS_API_KEY")
    or os.getenv("SPORTS_GAME_ODDS_API_KEY")
)

if not api_key:
    raise SystemExit("Missing SGO_API_KEY. Run: export SGO_API_KEY='your_key'")

url = "https://api.sportsgameodds.com/v2/events?leagueID=NCAAF&oddsAvailable=true&includeAltLines=false&includeOpenCloseOdds=true&limit=250"

raw_path = OUT_DIR / "sgo_ncaaf_events_raw.json"
meta_path = OUT_DIR / "sgo_ncaaf_events_meta.json"

cmd = [
    "curl",
    "-sS",
    "-i",
    "-H", "Accept: application/json",
    "-H", f"X-API-Key: {api_key}",
    "-H", "User-Agent: NCAAF-MarketBot/1.0",
    url,
]

print("GET", url)
res = subprocess.run(cmd, capture_output=True, text=True)

header_text, separator, body = res.stdout.partition("\n\n")
if not separator:
    header_text, separator, body = res.stdout.partition("\r\n\r\n")
safe_usage_headers = {}
for line in header_text.splitlines():
    if ":" not in line:
        continue
    key, value = line.split(":", 1)
    clean_key = key.strip().lower()
    if any(token in clean_key for token in ("rate", "quota", "remaining", "reset", "usage", "request-cost")):
        safe_usage_headers[clean_key] = value.strip()

raw_path.write_text(res.stdout)

meta = {
    "pulled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "url": url,
    "returncode": res.returncode,
    "stdout_len": len(res.stdout),
    "stderr": res.stderr,
    "estimated_request_cost": int(os.getenv("SGO_ESTIMATED_REQUEST_COST", "1")),
    "actual_request_cost": None,
    "usage_headers": safe_usage_headers,
    "usage_accounting_note": (
        "No quota headers returned; reconcile the estimate against the private provider dashboard."
        if not safe_usage_headers else "Usage fields captured from response headers."
    ),
}
meta_path.write_text(json.dumps(meta, indent=2))

print("returncode:", res.returncode)
print("stdout_len:", len(res.stdout))
print("wrote:", raw_path)
print("wrote:", meta_path)

if res.returncode != 0:
    raise SystemExit(res.stderr)
