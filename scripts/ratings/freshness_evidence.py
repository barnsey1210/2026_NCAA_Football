#!/usr/bin/env python3
"""Durable accepted-version evidence and completed-week freshness cutoffs."""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TEAM_BACKUP_SPECS = {
    "SP+": ("spplus_2026_from_espn_latest_*.csv", ("spplus", "spplus_off", "spplus_def")),
    "FPI": ("fpi_2026_latest_*.csv", ("fpi",)),
    "TeamRankings": ("teamrankings_2026_latest_*.csv", ("teamrankings",)),
}


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def accepted_after_cutoff(metadata: dict[str, Any], cutoff_at: str | None) -> bool:
    accepted = parse_utc(metadata.get("latest_accepted_update_at"))
    cutoff = parse_utc(cutoff_at)
    return bool(accepted and cutoff and accepted > cutoff)


def completed_week_cutoffs(results: dict[str, Any], watcher: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Map target week N to the last accepted final from completed Week N-1.

    Only canonical completed results participate. Canceled, postponed, abandoned,
    or otherwise unplayed schedule rows therefore cannot block rollover.
    """
    accepted = watcher.get("accepted") or {}
    by_week: dict[int, list[tuple[datetime, dict[str, Any]]]] = {}
    completed_counts: dict[int, int] = {}
    for game in results.get("games") or []:
        if not game.get("completed") and str(game.get("status") or "").lower() not in {"completed", "final"}:
            continue
        try:
            week = int(game.get("week"))
        except (TypeError, ValueError):
            continue
        completed_counts[week] = completed_counts.get(week, 0) + 1
        evidence = accepted.get(str(game.get("game_id") or "")) or {}
        observed = parse_utc(evidence.get("accepted_at"))
        if observed:
            by_week.setdefault(week, []).append((observed, game))

    out: dict[int, dict[str, Any]] = {}
    for completed_week, rows in by_week.items():
        # A partial final-event set cannot prove which game was last. Fail
        # closed until every canonical completed game has acceptance evidence.
        if len(rows) != completed_counts.get(completed_week):
            continue
        observed, game = max(rows, key=lambda item: item[0])
        out[completed_week + 1] = {
            "completed_week": completed_week,
            "game_id": game.get("game_id"),
            "away_team": game.get("away_team"),
            "home_team": game.get("home_team"),
            "final_completion_at": iso_utc(observed),
        }
    return out


def _stable_csv(path: Path, columns: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    with path.open(newline="", encoding="utf-8-sig", errors="ignore") as handle:
        rows = []
        for row in csv.DictReader(handle):
            team = str(row.get("team") or "").strip()
            rows.append((team, *(str(row.get(column) or "").strip() for column in columns)))
    return tuple(sorted(rows))


def _backup_timestamp(path: Path) -> str | None:
    match = re.search(r"_(\d{8}T\d{6}Z)\.csv$", path.name)
    if not match:
        return None
    try:
        return iso_utc(datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc))
    except ValueError:
        return None


def recover_team_accepted_update(root: Path, source: str) -> str | None:
    """Recover accepted changes from immutable pre-promotion backups.

    A backup is written only after all candidate validation passes and directly
    before promotion. A content difference between that backup and the next
    accepted state proves a successfully promoted changed version at the first
    backup's timestamp.
    """
    spec = TEAM_BACKUP_SPECS.get(source)
    if not spec:
        return None
    pattern, columns = spec
    backup_dir = root / "data/ratings/accepted_backups"
    backups = sorted(backup_dir.glob(pattern))
    current_names = {
        "SP+": "spplus_2026_from_espn_latest.csv",
        "FPI": "fpi_2026_latest.csv",
        "TeamRankings": "teamrankings_2026_latest.csv",
    }
    current = root / "data/ratings" / current_names[source]
    states = backups + ([current] if current.exists() else [])
    latest = None
    for before, after in zip(states, states[1:]):
        try:
            changed = _stable_csv(before, columns) != _stable_csv(after, columns)
        except OSError:
            continue
        if changed:
            latest = _backup_timestamp(before) or latest
    return latest


def recover_team_accepted_updates_from_logs(root: Path) -> dict[str, str]:
    """Recover exact accepted timestamps from successful acceptance stages."""
    latest: dict[str, str] = {}
    pattern = re.compile(
        r"^(SP\+|FPI|TeamRankings): UPDATED \| teams_changed=(\d+) "
        r"\| last_changed_at=([^\n]+)",
        re.M,
    )
    for path in sorted((root / "data/control/logs").glob("*.json")):
        try:
            run = json.loads(path.read_text())
        except (OSError, ValueError, TypeError):
            continue
        if run.get("stage") != "complete" or run.get("errors"):
            continue
        for stage in run.get("stages") or []:
            if stage.get("name") != "accept_live_rating_candidates_with_status.py" or stage.get("status") != "PASSED":
                continue
            for source, changed, accepted_at in pattern.findall(str(stage.get("output_tail") or "")):
                if int(changed) > 0 and parse_utc(accepted_at):
                    latest[source] = accepted_at.strip()
    return latest


def resolve_team_accepted_update(root: Path, source: str, metadata: dict[str, Any]) -> str | None:
    explicit = metadata.get("latest_accepted_update_at")
    if parse_utc(explicit):
        return str(explicit)
    logged = recover_team_accepted_updates_from_logs(root).get(source)
    return logged or recover_team_accepted_update(root, source)


def recover_projection_accepted_updates(root: Path) -> dict[str, str]:
    """Recover accepted feed changes from successful runtime task evidence."""
    component_to_source = {
        "dratings": "DRatings Predictions",
        "massey": "Massey Games",
        "sagarin": "Sagarin Game Total",
    }
    latest: dict[str, str] = {}
    for path in sorted((root / "data/control/logs").glob("*.json")):
        try:
            run = json.loads(path.read_text())
        except (OSError, ValueError, TypeError):
            continue
        if run.get("stage") != "complete" or run.get("errors"):
            continue
        completed_at = run.get("completion_timestamp")
        if not parse_utc(completed_at):
            continue
        for stage in run.get("stages") or []:
            if stage.get("name") != "run_fast_standard_source_refresh.py" or stage.get("status") != "PASSED":
                continue
            text = str(stage.get("output_tail") or "")
            match = re.search(r'"changed_components"\s*:\s*\[(.*?)\]', text, re.S)
            if not match:
                continue
            for component in re.findall(r'"([^"]+)"', match.group(1)):
                source = component_to_source.get(component)
                if source:
                    latest[source] = str(completed_at)
    return latest
