#!/usr/bin/env python3
"""Trace selected-week sportsbook coverage through every persisted layer."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


BOOKS = {
    "DraftKings": "draftkings",
    "FanDuel": "fanduel",
    "BetMGM": "betmgm",
    "Caesars": "williamhill_us",
    "Pinnacle": "pinnacle",
    "Novig": "novig",
    "ProphetX": "prophetx",
    "Kalshi": "kalshi",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pair_present(data, market):
    sides = (data or {}).get(market, {}) or {}
    expected = {"away", "home"} if market == "spread" else {"over", "under"}
    return set(sides) == expected


def raw_pair_present(markets, market):
    expected = 2
    return len((markets or {}).get(market, [])) == expected


def reason(*, raw, normalized, current, war, audit_rejections):
    if war:
        return "NONE"
    if raw and not normalized:
        return "ACQUIRED_BUT_LOST_DURING_NORMALIZATION"
    if normalized:
        return "NORMALIZED_BUT_NOT_PROPAGATED_TO_WAR_ROOM"
    if current:
        return "FRESH_CANONICAL_CURRENT_PAIR_NOT_SELECTED"
    if audit_rejections:
        return ";".join(sorted(audit_rejections))
    return "PROVIDER_SOURCE_DID_NOT_SUPPLY_PAIR"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--weeks", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--csv-out", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    matrix_path = args.matrix or root / "data/site/war_room_market_matrix.json"
    raw_path = root / "data/war_room/odds/theodds_ncaaf_lines_2026_raw_fast.json"
    normalized_path = root / "data/war_room/odds/theodds_ncaaf_lines_2026_fast.csv"
    current_path = root / "data/site/current_market_contract.json"

    for path in (matrix_path, raw_path, normalized_path, current_path):
        if not path.exists():
            raise SystemExit(f"Missing required audit input: {path}")

    matrix = load_json(matrix_path)
    raw = load_json(raw_path)
    current = load_json(current_path)

    raw_index = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for event in raw:
        event_id = str(event.get("id") or "")
        for book in event.get("bookmakers", []) or []:
            book_key = str(book.get("key") or "")
            for market in book.get("markets", []) or []:
                market_key = str(market.get("key") or "")
                raw_index[event_id][book_key][market_key] = list(
                    market.get("outcomes", []) or []
                )

    archive_index = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: {"observations": 0, "last_seen_file": None, "last_update": None}
            )
        )
    )
    archive_dir = root / "data/war_room/odds/raw_archive"
    for archive_path in sorted(archive_dir.glob("theodds_ncaaf_*.json")):
        for event in load_json(archive_path):
            event_id = str(event.get("id") or "")
            for book in event.get("bookmakers", []) or []:
                book_key = str(book.get("key") or "")
                for market in book.get("markets", []) or []:
                    market_key = str(market.get("key") or "")
                    outcomes = list(market.get("outcomes", []) or [])
                    if len(outcomes) != 2:
                        continue
                    item = archive_index[event_id][book_key][market_key]
                    item["observations"] += 1
                    item["last_seen_file"] = archive_path.name
                    item["last_update"] = (
                        market.get("last_update") or book.get("last_update")
                    )

    normalized = defaultdict(
        lambda: defaultdict(lambda: defaultdict(set))
    )
    with normalized_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            market = {
                "spreads": "spread",
                "totals": "total",
                "spread": "spread",
                "total": "total",
            }.get(str(row.get("market") or "").lower())
            if market:
                normalized[str(row.get("game_id") or "")][
                    str(row.get("book") or "")
                ][market].add(str(row.get("side") or ""))

    current_by_game = {
        str(game.get("game_id")): game
        for game in current.get("games", [])
    }
    fallback_rejections = defaultdict(set)
    for row in matrix.get("audit", {}).get(
        "current_market_fallback_rejections", []
    ):
        fallback_rejections[
            (str(row.get("game_id")), row.get("book"), row.get("market"))
        ].add(str(row.get("reason")))

    rows = []
    coverage = defaultdict(lambda: {"required": 0, "games": 0, "spread": 0, "total": 0})

    for game in matrix.get("games", []):
        if game.get("week") not in args.weeks:
            continue
        if not game.get("scope", {}).get("fbs_vs_fbs"):
            continue

        provider_ids = [str(value) for value in game.get("provider_game_ids", []) if value]
        provider_id = provider_ids[0] if provider_ids else ""
        current_game = current_by_game.get(str(game.get("game_id")), {})

        for book, provider_book_key in BOOKS.items():
            if book == "Pinnacle":
                war = game.get("market", {}).get("pinnacle", {}) or {}
            elif book in {"Novig", "ProphetX", "Kalshi"}:
                war = game.get("market", {}).get("exchanges", {}).get(book, {}) or {}
            else:
                war = game.get("market", {}).get("primary_sportsbooks", {}).get(book, {}) or {}

            current_book = current_game.get("quotes", {}).get(book, {}) or {}
            raw_markets = raw_index[provider_id][provider_book_key]
            archived_markets = archive_index[provider_id][provider_book_key]
            normalized_markets = normalized[provider_id][book]

            raw_spread = raw_pair_present(raw_markets, "spreads")
            raw_total = raw_pair_present(raw_markets, "totals")
            normalized_spread = normalized_markets.get("spread", set()) == {
                game.get("away_team"), game.get("home_team")
            }
            normalized_total = {
                value.lower() for value in normalized_markets.get("total", set())
            } == {"over", "under"}
            current_spread = pair_present(current_book, "spread")
            current_total = pair_present(current_book, "total")
            war_spread = pair_present(war, "spread")
            war_total = pair_present(war, "total")

            key = (game.get("week"), book)
            coverage[key]["required"] += 1
            coverage[key]["games"] += int(war_spread or war_total)
            coverage[key]["spread"] += int(war_spread)
            coverage[key]["total"] += int(war_total)

            gid = str(game.get("game_id"))
            rows.append({
                "week": game.get("week"),
                "game_id": gid,
                "away_team": game.get("away_team"),
                "home_team": game.get("home_team"),
                "sportsbook": book,
                "provider_event_id": provider_id,
                "game_row_present": True,
                "raw_provider_book_present": bool(raw_markets),
                "raw_provider_spread_pair": raw_spread,
                "raw_provider_total_pair": raw_total,
                "archive_spread_observations": archived_markets["spreads"]["observations"],
                "archive_spread_last_seen_file": archived_markets["spreads"]["last_seen_file"],
                "archive_spread_last_update": archived_markets["spreads"]["last_update"],
                "archive_total_observations": archived_markets["totals"]["observations"],
                "archive_total_last_seen_file": archived_markets["totals"]["last_seen_file"],
                "archive_total_last_update": archived_markets["totals"]["last_update"],
                "normalized_spread_pair": normalized_spread,
                "normalized_total_pair": normalized_total,
                "current_market_spread_pair": current_spread,
                "current_market_total_pair": current_total,
                "war_room_spread_pair": war_spread,
                "war_room_total_pair": war_total,
                "spread_rejection_reason": reason(
                    raw=raw_spread,
                    normalized=normalized_spread,
                    current=current_spread,
                    war=war_spread,
                    audit_rejections=fallback_rejections[(gid, book, "spread")],
                ),
                "total_rejection_reason": reason(
                    raw=raw_total,
                    normalized=normalized_total,
                    current=current_total,
                    war=war_total,
                    audit_rejections=fallback_rejections[(gid, book, "total")],
                ),
            })

    summary = []
    for (week, book), values in sorted(coverage.items()):
        required = values["required"]
        summary.append({
            "week": week,
            "sportsbook": book,
            **values,
            "spread_pct": round(100 * values["spread"] / required, 1) if required else 0,
            "total_pct": round(100 * values["total"] / required, 1) if required else 0,
        })

    csv_out = args.csv_out or root / "data/audits/war_room_selected_week_market_coverage.csv"
    json_out = args.json_out or root / "data/audits/war_room_selected_week_market_coverage.json"
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    json_out.write_text(
        json.dumps(
            {
                "schema_version": "war-room-selected-week-market-coverage-v1",
                "matrix_built_at": matrix.get("built_at"),
                "fast_refresh": matrix.get("fast_market_refresh"),
                "weeks": args.weeks,
                "summary": summary,
                "rows": rows,
                "matrix_input_audit": matrix.get("summary", {}),
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"wrote: {csv_out} ({len(rows)} rows)")
    print(f"wrote: {json_out}")
    for item in summary:
        print(
            f"W{item['week']} {item['sportsbook']:<12} "
            f"{item['games']}/{item['required']} "
            f"S {item['spread']}/{item['required']} ({item['spread_pct']:.1f}%) "
            f"T {item['total']}/{item['required']} ({item['total_pct']:.1f}%)"
        )


if __name__ == "__main__":
    main()
