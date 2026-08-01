#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DIR = Path("data/markets/sgo")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENDPOINT = "https://api.sportsgameodds.com/v2/events"
MAX_PAGES = int(os.getenv("SGO_MAX_PAGES", "5"))

api_key = (
    os.getenv("SGO_API_KEY")
    or os.getenv("SPORTSGAMEODDS_API_KEY")
    or os.getenv("SPORTS_GAME_ODDS_API_KEY")
)

if not api_key:
    raise SystemExit("Missing SGO_API_KEY")

base_params = {
    "leagueID": "NCAAF",
    "oddsAvailable": "true",
    "includeAltLines": "false",
    "includeOpenCloseOdds": "true",
    "limit": "250",
}

raw_path = OUT_DIR / "sgo_ncaaf_events_raw.json"
meta_path = OUT_DIR / "sgo_ncaaf_events_meta.json"

pages: list[dict] = []
events_by_id: dict[str, dict] = {}
cursor = None
seen_cursors: set[str] = set()
usage_headers: dict[str, str] = {}

for page_number in range(1, MAX_PAGES + 1):
    params = dict(base_params)
    if cursor:
        params["cursor"] = cursor

    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    print(f"GET page {page_number}: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "NCAAF-MarketBot/2.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
            page = json.loads(body)

            for key, value in response.headers.items():
                lower = key.lower()
                if any(
                    token in lower
                    for token in (
                        "rate",
                        "quota",
                        "remaining",
                        "reset",
                        "usage",
                        "request-cost",
                    )
                ):
                    usage_headers[lower] = value
    except Exception as exc:
        raise SystemExit(f"SGO request failed on page {page_number}: {exc}")

    if not isinstance(page, dict):
        raise SystemExit(
            f"SGO page {page_number} returned {type(page).__name__}, expected object"
        )

    pages.append(page)

    page_path = OUT_DIR / f"sgo_ncaaf_events_page_{page_number:03d}.json"
    page_path.write_text(json.dumps(page, indent=2) + "\n")

    page_events = page.get("data", [])
    if not isinstance(page_events, list):
        raise SystemExit(f"SGO page {page_number} has non-list data field")

    for event in page_events:
        event_id = str(event.get("eventID") or "")
        if not event_id:
            continue
        events_by_id[event_id] = event

    next_cursor = page.get("nextCursor")
    print(
        f"page {page_number}: events={len(page_events)}, "
        f"combined={len(events_by_id)}, nextCursor={bool(next_cursor)}"
    )

    if not next_cursor:
        cursor = None
        break

    next_cursor = str(next_cursor)
    if next_cursor in seen_cursors:
        raise SystemExit("SGO pagination returned a repeated cursor")

    seen_cursors.add(next_cursor)
    cursor = next_cursor

combined = {
    "success": all(page.get("success", True) for page in pages),
    "data": list(events_by_id.values()),
    "nextCursor": cursor,
    "notice": pages[-1].get("notice") if pages else None,
}

raw_path.write_text(json.dumps(combined, indent=2) + "\n")

pulled_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
meta = {
    "pulled_at": pulled_at,
    "endpoint": ENDPOINT,
    "query": base_params,
    "pages_fetched": len(pages),
    "max_pages": MAX_PAGES,
    "events_returned_before_deduplication": sum(
        len(page.get("data", []))
        for page in pages
        if isinstance(page.get("data"), list)
    ),
    "events_returned_after_deduplication": len(events_by_id),
    "next_cursor_remaining": bool(cursor),
    "coverage_status": "PARTIAL" if cursor else "COMPLETE",
    "estimated_request_cost": len(pages),
    "actual_request_cost": None,
    "usage_headers": usage_headers,
    "usage_accounting_note": (
        "No quota headers returned; reconcile the estimate against the "
        "private provider dashboard."
        if not usage_headers
        else "Usage fields captured from response headers."
    ),
}

meta_path.write_text(json.dumps(meta, indent=2) + "\n")

print("pages fetched:", len(pages))
print("combined events:", len(events_by_id))
print("next cursor remaining:", bool(cursor))
print("wrote:", raw_path)
print("wrote:", meta_path)

if cursor:
    raise SystemExit(
        f"SGO pagination remains incomplete after {MAX_PAGES} pages; "
        "combined payload retained but must not be accepted."
    )
