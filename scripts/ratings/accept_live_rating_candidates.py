#!/usr/bin/env python3

from datetime import datetime, timezone
from pathlib import Path
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RATINGS = ROOT / "data" / "ratings"
BACKUPS = RATINGS / "accepted_backups"

SOURCES = {
    "SP+": {
        "candidate": RATINGS / "spplus_2026_candidate.csv",
        "accepted": RATINGS / "spplus_2026_from_espn_latest.csv",
        "required": ["team", "spplus", "spplus_off", "spplus_def"],
    },
    "FPI": {
        "candidate": RATINGS / "fpi_2026_candidate.csv",
        "accepted": RATINGS / "fpi_2026_latest.csv",
        "required": ["team", "fpi"],
    },
    "TeamRankings": {
        "candidate": RATINGS / "teamrankings_2026_candidate.csv",
        "accepted": RATINGS / "teamrankings_2026_latest.csv",
        "required": ["team", "teamrankings"],
    },
}


def validate(name, spec):
    path = spec["candidate"]
    if not path.exists():
        raise SystemExit(f"{name}: candidate missing: {path}")

    df = pd.read_csv(path)

    missing_columns = [c for c in spec["required"] if c not in df.columns]
    if missing_columns:
        raise SystemExit(f"{name}: missing columns: {missing_columns}")

    if len(df) != 138:
        raise SystemExit(f"{name}: expected 138 rows, found {len(df)}")

    if df["team"].nunique() != 138:
        raise SystemExit(
            f"{name}: expected 138 unique teams, found {df['team'].nunique()}"
        )

    duplicates = df[df["team"].duplicated(keep=False)]["team"].tolist()
    if duplicates:
        raise SystemExit(f"{name}: duplicate teams: {duplicates}")

    for column in spec["required"]:
        if df[column].isna().any():
            count = int(df[column].isna().sum())
            raise SystemExit(f"{name}: {count} missing values in {column}")

    return df


def main():
    validated = {}

    for name, spec in SOURCES.items():
        validated[name] = validate(name, spec)
        print(f"{name}: candidate passed validation")

    team_sets = {
        name: set(df["team"])
        for name, df in validated.items()
    }
    baseline = team_sets["SP+"]
    for name, teams in team_sets.items():
        if teams != baseline:
            missing = sorted(baseline - teams)
            extra = sorted(teams - baseline)
            raise SystemExit(
                f"{name}: team universe mismatch; missing={missing}, extra={extra}"
            )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    BACKUPS.mkdir(parents=True, exist_ok=True)

    for name, spec in SOURCES.items():
        accepted = spec["accepted"]
        candidate = spec["candidate"]

        if accepted.exists():
            backup = BACKUPS / f"{accepted.stem}_{timestamp}{accepted.suffix}"
            shutil.copy2(accepted, backup)
            print(f"{name}: backed up accepted file to {backup.relative_to(ROOT)}")

        shutil.copy2(candidate, accepted)
        print(f"{name}: promoted {candidate.name} -> {accepted.name}")

    print("All three live rating candidates accepted.")


if __name__ == "__main__":
    main()
