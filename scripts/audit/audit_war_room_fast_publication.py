#!/usr/bin/env python3
"""Fail-closed validation for the bounded fast War Room public bundle."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "war_room_health.json": "war-room-health-v1",
    "war_room_market_matrix.json": "war-room-market-matrix-v1",
    "war_room_activity.json": "war-room-activity-v1",
}


def timestamp(value: object) -> datetime:
    raw = str(value or "").strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=ROOT / "build/war_room_public")
    parser.add_argument("--max-age-minutes", type=float, default=15.0)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    errors: list[str] = []

    page = bundle / "war-room.html"
    if not page.is_file() or page.stat().st_size < 1000:
        errors.append("war-room.html is missing or too small")
    else:
        text = page.read_text(errors="ignore")
        for name in EXPECTED:
            if f"data/site/{name}" not in text:
                errors.append(f"war-room.html does not reference data/site/{name}")
        if "cache:'no-store'" not in text and 'cache: "no-store"' not in text:
            errors.append("war-room.html does not require no-store JSON fetches")

    payloads: dict[str, dict] = {}
    for name, schema in EXPECTED.items():
        path = bundle / "data/site" / name
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{name} is missing or malformed: {exc}")
            continue
        payloads[name] = payload
        if payload.get("schema_version") != schema:
            errors.append(f"{name} schema is {payload.get('schema_version')!r}, expected {schema!r}")

    health = payloads.get("war_room_health.json", {})
    matrix = payloads.get("war_room_market_matrix.json", {})
    activity = payloads.get("war_room_activity.json", {})
    projection_health = health.get("projection_health")
    if not isinstance(projection_health, dict):
        errors.append("health projection_health must be an object")
    else:
        if projection_health.get("scope") != "LATEST_FAST_BOARD_FBS_VS_FBS_ONLY":
            errors.append("health projection scope is not latest-board FBS-vs-FBS")
        by_week = projection_health.get("by_week")
        if not isinstance(by_week, dict) or not by_week:
            errors.append("health projection_health.by_week must be nonempty")
        else:
            for week, health_state in by_week.items():
                for model in ("spread", "total", "shadow"):
                    model_state = (
                        health_state.get(model)
                        if isinstance(health_state, dict)
                        else None
                    )
                    if not isinstance(model_state, dict):
                        errors.append(f"Week {week} missing {model} projection health")
                        continue
                    if model_state.get("status") not in {
                        "OFFICIAL",
                        "DEGRADED",
                        "WAITING",
                        "UNAVAILABLE",
                    }:
                        errors.append(f"Week {week} has invalid {model} projection status")
    health_refresh = health.get("fast_market_refresh") or {}
    matrix_refresh = matrix.get("fast_market_refresh") or {}
    refresh_ids = {health_refresh.get("refresh_id"), matrix_refresh.get("refresh_id")}
    if None in refresh_ids or len(refresh_ids) != 1:
        errors.append("health and matrix refresh_id values do not match")
    elif activity.get("latest_refresh_id") not in refresh_ids:
        errors.append("activity latest_refresh_id does not match the fast market refresh")
    if not isinstance(activity.get("events"), list):
        errors.append("activity events must be a list")
    else:
        for row in activity["events"]:
            if not isinstance(row, dict) or not isinstance(row.get("display_priority"), int):
                errors.append("activity event missing display_priority")
                break
            if not isinstance(row.get("underlying_event_ids"), list):
                errors.append("activity event missing underlying_event_ids")
                break

    pull_values = {
        health_refresh.get("last_fast_pull_at"),
        matrix_refresh.get("last_fast_pull_at"),
    }
    if None in pull_values or len(pull_values) != 1:
        errors.append("health and matrix last_fast_pull_at values do not match")
    else:
        try:
            pulled_at = timestamp(next(iter(pull_values)))
            age_minutes = (datetime.now(timezone.utc) - pulled_at).total_seconds() / 60
            if age_minutes < -1 or age_minutes > args.max_age_minutes:
                errors.append(
                    f"fast market pull age is {age_minutes:.1f} minutes; "
                    f"allowed range is -1 to {args.max_age_minutes:.1f}"
                )
            for name, payload in payloads.items():
                if timestamp(payload.get("built_at")) < pulled_at:
                    errors.append(f"{name} was built before the fast market pull")
        except ValueError as exc:
            errors.append(str(exc))

    games = matrix.get("games")
    summary = matrix.get("summary") or {}
    matched = summary.get("fast_market_games_matched")
    if not isinstance(games, list) or not games:
        errors.append("market matrix games must be a nonempty list")
    if not isinstance(matched, int) or matched <= 0:
        errors.append("market matrix has no matched fast-market games")
    health_games = health_refresh.get("upcoming_games_in_pull")
    if isinstance(matched, int) and isinstance(health_games, int) and matched != health_games:
        errors.append(
            f"matched matrix games ({matched}) differ from health pull games ({health_games})"
        )

    if errors:
        print("WAR ROOM FAST PUBLICATION VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(
        "WAR ROOM FAST PUBLICATION VALIDATION PASSED: "
        f"refresh_id={next(iter(refresh_ids))}; games={matched}; "
        f"bundle={bundle}"
    )


if __name__ == "__main__":
    main()
