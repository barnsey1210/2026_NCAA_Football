#!/usr/bin/env python3
import json
import re
from pathlib import Path

import pandas as pd

ACTION = Path("data/odds/actionnetwork_season_game_lines_2026.csv")
FILES = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()

if not ACTION.exists():
    raise SystemExit(f"Missing {ACTION}")

a = pd.read_csv(ACTION)
lookup = {}

for _, r in a.iterrows():
    key = (str(r.get("date",""))[:10], norm(r.get("away_team")), norm(r.get("home_team")))
    vals = {}

    mapping = {
        "books_available": "market_books_available",
        "books_count": "market_books_count",

        "market_spread_hold_pct": "market_spread_hold_pct",
        "market_spread_hold_label": "market_spread_hold_label",
        "market_spread_hold_home_line": "market_spread_hold_home_line",
        "market_spread_hold_away_line": "market_spread_hold_away_line",

        # Restore corrected side-aware spread fields too.
        "market_spread_home": "market_spread_home",
        "market_spread_text": "market_spread_text",
        "market_spread_price": "market_spread_price",
        "market_spread_book": "market_spread_book",

        "market_best_home_spread_home": "market_best_home_spread_home",
        "market_best_home_spread_text": "market_best_home_spread_text",
        "market_best_home_spread_price": "market_best_home_spread_price",
        "market_best_home_spread_book": "market_best_home_spread_book",

        "market_best_away_spread_home": "market_best_away_spread_home",
        "market_best_away_spread_text": "market_best_away_spread_text",
        "market_best_away_spread_price": "market_best_away_spread_price",
        "market_best_away_spread_book": "market_best_away_spread_book",
    }

    for src, dst in mapping.items():
        if src in r.index and not pd.isna(r.get(src)):
            v = r.get(src)
            if src == "books_count":
                v = int(float(v))
            elif src in [
                "market_spread_home",
                "market_spread_price",
                "market_best_home_spread_home",
                "market_best_home_spread_price",
                "market_best_away_spread_home",
                "market_best_away_spread_price",
                "market_spread_hold_pct",
                "market_spread_hold_home_line",
                "market_spread_hold_away_line",
            ]:
                v = float(v)
            else:
                v = str(v)
            vals[dst] = v

    lookup[key] = vals

for p in FILES:
    if not p.exists():
        continue

    txt = p.read_text(errors="ignore")
    m = re.search(r'(<script id="db" type="application/json">)(.*?)(</script>)', txt, re.S)
    if not m:
        print(f"{p}: no DB found")
        continue

    db = json.loads(m.group(2))
    updated = 0

    for g in db.get("games", []):
        if g.get("market_line_source") != "Action Network":
            continue

        key = (str(g.get("date",""))[:10], norm(g.get("away_team")), norm(g.get("home_team")))
        vals = lookup.get(key)
        if not vals:
            continue

        g.update(vals)
        updated += 1

    new_json = json.dumps(db, separators=(",", ":"), ensure_ascii=False)
    txt = txt[:m.start(2)] + new_json + txt[m.end(2):]
    p.write_text(txt)
    print(f"{p}: restored Action metadata on {updated} games")
