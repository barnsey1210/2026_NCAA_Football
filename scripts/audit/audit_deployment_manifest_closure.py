#!/usr/bin/env python3
"""Validate that the MAIN-to-AUTO source manifest is complete and reproducible."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "deploy/source_manifest.txt"
DAILY_REGISTRY = ROOT / "config/daily_stages.json"
PUBLIC_BUILDER = ROOT / "scripts/site/build_public_site.py"
DAILY_ENTRYPOINT = ROOT / "daily_market_update.sh"
REQUIRED_RUNTIME_STATIC = {
    "v1.html",
    "data/snapshots/preseason/preseason_db.json",
}
SHADOW_STATIC_DEPENDENCIES = {
    "data/ratings/ratings_preseason_2026.csv":
        "scripts/war_room/build_war_room_market_matrix.py",
    "data/fixtures/shadow_activation_cases.json":
        "scripts/audit/audit_saturday_shadow_production_integration.py",
    "data/research/shadow_component_bridge_v1/model_artifacts.json":
        "scripts/audit/audit_saturday_shadow_production_integration.py",
    "data/research/shadow_component_bridge_v1/parity_report.json":
        "scripts/audit/audit_saturday_shadow_production_integration.py",
    "data/research/shadow_validated_models_v1/model_artifacts.json":
        "scripts/site/build_saturday_shadow_component_predictions.py",
    "data/research/historical/shadow/totals_oos_2024/enhanced_spplus_od_frozen_model_specification.csv":
        "scripts/projections/build_current_game_projection_contract.py",
}
SHADOW_GENERATED_INPUTS = {
    "data/research/shadow_live_feature_constructor/team_game_features_2026.json":
        "scripts/site/build_saturday_shadow_component_predictions.py",
    "data/ratings/market_implied_target_excluded_2026.json":
        "scripts/site/build_saturday_shadow_component_predictions.py",
    "data/ratings/market_implied_ratings_latest.csv":
        "scripts/site/build_saturday_shadow_component_predictions.py",
    "data/ratings/ratings_latest.csv":
        "scripts/site/build_saturday_shadow_component_predictions.py",
    "data/ratings/fundamental_market_rating_comparison.csv":
        "scripts/site/build_saturday_shadow_lines.py",
    "data/site/current_game_projection_contract.json":
        "scripts/site/build_saturday_shadow_lines.py",
    "data/site/matchups_view.json":
        "scripts/site/build_saturday_shadow_component_predictions.py",
    "data/site/postgame_shadow_replay.json":
        "scripts/site/build_saturday_shadow_lines.py",
    "data/site/postgame_shadow_updates.json":
        "scripts/site/build_saturday_shadow_lines.py",
    "data/site/saturday_shadow_component_predictions.json":
        "scripts/site/build_saturday_shadow_lines.py",
    "data/site/saturday_shadow_lines.json":
        "scripts/audit/audit_saturday_shadow_production_integration.py",
}


def manifest_paths(path: Path) -> list[str]:
    values = path.read_text(encoding="utf-8").splitlines()
    if any(not value for value in values):
        raise ValueError("manifest contains an empty path")
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"manifest contains duplicate paths: {duplicates}")
    return values


def resolve_registry_script(value: str) -> Path:
    candidate = ROOT / value
    if candidate.is_file():
        return candidate
    candidate = ROOT / "scripts" / value
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"daily registry script does not exist: {value}")


def local_script_imports(path: Path) -> set[str]:
    if path.suffix != ".py":
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    dependencies: set[str] = set()
    for module in modules:
        parts = module.split(".")
        if parts[0] != "scripts":
            continue
        candidate = ROOT.joinpath(*parts).with_suffix(".py")
        if not candidate.is_file():
            package = ROOT.joinpath(*parts, "__init__.py")
            if not package.is_file():
                continue
            candidate = package
        dependencies.add(candidate.relative_to(ROOT).as_posix())
    return dependencies


def public_build_static_dependencies(path: Path) -> set[str]:
    """Return repo-owned static files read or copied by build_public_site.py."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assignments: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            assignments[target.id] = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue

    dependencies: set[str] = set(REQUIRED_RUNTIME_STATIC)
    pages = assignments.get("PAGES")
    if not isinstance(pages, dict):
        raise ValueError("build_public_site.py PAGES mapping is not statically auditable")
    for source, target in pages.items():
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError("build_public_site.py PAGES contains a non-string path")
        selected = source if (ROOT / source).is_file() else target
        dependencies.add(selected)

    health_assets = assignments.get("PAGE_HEALTH_ASSETS")
    if not isinstance(health_assets, tuple) or not all(
        isinstance(value, str) for value in health_assets
    ):
        raise ValueError("build_public_site.py PAGE_HEALTH_ASSETS is not statically auditable")
    dependencies.update(health_assets)

    js_loop_found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id != "js_name":
            continue
        try:
            values = ast.literal_eval(node.iter)
        except (ValueError, TypeError):
            continue
        if isinstance(values, tuple) and all(isinstance(value, str) for value in values):
            dependencies.update(values)
            js_loop_found = True
    if not js_loop_found:
        raise ValueError("build_public_site.py JavaScript copy list is not statically auditable")
    return dependencies


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--target",
        type=Path,
        help="Optional deployed runtime whose manifest files must byte-match MAIN.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    try:
        paths = manifest_paths(args.manifest)
    except (OSError, ValueError) as exc:
        print(f"DEPLOYMENT MANIFEST CLOSURE: FAIL\n- {exc}")
        return 1
    path_set = set(paths)

    for relative in paths:
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            errors.append(f"invalid source manifest entry: {relative}")

    registry = json.loads(DAILY_REGISTRY.read_text(encoding="utf-8"))
    registry_paths: set[str] = set()
    for stage in registry["stages"]:
        for value in stage.get("scripts", []):
            try:
                resolved = resolve_registry_script(value)
            except FileNotFoundError as exc:
                errors.append(str(exc))
                continue
            relative = resolved.relative_to(ROOT).as_posix()
            registry_paths.add(relative)
            if relative not in path_set:
                errors.append(f"daily registry dependency missing from manifest: {relative}")

    import_dependencies: set[str] = set()
    for relative in paths:
        source = ROOT / relative
        if not source.is_file():
            continue
        try:
            import_dependencies.update(local_script_imports(source))
        except (OSError, SyntaxError) as exc:
            errors.append(f"cannot inspect imports for {relative}: {exc}")
    for relative in sorted(import_dependencies):
        if relative not in path_set:
            errors.append(f"local Python dependency missing from manifest: {relative}")

    try:
        public_static = public_build_static_dependencies(PUBLIC_BUILDER)
    except (OSError, SyntaxError, ValueError) as exc:
        errors.append(f"cannot inspect public build static dependencies: {exc}")
        public_static = set()
    for relative in sorted(public_static):
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            errors.append(f"public build static dependency is not a regular file: {relative}")
        elif relative not in path_set:
            errors.append(f"public build static dependency missing from manifest: {relative}")

    for relative, owner in sorted(SHADOW_STATIC_DEPENDENCIES.items()):
        source = ROOT / relative
        owner_path = ROOT / owner
        if not source.is_file() or source.is_symlink():
            errors.append(f"Shadow static dependency is not a regular file: {relative}")
        elif relative not in path_set:
            errors.append(f"Shadow static dependency missing from manifest: {relative}")
        try:
            owner_text = owner_path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot inspect Shadow dependency owner {owner}: {exc}")
        else:
            if relative not in owner_text:
                errors.append(
                    f"Shadow dependency ownership drift: {relative} is not referenced by {owner}"
                )

    for relative, owner in sorted(SHADOW_GENERATED_INPUTS.items()):
        if relative in path_set:
            errors.append(f"generated Shadow runtime input must not be deployed from MAIN: {relative}")
        owner_path = ROOT / owner
        try:
            owner_text = owner_path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot inspect generated Shadow input owner {owner}: {exc}")
        else:
            if relative not in owner_text:
                errors.append(
                    f"generated Shadow input ownership drift: {relative} is not referenced by {owner}"
                )

    public_builder_text = PUBLIC_BUILDER.read_text(encoding="utf-8")
    if "build_schedule_persistent.py" in public_builder_text:
        errors.append("AUTO-only schedule builder remains executable from public build")
    daily_text = DAILY_ENTRYPOINT.read_text(encoding="utf-8")
    for retired_stage in ("sgo_backup_pull", "sgo_backup_normalization"):
        if retired_stage in daily_text:
            errors.append(f"retired SGO stage identifier remains active: {retired_stage}")

    if args.target:
        target = args.target.resolve()
        for relative in paths:
            source = ROOT / relative
            deployed = target / relative
            if not deployed.is_file():
                errors.append(f"target missing manifest entry: {relative}")
            elif source.read_bytes() != deployed.read_bytes():
                errors.append(f"target differs from MAIN: {relative}")

    if errors:
        print("DEPLOYMENT MANIFEST CLOSURE: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("DEPLOYMENT MANIFEST CLOSURE: PASS")
    print(f"manifest_files={len(paths)}")
    print(f"daily_registry_scripts={len(registry_paths)}")
    print(f"local_script_imports={len(import_dependencies)}")
    print(f"public_static_dependencies={len(public_static)}")
    print(f"shadow_static_dependencies={len(SHADOW_STATIC_DEPENDENCIES)}")
    print(f"shadow_generated_inputs={len(SHADOW_GENERATED_INPUTS)}")
    if args.target:
        print(f"target_parity_files={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
