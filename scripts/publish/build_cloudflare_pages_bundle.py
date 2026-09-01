#!/usr/bin/env python3
"""Materialize the explicitly allowlisted Cloudflare Pages static bundle."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Iterable

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path("config/cloudflare_pages_manifest.json")


def relative_path(value: str, label: str) -> Path:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"unsafe {label} path: {value!r}")
    return path


def safe_source(root: Path, value: str) -> tuple[Path, Path]:
    relative = relative_path(value, "source")
    source = root / relative
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RuntimeError(f"symlink input is forbidden: {relative}")
    if not source.is_file():
        raise RuntimeError(f"required artifact is missing: {relative}")
    return source, relative


def safe_output(root: Path, value: str | None, manifest: dict[str, Any]) -> Path:
    relative = relative_path(value or manifest["output_directory"], "output")
    if not relative.parts or relative.parts[0] != "build":
        raise RuntimeError("output must be located under the repository build directory")
    output = root / relative
    if output == root or root not in output.parents:
        raise RuntimeError("output escapes repository root")
    return output


def load_manifest(root: Path, value: str) -> tuple[Path, dict[str, Any]]:
    path, _ = safe_source(root, value)
    manifest = json.loads(path.read_text())
    if manifest.get("schema_version") != 1:
        raise RuntimeError("unsupported Cloudflare Pages manifest schema")
    return path, manifest


def tree_files(root: Path, entry: dict[str, Any]) -> Iterable[tuple[Path, Path]]:
    source_relative = relative_path(entry["source"], "tree source")
    target_relative = relative_path(entry["target"], "tree target")
    source_root = root / source_relative
    if source_root.is_symlink() or not source_root.is_dir():
        raise RuntimeError(f"required artifact tree is missing or symlinked: {source_relative}")
    extensions = {str(value).lower() for value in entry["allowed_extensions"]}
    for source in sorted(source_root.rglob("*")):
        if source.is_symlink():
            raise RuntimeError(f"symlink input is forbidden: {source.relative_to(root)}")
        if source.is_dir():
            continue
        if source.suffix.lower() not in extensions:
            continue
        yield source, target_relative / source.relative_to(source_root)


def planned_files(root: Path, manifest: dict[str, Any]) -> list[tuple[Path, Path]]:
    planned: list[tuple[Path, Path]] = []
    for value in manifest["files"]:
        source, relative = safe_source(root, value)
        planned.append((source, relative))
    for entry in manifest.get("mapped_files", []):
        source, _ = safe_source(root, entry["source"])
        planned.append((source, relative_path(entry["target"], "target")))
    for entry in manifest.get("directory_trees", []):
        planned.extend(tree_files(root, entry))
    targets = [target.as_posix() for _, target in planned]
    if len(targets) != len(set(targets)):
        raise RuntimeError("manifest contains duplicate output paths")
    return planned


def build(root: Path, manifest_path: str, output_value: str | None = None) -> dict[str, int]:
    root = root.resolve()
    _, manifest = load_manifest(root, manifest_path)
    output = safe_output(root, output_value, manifest)
    planned = planned_files(root, manifest)
    maximum_file = int(manifest["max_file_bytes"])
    maximum_total = int(manifest["max_total_bytes"])
    total = 0
    for source, target in planned:
        size = source.stat().st_size
        if size > maximum_file:
            raise RuntimeError(f"public artifact exceeds file limit: {target} ({size} bytes)")
        total += size
    if total > maximum_total:
        raise RuntimeError(f"public bundle exceeds total limit: {total} bytes")
    if output.exists():
        if output.is_symlink():
            raise RuntimeError(f"refusing to replace symlink output: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for source, target in planned:
        destination = output / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)
    print(f"Built Cloudflare Pages bundle: {len(planned)} files, {total} bytes, {output}")
    return {"files": len(planned), "bytes": total}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output")
    args = parser.parse_args()
    build(Path(args.repo_root), args.manifest, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
