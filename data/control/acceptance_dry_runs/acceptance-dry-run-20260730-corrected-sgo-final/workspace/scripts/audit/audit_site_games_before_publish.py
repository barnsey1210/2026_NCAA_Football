#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("index.html")
OUT = Path("data/audits/site_game_projection_audit.csv")

NON_FBS_CONFS = {"fcs", "non-fbs", "non fbs", "fbs/fcs", "unknown", ""}

def load_db_from_html(path: Path) -> dict:
    txt = path.read_text()

    # Current site format
    m = re.search(r'<script id="db" type="application/json">\s*(\{.*?\})\s*</script>', txt, re.S)
    if m:
        return json.loads(m.group(1))

    # Older generated format
    m = re.search(r'const DB\s*=\s*(\{.*?\});\s*</script>', txt, re.S)
    if m:
        return json.loads(m.group(1))

    raise SystemExit(f"Could not find embedded DB in {path}")

def has_projection(g: dict) -> bool:
    return any(g.get(k) is not None for k in ["projected_margin_home", "projected_total", "win_prob_home"])

def has_market(g: dict) -> bool:
    return any(g.get(k) is not None for k in [
        "market_spread_home", "market_spread_text", "market_spread_price", "market_spread_book",
        "market_total", "market_total_over_price", "market_total_under_price", "market_total_book",
    ])

def main() -> None:
    db = load_db_from_html(HTML)
    games = db.get("games", [])

    rows = []
    for g in games:
        away_conf = str(g.get("away_conference") or "").strip()
        home_conf = str(g.get("home_conference") or "").strip()
        away_non_fbs = away_conf.lower() in NON_FBS_CONFS
        home_non_fbs = home_conf.lower() in NON_FBS_CONFS

        flags = []

        if (away_non_fbs or home_non_fbs) and has_projection(g):
            flags.append("NON_FBS_GAME_HAS_PROJECTION")

        if (away_non_fbs or home_non_fbs) and has_market(g):
            flags.append("NON_FBS_GAME_HAS_MARKET_LINE_REVIEW")

        if g.get("projected_total") is not None and (away_non_fbs or home_non_fbs):
            flags.append("NON_FBS_PROJECTED_TOTAL_REVIEW")

        if flags:
            rows.append({
                "week": g.get("week"),
                "date": g.get("date"),
                "away_team": g.get("away_team"),
                "home_team": g.get("home_team"),
                "away_conference": away_conf,
                "home_conference": home_conf,
                "projected_margin_home": g.get("projected_margin_home"),
                "projected_total": g.get("projected_total"),
                "win_prob_home": g.get("win_prob_home"),
                "market_spread_text": g.get("market_spread_text"),
                "market_spread_price": g.get("market_spread_price"),
                "market_spread_book": g.get("market_spread_book"),
                "market_total": g.get("market_total"),
                "market_total_over_price": g.get("market_total_over_price"),
                "market_total_under_price": g.get("market_total_under_price"),
                "market_total_book": g.get("market_total_book"),
                "flags": ";".join(flags),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print(f"Wrote {OUT}: {len(df)} flagged rows")
    if len(df):
        print(df.head(40).to_string(index=False))

if __name__ == "__main__":
    main()
