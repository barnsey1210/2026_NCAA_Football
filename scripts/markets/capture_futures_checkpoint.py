#!/usr/bin/env python3
"""Capture one immutable-per-UTC-date operational Futures checkpoint.

The source is the canonical data/site/futures_view.json artifact. Repeated
successful captures on the same UTC date replace that date's record with the
latest state rather than creating duplicates.

This history is prospective only. It must not fabricate historical model or
edge states.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]

RUNTIME_ROOT = Path(
    os.environ.get("NCAAF_RUNTIME_ROOT", str(ROOT))
).expanduser().resolve()

VIEW_PATH = Path(
    os.environ.get(
        "NCAAF_FUTURES_VIEW_IN",
        str(RUNTIME_ROOT / "data/site/futures_view.json"),
    )
).expanduser().resolve()

OUT_PATH = Path(
    os.environ.get(
        "NCAAF_FUTURES_CHECKPOINTS_PATH",
        str(RUNTIME_ROOT / "data/markets/futures_checkpoints_2026.jsonl"),
    )
).expanduser().resolve()


ROW_FIELDS = (
    "team",
    "conference",

    "projected_wins",
    "market_win_total",
    "win_edge",
    "win_direction",
    "win_price",
    "win_book",
    "win_book_count",

    "title_model_prob",
    "title_market_prob",
    "title_edge",
    "title_price",
    "title_book",
    "title_book_count",

    "playoff_model_prob",
    "playoff_market_prob",
    "playoff_edge",
    "playoff_price",
    "playoff_book",
    "playoff_book_count",

    "national_title_model_prob",
    "national_title_market_prob",
    "national_title_edge",
    "national_title_price",
    "national_title_book",
    "national_title_book_count",
)


def parse_timestamp(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def read_existing(path):
    records = []
    if not path.exists():
        return records

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            records.append(obj)

    return records


def atomic_write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as f:
        tmp = Path(f.name)
        for record in records:
            f.write(
                json.dumps(
                    record,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )

    os.replace(tmp, path)


def main():
    if not VIEW_PATH.exists():
        raise SystemExit(
            f"Futures view does not exist: {VIEW_PATH}"
        )

    view = json.loads(VIEW_PATH.read_text())

    built_at = parse_timestamp(view.get("built_at"))
    if built_at is None:
        built_at = datetime.now(timezone.utc)

    checkpoint_at = built_at.isoformat()
    checkpoint_date = built_at.date().isoformat()

    model_freshness = view.get("model_freshness") or {}
    market_contract = view.get("market_contract") or {}

    rows = []
    for row in view.get("rows", []):
        if not isinstance(row, dict) or not row.get("team"):
            continue
        rows.append(
            {
                key: row.get(key)
                for key in ROW_FIELDS
            }
        )

    record = {
        "schema_version": "futures-operational-checkpoint-v1",
        "season": 2026,
        "checkpoint_date": checkpoint_date,
        "checkpoint_at": checkpoint_at,
        "source_view_schema_version": view.get("schema_version"),
        "source_view_built_at": view.get("built_at"),
        "season_model_built_at": (
            model_freshness
            .get("season_simulation", {})
            .get("built_at")
        ),
        "playoff_model_built_at": (
            model_freshness
            .get("playoff_simulation", {})
            .get("built_at")
        ),
        "market_contract_built_at": market_contract.get("built_at"),
        "approved_executable_books": (
            market_contract.get("approved_executable_books") or []
        ),
        "rows": rows,
    }

    existing = read_existing(OUT_PATH)

    # One operational checkpoint per UTC date. A later successful run on the
    # same date replaces the earlier one with the more current state.
    by_date = {
        str(x.get("checkpoint_date")): x
        for x in existing
        if x.get("checkpoint_date")
    }
    by_date[checkpoint_date] = record

    records = sorted(
        by_date.values(),
        key=lambda x: (
            str(x.get("checkpoint_date") or ""),
            str(x.get("checkpoint_at") or ""),
        ),
    )

    atomic_write_jsonl(OUT_PATH, records)

    print(f"Futures checkpoint: {checkpoint_date}")
    print(f"rows: {len(rows)}")
    print(f"history checkpoints: {len(records)}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
