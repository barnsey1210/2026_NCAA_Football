#!/usr/bin/env python3
"""Build the production Odds Screen V2 payload from the canonical market contract.

Current-market source selection is owned exclusively by:
    data/site/current_market_contract.json

This page adapter does not select among live providers. It formats the canonical
current-market contract for the Odds page, while retaining the existing separate
opener/history inputs.
"""

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

CURRENT_MARKET = ROOT / "data/site/current_market_contract.json"
CFBD = ROOT / "data/odds/cfbd_lines_2026.csv"
HISTORY = ROOT / "data/site/matchup_line_history.json"

OUT = ROOT / "data/site/odds_screen_v2.json"
AUDIT = ROOT / "data/audits/odds_screen_v2_build_audit.json"


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


def csv_rows(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def integer(value):
    value = number(value)
    return int(value) if value is not None else None


def norm_team(value: str | None) -> str:
    value = (value or "").lower().replace("&", "and")
    value = value.replace("hawai'i", "hawaii").replace("miami (fl)", "miami-fl")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    aliases = {
        "miami fl": "miami florida",
        "miami": "miami florida",
        "ole miss": "mississippi",
        "ucf": "central florida",
        "utsa": "texas san antonio",
        "uconn": "connecticut",
        "umass": "massachusetts",
        "southern miss": "southern mississippi",
    }
    cleaned = " ".join(value.split())
    return aliases.get(cleaned, cleaned)


def matchup_key(date, away, home):
    return str(date or "")[:10], norm_team(away), norm_team(home)


def source_build_time(paths: tuple[Path, ...]) -> str:
    modified = max(path.stat().st_mtime for path in paths if path.exists())
    return datetime.fromtimestamp(modified, timezone.utc).isoformat()


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
                "source": (
                    point.get("market_spread_book")
                    or point.get("source")
                    or point.get("snapshot_label")
                ),
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
                "source": (
                    point.get("market_total_book")
                    or point.get("source")
                    or point.get("snapshot_label")
                ),
                "total": current,
                "over_price": number(point.get("market_total_over_price")),
                "under_price": number(point.get("market_total_under_price")),
                "movement": movement,
            }
        output.append(item)
        previous = current

    return list(reversed(output[-7:]))


def best_flags(quotes: dict, books: list[str], market: str) -> dict:
    result = {
        book: {side: False for side in ("away", "home", "over", "under")}
        for book in books
    }
    sides = ("away", "home") if market in ("spread", "moneyline") else ("over", "under")

    for side in sides:
        candidates = []
        for book in books:
            q = quotes.get(book, {}).get(market, {}).get(side)
            if not q:
                continue

            point = number(q.get("point"))
            price = number(q.get("price"))

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

        # Preserve previous UI behavior: only flag a "best" when comparison exists.
        if len(candidates) < 2:
            continue

        winning = max(score for score, _ in candidates)
        for score, book in candidates:
            if score == winning:
                result[book][side] = True

    return result


def contract_quote_to_screen(q: dict) -> dict:
    return {
        "point": number(q.get("line")),
        "price": number(q.get("price")),
        "status": q.get("freshness_status"),
        "updated_at": q.get("source_updated_at"),
        "source": q.get("source"),
        "venue_type": q.get("venue_type"),
    }


