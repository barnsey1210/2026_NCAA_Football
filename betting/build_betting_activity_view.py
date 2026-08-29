#!/usr/bin/env python3
"""Normalize the current betting snapshot and link game wagers to canonical game_id values."""

from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.ncaaf_config import canonical_team
from betting.key_aware_spread_ev import SpreadEVCalculator

INFILE = ROOT / "data/bets/bets_enriched.csv"
GAME_VIEW = ROOT / "data/site/matchups_view.json"
OUT = ROOT / "data/site/betting_activity_view.json"
AUDIT = ROOT / "data/audits/betting_activity_view_audit.json"


def clean(value):
    value = "" if value is None else str(value).strip()
    return "" if value.lower() in {"nan", "none"} else value


def number(value):
    try:
        value = clean(value).replace("$", "").replace(",", "").replace("%", "")
        return float(value) if value else None
    except ValueError:
        return None


def boolean(value):
    return clean(value).lower() in {"true", "1", "yes", "y"}


def week_from_row(row):
    text = f"{clean(row.get('Bet Description'))} {clean(row.get('week_bucket'))}"
    match = re.search(r"\bweek\s*(\d+)\b", text, re.I)
    return int(match.group(1)) if match else None


def actor(row):
    source = clean(row.get("Source"))
    return {"type": "owned_wager", "name": "James", "source": source, "sheet_account": clean(row.get("Account"))}


def category(row):
    value = clean(row.get("clv_category")) or clean(row.get("market_category"))
    if value:
        return value
    desc = clean(row.get("Bet Description")).lower()
    return "Win Total" if "win total" in desc else "Conference Future" if "conf" in desc else clean(row.get("Bet Type")) or "Other"


def strategy_tags(row):
    tags = []
    source = clean(row.get("Source")).lower()
    if source == "powers":
        tags.append("Powers")
    if source in {"model", "open", "model / open"} or week_from_row(row) is not None or category(row) in {"Spread", "Game Total", "1H Spread", "1H Total", "2H Spread", "2H Total"}:
        tags.append("Model")
    return tags or ["Other"]


def bet_period(row, game=None):
    """Classify the wager into the page's canonical season-period controls."""
    week = game.get("week") if game else week_from_row(row)
    if week is not None:
        return "Conference Championships" if int(week) == 14 else f"Week {int(week)}"

    text = " ".join([
        clean(row.get("Bet Description")), clean(row.get("Bet Type")),
        clean(row.get("market_category")), clean(row.get("clv_category")),
    ]).lower()
    if any(term in text for term in ("bowl", "playoff", "national championship")):
        return "Bowl / Playoff"
    if any(term in text for term in ("win total", "conf title", "conference future", "heisman", "future")):
        return "Futures"
    return "Unassigned"


def read_games():
    payload = json.loads(GAME_VIEW.read_text())
    games = [record["game"] for record in payload.get("games", [])]

    index = {}
    by_id = {}

    for game in games:
        game_id = clean(game.get("game_id"))
        if game_id:
            by_id[game_id] = game

        for team in (game.get("away_team"), game.get("home_team")):
            index.setdefault(
                (canonical_team(team), game.get("week")),
                []
            ).append(game)

    return games, index, by_id


def game_match(row, index, by_id):
    # Prefer the canonical game already resolved by betting enrichment.
    canonical_game_id = clean(row.get("current_market_game_id"))

    if canonical_game_id:
        game = by_id.get(canonical_game_id)
        if game:
            return game, "canonical_market_game_id"

    market = category(row)

    if market not in {
        "Spread",
        "Game Total",
        "Moneyline",
        "1H Spread",
        "1H Total",
        "2H Spread",
        "2H Total",
    }:
        return None, "not_game_market"

    team = canonical_team(clean(row.get("team_guess")))
    week = week_from_row(row)

    candidates = (
        index.get((team, week), [])
        if team and week is not None
        else []
    )

    if len(candidates) == 1:
        return candidates[0], "exact_team_week"

    if not team:
        return None, "missing_team"

    if week is None:
        return None, "missing_week"

    return None, "ambiguous" if candidates else "no_match"


