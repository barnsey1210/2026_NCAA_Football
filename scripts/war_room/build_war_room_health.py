#!/usr/bin/env python3
"""Build War Room operational health from the latest fast market pull."""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.markets.build_current_market_contract import (
    game_key,
    normalize_team,
    resolve_game_id,
    site_date_from_timestamp,
)

THEODDS = ROOT / "data/war_room/odds/theodds_ncaaf_lines_2026_fast.csv"
CONTRACT = ROOT / "data/site/current_market_contract.json"
PROJECTIONS = ROOT / "data/site/current_game_projection_contract.json"
FBS_UNIVERSE = ROOT / "data/ratings/ratings_preseason_2026.csv"
OUT = ROOT / "data/site/war_room_health.json"

QUOTA = (
    ROOT
    / "data/war_room/audits/theodds_api_quota_status_fast.json"
)

LATENCY = (
    ROOT
    / "data/war_room/audits/fast_market_latency_study.json"
)

RATINGS_STATUS = (
    ROOT
    / "data/ratings/ratings_source_status.csv"
)

PROJECTION_SOURCE_STATUS = (
    ROOT
    / "data/site/projection_source_status_view.json"
)

POSTGAME_SHADOW = (
    ROOT
    / "data/site/postgame_shadow_updates.json"
)

SHADOW_COMPONENTS = (
    ROOT
    / "data/site/saturday_shadow_component_predictions.json"
)

SHADOW_LINES = (
    ROOT
    / "data/site/saturday_shadow_lines.json"
)

MONTHLY_LIMIT = int(
    os.environ.get("NCAAF_FAST_API_MONTHLY_LIMIT", "20000")
)

EMERGENCY_RESERVE = int(
    os.environ.get("NCAAF_FAST_API_EMERGENCY_RESERVE", "2000")
)

ET = ZoneInfo("America/New_York")

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

REFERENCE = (
    "Pinnacle",
)

WATCHED = (*BETTABLE, *EXCHANGES, *REFERENCE)

GREEN_MARKET_COMPLETENESS = 0.95

STANDARD_SPREAD = "standard_spread_five_source_v1"
STANDARD_TOTAL = "standard_total_sp_massey_sagarin_v1"
SHADOW_SPREAD = "shadow_spread_sp_sagarin_v1"
SHADOW_TOTAL = "shadow_total_enhanced_spplus_od_v1"


def parse_ts(value: str | None):
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        d = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)



def integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_api_quota_health():
    if not QUOTA.exists():
        return {
            "status": "UNAVAILABLE",
            "color": "RED",
            "reason": "Fast API quota audit is missing.",
        }

    q = json.loads(QUOTA.read_text())

    used = integer(q.get("x_requests_used"))
    remaining = integer(q.get("x_requests_remaining"))
    last_cost = integer(q.get("x_requests_last"))

    now_et = datetime.now(ET)

    if now_et.month == 12:
        reset_at = datetime(
            now_et.year + 1,
            1,
            1,
            tzinfo=ET,
        )
    else:
        reset_at = datetime(
            now_et.year,
            now_et.month + 1,
            1,
            tzinfo=ET,
        )

    days_until_reset = max(
        1,
        (reset_at.date() - now_et.date()).days,
    )

    available_operating = (
        max(0, remaining - EMERGENCY_RESERVE)
        if remaining is not None
        else None
    )

    estimated_pulls = (
        remaining // last_cost
        if remaining is not None and last_cost
        else None
    )

    estimated_operating_pulls = (
        available_operating // last_cost
        if available_operating is not None and last_cost
        else None
    )

    daily_operating_credits = (
        round(available_operating / days_until_reset, 1)
        if available_operating is not None
        else None
    )

    daily_operating_pulls = (
        round(
            estimated_operating_pulls / days_until_reset,
            1,
        )
        if estimated_operating_pulls is not None
        else None
    )

    # Reserve-driven health. The color is not based on a percentage of
    # the original monthly allotment; it reflects operational headroom.
    if remaining is None:
        color = "RED"
        status = "UNAVAILABLE"

    elif remaining <= EMERGENCY_RESERVE:
        color = "RED"
        status = "RESERVE_ONLY"

    elif remaining <= EMERGENCY_RESERVE * 2:
        color = "YELLOW"
        status = "LOW_OPERATING_HEADROOM"

    else:
        color = "GREEN"
        status = "HEALTHY"

    return {
        "status": status,
        "color": color,
        "monthly_limit_configured": MONTHLY_LIMIT,
        "credits_used": used,
        "credits_remaining": remaining,
        "last_call_cost": last_cost,
        "emergency_reserve": EMERGENCY_RESERVE,
        "available_operating_credits": available_operating,
        "estimated_fast_pulls_remaining": estimated_pulls,
        "estimated_operating_pulls_before_reserve": (
            estimated_operating_pulls
        ),
        "calendar_month": now_et.strftime("%Y-%m"),
        "reset_at_et": reset_at.isoformat(),
        "days_until_reset": days_until_reset,
        "daily_operating_credit_budget": daily_operating_credits,
        "daily_operating_pull_budget": daily_operating_pulls,
        "scheduled_refresh_allowed": (
            remaining is not None
            and remaining > EMERGENCY_RESERVE
        ),
        "policy": (
            "Command Center quota is budgeted by calendar month. "
            "Scheduled fast refreshes protect the configured emergency "
            "reserve. Provider response headers are the runtime source "
            "of truth for actual usage."
        ),
    }


