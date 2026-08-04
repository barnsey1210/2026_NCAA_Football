#!/usr/bin/env python3
"""Restore email/market environment loading in the scheduled NCAAF wrapper.

The Phase 1 wrapper correctly redirected launchd to the canonical project
pipeline, but it did not preserve the old wrapper's environment-file sourcing.
This installer restores:
- ~/.ncaaf_email_env
- ~/.ncaaf_market_env

before executing ~/NCAAF_AUTO/daily_market_update.sh.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys


ROOT = Path.home() / "NCAAF_AUTO"
TARGET = Path.home() / "Scripts/NCAAF/daily_market_update.sh"
BACKUP_ROOT = ROOT / "backups/scheduled_wrapper_env_fix"


WRAPPER = """#!/bin/bash
set -e

if [ -f "$HOME/.ncaaf_email_env" ]; then
  set -a
  source "$HOME/.ncaaf_email_env"
  set +a
fi

if [ -f "$HOME/.ncaaf_market_env" ]; then
  set -a
  source "$HOME/.ncaaf_market_env"
  set +a
fi

exec /bin/bash "$HOME/NCAAF_AUTO/daily_market_update.sh"
"""


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if TARGET.exists():
        backup = BACKUP_ROOT / timestamp / "external" / TARGET.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TARGET, backup)
        print(f"backup:  {backup}")

    TARGET.write_text(WRAPPER, encoding="utf-8")
    TARGET.chmod(0o755)

    result = subprocess.run(
        ["/bin/bash", "-n", str(TARGET)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "bash syntax validation failed")

    print(f"patched: {TARGET}")
    print()
    print("SCHEDULED WRAPPER ENVIRONMENT FIX")
    print("=" * 100)
    print("Loads ~/.ncaaf_email_env: True")
    print("Loads ~/.ncaaf_market_env: True")
    print("Exports sourced variables to child process: True")
    print("Executes canonical daily pipeline: True")
    print("Shell syntax validation passed: True")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
