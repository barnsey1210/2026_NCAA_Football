#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json

import pandas as pd


ROOT = Path(".")
STATUS = ROOT / "data/ratings/ratings_source_status.csv"
CHANGE_STATE = ROOT / "data/ratings/live_rating_change_status.json"
MANUAL_STATE = ROOT / "data/ratings/manual_rating_source_status.json"


def main() -> int:
    if not STATUS.exists():
        raise SystemExit(f"Missing ratings status file: {STATUS}")

    status = pd.read_csv(STATUS)

    change_data = {}
    if CHANGE_STATE.exists():
        raw = json.loads(CHANGE_STATE.read_text())
        change_data = raw.get("sources", {})

    manual_data = {}
    if MANUAL_STATE.exists():
        manual_data = json.loads(MANUAL_STATE.read_text())

    new_columns = [
        "change_status",
        "latest_pull_at",
        "last_changed_at",
        "teams_changed",
        "changed_fields",
        "comparison_available",
    ]

    for column in new_columns:
        if column not in status.columns:
            status[column] = None

    for index, row in status.iterrows():
        source = str(row.get("source") or "")
        change = change_data.get(source)

        if change:
            for column in new_columns:
                status.at[index, column] = change.get(column)

        elif source == "Brad Powers":
            # Brad Powers is manually imported. Do not let an automated
            # ratings rebuild change its displayed update timestamp.
            manual = manual_data.get("Brad Powers", {})
            manual_changed_at = manual.get("last_changed_at")

            status.at[index, "change_status"] = "MANUAL_SOURCE"
            status.at[index, "latest_pull_at"] = manual_changed_at
            status.at[index, "last_changed_at"] = manual_changed_at
            status.at[index, "teams_changed"] = None
            status.at[index, "changed_fields"] = None
            status.at[index, "comparison_available"] = False

    temporary = STATUS.with_suffix(".csv.tmp")
    status.to_csv(temporary, index=False)
    temporary.replace(STATUS)

    print(f"Wrote {STATUS}")
    print(
        status[
            status["source"].isin(
                ["SP+", "FPI", "TeamRankings", "Brad Powers"]
            )
        ][
            [
                "source",
                "change_status",
                "latest_pull_at",
                "last_changed_at",
                "teams_changed",
            ]
        ].to_string(index=False)
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
