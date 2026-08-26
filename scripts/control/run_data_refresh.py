#!/usr/bin/env python3
"""Safe orchestration layer for the existing NCAAF refresh pipelines.

Status and previews remain safe by default. Controlled production execution is
enabled only for The Odds API game odds and the guarded CFBD postgame rebuild.
Publication requires mode policy plus explicit confirmation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CONTROL = ROOT / "data/control"
REPORTS = ROOT / "reports"
CONFIG_PATH = ROOT / "scripts/control/refresh_controller_config.json"
REGISTRY_PATH = ROOT / "scripts/control/refresh_stage_registry.json"
LEDGER = CONTROL / "refresh_runs.jsonl"
HISTORY = CONTROL / "refresh_run_history.json"
LATEST = CONTROL / "latest_refresh_status.json"
USAGE = CONTROL / "api_usage.jsonl"
STATE = CONTROL / "provider_state.json"
LOCK = CONTROL / "refresh.lock"
SUMMARY = REPORTS / "latest_refresh_summary.md"
RUN_LOGS = CONTROL / "logs"
PUBLISH_REPO = Path(os.environ.get("NCAAF_PUBLISH_REPO", "/Users/jameslindesmith/Sites/NCAAF_SITE"))

V2_SHELLS = [
    "index.html", "dashboard_v2.html", "openers_v2.html", "matchups_v2.html",
    "schedule_v2.html", "odds_v2.html", "ratings_v2.html", "futures_v2.html",
    "conferences_v2.html", "simulations_v2.html", "betting_v2.html",
    "team.html", "matchup.html",
]
WATCHED_OUTPUTS = [
    "data/odds/season_game_lines_2026.csv", "data/odds/game_line_history.csv",
    "data/site/matchup_line_history.json", "data/site/matchups_view.json",
    "data/site/odds_screen_v2.json", "data/site/odds_futures_v2.json",
    "data/ratings/ratings_latest.csv", "data/ratings/ratings_master_latest.csv",
    "data/projections/game_projection_blend_2026.csv",
]
RATING_SOURCES = {
    "SP+": "spplus", "FPI": "fpi", "TeamRankings": "teamrankings",
    "Brad Powers": "brad_powers", "Sagarin Predictor": "sagarin",
    "Massey Power": "massey", "Donchess Overall": "donchess", "KFord": "kford",
}
SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|password|authorization|bearer)\s*[:=]\s*[^\s,]+")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def file_hash(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hashes(paths: list[str]) -> dict[str, str | None]:
    return {p: file_hash(ROOT / p) for p in paths}


def safe_text(value: str) -> str:
    text = SECRET_RE.sub(lambda m: m.group(1) + "=[REDACTED]", value)
    for key, val in os.environ.items():
        if val and len(val) >= 8 and any(x in key.upper() for x in ("KEY", "TOKEN", "PASSWORD", "SECRET")):
            text = text.replace(val, "[REDACTED]")
    return text.replace(str(ROOT), "<PROJECT_ROOT>").replace(str(Path.home()), "<HOME>")


def shell(command: list[str], timeout: int = 1800) -> dict[str, Any]:
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    output = safe_text(((result.stdout or "") + (result.stderr or ""))[-12000:])
    return {"command": [str(x).replace(str(ROOT), "<PROJECT_ROOT>") for x in command],
            "returncode": result.returncode, "duration_seconds": round(time.monotonic()-started, 3),
            "output_tail": output}


def run_commands(run: dict[str, Any], commands: list[list[str]]) -> bool:
    """Run a reviewed command list, stopping at the first failure."""
    for command in commands:
        result = shell(command)
        name = Path(command[1]).name if len(command) > 1 else command[0]
        run["stages"].append({
            "name": name,
            "status": "PASSED" if result["returncode"] == 0 else "FAILED",
            **result,
        })
        if result["returncode"] != 0:
            run["errors"].append(f"{name} failed")
            return False
    return True


def accepted_ratings_changed() -> tuple[bool, dict[str, str]]:
    state = load_json(ROOT / "data/ratings/live_rating_change_status.json", {})
    statuses = {
        str(name): str(row.get("change_status") or "UNKNOWN")
        for name, row in (state.get("sources") or {}).items()
        if isinstance(row, dict)
    }
    return any(value in {"UPDATED", "INITIALIZED"} for value in statuses.values()), statuses


def matchup_source_refresh_status() -> tuple[bool, dict[str, Any]]:
    report = load_json(ROOT / "data/control/ratings_fast_source_refresh.json", {})
    changed = bool(report.get("changed_providers"))
    return changed, report


def ratings_acquisition_commands() -> list[list[str]]:
    return [
        [sys.executable, "scripts/ratings/test_rating_sources.py", "--sources", "spplus,fpi,teamrankings"],
        [sys.executable, "scripts/ratings/parse_rating_source_tables.py"],
        [sys.executable, "scripts/ratings/accept_live_rating_candidates_with_status.py"],
        [sys.executable, "scripts/ratings/run_fast_standard_source_refresh.py"],
    ]


def ratings_change_commands(matchup_report: dict[str, Any] | None = None) -> list[list[str]]:
    """Bounded canonical propagation after at least one accepted panel changes."""
    window = (matchup_report or {}).get("window") or {}
    bounds = []
    if window.get("start") and window.get("end"):
        bounds = ["--start-date", window["start"], "--end-date", window["end"]]
    return [
        [sys.executable, "scripts/ratings/build_all_ratings_latest.py"],
        [sys.executable, "scripts/ratings/build_active_2026_ratings_master.py"],
        [sys.executable, "scripts/ratings/merge_live_rating_change_status.py"],
        [sys.executable, "ratings/append_ratings_history.py"],
        [sys.executable, "ratings/build_ratings_movement.py"],
        [sys.executable, "scripts/projections/build_game_projection_sources_2026.py", *bounds],
        [sys.executable, "scripts/projections/build_current_game_projection_contract.py", *bounds],
        [sys.executable, "scripts/site/build_projection_source_status_view.py"],
        [sys.executable, "scripts/site/build_matchups_view.py"],
        [sys.executable, "scripts/audit/validate_projection_resolver.py"],
        [sys.executable, "scripts/war_room/build_war_room_health.py"],
        [sys.executable, "scripts/war_room/build_war_room_market_matrix.py"],
    ]


def ratings_no_change_commands(
    matchup_report: dict[str, Any] | None = None,
) -> list[list[str]]:
    """Refresh bounded provider observability even when values are unchanged."""
    window = (matchup_report or {}).get("window") or {}
    bounds = []
    if window.get("start") and window.get("end"):
        bounds = ["--start-date", window["start"], "--end-date", window["end"]]
    return [
        [sys.executable, "scripts/projections/build_game_projection_sources_2026.py", *bounds],
        [sys.executable, "scripts/site/build_projection_source_status_view.py"],
        [sys.executable, "scripts/war_room/build_war_room_health.py"],
    ]


def postgame_commands() -> list[list[str]]:
    """Bounded runtime-only Postgame propagation; never publishes the site."""
    return [
        [sys.executable, "scripts/schedule/pull_cfbd_schedule_2026.py"],
        [sys.executable, "scripts/results/build_game_results_2026.py"],
        [sys.executable, "scripts/postgame/pull_cfbd_postgame_2026.py"],
        [sys.executable, "scripts/postgame/build_postgame_features_2026.py"],
        [sys.executable, "scripts/postgame/build_shadow_team_game_features_2026.py"],
        [sys.executable, "scripts/site/build_saturday_shadow_component_predictions.py"],
        [sys.executable, "scripts/projections/build_current_game_projection_contract.py"],
        [sys.executable, "scripts/site/build_matchups_view.py"],
        [sys.executable, "scripts/site/build_saturday_shadow_lines.py"],
        [sys.executable, "scripts/audit/validate_projection_resolver.py"],
        [sys.executable, "scripts/site/build_schedule_live_enrichment.py"],
        [sys.executable, "scripts/model_tracking/settle_model_tracking.py", "--accept"],
        [sys.executable, "scripts/model_tracking/build_model_performance_view.py"],
        [sys.executable, "scripts/war_room/build_war_room_health.py"],
        [sys.executable, "scripts/war_room/build_war_room_market_matrix.py"],
    ]


def execute_postgame_service(run: dict[str, Any]) -> None:
    if run_commands(run, postgame_commands()):
        run["status"] = "COMPLETED"
        run["publication"] = {"status": "SKIPPED_RUNTIME_ONLY"}
    else:
        run["status"] = "FAILED"


def execute_ratings_service(
    run: dict[str, Any], cfg: dict[str, Any], confirm: bool
) -> None:
    """Execute only the bounded Ratings service contract."""
    service_allowed = cfg.get("publication_policy", {}).get("ratings", False)
    if not confirm:
        run["status"] = "BLOCKED_BY_CONFIGURATION"
        run["errors"].append("ratings requires --confirm-publish")
        return
    if not service_allowed:
        run["status"] = "BLOCKED_BY_CONFIGURATION"
        run["errors"].append("ratings service policy is disabled")
        return
    if not run_commands(run, ratings_acquisition_commands()):
        run["status"] = "FAILED"
        return

    global_changed, statuses = accepted_ratings_changed()
    matchup_changed, matchup_report = matchup_source_refresh_status()
    changed = global_changed or matchup_changed
    run["providers_called"] = [
        "spplus", "fpi", "teamrankings", "sagarin", "dratings", "massey"
    ]
    # Free webpage activity is distinct from quota-bearing provider credits.
    run["api"]["calls_consumed"] = 0
    run["api"]["credits_consumed"] = 0
    run["api"]["web_provider_contacts"] = len(run["providers_called"])
    run["validation_results"]["accepted_rating_changes"] = statuses
    run["validation_results"]["matchup_source_refresh"] = matchup_report
    run["change_counts"] = {
        "ratings": sum(
            value in {"UPDATED", "INITIALIZED"} for value in statuses.values()
        ) + len(matchup_report.get("changed_providers") or []),
        "projections": 0,
    }
    commands = (
        ratings_change_commands(matchup_report)
        if changed
        else ratings_no_change_commands(matchup_report)
    )
    if run_commands(run, commands):
        run["change_counts"]["projections"] = 1 if changed else 0
        run["status"] = "COMPLETED" if changed else "NO_CHANGES"
    else:
        run["status"] = "FAILED"


def deployed_commit() -> str | None:
    record = load_json(CONTROL / "deployed_source_version.json", {})
    value = str(record.get("source_commit") or "").strip()
    return value or None


def newest_timestamp(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        if path.suffix == ".json":
            data = load_json(path, {})
            candidates: list[str] = []
            def walk(v: Any) -> None:
                if isinstance(v, dict):
                    for k, x in v.items():
                        if any(t in k.lower() for t in ("timestamp", "updated", "pulled", "snapshot")) and isinstance(x, str): candidates.append(x)
                        walk(x)
                elif isinstance(v, list):
                    for x in v: walk(x)
            walk(data)
            return max(candidates) if candidates else None
        with path.open(newline="", errors="ignore") as fh:
            rows = csv.DictReader(fh)
            vals: list[str] = []
            for row in rows:
                for k in ("snapshot_ts", "pulled_at", "last_update", "snapshot_date", "rating_date"):
                    if row.get(k): vals.append(row[k])
            return max(vals) if vals else None
    except Exception:
        return None


def ratings_status(test_scenario: str = "") -> list[dict[str, Any]]:
    status_path = ROOT / "data/ratings/ratings_source_status.csv"
    latest_path = ROOT / "data/ratings/ratings_latest.csv"
    rows = list(csv.DictReader(status_path.open(newline=""))) if status_path.exists() else []
    by_source = {r.get("source", ""): r for r in rows}
    latest_rows = list(csv.DictReader(latest_path.open(newline=""))) if latest_path.exists() else []
    result = []
    for display, key in RATING_SOURCES.items():
        row = by_source.get(display, {})
        source_rows = [x for x in latest_rows if x.get("source") == display]
        team_names = [re.sub(r"[^a-z0-9]+", "", (x.get("team") or "").lower()) for x in source_rows if x.get("team")]
        teams = len(set(team_names)) or int(float(row.get("teams") or 0))
        duplicate_teams = max(0, len(team_names) - len(set(team_names)))
        seasons = {x.get("season") for x in source_rows if x.get("season")}
        numeric_missing = 0; out_of_range = 0
        for x in source_rows:
            try:
                value = float(x.get("rating", ""))
                if not -100 <= value <= 100: out_of_range += 1
            except (TypeError, ValueError): numeric_missing += 1
        errors = []
        if display in {"SP+", "FPI", "TeamRankings", "Brad Powers"} and teams < 120:
            errors.append(f"team coverage {teams} below minimum 120")
        if seasons and seasons != {"2026"}: errors.append(f"unexpected seasons: {sorted(seasons)}")
        if duplicate_teams: errors.append(f"duplicate normalized teams: {duplicate_teams}")
        if numeric_missing: errors.append(f"missing/non-numeric ratings: {numeric_missing}")
        if out_of_range: errors.append(f"ratings outside -100..100: {out_of_range}")
        if test_scenario == "rating_failure" and display == "FPI": errors.append("injected source failure")
        if test_scenario == "malformed_rating" and display == "SP+": errors.append("injected malformed parser output")
        result.append({"source": display, "provider_key": key, "check_timestamp": now(),
                       "status": "REJECTED" if errors else ("UNAVAILABLE" if not row else "CHECKED_NO_CHANGE"),
                       "source_reported_update_date": row.get("source_updated_at") or None,
                       "accepted_snapshot_date": row.get("snapshot_date") or None,
                       "teams": teams, "missing_teams": max(0, 138-teams) if teams else None,
                       "duplicate_teams": duplicate_teams if source_rows else None, "parsing_warnings": errors,
                       "content_hash": hashlib.sha256(json.dumps(source_rows, sort_keys=True).encode()).hexdigest() if source_rows else None, "content_changed": False,
                       "passed_validation": not errors and bool(row), "replaced_accepted_snapshot": False,
                       "rejection_reason": "; ".join(errors) or None, "downstream_rebuilt": False})
    return result


def lock_info() -> dict[str, Any] | None:
    return load_json(LOCK, None) if LOCK.exists() else None


def acquire_lock(run_id: str, stale_minutes: int) -> None:
    CONTROL.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        age = (time.time() - LOCK.stat().st_mtime) / 60
        if age <= stale_minutes: raise RuntimeError("another refresh is already running")
        LOCK.unlink()
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as fh: json.dump({"run_id": run_id, "pid": os.getpid(), "started_at": now(), "host": socket.gethostname()}, fh)


def release_lock(run_id: str) -> None:
    if LOCK.exists() and (load_json(LOCK, {}) or {}).get("run_id") == run_id: LOCK.unlink()


def provider_gate(provider: str, cfg: dict[str, Any], state: dict[str, Any], scenario: str) -> tuple[bool, str | None]:
    p = cfg["providers"].get(provider, {})
    if scenario == "quota_block": return False, "quota below safety threshold"
    if scenario == "cooldown_block": return False, "provider cooldown active"
    prior = state.get(provider, {}).get("last_attempt_epoch")
    if prior and time.time()-float(prior) < int(p.get("cooldown_seconds", 0)):
        return False, "provider cooldown active"
    remaining = state.get(provider, {}).get("remaining")
    if remaining is not None and float(remaining) <= float(p.get("low_quota_threshold", 0)):
        return False, "quota below safety threshold"
    return True, None


def current_status() -> dict[str, Any]:
    status = load_json(LATEST, {})
    history = load_json(HISTORY, [])
    last_odds = next((x.get("completion_timestamp") for x in history if x.get("requested_mode") in {"odds", "full"} and x.get("status") in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}), None)
    last_publish = next((x.get("completion_timestamp") for x in history if x.get("publication", {}).get("status") == "COMPLETED"), None)
    pub_dirty = None
    if (PUBLISH_REPO / ".git").exists():
        check = subprocess.run(["git", "-C", str(PUBLISH_REPO), "status", "--porcelain"], text=True, capture_output=True)
        pub_dirty = bool(check.stdout.strip()) if check.returncode == 0 else None
    last_run = history[0] if history else status
    status.update({"schema_version": 2, "generated_at": now(), "refresh_running": bool(lock_info()),
                   "active_lock": lock_info(), "latest_market_timestamp": newest_timestamp(ROOT/"data/odds/game_line_history.csv"),
                   "latest_projection_build": datetime.fromtimestamp((ROOT/"data/projections/game_projection_blend_2026.csv").stat().st_mtime, timezone.utc).isoformat() if (ROOT/"data/projections/game_projection_blend_2026.csv").exists() else None,
                   "currently_deployed_commit": deployed_commit(), "rating_sources": ratings_status(),
                   "provider_state": load_json(STATE, {}), "status_only_external_calls": 0,
                   "last_successful_odds_refresh": last_odds, "latest_publish": last_publish,
                   "publication_repository_dirty": pub_dirty,
                   "current_run": lock_info(), "last_run_result": last_run.get("status"),
                   "publication_result": last_run.get("publication", {}).get("status"),
                   "change_counts": {"games": last_run.get("change_counts", {}).get("games", 0),
                     "spreads": last_run.get("change_counts", {}).get("spreads", 0), "totals": last_run.get("change_counts", {}).get("totals", 0),
                     "ratings": last_run.get("change_counts", {}).get("ratings", 0), "projections": last_run.get("change_counts", {}).get("projections", 0),
                     "new_edges": last_run.get("change_counts", {}).get("new_edges", 0), "removed_edges": last_run.get("change_counts", {}).get("removed_edges", 0)},
                   "api_usage": load_json(STATE, {}), "warnings": last_run.get("warnings", []), "errors": last_run.get("errors", []),
                   "what_changed": "No accepted data changes." if not last_run.get("files_changed") else f"{len(last_run.get('files_changed', []))} controlled assets changed."})
    return status


def write_records(run: dict[str, Any], cfg: dict[str, Any]) -> None:
    CONTROL.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)
    RUN_LOGS.mkdir(parents=True, exist_ok=True)
    atomic_json(RUN_LOGS / f"{run['run_id']}.json", run)
    with LEDGER.open("a") as fh: fh.write(json.dumps(run, sort_keys=True) + "\n")
    if run.get("requested_scope", {}).get("providers"):
        with USAGE.open("a") as fh:
            for provider in run["requested_scope"]["providers"]:
                fh.write(json.dumps({"run_id": run["run_id"], "provider": provider,
                    "endpoint": "planned_scope", "request_timestamp": run["start_timestamp"],
                    "estimated_cost": cfg.get("providers", {}).get(provider, {}).get("estimated_cost", 0),
                    "actual_cost": run.get("api", {}).get("actual_cost"), "dry_run": not bool(run.get("providers_called")),
                    "remaining": run.get("api", {}).get("remaining", {}).get(provider)}) + "\n")
    history = load_json(HISTORY, [])
    history = ([run] + history)[:int(cfg.get("history_limit", 100))]
    atomic_json(HISTORY, history); atomic_json(LATEST, run)
    lines = [f"# Refresh {run['status']}", "", f"- Run: `{run['run_id']}`", f"- Mode: {run['requested_mode']}",
             f"- Started: {run['start_timestamp']}", f"- Completed: {run['completion_timestamp']}",
             f"- External calls: {run['api']['calls_consumed']}", f"- Estimated cost: {run['api']['estimated_cost']}",
             f"- Publication: {run['publication']['status']}", "", "## Stages", ""]
    lines += [f"- {s['name']}: {s['status']} ({s.get('duration_seconds',0)}s)" for s in run["stages"]]
    lines += ["", "## API usage", ""]
    if run.get("providers_called"):
        for provider in run["providers_called"]:
            actual = run.get("api", {}).get("actual_cost")
            source = "response reported" if actual is not None else "local estimate; dashboard reconciliation required"
            lines += [f"### {provider}", "", f"- Calls this run: {run['api'].get('calls_consumed', 0)}",
                      f"- Estimated units: {run['api'].get('estimated_cost', 0)}",
                      f"- Actual units: {actual if actual is not None else 'unavailable'}", f"- Source: {source}", ""]
    else:
        lines += ["- No provider calls were made."]
    if run["warnings"]: lines += ["", "## Warnings", ""] + [f"- {x}" for x in run["warnings"]]
    if run["errors"]: lines += ["", "## Errors", ""] + [f"- {x}" for x in run["errors"]]
    SUMMARY.write_text("\n".join(lines)+"\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["status", "odds", "ratings", "postgame", "pregame", "full", "publish-existing"])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--scope", choices=["games", "futures", "both"], default="both")
    p.add_argument("--week", default="current")
    p.add_argument("--markets", default="spread,total,moneyline")
    p.add_argument("--providers", default="", help="Comma list; empty uses the canonical providers for the selected mode/scope")
    p.add_argument("--trigger-source", default="local")
    p.add_argument("--requester", default="local-user")
    p.add_argument("--confirm-publish", action="store_true")
    p.add_argument("--test-scenario", choices=["", "no_change", "rating_failure", "malformed_rating", "quota_block", "cooldown_block", "overlap"], default="")
    return p.parse_args()


def main() -> int:
    args = parse_args(); cfg = load_json(CONFIG_PATH, {}); registry = load_json(REGISTRY_PATH, {})
    if args.mode == "status":
        status = current_status(); atomic_json(LATEST, status); print(json.dumps(status, indent=2)); return 0
    if not args.dry_run and not args.execute: raise SystemExit("Choose --dry-run or --execute")
    explicit_providers = [x.strip() for x in args.providers.split(",") if x.strip()]
    if explicit_providers:
        resolved_providers = explicit_providers
    elif args.mode in {"odds", "full"}:
        stage_names = (registry.get("modes", {}).get("odds", {}).get("scopes", {}).get(args.scope, []))
        resolved_providers = []
        for stage_name in stage_names:
            for provider in registry.get("stages", {}).get(stage_name, {}).get("providers", []):
                if provider not in resolved_providers: resolved_providers.append(provider)
    else:
        resolved_providers = []
    # The reviewed executable odds path is The Odds API, games-only, current
    # canonical week. With no confirmation it remains a preview. With explicit
    # confirmation plus acceptance/publication policy it promotes and publishes.
    if args.mode == "odds" and args.execute:
        requested_markets = [x.strip() for x in args.markets.split(",") if x.strip()]
        requested_providers = resolved_providers
        if args.scope != "games" or args.week != "current" or requested_markets != ["spread","total","moneyline"] or requested_providers != ["the_odds_api"]:
            raise SystemExit("Production odds requires scope=games, week=current, markets=spread,total,moneyline, providers=the_odds_api")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run: dict[str, Any] = {"schema_version": 1, "run_id": run_id, "trigger_source": args.trigger_source,
        "requester_identity": re.sub(r"[^A-Za-z0-9_.@-]", "_", args.requester)[:80], "requested_mode": args.mode,
        "requested_scope": {"scope": args.scope, "week": args.week, "markets": args.markets.split(","), "providers": resolved_providers},
        "mode_plan": (registry.get("modes", {}).get(args.mode) or {}),
        "start_timestamp": now(), "completion_timestamp": None, "status": "RUNNING", "stage": "lock",
        "host": socket.gethostname(), "execution_environment": sys.platform, "deployed_commit_before": deployed_commit(),
        "deployed_commit_after": None, "files_changed": [], "providers_called": [], "warnings": [], "errors": [],
        "validation_results": {}, "publication": {"status": "SKIPPED"}, "api": {"calls_consumed": 0, "estimated_cost": 0, "remaining": {}}, "stages": []}
    before = hashes(WATCHED_OUTPUTS); shell_before = hashes(V2_SHELLS)
    try:
        if args.test_scenario == "overlap":
            CONTROL.mkdir(parents=True, exist_ok=True); LOCK.write_text(json.dumps({"run_id":"test-overlap","started_at":now()}))
        acquire_lock(run_id, int(cfg.get("lock_stale_minutes", 180)))
        run["stages"].append({"name":"exclusive_lock","status":"PASSED","timestamp":now()})
        state = load_json(STATE, {})
        requested = resolved_providers if args.mode in {"odds","full"} else []
        blocked = []
        for provider in requested:
            ok, reason = provider_gate(provider, cfg, state, args.test_scenario)
            run["api"]["estimated_cost"] += cfg.get("providers",{}).get(provider,{}).get("estimated_cost",0)
            if not ok: blocked.append(f"{provider}: {reason}")
        if blocked:
            run["warnings"].extend(blocked); run["status"] = "BLOCKED_BY_QUOTA" if any("quota" in x for x in blocked) else "BLOCKED_BY_COOLDOWN"
        else:
            if args.mode in {"ratings","pregame","full"}:
                rs = ratings_status(args.test_scenario)
                rejected = [x for x in rs if x["status"] == "REJECTED"]
                run["validation_results"]["ratings"] = rs
                run["stages"].append({"name":"ratings_validation","status":"REJECTED" if rejected else "PASSED","timestamp":now()})
                if rejected: run["warnings"].append("one or more ratings sources rejected; last-known-good retained")
            if args.dry_run:
                mode_spec = registry.get("modes", {}).get(args.mode, {})
                stage_names = (mode_spec.get("scopes", {}).get(args.scope, []) if args.mode == "odds" else mode_spec.get("stages", []))
                for stage_name in stage_names:
                    spec = registry.get("stages", {}).get(stage_name, {})
                    run["stages"].append({"name":stage_name,"status":"DRY_RUN","timestamp":now(),
                        "commands":spec.get("commands",[]),"providers":spec.get("providers",[])})
                run["status"] = "NO_CHANGES" if args.test_scenario == "no_change" else ("COMPLETED_WITH_WARNINGS" if run["warnings"] else "COMPLETED")
            elif args.mode == "odds" and cfg.get("the_odds_api_preview_enabled", False):
                if not os.environ.get("THE_ODDS_API_KEY"):
                    run["status"]="FAILED"; run["errors"].append("THE_ODDS_API_KEY is not available to the runner")
                else:
                    from theodds_adapter import capture
                    state.setdefault("the_odds_api", {}).update({
                        "last_attempt_epoch":time.time(),"last_attempt_at":now(),
                        "last_run_id":run_id,"status":"ATTEMPTING"
                    })
                    atomic_json(STATE,state)
                    preview=capture(run_id)
                    state["the_odds_api"].update({
                        "status":"CAPTURE_COMPLETED","last_success_at":now(),
                        "actual_cost":preview.get("actual_api_cost")
                    })
                    atomic_json(STATE,state)
                    run["providers_called"]=["the_odds_api"]
                    run["api"]["calls_consumed"]=preview["external_calls"]
                    run["api"]["estimated_cost"]=preview.get("estimated_api_cost", preview.get("external_calls", 0))
                    run["api"]["actual_cost"]=preview.get("actual_api_cost")
                    run["preview"]=preview
                    complete = (
                        preview.get("coverage_status") == "COMPLETE"
                        and not preview.get("next_cursor_present")
                        and int(preview.get("missing_canonical_games", 0) or 0) == 0
                        and int(preview.get("events_ambiguous", 0) or 0) == 0
                    )
                    run["stages"].append({
                        "name":"the_odds_api_capture",
                        "status":"PASSED" if complete else "FAILED",
                        "timestamp":now(),
                        "staging_manifest":f"data/control/staging/{run_id}/manifest.json"
                    })
                    publish_allowed = (
                        cfg.get("automatic_publication_enabled", False)
                        or cfg.get("publication_policy", {}).get("odds", False)
                    )
                    if not args.confirm_publish:
                        run["status"]="COMPLETED"
                        run["warnings"].append("preview completed; acceptance/publication not requested")
                    elif not cfg.get("acceptance_enabled", False):
                        run["status"]="BLOCKED_BY_CONFIGURATION"
                        run["errors"].append("odds acceptance is disabled")
                    elif not publish_allowed:
                        run["status"]="BLOCKED_BY_CONFIGURATION"
                        run["errors"].append("odds publication policy is disabled")
                    elif not complete:
                        run["status"]="FAILED"
                        run["errors"].append("The Odds API coverage validation failed; no acceptance or publication")
                    else:
                        commands = [
                            [sys.executable, "build_theodds_season_lines_2026.py",
                             "--observations", f"data/control/staging/{run_id}/quote_observations.csv",
                             "--manifest", f"data/control/staging/{run_id}/manifest.json",
                             "--raw", f"data/control/raw/the_odds_api/{run_id}/response.json",
                             "--quotes-out", "data/odds/theodds_ncaaf_lines_2026.csv",
                             "--display-out", "data/odds/theodds_season_game_lines_2026.csv",
                             "--coverage-out", "data/audits/theodds_ncaaf_current_pull_audit.json",
                             "--exclusions-out", "data/audits/theodds_exclusions.csv"],
                            [sys.executable, "scripts/control/accept_theodds_staged.py",
                             "--stage-dir", f"data/control/staging/{run_id}",
                             "--display", "data/odds/theodds_season_game_lines_2026.csv",
                             "--coverage", "data/audits/theodds_ncaaf_current_pull_audit.json"],
                            [sys.executable, "scripts/odds/append_game_line_history.py"],
                            [sys.executable, "scripts/odds/append_game_line_history.py",
                             "--accepted-quotes", "data/odds/theodds_ncaaf_lines_2026.csv"],
                            [sys.executable, "scripts/odds/build_game_line_movement_report.py"],
                            [sys.executable, "scripts/site/build_matchups_view.py"],
                            [sys.executable, "scripts/history/build_matchup_line_history_clean.py"],
                            [sys.executable, "scripts/site/inject_matchup_line_history.py", "--asset-only"],
                            [sys.executable, "scripts/site/build_odds_screen_v2.py"],
                            [sys.executable, "scripts/site/build_schedule_live_enrichment.py"],
                        ]
                        failed = False
                        for command in commands:
                            result = shell(command)
                            name = Path(command[1]).name if len(command) > 1 else command[0]
                            run["stages"].append({"name":name,"status":"PASSED" if result["returncode"]==0 else "FAILED",**result})
                            if result["returncode"] != 0:
                                failed = True
                                run["errors"].append(f"{name} failed")
                                break
                        if not failed:
                            pub = shell(["bash", "scripts/publish/publish_site.sh", "--push"])
                            run["publication"] = {
                                "status": "COMPLETED" if pub["returncode"] == 0 else "FAILED",
                                **pub,
                            }
                            run["stages"].append({
                                "name": "canonical_publish",
                                "status": "PASSED" if pub["returncode"] == 0 else "FAILED",
                                **pub,
                            })
                            run["status"] = "COMPLETED" if pub["returncode"] == 0 else "FAILED"
                            if pub["returncode"] != 0:
                                run["errors"].append("website publication failed")
                                print(pub.get("output_tail", ""), file=sys.stderr)
                        else:
                            run["status"] = "FAILED"
            elif args.mode == "ratings":
                execute_ratings_service(run, cfg, args.confirm_publish)

            elif args.mode == "pregame":
                publish_allowed = (
                    cfg.get("automatic_publication_enabled", False)
                    or cfg.get("publication_policy", {}).get("pregame", False)
                )

                if not args.confirm_publish:
                    run["status"] = "BLOCKED_BY_CONFIGURATION"
                    run["errors"].append("pregame requires --confirm-publish")
                elif not publish_allowed:
                    run["status"] = "BLOCKED_BY_CONFIGURATION"
                    run["errors"].append("pregame publication policy is disabled")
                else:
                    commands = [
                        # 1. Refresh the three automated Sunday rating sources.
                        [sys.executable, "scripts/ratings/test_rating_sources.py",
                         "--sources", "spplus,fpi,teamrankings"],
                        [sys.executable, "scripts/ratings/parse_rating_source_tables.py"],
                        [sys.executable, "scripts/ratings/accept_live_rating_candidates_with_status.py"],

                        # 2. Rebuild canonical ratings and preserve movement history.
                        [sys.executable, "scripts/ratings/build_all_ratings_latest.py"],
                        [sys.executable, "scripts/ratings/build_active_2026_ratings_master.py"],
                        [sys.executable, "scripts/ratings/merge_live_rating_change_status.py"],
                        [sys.executable, "ratings/append_ratings_history.py"],
                        [sys.executable, "ratings/build_ratings_movement.py"],

                        # 3. Canonical projection owners used by the validated
                        #    full daily pipeline. No season/CFP simulations here.
                        [sys.executable, "scripts/projections/build_game_projection_sources_2026.py"],
                        [sys.executable, "scripts/projections/build_current_game_projection_contract.py"],
                        [sys.executable, "scripts/projections/build_game_projection_blend_2026.py"],
                        [sys.executable, "scripts/projections/apply_game_projection_blend_to_preseason_db.py"],

                        # 4. Rebuild current matchup/line/Shadow assets using
                        #    already-available postgame state.
                        [sys.executable, "scripts/site/build_matchups_view.py"],
                        [sys.executable, "scripts/history/build_matchup_line_history_clean.py"],
                        [sys.executable, "scripts/site/inject_matchup_line_history.py", "--asset-only"],
                        [sys.executable, "scripts/postgame/build_shadow_team_game_features_2026.py"],
                        [sys.executable, "scripts/site/build_saturday_shadow_component_predictions.py"],
                        [sys.executable, "scripts/projections/build_current_game_projection_contract.py"],
                        [sys.executable, "scripts/site/build_matchups_view.py"],
                        [sys.executable, "scripts/site/build_saturday_shadow_lines.py"],
                        [sys.executable, "scripts/audit/validate_projection_resolver.py"],
                        [sys.executable, "scripts/site/build_schedule_live_enrichment.py"],

                        # 5. Current Ratings / Odds-facing payloads.
                        [sys.executable, "scripts/site/build_ratings_view.py"],
                        [sys.executable, "scripts/markets/build_current_market_contract.py"],
                        [sys.executable, "scripts/site/build_odds_screen_v2.py"],
                        [sys.executable, "scripts/markets/apply_current_market_to_odds_screen.py"],
                        [sys.executable, "scripts/markets/apply_current_market_to_matchups.py"],

                        # 6. Freeze the refreshed pregame model state.
                        [sys.executable, "scripts/model_tracking/capture_model_tracking.py",
                         "--accept"],
                        [sys.executable, "scripts/model_tracking/settle_model_tracking.py",
                         "--accept"],
                        [sys.executable, "scripts/model_tracking/build_model_performance_view.py"],

                        # 7. Canonical public build and validation.
                        [sys.executable, "scripts/site/build_public_site.py"],
                        [sys.executable, "scripts/site/build_war_room_home.py"],
                        [sys.executable, "scripts/site/inject_market_presentation_fixes.py"],
                        [sys.executable, "scripts/site/compact_matchups_payload.py"],
                        [sys.executable, "scripts/site/apply_shared_war_room_shell.py"],
                        [sys.executable, "scripts/publish/check_public_site.py"],
                    ]

                    failed = False
                    for command in commands:
                        result = shell(command)
                        name = Path(command[1]).name if len(command) > 1 else command[0]
                        run["stages"].append({
                            "name": name,
                            "status": "PASSED" if result["returncode"] == 0 else "FAILED",
                            **result,
                        })
                        if result["returncode"] != 0:
                            failed = True
                            run["errors"].append(f"{name} failed")
                            print(result.get("output_tail", ""), file=sys.stderr)
                            break

                    if not failed:
                        pub = shell(["bash", "scripts/publish/publish_site.sh", "--push"])
                        run["publication"] = {
                            "status": "COMPLETED" if pub["returncode"] == 0 else "FAILED",
                            **pub,
                        }
                        run["stages"].append({
                            "name": "canonical_publish",
                            "status": "PASSED" if pub["returncode"] == 0 else "FAILED",
                            **pub,
                        })
                        run["status"] = (
                            "COMPLETED" if pub["returncode"] == 0 else "FAILED"
                        )
                        if pub["returncode"] != 0:
                            run["errors"].append("website publication failed")
                            print(pub.get("output_tail", ""), file=sys.stderr)
                    else:
                        run["status"] = "FAILED"

            elif args.mode == "postgame":
                execute_postgame_service(run)
            elif not cfg.get("live_provider_calls_enabled", False) and args.mode != "publish-existing":
                run["status"] = "BLOCKED_BY_CONFIGURATION"; run["errors"].append("live provider calls are disabled pending activation review")
            elif args.mode == "publish-existing":
                publication_allowed = (
                    cfg.get("automatic_publication_enabled", False)
                    or cfg.get("publication_policy", {}).get(args.mode, False)
                )

                if args.confirm_publish and publication_allowed:
                    pub = shell(["bash", "scripts/publish/publish_site.sh", "--push"])
                    run["publication"] = {
                        "status": "COMPLETED" if pub["returncode"] == 0 else "FAILED",
                        **pub,
                    }
                    run["stages"].append({
                        "name": "canonical_publish",
                        "status": "PASSED" if pub["returncode"] == 0 else "FAILED",
                        **pub,
                    })
                    run["status"] = "COMPLETED" if pub["returncode"] == 0 else "FAILED"
                    if pub["returncode"]:
                        run["errors"].append("website publication failed")
                        print(pub.get("output_tail", ""), file=sys.stderr)
                else:
                    check = shell(["bash", "scripts/publish/publish_site.sh", "--check"])
                    run["stages"].append({
                        "name": "canonical_publish_check",
                        "status": "PASSED" if check["returncode"] == 0 else "FAILED",
                        **check,
                    })
                    if check["returncode"]:
                        run["status"] = "FAILED"
                        run["errors"].append("canonical publish check failed")
                        print(check.get("output_tail", ""), file=sys.stderr)
                    else:
                        run["status"] = "COMPLETED_WITH_WARNINGS"
                        run["warnings"].append(
                            "validation passed; publication not enabled/confirmed"
                        )
            else:
                run["status"]="BLOCKED_BY_CONFIGURATION"; run["errors"].append("live adapters intentionally disabled")

        after = hashes(WATCHED_OUTPUTS); run["files_changed"]=[p for p in WATCHED_OUTPUTS if before[p] != after[p]]
        run["validation_results"]["v2_shell_hashes_unchanged"] = shell_before == hashes(V2_SHELLS)
        if not run["validation_results"]["v2_shell_hashes_unchanged"]:
            run["status"]="FAILED"; run["errors"].append("canonical V2 shell changed")
    except RuntimeError as exc:
        run["status"]="BLOCKED_BY_OVERLAP"; run["errors"].append(str(exc))
    except Exception as exc:
        run["status"]="FAILED"; run["errors"].append(safe_text(f"{type(exc).__name__}: {exc}"))
    finally:
        release_lock(run_id)
        if args.test_scenario == "overlap" and LOCK.exists() and (load_json(LOCK,{}) or {}).get("run_id") == "test-overlap": LOCK.unlink()
        run["completion_timestamp"]=now(); run["deployed_commit_after"]=deployed_commit(); run["stage"]="complete"
        write_records(run,cfg); print(json.dumps(run,indent=2))
    return 0 if run["status"] in {"COMPLETED","COMPLETED_WITH_WARNINGS","NO_CHANGES"} else 2


if __name__ == "__main__": raise SystemExit(main())
