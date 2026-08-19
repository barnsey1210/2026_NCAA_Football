#!/usr/bin/env python3
"""Audit canonical current-market propagation by semantic concept."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/site/current_market_contract.json"
MATCHUPS = ROOT / "data/site/matchups_view.json"
ODDS = ROOT / "data/site/odds_screen_v2.json"
OUT = ROOT / "data/audits/current_market_propagation_audit.json"


def same(a, b):
    return a == b


BETTABLE_BOOKS = {
    "DraftKings",
    "FanDuel",
    "BetMGM",
    "Caesars",
}

EXCHANGE_BOOKS = {
    "Novig",
    "ProphetX",
    "Kalshi",
}


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def expected_best(quotes, market, side, allowed_books):
    candidates = []

    for book, book_data in quotes.items():
        if book not in allowed_books:
            continue

        q = book_data.get(market, {}).get(side)
        if not q or q.get("freshness_status") not in {"LIVE", "BACKUP_SOURCE"}:
            continue

        line = number(q.get("line"))
        price = number(q.get("price"))

        if market == "moneyline":
            if price is not None:
                candidates.append(((price,), q))

        elif line is not None:
            if market == "spread":
                score = (
                    line,
                    price if price is not None else -100000,
                )
            elif side == "over":
                score = (
                    -line,
                    price if price is not None else -100000,
                )
            else:
                score = (
                    line,
                    price if price is not None else -100000,
                )

            candidates.append((score, q))

    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    matchups = json.loads(MATCHUPS.read_text())
    odds = json.loads(ODDS.read_text())

    c_by = {str(x["game_id"]): x for x in contract.get("games", [])}
    m_by = {str(x.get("game", {}).get("game_id")): x for x in matchups.get("games", [])}
    o_by = {str(x.get("game_id")): x for x in odds.get("games", [])}

    issues = []
    stale_displayed = 0

    sportsbook_selection_counts = Counter()
    exchange_selection_counts = Counter()
    caesars_source_counts = Counter()
    caesars_games = set()

    checks = [
        ("away_spread", "spread", "away"),
        ("home_spread", "spread", "home"),
        ("over", "total", "over"),
        ("under", "total", "under"),
        ("away_moneyline", "moneyline", "away"),
        ("home_moneyline", "moneyline", "home"),
    ]

    for gid, c in c_by.items():
        quotes = c.get("quotes", {})

        # Validate canonical fast-actionable sportsbook and exchange reducers.
        for field, market, side in checks:
            actual_book = c.get("best_sportsbook", {}).get(field)
            expected_book = expected_best(
                quotes,
                market,
                side,
                BETTABLE_BOOKS,
            )

            if actual_book != expected_book:
                issues.append({
                    "game_id": gid,
                    "consumer": "contract",
                    "field": f"best_sportsbook.{field}",
                    "reason": "selection_mismatch",
                })

            if actual_book:
                selected = actual_book.get("sportsbook")
                sportsbook_selection_counts[selected] += 1

                if selected not in BETTABLE_BOOKS:
                    issues.append({
                        "game_id": gid,
                        "consumer": "contract",
                        "field": f"best_sportsbook.{field}",
                        "reason": "invalid_fast_sportsbook",
                        "sportsbook": selected,
                    })

                if actual_book.get("freshness_status") not in {"LIVE", "BACKUP_SOURCE"}:
                    issues.append({
                        "game_id": gid,
                        "consumer": "contract",
                        "field": f"best_sportsbook.{field}",
                        "reason": "non_live_quote_selected",
                    })

            actual_exchange = c.get("best_exchange", {}).get(field)
            expected_exchange = expected_best(
                quotes,
                market,
                side,
                EXCHANGE_BOOKS,
            )

            if actual_exchange != expected_exchange:
                issues.append({
                    "game_id": gid,
                    "consumer": "contract",
                    "field": f"best_exchange.{field}",
                    "reason": "selection_mismatch",
                })

            if actual_exchange:
                selected = actual_exchange.get("sportsbook")
                exchange_selection_counts[selected] += 1

                if selected not in EXCHANGE_BOOKS:
                    issues.append({
                        "game_id": gid,
                        "consumer": "contract",
                        "field": f"best_exchange.{field}",
                        "reason": "invalid_exchange",
                        "sportsbook": selected,
                    })

                if actual_exchange.get("freshness_status") not in {"LIVE", "BACKUP_SOURCE"}:
                    issues.append({
                        "game_id": gid,
                        "consumer": "contract",
                        "field": f"best_exchange.{field}",
                        "reason": "non_live_quote_selected",
                    })

        # Caesars is preserved in the canonical quote tree but currently
        # excluded from fast-actionable sportsbook selection.
        caesars = quotes.get("Caesars", {})
        if caesars:
            caesars_games.add(gid)

        for market_data in caesars.values():
            for q in market_data.values():
                caesars_source_counts[q.get("source") or "UNKNOWN"] += 1

        m = m_by.get(gid)
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
            # Odds now consumes the canonical market contract directly.
            # current_market_status was an adapter-era field and is no longer
            # required by the consumer schema. If a status field is exposed,
            # validate it; otherwise quote parity is the authoritative check.
            consumer_status = o.get("availability_status")
            if consumer_status is None:
                consumer_status = o.get("current_market_status")
            if consumer_status is not None and consumer_status != c.get("availability_status"):
                issues.append({"game_id": gid, "consumer": "odds", "field": "availability_status", "contract": c.get("availability_status"), "consumer_value": consumer_status})

            if c.get("availability_status") == "MISSING" and o.get("quotes"):
                stale_displayed += 1
                issues.append({"game_id": gid, "consumer": "odds", "field": "quotes", "reason": "quotes shown while contract is MISSING"})

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
        "market_groups": contract.get("market_groups", {}),
        "fast_actionable_sportsbook_selection_counts": dict(
            sportsbook_selection_counts
        ),
        "exchange_selection_counts": dict(exchange_selection_counts),
        "caesars_games_preserved": len(caesars_games),
        "caesars_quote_source_counts": dict(caesars_source_counts),
        "note": (
            "Historical snapshots are intentionally audited separately from "
            "current/reference/best-side markets. Caesars quotes may remain "
            "preserved from Action Network but are excluded from the fast "
            "actionable sportsbook reducer until a fast-refresh source exists."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
