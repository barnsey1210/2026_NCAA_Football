#!/usr/bin/env python3
"""Fail when canonical root publication pages differ from the public build."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "build" / "public_site"
PAGES = (
    "index.html",
    "ratings.html",
    "odds.html",
    "openers.html",
    "matchups.html",
    "futures.html",
    "betting.html",
    "schedule.html",
    "conferences.html",
    "war-room.html",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    failures = []
    for name in PAGES:
        root_page = ROOT / name
        built_page = PUBLIC / name
        missing = [str(path.relative_to(ROOT)) for path in (root_page, built_page) if not path.is_file()]
        if missing:
            failures.append(name)
            print(f"FAIL: {name} missing required artifact(s): {', '.join(missing)}")
            continue
        root_digest = digest(root_page)
        built_digest = digest(built_page)
        if root_digest != built_digest:
            failures.append(name)
            print(
                f"FAIL: {name} differs from build/public_site/{name} "
                f"(root={root_digest[:12]} build={built_digest[:12]})"
            )
            continue
        print(f"PASS: {name} matches build/public_site/{name}")

    if failures:
        raise SystemExit(
            "Publication parity audit failed for: " + ", ".join(failures)
        )
    print(f"PASS: publication parity verified for {len(PAGES)} pages")


if __name__ == "__main__":
    main()
