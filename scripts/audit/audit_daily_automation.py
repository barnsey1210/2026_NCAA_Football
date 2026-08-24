#!/usr/bin/env python3
"""Static audit for the canonical daily orchestration and thin launcher."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


REQUIRED_REGISTRY_FIELDS = {
    "id",
    "name",
    "order",
    "required",
    "external_network",
    "email_dependency",
    "publication_dependency",
    "entrypoint",
    "scripts",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def active_shell_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def source_coverage(
    stages: list[dict[str, object]],
    source: str,
    repo_root: Path,
    runtime_root: Path,
) -> dict[str, object]:
    registered = [str(script) for stage in stages for script in stage["scripts"]]
    tracked = [script for script in registered if (repo_root / script).is_file()]
    runtime_only = [
        script
        for script in registered
        if not (repo_root / script).is_file() and (runtime_root / script).is_file()
    ]

    fallback_pairs = re.findall(
        r'run_py\s+"([^"]+)"(?:\s+"([^"]+)")?',
        source,
    )
    fallback_by_primary = {primary: fallback for primary, fallback in fallback_pairs if fallback}
    unresolved = []
    for script in registered:
        if (repo_root / script).is_file() or (runtime_root / script).is_file():
            continue
        fallback = fallback_by_primary.get(script)
        if fallback and (runtime_root / fallback).is_file():
            continue
        unresolved.append(script)

    source_hashes: dict[str, list[str]] = {}
    for path in repo_root.rglob("*"):
        if (
            path.is_file()
            and path.suffix in {".py", ".sh"}
            and ".git" not in path.parts
        ):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            source_hashes.setdefault(digest, []).append(path.relative_to(repo_root).as_posix())
    duplicate_mappings = []
    for script in tracked:
        digest = hashlib.sha256((repo_root / script).read_bytes()).hexdigest()
        equivalents = sorted(path for path in source_hashes[digest] if path != script)
        if equivalents:
            duplicate_mappings.append({"registered": script, "equivalent_paths": equivalents})

    active_fallbacks = [
        {
            "primary": primary,
            "fallback": fallback,
            "fallback_exists_in_runtime": (runtime_root / fallback).is_file(),
        }
        for primary, fallback in fallback_pairs
        if fallback
    ]
    total = len(registered)
    return {
        "registered_scripts": total,
        "registered_scripts_tracked_in_repo": len(tracked),
        "registered_scripts_runtime_only": len(runtime_only),
        "registered_runtime_only_paths": sorted(runtime_only),
        "duplicate_path_mapping_count": len(duplicate_mappings),
        "duplicate_path_mappings": duplicate_mappings,
        "unresolved_script_count": len(unresolved),
        "unresolved_scripts": sorted(unresolved),
        "active_legacy_fallback_count": len(active_fallbacks),
        "active_legacy_fallbacks": active_fallbacks,
        "repository_completeness_percent": round((len(tracked) / total * 100.0) if total else 100.0, 2),
    }


def audit(
    orchestrator: Path,
    registry_path: Path,
    launcher: Path,
    repo_root: Path | None = None,
    runtime_root: Path = Path("/Users/jameslindesmith/NCAAF_AUTO"),
) -> dict[str, object]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    stages = registry.get("stages", [])
    require(isinstance(stages, list) and stages, "registry has no stages")
    for stage in stages:
        require(REQUIRED_REGISTRY_FIELDS <= set(stage), f"incomplete registry stage: {stage.get('id')}")
        require(isinstance(stage["scripts"], list) and stage["scripts"], f"stage has no scripts: {stage.get('id')}")

    orders = [stage["order"] for stage in stages]
    ids = [stage["id"] for stage in stages]
    require(orders == sorted(orders), "registry stages are not in order")
    require(len(ids) == len(set(ids)), "duplicate registry stage id")

    source = orchestrator.read_text(encoding="utf-8")
    markers = re.findall(r"^\s*# STAGE: ([a-z0-9_]+)\s*$", source, flags=re.MULTILINE)
    require(markers == ids, f"orchestrator markers differ from registry: {markers}")

    position = {stage_id: source.index(f"# STAGE: {stage_id}") for stage_id in ids}
    helper_owned_scripts = {
        "ratings_refresh": {
            "scripts/ratings/test_rating_sources.py",
            "scripts/ratings/parse_rating_source_tables.py",
            "scripts/ratings/accept_live_rating_candidates_with_status.py",
        },
    }
    indirect_owner_scripts = {
        "site_build": {
            "scripts/site/build_war_room_page.py": "scripts/site/build_public_site.py",
        },
    }
    for index, stage in enumerate(stages):
        start = position[stage["id"]]
        end = position[stages[index + 1]["id"]] if index + 1 < len(stages) else len(source)
        stage_source = source[start:end]
        for script in stage["scripts"]:
            helper_owned = script in helper_owned_scripts.get(stage["id"], set())
            if helper_owned:
                require(
                    "refresh_live_rating_source" in stage_source and script in source[:start],
                    f"registered helper script is not owned by its stage: {stage['id']} -> {script}",
                )
            elif script in indirect_owner_scripts.get(stage["id"], {}):
                owner = repo_root / indirect_owner_scripts[stage["id"]][script] if repo_root else registry_path.resolve().parents[1] / indirect_owner_scripts[stage["id"]][script]
                require(
                    owner.is_file() and script in owner.read_text(encoding="utf-8"),
                    f"registered indirect script is not owned by its stage builder: {stage['id']} -> {script}",
                )
            else:
                require(script in stage_source, f"registered script is outside its stage: {stage['id']} -> {script}")
    ordering_rules = [
        ("email_build", "email_regression"),
        ("email_regression", "email_send"),
        ("ratings_refresh", "ratings_normalization"),
        ("ratings_normalization", "projections"),
        ("projections", "shadow_models"),
        ("site_build", "site_validation"),
        ("site_validation", "publication"),
    ]
    for first, second in ordering_rules:
        require(position[first] < position[second], f"stage order violation: {first} before {second}")

    require(source.index("NCAAF_SEND_EMAIL:-1") > position["email_regression"], "email gate precedes regression")
    require(source.index("send_daily_betting_angles_email.py") > position["email_regression"], "email send precedes regression")
    require("EMAIL_REGRESSION_PASSED=0" in source, "email regression failure is not recorded")
    require(
        "continuing independent production stages" in source,
        "email-only failure can still terminate independent production stages",
    )
    require(
        source.index('if [ "$EMAIL_REGRESSION_PASSED" -ne 1 ]') > position["email_send"],
        "email send is not blocked after regression failure",
    )
    require(source.index("NCAAF_AUTO_PUBLISH:-1") > position["site_validation"], "publication gate precedes validation")
    require(source.index("publish_site.sh --push") > position["site_validation"], "publisher precedes validation")
    require("NCAAF_SEND_EMAIL=0: daily email build completed" in source, "email-disable behavior not explicit")
    require("NCAAF_AUTO_PUBLISH=0: validated V2 build" in source, "publication-disable behavior not explicit")

    active = active_shell_lines(source)
    forbidden_active = (
        "index_auto_market.html \"$ICLOUD",
        "cp index_auto_market.html",
        "cp index.html",
        "v1.html",
        "install_",
    )
    for line in active:
        require(not any(token in line for token in forbidden_active), f"active legacy V1 behavior: {line}")

    launcher_source = launcher.read_text(encoding="utf-8")
    launcher_active = active_shell_lines(launcher_source)
    require("NCAAF_AUTO/daily_market_update.sh" in launcher_source, "launcher does not invoke runtime orchestration")
    require(sum("daily_market_update.sh" in line and "exec" in line for line in launcher_active) == 1,
            "launcher must have one canonical exec entry point")
    launcher_forbidden = (
        "pull_",
        "build_",
        "append_",
        "publish_site",
        "send_daily",
        "rsync",
        "git pull",
    )
    for line in launcher_active:
        require(not any(token in line for token in launcher_forbidden), f"launcher contains business logic: {line}")

    require("daily_run_status.py" in source, "structured run-status writer is not integrated")
    require("data/control/daily_run_status.json" in source, "canonical run-status output is missing")

    if repo_root is None:
        repo_root = registry_path.resolve().parents[1]
    result = {
        "result": "PASSED",
        "stages_checked": len(stages),
        "stage_order_rules_checked": len(ordering_rules),
        "launcher": str(launcher),
        "canonical_entrypoint": str(orchestrator),
        "legacy_v1_active": False,
        "email_disable_preserves_build": True,
        "publication_disable_preserves_build_and_validation": True,
    }
    result.update(source_coverage(stages, source, repo_root.resolve(), runtime_root.resolve()))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orchestrator", type=Path, default=Path("daily_market_update.sh"))
    parser.add_argument("--registry", type=Path, default=Path("config/daily_stages.json"))
    parser.add_argument(
        "--launcher",
        type=Path,
        default=Path.home() / "Scripts/NCAAF/daily_market_update.sh",
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--runtime-root", type=Path, default=Path("/Users/jameslindesmith/NCAAF_AUTO"))
    args = parser.parse_args()
    result = audit(
        args.orchestrator,
        args.registry,
        args.launcher,
        repo_root=args.repo_root,
        runtime_root=args.runtime_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