def latest_book_latency():
    if not LATENCY.exists():
        return {}

    try:
        payload = json.loads(LATENCY.read_text())
    except Exception:
        return {}

    return payload.get("provider_quote_age", {}).get("books", {})



def csv_records(path):
    if not path.exists():
        return []

    with path.open(
        newline="",
        encoding="utf-8-sig",
    ) as f:
        return list(csv.DictReader(f))


def load_json(path):
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def load_fbs_team_universe():
    if not FBS_UNIVERSE.exists():
        raise SystemExit(
            f"Missing canonical 2026 FBS universe: {FBS_UNIVERSE}"
        )

    teams = {
        normalize_team(row.get("team"))
        for row in csv_records(FBS_UNIVERSE)
        if str(row.get("team") or "").strip()
    }

    if len(teams) < 130:
        raise SystemExit(
            f"Unexpected FBS universe size: {len(teams)}"
        )

    return teams


def model_health(games, model_id):
    counts = Counter(
        str(
            game.get("projections", {})
            .get(model_id, {})
            .get("availability_status")
            or "UNAVAILABLE"
        )
        for game in games
    )
    total = len(games)
    official = counts.get("AVAILABLE", 0)
    degraded = counts.get("AVAILABLE_DEGRADED", 0)
    unavailable = total - official - degraded

    if total == 0 or unavailable > 0:
        status = "UNAVAILABLE"
        color = "RED"
    elif degraded > 0:
        status = "DEGRADED"
        color = "YELLOW"
    else:
        status = "OFFICIAL"
        color = "GREEN"

    return {
        "status": status,
        "color": color,
        "displayed_games": total,
        "official_games": official,
        "degraded_games": degraded,
        "unavailable_games": unavailable,
        "availability_counts": dict(sorted(counts.items())),
    }


def shadow_model_health(games):
    counts = Counter()

    for game in games:
        projections = game.get("projections", {})
        spread_status = str(
            projections.get(SHADOW_SPREAD, {})
            .get("availability_status")
            or "UNAVAILABLE"
        )
        total_status = str(
            projections.get(SHADOW_TOTAL, {})
            .get("availability_status")
            or "UNAVAILABLE"
        )
        statuses = {spread_status, total_status}

        if statuses == {"AVAILABLE"}:
            counts["READY"] += 1
        elif statuses <= {"AVAILABLE", "AVAILABLE_DEGRADED"}:
            counts["DEGRADED"] += 1
        elif statuses == {"NOT_YET_ACTIVATED"}:
            counts["WAITING"] += 1
        else:
            counts["UNAVAILABLE"] += 1

    total = len(games)

    if total == 0 or counts.get("UNAVAILABLE", 0) > 0:
        status = "UNAVAILABLE"
        color = "RED"
    elif counts.get("WAITING", 0) == total:
        status = "WAITING"
        color = "GRAY"
    elif counts.get("READY", 0) == total:
        status = "OFFICIAL"
        color = "GREEN"
    else:
        status = "DEGRADED"
        color = "YELLOW"

    return {
        "status": status,
        "color": color,
        "displayed_games": total,
        "ready_games": counts.get("READY", 0),
        "degraded_games": counts.get("DEGRADED", 0),
        "waiting_games": counts.get("WAITING", 0),
        "unavailable_games": counts.get("UNAVAILABLE", 0),
        "availability_counts": dict(sorted(counts.items())),
    }