def main() -> None:
    input_paths = [CURRENT_MARKET, CFBD, HISTORY]
    missing = [str(p.relative_to(ROOT)) for p in input_paths if not p.exists()]
    if missing:
        raise SystemExit(f"Missing required read-only inputs: {', '.join(missing)}")

    contract = json.loads(CURRENT_MARKET.read_text())
    if contract.get("market_source_policy") != "theodds-primary-action-fallback-v1":
        raise SystemExit(
            "Unexpected current-market source policy: "
            f"{contract.get('market_source_policy')!r}"
        )

    target_venues = contract.get("target_venues") or []
    books = [row.get("name") for row in target_venues if row.get("name")]
    if not books:
        books = list(contract.get("target_sportsbooks") or [])
    if not books:
        raise SystemExit("Canonical current-market contract has no configured venues.")

    venue_types = {
        row.get("name"): row.get("venue_type")
        for row in target_venues
        if row.get("name")
    }

    histories = json.loads(HISTORY.read_text())
    cfbd_rows = csv_rows(CFBD)

    cfbd_by_key = {
        matchup_key(r.get("date"), r.get("away_team"), r.get("home_team")): r
        for r in cfbd_rows
    }
    cfbd_by_pair = defaultdict(list)
    for row in cfbd_rows:
        cfbd_by_pair[
            (norm_team(row.get("away_team")), norm_team(row.get("home_team")))
        ].append(row)

    games = []
    coverage = Counter()
    book_market_games = {book: defaultdict(set) for book in books}
    malformed_spread_pairs = []

    contract_games = contract.get("games") or []

    # Odds page shows games with at least one live current quote.
    live_games = [
        game for game in contract_games
        if game.get("availability_status") == "LIVE" and game.get("quotes")
    ]

    for market_game in live_games:
        game_id = str(market_game.get("game_id") or "")
        date = str(market_game.get("date") or "")[:10]
        away = market_game.get("away_team")
        home = market_game.get("home_team")
        key = matchup_key(date, away, home)
        pair = (key[1], key[2])

        cfbd = cfbd_by_key.get(key, {})
        if not cfbd and len(cfbd_by_pair.get(pair, [])) == 1:
            cfbd = cfbd_by_pair[pair][0]

        quotes = {
            book: {"spread": {}, "total": {}, "moneyline": {}}
            for book in books
        }
        timestamps = []

        for book, book_data in (market_game.get("quotes") or {}).items():
            if book not in quotes:
                # Canonical contract should govern the displayed universe.
                continue

            for market in ("spread", "total", "moneyline"):
                for side, q in (book_data.get(market) or {}).items():
                    if side not in {"away", "home", "over", "under"}:
                        continue
                    screen_q = contract_quote_to_screen(q)
                    quotes[book][market][side] = screen_q
                    book_market_games[book][market].add(game_id)
                    if screen_q.get("updated_at"):
                        timestamps.append(screen_q["updated_at"])

        # Defensive validation remains in the page adapter.
        for book in books:
            away_quote = quotes[book]["spread"].get("away")
            home_quote = quotes[book]["spread"].get("home")
            away_point = number((away_quote or {}).get("point"))
            home_point = number((home_quote or {}).get("point"))
            if (
                away_point is not None
                and home_point is not None
                and abs(away_point + home_point) > 0.01
            ):
                reason = "Away and home spread points are not complementary"
                malformed_spread_pairs.append(
                    {
                        "game_id": game_id,
                        "date": date,
                        "away_team": away,
                        "home_team": home,
                        "book": book,
                        "away_point": away_point,
                        "home_point": home_point,
                        "action": "Excluded from Odds Screen display/best-line comparison",
                    }
                )
                quotes[book]["spread"] = {}

        points = histories.get(game_id, []) if game_id else []
        spread_history = history_rows(points, "spread")
        total_history = history_rows(points, "total")
        first_spread = spread_history[-1] if spread_history else None
        first_total = total_history[-1] if total_history else None

        open_home = number(cfbd.get("spread_open"))
        open_total = number(cfbd.get("total_open"))

        opener = {
            "spread": {
                "away": {
                    "point": -open_home if open_home is not None else None,
                    "price": first_spread.get("away_price") if first_spread else None,
                },
                "home": {
                    "point": open_home,
                    "price": first_spread.get("home_price") if first_spread else None,
                },
                "book": (first_spread or {}).get("source") or cfbd.get("book"),
                "captured_at": (
                    (first_spread or {}).get("timestamp")
                    or (first_spread or {}).get("date")
                    or cfbd.get("pulled_at")
                ),
                "note": (
                    "Earliest retained local daily snapshot; sportsbook actual posting time may be earlier"
                    if first_spread
                    else "Source opening field; opening price unavailable"
                ),
            },
            "total": {
                "over": {
                    "point": open_total,
                    "price": first_total.get("over_price") if first_total else None,
                },
                "under": {
                    "point": open_total,
                    "price": first_total.get("under_price") if first_total else None,
                },
                "book": (first_total or {}).get("source") or cfbd.get("book"),
                "captured_at": (
                    (first_total or {}).get("timestamp")
                    or (first_total or {}).get("date")
                    or cfbd.get("pulled_at")
                ),
                "note": (
                    "Earliest retained local daily snapshot; sportsbook actual posting time may be earlier"
                    if first_total
                    else "Source opening field; opening prices unavailable"
                ),
            },
            "moneyline": {
                "away": None,
                "home": None,
                "book": None,
                "captured_at": None,
                "note": "No opening-moneyline field or daily moneyline history is retained",
            },
        }

        available = {
            market: any(quotes[b][market] for b in books)
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
            for book, sides in best_flags(quotes, books, market).items():
                flags.setdefault(book, {}).setdefault(market, {}).update(sides)

        games.append(
            {
                "game_id": game_id,
                "source_game_id": game_id,
                "date": date,
                "week": integer(market_game.get("week")),
                "start_time_utc": market_game.get("start_time_utc")
                or market_game.get("commence_time"),
                "away_team": away,
                "home_team": home,
                "away_logo": team_logo_path(away),
                "home_logo": team_logo_path(home),
                "matchup_url": f"openers.html?game_id={game_id}" if game_id else None,
                "quotes": quotes,
                "best_flags": flags,
                "opener": opener,
                "history": {
                    "spread": spread_history,
                    "total": total_history,
                    "moneyline": [],
                },
                "moneyline_history_available": False,
                "source_updated_at": (
                    max(timestamps)
                    if timestamps
                    else market_game.get("current_market_updated_at")
                ),
                "availability_status": market_game.get("availability_status"),
                "reference": market_game.get("reference"),
                "best": market_game.get("best"),
                "data_quality_notes": (
                    ([] if points else ["No normalized spread/total history match"])
                    + (
                        ["One or more malformed current spread pairs were excluded"]
                        if any(x["game_id"] == game_id for x in malformed_spread_pairs)
                        else []
                    )
                ),
            }
        )

    games.sort(key=lambda g: (g.get("date") or "", g.get("start_time_utc") or "", g.get("away_team") or ""))

    built_at = source_build_time((CURRENT_MARKET, CFBD, HISTORY))

    payload = {
        "schema_version": "odds_screen_v2.production.2",
        "prototype_only": False,
        "built_at": built_at,
        "current_market_source": "data/site/current_market_contract.json",
        "market_source_policy": contract.get("market_source_policy"),
        "books": books,
        "venues": [
            {
                "name": book,
                "venue_type": venue_types.get(book, "unclassified"),
                "availability_status": (
                    (contract.get("venue_coverage") or {})
                    .get(book, {})
                    .get("availability_status", "UNAVAILABLE")
                ),
            }
            for book in books
        ],
        "venue_coverage": contract.get("venue_coverage") or {},
        "book_logos": {
            book: f"logos/books/{book.lower()}.png"
            for book in books
        },
        "moneyline_history": {
            "available": False,
            "message": "Daily moneyline history is not yet available in the current history pipeline.",
            "required_future_fields": [
                "snapshot_ts",
                "game_id",
                "book",
                "away_moneyline",
                "home_moneyline",
                "line_status",
            ],
        },
        "games": games,
    }

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
            book: {
                market: len(game_ids)
                for market, game_ids in book_market_games[book].items()
            }
            for book in books
        },
    }

    audit = {
        "built_at": built_at,
        "prototype_only": False,
        "files_read": [str(p.relative_to(ROOT)) for p in input_paths],
        "files_written": [str(OUT.relative_to(ROOT)), str(AUDIT.relative_to(ROOT))],
        "production_files_changed": False,
        "production_scope_confirmation": (
            "Builder formats the canonical current-market contract for Odds V2; "
            "it performs no live-provider source selection."
        ),
        "market_source_policy": contract.get("market_source_policy"),
        "canonical_current_market_input": str(CURRENT_MARKET.relative_to(ROOT)),
        "coverage_counts": counts,
        "books_detected": books,
        "venue_types": venue_types,
        "venue_coverage": contract.get("venue_coverage") or {},
        "current_market_source_selection_performed_here": False,
        "fields_used": {
            str(CURRENT_MARKET.relative_to(ROOT)): [
                "game_id",
                "date",
                "week",
                "away_team",
                "home_team",
                "availability_status",
                "current_market_updated_at",
                "quotes",
                "reference",
                "best",
                "target_venues",
                "venue_coverage",
            ],
            str(CFBD.relative_to(ROOT)): [
                "date",
                "away_team",
                "home_team",
                "spread_open",
                "total_open",
                "book",
                "pulled_at",
            ],
            str(HISTORY.relative_to(ROOT)): [
                "snapshot_date",
                "snapshot_ts",
                "market_spread_home",
                "market_spread_price",
                "market_spread_book",
                "market_total",
                "market_total_over_price",
                "market_total_under_price",
                "market_total_book",
                "source",
            ],
        },
        "moneyline_history_availability": {
            "available": False,
            "reason": (
                "Canonical current-market contract retains current moneyline quotes, "
                "while matchup_line_history.json currently contains spread/total history only."
            ),
        },
        "malformed_current_spread_pairs": malformed_spread_pairs,
        "warnings": [
            "Opening capture time is the earliest locally retained snapshot or CFBD source pull, not guaranteed sportsbook posting time.",
            "Opening prices are null when an opener-specific price was not retained.",
        ]
        + (
            [
                f"{len(malformed_spread_pairs)} malformed current spread pairs were excluded from display and best-line comparison"
            ]
            if malformed_spread_pairs
            else []
        ),
    }
    atomic_json(AUDIT, audit)

    print("ODDS SCREEN V2 BUILD")
    for key, value in counts.items():
        print(f"{key}: {value}")
    print("market_source_policy:", contract.get("market_source_policy"))
    print("current_market_source_selection_performed_here: false")
    print("moneyline_history_available: false")
    print(f"payload: {OUT.relative_to(ROOT)}")
    print(f"audit: {AUDIT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
