#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

WIN = ROOT / "market_win_totals_import.csv"
CONF = ROOT / "market_conference_futures_import.csv"
PLAYOFF = ROOT / "data/markets/action/action_playoff_futures_2026.json"
CONTRACT = ROOT / "data/markets/current_futures_market_2026.json"
FUTURES_VIEW = ROOT / "data/site/futures_view.json"
ODDS_FUTURES = ROOT / "data/site/odds_futures_v2.json"

STATE_DIR = ROOT / "data/control/futures_market_scheduler"
MARKET_STATE = STATE_DIR / "market_state.json"
LATEST = STATE_DIR / "refresh_latest.json"
CHANGES = ROOT / "data/markets/futures_fast_changes_2026.jsonl"

VOLATILE_PARTS = (
    "pulled_at",
    "updated_at",
    "built_at",
    "generated_at",
    "snapshot_date",
    "timestamp",
    "source_url",
    "notes",
    "freshness",
    "age_seconds",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def run(name: str, command: list[str], required: bool = True) -> bool:
    print()
    print("=" * 72)
    print(name)
    print("+", " ".join(command))
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode == 0:
        print(f"{name}: PASS")
        return True
    print(f"{name}: FAILED ({result.returncode})")
    if required:
        return False
    return True


def backup_files(paths: list[Path], directory: Path) -> dict[Path, Path]:
    saved = {}
    for i, path in enumerate(paths):
        if not path.exists():
            continue
        dest = directory / f"{i:02d}_{path.name}"
        shutil.copy2(path, dest)
        saved[path] = dest
    return saved


def restore(saved: dict[Path, Path], paths: list[Path] | None = None) -> None:
    wanted = set(paths) if paths is not None else set(saved)
    for original, backup in saved.items():
        if original not in wanted:
            continue
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, original)


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            lower = str(key).lower()
            if any(part in lower for part in VOLATILE_PARTS):
                continue
            out[key] = normalize(item)
        return out
    if isinstance(value, list):
        items = [normalize(item) for item in value]
        return sorted(
            items,
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
        )
    return value


def semantic_hash(path: Path) -> str:
    payload = json.loads(path.read_text())
    canonical = json.dumps(
        normalize(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


def write_result(status: str, changed: bool, **extra: Any) -> None:
    payload = {
        "schema_version": 1,
        "checked_at": now_iso(),
        "status": status,
        "changed": changed,
        **extra,
    }
    atomic_json(LATEST, payload)
    print()
    print("FAST_FUTURES_RESULT=" + json.dumps(payload, sort_keys=True))


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CHANGES.parent.mkdir(parents=True, exist_ok=True)

    prior_state = read_json(MARKET_STATE, {})
    prior_hash = prior_state.get("semantic_hash")

    protected = [WIN, CONF, PLAYOFF, CONTRACT, FUTURES_VIEW, ODDS_FUTURES]

    with tempfile.TemporaryDirectory(prefix="ncaaf-futures-fast-") as tmp:
        saved = backup_files(protected, Path(tmp))

        acquisition_ok = True

        acquisition_ok &= run(
            "Action Network win totals",
            [sys.executable, "pull_actionnetwork_win_totals_api.py"],
        )

        dk_ok = run(
            "Visible DraftKings win totals",
            [sys.executable, "odds/pull_actionnetwork_visible_dk_win_totals.py"],
            required=False,
        )
        if dk_ok:
            run(
                "Merge visible DraftKings win totals",
                [sys.executable, "odds/merge_visible_dk_win_totals.py"],
                required=False,
            )

        run(
            "FanDuel win totals",
            [sys.executable, "pull_fanduel_win_totals.py"],
            required=False,
        )

        run(
            "Caesars win totals",
            [sys.executable, "pull_bettingpros_caesars_win_totals.py"],
            required=False,
        )

        acquisition_ok &= run(
            "Action Network conference futures",
            [sys.executable, "pulls/pull_actionnetwork_conference_futures_api.py"],
        )

        run(
            "Quarantine invalid DraftKings win totals",
            [sys.executable, "odds/quarantine_bad_draftkings_win_total_rows.py"],
            required=False,
        )

        acquisition_ok &= run(
            "Futures acquisition reliability",
            [
                sys.executable,
                "scripts/markets/audit_futures_market_reliability.py",
                "--phase",
                "acquisition",
            ],
        )

        if not acquisition_ok:
            restore(saved, [WIN, CONF])
            write_result(
                "ACQUISITION_DEGRADED_PRIOR_MARKET_PRESERVED",
                False,
            )
            return 0

        playoff_ok = run(
            "Action Network CFP and national-title futures",
            [sys.executable, "scripts/markets/pull_actionnetwork_playoff_futures.py"],
            required=False,
        )
        if not playoff_ok:
            restore(saved, [PLAYOFF])

        if not run(
            "Build canonical Futures market contract",
            [sys.executable, "scripts/markets/build_current_futures_market_contract.py"],
        ):
            restore(saved, [CONTRACT, FUTURES_VIEW, ODDS_FUTURES])
            write_result("CONTRACT_BUILD_FAILED_PRIOR_VIEW_PRESERVED", False)
            return 0

        if not run(
            "Full Futures reliability audit",
            [
                sys.executable,
                "scripts/markets/audit_futures_market_reliability.py",
                "--phase",
                "all",
            ],
        ):
            restore(saved, [CONTRACT, FUTURES_VIEW, ODDS_FUTURES])
            write_result("RELIABILITY_FAILED_PRIOR_VIEW_PRESERVED", False)
            return 0

        if not run(
            "Build Futures view",
            [sys.executable, "scripts/site/build_futures_view.py"],
        ):
            restore(saved, [CONTRACT, FUTURES_VIEW, ODDS_FUTURES])
            write_result("FUTURES_VIEW_BUILD_FAILED_PRIOR_VIEW_PRESERVED", False)
            return 0

        if not run(
            "Build Odds Futures payload",
            [sys.executable, "scripts/site/build_odds_futures_v2.py"],
        ):
            restore(saved, [CONTRACT, FUTURES_VIEW, ODDS_FUTURES])
            write_result("ODDS_FUTURES_BUILD_FAILED_PRIOR_VIEW_PRESERVED", False)
            return 0

        current_hash = semantic_hash(CONTRACT)
        changed = current_hash != prior_hash

        state = {
            "schema_version": 1,
            "checked_at": now_iso(),
            "semantic_hash": current_hash,
            "prior_semantic_hash": prior_hash,
            "changed": changed,
            "contract": str(CONTRACT.relative_to(ROOT)),
        }
        atomic_json(MARKET_STATE, state)

        if changed:
            event = {
                "schema_version": 1,
                "changed_at": now_iso(),
                "prior_semantic_hash": prior_hash,
                "semantic_hash": current_hash,
                "reason": (
                    "INITIAL_BASELINE"
                    if not prior_hash
                    else "SUBSTANTIVE_FUTURES_MARKET_CHANGE"
                ),
            }
            with CHANGES.open("a") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")

        write_result(
            "SUCCEEDED",
            changed,
            semantic_hash=current_hash,
            prior_semantic_hash=prior_hash,
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