def build_projection_health(latest_rows):
    if not PROJECTIONS.exists():
        raise SystemExit(
            f"Missing canonical projection contract: {PROJECTIONS}"
        )

    payload = load_json(PROJECTIONS)
    projection_games = payload.get("games", [])
    fbs_teams = load_fbs_team_universe()
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

    displayed_game_ids = set()
    unmatched_provider_game_ids = set()

    for row in latest_rows:
        gid, _, _ = resolve_game_id(
            [
                site_date_from_timestamp(row.get("commence_time")),
                str(row.get("commence_time") or "")[:10],
            ],
            row.get("away_team"),
            row.get("home_team"),
            identity,
            key_to_game_id,
        )

        if gid:
            displayed_game_ids.add(gid)
        else:
            provider_gid = str(row.get("game_id") or "").strip()
            if provider_gid:
                unmatched_provider_game_ids.add(provider_gid)

    weekly_games = defaultdict(list)

    for gid in displayed_game_ids:
        game = projection_by_gid.get(gid)
        if not game:
            continue

        if (
            normalize_team(game.get("away_team")) not in fbs_teams
            or normalize_team(game.get("home_team")) not in fbs_teams
        ):
            continue

        weekly_games[str(game.get("week"))].append(game)

    by_week = {}

    for week, games in sorted(
        weekly_games.items(),
        key=lambda item: int(item[0]),
    ):
        by_week[week] = {
            "week": integer(week),
            "displayed_fbs_vs_fbs_games": len(games),
            "spread": model_health(games, STANDARD_SPREAD),
            "total": model_health(games, STANDARD_TOTAL),
            "shadow": shadow_model_health(games),
        }

    return {
        "scope": "LATEST_FAST_BOARD_FBS_VS_FBS_ONLY",
        "selection_policy": (
            "Frontend selects the matching week entry. ALL WEEKS does not "
            "aggregate season-wide projection health."
        ),
        "projection_contract_built_at": payload.get("built_at"),
        "matched_fast_board_games": len(displayed_game_ids),
        "unmatched_fast_board_games": len(unmatched_provider_game_ids),
        "fbs_vs_fbs_games": sum(
            len(games) for games in weekly_games.values()
        ),
        "by_week": by_week,
    }


