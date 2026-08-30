#!/usr/bin/env python3
"""Acquire current-week CFBD postgame inputs for the 2026 Shadow pipeline.

The lightweight /games acquisition is owned by pull_cfbd_schedule_2026.py.
This script is the richer postgame layer and should normally run only when
completed-game state has changed.

Inputs:
  data/canonical/game_results_2026.json

Outputs:
  data/canonical/postgame/2026/week_XX/plays.json.gz
  data/canonical/postgame/2026/week_XX/drives.json.gz
  data/canonical/postgame/2026/week_XX/havoc.json.gz
  data/audits/cfbd_postgame_2026_audit.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://api.collegefootballdata.com"

RESULTS = ROOT / "data/canonical/game_results_2026.json"
OUT_ROOT = ROOT / "data/canonical/postgame/2026"
AUDIT = ROOT / "data/audits/cfbd_postgame_2026_audit.json"

YEAR = 2026


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_key() -> str:
    key = os.environ.get("CFBD_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing CFBD_API_KEY")
    return key


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        dir=path.parent,
        delete=False,
        encoding="utf-8",
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    tmp.replace(path)


def write_gzip(
    path: Path,
    endpoint: str,
    params: dict[str, Any],
    rows: Any,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "cfbd-postgame-raw-v1",
        "fetched_at": now_iso(),
        "endpoint": endpoint,
        "params": params,
        "data": rows,
    }

    with tempfile.NamedTemporaryFile(
        "wb",
        dir=path.parent,
        delete=False,
    ) as raw:
        tmp = Path(raw.name)

    try:
        with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as handle:
            json.dump(payload, handle)
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def read_gzip(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


class CFBDClient:
    def __init__(self, key: str, max_calls: int):
        self.calls = 0
        self.max_calls = max_calls
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "ncaaf-postgame-2026/1.0",
        })

    def get(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> list[dict]:
        if self.calls >= self.max_calls:
            raise RuntimeError(
                f"CFBD call cap reached ({self.max_calls})"
            )

        response = self.session.get(
            BASE_URL + endpoint,
            params=params,
            timeout=180,
        )
        self.calls += 1

        if response.status_code in (400, 401, 403, 429):
            raise RuntimeError(
                f"CFBD {endpoint} HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        response.raise_for_status()
        rows = response.json()

        if not isinstance(rows, list):
            raise RuntimeError(
                f"Unexpected CFBD {endpoint} response type: {type(rows)}"
            )

        time.sleep(0.15)
        return rows


def completed_games() -> list[dict]:
    if not RESULTS.exists():
        raise SystemExit(
            f"Missing {RESULTS}. Run build_game_results_2026.py first."
        )

    payload = json.loads(RESULTS.read_text())
    return [
        row for row in payload.get("games", [])
        if row.get("completed")
    ]


def resolve_week(rows: list[dict], requested: int | None) -> int | None:
    if requested is not None:
        return requested

    weeks = []
    for row in rows:
        try:
            weeks.append(int(row.get("week")))
        except (TypeError, ValueError):
            continue

    return max(weeks) if weeks else None


def row_game_ids(rows: list[dict]) -> set[str]:
    """Return canonical CFBD game IDs represented by an endpoint payload."""
    game_ids = set()
    for row in rows:
        value = row.get("gameId")
        if value is None:
            value = row.get("game_id")
        if value is not None:
            game_ids.add(str(value))
    return game_ids


def cache_covers_completed_games(
    rows: list[dict],
    completed_game_ids: set[str],
) -> bool:
    """A weekly cache is reusable only after it covers every known final."""
    return completed_game_ids.issubset(row_game_ids(rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--week",
        type=int,
        help="Explicit 2026 week. Defaults to latest completed week.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refresh existing cached files.",
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        default=3,
        help="Hard CFBD API-call cap for this run.",
    )
    parser.add_argument(
        "--status-only",
        action="store_true",
        help="Report required week/cache state without making API calls.",
    )
    args = parser.parse_args()

    completed = completed_games()
    week = resolve_week(completed, args.week)

    if week is None:
        audit = {
            "schema_version": "cfbd-postgame-2026-audit-v1",
            "generated_at": now_iso(),
            "season": YEAR,
            "status": "NO_COMPLETED_GAMES",
            "week": None,
            "completed_games": len(completed),
            "api_calls_this_run": 0,
            "files": {},
        }
        atomic_text(AUDIT, json.dumps(audit, indent=2) + "\n")
        print(json.dumps(audit, indent=2))
        return

    completed_week_games = [
        row for row in completed
        if str(row.get("week")) == str(week)
    ]
    game_ids = {
        str(row.get("cfbd_game_id"))
        for row in completed_week_games
        if row.get("cfbd_game_id") is not None
    }

    week_dir = OUT_ROOT / f"week_{week:02d}"
    specs = [
        (
            "plays",
            "/plays",
            {
                "year": YEAR,
                "week": week,
                "seasonType": "regular",
            },
            week_dir / "plays.json.gz",
        ),
        (
            "drives",
            "/drives",
            {
                "year": YEAR,
                "week": week,
                "seasonType": "regular",
            },
            week_dir / "drives.json.gz",
        ),
        (
            "havoc",
            "/stats/game/havoc",
            {
                "year": YEAR,
                "week": week,
                "seasonType": "regular",
            },
            week_dir / "havoc.json.gz",
        ),
    ]

    if args.status_only:
        audit = {
            "schema_version": "cfbd-postgame-2026-audit-v1",
            "generated_at": now_iso(),
            "season": YEAR,
            "status": "STATUS_ONLY",
            "week": week,
            "completed_games": len(completed),
            "completed_games_in_week": len(completed_week_games),
            "api_calls_this_run": 0,
            "files": {
                name: {
                    "path": str(path.relative_to(ROOT)),
                    "exists": path.exists(),
                }
                for name, _, _, path in specs
            },
        }
        atomic_text(AUDIT, json.dumps(audit, indent=2) + "\n")
        print(json.dumps(audit, indent=2))
        return

    client = CFBDClient(
        require_key(),
        max_calls=args.max_calls,
    )

    file_audit = {}
    for name, endpoint, params, path in specs:
        refreshed = False
        cache_missing_game_ids = []

        if path.exists() and not args.force:
            payload = read_gzip(path)
            rows = payload.get("data", [])
            cache_missing_game_ids = sorted(
                game_ids - row_game_ids(rows)
            )
            if cache_covers_completed_games(rows, game_ids):
                fetched_at = payload.get("fetched_at")
                source = "cache"
            else:
                rows = client.get(endpoint, params)
                write_gzip(path, endpoint, params, rows)
                payload = read_gzip(path)
                fetched_at = payload.get("fetched_at")
                source = "api_incomplete_cache_refresh"
                refreshed = True
        else:
            rows = client.get(endpoint, params)
            write_gzip(path, endpoint, params, rows)
            payload = read_gzip(path)
            fetched_at = payload.get("fetched_at")
            source = "api"
            refreshed = True

        file_audit[name] = {
            "path": str(path.relative_to(ROOT)),
            "rows": len(rows),
            "source": source,
            "refreshed": refreshed,
            "fetched_at": fetched_at,
            "completed_game_ids_missing_from_prior_cache": (
                cache_missing_game_ids
            ),
            "completed_game_ids_missing_after_read": sorted(
                game_ids - row_game_ids(rows)
            ),
        }

    plays_payload = read_gzip(week_dir / "plays.json.gz")
    play_game_ids = row_game_ids(plays_payload.get("data", []))

    completed_with_pbp = sorted(game_ids & play_game_ids)
    completed_missing_pbp = sorted(game_ids - play_game_ids)

    status = (
        "READY"
        if not completed_missing_pbp
        else "PARTIAL_PBP"
    )

    audit = {
        "schema_version": "cfbd-postgame-2026-audit-v1",
        "generated_at": now_iso(),
        "season": YEAR,
        "status": status,
        "week": week,
        "completed_games": len(completed),
        "completed_games_in_week": len(completed_week_games),
        "completed_game_ids": sorted(game_ids),
        "completed_games_with_pbp": len(completed_with_pbp),
        "completed_games_missing_pbp": len(completed_missing_pbp),
        "completed_game_ids_missing_pbp": completed_missing_pbp,
        "api_calls_this_run": client.calls,
        "files": file_audit,
    }

    atomic_text(
        AUDIT,
        json.dumps(audit, indent=2, allow_nan=False) + "\n",
    )

    print(json.dumps(audit, indent=2))

    if completed_missing_pbp:
        print(
            "Postgame acquisition is incomplete: "
            "one or more completed games do not yet have PBP."
        )


if __name__ == "__main__":
    main()
