#!/usr/bin/env python3
"""Canonical schedule-derived horizon for Command Center market pulls."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_SCHEDULE = Path("data/canonical/cfbd_schedule_2026.json")


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def remaining_season_horizon(
    schedule_path: Path = DEFAULT_SCHEDULE,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime, datetime]:
    """Return request start, request end, and latest canonical kickoff.

    The one-day tail includes the complete UTC day around the final scheduled
    kickoff and avoids excluding a final game because its time is later revised.
    """
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    payload = json.loads(schedule_path.read_text(encoding="utf-8"))
    games = payload.get("games") if isinstance(payload, dict) else payload
    if not isinstance(games, list):
        raise ValueError(f"Canonical schedule has no games list: {schedule_path}")

    future_kickoffs = []
    for game in games:
        value = game.get("start_date") or game.get("commence_time")
        if not value:
            continue
        kickoff = parse_utc(value)
        if kickoff >= current:
            future_kickoffs.append(kickoff)

    if not future_kickoffs:
        raise ValueError(
            "Canonical schedule has no remaining 2026 kickoffs; refusing to "
            "substitute a short fast-market window."
        )

    latest = max(future_kickoffs)
    return current, latest + timedelta(days=1), latest


def provider_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
