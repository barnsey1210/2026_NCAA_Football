#!/usr/bin/env python3
"""Build the scoped production Odds Screen V2 game payload."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from team_identity import team_logo_path

ROOT = Path(__file__).resolve().parents[2]
ACTION = ROOT / "data/odds/actionnetwork_ncaaf_game_lines_2026.csv"
SGO = ROOT / "data/markets/sgo/sgo_ncaaf_game_odds.csv"
CFBD = ROOT / "data/odds/cfbd_lines_2026.csv"
HISTORY = ROOT / "data/site/matchup_line_history.json"
MATCHUPS = ROOT / "data/site/matchups_view.json"
OUT = ROOT / "data/site/odds_screen_v2.json"
AUDIT = ROOT / "data/audits/odds_screen_v2_build_audit.json"
BOOKS = ("DraftKings", "FanDuel", "BetMGM", "Caesars")


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def source_build_time(paths: tuple[Path, ...]) -> str:
    """Return a stable build timestamp derived from the newest canonical input."""
    modified = max(path.stat().st_mtime for path in paths if path.exists())
    return datetime.fromtimestamp(modified, timezone.utc).isoformat()


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def integer(value):
    val = number(value)
    return int(val) if val is not None else None


def norm_team(value: str | None) -> str:
    value = (value or "").lower().replace("&", "and")
    value = value.replace("hawai'i", "hawaii").replace("miami (fl)", "miami-fl")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    aliases = {
        "miami fl": "miami florida", "miami": "miami florida",
        "ole miss": "mississippi", "ucf": "central florida",
        "utsa": "texas san antonio", "uconn": "connecticut",
        "umass": "massachusetts", "southern miss": "southern mississippi",
    }
    cleaned = " ".join(value.split())
    return aliases.get(cleaned, cleaned)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def matchup_key(date, away, home):
    return str(date or "")[:10], norm_team(away), norm_team(home)


def best_flags(quotes: dict, market: str) -> dict:
    result = {book: {side: False for side in ("away", "home", "over", "under")} for book in BOOKS}
    sides = ("away", "home") if market in ("spread", "moneyline") else ("over", "under")
    for side in sides:
        candidates = []
        for book, book_data in quotes.items():
            q = book_data.get(market, {}).get(side)
            if not q or q.get("valid") is False:
                continue
            point, price = q.get("point"), q.get("price")
            if market == "moneyline":
                if price is not None:
                    candidates.append((price, book))
            elif point is not None:
                if market == "spread":
                    score = (point, price if price is not None else -100000)
                elif side == "over":
                    score = (-point, price if price is not None else -100000)
                else:
                    score = (point, price if price is not None else -100000)
                candidates.append((score, book))
        if len(candidates) < 2:
            continue
        winning = max(x[0] for x in candidates)
        for score, book in candidates:
            if score == winning:
                result[book][side] = True
    return result


def history_rows(points: list[dict], market: str) -> list[dict]:
    by_day = {}
    for point in points or []:
        day = str(point.get("snapshot_date") or point.get("snapshot_ts") or "")[:10]
        if not day:
            continue
        if market == "spread" and number(point.get("market_spread_home")) is None:
            continue
        if market == "total" and number(point.get("market_total")) is None:
            continue
        by_day[day] = point
    chronological = [by_day[d] for d in sorted(by_day)]
    output = []
    previous = None
    for point in chronological:
        if market == "spread":
            current = number(point.get("market_spread_home"))
            movement = None if previous is None else current - previous
            item = {
                "date": str(point.get("snapshot_date") or point.get("snapshot_ts"))[:10],
                "timestamp": point.get("snapshot_ts"),
                "source": point.get("market_spread_book") or point.get("source") or point.get("snapshot_label"),
                "away_point": -current,
                "away_price": number(point.get("market_spread_price")),
                "home_point": current,
                "home_price": number(point.get("market_spread_price")),
                "movement_home": movement,
            }
        else:
            current = number(point.get("market_total"))
            movement = None if previous is None else current - previous
            item = {
                "date": str(point.get("snapshot_date") or point.get("snapshot_ts"))[:10],
                "timestamp": point.get("snapshot_ts"),
                "source": point.get("market_total_book") or point.get("source") or point.get("snapshot_label"),
                "total": current,
                "over_price": number(point.get("market_total_over_price")),
                "under_price": number(point.get("market_total_under_price")),
                "movement": movement,
            }
        output.append(item)
        previous = current
    return list(reversed(output[-7:]))


def main() -> None:
    input_paths = [ACTION, SGO, CFBD, HISTORY, MATCHUPS]
    missing = [str(p.relative_to(ROOT)) for p in input_paths if not p.exists()]
    if missing:
        raise SystemExit(f"Missing required read-only inputs: {', '.join(missing)}")

    action_rows = rows(ACTION)
    sgo_rows = rows(SGO)
    cfbd_rows = rows(CFBD)
    histories = json.loads(HISTORY.read_text())
    matchup_payload = json.loads(MATCHUPS.read_text())
    site_games = matchup_payload.get("games", [])

    site_by_key = {}
    site_by_pair = defaultdict(list)
    for obj in site_games:
        game = obj.get("game", {})
        site_by_key[matchup_key(game.get("date"), game.get("away_team"), game.get("home_team"))] = obj
        site_by_pair[(norm_team(game.get("away_team")), norm_team(game.get("home_team")))].append(obj)

    sgo_by_key = {matchup_key(r.get("date"), r.get("away_team"), r.get("home_team")): r for r in sgo_rows}
    sgo_by_pair = defaultdict(list)
    for row in sgo_rows:
        sgo_by_pair[(norm_team(row.get("away_team")), norm_team(row.get("home_team")))].append(row)
    cfbd_by_key = {matchup_key(r.get("date"), r.get("away_team"), r.get("home_team")): r for r in cfbd_rows}
    cfbd_by_pair = defaultdict(list)
    for row in cfbd_rows:
        cfbd_by_pair[(norm_team(row.get("away_team")), norm_team(row.get("home_team")))].append(row)
    grouped = defaultdict(list)
    for row in action_rows:
        if row.get("book") in BOOKS and row.get("market") in {"spread", "total", "moneyline"}:
            grouped[matchup_key(row.get("date"), row.get("away_team"), row.get("home_team"))].append(row)

    games = []
    unmatched = []
    malformed_spread_pairs = []
    book_market_games = {book: defaultdict(set) for book in BOOKS}
    coverage = Counter()

    for key, market_rows in sorted(grouped.items()):
        first = market_rows[0]
        pair = (key[1], key[2])
        site_obj = site_by_key.get(key)
        if not site_obj and len(site_by_pair.get(pair, [])) == 1:
            site_obj = site_by_pair[pair][0]
        if not site_obj:
            unmatched.append({"date": key[0], "away_team": first.get("away_team"), "home_team": first.get("home_team"), "reason": "No exact normalized date/team match in matchups_view.json"})
        site_game = (site_obj or {}).get("game", {})
        game_id = site_game.get("game_id")
        source_game_id = first.get("game_id")
        quotes = {book: {"spread": {}, "total": {}, "moneyline": {}} for book in BOOKS}
        timestamps = []
        for row in market_rows:
            book, market, side = row.get("book"), row.get("market"), row.get("side")
            if book not in BOOKS or side not in {"away", "home", "over", "under"}:
                continue
            quote = {"point": number(row.get("point")), "price": number(row.get("price")), "status": row.get("line_status"), "updated_at": row.get("pulled_at")}
            quotes[book][market][side] = quote
            book_market_games[book][market].add(source_game_id)
            if row.get("pulled_at"):
                timestamps.append(row["pulled_at"])

        # A two-sided spread must be complementary. Preserve the source values
        # for auditability, but do not present or compare a malformed pair.
        for book in BOOKS:
            away_quote = quotes[book]["spread"].get("away")
            home_quote = quotes[book]["spread"].get("home")
            away_point = number((away_quote or {}).get("point"))
            home_point = number((home_quote or {}).get("point"))
            if away_point is not None and home_point is not None and abs(away_point + home_point) > 0.01:
                reason = "Away and home spread points are not complementary"
                away_quote["valid"] = False
                away_quote["validation_issue"] = reason
                home_quote["valid"] = False
                home_quote["validation_issue"] = reason
                malformed_spread_pairs.append({
                    "source_game_id": source_game_id,
                    "date": key[0],
                    "away_team": first.get("away_team"),
                    "home_team": first.get("home_team"),
                    "book": book,
                    "away_point": away_point,
                    "home_point": home_point,
                    "action": "Retained in payload but excluded from display and best-line comparison",
                })

        sgo = sgo_by_key.get(key, {})
        if not sgo and len(sgo_by_pair.get(pair, [])) == 1:
            sgo = sgo_by_pair[pair][0]
        cfbd = cfbd_by_key.get(key, {})
        if not cfbd and len(cfbd_by_pair.get(pair, [])) == 1:
            cfbd = cfbd_by_pair[pair][0]
        points = histories.get(game_id, []) if game_id else []
        spread_history = history_rows(points, "spread")
        total_history = history_rows(points, "total")
        first_spread = spread_history[-1] if spread_history else None
        first_total = total_history[-1] if total_history else None
        open_home = number(sgo.get("market_spread_open_home"))
        if open_home is None:
            open_home = number(cfbd.get("spread_open"))
        open_total = number(sgo.get("market_total_open"))
        if open_total is None:
            open_total = number(cfbd.get("total_open"))
        opener = {
            "spread": {
                "away": {"point": -open_home if open_home is not None else None, "price": first_spread.get("away_price") if first_spread else None},
                "home": {"point": open_home, "price": first_spread.get("home_price") if first_spread else None},
                "book": (first_spread or {}).get("source") or sgo.get("market_spread_book") or cfbd.get("book"),
                "captured_at": (first_spread or {}).get("timestamp") or (first_spread or {}).get("date") or sgo.get("pulled_at") or cfbd.get("pulled_at"),
                "note": "Earliest retained local daily snapshot; sportsbook actual posting time may be earlier" if first_spread else "Source opening field; opening price unavailable",
            },
            "total": {
                "over": {"point": open_total, "price": first_total.get("over_price") if first_total else None},
                "under": {"point": open_total, "price": first_total.get("under_price") if first_total else None},
                "book": (first_total or {}).get("source") or sgo.get("market_total_book") or cfbd.get("book"),
                "captured_at": (first_total or {}).get("timestamp") or (first_total or {}).get("date") or sgo.get("pulled_at") or cfbd.get("pulled_at"),
                "note": "Earliest retained local daily snapshot; sportsbook actual posting time may be earlier" if first_total else "Source opening field; opening prices unavailable",
            },
            "moneyline": {"away": None, "home": None, "book": None, "captured_at": None, "note": "No opening-moneyline field or daily moneyline history is retained"},
        }

        available = {
            market: any(quotes[b][market] for b in BOOKS)
            for market in ("spread", "total", "moneyline")
        }
        for market, present in available.items():
            if present:
                coverage[market] += 1
        if open_home is not None:
            coverage["spread_opener"] += 1
        if open_total is not None:
            coverage["total_opener"] += 1
        if spread_history:
            coverage["spread_history"] += 1
        if total_history:
            coverage["total_history"] += 1

        flags = {}
        for market in ("spread", "total", "moneyline"):
            for book, sides in best_flags(quotes, market).items():
                flags.setdefault(book, {}).setdefault(market, {}).update(sides)

        canonical_away = site_game.get("away_team") or first.get("away_team")
        canonical_home = site_game.get("home_team") or first.get("home_team")
        games.append({
            "game_id": game_id or f"action-{source_game_id}",
            "source_game_id": source_game_id,
            "date": first.get("date"),
            "week": integer(first.get("week")),
            "start_time_utc": first.get("commence_time"),
            "away_team": canonical_away,
            "home_team": canonical_home,
            "away_logo": team_logo_path(canonical_away),
            "home_logo": team_logo_path(canonical_home),
            "matchup_url": f"openers.html?game_id={game_id}" if game_id else None,
            "quotes": quotes,
            "best_flags": flags,
            "opener": opener,
            "history": {"spread": spread_history, "total": total_history, "moneyline": []},
            "moneyline_history_available": False,
            "source_updated_at": max(timestamps) if timestamps else None,
            "data_quality_notes": (["No exact V2 game match; board uses Action Network identity"] if not site_obj else []) + (["No normalized spread/total history match"] if not points else []) + (["One or more malformed current spread pairs were excluded"] if any(x["source_game_id"] == source_game_id for x in malformed_spread_pairs) else []),
        })

    built_at = source_build_time((ACTION, SGO, CFBD, HISTORY, MATCHUPS))
    payload = {
        "schema_version": "odds_screen_v2.production.1",
        "prototype_only": False,
        "built_at": built_at,
        "books": list(BOOKS),
        "book_logos": {book: f"logos/books/{book.lower()}.png" for book in BOOKS},
        "moneyline_history": {"available": False, "message": "Daily moneyline history is not yet available in the current history pipeline.", "required_future_fields": ["snapshot_ts", "game_id", "book", "away_moneyline", "home_moneyline", "line_status"]},
        "games": games,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(OUT, payload)

    counts = {
        "games": len(games),
        "spread_coverage": coverage["spread"],
        "total_coverage": coverage["total"],
        "moneyline_coverage": coverage["moneyline"],
        "spread_opener_coverage": coverage["spread_opener"],
        "total_opener_coverage": coverage["total_opener"],
        "spread_history_coverage": coverage["spread_history"],
        "total_history_coverage": coverage["total_history"],
        "per_book_game_coverage": {
            book: {market: len(game_ids) for market, game_ids in book_market_games[book].items()}
            for book in BOOKS
        },
    }
    audit = {
        "built_at": built_at,
        "prototype_only": False,
        "files_read": [str(p.relative_to(ROOT)) for p in input_paths],
        "files_written": [str(OUT.relative_to(ROOT)), str(AUDIT.relative_to(ROOT))],
        "production_files_changed": False,
        "production_scope_confirmation": "Builder writes only the production Odds V2 payload and its build audit; publication remains a separate controlled step.",
        "coverage_counts": counts,
        "books_detected": list(BOOKS),
        "fields_used": {
            str(ACTION.relative_to(ROOT)): ["game_id", "season", "week", "commence_time", "date", "away_team", "home_team", "book", "market", "side", "point", "price", "line_status", "pulled_at"],
            str(SGO.relative_to(ROOT)): ["date", "away_team", "home_team", "market_spread_open_home", "market_total_open", "market_spread_book", "market_total_book", "pulled_at"],
            str(CFBD.relative_to(ROOT)): ["date", "away_team", "home_team", "spread_open", "total_open", "book", "pulled_at"],
            str(HISTORY.relative_to(ROOT)): ["snapshot_date", "snapshot_ts", "market_spread_home", "market_spread_price", "market_spread_book", "market_total", "market_total_over_price", "market_total_under_price", "market_total_book", "source"],
            str(MATCHUPS.relative_to(ROOT)): ["game.game_id", "game.date", "game.away_team", "game.home_team"],
        },
        "moneyline_history_availability": {"available": False, "reason": "Current Action Network and SGO files retain current moneyline quotes, while matchup_line_history.json contains spread and total fields only."},
        "prototype_ui_features": {
            "combined_line_price_formatting": True,
            "week_buttons": True,
            "default_selected_week": 1 if any(game.get("week") == 1 for game in games) else min((game.get("week") for game in games if game.get("week") is not None), default=None),
            "sortable_matchup_header": ["away_asc", "away_desc", "home_asc", "home_desc"],
            "sortable_start_header": ["earliest_first", "latest_first"],
            "spread_history_timestamp_coverage": {
                "snapshots": sum(len(game["history"]["spread"]) for game in games),
                "with_full_timestamp": sum(bool(row.get("timestamp")) for game in games for row in game["history"]["spread"]),
            },
            "total_history_timestamp_coverage": {
                "snapshots": sum(len(game["history"]["total"]) for game in games),
                "with_full_timestamp": sum(bool(row.get("timestamp")) for game in games for row in game["history"]["total"]),
            },
            "production_files_unchanged": True,
        },
        "unmatched_games_or_team_name_mismatches": unmatched,
        "malformed_current_spread_pairs": malformed_spread_pairs,
        "warnings": ["Opening capture time is the earliest locally retained snapshot or source pull, not guaranteed sportsbook posting time.", "Opening prices are null when an opener-specific price was not retained."] + ([f"{len(unmatched)} current-odds games did not match a V2 site game exactly"] if unmatched else []) + ([f"{len(malformed_spread_pairs)} malformed current spread pairs were excluded from display and best-line comparison"] if malformed_spread_pairs else []),
    }
    atomic_json(AUDIT, audit)

    print("ODDS SCREEN V2 BUILD")
    for key, value in counts.items():
        print(f"{key}: {value}")
    print(f"moneyline_history_available: false")
    print(f"payload: {OUT.relative_to(ROOT)}")
    print(f"audit: {AUDIT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
