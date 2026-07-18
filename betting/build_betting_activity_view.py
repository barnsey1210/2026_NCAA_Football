#!/usr/bin/env python3
"""Normalize the current betting snapshot and link game wagers to canonical game_id values."""

from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.ncaaf_config import canonical_team

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
    if clean(row.get("Source")).lower() == "powers":
        tags.append("Powers")
    if week_from_row(row) is not None or category(row) in {"Spread", "Game Total", "1H Spread", "1H Total", "2H Spread", "2H Total"}:
        tags.append("Model")
    return tags or ["Other"]


def read_games():
    payload = json.loads(GAME_VIEW.read_text())
    games = [record["game"] for record in payload.get("games", [])]
    index = {}
    for game in games:
        for team in (game.get("away_team"), game.get("home_team")):
            index.setdefault((canonical_team(team), game.get("week")), []).append(game)
    return games, index


def game_match(row, index):
    market = category(row)
    if market not in {"Spread", "Game Total", "1H Spread", "1H Total", "2H Spread", "2H Total"}:
        return None, "not_game_market"
    team = canonical_team(clean(row.get("team_guess")))
    week = week_from_row(row)
    candidates = index.get((team, week), []) if team and week is not None else []
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
    _, game_index = read_games()
    with INFILE.open(newline="", encoding="utf-8-sig") as handle:
        source_rows = list(csv.DictReader(handle))

    records = []
    match_reasons = {}
    for position, row in enumerate(source_rows, 1):
        game, reason = game_match(row, game_index)
        match_reasons[reason] = match_reasons.get(reason, 0) + 1
        bet_id = clean(row.get("bet_id")) or hashlib.sha256(f"{position}|{clean(row.get('Date'))}|{clean(row.get('Bet'))}".encode()).hexdigest()[:16]
        team = canonical_team(clean(row.get("team_guess")))
        records.append({
            "bet_id": bet_id, "game_id": game.get("game_id") if game else None,
            "game_link_status": reason, "week": game.get("week") if game else week_from_row(row),
            "game_date": game.get("date") if game else None,
            "away_team": game.get("away_team") if game else None, "home_team": game.get("home_team") if game else None,
            "actor": actor(row), "placed_at": clean(row.get("Date")), "status": clean(row.get("status")) or "Open",
            "is_open": boolean(row.get("is_open")), "sport": clean(row.get("Sport")), "market": category(row),
            "strategy_tags": strategy_tags(row),
            "selection": clean(row.get("Bet")), "team": team or None, "side": clean(row.get("side")) or None,
            "line": number(row.get("bet_line")), "price": number(row.get("bet_price")),
            "sportsbook": clean(row.get("book_norm")) or clean(row.get("Sportsbook")), "stake": number(row.get("stake")),
            "realized_profit": number(row.get("realized_profit")) or 0,
            "notes": clean(row.get("Notes")), "current_market_line": number(row.get("current_market_line")),
            "current_market_price": number(row.get("current_market_price")), "current_market_book": clean(row.get("current_market_book")),
            "clv_pct_current": number(row.get("clv_pct_current")), "ev_current_pct": number(row.get("ev_current_pct")),
            "beat_clv": clean(row.get("beat_clv")), "source_pulled_at": clean(row.get("pulled_at")),
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
