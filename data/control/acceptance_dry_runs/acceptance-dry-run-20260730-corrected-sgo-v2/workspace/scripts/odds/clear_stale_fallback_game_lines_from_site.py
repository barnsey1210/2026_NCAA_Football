#!/usr/bin/env python3
import json
import re
from pathlib import Path

import pandas as pd

FILES = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

STALE_DAYS = 7
PRIMARY_SOURCE = "Action Network"

MARKET_KEYS = [
    "market_spread_home",
    "market_spread_open_home",
    "market_spread_text",
    "market_spread_price",
    "market_spread_book",
    "market_spread_last_update",
    "market_spread_display_side",
    "market_spread_display_team",
    "market_formatted_spread",
    "market_best_home_spread_home",
    "market_best_home_spread_text",
    "market_best_home_spread_price",
    "market_best_home_spread_book",
    "market_best_away_spread_home",
    "market_best_away_spread_text",
    "market_best_away_spread_price",
    "market_best_away_spread_book",
    "market_total",
    "market_total_open",
    "market_total_book",
    "market_total_over_price",
    "market_total_under_price",
    "market_total_last_update",
    "market_best_over_total",
    "market_best_over_price",
    "market_best_over_book",
    "market_best_under_total",
    "market_best_under_price",
    "market_best_under_book",
    "home_moneyline",
    "away_moneyline",
    "home_moneyline_implied",
    "away_moneyline_implied",
    "books_available",
    "books_count",
    "market_line_source",
    "market_price_status",
    "line_source",
]

def latest_market_ts(g):
    vals = []
    for k in ["market_spread_last_update", "market_total_last_update"]:
        v = g.get(k)
        if v not in [None, ""]:
            vals.append(v)
    if not vals:
        return pd.NaT
    parsed = pd.to_datetime(pd.Series(vals), errors="coerce", utc=True).dropna()
    if parsed.empty:
        return pd.NaT
    return parsed.max()

def clear_market(g, reason):
    for k in MARKET_KEYS:
        if k in g:
            g[k] = None
    g["market_price_status"] = "stale_backup_hidden"
    g["market_line_note"] = reason

def process(path: Path):
    if not path.exists():
        return

    txt = path.read_text(errors="ignore")
    m = re.search(r'(<script id="db" type="application/json">)(.*?)(</script>)', txt, re.S)
    if not m:
        print(f"{path}: missing DB")
        return

    db = json.loads(m.group(2))
    games = db.get("games", [])

    now = pd.Timestamp.now(tz="UTC")
    cleared = []

    for g in games:
        source = str(g.get("market_line_source") or g.get("line_source") or "")
        has_market = g.get("market_spread_home") is not None or g.get("market_total") is not None
        if not has_market:
            continue

        # Keep Action Network as the primary source. This script only guards backup/fallback lines.
        if source == PRIMARY_SOURCE:
            continue

        ts = latest_market_ts(g)
        if pd.isna(ts):
            reason = f"Backup market line hidden because {source or 'fallback source'} had no usable timestamp."
            clear_market(g, reason)
            cleared.append((g.get("away_team"), g.get("home_team"), source, "missing timestamp"))
            continue

        age_days = (now - ts).total_seconds() / 86400
        if age_days > STALE_DAYS:
            reason = f"Backup market line hidden because {source or 'fallback source'} was stale: last update {ts.date()}."
            clear_market(g, reason)
            cleared.append((g.get("away_team"), g.get("home_team"), source, f"{age_days:.1f} days"))

    new_json = json.dumps(db, separators=(",", ":"), ensure_ascii=False)
    txt = txt[:m.start(2)] + new_json + txt[m.end(2):]
    path.write_text(txt)

    print(f"{path}: cleared {len(cleared)} stale fallback market lines")
    for row in cleared[:30]:
        print("  ", row)

for f in FILES:
    process(f)
