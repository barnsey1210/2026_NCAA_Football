#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import subprocess
import sys

import pandas as pd


ROOT = Path(".")
RATINGS = ROOT / "data/ratings"
STATE = RATINGS / "live_rating_change_status.json"
ACCEPT_SCRIPT = ROOT / "scripts/ratings/accept_live_rating_candidates.py"

SPECS = {
    "SP+": {
        "candidate": RATINGS / "spplus_2026_candidate.csv",
        "accepted": RATINGS / "spplus_2026_from_espn_latest.csv",
        "value_columns": ["spplus", "spplus_off", "spplus_def"],
    },
    "FPI": {
        "candidate": RATINGS / "fpi_2026_candidate.csv",
        "accepted": RATINGS / "fpi_2026_latest.csv",
        "value_columns": ["fpi"],
    },
    "TeamRankings": {
        "candidate": RATINGS / "teamrankings_2026_candidate.csv",
        "accepted": RATINGS / "teamrankings_2026_latest.csv",
        "value_columns": ["teamrankings"],
    },
}

CLI_SOURCES = {
    "spplus": "SP+",
    "fpi": "FPI",
    "teamrankings": "TeamRankings",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sources",
        default="spplus,fpi,teamrankings",
        help="Comma-separated sources: spplus,fpi,teamrankings",
    )
    return parser.parse_args()



def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def file_timestamp(path: Path) -> str | None:
    if not path.exists():
        return None
    return (
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_state() -> dict:
    if not STATE.exists():
        return {"schema_version": 1, "sources": {}}
    try:
        data = json.loads(STATE.read_text())
        if not isinstance(data, dict):
            raise ValueError("state is not an object")
        data.setdefault("schema_version", 1)
        data.setdefault("sources", {})
        return data
    except Exception:
        return {"schema_version": 1, "sources": {}}


def normalized_frame(path: Path, value_columns: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {"team", *value_columns}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"{path}: missing comparison columns {missing}")

    out = df[["team", *value_columns]].copy()
    out["team"] = out["team"].astype(str).str.strip()

    for column in value_columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")

    return out.sort_values("team").reset_index(drop=True)


def compare_source(
    name: str,
    candidate_path: Path,
    accepted_path: Path,
    value_columns: list[str],
    prior: dict,
    checked_at: str,
) -> dict:
    candidate = normalized_frame(candidate_path, value_columns)

    if not accepted_path.exists():
        return {
            "source": name,
            "change_status": "INITIALIZED",
            "latest_pull_at": checked_at,
            "last_changed_at": checked_at,
            "teams_changed": int(candidate["team"].nunique()),
            "changed_fields": int(candidate["team"].nunique() * len(value_columns)),
            "comparison_available": False,
            "teams": int(candidate["team"].nunique()),
            "value_columns": value_columns,
        }

    accepted = normalized_frame(accepted_path, value_columns)

    merged = accepted.merge(
        candidate,
        on="team",
        how="outer",
        suffixes=("_old", "_new"),
        indicator=True,
    )

    changed_team_mask = merged["_merge"].ne("both")
    changed_fields = 0

    for column in value_columns:
        old = merged[f"{column}_old"]
        new = merged[f"{column}_new"]

        equal = old.eq(new) | (old.isna() & new.isna())
        field_changed = ~equal

        changed_team_mask = changed_team_mask | field_changed
        changed_fields += int(field_changed.sum())

    teams_changed = int(changed_team_mask.sum())
    changed = teams_changed > 0

    prior_last_changed = prior.get("last_changed_at")
    baseline_timestamp = file_timestamp(accepted_path)

    if changed:
        last_changed_at = checked_at
        status = "UPDATED"
    elif prior_last_changed:
        last_changed_at = prior_last_changed
        status = "NO_CHANGE"
    else:
        # First tracked comparison. This establishes the accepted file as
        # the initial baseline without falsely claiming a newly observed move.
        last_changed_at = baseline_timestamp
        status = "BASELINE_ESTABLISHED"

    return {
        "source": name,
        "change_status": status,
        "latest_pull_at": checked_at,
        "last_changed_at": last_changed_at,
        "teams_changed": teams_changed,
        "changed_fields": changed_fields,
        "comparison_available": True,
        "teams": int(candidate["team"].nunique()),
        "value_columns": value_columns,
    }


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    args = parse_args()
    requested_keys = [x.strip().lower() for x in args.sources.split(",") if x.strip()]
    unknown = sorted(set(requested_keys) - set(CLI_SOURCES))
    if unknown:
        raise SystemExit(f"Unknown rating sources: {unknown}")
    requested_names = [CLI_SOURCES[x] for x in requested_keys]

    if not ACCEPT_SCRIPT.exists():
        raise SystemExit(f"Missing acceptance script: {ACCEPT_SCRIPT}")

    checked_at = now_utc()
    previous_state = load_state()
    comparisons = {}

    # Compare before promotion while the accepted files still represent
    # the prior accepted version.
    for name in requested_names:
        spec = SPECS[name]
        candidate = spec["candidate"]
        accepted = spec["accepted"]

        if not candidate.exists():
            raise SystemExit(f"{name}: candidate missing: {candidate}")

        comparisons[name] = compare_source(
            name=name,
            candidate_path=candidate,
            accepted_path=accepted,
            value_columns=spec["value_columns"],
            prior=previous_state.get("sources", {}).get(name, {}),
            checked_at=checked_at,
        )

    # Retain the existing all-or-nothing validation and promotion behavior.
    result = subprocess.run(
        [
            sys.executable,
            str(ACCEPT_SCRIPT),
            "--sources",
            ",".join(requested_keys),
        ],
        text=True,
    )
    if result.returncode != 0:
        return result.returncode

    merged_sources = dict(previous_state.get("sources", {}))
    merged_sources.update(comparisons)

    next_state = {
        "schema_version": 1,
        "updated_at": checked_at,
        "sources": merged_sources,
    }
    atomic_json(STATE, next_state)

    print("\nLive ratings change summary:")
    for name, row in comparisons.items():
        print(
            f"{name}: {row['change_status']} | "
            f"teams_changed={row['teams_changed']} | "
            f"last_changed_at={row['last_changed_at']}"
        )

    print(f"Wrote {STATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
