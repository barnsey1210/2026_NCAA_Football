#!/usr/bin/env python3
"""Content-fingerprint gate for deterministic daily simulation inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "data/control/simulation_input_fingerprints.json"

INPUTS = {
    "conference": (
        "data/snapshots/preseason/preseason_db.json",
        "data/ratings/ratings_master_latest.csv",
        "data/projections/game_projection_blend_2026.csv",
        "data/canonical/game_results_2026.json",
    ),
    "playoff": (
        "data/site/season_simulations_2026.json",
        "data/ratings/ratings_master_latest.csv",
        "data/projections/game_projection_blend_2026.csv",
        "data/canonical/game_results_2026.json",
    ),
}


def digest(paths: tuple[str, ...]) -> str:
    value = hashlib.sha256()
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            raise SystemExit(f"required simulation input missing: {relative}")
        value.update(relative.encode())
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                value.update(block)
    return value.hexdigest()


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError, TypeError):
        return {"schema_version": 1, "domains": {}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", choices=sorted(INPUTS))
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    fingerprint = digest(INPUTS[args.domain])
    state = load_state()
    prior = (state.get("domains") or {}).get(args.domain, {}).get("fingerprint")
    if args.record:
        state.setdefault("domains", {})[args.domain] = {
            "fingerprint": fingerprint,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "inputs": list(INPUTS[args.domain]),
        }
        STATE.parent.mkdir(parents=True, exist_ok=True)
        temporary = STATE.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        temporary.replace(STATE)
        print(f"{args.domain}: recorded {fingerprint}")
        return 0
    changed = prior != fingerprint
    print(json.dumps({"domain": args.domain, "changed": changed, "fingerprint": fingerprint, "prior": prior}))
    return 0 if changed else 3


if __name__ == "__main__":
    raise SystemExit(main())
