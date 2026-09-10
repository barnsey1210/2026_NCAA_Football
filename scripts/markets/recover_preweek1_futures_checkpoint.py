#!/usr/bin/env python3
"""Recover the authentic 2026 pre-Week-1 Futures checkpoint from Git.

This is deliberately not a historical rebuild.  It reads the exact public
Futures artifact committed before Week 1, verifies its immutable Git blob, and
imports only fields already present in that artifact.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from capture_futures_checkpoint import ROW_FIELDS, read_existing


ROOT = Path(__file__).resolve().parents[2]
SOURCE_COMMIT = "cad503f9754f4ee057ef2040e5c297e8fdae08e7"
SOURCE_PATH = "data/site/futures_view.json"
SOURCE_BLOB = "c42eb8a869f1e53cfc9702504e36dda07c84727d"
SOURCE_SHA256 = "10b7f64d5e342c1c666adfbeb14181f223b5241ccd15fec12ce3cdc06cd79236"
SEASON_SOURCE_PATH = "data/site/season_simulations_2026.json"
SEASON_SOURCE_BLOB = "0afc7936ee446217df0d5c1f0a171fb89cf1ead9"
PLAYOFF_SOURCE_PATH = "data/site/playoff_model_2026.json"
PLAYOFF_SOURCE_BLOB = "1b11e2455361e3c6f89fbe2d04dcf77e5669ddc3"
WEEK1_CUTOFF = datetime.fromisoformat("2026-09-03T22:00:00+00:00")
CHECKPOINT_ID = "2026-preweek1-git-c42eb8a869f1e"

OUT_PATH = Path(os.environ.get(
    "NCAAF_FUTURES_CHECKPOINTS_PATH",
    str(ROOT / "data/markets/futures_checkpoints_2026.jsonl"),
)).expanduser().resolve()


def git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


def git_blob(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def build_recovered_checkpoint() -> dict:
    raw = git_bytes(SOURCE_COMMIT, SOURCE_PATH)
    if git_blob(SOURCE_COMMIT, SOURCE_PATH) != SOURCE_BLOB:
        raise SystemExit("Pre-Week-1 Futures Git blob does not match audited provenance")
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise SystemExit("Pre-Week-1 Futures SHA-256 does not match audited provenance")
    if git_blob(SOURCE_COMMIT, SEASON_SOURCE_PATH) != SEASON_SOURCE_BLOB:
        raise SystemExit("Pre-Week-1 season simulation blob does not match provenance")
    if git_blob(SOURCE_COMMIT, PLAYOFF_SOURCE_PATH) != PLAYOFF_SOURCE_BLOB:
        raise SystemExit("Pre-Week-1 playoff simulation blob does not match provenance")

    view = json.loads(raw)
    checkpoint_at = datetime.fromisoformat(str(view["built_at"]).replace("Z", "+00:00"))
    if checkpoint_at.astimezone(timezone.utc) >= WEEK1_CUTOFF:
        raise SystemExit("Audited checkpoint is not strictly before Week 1 kickoff")
    rows = [
        {field: row.get(field) for field in ROW_FIELDS}
        for row in view.get("rows", [])
        if isinstance(row, dict) and row.get("team")
    ]
    if len(rows) != 138:
        raise SystemExit(f"Expected 138 authentic rows; found {len(rows)}")
    return {
        "schema_version": "futures-operational-checkpoint-v1",
        "season": 2026,
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_date": checkpoint_at.date().isoformat(),
        "checkpoint_at": checkpoint_at.isoformat(),
        "status": "successful",
        "recovery_method": "RECOVERED_FROM_PUBLISHED_PREKICKOFF_ARTIFACTS",
        "immutable_historical_input": True,
        "source_view_schema_version": view.get("schema_version"),
        "source_view_built_at": view.get("built_at"),
        "provenance": {
            "source_commit": SOURCE_COMMIT,
            "source_path": SOURCE_PATH,
            "source_blob": SOURCE_BLOB,
            "source_sha256": SOURCE_SHA256,
            "season_source_path": SEASON_SOURCE_PATH,
            "season_source_blob": SEASON_SOURCE_BLOB,
            "season_model_built_at": "2026-08-31T12:02:23.196619+00:00",
            "playoff_source_path": PLAYOFF_SOURCE_PATH,
            "playoff_source_blob": PLAYOFF_SOURCE_BLOB,
            "playoff_model_built_at": "2026-08-31T12:05:11.378254+00:00",
            "week1_cutoff_at": WEEK1_CUTOFF.isoformat(),
        },
        "rows": rows,
    }


def write_import(path: Path, recovered: dict) -> None:
    records = read_existing(path)
    matches = [x for x in records if x.get("checkpoint_id") == CHECKPOINT_ID]
    if matches:
        if matches != [recovered]:
            raise SystemExit("Immutable recovered checkpoint already exists with different content")
        print(f"Verified existing immutable checkpoint: {path}")
        return
    records.append(recovered)
    records.sort(key=lambda x: str(x.get("checkpoint_at") or ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        for record in records:
            handle.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    print(f"Imported immutable pre-Week-1 checkpoint: {path}")


def main() -> None:
    checkpoint = build_recovered_checkpoint()
    write_import(OUT_PATH, checkpoint)
    print(f"checkpoint_at: {checkpoint['checkpoint_at']}")
    print(f"rows: {len(checkpoint['rows'])}")


if __name__ == "__main__":
    main()
