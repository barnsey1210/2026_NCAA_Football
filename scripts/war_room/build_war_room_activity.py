#!/usr/bin/env python3
"""Build the durable War Room activity ledger and bounded public projection.

This adapter detects changes between already-resolved canonical artifacts. It
does not acquire data, calculate projections, select markets, or redefine
provider health. The browser consumes only the bounded public projection;
runtime history remains append-only under data/war_room/history.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = ROOT / "data/site/war_room_market_matrix.json"
DEFAULT_HEALTH = ROOT / "data/site/war_room_health.json"
DEFAULT_RESULTS = ROOT / "data/canonical/game_results_2026.json"
DEFAULT_POSTGAME = ROOT / "data/site/postgame_shadow_updates.json"
DEFAULT_HISTORY = ROOT / "data/war_room/history/war_room_events.jsonl"
DEFAULT_STATE = ROOT / "data/war_room/history/war_room_activity_state.json"
DEFAULT_OUT = ROOT / "data/site/war_room_activity.json"
DEFAULT_LINE_HISTORY = ROOT / "data/site/matchup_line_history.json"
DEFAULT_GAME_INDEX = ROOT / "data/war_room/history/war_room_game_activity_index.json"
DEFAULT_BOOK_HISTORY = ROOT / "data/odds/game_book_line_history.csv"

BOOKS = (
    "DraftKings", "FanDuel", "BetMGM", "Caesars",
    "Pinnacle", "Novig", "ProphetX", "Kalshi",
)
MARKET_TYPES = ("spread", "total")
PUBLIC_MOVE_BOOKS = {"DraftKings", "FanDuel", "BetMGM", "Caesars", "Pinnacle"}
PUBLIC_MOVE_THRESHOLD = 0.5
AGGREGATION_SECONDS = 90
ACTIONABLE_EDGE_THRESHOLD = 3.0
DISPLAY_PRIORITY = {
    "EDGE_BECAME_ACTIONABLE": 100, "EDGE_LOST_ACTIONABLE": 100,
    "EDGE_ACTIONABLE_CHANGED": 95,
    "BEST_SPREAD_CHANGED": 92, "BEST_TOTAL_CHANGED": 92,
    "MARKET_OPENED": 90, "PINNACLE_OPENED": 88,
    "PINNACLE_MOVE": 82, "MARKET_FOLLOW": 81, "MARKET_MOVE": 80,
    "MODEL_STATE_CHANGED": 70, "SHADOW_SPREAD_READY": 70, "SHADOW_TOTAL_READY": 70,
    "RATINGS_UPDATED": 60, "FINAL_POSTED": 50,
    "PROVIDER_UNAVAILABLE": 42, "PROVIDER_DEGRADED": 41, "PROVIDER_RECOVERED": 40,
}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized_timestamp(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text + "T00:00:00Z"
    return text.replace("+00:00", "Z")


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def parsed_timestamp(value: Any) -> datetime:
    text = normalized_timestamp(value, "1970-01-01T00:00:00Z").replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def quote_time(quote: dict[str, Any]) -> str | None:
    return quote.get("last_update") or quote.get("pulled_at")


def complete_pair(market: str, sides: Any) -> bool:
    if not isinstance(sides, dict):
        return False
    expected = {"away", "home"} if market == "spread" else {"over", "under"}
    return set(sides) == expected and all(isinstance(sides.get(side), dict) for side in expected)


def book_bundle(game: dict[str, Any], book: str) -> dict[str, Any]:
    market = game.get("market") or {}
    if book == "Pinnacle":
        return market.get("pinnacle") or {}
    return (
        (market.get("primary_sportsbooks") or {}).get(book)
        or (market.get("exchanges") or {}).get(book)
        or {}
    )


def pair_snapshot(game: dict[str, Any], book: str, market: str) -> dict[str, Any] | None:
    sides = (book_bundle(game, book).get(market) or {})
    if not complete_pair(market, sides):
        return None
    side = "home" if market == "spread" else "over"
    quote = sides[side]
    timestamps = [quote_time(row) for row in sides.values() if quote_time(row)]
    return {
        "game_id": str(game.get("game_id") or ""),
        "season": game.get("season", 2026),
        "week": game.get("week"),
        "away_team": game.get("away_team"),
        "home_team": game.get("home_team"),
        "book": book,
        "market": market,
        "side": side,
        "line": quote.get("line"),
        "price": quote.get("price"),
        "source": quote.get("source"),
        "selection_source": quote.get("selection_source"),
        "quote_timestamp": max(timestamps) if timestamps else None,
        "pair_fingerprint": stable_hash(sides),
    }


def decision_snapshot(game: dict[str, Any], market: str) -> dict[str, Any]:
    """Observe already-resolved BEST and EDGE values without recalculating them."""
    edges = (game.get("edges") or {}).get(market) or {}
    best_side = edges.get("best_side")
    best_edge = edges.get("best_edge")

    best_market = ((game.get("market") or {}).get("best_sportsbook") or {}).get(market) or {}
    quote = best_market.get(best_side) if best_side else None
    if not isinstance(quote, dict):
        quote = None

    return {
        "market": market,
        "best_side": best_side,
        "best_edge": best_edge,
        "book": quote.get("book") if quote else None,
        "line": quote.get("line") if quote else None,
        "price": quote.get("price") if quote else None,
        "quote_timestamp": quote_time(quote) if quote else None,
        "selection_source": quote.get("selection_source") if quote else None,
    }


def selected_week_health(matrix: dict[str, Any]) -> dict[str, Any]:
    by_week: dict[str, Any] = {}
    games = [g for g in matrix.get("games", []) if (g.get("scope") or {}).get("fbs_vs_fbs") is True]
    for week in sorted({str(g.get("week")) for g in games}):
        rows = [g for g in games if str(g.get("week")) == week]
        by_week[week] = {}
        for book in BOOKS:
            spread = sum(pair_snapshot(g, book, "spread") is not None for g in rows)
            total = sum(pair_snapshot(g, book, "total") is not None for g in rows)
            covered = sum(
                pair_snapshot(g, book, "spread") is not None
                or pair_snapshot(g, book, "total") is not None
                for g in rows
            )
            required = len(rows)
            if required and covered == spread == total == required:
                status = "GREEN"
            elif covered:
                status = "YELLOW"
            else:
                status = "RED"
            by_week[week][book] = {
                "status": status, "required": required,
                "games": covered, "spread": spread, "total": total,
            }
    return by_week


def authority_value(game: dict[str, Any], domain: str, field: str) -> Any:
    value = ((game.get("authority") or {}).get(domain))
    if isinstance(value, dict):
        return value.get(field)
    return value if field == "projection_authority" else None


def current_snapshot(matrix: dict[str, Any], health: dict[str, Any], results: dict[str, Any], postgame: dict[str, Any]) -> dict[str, Any]:
    markets: dict[str, Any] = {}
    models: dict[str, Any] = {}
    shadows: dict[str, Any] = {}
    decisions: dict[str, Any] = {}
    games_meta: dict[str, Any] = {}
    for game in matrix.get("games", []):
        gid = str(game.get("game_id") or "")
        if not gid:
            continue
        games_meta[gid] = {
            "season": game.get("season", 2026), "week": game.get("week"),
            "away_team": game.get("away_team"), "home_team": game.get("home_team"),
            "kickoff_time": game.get("kickoff_time") or game.get("date"),
            "neutral_site": game.get("neutral_site"),
        }
        decisions[gid] = {
            market: decision_snapshot(game, market)
            for market in MARKET_TYPES
        }
        models[gid] = {
            "state": game.get("state"),
            "spread_authority": authority_value(game, "spread", "projection_authority"),
            "spread_model_id": authority_value(game, "spread", "model_id"),
            "total_authority": authority_value(game, "total", "projection_authority"),
            "total_model_id": authority_value(game, "total", "model_id"),
        }
        for domain, model_name in (("spread", "shadow_spread"), ("total", "shadow_total")):
            model = (game.get("models") or {}).get(model_name) or {}
            value_key = "value_home_line" if domain == "spread" else "value_total"
            shadows[f"{gid}|{domain}"] = {
                "ready": model.get("selection_status") == "AVAILABLE" and model.get(value_key) is not None,
                "value": model.get(value_key),
                "model_id": model.get("model_id"),
                "component_status": model.get("component_status"),
            }
        for book in BOOKS:
            for market in MARKET_TYPES:
                pair = pair_snapshot(game, book, market)
                if pair:
                    markets[f"{gid}|{book}|{market}"] = pair

    ratings = {}
    for key, row in ((health.get("ratings_health") or {}).get("sources") or {}).items():
        if not isinstance(row, dict):
            continue
        source = str(row.get("source") or key)
        ratings[source] = {
            "accepted_timestamp": row.get("last_changed_at") or row.get("snapshot_date"),
            "snapshot_date": row.get("snapshot_date") or row.get("latest_snapshot_date"),
            "status": row.get("status"),
            "coverage": row.get("games_available") or row.get("teams"),
            "change_status": row.get("change_status"),
        }

    finals = {}
    for game in results.get("games", []) if isinstance(results, dict) else []:
        gid = str(game.get("game_id") or "")
        if not gid:
            continue
        finals[gid] = {
            "season": game.get("season", results.get("season", 2026)),
            "week": game.get("week"), "away_team": game.get("away_team"),
            "home_team": game.get("home_team"), "away_score": game.get("away_score"),
            "home_score": game.get("home_score"), "source": game.get("source") or results.get("source"),
            "final_at": game.get("completed_at") or game.get("source_updated_at") or results.get("generated_at"),
        }

    return {
        "refresh_id": ((matrix.get("fast_market_refresh") or {}).get("refresh_id")
                       or (health.get("fast_market_refresh") or {}).get("refresh_id")),
        "built_at": matrix.get("built_at"), "markets": markets,
        "opened_market_keys": sorted(markets),
        "opened_game_market_keys": sorted({f"{row['game_id']}|{row['market']}" for row in markets.values()}),
        "models": models, "shadows": shadows, "decisions": decisions,
        "ratings": ratings, "finals": finals, "provider_health": selected_week_health(matrix),
        "postgame": {"built_at": postgame.get("built_at"), "status": postgame.get("status"),
                     "completed_team_updates": (postgame.get("summary") or {}).get("completed_team_updates")},
        "pipeline_refreshes": {
            "market": ((matrix.get("fast_market_refresh") or {}).get("last_fast_pull_at")
                       or matrix.get("built_at")),
            "model": ((health.get("ratings_health") or {}).get("generated_at")
                      or health.get("built_at")),
            "postgame": postgame.get("built_at"),
        },
        "games_meta": games_meta,
    }


def event(*, event_type: str, observed_at: str, detected_at: str, refresh_id: str | None,
          entity_type: str, entity_id: str, source_system: str, season=None, week=None,
          game_id=None, away_team=None, home_team=None, book=None, market=None, side=None,
          old_line=None, new_line=None, old_price=None, new_price=None,
          source=None, significance="INFORMATIONAL", metadata=None, identity_parts=()) -> dict[str, Any]:
    idempotency = "|".join(str(x) for x in (event_type, entity_id, *identity_parts))
    event_id = "wre_" + hashlib.sha256(idempotency.encode()).hexdigest()[:24]
    cycle = f"{season or 2026}_WK{week}_PREP" if week is not None else f"{season or 2026}_SYSTEM"
    return {
        "event_id": event_id, "event_type": event_type, "event_version": 1,
        "event_timestamp": observed_at, "observed_at": observed_at,
        "detected_at": detected_at, "created_at": detected_at,
        "refresh_id": refresh_id, "source_system": source_system,
        "entity_type": entity_type, "entity_id": entity_id, "cycle_id": cycle,
        "correlation_id": refresh_id or event_id, "idempotency_key": idempotency,
        "season": season, "week": week, "game_id": game_id,
        "away_team": away_team, "home_team": home_team, "book": book,
        "market": market, "side": side, "old_line": old_line,
        "new_line": new_line, "old_price": old_price, "new_price": new_price,
        "source": source, "significance": significance,
        "metadata": metadata or {}, "payload": metadata or {},
    }


def detect(previous: dict[str, Any], current: dict[str, Any], detected_at: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    refresh_id = current.get("refresh_id")
    previously_opened = set(previous.get("opened_market_keys") or previous.get("markets", {}))
    previously_opened_game_markets = set(previous.get("opened_game_market_keys") or {
        f"{row.get('game_id')}|{row.get('market')}" for row in (previous.get("markets") or {}).values()
    })
    games_meta = current.get("games_meta", {})
    newly_opened_game_markets: set[str] = set()

    current_markets = current.get("markets", {})
    for key, new in sorted(
        current_markets.items(),
        key=lambda item: (
            normalized_timestamp(item[1].get("quote_timestamp"), detected_at),
            item[0],
        ),
    ):
        old = (previous.get("markets") or {}).get(key)
        common = dict(
            observed_at=normalized_timestamp(new.get("quote_timestamp"), detected_at),
            detected_at=detected_at, refresh_id=refresh_id, entity_type="market",
            entity_id=key, source_system="canonical_market", season=new.get("season"),
            week=new.get("week"), game_id=new.get("game_id"), away_team=new.get("away_team"),
            home_team=new.get("home_team"), book=new.get("book"), market=new.get("market"),
            side=new.get("side"), new_line=new.get("line"), new_price=new.get("price"),
            source=new.get("source"), significance="ACTIONABLE",
        )
        if old is None:
            game_market_key = f"{new.get('game_id')}|{new.get('market')}"
            first_game_market = (
                game_market_key not in previously_opened_game_markets
                and game_market_key not in newly_opened_game_markets
            )
            event_type = "MARKET_OPENED" if first_game_market else "BOOK_MARKET_ADDED"
            newly_opened_game_markets.add(game_market_key)
            if first_game_market:
                common["observed_at"] = detected_at
            out.append(event(event_type=event_type, metadata={"selection_source": new.get("selection_source")},
                             identity_parts=(new.get("pair_fingerprint"),), **common))
        elif old.get("line") != new.get("line"):
            event_type = "SPREAD_MOVED" if new.get("market") == "spread" else "TOTAL_MOVED"
            out.append(event(event_type=event_type, old_line=old.get("line"), old_price=old.get("price"),
                             identity_parts=(old.get("pair_fingerprint"), new.get("pair_fingerprint")),
                             metadata={"selection_source": new.get("selection_source")}, **common))

    for key, old in (previous.get("markets") or {}).items():
        if key in current.get("markets", {}):
            continue
        if str(old.get("game_id")) not in games_meta:
            continue
        meta = games_meta.get(str(old.get("game_id"))) or old
        out.append(event(
            event_type="BOOK_MARKET_REMOVED", observed_at=detected_at, detected_at=detected_at,
            refresh_id=refresh_id, entity_type="market", entity_id=key,
            source_system="canonical_market", season=meta.get("season"), week=meta.get("week"),
            game_id=old.get("game_id"), away_team=meta.get("away_team"), home_team=meta.get("home_team"),
            book=old.get("book"), market=old.get("market"), side=old.get("side"),
            old_line=old.get("line"), old_price=old.get("price"), source=old.get("source"),
            significance="OPERATIONAL", metadata={"reason": "resolved accepted pair unavailable"},
            identity_parts=(old.get("pair_fingerprint"), refresh_id),
        ))

    # BEST sportsbook and actionable-edge transitions are observed from the
    # already-resolved matrix. This layer does not select books or calculate edges.
    for gid, new_domains in current.get("decisions", {}).items():
        old_domains = (previous.get("decisions") or {}).get(gid)
        if not isinstance(old_domains, dict):
            # Establish a baseline when upgrading an existing state file.
            continue

        meta = games_meta.get(gid, {})

        for market in MARKET_TYPES:
            new = new_domains.get(market) or {}
            old = old_domains.get(market) or {}

            if not old:
                continue

            old_best = (
                old.get("best_side"),
                old.get("book"),
                old.get("line"),
                old.get("price"),
            )
            new_best = (
                new.get("best_side"),
                new.get("book"),
                new.get("line"),
                new.get("price"),
            )

            if old_best != new_best and any(value is not None for value in new_best):
                event_type = "BEST_SPREAD_CHANGED" if market == "spread" else "BEST_TOTAL_CHANGED"
                out.append(event(
                    event_type=event_type,
                    observed_at=detected_at,
                    detected_at=detected_at,
                    refresh_id=refresh_id,
                    entity_type="game_market",
                    entity_id=f"{gid}|{market}|best",
                    source_system="war_room_matrix_observer",
                    season=meta.get("season"),
                    week=meta.get("week"),
                    game_id=gid,
                    away_team=meta.get("away_team"),
                    home_team=meta.get("home_team"),
                    book=new.get("book"),
                    market=market,
                    side=new.get("best_side"),
                    old_line=old.get("line"),
                    new_line=new.get("line"),
                    old_price=old.get("price"),
                    new_price=new.get("price"),
                    significance="ACTIONABLE",
                    metadata={
                        "old_best": old,
                        "new_best": new,
                        "old_book": old.get("book"),
                        "new_book": new.get("book"),
                    },
                    identity_parts=(stable_hash(old), stable_hash(new)),
                ))

            try:
                old_edge = float(old.get("best_edge"))
            except (TypeError, ValueError):
                old_edge = None
            try:
                new_edge = float(new.get("best_edge"))
            except (TypeError, ValueError):
                new_edge = None

            if old_edge is None or new_edge is None:
                continue

            edge_event = None
            if old_edge < ACTIONABLE_EDGE_THRESHOLD <= new_edge:
                edge_event = "EDGE_BECAME_ACTIONABLE"
            elif old_edge >= ACTIONABLE_EDGE_THRESHOLD > new_edge:
                edge_event = "EDGE_LOST_ACTIONABLE"
            elif (
                old_edge >= ACTIONABLE_EDGE_THRESHOLD
                and new_edge >= ACTIONABLE_EDGE_THRESHOLD
                and (
                    old.get("best_side") != new.get("best_side")
                    or abs(new_edge - old_edge) >= 0.5
                )
            ):
                edge_event = "EDGE_ACTIONABLE_CHANGED"

            if edge_event:
                out.append(event(
                    event_type=edge_event,
                    observed_at=detected_at,
                    detected_at=detected_at,
                    refresh_id=refresh_id,
                    entity_type="game_edge",
                    entity_id=f"{gid}|{market}|edge",
                    source_system="war_room_matrix_observer",
                    season=meta.get("season"),
                    week=meta.get("week"),
                    game_id=gid,
                    away_team=meta.get("away_team"),
                    home_team=meta.get("home_team"),
                    book=new.get("book"),
                    market=market,
                    side=new.get("best_side"),
                    old_line=old.get("line"),
                    new_line=new.get("line"),
                    old_price=old.get("price"),
                    new_price=new.get("price"),
                    significance="ACTIONABLE",
                    metadata={
                        "old_edge": old_edge,
                        "new_edge": new_edge,
                        "old_side": old.get("best_side"),
                        "new_side": new.get("best_side"),
                        "old_book": old.get("book"),
                        "new_book": new.get("book"),
                    },
                    identity_parts=(
                        market,
                        old_edge,
                        new_edge,
                        old.get("best_side"),
                        new.get("best_side"),
                        refresh_id,
                    ),
                ))

    for source, new in current.get("ratings", {}).items():
        old = (previous.get("ratings") or {}).get(source)
        if old and old.get("accepted_timestamp") != new.get("accepted_timestamp"):
            out.append(event(
                event_type="RATING_UPDATED", observed_at=normalized_timestamp(new.get("accepted_timestamp"), detected_at),
                detected_at=detected_at, refresh_id=refresh_id, entity_type="provider_panel",
                entity_id=source, source_system="ratings_acceptance", season=2026,
                source=source, significance="OPERATIONAL", metadata={"previous": old, "current": new},
                identity_parts=(old.get("accepted_timestamp"), new.get("accepted_timestamp")),
            ))

    for gid, new in current.get("models", {}).items():
        old = (previous.get("models") or {}).get(gid)
        if old and old != new:
            meta = games_meta.get(gid, {})
            out.append(event(
                event_type="MODEL_STATE_CHANGED", observed_at=detected_at, detected_at=detected_at,
                refresh_id=refresh_id, entity_type="game", entity_id=gid,
                source_system="projection_adapter", season=meta.get("season"), week=meta.get("week"),
                game_id=gid, away_team=meta.get("away_team"), home_team=meta.get("home_team"),
                significance="OPERATIONAL", metadata={"old_state": old.get("state"), "new_state": new.get("state"),
                "old_spread_authority": old.get("spread_authority"), "spread_authority": new.get("spread_authority"),
                "old_total_authority": old.get("total_authority"), "total_authority": new.get("total_authority"),
                "spread_model_id": new.get("spread_model_id"), "total_model_id": new.get("total_model_id")},
                identity_parts=(stable_hash(old), stable_hash(new)),
            ))

    for key, new in current.get("shadows", {}).items():
        old = (previous.get("shadows") or {}).get(key)
        if old and not old.get("ready") and new.get("ready"):
            gid, domain = key.split("|", 1)
            meta = games_meta.get(gid, {})
            out.append(event(
                event_type=f"SHADOW_{domain.upper()}_READY", observed_at=detected_at,
                detected_at=detected_at, refresh_id=refresh_id, entity_type="game", entity_id=key,
                source_system="shadow_projection", season=meta.get("season"), week=meta.get("week"),
                game_id=gid, away_team=meta.get("away_team"), home_team=meta.get("home_team"),
                significance="OPERATIONAL", metadata=new,
                identity_parts=(new.get("model_id"), new.get("value")),
            ))

    for gid, new in current.get("finals", {}).items():
        if gid not in (previous.get("finals") or {}):
            out.append(event(
                event_type="FINAL_POSTED", observed_at=normalized_timestamp(new.get("final_at"), detected_at),
                detected_at=detected_at, refresh_id=refresh_id, entity_type="game", entity_id=gid,
                source_system="canonical_results", season=new.get("season"), week=new.get("week"),
                game_id=gid, away_team=new.get("away_team"), home_team=new.get("home_team"),
                source=new.get("source"), significance="OPERATIONAL", metadata={"away_score": new.get("away_score"),
                "home_score": new.get("home_score")}, identity_parts=(new.get("away_score"), new.get("home_score")),
            ))

    old_post = previous.get("postgame") or {}
    new_post = current.get("postgame") or {}
    if old_post and old_post.get("built_at") != new_post.get("built_at") and new_post.get("completed_team_updates"):
        out.append(event(
            event_type="POSTGAME_REFRESHED", observed_at=normalized_timestamp(new_post.get("built_at"), detected_at),
            detected_at=detected_at, refresh_id=refresh_id, entity_type="system", entity_id="postgame",
            source_system="postgame_pipeline", season=2026, significance="OPERATIONAL",
            metadata=new_post, identity_parts=(new_post.get("built_at"),),
        ))

    for week, books in current.get("provider_health", {}).items():
        old_books = (previous.get("provider_health") or {}).get(week, {})
        for book, new in books.items():
            old = old_books.get(book)
            if not old or old.get("status") == new.get("status"):
                continue
            if new["status"] == "GREEN":
                kind = "PROVIDER_RECOVERED"
            elif new["status"] == "RED":
                kind = "PROVIDER_UNAVAILABLE"
            else:
                kind = "PROVIDER_DEGRADED"
            out.append(event(
                event_type=kind, observed_at=detected_at, detected_at=detected_at,
                refresh_id=refresh_id, entity_type="provider_panel", entity_id=f"W{week}|{book}",
                source_system="war_room_selected_week_health", season=2026, week=int(week), book=book,
                significance="OPERATIONAL", metadata={"previous": old, "current": new},
                identity_parts=(old.get("status"), new.get("status"), refresh_id),
            ))
    return out


def first_market_availability(previous: dict[str, Any], current: dict[str, Any], detected_at: str) -> dict[str, Any]:
    """Persist first accepted game/market availability without replaying startup inventory."""

    established = dict(previous.get("first_market_availability") or {})
    initializing = not bool(previous)
    prior_game_markets = set(previous.get("opened_game_market_keys") or [])
    candidates: dict[str, list[dict[str, Any]]] = {}
    for row in (current.get("markets") or {}).values():
        key = f"{row.get('game_id')}|{row.get('market')}"
        candidates.setdefault(key, []).append(row)

    for key, rows in candidates.items():
        if key in established:
            continue
        first = sorted(
            rows,
            key=lambda row: (
                normalized_timestamp(row.get("quote_timestamp"), detected_at),
                str(row.get("book") or ""),
            ),
        )[0]
        established[key] = {
            "first_market_available_at": detected_at,
            "detected_at": detected_at,
            "first_quote_timestamp": first.get("quote_timestamp"),
            # A state file created before this field existed already proves
            # those game/markets were established inventory, not new alerts.
            "baseline": initializing or key in prior_game_markets,
            "book": first.get("book"),
            "line": first.get("line"),
            "price": first.get("price"),
            "side": first.get("side"),
            "selection_source": first.get("selection_source"),
        }
    return established


def public_summary(events: list[dict[str, Any]]) -> dict[str, int]:
    groups = Counter()
    for row in events:
        kind = row["event_type"]
        if kind in {"MARKET_OPENED", "PINNACLE_OPENED"}:
            groups["open"] += 1
        elif kind in {"MARKET_MOVE", "PINNACLE_MOVE", "MARKET_FOLLOW"}:
            groups["moves"] += 1
        elif kind in {"BEST_SPREAD_CHANGED", "BEST_TOTAL_CHANGED"}:
            groups["best"] += 1
        elif kind == "EDGE_BECAME_ACTIONABLE":
            groups["new_edge"] += 1
        elif kind == "EDGE_ACTIONABLE_CHANGED":
            groups["edge_changed"] += 1
        elif kind == "EDGE_LOST_ACTIONABLE":
            groups["edge_lost"] += 1
        elif kind == "RATINGS_UPDATED":
            groups["ratings"] += 1
        elif kind in {
            "MODEL_STATE_CHANGED",
            "SHADOW_SPREAD_READY",
            "SHADOW_TOTAL_READY",
        }:
            groups["model"] += 1
        elif kind in {"FINAL_POSTED", "POSTGAME_REFRESHED"}:
            groups["final"] += 1

    return {
        key: groups[key]
        for key in (
            "open",
            "moves",
            "best",
            "new_edge",
            "edge_changed",
            "edge_lost",
            "ratings",
            "model",
            "final",
        )
    }


def public_event(kind: str, rows: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row.get("event_timestamp") or "", row.get("event_id") or ""))
    first, last = ordered[0], ordered[-1]
    underlying = [row["event_id"] for row in ordered]
    result = dict(last)
    result.update({
        "event_id": "wrp_" + stable_hash({"kind": kind, "events": underlying})[:24],
        "event_type": kind,
        "event_timestamp": first.get("event_timestamp"),
        "observed_at": first.get("observed_at"),
        "detected_at": last.get("detected_at"),
        "underlying_event_ids": underlying,
        "display_priority": DISPLAY_PRIORITY.get(kind, 30),
        "metadata": {**(last.get("metadata") or {}), **(metadata or {})},
    })
    result["payload"] = result["metadata"]
    return result


def public_openers(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    opened = [row for row in history if row.get("event_type") in {"MARKET_OPENED", "BOOK_MARKET_ADDED"}]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in opened:
        groups.setdefault((str(row.get("game_id")), str(row.get("market"))), []).append(row)
    projected = []
    for rows in groups.values():
        ordered = sorted(rows, key=lambda row: (row.get("event_timestamp") or "", row.get("event_id") or ""))
        first = next((row for row in ordered if row.get("event_type") == "MARKET_OPENED"), None)
        if first is None:
            continue
        projected.append(public_event("MARKET_OPENED", [first], {"opening_book": first.get("book")}))
        pinnacle = next((row for row in ordered if row.get("book") == "Pinnacle"), None)
        if pinnacle and pinnacle["event_id"] != first["event_id"]:
            delay = (parsed_timestamp(pinnacle.get("event_timestamp")) - parsed_timestamp(first.get("event_timestamp"))).total_seconds()
            if delay > AGGREGATION_SECONDS:
                projected.append(public_event("PINNACLE_OPENED", [pinnacle], {"delay_seconds": delay}))
    return projected


def public_moves(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for row in history:
        if row.get("event_type") not in {"SPREAD_MOVED", "TOTAL_MOVED"}:
            continue
        if row.get("book") not in PUBLIC_MOVE_BOOKS:
            continue
        try:
            delta = float(row.get("new_line")) - float(row.get("old_line"))
        except (TypeError, ValueError):
            continue
        if abs(delta) < PUBLIC_MOVE_THRESHOLD:
            continue
        candidates.append((row, 1 if delta > 0 else -1))

    groups: list[list[dict[str, Any]]] = []
    for row, direction in sorted(candidates, key=lambda item: parsed_timestamp(item[0].get("event_timestamp"))):
        matched = None
        for group in reversed(groups):
            anchor = group[0]
            anchor_delta = float(anchor["new_line"]) - float(anchor["old_line"])
            if (anchor.get("game_id"), anchor.get("market"), 1 if anchor_delta > 0 else -1) != (row.get("game_id"), row.get("market"), direction):
                continue
            if (parsed_timestamp(row.get("event_timestamp")) - parsed_timestamp(group[-1].get("event_timestamp"))).total_seconds() <= AGGREGATION_SECONDS:
                matched = group
            break
        if matched is None:
            groups.append([row])
        else:
            matched.append(row)

    projected = []
    for rows in groups:
        books = list(dict.fromkeys(row.get("book") for row in rows))
        if rows[0].get("book") == "Pinnacle" and len(rows) > 1:
            projected.append(public_event("PINNACLE_MOVE", [rows[0]], {"books": ["Pinnacle"]}))
            projected.append(public_event("MARKET_FOLLOW", rows[1:], {"books": books[1:], "leader": "Pinnacle"}))
        elif len(rows) == 1 and books == ["Pinnacle"]:
            projected.append(public_event("PINNACLE_MOVE", rows, {"books": books}))
        else:
            projected.append(public_event("MARKET_MOVE", rows, {"books": books}))
    return projected


def public_ratings(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in history:
        if row.get("event_type") == "RATING_UPDATED":
            grouped.setdefault(str(row.get("refresh_id") or row.get("detected_at")), []).append(row)
    return [public_event("RATINGS_UPDATED", rows, {"sources": [row.get("source") for row in rows]}) for rows in grouped.values()]


def project_public(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    retained = [row for row in history if row.get("event_type") in {
        "MODEL_STATE_CHANGED", "SHADOW_SPREAD_READY", "SHADOW_TOTAL_READY", "FINAL_POSTED",
        "PROVIDER_DEGRADED", "PROVIDER_RECOVERED", "PROVIDER_UNAVAILABLE",
        "EDGE_BECAME_ACTIONABLE", "EDGE_LOST_ACTIONABLE", "EDGE_ACTIONABLE_CHANGED",
        "BEST_SPREAD_CHANGED", "BEST_TOTAL_CHANGED",
    }]
    projected = public_openers(history) + public_moves(history) + public_ratings(history)
    projected.extend(public_event(row["event_type"], [row]) for row in retained)
    return sorted(projected, key=lambda row: (row.get("event_timestamp") or "", row.get("event_id") or ""), reverse=True)


def first_tracked_opener(rows: list[dict[str, Any]], market: str, *, book: str | None = None) -> dict[str, Any] | None:
    """Return the earliest accepted canonical history observation.

    The matchup-line-history contract is the pre-Activity opener authority. A
    current matrix quote is never substituted here. Explicit provider opener
    fields are preferred when present; otherwise the earliest tracked accepted
    line is retained and labeled as a first observation.
    """
    if market == "spread":
        line_fields = ("market_spread_open_home", "market_spread_home")
        book_field, price_field, update_field = (
            "market_spread_book", "market_spread_price", "market_spread_last_update"
        )
    else:
        line_fields = ("market_total_open", "market_total")
        book_field, price_field, update_field = (
            "market_total_book", "market_total_over_price", "market_total_last_update"
        )
    candidates = []
    for row in rows:
        row_book = str(row.get(book_field) or "").strip()
        if book and row_book.lower() != book.lower():
            continue
        explicit = row.get(line_fields[0])
        observed = row.get(line_fields[1])
        line = explicit if explicit is not None else observed
        if line is None:
            continue
        timestamp = row.get(update_field) or row.get("snapshot_ts") or row.get("snapshot_date")
        if not timestamp:
            continue
        candidates.append((parsed_timestamp(timestamp), row, line, explicit is not None))
    if not candidates:
        return None
    _, row, line, explicit = min(candidates, key=lambda item: item[0])
    timestamp = row.get(update_field) or row.get("snapshot_ts") or row.get("snapshot_date")
    return {
        "market": market,
        "line": line,
        "price": row.get(price_field),
        "book": row.get(book_field),
        "observed_at": normalized_timestamp(timestamp, str(timestamp)),
        "source": row.get("source") or row.get("market_line_source"),
        "provenance": "canonical_matchup_line_history",
        "authority": "PROVIDER_OPEN" if explicit else "FIRST_TRACKED_ACCEPTED",
    }


def load_pinnacle_openers(path: Path) -> dict[str, dict[str, Any]]:
    """Read only Pinnacle's first accepted spread/total observations."""
    candidates: dict[tuple[str, str], tuple[datetime, dict[str, Any]]] = {}
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if str(row.get("book") or "").strip().lower() != "pinnacle":
                    continue
                if str(row.get("available") or "true").strip().lower() in {"false", "0", "no"}:
                    continue
                market = str(row.get("market") or "").strip().lower()
                side = str(row.get("side") or "").strip().lower()
                if (market, side) not in {("spread", "home"), ("total", "over")}:
                    continue
                gid = str(row.get("canonical_game_id") or "").strip()
                timestamp = row.get("source_updated_at") or row.get("book_last_updated") or row.get("snapshot_ts")
                if not gid or not timestamp or row.get("line") in (None, ""):
                    continue
                try:
                    parsed = parsed_timestamp(timestamp)
                    line = float(row["line"])
                    price = float(row["price"]) if row.get("price") not in (None, "") else None
                except (TypeError, ValueError):
                    continue
                record = {
                    "market": market, "line": line, "price": price, "book": "Pinnacle",
                    "observed_at": normalized_timestamp(timestamp, str(timestamp)),
                    "source": row.get("source"),
                    "provenance": "canonical_game_book_line_history",
                    "authority": "FIRST_TRACKED_ACCEPTED",
                }
                key = (gid, market)
                if key not in candidates or parsed < candidates[key][0]:
                    candidates[key] = (parsed, record)
    except OSError:
        return {}
    grouped: dict[str, dict[str, Any]] = {}
    for (gid, market), (_, record) in candidates.items():
        grouped.setdefault(gid, {})[market] = record
    return grouped


