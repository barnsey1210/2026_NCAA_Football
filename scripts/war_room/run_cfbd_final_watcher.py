#!/usr/bin/env python3
"""Budgeted CFBD scoreboard watcher and canonical-final dispatcher."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts.schedule.kickoff_quality import game_kickoff_status, parse_kickoff

CONFIG = ROOT / "config/cfbd_final_watcher.json"
DB = ROOT / "data/snapshots/preseason/preseason_db.json"
SCOREBOARD = ROOT / "data/canonical/cfbd_scoreboard_live_2026.json"
RESULTS = ROOT / "data/canonical/game_results_2026.json"
STATE_DIR = ROOT / "data/control/cfbd_final_watcher"
LATEST, STATE = STATE_DIR / "latest.json", STATE_DIR / "state.json"
API_BASE = "https://api.collegefootballdata.com"
ET = ZoneInfo("America/New_York")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True); handle.write("\n")
        tmp = Path(handle.name)
    tmp.replace(path)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return (dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt).astimezone(ET)
    except ValueError:
        return None


def canonical_games(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or DB
    rows = load_json(path, {}).get("games", [])
    return [r for r in rows if isinstance(r, dict) and int(r.get("season", 2026) or 2026) == 2026]


def monitoring_window(games: list[dict[str, Any]], now: datetime, cfg: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    now_et = now.astimezone(ET)
    before = int(cfg.get("monitor_window", {}).get("minutes_before_first_kickoff", 30))
    after = float(cfg.get("monitor_window", {}).get("hours_after_last_kickoff", 5))
    by_game_date: dict[Any, dict[str, Any]] = {}
    for game in games:
        raw = game.get("cfbd_start_date") or game.get("start_date") or game.get("kickoff")
        kickoff = parse_kickoff(raw)
        date_text = str(game.get("date") or (kickoff.date().isoformat() if kickoff else ""))[:10]
        try: game_date = datetime.fromisoformat(date_text).date()
        except ValueError: continue
        bucket = by_game_date.setdefault(game_date, {"verified": [], "unresolved": 0, "games": 0})
        bucket["games"] += 1
        if game_kickoff_status(game) == "VERIFIED_KICKOFF" and kickoff:
            bucket["verified"].append(kickoff)
        else:
            bucket["unresolved"] += 1
    windows = []
    unresolved_days = []
    for game_date, bucket in by_game_date.items():
        verified = bucket["verified"]
        if not verified:
            if game_date in {now_et.date(), now_et.date()-timedelta(days=1)}:
                unresolved_days.append(game_date.isoformat())
            continue
        start = min(verified) - timedelta(minutes=before)
        end = max(verified) + timedelta(hours=after)
        if bucket["unresolved"]:
            # Mixed-quality days remain bounded but cover unresolved late games
            # through 5 AM ET the following day.
            fallback_end = datetime.combine(game_date + timedelta(days=1), datetime.min.time(), ET) + timedelta(hours=5)
            end = max(end, fallback_end)
        windows.append((start, end, game_date, bucket))
    active = [w for w in windows if w[0] <= now_et <= w[1]]
    detail: dict[str, Any] = {"now_et": now_et.isoformat(), "scheduled_games": sum(x["games"] for x in by_game_date.values()), "verified_kickoffs": sum(len(x["verified"]) for x in by_game_date.values()), "unresolved_kickoffs": sum(x["unresolved"] for x in by_game_date.values())}
    if not active:
        detail["reason"] = "GAME_DAY_TIME_UNRESOLVED" if unresolved_days else "NO_ACTIVE_CANONICAL_GAME_WINDOW"
        if unresolved_days: detail["unresolved_game_dates"] = unresolved_days
        return False, detail
    detail.update(window_start_et=min(w[0] for w in active).isoformat(), window_end_et=max(w[1] for w in active).isoformat(), active_game_dates=sorted({w[2].isoformat() for w in active}), mixed_quality_fallback=any(w[3]["unresolved"] for w in active))
    return True, detail


def norm_team(value: Any) -> str:
    return " ".join(str(value or "").lower().replace("&", "and").split())


def canonical_index(games: list[dict[str, Any]]) -> tuple[dict[str, dict], dict[tuple[str, str, str], dict]]:
    by_id: dict[str, dict] = {}; by_match: dict[tuple[str, str, str], dict] = {}
    for game in games:
        if game.get("cfbd_game_id") not in (None, ""):
            by_id[str(game["cfbd_game_id"])] = game
        dt = parse_dt(game.get("cfbd_start_date") or game.get("start_date"))
        date = dt.date().isoformat() if dt else str(game.get("date") or "")[:10]
        by_match[(date, norm_team(game.get("away_team")), norm_team(game.get("home_team")))] = game
    return by_id, by_match


def normalize_scoreboard(raw: Any, canonical: list[dict[str, Any]], pulled_at: str) -> list[dict[str, Any]]:
    rows = raw if isinstance(raw, list) else (raw.get("games", []) if isinstance(raw, dict) else [])
    by_id, by_match = canonical_index(canonical); output = []
    for row in rows:
        if not isinstance(row, dict): continue
        gid = row.get("id", row.get("gameId", row.get("game_id")))
        start = row.get("startDate", row.get("start_date", row.get("startTime")))
        away_obj, home_obj = row.get("awayTeam", row.get("away_team")), row.get("homeTeam", row.get("home_team"))
        away = away_obj.get("name") if isinstance(away_obj, dict) else away_obj
        home = home_obj.get("name") if isinstance(home_obj, dict) else home_obj
        dt = parse_dt(start)
        match = by_id.get(str(gid)) if gid not in (None, "") else None
        if not match:
            match = by_match.get(((dt.date().isoformat() if dt else str(start or "")[:10]), norm_team(away), norm_team(home)))
        if not match: continue
        output.append({
            "game_id": str(match.get("game_id") or ""), "cfbd_game_id": gid,
            "start_date": start, "start_time_tbd": row.get("startTimeTBD", row.get("start_time_tbd")),
            "status": row.get("status", row.get("gameStatus")), "period": row.get("period"), "clock": row.get("clock"),
            "home_team": home, "away_team": away,
            "home_points": home_obj.get("points") if isinstance(home_obj, dict) else row.get("homePoints", row.get("home_points")),
            "away_points": away_obj.get("points") if isinstance(away_obj, dict) else row.get("awayPoints", row.get("away_points")),
            "home_classification": home_obj.get("classification") if isinstance(home_obj, dict) else row.get("homeClassification", row.get("home_classification")),
            "away_classification": away_obj.get("classification") if isinstance(away_obj, dict) else row.get("awayClassification", row.get("away_classification")),
            "possession": row.get("possession"), "last_play": row.get("lastPlay", row.get("last_play")), "pulled_at": pulled_at,
        })
    return output


def is_final(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").upper()
    return ("FINAL" in status or status in {"COMPLETED", "COMPLETE"}) and row.get("home_points") is not None and row.get("away_points") is not None


def accepted_result_ids(path: Path | None = None) -> set[str]:
    path = path or RESULTS
    payload = load_json(path, {}); rows = payload.get("games") or payload.get("results") or []
    return {str(row[key]) for row in rows if isinstance(row, dict) for key in ("game_id", "cfbd_game_id") if row.get(key) not in (None, "")}


class Budget:
    def __init__(self, cfg: dict[str, Any], now: datetime):
        self.limit = int(cfg.get("monthly_call_limit", 5000)); self.reserve = int(cfg.get("protected_reserve_calls", 500))
        self.path = STATE_DIR / f"usage_{now.astimezone(timezone.utc):%Y-%m}.json"
        self.data = load_json(self.path, {"schema_version": 1, "month_utc": f"{now:%Y-%m}", "calls_used": 0, "operations": []})

    def allowed(self, calls: int = 1) -> bool:
        return int(self.data.get("calls_used", 0)) + calls <= self.limit - self.reserve

    def record(self, endpoint: str, run_id: str, trigger: str, outcome: str, now: datetime) -> None:
        used = int(self.data.get("calls_used", 0)) + 1
        self.data.update(calls_used=used, estimated_remaining_calls=self.limit-used, protected_reserve_calls=self.reserve)
        self.data.setdefault("operations", []).append({"timestamp": iso(now), "endpoint": endpoint, "calls": 1, "cumulative_month_usage": used, "estimated_remaining_calls": self.limit-used, "run_id": run_id, "trigger": trigger, "outcome": outcome})
        atomic_json(self.path, self.data)


def provider_get(endpoint: str, params: dict[str, Any], key: str) -> Any:
    request = urllib.request.Request(API_BASE + endpoint + "?" + urllib.parse.urlencode(params), headers={"Authorization": f"Bearer {key}", "Accept": "application/json", "User-Agent": "ncaaf-war-room/1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False, timeout=3600)


def execute(*, now: datetime, cfg: dict[str, Any], trigger: str, fetch: Callable = provider_get, runner: Callable = run_command) -> tuple[int, dict[str, Any]]:
    run_id = f"cfbd-final-{now.astimezone(timezone.utc):%Y%m%dT%H%M%SZ}"
    report: dict[str, Any] = {"schema_version": 1, "run_id": run_id, "checked_at": iso(now), "status": "STARTED", "api_calls_this_run": 0, "trigger": trigger}
    if not cfg.get("enabled", False): report["status"] = "DISABLED"; return 0, report
    games = canonical_games(); active, window = monitoring_window(games, now, cfg); report["window"] = window
    if not active:
        report["status"] = "GAME_DAY_TIME_UNRESOLVED" if window.get("reason") == "GAME_DAY_TIME_UNRESOLVED" else "OUTSIDE_GAME_WINDOW"
        return 0, report
    key = os.environ.get("CFBD_API_KEY", "").strip()
    if not key: report.update(status="PROVIDER_FAILED", error="CFBD_API_KEY unavailable"); return 2, report
    budget = Budget(cfg, now)
    if not budget.allowed(): report["status"] = "BUDGET_BLOCKED"; return 2, report
    try:
        raw = fetch("/scoreboard", {}, key)
        budget.record("/scoreboard", run_id, trigger, "SUCCESS", now); report["api_calls_this_run"] += 1
    except Exception as exc:
        budget.record("/scoreboard", run_id, trigger, f"FAILED:{type(exc).__name__}", now)
        report.update(status="PROVIDER_FAILED", error=f"scoreboard request failed: {type(exc).__name__}"); return 2, report
    pulled_at = iso(now); normalized = normalize_scoreboard(raw, games, pulled_at)
    atomic_json(SCOREBOARD, {"schema_version": "cfbd-scoreboard-live-v1", "pulled_at": pulled_at, "source": "CFBD /scoreboard", "games": normalized})
    live_build = runner([sys.executable, "scripts/site/build_schedule_live_enrichment.py"])
    if live_build.returncode != 0:
        report.update(status="SCHEDULE_BUILD_FAILED", error="live Schedule enrichment build failed")
        return 2, report
    state = load_json(STATE, {"schema_version": 1, "candidates": {}, "accepted": {}, "dispatched": {}})
    pending = [r for r in normalized if is_final(r) and r["game_id"] not in state.get("dispatched", {})]
    if not pending: report.update(status="NO_NEW_FINALS", relevant_games=len(normalized)); return 0, report
    retry_cfg = cfg.get("retry_policy", {}); max_attempts = int(retry_cfg.get("max_attempts", 4))
    for row in pending: state.setdefault("candidates", {}).setdefault(row["game_id"], {"first_seen_at": pulled_at, "attempts": 0})
    accepted_state = state.get("accepted", {})
    already_accepted = []
    waiting_accepted = []
    for row in pending:
        meta = accepted_state.get(row["game_id"])
        if not meta: continue
        retry_at = parse_dt(meta.get("postgame_next_retry_at"))
        attempts = int(meta.get("postgame_attempts", 0))
        if attempts < max_attempts and (not retry_at or now.astimezone(ET) >= retry_at): already_accepted.append(row)
        else: waiting_accepted.append(row)
    validate = []
    for row in pending:
        if row["game_id"] in accepted_state: continue
        item = state["candidates"][row["game_id"]]
        next_retry = parse_dt(item.get("next_retry_at"))
        if int(item.get("attempts", 0)) < max_attempts and (not next_retry or now.astimezone(ET) >= next_retry): validate.append(row)
    atomic_json(STATE, state); report["status"] = "FINAL_CANDIDATE"
    accepted = list(already_accepted); newly_accepted: list[dict[str, Any]] = []; rejected: list[dict[str, Any]] = []
    if validate:
        if not budget.allowed(): report["status"] = "BUDGET_BLOCKED"; return 2, report
        schedule = runner([sys.executable, "scripts/schedule/pull_cfbd_schedule_2026.py"])
        budget.record("/games", run_id, trigger, "SUCCESS" if schedule.returncode == 0 else "FAILED", now); report["api_calls_this_run"] += 1
        if schedule.returncode != 0: report.update(status="PROVIDER_FAILED", error="canonical /games refresh failed"); return 2, report
        results = runner([sys.executable, "scripts/results/build_game_results_2026.py"])
        if results.returncode != 0: report.update(status="PROVIDER_FAILED", error="canonical results build failed"); return 2, report
        accepted_ids = accepted_result_ids(); newly_accepted = [r for r in validate if r["game_id"] in accepted_ids or str(r.get("cfbd_game_id")) in accepted_ids]; accepted.extend(newly_accepted)
        rejected = [r for r in validate if r not in accepted]
    delays = retry_cfg.get("delays_minutes", [5, 10, 30])
    for row in rejected:
        item = state["candidates"][row["game_id"]]; item["attempts"] = int(item.get("attempts", 0)) + 1
        delay = delays[min(item["attempts"]-1, len(delays)-1)] if delays else 5
        item.update(last_attempt_at=pulled_at, next_retry_at=iso(now + timedelta(minutes=float(delay))))
    for row in newly_accepted: state.setdefault("accepted", {})[row["game_id"]] = {"accepted_at": pulled_at, "cfbd_game_id": row.get("cfbd_game_id")}
    atomic_json(STATE, state)
    if not accepted and waiting_accepted:
        report.update(status="POSTGAME_FAILED", retryable_game_ids=[r["game_id"] for r in waiting_accepted if int(accepted_state[r["game_id"]].get("postgame_attempts", 0)) < max_attempts])
        return 0, report
    if not accepted:
        report.update(status="FINAL_CANDIDATE", retryable_game_ids=[r["game_id"] for r in pending if int(state["candidates"][r["game_id"]].get("attempts", 0)) < max_attempts]); return 0, report
    report["status"] = "FINAL_ACCEPTED"; failed = []
    for row in accepted:
        task_id = f"postgame-{row['game_id'].lower().replace('_','-')}-{now:%Y%m%d%H%M%S}"[:64]
        result = runner([sys.executable, "scripts/control/run_war_room_service.py", "postgame", "--trigger", "cfbd-final-watcher", "--requester", "scheduler", "--task-id", task_id, "--prepared-results"])
        if result.returncode == 0: state.setdefault("dispatched", {})[row["game_id"]] = {"task_id": task_id, "completed_at": pulled_at}
        else:
            failed.append(row["game_id"])
            meta = state["accepted"][row["game_id"]]
            attempts = int(meta.get("postgame_attempts", 0)) + 1
            delay = delays[min(attempts-1, len(delays)-1)] if delays else 5
            meta.update(postgame_attempts=attempts, postgame_last_attempt_at=pulled_at, postgame_next_retry_at=iso(now + timedelta(minutes=float(delay))))
    atomic_json(STATE, state)
    report.update(status="POSTGAME_FAILED" if failed else "POSTGAME_DISPATCHED", accepted_game_ids=[r["game_id"] for r in accepted], failed_game_ids=failed)
    return (2 if failed else 0), report


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--trigger", default="scheduler"); args = parser.parse_args()
    code, report = execute(now=utc_now(), cfg=load_json(CONFIG, {}), trigger=args.trigger)
    atomic_json(LATEST, report); append_jsonl(STATE_DIR / "runs.jsonl", report); print(json.dumps(report, indent=2)); return code


if __name__ == "__main__": raise SystemExit(main())
