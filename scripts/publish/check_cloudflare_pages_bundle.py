#!/usr/bin/env python3
"""Fail-closed validation for the allowlisted Cloudflare Pages bundle."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = DEFAULT_ROOT / "scripts/publish/build_cloudflare_pages_bundle.py"
SPEC = importlib.util.spec_from_file_location("cloudflare_pages_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)

REFERENCE = re.compile(
    r"(?:src|href)\s*=\s*[\"']([^\"']+)[\"']|"
    r"fetch\(\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)
MALFORMED_CACHE_BUST = re.compile(
    r"data/site/[A-Za-z0-9_./-]+\.json\?v=[^\"'`\s<>{}]*\)\}"
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def local_reference(value: str, page: str = "") -> str | None:
    if not value or "${" in value or value.startswith(("#", "data:", "mailto:", "javascript:")):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    raw_path = unquote(parsed.path)
    if not raw_path or raw_path.endswith("/"):
        return None
    if raw_path.startswith("/"):
        resolved = Path(raw_path.lstrip("/"))
    else:
        resolved = Path(page).parent / raw_path
    normalized: list[str] = []
    for part in resolved.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not normalized:
                return None
            normalized.pop()
        else:
            normalized.append(part)
    return Path(*normalized).as_posix() if normalized else None


def untracked_inputs(root: Path, paths: list[Path]) -> list[str]:
    requested = {path.relative_to(root).as_posix() for path in paths}
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--", *sorted(requested)],
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = {line for line in completed.stdout.splitlines() if line}
    return sorted(requested - tracked)


def validate(
    root: Path,
    manifest_path: str,
    output_value: str | None = None,
    allow_untracked_inputs: bool = False,
) -> list[str]:
    root = root.resolve()
    manifest_source, manifest = builder.load_manifest(root, manifest_path)
    output = builder.safe_output(root, output_value, manifest)
    if output.is_symlink() or not output.is_dir():
        raise RuntimeError(f"Cloudflare Pages bundle is missing or symlinked: {output}")
    planned = builder.planned_files(root, manifest)
    if manifest.get("require_git_tracked_inputs") and not allow_untracked_inputs:
        missing_from_git = untracked_inputs(
            root, [manifest_source, *(source for source, _ in planned)]
        )
        if missing_from_git:
            raise RuntimeError(f"manifest inputs are not Git-tracked: {missing_from_git}")
    expected = {target.as_posix(): source for source, target in planned}
    actual: dict[str, Path] = {}
    for path in output.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"bundle contains symlink: {path.relative_to(output)}")
        if path.is_file():
            actual[path.relative_to(output).as_posix()] = path
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        raise RuntimeError(f"bundle is missing allowlisted files: {missing[:10]}")
    if extra:
        raise RuntimeError(f"bundle contains non-allowlisted files: {extra[:10]}")
    for relative, source in expected.items():
        body = builder.materialized_bytes(source, Path(relative), manifest)
        if body is None:
            if digest(source) != digest(actual[relative]):
                raise RuntimeError(f"bundle hash mismatch: {relative}")
        elif actual[relative].read_bytes() != body:
            raise RuntimeError(f"bundle compact JSON mismatch: {relative}")
    for page in manifest["required_pages"]:
        if page not in actual:
            raise RuntimeError(f"required public page is missing: {page}")
    top_level = {Path(value).parts[0] for value in actual}
    allowed = set(manifest["allowed_top_level"])
    if top_level - allowed:
        raise RuntimeError(f"unexpected top-level bundle content: {sorted(top_level - allowed)}")
    forbidden = set(manifest["forbidden_top_level"])
    if top_level & forbidden:
        raise RuntimeError(f"forbidden repository content leaked: {sorted(top_level & forbidden)}")
    if "_redirects" in actual:
        raise RuntimeError("SPA/redirect fallback is not approved for Phase 1")
    for required in (
        "data/snapshots/preseason/preseason_db.json",
        "data/research/shadow_value_confidence/summary.json",
    ):
        if required not in actual:
            raise RuntimeError(f"required non-data/site dependency is missing: {required}")
    for relative, path in actual.items():
        if path.suffix.lower() not in {".html", ".js", ".css"}:
            continue
        text = path.read_text(errors="replace")
        if MALFORMED_CACHE_BUST.search(text):
            raise RuntimeError(f"malformed cache-busting URL found: {relative}")
        for match in REFERENCE.finditer(text):
            reference = local_reference(match.group(1) or match.group(2), relative)
            if (
                reference
                and reference not in actual
                and reference not in set(manifest.get("optional_references", []))
            ):
                raise RuntimeError(f"missing referenced public asset: {relative} -> {reference}")
    total = sum(path.stat().st_size for path in actual.values())
    if any(path.stat().st_size > int(manifest["max_file_bytes"]) for path in actual.values()):
        raise RuntimeError("bundle contains an unexpectedly large file")
    if total > int(manifest["max_total_bytes"]):
        raise RuntimeError("bundle exceeds total size limit")
    messages = [
        f"PASS: {len(actual)} files match the explicit allowlist and source hashes",
        "PASS: no symlinks, repository leakage, SPA fallback, or malformed cache URLs",
        "PASS: required pages, referenced assets, and non-data/site dependencies exist",
    ]
    for message in messages:
        print(message)
    return messages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--manifest", default="config/cloudflare_pages_manifest.json")
    parser.add_argument("--output")
    parser.add_argument(
        "--allow-untracked-inputs",
        action="store_true",
        help="Pre-commit review only; production Pages validation remains strict by default.",
    )
    args = parser.parse_args()
    validate(
        Path(args.repo_root),
        args.manifest,
        args.output,
        allow_untracked_inputs=args.allow_untracked_inputs,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
