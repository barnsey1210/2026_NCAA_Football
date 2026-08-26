"""Canonical CFBD kickoff-time quality semantics."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
STATUSES = {"VERIFIED_KICKOFF", "TBD", "DATE_PLACEHOLDER", "MISSING", "UNRESOLVED"}


def parse_kickoff(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return None
        return dt.astimezone(ET)
    except (TypeError, ValueError):
        return None


def classify_kickoff(start_date: Any, start_time_tbd: Any) -> str:
    """Classify provider kickoff evidence without treating a date as a time."""
    if start_date in (None, ""):
        return "MISSING"
    kickoff = parse_kickoff(start_date)
    if kickoff is None:
        return "UNRESOLVED"
    is_local_midnight = kickoff.hour == 0 and kickoff.minute == 0 and kickoff.second == 0
    if start_time_tbd is True:
        return "DATE_PLACEHOLDER" if is_local_midnight else "TBD"
    if start_time_tbd is False:
        return "UNRESOLVED" if is_local_midnight else "VERIFIED_KICKOFF"
    return "DATE_PLACEHOLDER" if is_local_midnight else "UNRESOLVED"


def game_kickoff_status(game: dict[str, Any]) -> str:
    declared = game.get("kickoff_status") or game.get("cfbd_kickoff_status")
    if declared in STATUSES:
        return declared
    return classify_kickoff(
        game.get("start_date") or game.get("cfbd_start_date"),
        game.get("start_time_tbd") if "start_time_tbd" in game else game.get("cfbd_start_time_tbd"),
    )