def build_ratings_health():
    rows = csv_records(RATINGS_STATUS)

    by_source = {
        str(r.get("source") or ""): r
        for r in rows
    }

    projection_status = load_json(
        PROJECTION_SOURCE_STATUS
    )

    spread_sources = {
        str(r.get("key") or ""): r
        for r in projection_status
        .get("standard_spread", {})
        .get("sources", [])
    }

    total_sources = {
        str(r.get("key") or ""): r
        for r in projection_status
        .get("standard_total", {})
        .get("sources", [])
    }

    feeds = {
        str(r.get("source_key") or ""): r
        for r in projection_status.get(
            "game_prediction_feeds",
            [],
        )
    }

    out = {}

    # --------------------------------------------------------
    # Team-rating feeds.
    # --------------------------------------------------------

    for source, short in (
        ("SP+", "SP+"),
        ("FPI", "FPI"),
        ("TeamRankings", "TR"),
    ):
        r = by_source.get(source, {})

        teams = integer(r.get("teams"))
        active = str(
            r.get("active_2026") or ""
        ).lower() == "true"

        if active and teams and teams >= 135:
            color = "GREEN"
            status = "CURRENT"
        elif teams:
            color = "YELLOW"
            status = "PARTIAL"
        else:
            color = "RED"
            status = "UNAVAILABLE"

        out[short] = {
            "source": source,
            "color": color,
            "status": status,
            "teams": teams,
            "snapshot_date": r.get("snapshot_date"),
            "pulled_at": r.get("pulled_at"),
            "latest_pull_at": r.get("latest_pull_at"),
            "last_changed_at": r.get("last_changed_at"),
            "change_status": r.get("change_status"),
            "teams_changed": integer(
                r.get("teams_changed")
            ),
            "production_weight_pct": number(
                r.get("production_weight_pct")
            ),
        }

    # --------------------------------------------------------
    # Sagarin: currently absent from active team-rating status
    # and explicitly missing from both production models.
    # This is WAITING, not a hard feed failure.
    # --------------------------------------------------------

    sag_spread = spread_sources.get(
        "Sagarin Rating",
        {},
    )
    sag_total = total_sources.get(
        "Sagarin",
        {},
    )

    sag_games = max(
        integer(sag_spread.get("games_available")) or 0,
        integer(sag_total.get("games_available")) or 0,
    )

    out["SAG"] = {
        "source": "Sagarin",
        "color": (
            "GREEN"
            if sag_games > 0
            else "YELLOW"
        ),
        "status": (
            "CURRENT"
            if sag_games > 0
            else "WAITING"
        ),
        "games_available": sag_games,
        "spread_state": sag_spread.get("state"),
        "total_state": sag_total.get("state"),
        "coverage_pct": max(
            number(sag_spread.get("coverage_pct")) or 0,
            number(sag_total.get("coverage_pct")) or 0,
        ),
    }

    # --------------------------------------------------------
    # DRatings game predictions.
    # --------------------------------------------------------

    dr = feeds.get("DRatings Predictions", {})

    dr_games = integer(
        dr.get("games_available")
    ) or 0

    out["DR"] = {
        "source": "DRatings Game Predictions",
        "color": (
            "GREEN"
            if dr.get("state") == "FULL"
            else "YELLOW"
            if dr_games > 0
            else "RED"
        ),
        "status": (
            "CURRENT"
            if dr.get("state") == "FULL"
            else "PARTIAL"
            if dr_games > 0
            else "UNAVAILABLE"
        ),
        "games_available": dr_games,
        "production_games": integer(
            dr.get("production_games")
        ),
        "coverage_pct": number(
            dr.get("coverage_pct")
        ),
        "latest_pulled_at": dr.get(
            "latest_pulled_at"
        ),
        "latest_snapshot_date": dr.get(
            "latest_snapshot_date"
        ),
    }

    # --------------------------------------------------------
    # Massey game predictions / dual source.
    # --------------------------------------------------------

    mas = feeds.get("Massey Games", {})

    mas_games = integer(
        mas.get("games_available")
    ) or 0

    out["MAS"] = {
        "source": "Massey Game Predictions",
        "color": (
            "GREEN"
            if mas.get("state") == "FULL"
            else "YELLOW"
            if mas_games > 0
            else "RED"
        ),
        "status": (
            "CURRENT"
            if mas.get("state") == "FULL"
            else "PARTIAL"
            if mas_games > 0
            else "UNAVAILABLE"
        ),
        "games_available": mas_games,
        "production_games": integer(
            mas.get("production_games")
        ),
        "coverage_pct": number(
            mas.get("coverage_pct")
        ),
        "latest_pulled_at": mas.get(
            "latest_pulled_at"
        ),
        "latest_snapshot_date": mas.get(
            "latest_snapshot_date"
        ),
    }

    return {
        "status": "AVAILABLE",
        "generated_at": projection_status.get(
            "generated_at"
        ),
        "sources": out,
    }


