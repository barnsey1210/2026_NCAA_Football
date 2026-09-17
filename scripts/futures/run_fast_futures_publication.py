#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKER = "FAST_FUTURES_RESULT="


def run_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command))
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result


def parse_result(text: str) -> dict:
    for line in reversed(text.splitlines()):
        if line.startswith(MARKER):
            try:
                value = json.loads(line.split("=", 1)[1])
                return value if isinstance(value, dict) else {}
            except Exception:
                return {}
    return {}


def main() -> int:
    refresh = run_capture(
        [sys.executable, "scripts/futures/run_fast_futures_refresh.py"]
    )
    if refresh.returncode != 0:
        return refresh.returncode

    result = parse_result((refresh.stdout or "") + "\n" + (refresh.stderr or ""))
    changed = result.get("changed") is True

    if not changed:
        payload = {
            "refresh_status": result.get("status", "UNKNOWN"),
            "changed": False,
            "publication_status": "SKIPPED_NO_CHANGE",
        }
        print("FAST_FUTURES_PUBLICATION_RESULT=" + json.dumps(payload, sort_keys=True))
        return 0

    build = run_capture(
        [sys.executable, "scripts/site/build_public_site.py"]
    )
    if build.returncode != 0:
        return build.returncode

    publish = run_capture(
        ["bash", "scripts/publish/publish_site.sh", "--push"]
    )
    if publish.returncode != 0:
        return publish.returncode

    payload = {
        "refresh_status": result.get("status", "SUCCEEDED"),
        "changed": True,
        "publication_status": "PUBLISHED",
        "semantic_hash": result.get("semantic_hash"),
    }
    print("FAST_FUTURES_PUBLICATION_RESULT=" + json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
