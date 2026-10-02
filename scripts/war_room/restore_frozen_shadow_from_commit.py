#!/usr/bin/env python3
"""Restore missing frozen Shadow values from an exact pre-kickoff Git snapshot.

This migration never calculates a projection. It copies the already-materialized
game-level spread and total fields from one explicitly selected historical
commit into null slots in the write-once runtime freeze store.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def git_bytes(repo: Path, commit: str, relative: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=repo,
        capture_output=True, check=True,
    ).stdout


def commit_time(repo: Path, commit: str) -> datetime:
    raw = subprocess.run(
        ["git", "show", "-s", "--format=%cI", commit], cwd=repo,
        text=True, capture_output=True, check=True,
    ).stdout.strip()
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)


def parsed(value: object) -> datetime:
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--freeze-store", type=Path, required=True)
    parser.add_argument("--game-id", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    contract = json.loads(git_bytes(args.source_repo, args.source_commit,
                                    "data/site/current_game_projection_contract.json"))
    components = json.loads(git_bytes(args.source_repo, args.source_commit,
                                      "data/site/saturday_shadow_component_predictions.json"))
    store = json.loads(args.freeze_store.read_text())
    contract_by_gid = {str(row.get("game_id")): row for row in contract.get("games", [])}
    component_rows = components.get("games") or components.get("rows") or []
    component_by_gid = {str(row.get("game_id")): row for row in component_rows}
    selected = set(args.game_id) if args.game_id else set(store.get("games", {}))
    source_time = commit_time(args.source_repo, args.source_commit)
    restored = []

    for gid in sorted(selected):
        frozen = (store.get("games") or {}).get(gid)
        historical = contract_by_gid.get(gid)
        component = component_by_gid.get(gid)
        if not isinstance(frozen, dict) or not historical or not component:
            continue
        kickoff = parsed(frozen.get("kickoff_time"))
        if source_time >= kickoff:
            raise SystemExit(f"source commit is not pre-kickoff for {gid}")
        models = frozen.get("models") or {}
        spread = models.get("shadow_spread") or {}
        total = models.get("shadow_total") or {}
        historical_models = historical.get("projections") or {}
        exact_spread = (historical_models.get("shadow_spread_sp_sagarin_v1") or {}).get("value_home_line")
        exact_total = component.get("predicted_sp_plus_component_total")
        if component.get("spread_projection_readiness") != "ready" or component.get("total_projection_readiness") != "ready":
            continue
        changed = False
        if spread.get("value_home_line") is None and exact_spread is not None:
            spread["value_home_line"] = exact_spread
            spread["selection_status"] = "AVAILABLE"
            spread["selection_reason"] = "EXACT_FROZEN_PREGAME_SNAPSHOT"
            spread["availability_status"] = "AVAILABLE"
            changed = True
        if total.get("value_total") is None and exact_total is not None:
            total["value_total"] = exact_total
            total["selection_status"] = "AVAILABLE"
            total["selection_reason"] = "EXACT_FROZEN_PREGAME_SNAPSHOT"
            total["availability_status"] = "AVAILABLE"
            changed = True
        if changed:
            frozen["shadow_value_restore"] = {
                "source_commit": args.source_commit,
                "source_commit_at": source_time.isoformat(),
                "method": "EXACT_GAME_LEVEL_FIELD_COPY_NO_RECOMPUTATION",
            }
            restored.append(gid)

    report = {"source_commit": args.source_commit, "restored_game_ids": restored,
              "restored_count": len(restored), "applied": args.apply}
    if args.apply:
        temporary = args.freeze_store.with_suffix(args.freeze_store.suffix + ".tmp")
        temporary.write_text(json.dumps(store, indent=2) + "\n")
        temporary.replace(args.freeze_store)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