def build_shadow_health():
    postgame = load_json(POSTGAME_SHADOW)
    components = load_json(SHADOW_COMPONENTS)
    lines = load_json(SHADOW_LINES)

    component_summary = components.get(
        "summary",
        {},
    )

    postgame_summary = postgame.get(
        "summary",
        {},
    )

    completed_updates = integer(
        postgame_summary.get(
            "completed_team_updates"
        )
    ) or integer(
        component_summary.get(
            "postgame_updated_teams"
        )
    ) or 0

    displayed_rows = integer(
        component_summary.get(
            "displayed_shadow_rows"
        )
    ) or 0

    component_games = components.get(
        "games",
        [],
    )

    display_ready = sum(
        1
        for g in component_games
        if g.get("shadow_display_ready") is True
    )

    postgame_status = str(
        postgame.get("status") or ""
    )

    # Expected preseason / pre-completion state.
    waiting_states = {
        "awaiting_live_results",
        "awaiting_completed_games",
        "awaiting_results",
    }

    if (
        completed_updates > 0
        and display_ready > 0
    ):
        color = "GREEN"
        status = "READY"

    elif (
        postgame_status in waiting_states
        or completed_updates == 0
    ):
        color = "YELLOW"
        status = "WAITING_FOR_COMPLETED_GAMES"

    else:
        color = "RED"
        status = "NOT_READY"

    spread_model = postgame.get(
        "spread_model",
        {},
    )

    total_model = postgame.get(
        "total_model",
        {},
    )

    return {
        "color": color,
        "status": status,
        "postgame_status": postgame_status,
        "completed_team_updates": completed_updates,
        "display_ready_games": display_ready,
        "displayed_shadow_rows": displayed_rows,
        "component_games": len(component_games),
        "spread_model_status": spread_model.get(
            "status"
        ),
        "total_model_status": total_model.get(
            "status"
        ),
        "postgame_built_at": postgame.get(
            "built_at"
        ),
        "components_generated_at": components.get(
            "generated_at"
        ),
        "shadow_lines_built_at": lines.get(
            "built_at"
        ),
        "activation_policy": (
            "GREEN only after genuine completed-game updates "
            "exist and at least one Shadow projection is "
            "display-ready. Expected pregame waiting states "
            "are YELLOW, not RED."
        ),
    }


