#!/usr/bin/env python3
"""Read-only audit of the source commit recorded in an NCAAF runtime."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


EXPECTED_REMOTES = {
    "https://github.com/barnsey1210/2026_NCAA_Football.git",
    "https://github.com/barnsey1210/2026_NCAA_Football",
    "git@github.com:barnsey1210/2026_NCAA_Football.git",
}
DEFAULT_TARGET = Path("/Users/jameslindesmith/NCAAF_AUTO")


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def load_manifest(root: Path, manifest: Path) -> list[str]:
    paths: list[str] = []
    for number, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        value = raw.rstrip("\r")
        candidate = Path(value)
        if (
            not value
            or candidate.is_absolute()
            or value in {".", ".."}
            or ".." in candidate.parts
            or value.endswith("/")
        ):
            raise ValueError(f"unsafe manifest path at line {number}: {value!r}")
        source = root / candidate
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"manifest source is not a regular non-symlink file: {value}")
        if source.resolve().parent != root and root not in source.resolve().parents:
            raise ValueError(f"manifest source escapes repository: {value}")
        if value in paths:
            raise ValueError(f"duplicate manifest path: {value}")
        paths.append(value)
    if not paths:
        raise ValueError("manifest contains no files")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    try:
        detected = Path(git(root, "rev-parse", "--show-toplevel").stdout.decode().strip()).resolve()
    except subprocess.CalledProcessError:
        return fail("status script is not inside a Git repository")
    if detected != root:
        return fail(f"unexpected source repository root: {detected}")
    origin = git(root, "remote", "get-url", "origin", check=False).stdout.decode().strip()
    if origin not in EXPECTED_REMOTES:
        return fail(f"unexpected origin remote: {origin or 'missing'}")

    target = args.target.expanduser().resolve()
    if target == Path("/") or target == root or root in target.parents:
        return fail(f"unsafe runtime target: {target}")
    manifest = (args.manifest or root / "deploy/source_manifest.txt").resolve()
    try:
        paths = load_manifest(root, manifest)
    except (OSError, ValueError) as exc:
        return fail(str(exc))

    head = git(root, "rev-parse", "HEAD").stdout.decode().strip()
    record_path = target / "data/control/deployed_source_version.json"
    if not record_path.is_file() or record_path.is_symlink():
        print("Deployment state: UNKNOWN")
        print(f"Recorded deployment: missing ({record_path})")
        print(f"Current source HEAD: {head}")
        return 0
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("Deployment state: UNKNOWN")
        print(f"Recorded deployment: unreadable ({exc})")
        print(f"Current source HEAD: {head}")
        return 0

    recorded = str(record.get("source_commit", ""))
    recorded_files = record.get("deployed_files")
    mismatches: list[str] = []
    comparison_known = (
        bool(recorded)
        and isinstance(recorded_files, list)
        and record.get("source_repository") == str(root)
        and record.get("overall_status") == "PASSED"
    )
    commit_exists = False
    if comparison_known:
        commit_exists = git(root, "cat-file", "-e", f"{recorded}^{{commit}}", check=False).returncode == 0
        comparison_known = commit_exists
    if comparison_known:
        if recorded_files != paths:
            comparison_known = False
        else:
            for path in paths:
                runtime_file = target / path
                source_at_commit = git(root, "show", f"{recorded}:{path}", check=False)
                if source_at_commit.returncode != 0:
                    comparison_known = False
                    break
                if not runtime_file.is_file() or runtime_file.is_symlink():
                    mismatches.append(path)
                elif runtime_file.read_bytes() != source_at_commit.stdout:
                    mismatches.append(path)

    runtime_at_recorded: bool | None = None if not comparison_known else not mismatches
    newer: bool | None
    if not commit_exists:
        newer = None
    elif recorded == head:
        newer = False
    else:
        newer = git(root, "merge-base", "--is-ancestor", recorded, head, check=False).returncode == 0

    if runtime_at_recorded is True and recorded == head:
        state = "CURRENT"
    elif runtime_at_recorded is True and newer is True:
        state = "BEHIND"
    else:
        state = "UNKNOWN"

    print(f"Deployment state: {state}")
    print(f"Recorded deployed commit: {recorded or 'unknown'}")
    print(f"Current source HEAD: {head}")
    print(
        "Runtime matches recorded commit: "
        + ("YES" if runtime_at_recorded is True else "NO" if runtime_at_recorded is False else "UNKNOWN")
    )
    print(
        "Main repository has newer commits: "
        + ("YES" if newer is True else "NO" if newer is False else "UNKNOWN")
    )
    if mismatches:
        print("Manifest file mismatches:")
        for path in mismatches:
            print(f"  {path}")
    elif comparison_known:
        print(f"Manifest file mismatches: 0 ({len(paths)} checked)")
    else:
        print("Manifest file comparison: UNKNOWN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
