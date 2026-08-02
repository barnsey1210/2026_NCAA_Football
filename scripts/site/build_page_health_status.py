#!/usr/bin/env python3
"""Build centralized, page-specific V2 data-health status artifacts."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "config/page_health_registry.json"
VALID = {"green", "yellow", "red", "gray"}


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except ValueError:
        try:
            return datetime.fromisoformat(text[:10]).replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


class Context:
    def __init__(self, root: Path, now: datetime, shared: dict[str, Any] | None = None):
        self.root, self.now, self.cache, self.shared = root, now, {}, shared or {}

    def load(self, rel: str) -> Any:
        if rel not in self.cache:
            path = self.root / rel
            if not path.is_file():
                self.cache[rel] = None
            else:
                try:
                    self.cache[rel] = json.loads(path.read_text())
                except (json.JSONDecodeError, OSError):
                    self.cache[rel] = False
        return self.cache[rel]

    def timestamp(self, rel: str, data: Any = None) -> datetime | None:
        data = self.load(rel) if data is None else data
        if isinstance(data, dict):
            for key in ("built_at", "generated_at", "updated_at", "snapshot_timestamp", "snapshot_date", "last_successful_pull"):
                parsed = parse_time(data.get(key))
                if parsed:
                    return parsed
        path = self.root / rel
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) if path.is_file() else None


def metric(label: str, value: Any, detail: str = "") -> dict[str, Any]:
    return {"label": label, "value": "—" if value is None else value, "detail": detail}


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    try:
        with path.open(newline="", errors="replace") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def matchup_data(c: Context) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    data = c.load("data/site/matchups_view.json")
    return (data, data.get("games", []), data.get("audit_summary", {})) if isinstance(data, dict) else ({}, [], {})


def injury_health(c: Context) -> dict[str, Any]:
    """Classify source availability without treating unreleased reports as failure."""
    cfg = c.shared.get("injuries", {})
    raw_paths = [c.root / rel for rel in cfg.get("raw_artifacts", [])]
    normalized_path = c.root / cfg.get("normalized_artifact", "data/injuries/injury_events_normalized.csv")
    alerts_path = c.root / cfg.get("alerts_artifact", "data/injuries/injury_alerts.csv")
    raw_rows = [row for path in raw_paths for row in csv_rows(path)]
    normalized = csv_rows(normalized_path)
    alerts = csv_rows(alerts_path)
    error_tokens = ("error", "failed", "fetch_error")
    source_failed = any(any(token in str(value).lower() for token in error_tokens) for row in raw_rows for value in row.values())
    existing = [path for path in [*raw_paths, normalized_path, alerts_path] if path.is_file()]
    latest = max((datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) for path in existing), default=None)
    age = (c.now - latest).total_seconds() / 3600 if latest else None
    if source_failed or (raw_rows and not normalized_path.is_file()):
        state, label = "source_failed", "RED · Source failed"
    elif not raw_rows and not normalized and not alerts:
        state, label = "not_released", "GRAY · No reports released"
    elif alerts and age is not None and age > cfg.get("stale_hours", 96):
        state, label = "active_stale", "RED · Active reports stale"
    elif latest and age is not None and age > cfg.get("fresh_hours", 36):
        state, label = "active_aging", "YELLOW · Reports aging"
    elif alerts:
        state, label = "active", f"{len(alerts)} active alerts"
    else:
        state, label = "no_injuries", "No injuries found"
    return {"state": state, "label": label, "alerts": len(alerts), "age_hours": age}


def explicitly_inactive(data: Any) -> bool:
    """Only explicit source/domain state may make an otherwise valid page GRAY."""
    if not isinstance(data, dict):
        return False
    state = str(data.get("status") or data.get("state") or data.get("availability") or "").lower().replace(" ", "_")
    has_data = bool(data.get("teams") or data.get("games") or data.get("trials"))
    return not has_data and state in {"inactive", "not_released", "not_open", "unavailable"}


def odds_counts(data: dict[str, Any]) -> dict[str, int]:
    out = {"spread": 0, "total": 0, "moneyline": 0, "fallback": 0, "unavailable": 0, "stale": 0}
    for game in data.get("games", []):
        seen = {key: False for key in ("spread", "total", "moneyline")}
        for quote in game.get("quotes", {}).values():
            for market in seen:
                if quote.get(market):
                    seen[market] = True
        for market, present in seen.items():
            out[market] += int(present)
        out["unavailable"] += int(not any(seen.values()))
        out["fallback"] += sum("fallback" in str(note).lower() for note in game.get("data_quality_notes", []))
    return out


def latest_market_time(data: dict[str, Any]) -> datetime | None:
    qa = data.get("market_qa", {}) if isinstance(data, dict) else {}
    return parse_time(qa.get("last_successful_pull")) or parse_time(data.get("market_freshness"))


def latest_completed_run(c: Context) -> dict[str, Any] | None:
    run = c.load("data/control/daily_run_status.json")
    if isinstance(run, dict) and run.get("overall_result") in {"PASSED", "PASSED_WITH_WARNINGS"} and run.get("finished_at_utc"):
        return run
    return None


def evaluate(page_id: str, cfg: dict[str, Any], c: Context) -> dict[str, Any]:
    metrics: list[dict[str, Any]] = []
    warnings: list[str] = []
    failures: list[str] = []
    unavailable: list[str] = []
    page_specific_freshness = False
    timestamps: list[datetime] = []
    sources = list(cfg.get("critical_artifacts", []))
    for rel in sources:
        value = c.load(rel)
        if value is None:
            failures.append(f"Missing critical artifact: {rel}")
        elif value is False:
            failures.append(f"Malformed critical artifact: {rel}")
        else:
            stamp = c.timestamp(rel, value)
            if stamp:
                timestamps.append(stamp)

    matchups, games, audit = matchup_data(c)
    latest_success = max(timestamps) if timestamps else None
    artifact_built = latest_success
    injuries = injury_health(c) if page_id in {"dashboard", "matchups", "schedule"} else None

    if page_id == "dashboard":
        bets = c.load("data/site/betting_activity_view.json") or {}
        moves = csv_rows(c.root / "data/history/game_line_model_history.csv")
        signals = csv_rows(c.root / "data/agents/daily_betting_angles.csv")
        run = c.load("data/control/daily_run_status.json")
        run_label, run_value = "Last completed run", "Unavailable"
        if isinstance(run, dict) and run.get("overall_result") == "RUNNING":
            run_label = "Current run at build"
            run_value = f"RUNNING · {run.get('started_at_utc') or 'start unavailable'}"
        elif isinstance(run, dict) and run.get("finished_at_utc"):
            run_value = f"{run.get('overall_result', 'COMPLETED')} · {run['finished_at_utc']}"
        metrics = [metric("Slate games", len(games)), metric("Betting signals", len(signals)), metric("Market history", len(moves)), metric("Injuries", injuries["label"]), metric("Open wagers", bets.get("summary", {}).get("owned_open", 0)), metric(run_label, run_value)]
        if not isinstance(run, dict): warnings.append("Last completed daily-run status is unavailable; page data remains independently usable.")
    elif page_id == "ratings":
        data = c.load("data/site/ratings_view.json") or {}
        ratings_time = c.timestamp("data/site/ratings_view.json", data)
        if ratings_time: latest_success = ratings_time
        teams = data.get("teams", [])
        rated = sum(t.get("rating") is not None for t in teams)
        source_counts = {s: sum((t.get("sources", {}).get(s) or {}).get("rating") is not None for t in teams) for s in ("spplus", "fpi", "teamrankings", "bradpowers")}
        expected = cfg.get("expected_teams", 138)
        market = sum((t.get("market") or {}).get("rating") is not None for t in teams)
        matchup_teams = {}
        for game in games:
            for side in ("away", "home"):
                team = game.get("teams", {}).get(side, {})
                if team.get("team"):
                    matchup_teams[team["team"]] = team
        offense = sum(t.get("offense_rank") is not None for t in matchup_teams.values())
        defense = sum(t.get("defense_rank") is not None for t in matchup_teams.values())
        movement = len(csv_rows(c.root / "data/ratings/ratings_movement.csv"))
        variance = sum(t.get("variance") is not None for t in teams)
        metrics = [metric("Composite", f"{rated}/{expected}"), metric("Rating sources", f"SP+ {source_counts['spplus']} · FPI {source_counts['fpi']} · TR {source_counts['teamrankings']} · BP {source_counts['bradpowers']}"), metric("Market-derived", f"{market}/{expected}", "Separate from composite"), metric("Off / Def", f"{offense}/{expected} · {defense}/{expected}"), metric("Movement", movement), metric("Variance", f"{variance}/{expected}")]
        if rated < cfg.get("expected_teams", 138): failures.append("Composite ratings coverage is below the expected FBS inventory.")
        if min(source_counts.values(), default=0) < cfg.get("expected_teams", 138): warnings.append("At least one ratings source has partial team coverage.")
        if market == 0: failures.append("Market-Derived Ratings are missing; they remain separate from the composite.")
        elif market < expected: warnings.append("Market-Derived Ratings have partial team coverage; they remain separate from the composite.")
        if offense == 0 or defense == 0: failures.append("Offensive or Defensive Ratings are missing.")
        elif offense < expected or defense < expected: warnings.append("Offensive or Defensive Ratings have partial team coverage.")
        if movement == 0: failures.append("Ratings Movement is missing.")
        if variance == 0: failures.append("Ratings Variance is missing.")
        elif variance < expected: warnings.append("Ratings Variance has partial team coverage.")
    elif page_id == "openers":
        odds = c.load("data/site/odds_screen_v2.json") or {}; og = odds.get("games", [])
        spread = sum(bool(g.get("opener", {}).get("spread", {}).get("away")) for g in og)
        total = sum(bool(g.get("opener", {}).get("total", {}).get("over")) for g in og)
        history = sum(bool(g.get("history", {}).get("spread") or g.get("history", {}).get("total")) for g in og)
        unmatched = sum(not g.get("game_id") or any("no exact" in str(n).lower() for n in g.get("data_quality_notes", [])) for g in og)
        quote_times = [parse_time(g.get("source_updated_at")) for g in og]; quote_times = [x for x in quote_times if x]
        if quote_times: latest_success = max(quote_times)
        metrics = [metric("Games", len(og)), metric("Spread openers", spread), metric("Total openers", total), metric("History", history), metric("Unmatched", unmatched), metric("Market updated", latest_success.isoformat() if latest_success else None)]
        if og and (spread < len(og) or total < len(og)): warnings.append("Some games do not yet have both retained spread and total openers.")
        if og and history < len(og): warnings.append("Retained opener history is partial for market-covered games.")
        if unmatched: warnings.append(f"{unmatched} opener games lack an exact canonical mapping.")
    elif page_id == "matchups":
        metrics = [metric("Matchups", audit.get("games", len(games))), metric("Model coverage", f"{audit.get('model_spread', 0)} S · {audit.get('model_total', 0)} T"), metric("Five Factors", audit.get("five_factors_complete")), metric("Coaching", audit.get("coach_full_both_teams")), metric("Odds", audit.get("market_spread")), metric("Injuries", injuries["label"])]
        if audit.get("games", len(games)) and not audit.get("model_spread"): failures.append("Model spread coverage is missing.")
        if audit.get("five_factors_complete", 0) < len(games): warnings.append("Advanced matchup coverage is partial for the current inventory.")
    elif page_id == "odds":
        data = c.load("data/site/odds_screen_v2.json") or {}; counts = odds_counts(data); total_games = len(data.get("games", []))
        quote_times = [parse_time(g.get("source_updated_at")) for g in data.get("games", [])]; quote_times = [x for x in quote_times if x]
        quote_latest = max(quote_times) if quote_times else None
        if quote_latest: latest_success = quote_latest
        metrics = [metric("Games", total_games), metric("Spreads", counts["spread"]), metric("Totals", counts["total"]), metric("Moneylines", counts["moneyline"]), metric("Books", len(data.get("books", []))), metric("Unavailable", counts["unavailable"])]
        if total_games and counts["spread"] < total_games: warnings.append("Spread coverage is partial.")
        mapping_failures = sum(any("no exact" in str(note).lower() for note in game.get("data_quality_notes", [])) for game in data.get("games", []))
        malformed = sum(any("malformed" in str(note).lower() for note in game.get("data_quality_notes", [])) for game in data.get("games", []))
        if mapping_failures: failures.append(f"{mapping_failures} current odds games failed exact canonical mapping.")
        if malformed: failures.append(f"{malformed} current odds games contain malformed market pairs.")
        if quote_latest and (c.now-quote_latest).total_seconds()/3600 > cfg["stale_hours"]: failures.append("Current odds quotes are stale beyond the maximum threshold.")
    elif page_id == "schedule":
        data = c.load("data/site/schedule_live_enrichment.json") or {}; rows = data.get("games", [])
        kickoff = sum(bool(r.get("kickoff_utc") or r.get("date")) for r in rows); projections = audit.get("model_spread", 0); odds = audit.get("market_spread", 0); results = sum(bool(r.get("home_score") is not None and r.get("away_score") is not None) for r in rows)
        ids = [r.get("game_id") for r in rows if r.get("game_id")]; duplicates = len(ids)-len(set(ids))
        metrics = [metric("Games", len(rows)), metric("Kickoffs", kickoff), metric("Projections", projections), metric("Odds", odds), metric("Results / integrity", f"{results} results · {duplicates} dupes"), metric("Injuries", injuries["label"])]
        if duplicates: failures.append(f"Schedule contains {duplicates} duplicate game IDs.")
        if rows and projections == 0: failures.append("Schedule projection coverage is missing.")
        elif rows and odds == 0: warnings.append("No current market odds are available for the schedule inventory.")
    elif page_id == "futures":
        page_specific_freshness = True
        data = c.load("data/site/futures_view.json") or {}; summary = data.get("summary", {}); qa = data.get("market_qa", {})
        books = qa.get("books", []); metrics = [metric("Teams", summary.get("teams")), metric("Win totals", summary.get("win_markets")), metric("Conference title", summary.get("title_markets")), metric("Playoff", summary.get("playoff_markets")), metric("National title", summary.get("national_title_markets")), metric("Books", len(books))]
        market_time = latest_market_time(data)
        market_age = (c.now-market_time).total_seconds()/3600 if market_time else None
        if market_time: latest_success = market_time
        expected = cfg.get("expected_teams", 138)
        coverages = [summary.get(k, 0) or 0 for k in ("win_markets", "title_markets", "playoff_markets", "national_title_markets")]
        if not any(coverages): failures.append("All critical futures market categories are missing.")
        elif min(coverages) < expected: warnings.append("Futures team-market coverage is partial or has missing teams.")
        if qa.get("invalid_prices") or qa.get("invalid_implied_probabilities"): failures.append("Futures output contains malformed current prices.")
        if qa.get("stale_prices_displayed_as_current"): failures.append("Stale futures prices are displayed as current.")
        elif market_age is None or market_age >= cfg["fresh_hours"] or str(qa.get("status", "")).lower() not in ("pass", "current", "ok"):
            warnings.extend(qa.get("warnings", []) or ["Sportsbook futures are stale or have partial provider coverage."])
    elif page_id == "conferences":
        data = c.load("data/site/conference_workspace.json") or {}; confs = data.get("conferences", []); teams = [t for conf in confs for t in conf.get("teams", [])]; names = [t.get("team") for t in teams if t.get("team")]
        conference_time = c.timestamp("data/site/conference_workspace.json", data)
        if conference_time: latest_success = conference_time
        duplicates = len(names)-len(set(names)); missing = max(0, cfg.get("expected_teams", 138)-len(set(names)))
        title_cov = sum(t.get("title_pct") is not None for t in teams); eligibility_cov = sum(t.get("make_title_game_pct") is not None and t.get("title_pct") is not None for t in teams); market_cov = sum(t.get("title_market_prob") is not None for t in teams)
        records = sum(all(t.get(k) is not None for k in ("current_wins", "current_losses")) for t in teams)
        conf_records = sum(all(t.get(k) is not None for k in ("current_conf_wins", "current_conf_losses")) for t in teams)
        metrics = [metric("Conferences", len(confs)), metric("Teams / integrity", f"{len(set(names))} · {missing} missing · {duplicates} dupes"), metric("Current records", records), metric("Conf records", conf_records), metric("Eligibility / sims", f"{eligibility_cov}/{len(teams)}"), metric("Title markets", market_cov)]
        if len(confs) < cfg.get("expected_conferences", 10) or missing or duplicates: failures.append("Conference membership coverage is incomplete or duplicated.")
        if records < len(teams) or conf_records < len(teams): failures.append("Current overall or conference records are incomplete.")
        if title_cov < len(teams) or eligibility_cov < len(teams): warnings.append("Conference simulation or eligibility coverage is partial.")
        if conference_time and (c.now-conference_time).total_seconds()/3600 > cfg["fresh_hours"]: warnings.append("Conference simulations or records are aging.")
        futures = c.load("data/site/futures_view.json") or {}; market_time = latest_market_time(futures)
        if market_cov == 0: warnings.append("Conference title market data is unavailable.")
        elif not market_time or (c.now-market_time).total_seconds()/3600 >= 24: warnings.append("Conference title market data is stale.")
    elif page_id in ("playoff", "simulations"):
        page_specific_freshness = True
        data = c.load("data/site/playoff_model_2026.json") or {}; teams = data.get("teams", []); complete = sum(t.get("playoff_pct") is not None for t in teams); title = sum(t.get("national_title_pct") is not None for t in teams)
        metrics = [metric("Simulations", data.get("trials")), metric("Teams", len(teams)), metric("Playoff coverage", complete), metric("Title coverage", title), metric("Excluded", max(0, cfg.get("expected_teams", 138)-len(teams)))]
        if page_id == "simulations":
            confs = c.load("data/site/conference_workspace.json") or {}; metrics.append(metric("Conferences", len(confs.get("conferences", []))))
            run = latest_completed_run(c)
            if not run:
                warnings.append("No latest successful daily-run record is available to verify simulation completion.")
            else:
                run_start = parse_time(run.get("started_at_utc")); sim_time = c.timestamp("data/site/playoff_model_2026.json", data)
                stage = next((s for s in run.get("stages", []) if s.get("id") in {"simulations", "simulation", "conference_simulations"}), None)
                if stage and stage.get("status") == "FAILED": failures.append("Simulation stage failed during the latest completed daily run.")
                elif not sim_time or (run_start and sim_time < run_start): warnings.append("Simulation did not complete during the latest successful daily run.")
        else:
            ratings = c.load("data/site/ratings_view.json") or {}; futures = c.load("data/site/futures_view.json") or {}
            sim_time = c.timestamp("data/site/playoff_model_2026.json", data); ratings_time = c.timestamp("data/site/ratings_view.json", ratings); market_time = latest_market_time(futures)
            market_cov = (futures.get("summary", {}).get("playoff_markets", 0) or 0)
            metrics[-1] = metric("Playoff markets", f"{market_cov}/{cfg.get('expected_teams', 138)}")
            if market_cov < cfg.get("expected_teams", 138): warnings.append("Eligible-team playoff market coverage is partial.")
            if not market_time or (c.now-market_time).total_seconds()/3600 >= 24: warnings.append("Playoff prices were not updated within 24 hours.")
            if sim_time and ratings_time and ratings_time > sim_time: warnings.append("Newer ratings inputs exist than the playoff simulation output.")
            elif sim_time and (c.now-sim_time).total_seconds()/3600 >= cfg["fresh_hours"]: warnings.append("Playoff simulation is older than the current readiness threshold.")
        if teams and complete < len(teams): warnings.append("Some teams lack playoff probability output.")
    elif page_id == "betting":
        data = c.load("data/site/betting_activity_view.json") or {}; records = data.get("records", []); signals = csv_rows(c.root / "data/agents/daily_betting_angles.csv")
        malformed = sum(r.get("price") is not None and (not isinstance(r.get("price"), (int, float)) or not math.isfinite(float(r["price"]))) for r in records)
        visible_nan = sum(any(str(v).strip().lower() == "nan" for v in r.values()) for r in signals)
        ids = [r.get("bet_id") for r in records if r.get("bet_id")]; duplicates = len(ids)-len(set(ids))
        moves = len(csv_rows(c.root / "data/history/game_line_model_history.csv"))
        metrics = [metric("Games evaluated", len(games)), metric("Active signals", len(signals)), metric("Line moves", moves), metric("Open wagers", data.get("summary", {}).get("owned_open")), metric("Duplicates", duplicates), metric("Malformed", malformed+visible_nan)]
        if malformed or visible_nan: failures.append("Betting output contains malformed prices or visible nan values.")
        if duplicates: failures.append("Betting output contains duplicate bet IDs.")

    if injuries:
        if injuries["state"] in {"source_failed", "active_stale"}:
            failures.append(f"Injury status: {injuries['label']}.")
        elif injuries["state"] == "active_aging":
            warnings.append(f"Injury status: {injuries['label']}.")
        elif injuries["state"] == "not_released":
            unavailable.append("No actionable CFBDepth injury reports have been released; injury context is inactive and does not reduce page health.")

    age_hours = (c.now-latest_success).total_seconds()/3600 if latest_success else None
    domain_inactive = page_id == "playoff" and explicitly_inactive(c.load("data/site/playoff_model_2026.json"))
    if not page_specific_freshness and age_hours is not None and age_hours > cfg["fresh_hours"] and age_hours <= cfg["stale_hours"]:
        warnings.append(f"Critical page data is aging ({age_hours:.1f} hours old).")
    if failures:
        status = "red"
    elif domain_inactive:
        status = "gray"; unavailable.append("The playoff source explicitly reports that the domain is not released or active.")
    elif age_hours is None:
        status = "red"; failures.append("No parseable critical artifact timestamp is available.")
    elif not page_specific_freshness and age_hours > cfg["stale_hours"]:
        status = "red"; failures.append("Critical page data is stale beyond the maximum threshold.")
    elif age_hours > cfg["fresh_hours"] or warnings:
        status = "yellow"
    else:
        status = "green"
    labels = {"green": "Healthy", "yellow": "Usable with warnings", "red": "Action required", "gray": "Inactive / unavailable"}
    summary = failures[0] if failures else warnings[0] if warnings else unavailable[0] if unavailable else "Critical data is current and expected coverage checks passed."
    return {"page_id": page_id, "display_name": cfg["display_name"], "status": status, "status_label": labels[status], "summary": summary, "last_success_at": latest_success.isoformat() if latest_success else None, "artifact_built_at": artifact_built.isoformat() if artifact_built else None, "age_minutes": round(age_hours*60, 1) if age_hours is not None else None, "age_hours": round(age_hours, 2) if age_hours is not None else None, "metrics": metrics[:6], "warnings": warnings, "critical_failures": failures, "unavailable_reasons": unavailable, "page_url": cfg["page_url"], "source_artifacts": sources, "legacy_status_selectors": cfg.get("legacy_status_selectors", [])}


def build(root: Path, registry_path: Path, now: datetime) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text())
    context = Context(root, now, registry.get("shared_checks"))
    pages = [evaluate(page_id, cfg, context) for page_id, cfg in registry["pages"].items()]
    if {p["status"] for p in pages} - VALID:
        raise ValueError("Invalid status generated")
    return {"schema_version": "page-health-status-v1", "built_at": now.isoformat(), "pages": pages}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--now")
    args = ap.parse_args()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc).replace(second=0, microsecond=0)
    if now is None:
        raise SystemExit("Invalid --now timestamp")
    payload = build(args.root.resolve(), args.registry.resolve(), now)
    text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    qa_json = args.root / "data/qa/page_health_status.json"
    site_json = args.root / "data/site/page_health_status.json"
    details = args.root / "data/qa/page_health_status_details.csv"
    atomic_write(qa_json, text); atomic_write(site_json, text)
    rows = []
    for page in payload["pages"]:
        for m in page["metrics"]:
            rows.append({"page_id": page["page_id"], "status": page["status"], "metric": m["label"], "value": m["value"], "detail": m["detail"], "last_success_at": page["last_success_at"], "source_artifacts": "|".join(page["source_artifacts"])})
    details.parent.mkdir(parents=True, exist_ok=True)
    tmp = details.with_name(f".{details.name}.{os.getpid()}.tmp")
    with tmp.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["page_id", "status", "metric", "value", "detail", "last_success_at", "source_artifacts"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, details)
    counts = {s: sum(p["status"] == s for p in payload["pages"]) for s in sorted(VALID)}
    print(f"Built page health for {len(payload['pages'])} pages: {counts}")


if __name__ == "__main__":
    main()