def main():
    if not THEODDS.exists():
        raise SystemExit(f"Missing fast-market source: {THEODDS}")

    with THEODDS.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    parsed = [
        (parse_ts(r.get("pulled_at")), r)
        for r in rows
    ]
    parsed = [(ts, r) for ts, r in parsed if ts is not None]

    if not parsed:
        raise SystemExit("No valid pulled_at values in The Odds API artifact")

    latest_at = max(ts for ts, _ in parsed)

    # pulled_at is assigned to the API collection generation.
    latest_rows = [
        r for ts, r in parsed
        if ts == latest_at
    ]

    refresh_id = f"theodds_{latest_at.strftime('%Y%m%dT%H%M%SZ')}"

    latest_game_ids = {
        str(r.get("game_id") or "").strip()
        for r in latest_rows
        if str(r.get("game_id") or "").strip()
    }

    universe_games = len(latest_game_ids)

    book_games = defaultdict(set)
    book_market_games = defaultdict(lambda: defaultdict(set))
    book_quotes = Counter()

    for r in latest_rows:
        book = str(r.get("book") or "").strip()
        gid = str(r.get("game_id") or "").strip()
        market = str(r.get("market") or "").strip()

        if not book or not gid:
            continue

        market = {
            "spreads": "spread",
            "totals": "total",
            "h2h": "moneyline",
        }.get(market, market)

        book_games[book].add(gid)
        if market:
            book_market_games[book][market].add(gid)
        book_quotes[book] += 1

    # Normal canonical availability is useful context, but does NOT control
    # War Room fast-pull participation.
    canonical = json.loads(CONTRACT.read_text()) if CONTRACT.exists() else {}

    canonical_games_by_book = Counter()
    canonical_sources = defaultdict(Counter)

    for game in canonical.get("games", []):
        for book, markets in game.get("quotes", {}).items():
            if not markets:
                continue

            canonical_games_by_book[book] += 1

            for sides in markets.values():
                for q in sides.values():
                    canonical_sources[book][
                        q.get("source") or "UNKNOWN"
                    ] += 1

    api_quota = build_api_quota_health()
    latency_books = latest_book_latency()

    ratings_health = build_ratings_health()
    shadow_health = build_shadow_health()
    projection_health = build_projection_health(latest_rows)

    books = {}

    for book in WATCHED:
        games = len(book_games.get(book, set()))
        coverage = (
            games / universe_games
            if universe_games
            else 0.0
        )

        spread_games = len(
            book_market_games.get(book, {}).get("spread", set())
        )
        total_games = len(
            book_market_games.get(book, {}).get("total", set())
        )

        spread_completeness = (
            spread_games / games
            if games
            else 0.0
        )
        total_completeness = (
            total_games / games
            if games
            else 0.0
        )

        if games == 0:
            color = "RED"
            status = "MISSING_FROM_LAST_FAST_PULL"

        elif (
            spread_completeness >= GREEN_MARKET_COMPLETENESS
            and total_completeness >= GREEN_MARKET_COMPLETENESS
        ):
            color = "GREEN"
            status = "CURRENT_HEALTHY"

        else:
            color = "YELLOW"
            status = "CURRENT_INCOMPLETE_MARKETS"

        if book in BETTABLE:
            group = "BETTABLE_SPORTSBOOK"
        elif book in EXCHANGES:
            group = "EXCHANGE"
        else:
            group = "SHARP_REFERENCE"

        books[book] = {
            "group": group,
            "color": color,
            "status": status,
            "participated_in_last_fast_pull": games > 0,
            "eligible_for_fast_market_selection": games > 0,
            "games_with_any_quote": games,

            # Board breadth is informational and does not determine
            # sportsbook / exchange health.
            "board_breadth_pct": round(coverage * 100, 1),

            "spread_games": spread_games,
            "total_games": total_games,

            "spread_completeness_pct": round(
                spread_completeness * 100, 1
            ),
            "total_completeness_pct": round(
                total_completeness * 100, 1
            ),

            "quote_rows": int(book_quotes.get(book, 0)),
            "canonical_current_games": int(
                canonical_games_by_book.get(book, 0)
            ),
            "canonical_source_counts": dict(
                canonical_sources.get(book, {})
            ),

            # Informational only. Quote age does not determine G/Y/R
            # because an unchanged sportsbook line can legitimately
            # retain an older provider update timestamp.
            "quote_age_median_seconds": (
                latency_books.get(book, {})
                .get("all", {})
                .get("median_seconds")
            ),
            "quote_age_p90_seconds": (
                latency_books.get(book, {})
                .get("all", {})
                .get("p90_seconds")
            ),
        }

    payload = {
        "schema_version": "war-room-health-v1",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "fast_market_refresh": {
            "refresh_id": refresh_id,
            "last_fast_pull_at": latest_at.isoformat(),
            "source": "The Odds API",
            "upcoming_games_in_pull": universe_games,
            "participation_policy": (
                "Book participation remains tied to the most recent fast "
                "market pull until another fast pull occurs. No elapsed-time "
                "cutoff changes participation."
            ),
            "display_policy": {
                "GREEN": (
                    "Participated in latest fast pull and returned "
                    "structurally healthy spread/total coverage across "
                    "the games the venue currently offers."
                ),
                "YELLOW": (
                    "Participated in latest fast pull but spread/total "
                    "coverage is materially incomplete within its "
                    "returned game set."
                ),
                "RED": (
                    "Did not return usable spread/total data in latest "
                    "fast pull."
                ),
            },
        },
        "api_quota": api_quota,
        "ratings_health": ratings_health,
        "shadow_health": shadow_health,
        "projection_health": projection_health,
        "market_groups": {
            "bettable_sportsbooks": list(BETTABLE),
            "exchanges": list(EXCHANGES),
            "sharp_reference": list(REFERENCE),
        },
        "books": books,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print("WAR ROOM MARKET HEALTH")
    print("refresh_id:", refresh_id)
    print("last_fast_pull_at:", latest_at.isoformat())
    print("games in latest pull:", universe_games)

    for book in WATCHED:
        h = books[book]
        print(
            f'{book:12} '
            f'{h["color"]:6} '
            f'{h["games_with_any_quote"]:3}/{universe_games:<3} '
            f'B:{h["board_breadth_pct"]:5.1f}% '
            f'S:{h["spread_games"]:3} '
            f'({h["spread_completeness_pct"]:5.1f}%) '
            f'T:{h["total_games"]:3} '
            f'({h["total_completeness_pct"]:5.1f}%)'
        )

    print("wrote:", OUT)


if __name__ == "__main__":
    main()
