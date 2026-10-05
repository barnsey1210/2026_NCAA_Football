#!/usr/bin/env python3
"""Rebuild Odds payloads from a fresh, already-accepted market contract.

This recovery path never acquires provider data.  It is intended for a daily
workflow that stopped after canonical market acceptance but before the normal
Odds adapter stage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing built_at timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("built_at timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def recover(root: Path, max_age_hours: float, now: datetime) -> str:
    market_path = root / "data/site/current_market_contract.json"
    odds_path = root / "data/site/odds_screen_v2.json"
    market = load(market_path)
    if market.get("schema_version") != "current-market-contract-v1":
        raise ValueError("canonical current-market contract has an unsupported schema")

    market_built_at = timestamp(market.get("built_at"))
    age_hours = (now - market_built_at).total_seconds() / 3600
    if age_hours < -0.25 or age_hours > max_age_hours:
        raise ValueError(
            f"accepted current-market contract is {age_hours:.2f}h old; "
            f"recovery limit is {max_age_hours:.2f}h"
        )

    if odds_path.is_file():
        try:
            odds_built_at = timestamp(load(odds_path).get("built_at"))
        except (OSError, ValueError, json.JSONDecodeError):
            odds_built_at = None
        if odds_built_at is not None and odds_built_at >= market_built_at:
            return "already_current"

    commands = (
        [sys.executable, "scripts/site/build_odds_screen_v2.py"],
        [sys.executable, "scripts/site/build_odds_futures_v2.py"],
    )
    for command in commands:
        subprocess.run(command, cwd=root, check=True)

    rebuilt = load(odds_path)
    if timestamp(rebuilt.get("built_at")) != market_built_at:
        raise ValueError("rebuilt Odds timestamp does not match accepted current market")
    return "recovered"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--max-age-hours", type=float, default=18.0)
    args = parser.parse_args()
    result = recover(args.root.resolve(), args.max_age_hours, datetime.now(timezone.utc))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
