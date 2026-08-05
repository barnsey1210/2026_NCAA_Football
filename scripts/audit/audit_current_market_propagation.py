#!/usr/bin/env python3
"""Audit canonical current-market propagation by semantic concept."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/site/current_market_contract.json"
MATCHUPS = ROOT / "data/site/matchups_view.json"
ODDS = ROOT / "data/site/odds_screen_v2.json"
OUT = ROOT / "data/audits/current_market_propagation_audit.json"


def same(a, b):
    return a == b


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    matchups = json.loads(MATCHUPS.read_text())
    odds = json.loads(ODDS.read_text())

    c_by = {str(x["game_id"]): x for x in contract.get("games", [])}
    m_by = {str(x.get("game", {}).get("game_id")): x for x in matchups.get("games", [])}
    o_by = {str(x.get("game_id")): x for x in odds.get("games", [])}

    issues = []
    stale_displayed = 0

    for gid, c in c_by.items():
        m = m_by.get(gid)
        if m:
            status = c.get("availability_status")
            if m.get("market", {}).get("spread", {}).get("availability_status") != status:
                issues.append({"game_id": gid, "consumer": "matchups", "field": "availability_status"})
            c_home = (c.get("best", {}).get("home_spread") or {}).get("line")
            m_home = (m.get("market", {}).get("spread", {}).get("best_home") or {}).get("home_line")
            if not same(c_home, m_home):
                issues.append({"game_id": gid, "consumer": "matchups", "field": "best_home_spread", "contract": c_home, "consumer_value": m_home})
            c_away = (c.get("best", {}).get("away_spread") or {}).get("line")
            m_away_home_perspective = (m.get("market", {}).get("spread", {}).get("best_away") or {}).get("home_line")
            if c_away is not None and not same(-c_away, m_away_home_perspective):
                issues.append({"game_id": gid, "consumer": "matchups", "field": "best_away_spread", "contract": c_away, "consumer_value": m_away_home_perspective})
            if status == "MISSING":
                for section in ("spread", "total", "moneyline"):
                    values = m.get("market", {}).get(section, {})
                    if any(values.get(k) is not None for k in ("home_line", "line", "away_price", "home_price")):
                        stale_displayed += 1
                        issues.append({"game_id": gid, "consumer": "matchups", "field": section, "reason": "current value shown while contract is MISSING"})

        o = o_by.get(gid)
        if o:
            if o.get("current_market_status") != c.get("availability_status"):
                issues.append({"game_id": gid, "consumer": "odds", "field": "current_market_status"})
            for book, markets in c.get("quotes", {}).items():
                for market, sides in markets.items():
                    for side, q in sides.items():
                        oq = o.get("quotes", {}).get(book, {}).get(market, {}).get(side)
                        if not oq or oq.get("point") != q.get("line") or oq.get("price") != q.get("price"):
                            issues.append({"game_id": gid, "consumer": "odds", "field": f"{book}.{market}.{side}"})

    result = {
        "status": "PASS" if not issues and stale_displayed == 0 else "FAIL",
        "contract_games": len(c_by),
        "issues": issues[:500],
        "issue_count": len(issues),
        "stale_current_quotes_displayed": stale_displayed,
        "history_compared_to_current": False,
        "note": "Historical snapshots are intentionally audited separately from current/reference/best-side markets.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
