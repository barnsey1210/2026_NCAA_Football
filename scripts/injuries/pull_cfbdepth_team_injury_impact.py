#!/usr/bin/env python3
"""Acquire and normalize the official CFBDepth team Injury Impact export."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.site.team_identity import canonical_team_key, canonical_team_name


SOURCE_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1lwL8MNI3FHf5lkLCYNmKCQeixWDfpADzYRuzyz1ir6c/"
    "export?format=csv&gid=2049577672"
)
DEFAULT_OUTPUT = ROOT / "data/canonical/cfbdepth_team_injury_impact_current.json"
DEFAULT_AUDIT = ROOT / "data/audits/cfbdepth_team_injury_impact_audit.json"
RAW_HISTORY_ROOT = ROOT / "data/raw/cfbdepth"
REQUIRED_COLUMNS = {
    "School",
    "Conference",
    "Injury Number",
    "Injury New",
    "Injury Impact",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def number(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return int(parsed) if parsed.is_integer() else parsed


def acquire(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "NCAAF-War-Room/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def normalize(raw_bytes: bytes, pulled_at: str, source_updated_at: str | None = None):
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    missing_columns = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
    if missing_columns:
        raise ValueError(f"CFBDepth injury export missing columns: {missing_columns}")

    normalized = []
    unresolved = []
    for source_row in reader:
        source_team = str(source_row.get("School") or "").strip()
        team = canonical_team_name(source_team)
        if not team:
            unresolved.append(source_team)
            continue
        impact = number(source_row.get("Injury Impact"))
        if impact is None:
            raise ValueError(f"CFBDepth injury impact missing/non-numeric for {source_team}")
        normalized.append(
            {
                "team": team,
                "canonical_team_key": canonical_team_key(team),
                "source_team": source_team,
                "conference": str(source_row.get("Conference") or "").strip() or None,
                "injury_impact_score": impact,
                "injury_number": number(source_row.get("Injury Number")),
                "injury_new": number(source_row.get("Injury New")),
                "source_updated_at": source_updated_at,
                "pulled_at": pulled_at,
                "source": "CFBDepth Injury Impact Report",
                "status": "AVAILABLE_SOURCE_TIME_UNVERIFIED" if not source_updated_at else "AVAILABLE",
            }
        )

    duplicates = sorted(
        team
        for team in {row["team"] for row in normalized}
        if sum(row["team"] == team for row in normalized) > 1
    )
    if unresolved or duplicates:
        raise ValueError(
            f"CFBDepth injury identity failure: unresolved={sorted(set(unresolved))}, "
            f"duplicates={duplicates}"
        )

    # Full ordinal ranking is deterministic even when impact scores tie:
    # healthier/lower impact first, canonical team name as the fixed tie-break.
    normalized.sort(key=lambda row: (row["injury_impact_score"], row["team"]))
    for rank, row in enumerate(normalized, start=1):
        row["injury_impact_rank"] = rank

    return normalized


def parse_timestamp(value: str):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_weekly_baseline(pulled_at: str):
    current = parse_timestamp(pulled_at)
    if current is None:
        return {}, {
            "status": "UNAVAILABLE",
            "reason": "INVALID_CURRENT_TIMESTAMP",
            "baseline_date": None,
            "days": None,
        }

    for days in (7, 6, 8):
        baseline_date = (current - timedelta(days=days)).date().isoformat()
        directory = RAW_HISTORY_ROOT / baseline_date
        candidates = sorted(
            directory.glob("cfbdepth-injury_*.csv"),
            reverse=True,
        )

        for candidate in candidates:
            try:
                baseline_rows = normalize(
                    candidate.read_bytes(),
                    baseline_date + "T00:00:00Z",
                )
            except (OSError, UnicodeDecodeError, ValueError):
                continue

            if len(baseline_rows) != 138:
                continue

            return (
                {
                    row["canonical_team_key"]: row
                    for row in baseline_rows
                },
                {
                    "status": "AVAILABLE",
                    "baseline_date": baseline_date,
                    "days": days,
                    "source_file": str(candidate),
                },
            )

    return {}, {
        "status": "UNAVAILABLE",
        "reason": "NO_VALID_6_TO_8_DAY_BASELINE",
        "baseline_date": None,
        "days": None,
    }


def apply_weekly_trend(rows, pulled_at: str):
    baseline, metadata = load_weekly_baseline(pulled_at)

    for row in rows:
        prior = baseline.get(row["canonical_team_key"])

        if prior is None:
            row["weekly_prior_rank"] = None
            row["weekly_prior_score"] = None
            row["weekly_impact_delta"] = None
            row["weekly_direction"] = "UNAVAILABLE"
            row["weekly_baseline_date"] = metadata.get("baseline_date")
            row["weekly_days"] = metadata.get("days")
            continue

        current_score = number(row.get("injury_impact_score"))
        prior_score = number(prior.get("injury_impact_score"))

        if current_score is None or prior_score is None:
            delta = None
            direction = "UNAVAILABLE"
        else:
            delta = round(float(current_score) - float(prior_score), 1)
            if delta >= 0.5:
                direction = "WORSE"
            elif delta <= -0.5:
                direction = "BETTER"
            else:
                direction = "FLAT"

        row["weekly_prior_rank"] = prior.get("injury_impact_rank")
        row["weekly_prior_score"] = prior_score
        row["weekly_impact_delta"] = delta
        row["weekly_direction"] = direction
        row["weekly_baseline_date"] = metadata.get("baseline_date")
        row["weekly_days"] = metadata.get("days")

    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Use an existing official CSV without network access")
    parser.add_argument("--url", default=SOURCE_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--raw-output", type=Path)
    parser.add_argument("--pulled-at")
    parser.add_argument("--source-updated-at")
    args = parser.parse_args()

    pulled_at = args.pulled_at or utc_now()

    if args.input:
        raw_bytes = args.input.read_bytes()
        rows = normalize(raw_bytes, pulled_at, args.source_updated_at)
    else:
        last_error = None
        for attempt in range(2):
            raw_bytes = acquire(args.url)
            try:
                rows = normalize(raw_bytes, pulled_at, args.source_updated_at)
                break
            except ValueError as exc:
                last_error = exc
                if attempt == 0:
                    print(
                        f"CFBDepth validation failed on first acquisition; "
                        f"retrying once: {exc}",
                        file=sys.stderr,
                    )
                    time.sleep(3)
                    continue
                raise
        else:
            raise last_error

    output = args.output.resolve()
    audit_path = args.audit.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    raw_output = args.raw_output
    if raw_output is None and args.input is None:
        stamp = pulled_at.replace("-", "").replace(":", "")[:15]
        day = pulled_at[:10]
        raw_output = ROOT / "data/raw/cfbdepth" / day / f"cfbdepth-injury_{stamp}.csv"
    if raw_output:
        raw_output.resolve().parent.mkdir(parents=True, exist_ok=True)
        raw_output.resolve().write_bytes(raw_bytes)

    weekly_trend = apply_weekly_trend(rows, pulled_at)

    payload = {
        "schema_version": "cfbdepth-team-injury-impact-v2",
        "source": "CFBDepth Injury Impact Report",
        "source_url": args.url,
        "source_updated_at": args.source_updated_at,
        "pulled_at": pulled_at,
        "status": "AVAILABLE_SOURCE_TIME_UNVERIFIED" if not args.source_updated_at else "AVAILABLE",
        "coverage": {
            "team_count": len(rows),
            "expected_team_count": 138,
            "full_coverage": len(rows) == 138,
        },
        "ranking": {
            "direction": "ascending_injury_impact",
            "rank_1": "lowest injury impact / healthiest",
            "tie_break": "canonical team name ascending",
        },
        "weekly_trend": weekly_trend,
        "teams": rows,
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    audit = {
        "schema_version": "cfbdepth-team-injury-impact-audit-v1",
        "built_at": utc_now(),
        "source_url": args.url,
        "source_updated_at": args.source_updated_at,
        "pulled_at": pulled_at,
        "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "rows": len(rows),
        "canonical_teams": len({row["team"] for row in rows}),
        "full_coverage": len(rows) == 138,
        "warnings": [] if len(rows) == 138 else [f"Expected 138 teams; found {len(rows)}"],
        "output": str(output),
        "raw_output": str(raw_output.resolve()) if raw_output else None,
        "weekly_trend": weekly_trend,
    }
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(f"CFBDepth injury impact normalized: {len(rows)} teams -> {output}")


if __name__ == "__main__":
    main()
