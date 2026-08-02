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
    def __init__(self, root: Path, now: datetime):
        self.root, self.now, self.cache = root, now, {}

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


def evaluate(page_id: str, cfg: dict[str, Any], c: Context) -> dict[str, Any]:
    metrics: list[dict[str, Any]] = []
    warnings: list[str] = []
    failures: list[str] = []
    unavailable: list[str] = []
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

    if page_id == "dashboard":
        bets = c.load("data/site/betting_activity_view.json") or {}
        moves = csv_rows(c.root / "data/history/game_line_model_history.csv")
        signals = csv_rows(c.root / "data/agents/daily_betting_angles.csv")
        injuries = csv_rows(c.root / "data/injuries/injury_alerts.csv")
        run = c.load("data/control/daily_run_status.json")
        metrics = [metric("Slate games", len(games)), metric("Betting signals", len(signals)), metric("Market history", len(moves)), metric("Injury alerts", len(injuries)), metric("Open wagers", bets.get("summary", {}).get("owned_open", 0))]
        if not isinstance(run, dict): warnings.append("Daily-run status is unavailable; page data remains independently usable.")
    elif page_id == "ratings":
        data = c.load("data/site/ratings_view.json") or {}
        teams = data.get("teams", [])
        rated = sum(t.get("rating") is not None for t in teams)
        source_counts = {s: sum((t.get("sources", {}).get(s) or {}).get("rating") is not None for t in teams) for s in ("spplus", "fpi", "teamrankings", "bradpowers")}
        metrics = [metric("Composite", f"{rated}/{cfg.get('expected_teams', 138)}"), metric("SP+", source_counts["spplus"]), metric("FPI", source_counts["fpi"]), metric("TeamRankings", source_counts["teamrankings"]), metric("Brad Powers", source_counts["bradpowers"]), metric("Movement rows", len(csv_rows(c.root / "data/ratings/ratings_movement.csv")))]
        if rated < cfg.get("expected_teams", 138): failures.append("Composite ratings coverage is below the expected FBS inventory.")
        if min(source_counts.values(), default=0) < cfg.get("expected_teams", 138): warnings.append("At least one ratings source has partial team coverage.")
    elif page_id == "openers":
        odds = c.load("data/site/odds_screen_v2.json") or {}; og = odds.get("games", [])
        spread = sum(bool(g.get("opener", {}).get("spread", {}).get("away")) for g in og)
        total = sum(bool(g.get("opener", {}).get("total", {}).get("over")) for g in og)
        history = sum(bool(g.get("history", {}).get("spread") or g.get("history", {}).get("total")) for g in og)
        metrics = [metric("Games", len(games)), metric("Spread openers", spread), metric("Total openers", total), metric("History", history), metric("Unmatched", max(0, len(og)-history))]
        if og and (spread < len(og) or total < len(og)): warnings.append("Some games do not yet have both retained spread and total openers.")
        if og and history < len(og): warnings.append("Retained opener history is partial for market-covered games.")
    elif page_id == "matchups":
        metrics = [metric("Matchups", audit.get("games", len(games))), metric("Model spreads", audit.get("model_spread")), metric("Model totals", audit.get("model_total")), metric("Five Factors", audit.get("five_factors_complete")), metric("Coaching", audit.get("coach_full_both_teams")), metric("Odds", audit.get("market_spread"))]
        if audit.get("games", len(games)) and not audit.get("model_spread"): failures.append("Model spread coverage is missing.")
        if audit.get("five_factors_complete", 0) < len(games): warnings.append("Advanced matchup coverage is partial for the current inventory.")
    elif page_id == "odds":
        data = c.load("data/site/odds_screen_v2.json") or {}; counts = odds_counts(data); total_games = len(data.get("games", []))
        quote_times = [parse_time(g.get("source_updated_at")) for g in data.get("games", [])]; quote_times = [x for x in quote_times if x]
        quote_latest = max(quote_times) if quote_times else None
        if quote_latest: latest_success = quote_latest
        metrics = [metric("Games", total_games), metric("Spreads", counts["spread"]), metric("Totals", counts["total"]), metric("Moneylines", counts["moneyline"]), metric("Books", len(data.get("books", []))), metric("Unavailable", counts["unavailable"])]
        if total_games and counts["spread"] < total_games: warnings.append("Spread coverage is partial.")
        if quote_latest and (c.now-quote_latest).total_seconds()/3600 > cfg["stale_hours"]: failures.append("Current odds quotes are stale beyond the maximum threshold.")
    elif page_id == "schedule":
        data = c.load("data/site/schedule_live_enrichment.json") or {}; rows = data.get("games", [])
        kickoff = sum(bool(r.get("kickoff_utc") or r.get("date")) for r in rows); projections = audit.get("model_spread", 0); odds = audit.get("market_spread", 0); results = sum(bool(r.get("home_score") is not None and r.get("away_score") is not None) for r in rows)
        ids = [r.get("game_id") for r in rows if r.get("game_id")]; duplicates = len(ids)-len(set(ids))
        metrics = [metric("Games", len(rows)), metric("Kickoffs", kickoff), metric("Projections", projections), metric("Odds", odds), metric("Results", results), metric("Duplicates", duplicates)]
        if duplicates: failures.append(f"Schedule contains {duplicates} duplicate game IDs.")
        if rows and projections == 0: failures.append("Schedule projection coverage is missing.")
        elif rows and odds == 0: warnings.append("No current market odds are available for the schedule inventory.")
    elif page_id == "futures":
        data = c.load("data/site/futures_view.json") or {}; summary = data.get("summary", {}); qa = data.get("market_qa", {})
        books = qa.get("books", []); metrics = [metric("Teams", summary.get("teams")), metric("Win totals", summary.get("win_markets")), metric("Conference title", summary.get("title_markets")), metric("Playoff", summary.get("playoff_markets")), metric("National title", summary.get("national_title_markets")), metric("Books", len(books))]
        if str(qa.get("status", "")).lower() not in ("pass", "current", "ok"): warnings.extend(qa.get("warnings", []) or ["Futures market QA is not fully current."])
    elif page_id == "conferences":
        data = c.load("data/site/conference_workspace.json") or {}; confs = data.get("conferences", []); teams = [t for conf in confs for t in conf.get("teams", [])]; names = [t.get("team") for t in teams if t.get("team")]
        duplicates = len(names)-len(set(names)); missing = max(0, cfg.get("expected_teams", 138)-len(set(names)))
        title_cov = sum(t.get("title_pct") is not None for t in teams); market_cov = sum(t.get("title_market_prob") is not None for t in teams)
        metrics = [metric("Conferences", len(confs)), metric("Teams assigned", len(set(names))), metric("Missing", missing), metric("Duplicates", duplicates), metric("Title sims", title_cov), metric("Title markets", market_cov)]
        if len(confs) < cfg.get("expected_conferences", 10) or missing or duplicates: failures.append("Conference membership coverage is incomplete or duplicated.")
    elif page_id in ("playoff", "simulations"):
        data = c.load("data/site/playoff_model_2026.json") or {}; teams = data.get("teams", []); complete = sum(t.get("playoff_pct") is not None for t in teams); title = sum(t.get("national_title_pct") is not None for t in teams)
        metrics = [metric("Simulations", data.get("trials")), metric("Teams", len(teams)), metric("Playoff coverage", complete), metric("Title coverage", title), metric("Excluded", max(0, cfg.get("expected_teams", 138)-len(teams)))]
        if page_id == "simulations":
            confs = c.load("data/site/conference_workspace.json") or {}; metrics.append(metric("Conferences", len(confs.get("conferences", []))))
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

    age_hours = (c.now-latest_success).total_seconds()/3600 if latest_success else None
    inactive = parse_time(cfg.get("inactive_before"))
    if age_hours is not None and age_hours > cfg["fresh_hours"] and age_hours <= cfg["stale_hours"]:
        warnings.append(f"Critical page data is aging ({age_hours:.1f} hours old).")
    if failures:
        status = "red"
    elif inactive and c.now < inactive:
        status = "gray"; unavailable.append(f"Legitimately inactive before {inactive.date().isoformat()}.")
    elif age_hours is None:
        status = "red"; failures.append("No parseable critical artifact timestamp is available.")
    elif age_hours > cfg["stale_hours"]:
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
    context = Context(root, now)
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
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
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
