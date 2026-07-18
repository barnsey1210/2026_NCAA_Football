#!/usr/bin/env python3
"""Build the standalone Futures data contract from canonical site inputs."""
from pathlib import Path
from datetime import datetime, timezone
import json, re, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts.lib.ncaaf_config import canonical_team

def number(value):
    try: return float(value) if value not in (None, "") else None
    except (TypeError, ValueError): return None

def main():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not match: raise SystemExit("Embedded canonical database not found in index.html")
    db = json.loads(match.group(1))
    teams = {canonical_team(x.get("team")): x for x in db.get("teams", [])}
    bets_path = ROOT / "data/site/betting_activity_view.json"
    bets = json.loads(bets_path.read_text()).get("records", []) if bets_path.exists() else []
    open_futures = [x for x in bets if x.get("is_open") and x.get("market") in {"Win Total", "Conference Future"}]
    movement = {}
    for x in db.get("market_win_totals_movement", []):
        movement[(canonical_team(x.get("team")), x.get("book"))] = x
    title_movement = {}
    for x in db.get("market_conference_futures_movement", []):
        title_movement[(canonical_team(x.get("team")), x.get("book"))] = x
    rows = []
    merged_markets = {}
    for source in db.get("market_futures_best_prices", []):
        key = canonical_team(source.get("team"))
        target = merged_markets.setdefault(key, {})
        for field, value in source.items():
            if value not in (None, ""): target[field] = value
    for market in merged_markets.values():
        key, team = canonical_team(market.get("team")), None
        team = teams.get(key)
        if not team: continue
        projected_wins = number(team.get("avg_total_wins"))
        title_prob = number(team.get("conference_title_pct"))
        total = number(market.get("market_win_total"))
        title_market = number(market.get("market_implied_title_prob"))
        direction = "Over" if projected_wins is not None and total is not None and projected_wins >= total else "Under"
        price = market.get("best_over_odds" if direction == "Over" else "best_under_odds")
        book = market.get("best_over_book" if direction == "Over" else "best_under_book")
        team_bets = [b for b in open_futures if canonical_team(b.get("team")) == key]
        rows.append({
            "team": team.get("team"), "slug": team.get("slug"), "conference": team.get("conference"), "rank": team.get("rank"),
            "projected_wins": projected_wins, "market_win_total": total, "win_edge": projected_wins-total if projected_wins is not None and total is not None else None,
            "win_direction": direction, "win_price": price, "win_book": book,
            "title_model_prob": title_prob, "title_market_prob": title_market,
            "title_edge": title_prob-title_market if title_prob is not None and title_market is not None else None,
            "title_price": market.get("best_title_odds"), "title_book": market.get("best_title_book"),
            "win_movement": movement.get((key, book)), "title_movement": title_movement.get((key, market.get("best_title_book"))),
            "open_wagers": team_bets, "last_updated": market.get("last_updated")})
    payload = {"schema_version":"futures-view-v1", "built_at":datetime.now(timezone.utc).isoformat(),
               "model_updated":db.get("meta",{}).get("generated_at"), "rows":rows,
               "summary":{"teams":len(rows),"win_markets":sum(x["market_win_total"] is not None for x in rows),
                          "title_markets":sum(x["title_price"] is not None for x in rows),"open_wagers":len(open_futures)}}
    out = ROOT / "data/site/futures_view.json"; out.write_text(json.dumps(payload,separators=(",",":"))+"\n")
    print(json.dumps(payload["summary"],indent=2)); print(out)
if __name__ == "__main__": main()