def game_openers(
    line_history: dict[str, Any], game_id: str,
    pinnacle_openers: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = line_history.get(str(game_id)) or []
    if not isinstance(rows, list):
        rows = []
    return {
        "spread": first_tracked_opener(rows, "spread"),
        "total": first_tracked_opener(rows, "total"),
        "pinnacle_spread": ((pinnacle_openers or {}).get(game_id) or {}).get("spread")
            or first_tracked_opener(rows, "spread", book="Pinnacle"),
        "pinnacle_total": ((pinnacle_openers or {}).get(game_id) or {}).get("total")
            or first_tracked_opener(rows, "total", book="Pinnacle"),
    }


def opener_events(game_id: str, meta: dict[str, Any], openers: dict[str, Any]) -> list[dict[str, Any]]:
    """Project canonical opener summaries into the selected-game market tape."""
    projected = []
    for key, opener in openers.items():
        if not isinstance(opener, dict):
            continue
        is_pinnacle = key.startswith("pinnacle_")
        market = opener.get("market") or ("total" if key.endswith("total") else "spread")
        identity = stable_hash({"game_id": game_id, "key": key, "opener": opener})[:24]
        projected.append({
            "event_id": "wro_" + identity,
            "event_type": "PINNACLE_OPENED" if is_pinnacle else "MARKET_OPENED",
            "event_version": 1,
            "event_timestamp": opener.get("observed_at"),
            "observed_at": opener.get("observed_at"),
            "detected_at": opener.get("observed_at"),
            "created_at": opener.get("observed_at"),
            "source_system": "canonical_market_history",
            "entity_type": "market_opener",
            "entity_id": f"{game_id}|{key}",
            "season": meta.get("season"), "week": meta.get("week"),
            "game_id": game_id, "away_team": meta.get("away_team"),
            "home_team": meta.get("home_team"), "book": opener.get("book"),
            "market": market, "side": "home" if market == "spread" else "over",
            "old_line": None, "new_line": opener.get("line"),
            "old_price": None, "new_price": opener.get("price"),
            "source": opener.get("source"), "significance": "INFORMATIONAL",
            "display_priority": DISPLAY_PRIORITY["PINNACLE_OPENED" if is_pinnacle else "MARKET_OPENED"],
            "underlying_event_ids": [],
            "metadata": {"opening_book": opener.get("book"), "opener_key": key,
                         "provenance": opener.get("provenance"), "authority": opener.get("authority")},
            "payload": {"opening_book": opener.get("book"), "opener_key": key,
                        "provenance": opener.get("provenance"), "authority": opener.get("authority")},
        })
    return sorted(projected, key=lambda row: (row.get("event_timestamp") or "", row["event_id"]), reverse=True)


def prior_game_for_team(
    selected_id: str, selected_meta: dict[str, Any], team: str,
    games_meta: dict[str, Any], events_by_game: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    selected_kickoff = parsed_timestamp(selected_meta.get("kickoff_time"))
    candidates = []
    for gid, meta in games_meta.items():
        if gid == selected_id or team not in {meta.get("away_team"), meta.get("home_team")}:
            continue
        kickoff = meta.get("kickoff_time")
        if not kickoff:
            continue
        try:
            parsed = parsed_timestamp(kickoff)
        except (TypeError, ValueError):
            continue
        if parsed < selected_kickoff:
            candidates.append((parsed, gid, meta))
    if not candidates:
        return {"selected_team": team, "status": "NO_PRIOR_GAME", "game_id": None, "events": []}
    _, gid, meta = max(candidates, key=lambda item: (item[0], item[1]))
    meaningful_types = {"FINAL_POSTED", "MODEL_STATE_CHANGED", "SHADOW_SPREAD_READY", "SHADOW_TOTAL_READY"}
    rows = [row for row in events_by_game.get(gid, []) if row.get("event_type") in meaningful_types]
    deduped = {row.get("event_id"): row for row in rows if row.get("event_id")}
    events = sorted(deduped.values(), key=lambda row: (row.get("event_timestamp") or "", row.get("event_id") or ""), reverse=True)
    has_final = any(row.get("event_type") == "FINAL_POSTED" for row in events)
    has_shadow = any(str(row.get("event_type") or "").startswith("SHADOW_") for row in events)
    has_processed = has_shadow or any(row.get("event_type") == "MODEL_STATE_CHANGED" for row in events)
    status = "SHADOW_READY" if has_shadow else "POSTGAME_PROCESSED" if has_processed else "FINAL_POSTED" if has_final else "NOT_YET_FINAL"
    return {
        "selected_team": team, "status": status, "game_id": gid,
        "season": meta.get("season"), "week": meta.get("week"),
        "kickoff_time": meta.get("kickoff_time"), "neutral_site": meta.get("neutral_site"),
        "away_team": meta.get("away_team"), "home_team": meta.get("home_team"),
        "events": events,
    }


def build_game_index(
    public_events: list[dict[str, Any]], line_history: dict[str, Any],
    games_meta: dict[str, Any], built_at: str, refresh_id: str | None,
    max_events: int = 100, pinnacle_openers: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a bounded derived lookup; the append-only JSONL remains authority."""
    events_by_game: dict[str, list[dict[str, Any]]] = {}
    for row in public_events:
        gid = str(row.get("game_id") or "")
        if gid:
            events_by_game.setdefault(gid, []).append(row)
    game_ids = set(games_meta) | set(events_by_game) | set(line_history)
    games = {}
    for gid in sorted(game_ids):
        meta = games_meta.get(gid) or {}
        rows = events_by_game.get(gid, [])
        openers = game_openers(line_history, gid, pinnacle_openers)
        if not meta and not rows and not any(openers.values()):
            continue
        # Canonical history owns opener events in game mode. Activity-era
        # opener milestones are removed here to prevent duplicate "open" rows.
        rows = [row for row in rows if row.get("event_type") not in {"MARKET_OPENED", "PINNACLE_OPENED"}]
        rows = sorted(opener_events(gid, meta, openers) + rows,
                      key=lambda row: (row.get("event_timestamp") or "", row.get("event_id") or ""), reverse=True)
        games[gid] = {
            "game_id": gid,
            "season": meta.get("season") or (rows[0].get("season") if rows else None),
            "week": meta.get("week") if meta else (rows[0].get("week") if rows else None),
            "away_team": meta.get("away_team") or (rows[0].get("away_team") if rows else None),
            "home_team": meta.get("home_team") or (rows[0].get("home_team") if rows else None),
            "openers": openers,
            "events": rows[:max(1, max_events)],
            "event_count": min(len(rows), max(1, max_events)),
        }
    for gid, row in games.items():
        meta = games_meta.get(gid) or row
        row["prior_games"] = {
            "away": prior_game_for_team(gid, meta, str(row.get("away_team") or ""), games_meta, events_by_game),
            "home": prior_game_for_team(gid, meta, str(row.get("home_team") or ""), games_meta, events_by_game),
        }
    return {
        "schema_version": "war-room-game-activity-index-v1",
        "built_at": built_at,
        "latest_refresh_id": refresh_id,
        "game_count": len(games),
        "max_events_per_game": max(1, max_events),
        "games": games,
    }


def read_history(path: Path) -> list[dict[str, Any]]:
    rows = []
    try:
        for line in path.read_text().splitlines():
            if line.strip(): rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        pass
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--health", type=Path, default=DEFAULT_HEALTH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--postgame", type=Path, default=DEFAULT_POSTGAME)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--line-history", type=Path, default=DEFAULT_LINE_HISTORY)
    parser.add_argument("--game-index-output", type=Path, default=DEFAULT_GAME_INDEX)
    parser.add_argument("--book-history", type=Path, default=DEFAULT_BOOK_HISTORY)
    parser.add_argument("--max-public-events", type=int, default=200)
    parser.add_argument("--max-game-events", type=int, default=100)
    parser.add_argument("--detected-at")
    args = parser.parse_args()
    detected_at = args.detected_at or utc_now()
    matrix = load_json(args.matrix, {})
    health = load_json(args.health, {})
    if matrix.get("schema_version") != "war-room-market-matrix-v1":
        raise SystemExit("War Room activity requires war-room-market-matrix-v1")
    current = current_snapshot(matrix, health, load_json(args.results, {}), load_json(args.postgame, {}))
    args.history.parent.mkdir(parents=True, exist_ok=True)
    lock_path = args.history.with_suffix(args.history.suffix + ".lock")
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        previous = load_json(args.state, {})
        history = read_history(args.history)
        known_ids = {row.get("event_id") for row in history}
        new_events = [] if not previous else [row for row in detect(previous, current, detected_at) if row["event_id"] not in known_ids]
        if new_events:
            with args.history.open("a", encoding="utf-8") as handle:
                for row in sorted(new_events, key=lambda x: (x["observed_at"], x["event_id"])):
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
            history.extend(new_events)
        current["opened_market_keys"] = sorted(set(previous.get("opened_market_keys", [])) | set(current["markets"]))
        current["opened_game_market_keys"] = sorted(
            set(previous.get("opened_game_market_keys", [])) | set(current["opened_game_market_keys"])
        )
        current["first_market_availability"] = first_market_availability(
            previous, current, detected_at
        )
        current["initialized_at"] = previous.get("initialized_at") or detected_at
        current["updated_at"] = detected_at
        atomic_json(args.state, current)
        newest = project_public(history)
        latest_underlying = {event_id for row in new_events for event_id in [row["event_id"]]}
        latest_public = [row for row in newest if latest_underlying.intersection(row.get("underlying_event_ids") or [])]
        recent_change_types = {
            "BEST_SPREAD_CHANGED",
            "BEST_TOTAL_CHANGED",
            "EDGE_BECAME_ACTIONABLE",
            "EDGE_ACTIONABLE_CHANGED",
            "EDGE_LOST_ACTIONABLE",
        }
        recent_change_cutoff = parsed_timestamp(detected_at).timestamp() - (30 * 60)
        recent_change_events = [
            row
            for row in newest
            if row.get("event_type") in recent_change_types
            and parsed_timestamp(
                row.get("detected_at")
                or row.get("created_at")
                or row.get("observed_at")
            ).timestamp() >= recent_change_cutoff
        ]

        payload = {
            "schema_version": "war-room-activity-v1", "built_at": detected_at,
            "latest_refresh_id": current.get("refresh_id"), "event_count": len(history),
            "public_event_count": len(newest), "new_event_count": len(latest_public),
            "latest_refresh_event_ids": [e["event_id"] for e in latest_public],
            "since_last_refresh": public_summary(latest_public),
            "pipeline_refreshes": current.get("pipeline_refreshes"),
            "recent_change_window_minutes": 30,
            "recent_change_events": recent_change_events,
            "events": newest[:max(1, args.max_public_events)],
        }
        line_history = load_json(args.line_history, {})
        game_index = build_game_index(
            newest, line_history if isinstance(line_history, dict) else {},
            current.get("games_meta") or {}, detected_at, current.get("refresh_id"),
            args.max_game_events, load_pinnacle_openers(args.book_history),
        )
        # Static fallback includes only opener summaries and the already-bounded
        # public tape; full per-game history remains lazy through the live API.
        payload["opening_markets"] = {
            gid: row.get("openers") for gid, row in game_index["games"].items()
            if any((row.get("openers") or {}).values())
        }
        atomic_json(args.output, payload)
        atomic_json(args.game_index_output, game_index)
    print(f"activity events: {len(history)} total, {len(new_events)} new")
    print(f"wrote: {args.output}")


if __name__ == "__main__":
    main()
