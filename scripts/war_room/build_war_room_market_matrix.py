#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Allow direct execution from scripts/war_room while reusing the
# canonical market identity resolver from the repo.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.markets.build_current_market_contract import (
    game_key,
    normalize_team,
    resolve_game_id,
    site_date_from_timestamp,
)
from scripts.war_room.build_war_room_activity import (
    game_openers,
    load_pinnacle_openers,
    read_history,
)

FAST_QUOTES = (
    ROOT
    / "data/war_room/odds/theodds_ncaaf_lines_2026_fast.csv"
)

CURRENT_MARKET = (
    ROOT / "data/site/current_market_contract.json"
)

PROJECTIONS = (
    ROOT
    / "data/site/current_game_projection_contract.json"
)

FBS_UNIVERSE = (
    ROOT
    / "data/ratings/ratings_preseason_2026.csv"
)

HEALTH = ROOT / "data/site/war_room_health.json"
SHADOW_COMPONENTS = (
    ROOT
    / "data/site/saturday_shadow_component_predictions.json"
)

GAME_RESULTS = (
    ROOT
    / "data/canonical/game_results_2026.json"
)

RATINGS_SOURCE_STATUS = (
    ROOT
    / "data/ratings/ratings_source_status.csv"
)

LIVE_RATING_CHANGE_STATUS = (
    ROOT
    / "data/ratings/live_rating_change_status.json"
)

PROJECTION_SOURCE_STATUS = (
    ROOT
    / "data/site/projection_source_status_view.json"
)

RATINGS_VIEW = ROOT / "data/site/ratings_view.json"

BETTING_ANGLES = (
    ROOT / "data/signals/game_betting_angles_2026.csv"
)

BETTING_SIGNALS = (
    ROOT / "data/signals/game_betting_signals.csv"
)

OUT = ROOT / "data/site/war_room_market_matrix.json"
MATCHUP_LINE_HISTORY = ROOT / "data/site/matchup_line_history.json"
BOOK_LINE_HISTORY = ROOT / "data/odds/game_book_line_history.csv"
ACTIVITY_HISTORY = ROOT / "data/war_room/history/war_room_events.jsonl"
ACTIVITY_STATE = ROOT / "data/war_room/history/war_room_activity_state.json"
FAST_REFRESH_HISTORY = ROOT / "data/war_room/audits/fast_market_refresh_history.csv"

BETTABLE = (
    "DraftKings",
    "FanDuel",
    "BetMGM",
    "Caesars",
)

EXCHANGES = (
    "Novig",
    "ProphetX",
    "Kalshi",
)

PINNACLE = "Pinnacle"

STANDARD_SPREAD = "standard_spread_five_source_v1"
STANDARD_TOTAL = "standard_total_sp_massey_sagarin_v1"
DEGRADED_SPREAD = "standard_spread_degraded_v1"
DEGRADED_TOTAL = "standard_total_degraded_v1"
SHADOW_SPREAD = "shadow_spread_sp_sagarin_v1"
SHADOW_TOTAL = "shadow_total_enhanced_spplus_od_v1"

BEST_EXCHANGE_MIN_PRICE = -120
MATERIAL_MOVE_THRESHOLD = 0.5
MOVEMENT_RECENCY_MINUTES = {"very_recent": 15, "recent": 45, "older_recent": 90}
OPENER_RECENCY_MINUTES = {"new": 30, "recent": 90}


def number(value):
    if value in (None, ""):
        return None

    try:
        x = float(value)
    except (TypeError, ValueError):
        return None

    if x.is_integer():
        return int(x)

    return x


def bool_value(value):
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }


def price_is_exchange_eligible(price):
    p = number(price)

    if p is None:
        return False

    return p >= BEST_EXCHANGE_MIN_PRICE


def quote_payload(row, *, canonical_game_id, market, side):
    return {
        "game_id": canonical_game_id,
        "provider_game_id": row.get("game_id"),
        "book": row.get("book"),
        "book_key": row.get("book_key"),
        "venue_type": row.get("venue_type"),
        "market": market,
        "side": side,
        "line": number(row.get("point")),
        "price": number(row.get("price")),
        "last_update": row.get("last_update"),
        "pulled_at": row.get("pulled_at"),
        "source": row.get("source"),
        "selection_source": "LATEST_FAST_PULL",
    }


