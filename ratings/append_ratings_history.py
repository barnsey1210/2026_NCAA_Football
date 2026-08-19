#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_LATEST = (
    ROOT / "data/ratings/ratings_latest.csv"
)

DEFAULT_HISTORY = (
    ROOT / "data/ratings/ratings_history.csv"
)

KEYS = [
    "snapshot_date",
    "season",
    "source",
    "team",
    "pulled_at",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Append canonical ratings snapshots to "
            "ratings history without destroying "
            "distinct no-lookahead observations."
        )
    )

    parser.add_argument(
        "--latest",
        type=Path,
        default=DEFAULT_LATEST,
    )

    parser.add_argument(
        "--history",
        type=Path,
        default=DEFAULT_HISTORY,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    latest_path = args.latest.resolve()
    history_path = args.history.resolve()

    if not latest_path.is_file():
        raise SystemExit(
            f"Missing latest ratings: {latest_path}"
        )

    latest = pd.read_csv(
        latest_path,
        low_memory=False,
    )

    missing_keys = [
        key
        for key in KEYS
        if key not in latest.columns
    ]

    if missing_keys:
        raise SystemExit(
            "Latest ratings missing required "
            f"history keys: {missing_keys}"
        )

    if history_path.exists():
        hist = pd.read_csv(
            history_path,
            low_memory=False,
        )

        for col in latest.columns:
            if col not in hist.columns:
                hist[col] = pd.NA

        for col in hist.columns:
            if col not in latest.columns:
                latest[col] = pd.NA

        latest = latest[
            hist.columns
        ]

        out = pd.concat(
            [hist, latest],
            ignore_index=True,
        )
    else:
        history_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        out = latest.copy()

    before_dedupe = len(out)

    out = out.drop_duplicates(
        subset=KEYS,
        keep="last",
    )

    duplicates_removed = (
        before_dedupe - len(out)
    )

    sort_columns = [
        "source",
        "team",
        "snapshot_date",
        "pulled_at",
    ]

    out = out.sort_values(
        sort_columns,
        kind="stable",
    )

    history_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    out.to_csv(
        history_path,
        index=False,
    )

    print(
        f"Wrote {history_path}: "
        f"{len(out)} rows"
    )

    print(
        "duplicates_removed:",
        duplicates_removed,
    )

    print(
        out.groupby("source")
        .size()
        .to_string()
    )


if __name__ == "__main__":
    main()