def main():
    if not INFILE.exists() or not GAME_VIEW.exists():
        raise SystemExit("Run the betting enrichment and Matchups view builders first.")
    _, game_index, games_by_id = read_games()
    with INFILE.open(newline="", encoding="utf-8-sig") as handle:
        source_rows = list(csv.DictReader(handle))

    spread_ev = SpreadEVCalculator(ROOT)

    records = []
    match_reasons = {}
    for position, row in enumerate(source_rows, 1):
        game, reason = game_match(
            row,
            game_index,
            games_by_id,
        )
        match_reasons[reason] = match_reasons.get(reason, 0) + 1
        bet_id = clean(row.get("bet_id")) or hashlib.sha256(f"{position}|{clean(row.get('Date'))}|{clean(row.get('Bet'))}".encode()).hexdigest()[:16]
        team = canonical_team(clean(row.get("team_guess")))

        market = category(row)
        is_open = boolean(row.get("is_open"))

        bet_line = number(row.get("bet_line"))
        bet_price = number(row.get("bet_price"))

        current_market_line = number(row.get("current_market_line"))
        current_market_price = number(row.get("current_market_price"))

        closing_market_line = number(row.get("closing_market_line"))
        closing_market_price = number(row.get("closing_market_price"))
        closing_frozen = boolean(row.get("closing_clv_frozen"))

        current_market_ev_pct = None
        final_clv_ev_pct = None
        ev_state = "UNAVAILABLE"
        spread_ev_method = None
        spread_ev_weakest_step_n = None

        # Full-game spreads only. The calibration is not valid for
        # 1H/2H spreads, totals, futures, or moneylines.
        if market == "Spread" and bet_line is not None and bet_price is not None:

            if (
                is_open
                and boolean(row.get("current_market_match"))
                and current_market_line is not None
                and current_market_price is not None
            ):
                priced = spread_ev.current_market_ev(
                    current_market_line,
                    current_market_price,
                    bet_line,
                    bet_price,
                )

                if priced is not None:
                    current_market_ev_pct = priced["ev_pct"]
                    spread_ev_weakest_step_n = priced["weakest_half_point_sample_n"]
                    spread_ev_method = "key_aware_current_market_relative_v1"
                    ev_state = "CURRENT"

            elif (
                not is_open
                and closing_frozen
                and closing_market_line is not None
            ):
                # Reproduce historical Final CLV EV methodology.
                # The close is treated as an efficient spread market;
                # actual ticket juice determines expected return.
                priced = spread_ev.ticket_ev(
                    closing_market_line,
                    bet_line,
                    bet_price,
                )

                if priced is not None:
                    final_clv_ev_pct = priced["ev_pct"]
                    spread_ev_weakest_step_n = priced["weakest_half_point_sample_n"]
                    spread_ev_method = "key_aware_final_clv_v1"
                    ev_state = "FINAL"

        legacy_ev_current_pct = number(row.get("ev_current_pct"))

        # Existing field remains for backwards compatibility.
        # Spread rows now receive the key-aware value appropriate to state.
        if market == "Spread":
            display_ev_pct = (
                current_market_ev_pct
                if ev_state == "CURRENT"
                else final_clv_ev_pct
                if ev_state == "FINAL"
                else None
            )
        else:
            display_ev_pct = legacy_ev_current_pct

        period = bet_period(row, game)
        is_graded = clean(row.get("status")) in {"Won", "Lost", "Push", "Cashout"}
        stake = number(row.get("stake"))
        realized_profit = number(row.get("realized_profit")) or 0
        records.append({
            "bet_id": bet_id, "game_id": game.get("game_id") if game else None,
            "game_link_status": reason, "week": game.get("week") if game else week_from_row(row),
            "game_date": game.get("date") if game else None,
            "away_team": game.get("away_team") if game else None, "home_team": game.get("home_team") if game else None,
            "actor": actor(row), "placed_at": clean(row.get("Date")), "status": clean(row.get("status")) or "Open",
            "is_open": is_open, "sport": clean(row.get("Sport")), "market": market,
            "strategy_tags": strategy_tags(row), "bet_period": period,
            "period_sort": int(game.get("week")) if game and game.get("week") is not None else week_from_row(row),
            "market_group": market, "is_future": period == "Futures", "is_graded": is_graded,
            "selection": clean(row.get("Bet")), "team": team or None, "side": clean(row.get("side")) or None,
            "line": bet_line, "price": bet_price,
            "sportsbook": clean(row.get("book_norm")) or clean(row.get("Sportsbook")), "stake": stake,
            "settled_risk": stake if is_graded else 0, "realized_profit": realized_profit, "realized_pl": realized_profit,

            "notes": clean(row.get("Notes")),

            "current_market_line": current_market_line,
            "current_market_price": current_market_price,
            "current_market_book": clean(row.get("current_market_book")),
            "current_market_match": boolean(row.get("current_market_match")),
            "line_clv_current": number(row.get("line_clv_current")),

            "closing_clv_frozen": closing_frozen,
            "closing_market_line": closing_market_line,
            "closing_market_price": closing_market_price,
            "closing_market_book": clean(row.get("closing_market_book")),
            "closing_line_clv": number(row.get("closing_line_clv")),

            "current_market_ev_pct": current_market_ev_pct,
            "final_clv_ev_pct": final_clv_ev_pct,
            "ev_state": ev_state,
            "spread_ev_method": spread_ev_method,
            "spread_ev_weakest_half_point_sample_n": spread_ev_weakest_step_n,
            "final_closing_price_assumption": -110 if ev_state == "FINAL" else None,

            "legacy_clv_pct_current": number(row.get("clv_pct_current")),
            "legacy_ev_current_pct": legacy_ev_current_pct,

            "clv_pct_current": number(row.get("clv_pct_current")),
            "clv_value": number(row.get("clv_pct_current")),
            "has_valid_closing_line": number(row.get("clv_pct_current")) is not None,
            "ev_current_pct": display_ev_pct,
            "current_ev": (stake or 0) * (display_ev_pct or 0) if is_open else 0,

            "beat_clv": clean(row.get("beat_clv")),
            "source_pulled_at": clean(row.get("pulled_at")),
        })

    open_rows = [row for row in records if row["is_open"]]
    def metrics(rows):
        open_group = [row for row in rows if row["is_open"]]
        settled = [row for row in rows if not row["is_open"]]
        settled_stake = sum(row["stake"] or 0 for row in settled)
        profit = sum(row["realized_profit"] or 0 for row in settled)
        clv = [row["clv_pct_current"] for row in rows if row["clv_pct_current"] is not None]
        ev = [row["ev_current_pct"] for row in rows if row["ev_current_pct"] is not None]
        return {"bets": len(rows), "open": len(open_group), "settled": len(settled),
                "amount_risked": round(sum(row["stake"] or 0 for row in rows), 2),
                "settled_risk": round(settled_stake, 2),
                "open_exposure": round(sum(row["stake"] or 0 for row in open_group), 2),
                "wins": sum(row["status"] == "Won" for row in settled), "losses": sum(row["status"] == "Lost" for row in settled),
                "pushes": sum(row["status"] == "Push" for row in settled), "profit": round(profit, 2),
                "roi": round(profit / settled_stake, 4) if settled_stake else None,
                "clv_matched": len(clv), "positive_clv": sum(value > 0 for value in clv),
                "positive_clv_pct": round(sum(value > 0 for value in clv) / len(clv), 4) if clv else None,
                "avg_clv_pct": round(sum(clv) / len(clv), 4) if clv else None,
                "avg_ev_pct": round(sum(ev) / len(ev), 4) if ev else None,
                "current_ev_dollars": round(sum((row["stake"] or 0) * (row["ev_current_pct"] or 0) for row in open_group), 2)}

    groups = {"Overall": metrics(records), "Powers": metrics([row for row in records if "Powers" in row["strategy_tags"]]),
              "Model": metrics([row for row in records if "Model" in row["strategy_tags"]])}
    market_groups = {name: metrics([row for row in records if row["market"] == name]) for name in sorted({row["market"] for row in records})}
    week_groups = {}
    for week in sorted({row["week"] for row in records if row["week"] is not None}):
        week_groups[f"Week {week}"] = metrics([row for row in records if row["week"] == week])
    period_groups = {
        period: metrics([row for row in records if row["bet_period"] == period])
        for period in ["Futures", *sorted({row["bet_period"] for row in records if row["bet_period"].startswith("Week ")}, key=lambda value: int(value.split()[-1])), "Conference Championships", "Bowl / Playoff", "Unassigned"]
        if any(row["bet_period"] == period for row in records)
    }
    summary = {
        "records": len(records), "open": len(open_rows),
        "owned_open": len(open_rows), "tracked_open": 0, "unassigned_open": 0,
        "game_linked": sum(bool(row["game_id"]) for row in records),
        "open_exposure": round(sum(row["stake"] or 0 for row in open_rows), 2),
    }
    history_path = ROOT / "data/bets/betting_performance_history.csv"
    history = []
    if history_path.exists():
        with history_path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                history.append({key: number(value) if key not in {"snapshot_at", "season_phase"} else clean(value) for key, value in row.items()})
    built_at = datetime.now(timezone.utc).isoformat()
    payload = {"schema_version": "betting-activity-v1", "built_at": built_at, "summary": summary,
               "strategy_metrics": groups, "market_metrics": market_groups, "week_metrics": week_groups,
               "period_metrics": period_groups,
               "performance_history": history, "records": records}
    audit = {"built_at": built_at, "summary": summary, "game_match_reasons": match_reasons,
             "policy": {"all_sheet_rows": "owned_wager", "strategy_tags": "Powers and Model are independent, non-exclusive tags"}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