def parse_timestamp(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(
            raw.replace("Z", "+00:00")
        )
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def load_team_composite_ranks(path):
    payload = load_json(path, {})
    ranks = {}
    for row in payload.get("teams", []):
        team = normalize_team(row.get("team"))
        rank = number(row.get("overall_rank"))
        if not team or not isinstance(rank, int) or rank < 1:
            continue
        ranks[team] = rank
    return ranks


def spread_move_direction(old_line, new_line):
    """Describe movement of the displayed spread line, never edge favorability."""
    old = number(old_line)
    new = number(new_line)
    if old is None or new is None:
        return "NEUTRAL"
    if old * new < 0:
        return "NEUTRAL"
    old_magnitude = abs(old)
    new_magnitude = abs(new)
    if new_magnitude > old_magnitude:
        return "UP"
    if new_magnitude < old_magnitude:
        return "DOWN"
    return "NEUTRAL"


def total_move_direction(old_line, new_line):
    old = number(old_line)
    new = number(new_line)
    if old is None or new is None or old == new:
        return "NEUTRAL"
    return "UP" if new > old else "DOWN"


def load_recent_refresh_ids(path, current_refresh_id, limit=3):
    ordered = []
    if current_refresh_id:
        ordered.append(str(current_refresh_id))
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        for row in reversed(rows):
            rid = str(row.get("refresh_id") or "").strip()
            if rid and rid not in ordered:
                ordered.append(rid)
            if len(ordered) >= limit:
                break
    except OSError:
        pass
    return ordered[:limit]


def material_move_index(events):
    """Return the latest qualifying move for each game/book/market pair."""
    grouped = {}
    counts = Counter()
    for row in events:
        if row.get("event_type") not in {"SPREAD_MOVED", "TOTAL_MOVED"}:
            continue
        old = number(row.get("old_line"))
        new = number(row.get("new_line"))
        if old is None or new is None or abs(new - old) < MATERIAL_MOVE_THRESHOLD:
            continue
        gid = str(row.get("game_id") or "")
        book = str(row.get("book") or "")
        market = str(row.get("market") or "")
        if not gid or not book or market not in {"spread", "total"}:
            continue
        key = (gid, book, market)
        counts[key] += 1
        stamp = parse_timestamp(row.get("detected_at")) or datetime.min.replace(tzinfo=timezone.utc)
        identity = str(row.get("event_id") or "")
        if key not in grouped or (stamp, identity) > grouped[key][0]:
            grouped[key] = ((stamp, identity), row)
    return {
        key: bounded_move(row, counts[key] - 1)
        for key, (_, row) in grouped.items()
    }


def bounded_move(row, previous_count=0):
    market = str(row.get("market") or "")
    old = number(row.get("old_line"))
    new = number(row.get("new_line"))
    direction = (
        spread_move_direction(old, new)
        if market == "spread"
        else total_move_direction(old, new)
    )
    return {
        "event_id": row.get("event_id"),
        "detected_refresh_id": row.get("refresh_id"),
        "detected_at": row.get("detected_at"),
        "quote_timestamp": row.get("observed_at"),
        "old_line": old,
        "new_line": new,
        "book": row.get("book"),
        "market": market,
        "side": row.get("side"),
        "direction": direction,
        "magnitude_old": abs(old) if old is not None else None,
        "magnitude_new": abs(new) if new is not None else None,
        "previous_qualifying_moves": max(0, previous_count),
    }


def move_for_displayed_quote(move_index, game_id, quote, market, side):
    """Attach a move only when its book is the currently displayed BEST book."""
    if not isinstance(quote, dict) or not quote.get("book"):
        return None
    move = move_index.get((str(game_id), str(quote["book"]), market))
    if not move:
        return None
    result = dict(move)
    if market == "spread" and side == "away":
        result["old_line"] = -number(move["old_line"])
        result["new_line"] = -number(move["new_line"])
        result["side"] = "away"
        result["direction"] = spread_move_direction(
            result["old_line"], result["new_line"]
        )
    elif market == "total":
        result["side"] = side
    return result


def enrich_best_quotes(best_sportsbook, game_id, move_index):
    enriched = {"spread": {}, "total": {}}
    for market, sides in best_sportsbook.items():
        for side, quote in sides.items():
            if not isinstance(quote, dict):
                enriched[market][side] = quote
                continue
            payload = dict(quote)
            payload["last_material_move"] = move_for_displayed_quote(
                move_index, game_id, quote, market, side
            )
            enriched[market][side] = payload
    return enriched


def enrich_activity_metadata(payload, activity_state, activity_events):
    """Refresh Activity-owned display metadata without rebuilding the market."""
    first_market_state = activity_state.get("first_market_availability") or {}
    move_index = material_move_index(activity_events)
    for game in payload.get("games", []):
        gid = str(game.get("game_id") or "")
        market = game.get("market")
        if not gid or not isinstance(market, dict):
            continue
        market["first_available"] = {
            name: first_market_state.get(f"{gid}|{name}")
            for name in ("spread", "total")
        }
        best = market.get("best_sportsbook")
        if isinstance(best, dict):
            market["best_sportsbook"] = enrich_best_quotes(best, gid, move_index)
    return payload


def enrich_activity_output():
    if not OUT.exists():
        raise SystemExit(f"Missing War Room matrix: {OUT}")
    payload = load_json(OUT, {})
    enrich_activity_metadata(
        payload,
        load_json(ACTIVITY_STATE, {}),
        read_history(ACTIVITY_HISTORY),
    )
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print("WAR ROOM MARKET ACTIVITY ENRICHMENT")
    print("games:", len(payload.get("games", [])))
    print("wrote:", OUT)


def opener_payload(openers, activity_initialized_at):
    result = {}
    activated = parse_timestamp(activity_initialized_at)
    for key, opener in openers.items():
        if not isinstance(opener, dict):
            result[key] = None
            continue
        row = dict(opener)
        observed = parse_timestamp(row.get("observed_at"))
        row["predates_activity_activation"] = (
            observed < activated if observed and activated else None
        )
        result[key] = row
    return result


def current_quote_pair_is_fresh(sides, *, now, max_age_hours):
    if not sides:
        return False

    statuses = {
        quote.get("freshness_status")
        for quote in sides.values()
    }

    if statuses == {"FROZEN_CLOSE"}:
        return True

    for quote in sides.values():
        if quote.get("freshness_status") not in {
            "LIVE",
            "BACKUP_SOURCE",
        }:
            return False

        updated = parse_timestamp(
            quote.get("source_updated_at")
        )
        if updated is None:
            return False

        age_hours = (
            now - updated
        ).total_seconds() / 3600
        if age_hours < -0.25 or age_hours > max_age_hours:
            return False

    return True


def merge_current_market_fallbacks(
    quote_inventory,
    current_payload,
    participating_books,
    *,
    reference_time,
    eligible_game_ids=None,
):
    """Fill exact missing fast slots from the canonical fresh contract.

    The latest fast pull always wins. A fallback is accepted only as a
    complete, internally valid pair whose source timestamp still satisfies
    the canonical current-market age limit at the fast-pull timestamp.
    """
    accepted = []
    rejected = []
    max_age_hours = number(
        current_payload.get("max_quote_age_hours")
    )
    if max_age_hours is None:
        max_age_hours = 18

    now = parse_timestamp(reference_time) or datetime.now(
        timezone.utc
    )
    eligible = (
        set(eligible_game_ids)
        if eligible_game_ids is not None
        else set(quote_inventory)
    )

    for game in current_payload.get("games", []):
        gid = str(game.get("game_id") or "")
        if not gid:
            continue

        is_closing = (
            game.get("availability_status") == "CLOSING"
        )

        if gid not in eligible and not is_closing:
            continue

        for book, book_data in (
            game.get("quotes", {}) or {}
        ).items():
            if book not in participating_books:
                continue

            for market in ("spread", "total"):
                current_sides = dict(
                    (book_data or {}).get(market, {}) or {}
                )
                fast_sides = quote_inventory[gid][book][market]

                if pair_is_valid(market, fast_sides):
                    continue

                reason = None
                if not pair_is_valid(market, current_sides):
                    reason = "INVALID_OR_INCOMPLETE_CURRENT_PAIR"
                elif not current_quote_pair_is_fresh(
                    current_sides,
                    now=now,
                    max_age_hours=max_age_hours,
                ):
                    reason = "STALE_CURRENT_PAIR"

                if reason:
                    if current_sides:
                        rejected.append({
                            "game_id": gid,
                            "book": book,
                            "market": market,
                            "reason": reason,
                        })
                    continue

                replacement = {}
                for side, quote in current_sides.items():
                    replacement[side] = {
                        "game_id": gid,
                        "provider_game_id": None,
                        "book": book,
                        "book_key": None,
                        "venue_type": quote.get("venue_type"),
                        "market": market,
                        "side": side,
                        "line": number(quote.get("line")),
                        "price": number(quote.get("price")),
                        "last_update": quote.get(
                            "source_updated_at"
                        ),
                        "pulled_at": current_payload.get("built_at"),
                        "source": quote.get("source"),
                        "selection_source": (
                            "FROZEN_CLOSE"
                            if quote.get("freshness_status") == "FROZEN_CLOSE"
                            else "CURRENT_MARKET_CONTRACT_FALLBACK"
                        ),
                        "freshness_status": quote.get(
                            "freshness_status"
                        ),
                        "market_lifecycle_state": quote.get(
                            "market_lifecycle_state"
                        ),
                        "kickoff_at": quote.get("kickoff_at"),
                    }

                quote_inventory[gid][book][market] = replacement
                accepted.append({
                    "game_id": gid,
                    "book": book,
                    "market": market,
                    "source": sorted({
                        str(q.get("source") or "")
                        for q in current_sides.values()
                    }),
                    "source_updated_at": max(
                        str(q.get("source_updated_at") or "")
                        for q in current_sides.values()
                    ),
                })

    return accepted, rejected


def pair_is_valid(market, sides):
    if market == "spread":
        if set(sides) != {"away", "home"}:
            return False

        away = number(sides["away"].get("line"))
        home = number(sides["home"].get("line"))

        return (
            away is not None
            and home is not None
            and abs(away + home) <= 0.01
        )

    if market == "total":
        if set(sides) != {"over", "under"}:
            return False

        over = number(sides["over"].get("line"))
        under = number(sides["under"].get("line"))

        return (
            over is not None
            and under is not None
            and abs(over - under) <= 0.01
        )

    return False


def best_quote(
    quotes,
    market,
    side,
    *,
    allowed_books,
    exchange_price_filter=False,
):
    candidates = []

    for book in allowed_books:
        q = quotes.get(book, {}).get(market, {}).get(side)

        if not q:
            continue

        line = number(q.get("line"))
        price = number(q.get("price"))

        if line is None:
            continue

        if (
            exchange_price_filter
            and not price_is_exchange_eligible(price)
        ):
            continue

        if market == "spread":
            score = (
                line,
                price if price is not None else -1000000,
            )

        elif side == "over":
            score = (
                -line,
                price if price is not None else -1000000,
            )

        else:
            score = (
                line,
                price if price is not None else -1000000,
            )

        candidates.append((score, q))

    if not candidates:
        return None

    return max(candidates, key=lambda item: item[0])[1]


def model_resolution(game, model_id):
    if model_id == STANDARD_SPREAD:
        return game.get("operational_projections", {}).get("spread", {})
    if model_id == STANDARD_TOTAL:
        return game.get("operational_projections", {}).get("total", {})
    return game.get("resolved_projections", {}).get(model_id, {})


def model_value(game, model_id, field):
    resolved = model_resolution(game, model_id)

    if resolved.get("selection_status") != "AVAILABLE":
        return None

    return number(resolved.get(field))


def model_summary(game, model_id):
    r = model_resolution(game, model_id)
    selected_model_id = r.get("model_id", model_id)
    projection = (
        game.get("projections", {})
        .get(selected_model_id, {})
    )

    return {
        "model_id": selected_model_id,
        "official_model_id": r.get("official_model_id"),
        "authority": r.get("authority"),
        "operational_degraded_used": r.get(
            "operational_degraded_used",
            False,
        ),
        "selection_status": r.get("selection_status"),
        "selection_reason": r.get("selection_reason"),
        "availability_status": r.get("availability_status"),
        "freshness_timestamp": r.get("freshness_timestamp"),
        "resolution_mode": r.get("resolution_mode"),
        "missing_components": r.get("missing_components"),
        # Presentation metadata only. These are the canonical
        # game-level component projections already used by the
        # projection engine; the War Room never recalculates them.
        "component_values": projection.get("component_values", {}),
        "component_status": projection.get("component_status", {}),
        "weights_used": r.get("weights_used", {}),
    }


def shadow_readiness(component):
    def clean_count(value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 0
        return max(0, min(2, value))

    legacy_count = clean_count(
        component.get(
            "completed_team_update_count"
        )
    )

    spread_flags_present = all(
        key in component for key in
        ("away_spread_shadow_ready", "home_spread_shadow_ready")
    )
    total_flags_present = all(
        key in component for key in
        ("away_total_shadow_ready", "home_total_shadow_ready")
    )
    spread_count = (
        sum(bool(component.get(key)) for key in ("away_spread_shadow_ready", "home_spread_shadow_ready"))
        if spread_flags_present else clean_count(component.get("shadow_spread_updated_team_count", legacy_count))
    )
    total_count = (
        sum(bool(component.get(key)) for key in ("away_total_shadow_ready", "home_total_shadow_ready"))
        if total_flags_present else clean_count(component.get("shadow_total_updated_team_count", legacy_count))
    )

    def state(count):
        if count >= 2:
            return "READY"
        if count == 1:
            return "PARTIAL"
        return "WAITING"

    def net_impact(*fields):
        values = [number(component.get(field)) for field in fields]
        if any(value is None for value in values):
            return None
        return sum(values) / len(values)

    spread_status = state(spread_count)
    total_status = state(total_count)

    if (
        spread_status == "READY"
        or total_status == "READY"
    ):
        overall = "READY"
    elif (
        spread_status == "PARTIAL"
        or total_status == "PARTIAL"
    ):
        overall = "PARTIAL"
    else:
        overall = "WAITING"

    return {
        "completed_team_count": legacy_count,
        "required_team_count": 2,
        "overall_status": overall,

        "spread_completed_team_count":
            spread_count,

        "total_completed_team_count":
            total_count,

        "spread_status":
            spread_status,

        "total_status":
            total_status,

        "away_spread_shadow_ready": bool(component.get("away_spread_shadow_ready")),
        "home_spread_shadow_ready": bool(component.get("home_spread_shadow_ready")),
        "away_total_shadow_ready": bool(component.get("away_total_shadow_ready")),
        "home_total_shadow_ready": bool(component.get("home_total_shadow_ready")),

        "display_ready": (
            component.get(
                "shadow_display_ready"
            ) is True
        ),

        "has_genuine_postgame_update": (
            component.get(
                "has_genuine_postgame_update"
            ) is True
        ),

        "activation_reason": (
            component.get(
                "shadow_activation_reason"
            )
        ),

        "spread_projection_readiness": (
            component.get(
                "spread_projection_readiness"
            )
        ),

        "total_projection_readiness": (
            component.get(
                "total_projection_readiness"
            )
        ),

        "market_readiness_state": (
            component.get(
                "market_readiness_state"
            )
        ),

        "market_readiness_reason": (
            component.get(
                "market_readiness_reason"
            )
        ),

        # Presentation-only metadata copied from the validated Shadow
        # component artifact. The browser does not recalculate model impacts.
        "team_contributions": {
            side: {
                "spread": {
                    "sp_plus_change": component.get(f"{side}_predicted_sp_plus_change"),
                    "sagarin_change": component.get(f"{side}_predicted_sagarin_change"),
                    "net_impact": net_impact(
                        f"{side}_predicted_sp_plus_change",
                        f"{side}_predicted_sagarin_change",
                    ),
                    # Team-perspective sign: a positive accepted rating update
                    # moves the 50/50 next-game spread toward that team. The
                    # home-line orientation is applied only when the two team
                    # contributions are combined by the projection engine.
                    "net_impact_formula": "0.5 * SP+ change + 0.5 * Sagarin change",
                },
                "total": {
                    "offense_change": component.get(f"{side}_predicted_sp_plus_offense_change"),
                    "defense_change": component.get(f"{side}_predicted_sp_plus_defense_change"),
                    "net_impact": net_impact(
                        f"{side}_predicted_sp_plus_offense_change",
                        f"{side}_predicted_sp_plus_defense_change",
                    ),
                    "net_impact_formula": "0.5 * offense change + 0.5 * defense change",
                },
                "component_status": component.get(f"{side}_component_status"),
                "component_reason": component.get(f"{side}_component_reason"),
            }
            for side in ("away", "home")
        },
        "spread_missing_reasons": component.get("spread_missing_reasons") or [],
        "total_missing_reasons": component.get("total_missing_reasons") or [],
    }


def projection_is_available(game, model_id):
    r = model_resolution(game, model_id)
    return r.get("selection_status") == "AVAILABLE"


def refreshed_standard_value(
    game,
    freshness,
    standard_model_id,
    field,
):
    projection = (
        game.get("projections", {})
        .get(standard_model_id, {})
    )

    values = (
        projection.get("component_values")
        or {}
    )

    weights = (
        projection.get("weights")
        or {}
    )

    source_states = (
        freshness.get("sources")
        or {}
    )

    updated = {}

    for component, meta in source_states.items():
        if meta.get("state") != "UPDATED":
            continue

        value = number(
            values.get(component)
        )

        weight = number(
            weights.get(component)
        )

        if value is None or weight is None:
            continue

        updated[component] = {
            "value": value,
            "weight": weight,
        }

    if len(updated) < 2:
        return None

    weight_sum = sum(
        item["weight"]
        for item in updated.values()
    )

    if not weight_sum:
        return None

    blended = sum(
        item["value"]
        * item["weight"]
        for item in updated.values()
    ) / weight_sum

    # Standard Spread component_values are the canonical
    # source-side home margins used by the contract builder;
    # value_home_line uses bookmaker line orientation.
    if field == "value_home_line":
        blended = -blended

    return {
        "value": blended,
        "components": list(updated),
        "weights_used": {
            component: (
                item["weight"]
                / weight_sum
            )
            for component, item in updated.items()
        },
    }


def authority_resolution(
    game,
    component,
    freshness,
    standard_model_id,
    shadow_model_id,
    field,
):
    standard_value = model_value(
        game,
        standard_model_id,
        field,
    )
    standard_resolution = model_resolution(
        game,
        standard_model_id,
    )
    operational_standard_model_id = (
        standard_resolution.get("model_id")
        or standard_model_id
    )

    shadow_value = model_value(
        game,
        shadow_model_id,
        field,
    )

    readiness = shadow_readiness(component)

    temporal_status = freshness.get(
        "temporal_status",
        "PRE_GAME",
    )

    updated_count = int(
        freshness.get("updated_sources")
        or 0
    )

    nominal_count = int(
        freshness.get("nominal_sources")
        or 0
    )

    if shadow_model_id == SHADOW_SPREAD:
        shadow_domain_status = (
            readiness.get("spread_status")
        )
    else:
        shadow_domain_status = (
            readiness.get("total_status")
        )

    shadow_available = (
        shadow_domain_status == "READY"
        and projection_is_available(
            game,
            shadow_model_id,
        )
        and shadow_value is not None
    )

    # Complete nominal Standard model has refreshed.
    if (
        nominal_count > 0
        and updated_count == nominal_count
        and standard_value is not None
    ):
        return {
            "source": "STANDARD",
            "model_id": operational_standard_model_id,
            "official_model_id": standard_model_id,
            "projection_authority": standard_resolution.get("authority"),
            "value": standard_value,
            "status": "ACTIVE",
            "maturity": "UPDATED",
            "model_quality": (
                freshness.get("model_quality")
            ),
            "updated_source_count":
                updated_count,
            "nominal_source_count":
                nominal_count,
            "reason": (
                "all_nominal_standard_sources_"
                "postgame_current"
            ),
        }

    # User-defined HYBRID authority threshold:
    # two or more newly refreshed canonical Standard sources.
    #
    # The authority value uses ONLY those refreshed sources.
    if updated_count >= 2:
        hybrid = refreshed_standard_value(
            game,
            freshness,
            standard_model_id,
            field,
        )

        if hybrid is not None:
            return {
                "source": "STANDARD",
                "model_id": standard_model_id,
                "official_model_id": standard_model_id,
                "projection_authority": "HYBRID_REFRESHED_SOURCES",
                "value": hybrid["value"],
                "status": "ACTIVE",
                "maturity": "HYBRID",
                "model_quality": (
                    freshness.get("model_quality")
                ),
                "updated_source_count":
                    updated_count,
                "nominal_source_count":
                    nominal_count,
                "hybrid_components":
                    hybrid["components"],
                "hybrid_weights_used":
                    hybrid["weights_used"],
                "reason": (
                    "two_plus_updated_standard_"
                    "sources_refreshed_only_blend"
                ),
            }

    # Below the two-source Standard threshold, a fully mature
    # two-team Shadow model is authoritative.
    if shadow_available:
        return {
            "source": "SHADOW",
            "model_id": shadow_model_id,
            "value": shadow_value,
            "status": "ACTIVE",
            "maturity": "SHADOW",
            "model_quality": (
                freshness.get("model_quality")
            ),
            "updated_source_count":
                updated_count,
            "nominal_source_count":
                nominal_count,
            "reason": (
                "full_two_team_shadow_active_"
                "below_standard_hybrid_threshold"
            ),
        }

    # Partial Shadow is diagnostic only and never authoritative.
    # If Standard exists, retain it until Shadow is complete or
    # at least two Standard sources refresh.
    if standard_value is not None:
        if shadow_domain_status == "PARTIAL":
            reason = (
                "shadow_partial_standard_retained"
            )
        elif updated_count == 1:
            reason = (
                "one_updated_standard_source_"
                "below_hybrid_threshold"
            )
        else:
            reason = (
                "shadow_not_ready_standard_retained"
            )

        return {
            "source": "STANDARD",
            "model_id": operational_standard_model_id,
            "official_model_id": standard_model_id,
            "projection_authority": standard_resolution.get("authority"),
            "value": standard_value,
            "status": "ACTIVE",
            "maturity": temporal_status,
            "model_quality": (
                freshness.get("model_quality")
            ),
            "updated_source_count":
                updated_count,
            "nominal_source_count":
                nominal_count,
            "reason": reason,
        }

    return {
        "source": None,
        "model_id": None,
        "value": None,
        "status": "UNAVAILABLE",
        "maturity": temporal_status,
        "model_quality": (
            freshness.get("model_quality")
        ),
        "updated_source_count":
            updated_count,
        "nominal_source_count":
            nominal_count,
        "reason":
            "no_authoritative_projection_available",
    }


def maturity_state(
    game,
    component,
    spread_freshness,
    total_freshness,
    spread_authority,
    total_authority,
):
    readiness = shadow_readiness(component)

    spread_temporal = spread_freshness.get(
        "temporal_status",
        "PRE_GAME",
    )

    total_temporal = total_freshness.get(
        "temporal_status",
        "PRE_GAME",
    )

    temporal_states = {
        spread_temporal,
        total_temporal,
    }

    # The initial Week 0/preseason projection panel is the accepted
    # season baseline, not a carry-forward from a completed weekly
    # cycle. Before any completed-game watermark or genuine Shadow
    # update exists, active Standard authority in both domains is
    # therefore current for this baseline.
    initial_baseline = (
        number(game.get("week")) == 0
        and spread_temporal == "PRE_GAME"
        and total_temporal == "PRE_GAME"
        and spread_freshness.get("watermark_date") is None
        and total_freshness.get("watermark_date") is None
        and spread_authority.get("source") == "STANDARD"
        and spread_authority.get("status") == "ACTIVE"
        and total_authority.get("source") == "STANDARD"
        and total_authority.get("status") == "ACTIVE"
        and readiness["overall_status"] == "WAITING"
        and readiness["has_genuine_postgame_update"] is False
    )

    if initial_baseline:
        return "UPDATED"

    # Both betting markets have completed their Standard
    # postgame refresh cycle.
    if temporal_states == {"UPDATED"}:
        return "UPDATED"

    # At least one Standard market has begun/finished its
    # postgame refresh while the other has not fully matured.
    if (
        "HYBRID" in temporal_states
        or (
            "UPDATED" in temporal_states
            and len(temporal_states) > 1
        )
    ):
        return "HYBRID"

    any_shadow_active = (
        spread_authority.get("source") == "SHADOW"
        or total_authority.get("source") == "SHADOW"
    )

    if any_shadow_active:
        return "SHADOW"

    if readiness["overall_status"] == "PARTIAL":
        return "SHADOW_PARTIAL"

    return "STALE"


def iso_date(value):
    s = str(value or "").strip()
    return s[:10] if len(s) >= 10 else None


def latest_completed_by_team(results_payload):
    out = {}

    for row in results_payload.get("games", []):
        if row.get("completed") is not True:
            continue

        completed_date = iso_date(row.get("date"))
        if not completed_date:
            continue

        for team in (
            row.get("away_team"),
            row.get("home_team"),
        ):
            key = normalize_team(team)

            prior = out.get(key)

            if (
                prior is None
                or completed_date > prior["date"]
            ):
                out[key] = {
                    "date": completed_date,
                    "game_id": row.get("game_id"),
                }

    return out


def game_freshness_watermark(game, completed_by_team):
    away = completed_by_team.get(
        normalize_team(game.get("away_team"))
    )
    home = completed_by_team.get(
        normalize_team(game.get("home_team"))
    )

    dates = [
        x.get("date")
        for x in (away, home)
        if x and x.get("date")
    ]

    return {
        "away": away,
        "home": home,
        "completed_team_count": len(dates),
        "watermark_date": max(dates) if dates else None,
    }


def source_date_state(
    snapshot_date,
    watermark_date,
    *,
    change_status=None,
    last_changed_at=None,
    comparison_available=None,
):
    if not watermark_date:
        return "PRE_GAME"

    if not snapshot_date:
        return "UNKNOWN"

    # A later observation/pull date proves availability, not a changed
    # provider state. Authority freshness requires explicit accepted change
    # evidence from the owning source pipeline and a change timestamp after
    # the applicable completed-game watermark. Missing evidence fails closed.
    accepted_change = (
        str(change_status or "").strip().upper() == "UPDATED"
        and comparison_available is True
    )
    changed_date = iso_date(last_changed_at)

    if (
        accepted_change
        and changed_date
        and changed_date > watermark_date
    ):
        return "UPDATED"

    return "STALE"


def load_team_source_snapshots(
    path,
    change_status_path=LIVE_RATING_CHANGE_STATUS,
):
    out = {}

    change_sources = {}
    if change_status_path.exists():
        try:
            change_payload = json.loads(
                change_status_path.read_text()
            )
            change_sources = (
                change_payload.get("sources") or {}
            )
        except (OSError, json.JSONDecodeError):
            change_sources = {}

    if not path.exists():
        return out

    with path.open(
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        for row in csv.DictReader(handle):
            source = str(row.get("source") or "").strip()
            if not source:
                continue

            accepted_change = change_sources.get(source, {})

            def row_or_change(field):
                value = row.get(field)
                if value not in (None, ""):
                    return value
                return accepted_change.get(field)

            out[source] = {
                "snapshot_date": iso_date(
                    row.get("snapshot_date")
                ),
                "pulled_at": row.get("pulled_at"),
                "latest_pull_at": row.get("latest_pull_at"),
                "display_status": row.get("display_status"),
                "change_status": row_or_change("change_status"),
                "last_changed_at": row_or_change("last_changed_at"),
                "teams_changed": number(
                    row_or_change("teams_changed")
                ),
                "changed_fields": number(
                    row_or_change("changed_fields")
                ),
                "comparison_available": bool_value(
                    row_or_change("comparison_available")
                ),
            }

    return out


def load_game_feed_snapshots(payload):
    out = {}

    for row in payload.get("game_prediction_feeds", []):
        source_key = str(
            row.get("source_key") or ""
        ).strip()

        if not source_key:
            continue

        out[source_key] = {
            "snapshot_date": iso_date(
                row.get("latest_snapshot_date")
            ),
            "pulled_at": row.get("latest_pulled_at"),
            "state": row.get("state"),
            # Game-feed pulls do not count as authority updates unless their
            # owning pipeline supplies explicit accepted version-change
            # evidence. Current DRatings/Massey status rows omit these fields
            # and therefore correctly fail closed while remaining available.
            "change_status": row.get("change_status"),
            "last_changed_at": row.get("last_changed_at"),
            "comparison_available": bool_value(
                row.get("comparison_available")
            ),
        }

    return out


TEAM_SOURCE_MAP = {
    "SP+": "SP+",
    "FPI": "FPI",
    "TeamRankings": "TeamRankings",
    "Sagarin Rating": "Sagarin Rating",
}

GAME_FEED_MAP = {
    "DRatings": "DRatings Predictions",
    "Massey Dual": "Massey Games",
    "Sagarin Total": "Sagarin Game Total",
}


def model_freshness(
    game,
    model_id,
    watermark,
    team_source_snapshots,
    game_feed_snapshots,
):
    resolved = game.get(
        "resolved_projections",
        {}
    ).get(model_id, {})

    component_status = (
        resolved.get("component_status") or {}
    )

    watermark_date = watermark.get("watermark_date")

    nominal = []
    participating = []
    sources = {}

    for component, status in component_status.items():
        # Ignore formula/activation metadata.
        if component not in TEAM_SOURCE_MAP and component not in GAME_FEED_MAP:
            continue

        nominal.append(component)

        present = status == "PRESENT"

        if present:
            participating.append(component)

        if component in TEAM_SOURCE_MAP:
            source_key = TEAM_SOURCE_MAP[component]
            meta = team_source_snapshots.get(
                source_key,
                {},
            )
        else:
            source_key = GAME_FEED_MAP[component]
            meta = game_feed_snapshots.get(
                source_key,
                {},
            )

        snapshot_date = meta.get("snapshot_date")

        if not present:
            state = "MISSING"
        else:
            state = source_date_state(
                snapshot_date,
                watermark_date,
                change_status=meta.get("change_status"),
                last_changed_at=meta.get("last_changed_at"),
                comparison_available=meta.get("comparison_available"),
            )

        sources[component] = {
            "source_key": source_key,
            "participating": present,
            "state": state,
            "snapshot_date": snapshot_date,
            "pulled_at": (
                meta.get("pulled_at")
                or meta.get("latest_pull_at")
            ),
            "change_status": meta.get("change_status"),
            "last_changed_at": meta.get("last_changed_at"),
            "comparison_available": meta.get("comparison_available"),
        }

    participating_states = [
        sources[source]["state"]
        for source in participating
    ]

    updated_count = sum(
        state == "UPDATED"
        for state in participating_states
    )

    participating_count = len(participating)

    nominal_count = len(nominal)

    if watermark_date is None:
        temporal_status = "PRE_GAME"
    elif participating_count == 0:
        temporal_status = "UNAVAILABLE"
    elif (
        nominal_count > 0
        and updated_count == nominal_count
    ):
        temporal_status = "UPDATED"
    elif updated_count >= 2:
        temporal_status = "HYBRID"
    else:
        temporal_status = "STALE"

    resolution_mode = resolved.get("resolution_mode")

    model_quality = (
        "DEGRADED"
        if resolution_mode == "DEGRADED_RENORMALIZED"
        else "FULL"
        if resolved.get("selection_status") == "AVAILABLE"
        else "UNAVAILABLE"
    )

    return {
        "watermark_date": watermark_date,
        "temporal_status": temporal_status,
        "model_quality": model_quality,
        "participating_sources": participating_count,
        "updated_sources": updated_count,
        "nominal_sources": len(nominal),
        "authority_stage": (
            "UPDATED"
            if (
                len(nominal) > 0
                and updated_count == len(nominal)
            )
            else "HYBRID_AUTHORITY"
            if updated_count >= 2
            else "BELOW_HYBRID_THRESHOLD"
            if updated_count == 1
            else "STALE"
        ),
        "sources": sources,
    }



def spread_edges(model_home_line, best):
    if model_home_line is None:
        return {
            "away": None,
            "home": None,
            "best_side": None,
            "best_edge": None,
        }

    away_q = best.get("away")
    home_q = best.get("home")

    away_edge = None
    home_edge = None

    if away_q and number(away_q.get("line")) is not None:
        away_edge = round(
            number(away_q["line"]) - (-model_home_line),
            3,
        )

    if home_q and number(home_q.get("line")) is not None:
        home_edge = round(
            number(home_q["line"]) - model_home_line,
            3,
        )

    choices = []

    if away_edge is not None:
        choices.append(("away", away_edge))

    if home_edge is not None:
        choices.append(("home", home_edge))

    if not choices:
        return {
            "away": away_edge,
            "home": home_edge,
            "best_side": None,
            "best_edge": None,
        }

    best_side, best_edge = max(
        choices,
        key=lambda item: item[1],
    )

    return {
        "away": away_edge,
        "home": home_edge,
        "best_side": best_side,
        "best_edge": best_edge,
    }


def total_edges(model_total, best):
    if model_total is None:
        return {
            "over": None,
            "under": None,
            "best_side": None,
            "best_edge": None,
        }

    over_q = best.get("over")
    under_q = best.get("under")

    over_edge = None
    under_edge = None

    if over_q and number(over_q.get("line")) is not None:
        over_edge = round(
            model_total - number(over_q["line"]),
            3,
        )

    if under_q and number(under_q.get("line")) is not None:
        under_edge = round(
            number(under_q["line"]) - model_total,
            3,
        )

    choices = []

    if over_edge is not None:
        choices.append(("over", over_edge))

    if under_edge is not None:
        choices.append(("under", under_edge))

    if not choices:
        return {
            "over": over_edge,
            "under": under_edge,
            "best_side": None,
            "best_edge": None,
        }

    best_side, best_edge = max(
        choices,
        key=lambda item: item[1],
    )

    return {
        "over": over_edge,
        "under": under_edge,
        "best_side": best_side,
        "best_edge": best_edge,
    }



def load_team_betting_signals():
    by_game = defaultdict(lambda: defaultdict(list))

    if BETTING_ANGLES.exists():
        with BETTING_ANGLES.open(
            newline="",
            encoding="utf-8-sig",
        ) as f:
            for row in csv.DictReader(f):
                gid = str(row.get("game_id") or "")
                team = str(row.get("side_team") or "").strip()

                if not gid or not team:
                    continue

                by_game[gid][team].append({
                    "source_type": "betting_angle",
                    "signal_type": row.get("angle_key"),
                    "label": row.get("angle_label"),
                    "tier": row.get("tier"),
                    "reason": row.get("reason"),
                })

    if BETTING_SIGNALS.exists():
        with BETTING_SIGNALS.open(
            newline="",
            encoding="utf-8-sig",
        ) as f:
            for row in csv.DictReader(f):
                gid = str(row.get("game_id") or "")
                team = str(row.get("team") or "").strip()

                if not gid or not team:
                    continue

                by_game[gid][team].append({
                    "source_type": "betting_signal",
                    "signal_group": row.get("signal_group"),
                    "signal_type": row.get("signal_type"),
                    "strength": row.get("strength"),
                    "confidence": row.get("confidence"),
                    "headline": row.get("headline"),
                })

    return by_game


def compact_signal_summary(game, signal_map):
    gid = str(game.get("game_id") or "")

    away = str(game.get("away_team") or "")
    home = str(game.get("home_team") or "")

    game_signals = signal_map.get(gid, {})

    away_rows = list(game_signals.get(away, []))
    home_rows = list(game_signals.get(home, []))

    return {
        "away": {
            "team": away,
            "count": len(away_rows),
            "signals": away_rows,
        },
        "home": {
            "team": home,
            "count": len(home_rows),
            "signals": home_rows,
        },
        "total_count": len(away_rows) + len(home_rows),
    }



def load_fbs_team_universe():
    if not FBS_UNIVERSE.exists():
        raise SystemExit(
            f"Missing canonical 2026 FBS universe: {FBS_UNIVERSE}"
        )

    teams = set()

    with FBS_UNIVERSE.open(
        newline="",
        encoding="utf-8-sig",
    ) as f:
        for row in csv.DictReader(f):
            team = str(row.get("team") or "").strip()

            if team:
                teams.add(normalize_team(team))

    if len(teams) < 130:
        raise SystemExit(
            f"Unexpected FBS universe size: {len(teams)}"
        )

    return teams


def market_universe_counts(games_out, fast_board_game_ids):
    return {
        "matrix_games": len(games_out),
        "fast_market_games_matched": len(fast_board_game_ids),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--activity-enrichment-only",
        action="store_true",
        help="Refresh Activity-derived matrix metadata without resolving quotes",
    )
    args = parser.parse_args()
    if args.activity_enrichment_only:
        enrich_activity_output()
        return

    if not FAST_QUOTES.exists():
        raise SystemExit(f"Missing fast quotes: {FAST_QUOTES}")

    if not PROJECTIONS.exists():
        raise SystemExit(
            f"Missing projection contract: {PROJECTIONS}"
        )

    if not HEALTH.exists():
        raise SystemExit(f"Missing War Room health: {HEALTH}")

    projection_payload = json.loads(PROJECTIONS.read_text())
    health_payload = json.loads(HEALTH.read_text())
    current_market_payload = (
        json.loads(CURRENT_MARKET.read_text())
        if CURRENT_MARKET.exists()
        else {"games": []}
    )
    line_history_payload = load_json(MATCHUP_LINE_HISTORY, {})
    pinnacle_openers = load_pinnacle_openers(BOOK_LINE_HISTORY)
    activity_state = load_json(ACTIVITY_STATE, {})
    first_market_state = activity_state.get("first_market_availability") or {}
    move_index = material_move_index(read_history(ACTIVITY_HISTORY))

    shadow_component_payload = (
        json.loads(SHADOW_COMPONENTS.read_text())
        if SHADOW_COMPONENTS.exists()
        else {}
    )

    shadow_components_by_gid = {
        str(row.get("game_id")): row
        for row in shadow_component_payload.get("games", [])
        if row.get("game_id") is not None
    }

    results_payload = (
        json.loads(GAME_RESULTS.read_text())
        if GAME_RESULTS.exists()
        else {"games": []}
    )

    completed_by_team = latest_completed_by_team(
        results_payload
    )

    team_source_snapshots = load_team_source_snapshots(
        RATINGS_SOURCE_STATUS
    )

    projection_source_payload = (
        json.loads(PROJECTION_SOURCE_STATUS.read_text())
        if PROJECTION_SOURCE_STATUS.exists()
        else {}
    )

    game_feed_snapshots = load_game_feed_snapshots(
        projection_source_payload
    )

    fbs_teams = load_fbs_team_universe()
    team_composite_ranks = load_team_composite_ranks(RATINGS_VIEW)
    betting_signal_map = load_team_betting_signals()

    projection_games = projection_payload.get("games", [])

    identity = {}
    key_to_game_id = {}
    projection_by_gid = {}

    for game in projection_games:
        gid = str(game.get("game_id") or "")

        if not gid:
            continue

        projection_by_gid[gid] = game

        identity[gid] = {
            "game_id": gid,
            "date": str(game.get("date") or "")[:10],
            "week": game.get("week"),
            "away_team": game.get("away_team"),
            "home_team": game.get("home_team"),
        }

        key_to_game_id[
            game_key(
                game.get("date"),
                game.get("away_team"),
                game.get("home_team"),
            )
        ] = gid

    fast_health = health_payload.get(
        "fast_market_refresh",
        {},
    )

    refresh_id = fast_health.get("refresh_id")
    last_fast_pull_at = fast_health.get(
        "last_fast_pull_at"
    )

    health_books = health_payload.get("books", {})

    participating_books = {
        book
        for book, info in health_books.items()
        if info.get("participated_in_last_fast_pull")
    }

    quote_inventory = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(dict)
        )
    )

    provider_ids = defaultdict(set)
    fast_board_game_ids = set()

    unmatched = []
    invalid_rows = []
    exchange_price_rejections = []
    post_kickoff_fast_quotes = []
    resolution_cache = {}
    commence_by_gid = {}

    with FAST_QUOTES.open(
        newline="",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            local_date = site_date_from_timestamp(
                row.get("commence_time")
            )

            date_candidates = [
                local_date,
                str(row.get("commence_time") or "")[:10],
            ]

            resolution_key = (
                str(row.get("game_id") or ""),
                str(row.get("commence_time") or ""),
                str(row.get("away_team") or ""),
                str(row.get("home_team") or ""),
            )
            if resolution_key not in resolution_cache:
                resolution_cache[resolution_key] = resolve_game_id(
                    date_candidates,
                    row.get("away_team"),
                    row.get("home_team"),
                    identity,
                    key_to_game_id,
                )
            gid, match_method, reversed_orientation = resolution_cache[
                resolution_key
            ]

            if not gid:
                unmatched.append({
                    "provider_game_id": row.get("game_id"),
                    "commence_time": row.get(
                        "commence_time"
                    ),
                    "away_team": row.get("away_team"),
                    "home_team": row.get("home_team"),
                })
                continue

            fast_board_game_ids.add(gid)
            if gid not in commence_by_gid:
                commence_by_gid[gid] = row.get("commence_time")

            quote_updated = parse_timestamp(
                row.get("last_update")
                or row.get("pulled_at")
            )
            kickoff = parse_timestamp(
                row.get("commence_time")
            )

            if (
                quote_updated is not None
                and kickoff is not None
                and quote_updated >= kickoff
            ):
                post_kickoff_fast_quotes.append({
                    "game_id": gid,
                    "provider_game_id": row.get("game_id"),
                    "book": row.get("book"),
                    "market": row.get("market"),
                    "side": row.get("side"),
                    "source_updated_at": (
                        row.get("last_update")
                        or row.get("pulled_at")
                    ),
                    "commence_time": row.get("commence_time"),
                })
                continue

            raw_market = str(
                row.get("market") or ""
            ).lower()

            market = {
                "spreads": "spread",
                "spread": "spread",
                "totals": "total",
                "total": "total",
            }.get(raw_market)

            if market not in {"spread", "total"}:
                continue

            raw_side = str(
                row.get("side") or ""
            ).strip()

            side = None

            if market == "spread":
                if (
                    normalize_team(raw_side)
                    == normalize_team(row.get("away_team"))
                ):
                    provider_side = "away"

                elif (
                    normalize_team(raw_side)
                    == normalize_team(row.get("home_team"))
                ):
                    provider_side = "home"

                else:
                    invalid_rows.append({
                        "reason": "unrecognized_spread_side",
                        "provider_game_id": row.get("game_id"),
                        "book": row.get("book"),
                        "side": raw_side,
                    })
                    continue

                if reversed_orientation:
                    side = (
                        "home"
                        if provider_side == "away"
                        else "away"
                    )
                else:
                    side = provider_side

            else:
                low = raw_side.lower()

                if low == "over":
                    side = "over"

                elif low == "under":
                    side = "under"

                else:
                    invalid_rows.append({
                        "reason": "unrecognized_total_side",
                        "provider_game_id": row.get("game_id"),
                        "book": row.get("book"),
                        "side": raw_side,
                    })
                    continue

            book = row.get("book")

            if not book:
                continue

            if book not in participating_books:
                continue

            q = quote_payload(
                row,
                canonical_game_id=gid,
                market=market,
                side=side,
            )

            # If provider orientation was reversed, spread line
            # itself remains attached to the named team, so only
            # side identity changes. No sign inversion is needed.
            quote_inventory[gid][book][market][side] = q

            provider_ids[gid].add(
                row.get("game_id")
            )

            if (
                book in EXCHANGES
                and not price_is_exchange_eligible(
                    q.get("price")
                )
            ):
                exchange_price_rejections.append({
                    "game_id": gid,
                    "provider_game_id": row.get("game_id"),
                    "book": book,
                    "market": market,
                    "side": side,
                    "line": q.get("line"),
                    "price": q.get("price"),
                    "reason": (
                        "PRICE_WORSE_THAN_MINUS_120"
                    ),
                })

    current_market_fallbacks, current_market_fallback_rejections = (
        merge_current_market_fallbacks(
            quote_inventory,
            current_market_payload,
            participating_books,
            reference_time=last_fast_pull_at,
            eligible_game_ids=fast_board_game_ids,
        )
    )

    # Every canonical FBS-vs-FBS game belongs in the War Room matrix,
    # even before a sportsbook posts a market. Market fallback eligibility
    # remains restricted to games actually present on the fast board.
    for game in projection_games:
        gid = str(game.get("game_id") or "")
        if not gid:
            continue

        away = normalize_team(game.get("away_team"))
        home = normalize_team(game.get("home_team"))

        if away not in fbs_teams or home not in fbs_teams:
            continue

        quote_inventory[gid]

    games_out = []

    pair_validation_failures = []

    for gid, quotes in quote_inventory.items():
        game = projection_by_gid.get(gid)

        if not game:
            continue

        # Validate individual book pairs for diagnostics.
        for book, book_data in quotes.items():
            for market in ("spread", "total"):
                sides = book_data.get(market, {})

                if sides and not pair_is_valid(
                    market,
                    sides,
                ):
                    pair_validation_failures.append({
                        "game_id": gid,
                        "book": book,
                        "market": market,
                        "sides": sides,
                    })

        best_sportsbook = {
            "spread": {
                "away": best_quote(
                    quotes,
                    "spread",
                    "away",
                    allowed_books=BETTABLE,
                ),
                "home": best_quote(
                    quotes,
                    "spread",
                    "home",
                    allowed_books=BETTABLE,
                ),
            },
            "total": {
                "over": best_quote(
                    quotes,
                    "total",
                    "over",
                    allowed_books=BETTABLE,
                ),
                "under": best_quote(
                    quotes,
                    "total",
                    "under",
                    allowed_books=BETTABLE,
                ),
            },
        }
        best_sportsbook = enrich_best_quotes(
            best_sportsbook,
            gid,
            move_index,
        )

        best_exchange = {
            "spread": {
                "away": best_quote(
                    quotes,
                    "spread",
                    "away",
                    allowed_books=EXCHANGES,
                    exchange_price_filter=True,
                ),
                "home": best_quote(
                    quotes,
                    "spread",
                    "home",
                    allowed_books=EXCHANGES,
                    exchange_price_filter=True,
                ),
            },
            "total": {
                "over": best_quote(
                    quotes,
                    "total",
                    "over",
                    allowed_books=EXCHANGES,
                    exchange_price_filter=True,
                ),
                "under": best_quote(
                    quotes,
                    "total",
                    "under",
                    allowed_books=EXCHANGES,
                    exchange_price_filter=True,
                ),
            },
        }

        pinnacle = {
            "spread": quotes.get(
                PINNACLE,
                {},
            ).get("spread"),
            "total": quotes.get(
                PINNACLE,
                {},
            ).get("total"),
        }

        model_home_line = model_value(
            game,
            STANDARD_SPREAD,
            "value_home_line",
        )

        model_total = model_value(
            game,
            STANDARD_TOTAL,
            "value_total",
        )

        shadow_home_line = model_value(
            game,
            SHADOW_SPREAD,
            "value_home_line",
        )

        shadow_total = model_value(
            game,
            SHADOW_TOTAL,
            "value_total",
        )

        shadow_component = shadow_components_by_gid.get(
            gid,
            {},
        )

        freshness_watermark = game_freshness_watermark(
            game,
            completed_by_team,
        )

        spread_freshness = model_freshness(
            game,
            STANDARD_SPREAD,
            freshness_watermark,
            team_source_snapshots,
            game_feed_snapshots,
        )

        total_freshness = model_freshness(
            game,
            STANDARD_TOTAL,
            freshness_watermark,
            team_source_snapshots,
            game_feed_snapshots,
        )

        spread_authority = authority_resolution(
            game,
            shadow_component,
            spread_freshness,
            STANDARD_SPREAD,
            SHADOW_SPREAD,
            "value_home_line",
        )

        total_authority = authority_resolution(
            game,
            shadow_component,
            total_freshness,
            STANDARD_TOTAL,
            SHADOW_TOTAL,
            "value_total",
        )

        spread_edge = spread_edges(
            spread_authority.get("value"),
            best_sportsbook["spread"],
        )

        total_edge = total_edges(
            total_authority.get("value"),
            best_sportsbook["total"],
        )

        standard_spread_edge = spread_edges(
            model_home_line,
            best_sportsbook["spread"],
        )

        shadow_spread_edge = spread_edges(
            shadow_home_line,
            best_sportsbook["spread"],
        )

        standard_total_edge = total_edges(
            model_total,
            best_sportsbook["total"],
        )

        shadow_total_edge = total_edges(
            shadow_total,
            best_sportsbook["total"],
        )

        primary_books = {}

        for book in BETTABLE:
            if book in quotes:
                primary_books[book] = {
                    "spread": quotes[book].get(
                        "spread"
                    ),
                    "total": quotes[book].get(
                        "total"
                    ),
                }

        exchange_books = {}

        for book in EXCHANGES:
            if book not in quotes:
                continue

            exchange_books[book] = {
                "spread": quotes[book].get(
                    "spread"
                ),
                "total": quotes[book].get(
                    "total"
                ),
            }

        executable_edges = []

        if spread_edge["best_edge"] is not None:
            executable_edges.append({
                "market": "spread",
                "side": spread_edge["best_side"],
                "edge": spread_edge["best_edge"],
            })

        if total_edge["best_edge"] is not None:
            executable_edges.append({
                "market": "total",
                "side": total_edge["best_side"],
                "edge": total_edge["best_edge"],
            })

        best_action = (
            max(
                executable_edges,
                key=lambda item: item["edge"],
            )
            if executable_edges
            else None
        )

        games_out.append({
            "game_id": gid,
            "season": game.get("season"),
            "week": game.get("week"),
            "date": game.get("date"),
            "kickoff_time": None,
            "away_team": game.get("away_team"),
            "home_team": game.get("home_team"),
            "team_composite_rank": {
                "away": team_composite_ranks.get(
                    normalize_team(game.get("away_team"))
                ),
                "home": team_composite_ranks.get(
                    normalize_team(game.get("home_team"))
                ),
                "source": "ratings_view.teams.overall_rank",
            },
            "neutral_site": game.get("neutral_site"),
            "provider_game_ids": sorted(
                x
                for x in provider_ids.get(gid, set())
                if x
            ),

            "scope": {
                "away_fbs": (
                    normalize_team(game.get("away_team"))
                    in fbs_teams
                ),
                "home_fbs": (
                    normalize_team(game.get("home_team"))
                    in fbs_teams
                ),
                "fbs_vs_fbs": (
                    normalize_team(game.get("away_team"))
                    in fbs_teams
                    and
                    normalize_team(game.get("home_team"))
                    in fbs_teams
                ),
            },

            # We do not manufacture a release timestamp from the
            # current snapshot. This must come from canonical opener /
            # line-history data when wired later.
            "market_release_timestamp": None,

            "state": maturity_state(
                game,
                shadow_component,
                spread_freshness,
                total_freshness,
                spread_authority,
                total_authority,
            ),

            "shadow_readiness": shadow_readiness(
                shadow_component
            ),

            "standard_freshness": {
                "watermark": freshness_watermark,
                "spread": spread_freshness,
                "total": total_freshness,
            },

            "authority": {
                "spread": spread_authority,
                "total": total_authority,
            },

            "models": {
                "standard_spread": {
                    **model_summary(
                        game,
                        STANDARD_SPREAD,
                    ),
                    "value_home_line": model_home_line,
                },
                "standard_total": {
                    **model_summary(
                        game,
                        STANDARD_TOTAL,
                    ),
                    "value_total": model_total,
                },
                "shadow_spread": {
                    **model_summary(
                        game,
                        SHADOW_SPREAD,
                    ),
                    "value_home_line": shadow_home_line,
                },
                "shadow_total": {
                    **model_summary(
                        game,
                        SHADOW_TOTAL,
                    ),
                    "value_total": shadow_total,
                },
            },

            "market": {
                "primary_sportsbooks": primary_books,
                "best_sportsbook": best_sportsbook,
                "exchanges": exchange_books,
                "best_exchange": best_exchange,
                "pinnacle": pinnacle,
                "openers": opener_payload(
                    game_openers(
                        line_history_payload,
                        gid,
                        pinnacle_openers,
                    ),
                    activity_state.get("initialized_at"),
                ),
                "first_available": {
                    market: first_market_state.get(f"{gid}|{market}")
                    for market in ("spread", "total")
                },
            },

            "edges": {
                "spread": spread_edge,
                "total": total_edge,
                "best_action": best_action,
                "comparisons": {
                    "standard_spread": standard_spread_edge,
                    "shadow_spread": shadow_spread_edge,
                    "standard_total": standard_total_edge,
                    "shadow_total": shadow_total_edge,
                },
            },

            "betting_signals": compact_signal_summary(
                game,
                betting_signal_map,
            ),

            "injury_rank": {
                "away": None,
                "home": None,
                "status": "SOURCE_NOT_CONFIGURED",
            },
        })

    completed_kickoff_by_gid = {
        str(row.get("game_id")): row.get("start_date")
        for row in results_payload.get("games", [])
        if row.get("completed") is True
        and row.get("game_id") is not None
        and row.get("start_date")
    }

    for game in games_out:
        gid = str(game["game_id"])
        game["kickoff_time"] = (
            commence_by_gid.get(gid)
            or completed_kickoff_by_gid.get(gid)
        )

    games_out.sort(
        key=lambda g: (
            g.get("week")
            if g.get("week") is not None
            else 999,
            g.get("kickoff_time") or "",
            g.get("away_team") or "",
        )
    )

    state_counts = Counter(
        g.get("state")
        for g in games_out
    )

    payload = {
        "schema_version": "war-room-market-matrix-v1",
        "built_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "season": projection_payload.get(
            "season",
            2026,
        ),

        "fast_market_refresh": {
            "refresh_id": refresh_id,
            "last_fast_pull_at": last_fast_pull_at,
            "source": "The Odds API",
            "markets": [
                "spread",
                "total",
            ],
            "recent_completed_refresh_ids": load_recent_refresh_ids(
                FAST_REFRESH_HISTORY,
                refresh_id,
            ),
        },

        "matrix_alert_policy": {
            "material_move_threshold_points": MATERIAL_MOVE_THRESHOLD,
            "movement_recency_minutes": MOVEMENT_RECENCY_MINUTES,
            "opener_recency_minutes": OPENER_RECENCY_MINUTES,
            "movement_generation_count": 3,
            "movement_generation_rule": (
                "latest refresh is very recent; two immediately preceding "
                "refresh generations are recent, subject to 90-minute expiry"
            ),
            "movement_scope": "CURRENT_BEST_SPORTSBOOK_ONLY_NO_EXCHANGES",
            "opener_authority": "EARLIEST_ACCEPTED_CANONICAL_LINE_HISTORY",
        },

        "selection_policy": {
            "latest_fast_pull_priority": (
                "Latest accepted fast quote pair always wins."
            ),
            "missing_pair_fallback": (
                "An exact missing or invalid fast pair may be filled only "
                "from the canonical current-market contract when the pair "
                "is complete, internally valid, and still satisfies the "
                "canonical quote-age limit at the fast-pull timestamp."
            ),
            "bettable_sportsbooks": list(BETTABLE),
            "exchanges": list(EXCHANGES),
            "sharp_reference": PINNACLE,
            "best_exchange_minimum_price": (
                BEST_EXCHANGE_MIN_PRICE
            ),
            "best_exchange_price_rule": (
                "Only an exchange quote priced -120 or better "
                "may compete for Best Exchange. Raw exchange "
                "quotes remain preserved."
            ),
            "best_sportsbook_price_rule": (
                "No -120 exchange filter is applied to the "
                "primary sportsbook group."
            ),
            "pinnacle_price_rule": (
                "Pinnacle is a separate sharp reference and "
                "is not subject to the Best Exchange filter."
            ),
            "pinnacle_matrix_display": (
                "Pinnacle remains canonical history and Activity context; "
                "the permanent matrix column displays the general opener."
            ),
        },

        "model_policy": {
            "standard_spread_model": STANDARD_SPREAD,
            "standard_total_model": STANDARD_TOTAL,
            "operational_degraded_spread_model": DEGRADED_SPREAD,
            "operational_degraded_total_model": DEGRADED_TOTAL,
            "shadow_spread_model": SHADOW_SPREAD,
            "shadow_total_model": SHADOW_TOTAL,
            "source": (
                "current_game_projection_contract.json "
                "strict resolved_projections plus explicit "
                "operational_projections"
            ),
        },

        "summary": {
            "canonical_projection_games": len(
                projection_games
            ),
            **market_universe_counts(
                games_out,
                fast_board_game_ids,
            ),
            "unmatched_fast_rows": len(unmatched),
            "invalid_fast_rows": len(invalid_rows),
            "invalid_book_pairs": len(
                pair_validation_failures
            ),
            "exchange_quotes_rejected_by_price": len(
                exchange_price_rejections
            ),
            "current_market_fallback_pairs": len(
                current_market_fallbacks
            ),
            "current_market_fallback_rejections": len(
                current_market_fallback_rejections
            ),
            "state_counts": dict(state_counts),
            "fbs_vs_fbs_games": sum(
                1
                for g in games_out
                if g.get("scope", {}).get("fbs_vs_fbs")
            ),
            "other_games": sum(
                1
                for g in games_out
                if not g.get("scope", {}).get("fbs_vs_fbs")
            ),
        },

        "games": games_out,

        "audit": {
            "unmatched_fast_rows": unmatched,
            "invalid_fast_rows": invalid_rows,
            "invalid_book_pairs": (
                pair_validation_failures
            ),
            "exchange_price_rejections": (
                exchange_price_rejections
            ),
            "current_market_fallbacks": (
                current_market_fallbacks
            ),
            "current_market_fallback_rejections": (
                current_market_fallback_rejections
            ),
        },
    }

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUT.write_text(
        json.dumps(
            payload,
            indent=2,
        )
        + "\n"
    )

    print("WAR ROOM MARKET MATRIX")
    print("=" * 72)
    print("refresh:", refresh_id)
    print(
        "canonical projection games:",
        len(projection_games),
    )
    print(
        "fast market games matched:",
        len(fast_board_game_ids),
    )
    print(
        "unmatched fast rows:",
        len(unmatched),
    )
    print(
        "invalid fast rows:",
        len(invalid_rows),
    )
    print(
        "post-kickoff fast quotes rejected:",
        len(post_kickoff_fast_quotes),
    )
    print(
        "invalid book pairs:",
        len(pair_validation_failures),
    )
    print(
        "exchange quotes rejected "
        "for price worse than -120:",
        len(exchange_price_rejections),
    )
    print("states:", dict(state_counts))
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
