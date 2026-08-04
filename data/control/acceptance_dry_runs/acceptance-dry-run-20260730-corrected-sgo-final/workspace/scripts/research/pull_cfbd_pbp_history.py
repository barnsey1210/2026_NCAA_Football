#!/usr/bin/env python3
"""Cache CFBD historical PBP inputs as gzip JSON with a strict API-call cap."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests


BASE_URL = "https://api.collegefootballdata.com"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_key(path: Path) -> str:
    key = os.environ.get("CFBD_API_KEY", "").strip()
    if not key and path.exists():
        key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise SystemExit("CFBD key unavailable; set CFBD_API_KEY or provide --key-file")
    return key


def read_gzip(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def write_gzip(path: Path, endpoint: str, params: Dict[str, Any], data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        json.dump({"fetched_at": now_iso(), "endpoint": endpoint, "params": params, "data": data}, handle)


class Client:
    def __init__(self, key: str, root: Path, max_calls: int, legacy_2024: Path):
        self.root = root
        self.max_calls = max_calls
        self.calls = 0
        self.legacy_2024 = legacy_2024
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "ncaaf-pbp-history/0.1",
        })

    def get(self, season: int, endpoint: str, params: Dict[str, Any], name: str, force: bool = False) -> List[Dict[str, Any]]:
        path = self.root / str(season) / f"{name}.json.gz"
        if path.exists() and not force:
            return read_gzip(path)
        legacy = self.legacy_2024 / f"{name}.json"
        if season == 2024 and legacy.exists():
            payload = json.loads(legacy.read_text(encoding="utf-8"))
            data = payload.get("data", payload) if isinstance(payload, dict) else payload
            write_gzip(path, endpoint, params, data)
            return data
        if self.calls >= self.max_calls:
            raise RuntimeError(f"API call cap of {self.max_calls} reached")
        response = self.session.get(BASE_URL + endpoint, params=params, timeout=180)
        self.calls += 1
        if response.status_code in (400, 401, 403, 429):
            raise RuntimeError(f"CFBD {endpoint} HTTP {response.status_code}: {response.text[:500]}")
        response.raise_for_status()
        data = response.json()
        write_gzip(path, endpoint, params, data)
        time.sleep(0.15)
        return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025])
    parser.add_argument("--key-file", type=Path, default=Path("/private/tmp/ncaaf_cfbd_api_key"))
    parser.add_argument("--cache-root", type=Path, default=Path("cfbd_cache/pbp_history"))
    parser.add_argument("--legacy-2024", type=Path, default=Path("cfbd_cache/pbp_pilot_2024"))
    parser.add_argument("--max-calls", type=int, default=120)
    parser.add_argument("--through-week", type=int, help="Only request plays through this week; useful in-season.")
    parser.add_argument("--refresh-week", type=int, help="Replace the cached PBP file for this week.")
    parser.add_argument("--refresh-season-aggregates", action="store_true", help="Refresh drives, advanced, and havoc.")
    args = parser.parse_args()

    client = Client(load_key(args.key_file), args.cache_root, args.max_calls, args.legacy_2024)
    manifest: Dict[str, Any] = {"built_at": now_iso(), "seasons": {}, "api_calls_this_run": 0}
    for season in args.seasons:
        base = {"year": season, "seasonType": "regular"}
        calendar = client.get(season, "/calendar", {"year": season}, "calendar")
        teams = client.get(season, "/teams/fbs", {"year": season}, "teams_fbs")
        weeks = sorted({
            int(row["week"]) for row in calendar
            if str(row.get("seasonType") or row.get("season_type") or "").lower() == "regular"
        })
        if args.through_week is not None:
            weeks = [week for week in weeks if week <= args.through_week]
        if not weeks:
            raise RuntimeError(f"No regular-season weeks for {season}")
        weekly_counts = {}
        for week in weeks:
            plays = client.get(season, "/plays", {**base, "week": week}, f"plays_week_{week:02d}", force=week == args.refresh_week)
            weekly_counts[str(week)] = len(plays)
            del plays
        drives = client.get(season, "/drives", base, "drives_regular", force=args.refresh_season_aggregates)
        advanced = client.get(season, "/stats/game/advanced", base, "advanced_regular", force=args.refresh_season_aggregates)
        havoc = client.get(season, "/stats/game/havoc", base, "havoc_regular", force=args.refresh_season_aggregates)
        manifest["seasons"][str(season)] = {
            "regular_weeks": weeks,
            "fbs_teams": len(teams),
            "weekly_play_rows": weekly_counts,
            "total_play_rows": sum(weekly_counts.values()),
            "drive_rows": len(drives),
            "advanced_rows": len(advanced),
            "havoc_rows": len(havoc),
        }
        del calendar, teams, drives, advanced, havoc
        print(season, manifest["seasons"][str(season)])
    manifest["api_calls_this_run"] = client.calls
    manifest["gzip_files"] = len(list(args.cache_root.glob("*/*.json.gz")))
    manifest["cache_bytes"] = sum(p.stat().st_size for p in args.cache_root.glob("*/*.json.gz"))
    args.cache_root.mkdir(parents=True, exist_ok=True)
    (args.cache_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
