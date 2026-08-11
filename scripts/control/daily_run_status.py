#!/usr/bin/env python3
"""Atomically maintain the canonical daily orchestration status artifact."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FINAL_STATES = {"PASSED", "FAILED", "SKIPPED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def registry_stages(registry_path: Path) -> list[dict[str, Any]]:
    registry = load_json(registry_path)
    stages = registry.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError("stage registry must contain a non-empty stages list")
    orders = [stage.get("order") for stage in stages]
    if any(not isinstance(order, int) for order in orders) or orders != sorted(orders):
        raise ValueError("stage registry orders must be increasing integers")
    ids = [stage.get("id") for stage in stages]
    if any(not isinstance(stage_id, str) or not stage_id for stage_id in ids):
        raise ValueError("every stage requires a non-empty id")
    if len(ids) != len(set(ids)):
        raise ValueError("stage ids must be unique")
    return stages


def cmd_init(args: argparse.Namespace) -> None:
    stages = registry_stages(args.registry)
    deployed_commit = None
    if args.source_record.exists():
        try:
            deployed_commit = load_json(args.source_record).get("source_commit")
        except (OSError, ValueError, json.JSONDecodeError):
            deployed_commit = None
    payload: dict[str, Any] = {
        "schema_version": 1,
        "run_id": args.run_id,
        "execution_profile": args.profile,
        "started_at_utc": args.started_at,
        "finished_at_utc": None,
        "source_deployed_commit": deployed_commit,
        "overall_result": "RUNNING",
        "warnings": [],
        "email_build_status": "PENDING",
        "email_send_status": "PENDING",
        "site_validation_status": "PENDING",
        "publication_status": "PENDING",
        "stages": [
            {
                "id": stage["id"],
                "name": stage["name"],
                "order": stage["order"],
                "required": bool(stage["required"]),
                "external_network": bool(stage["external_network"]),
                "email_dependency": bool(stage["email_dependency"]),
                "publication_dependency": bool(stage["publication_dependency"]),
                "status": "PENDING",
                "started_at_utc": None,
                "finished_at_utc": None,
                "detail": None,
            }
            for stage in stages
        ],
    }
    atomic_write(args.output, payload)


def find_stage(payload: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in payload.get("stages", []):
        if stage.get("id") == stage_id:
            return stage
    raise ValueError(f"unknown stage id: {stage_id}")


def update_summary_fields(payload: dict[str, Any]) -> None:
    mapping = {
        "email_build_status": "email_build",
        "email_send_status": "email_send",
        "site_validation_status": "site_validation",
        "publication_status": "publication",
    }
    for field, stage_id in mapping.items():
        payload[field] = find_stage(payload, stage_id)["status"]


def cmd_stage(args: argparse.Namespace) -> None:
    payload = load_json(args.output)
    stage = find_stage(payload, args.stage_id)
    now = utc_now()
    if args.status == "RUNNING":
        stage["started_at_utc"] = stage["started_at_utc"] or now
        stage["finished_at_utc"] = None
    else:
        if args.status not in FINAL_STATES:
            raise ValueError(f"invalid final stage status: {args.status}")
        stage["started_at_utc"] = stage["started_at_utc"] or now
        stage["finished_at_utc"] = now
    stage["status"] = args.status
    stage["detail"] = args.detail
    update_summary_fields(payload)
    atomic_write(args.output, payload)


def cmd_warning(args: argparse.Namespace) -> None:
    payload = load_json(args.output)
    payload.setdefault("warnings", []).append(
        {"stage_id": args.stage_id or None, "message": args.message, "at_utc": utc_now()}
    )
    atomic_write(args.output, payload)


def cmd_finish(args: argparse.Namespace) -> None:
    payload = load_json(args.output)
    required_failed = any(
        stage.get("required") and stage.get("status") == "FAILED"
        for stage in payload.get("stages", [])
    )
    payload["finished_at_utc"] = args.finished_at
    if args.exit_code != 0 or required_failed:
        payload["overall_result"] = "FAILED"
    elif payload.get("warnings"):
        payload["overall_result"] = "PASSED_WITH_WARNINGS"
    else:
        payload["overall_result"] = "PASSED"
    update_summary_fields(payload)
    atomic_write(args.output, payload)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--registry", type=Path, required=True)
    init.add_argument("--source-record", type=Path, required=True)
    init.add_argument("--run-id", required=True)
    init.add_argument("--profile", default="full")
    init.add_argument("--started-at", required=True)
    init.set_defaults(func=cmd_init)

    stage = sub.add_parser("stage")
    stage.add_argument("--output", type=Path, required=True)
    stage.add_argument("--stage-id", required=True)
    stage.add_argument("--status", choices=["RUNNING", "PASSED", "FAILED", "SKIPPED"], required=True)
    stage.add_argument("--detail")
    stage.set_defaults(func=cmd_stage)

    warning = sub.add_parser("warning")
    warning.add_argument("--output", type=Path, required=True)
    warning.add_argument("--stage-id", default="")
    warning.add_argument("--message", required=True)
    warning.set_defaults(func=cmd_warning)

    finish = sub.add_parser("finish")
    finish.add_argument("--output", type=Path, required=True)
    finish.add_argument("--finished-at", required=True)
    finish.add_argument("--exit-code", type=int, required=True)
    finish.set_defaults(func=cmd_finish)
    return result


def main() -> int:
    args = parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
