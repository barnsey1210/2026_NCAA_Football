#!/usr/bin/env python3
"""Fail closed on stale or materially incomplete Futures market inputs.

This audit deliberately does not select prices or synthesize markets.  It
checks the normalized inputs produced by the existing provider pullers against
the canonical season-model universe and the most recent earlier history date.
The optional full-contract checkpoint preserves exact quote provenance for
future daily/weekly comparisons.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "scripts/site"
if str(SITE) not in os.sys.path:
    os.sys.path.insert(0, str(SITE))

from market_team_identity import resolve_market_team

EASTERN = ZoneInfo("America/New_York")
APPROVED_BOOKS = {"DraftKings", "FanDuel", "BetMGM", "Caesars"}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def parse_time(value):
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        result = datetime.fromisoformat(text)
    except ValueError:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def valid_price(value) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number != 0 and abs(number) <= 1_000_000


def previous_date_rows(rows: list[dict], today: str) -> tuple[str | None, list[dict]]:
    dates = sorted({str(row.get("snapshot_date") or "") for row in rows})
    dates = [value for value in dates if value and value < today]
    if not dates:
        return None, []
    prior = dates[-1]
    return prior, [row for row in rows if str(row.get("snapshot_date")) == prior]


def normalized_coverage(rows, canonical_names, price_fields):
    teams = defaultdict(set)
    unmatched = set()
    invalid = []
    duplicate_lines = defaultdict(set)

    for index, row in enumerate(rows, 2):
        team = resolve_market_team(row.get("team"), canonical_names)
        if not team:
            unmatched.add(str(row.get("team") or ""))
            continue
        book = str(row.get("book") or "").strip()
        if not book:
            continue
        teams[team].add(book)
        key = (team, book)
        if row.get("win_total") not in (None, ""):
            duplicate_lines[key].add(str(row.get("win_total")))
        for field in price_fields:
            value = row.get(field)
            if value not in (None, "") and not valid_price(value):
                invalid.append({"row": index, "team": team, "book": book,
                                "field": field, "value": value})

    ambiguous = [
        {"team": team, "book": book, "lines": sorted(lines)}
        for (team, book), lines in sorted(duplicate_lines.items())
        if len(lines) > 1
    ]
    return teams, sorted(unmatched), invalid, ambiguous


def material_drop(current: int, prior: int) -> bool:
    return prior >= 10 and current < prior - max(5, math.ceil(prior * 0.10))


def audit_csv_domain(name, current_path, history_path, canonical_names,
                     expected_teams, price_fields, today):
    rows = read_csv(current_path)
    history = read_csv(history_path)
    dates = sorted({str(row.get("snapshot_date") or "") for row in rows})
    current_rows = [row for row in rows if str(row.get("snapshot_date")) == today]
    teams, unmatched, invalid, ambiguous = normalized_coverage(
        current_rows, canonical_names, price_fields
    )
    prior_date, prior_rows = previous_date_rows(history, today)
    prior_teams, _, _, _ = normalized_coverage(
        prior_rows, canonical_names, price_fields
    )

    current_books = Counter(book for books in teams.values() for book in books)
    prior_books = Counter(book for books in prior_teams.values() for book in books)
    disappeared = sorted(
        book for book, count in prior_books.items()
        if count >= 10 and current_books.get(book, 0) == 0
    )
    dropped_books = {
        book: {"previous": count, "current": current_books.get(book, 0)}
        for book, count in prior_books.items()
        if material_drop(current_books.get(book, 0), count)
    }

    missing = sorted(set(expected_teams) - set(teams))
    errors = []
    warnings = []
    if today not in dates:
        errors.append(f"{name}: no normalized rows dated {today}")
    if unmatched:
        errors.append(f"{name}: {len(unmatched)} unmatched team labels")
    if invalid:
        errors.append(f"{name}: {len(invalid)} malformed prices")
    if missing:
        errors.append(f"{name}: {len(missing)} expected teams have no quote")
    if disappeared:
        errors.append(f"{name}: provider-wide disappearance: {', '.join(disappeared)}")
    if dropped_books:
        errors.append(f"{name}: material provider coverage drop")
    if ambiguous:
        warnings.append(
            f"{name}: {len(ambiguous)} team/book pairs expose multiple totals; "
            "the existing selector collapses these at brand level"
        )

    return {
        "domain": name,
        "status": "fail" if errors else "warn" if warnings else "pass",
        "current_date": today,
        "current_rows": len(current_rows),
        "expected_teams": len(expected_teams),
        "covered_teams": len(teams),
        "missing_teams": missing,
        "book_team_counts": dict(sorted(current_books.items())),
        "previous_snapshot_date": prior_date,
        "previous_book_team_counts": dict(sorted(prior_books.items())),
        "provider_wide_disappearances": disappeared,
        "material_book_drops": dropped_books,
        "unmatched_team_labels": unmatched,
        "invalid_prices": invalid,
        "ambiguous_team_book_lines": ambiguous,
        "errors": errors,
        "warnings": warnings,
    }


def contract_domain(contract, key, expected_teams, pulled_at, now, prior_rows=None):
    rows = contract.get(key, {}).get("rows", [])
    if key in {"make_cfp", "national_title"}:
        rows = [row for row in rows if row.get("outcome") in (None, "Yes")]
    by_team = {row.get("team"): row for row in rows if row.get("team")}
    missing = sorted(set(expected_teams) - set(by_team))
    no_executable = sorted(
        team for team, row in by_team.items()
        if not row.get("executable_book_count")
    )
    current_books = Counter(
        book for row in rows for book in row.get("executable_books", [])
    )
    prior_books = Counter(
        book for row in (prior_rows or [])
        if row.get("outcome") in (None, "Yes")
        for book in row.get("executable_books", [])
    )
    disappeared = sorted(
        book for book, count in prior_books.items()
        if count >= 10 and current_books.get(book, 0) == 0
    )
    dropped_books = {
        book: {"previous": count, "current": current_books.get(book, 0)}
        for book, count in prior_books.items()
        if material_drop(current_books.get(book, 0), count)
    }
    errors = []
    timestamp = parse_time(pulled_at)
    age_hours = ((now - timestamp).total_seconds() / 3600) if timestamp else None
    if timestamp is None or age_hours > 26:
        errors.append(f"{key}: Action Network pull is stale or unavailable")
    if missing:
        errors.append(f"{key}: {len(missing)} expected teams disappeared")
    if no_executable:
        errors.append(f"{key}: {len(no_executable)} teams lack an approved executable quote")
    if disappeared:
        errors.append(f"{key}: provider-wide disappearance: {', '.join(disappeared)}")
    if dropped_books:
        errors.append(f"{key}: material provider coverage drop")
    return {
        "domain": key,
        "status": "fail" if errors else "pass",
        "pulled_at": pulled_at,
        "age_hours": round(age_hours, 3) if age_hours is not None else None,
        "expected_teams": len(expected_teams),
        "covered_teams": len(by_team),
        "missing_teams": missing,
        "teams_without_executable_quote": no_executable,
        "book_team_counts": dict(sorted(current_books.items())),
        "previous_book_team_counts": dict(sorted(prior_books.items())),
        "provider_wide_disappearances": disappeared,
        "material_book_drops": dropped_books,
        "errors": errors,
        "warnings": [],
    }


def atomic_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=path.name + ".", suffix=".tmp",
                                     delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def capture_contract(contract_path: Path, output_dir: Path, today: str):
    raw = contract_path.read_bytes()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{today}.json.gz"
    with tempfile.NamedTemporaryFile("wb", dir=output_dir,
                                     prefix=target.name + ".", suffix=".tmp",
                                     delete=False) as handle:
        temporary = Path(handle.name)
        with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as zipped:
            zipped.write(raw)
    os.replace(temporary, target)
    return {"path": str(target), "sha256": hashlib.sha256(raw).hexdigest(),
            "uncompressed_bytes": len(raw)}


def load_prior_contract(snapshot_dir: Path, today: str):
    candidates = sorted(path for path in snapshot_dir.glob("*.json.gz") if path.stem.split(".")[0] < today)
    if not candidates:
        return None
    with gzip.open(candidates[-1], "rt", encoding="utf-8") as handle:
        return json.load(handle)


def checkpoint_offered_teams(path: Path, key: str):
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("checkpoint_date"):
            records.append(record)
    if not records:
        return []
    prior = sorted(records, key=lambda row: row["checkpoint_date"])[-1]
    field = "playoff_price" if key == "make_cfp" else "national_title_price"
    return [row.get("team") for row in prior.get("rows", []) if row.get("team") and row.get(field) is not None]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", default=os.environ.get("NCAAF_RUNTIME_ROOT", str(ROOT)))
    parser.add_argument("--phase", choices=("acquisition", "all"), default="all")
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--today")
    parser.add_argument("--audit-out")
    args = parser.parse_args()

    runtime = Path(args.runtime_root).expanduser().resolve()
    now = datetime.now(timezone.utc)
    today = args.today or now.astimezone(EASTERN).date().isoformat()
    season = json.loads((runtime / "data/site/season_simulations_2026.json").read_text())
    canonical = [row["team"] for row in season.get("teams", [])]
    conferences = {row["team"]: row.get("conference") for row in season.get("teams", [])}
    conference_teams = [team for team in canonical if conferences.get(team) != "Independent"]

    domains = [
        audit_csv_domain(
            "win_totals", runtime / "market_win_totals_import.csv",
            runtime / "market_win_totals_history.csv", canonical, canonical,
            ("over_odds", "under_odds"), today,
        ),
        audit_csv_domain(
            "conference_titles", runtime / "market_conference_futures_import.csv",
            runtime / "market_conference_futures_history.csv", canonical,
            conference_teams, ("american_odds",), today,
        ),
    ]

    capture = None
    if args.phase == "all":
        contract_path = runtime / "data/markets/current_futures_market_2026.json"
        contract = json.loads(contract_path.read_text())
        action = json.loads((runtime / "data/markets/action/action_playoff_futures_2026.json").read_text())
        pulled_at = action.get("pulled_at") if action.get("pull_succeeded") else None
        snapshot_dir = runtime / "data/markets/futures_quote_snapshots_2026"
        prior_contract = load_prior_contract(snapshot_dir, today)
        expected_by_domain = {}
        for key in ("make_cfp", "national_title"):
            expected = checkpoint_offered_teams(
                runtime / "data/markets/futures_checkpoints_2026.jsonl", key
            )
            expected_by_domain[key] = expected or canonical
        domains.extend([
            contract_domain(
                contract, "make_cfp", expected_by_domain["make_cfp"], pulled_at, now,
                (prior_contract or {}).get("make_cfp", {}).get("rows", []),
            ),
            contract_domain(
                contract, "national_title", expected_by_domain["national_title"], pulled_at, now,
                (prior_contract or {}).get("national_title", {}).get("rows", []),
            ),
        ])
        if args.capture and not any(item["status"] == "fail" for item in domains):
            capture = capture_contract(
                contract_path, runtime / "data/markets/futures_quote_snapshots_2026", today
            )

    errors = [error for item in domains for error in item["errors"]]
    warnings = [warning for item in domains for warning in item["warnings"]]
    payload = {
        "schema_version": "futures-market-reliability-audit-v1",
        "generated_at": now.isoformat(),
        "phase": args.phase,
        "status": "fail" if errors else "warn" if warnings else "pass",
        "canonical_team_count": len(canonical),
        "domains": {item["domain"]: item for item in domains},
        "quote_checkpoint": capture,
        "errors": errors,
        "warnings": warnings,
    }
    audit_path = Path(args.audit_out) if args.audit_out else runtime / "data/audits/futures_market_reliability.json"
    atomic_json(audit_path, payload)
    print(json.dumps(payload, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
