#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RATINGS = ROOT / "data" / "ratings"
BACKUPS = RATINGS / "accepted_backups"
CANDIDATE_RECEIPTS = RATINGS / "candidate_receipts"

RECEIPT_KEYS = {
    "SP+": "spplus",
    "FPI": "fpi",
    "TeamRankings": "teamrankings",
}

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



def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_receipt(name, candidate):
    key = RECEIPT_KEYS[name]
    receipt_path = CANDIDATE_RECEIPTS / f"{key}.json"

    if not receipt_path.exists():
        raise SystemExit(
            f"{name}: validated candidate receipt missing: {receipt_path}"
        )

    try:
        receipt = json.loads(receipt_path.read_text())
    except Exception as exc:
        raise SystemExit(
            f"{name}: invalid candidate receipt: {exc}"
        )

    if receipt.get("source") != key:
        raise SystemExit(
            f"{name}: candidate receipt source mismatch"
        )

    if receipt.get("candidate") != candidate.name:
        raise SystemExit(
            f"{name}: candidate receipt filename mismatch"
        )

    generated_at = receipt.get("generated_at")
    try:
        generated = datetime.fromisoformat(
            str(generated_at).replace("Z", "+00:00")
        )
        if generated.tzinfo is None:
            generated = generated.replace(tzinfo=timezone.utc)
        generated = generated.astimezone(timezone.utc)
    except (TypeError, ValueError):
        raise SystemExit(
            f"{name}: candidate receipt timestamp invalid"
        )

    age = datetime.now(timezone.utc) - generated
    if age < timedelta(0) or age > timedelta(hours=1):
        raise SystemExit(
            f"{name}: candidate receipt expired"
        )

    expected_hash = receipt.get("sha256")
    actual_hash = sha256_file(candidate)

    if not expected_hash or expected_hash != actual_hash:
        raise SystemExit(
            f"{name}: candidate receipt hash mismatch"
        )

    return receipt_path


def validate(name, spec):
    path = spec["candidate"]
    if not path.exists():
        raise SystemExit(f"{name}: candidate missing: {path}")

    receipt_path = validate_receipt(name, path)

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

    return df, receipt_path


def main():
    args = parse_args()
    requested_keys = [x.strip().lower() for x in args.sources.split(",") if x.strip()]
    unknown = sorted(set(requested_keys) - set(CLI_SOURCES))
    if unknown:
        raise SystemExit(f"Unknown rating sources: {unknown}")

    requested_names = [CLI_SOURCES[x] for x in requested_keys]
    validated = {}
    receipts = {}

    for name in requested_names:
        spec = SOURCES[name]
        validated[name], receipts[name] = validate(name, spec)
        print(f"{name}: candidate and receipt passed validation")

    team_sets = {
        name: set(df["team"])
        for name, df in validated.items()
    }
    baseline = next(iter(team_sets.values()))
    for name, teams in team_sets.items():
        if teams != baseline:
            missing = sorted(baseline - teams)
            extra = sorted(teams - baseline)
            raise SystemExit(
                f"{name}: team universe mismatch; missing={missing}, extra={extra}"
            )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    BACKUPS.mkdir(parents=True, exist_ok=True)

    for name in requested_names:
        spec = SOURCES[name]
        accepted = spec["accepted"]
        candidate = spec["candidate"]

        if accepted.exists():
            backup = BACKUPS / f"{accepted.stem}_{timestamp}{accepted.suffix}"
            shutil.copy2(accepted, backup)
            print(f"{name}: backed up accepted file to {backup.relative_to(ROOT)}")

        shutil.copy2(candidate, accepted)
        print(f"{name}: promoted {candidate.name} -> {accepted.name}")

        candidate.unlink()
        receipts[name].unlink()
        print(f"{name}: consumed candidate and validation receipt")

    print("Requested live rating candidates accepted:", ", ".join(requested_names))


if __name__ == "__main__":
    main()
