#!/usr/bin/env python3
"""Static audit for the canonical daily orchestration and thin launcher."""

from __future__ import annotations

import argparse
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


def audit(orchestrator: Path, registry_path: Path, launcher: Path) -> dict[str, object]:
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
    for index, stage in enumerate(stages):
        start = position[stage["id"]]
        end = position[stages[index + 1]["id"]] if index + 1 < len(stages) else len(source)
        stage_source = source[start:end]
        for script in stage["scripts"]:
            require(script in stage_source, f"registered script is outside its stage: {stage['id']} -> {script}")
    ordering_rules = [
        ("sgo_pull", "sgo_normalization"),
        ("sgo_normalization", "game_line_history"),
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

    return {
        "result": "PASSED",
        "stages_checked": len(stages),
        "stage_order_rules_checked": len(ordering_rules),
        "launcher": str(launcher),
        "canonical_entrypoint": str(orchestrator),
        "legacy_v1_active": False,
        "email_disable_preserves_build": True,
        "publication_disable_preserves_build_and_validation": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orchestrator", type=Path, default=Path("daily_market_update.sh"))
    parser.add_argument("--registry", type=Path, default=Path("config/daily_stages.json"))
    parser.add_argument(
        "--launcher",
        type=Path,
        default=Path.home() / "Scripts/NCAAF/daily_market_update.sh",
    )
    args = parser.parse_args()
    result = audit(args.orchestrator, args.registry, args.launcher)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
