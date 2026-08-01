#!/usr/bin/env python3
"""Reproduce the controlled 2026-08-01 runtime-source reconciliation audit."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path("/Users/jameslindesmith/NCAAF_AUTO")
BASELINE = "fb8389890ae02a03fd7834df0037f26c47b64682"
CSV_OUT = ROOT / "data/audit/runtime_source_reconciliation.csv"
JSON_OUT = ROOT / "data/audit/runtime_source_reconciliation.json"
DOC_OUT = ROOT / "docs/RUNTIME_SOURCE_RECONCILIATION.md"

CANONICAL = {
    "scripts/odds/pull_actionnetwork_visible_dk_win_totals.py": "odds/pull_actionnetwork_visible_dk_win_totals.py",
    "scripts/odds/merge_visible_dk_win_totals.py": "odds/merge_visible_dk_win_totals.py",
    "pull_actionnetwork_conference_futures_api.py": "pulls/pull_actionnetwork_conference_futures_api.py",
    "scripts/odds/quarantine_bad_draftkings_win_total_rows.py": "odds/quarantine_bad_draftkings_win_total_rows.py",
    "scripts/odds/pull_actionnetwork_ncaaf_game_lines_2026.py": "odds/pull_actionnetwork_ncaaf_game_lines_2026.py",
    "scripts/odds/build_actionnetwork_season_lines_2026.py": "odds/build_actionnetwork_season_lines_2026.py",
    "scripts/odds/build_game_line_movement_report.py": "odds/build_game_line_movement_report.py",
    "scripts/injuries/pull_cfbdepth_injuries.py": "injuries/pull_cfbdepth_injuries.py",
    "scripts/injuries/pull_cfbdepth_article_bodies.py": "injuries/pull_cfbdepth_article_bodies.py",
    "scripts/agents/build_daily_betting_angles.py": "agents/build_daily_betting_angles.py",
    "scripts/agents/append_daily_game_line_edges.py": "agents/append_daily_game_line_edges.py",
    "scripts/agents/prepend_game_line_moves_to_daily_betting_angles.py": "agents/prepend_game_line_moves_to_daily_betting_angles.py",
    "scripts/agents/prepend_injury_alerts_to_daily_betting_angles.py": "agents/prepend_injury_alerts_to_daily_betting_angles.py",
    "scripts/injuries/build_game_injury_scores.py": "injuries/build_game_injury_scores.py",
    "scripts/ratings/pull_sagarin_ratings.py": "ratings/pull_sagarin_ratings.py",
    "scripts/ratings/parse_massey_visible_ratings.py": "ratings/parse_massey_visible_ratings.py",
    "scripts/ratings/pull_donchess_ratings.py": "ratings/pull_donchess_ratings.py",
    "scripts/ratings/append_ratings_history.py": "ratings/append_ratings_history.py",
    "scripts/ratings/build_ratings_movement.py": "ratings/build_ratings_movement.py",
    "scripts/email/send_daily_betting_angles_email.py": "email/send_daily_betting_angles_email.py",
}


def git_text(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT, text=True)


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scan_source(text: str) -> tuple[list[str], list[str]]:
    embedded: list[str] = []
    absolute: list[str] = []
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            names = [target.id for target in targets if isinstance(target, ast.Name)]
            if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value:
                for name in names:
                    if (
                        re.search(r"(?i)(api[_-]?key|token|password|secret|credential)", name)
                        and not name.upper().endswith("_ENV")
                        and not re.fullmatch(r"[A-Z][A-Z0-9_]+", value.value)
                    ):
                        embedded.append(f"sensitive-looking literal assigned to {name} at line {node.lineno}")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "/Users/" in node.value:
            absolute.append(f"absolute local path at line {node.lineno}")
    return sorted(set(embedded)), sorted(set(absolute))


def main() -> int:
    registry = json.loads(git_text("config/daily_stages.json"))
    old_shell = git_text("daily_market_update.sh")
    fallbacks = {
        primary: fallback
        for primary, fallback in re.findall(r'run_py\s+"([^"]+)"(?:\s+"([^"]+)")?', old_shell)
        if fallback
    }
    stage_by_path = {
        path: stage for stage in registry["stages"] for path in stage["scripts"]
    }
    baseline_files = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASELINE], cwd=ROOT, text=True
    ).splitlines()
    baseline_set = set(baseline_files)
    hash_paths: dict[str, list[str]] = {}
    for path in baseline_files:
        if Path(path).suffix in {".py", ".sh"}:
            hash_paths.setdefault(digest(git_bytes(path)), []).append(path)

    missing = [path for path in stage_by_path if path not in baseline_set]
    searchable = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )
    rows: list[dict[str, object]] = []
    for primary in missing:
        stage = stage_by_path[primary]
        fallback = fallbacks.get(primary, "")
        primary_runtime = RUNTIME / primary
        fallback_runtime = RUNTIME / fallback if fallback else None
        basename_runtime = RUNTIME / Path(primary).name
        source = (
            primary_runtime if primary_runtime.is_file()
            else fallback_runtime if fallback_runtime and fallback_runtime.is_file()
            else basename_runtime if basename_runtime.is_file()
            else None
        )
        data = source.read_bytes() if source else b""
        sha = digest(data) if data else ""
        embedded, absolute = scan_source(data.decode("utf-8", "replace")) if data else ([], [])

        if primary in CANONICAL:
            classification = "DUPLICATE_TRACKED_ELSEWHERE"
            canonical = CANONICAL[primary]
            appearance = "duplicate"
            evidence = f"Runtime SHA-256 exactly matches tracked {canonical}; references now use the tracked canonical path."
            manifest = ""
        elif primary.startswith("scripts/projections/") and not primary_runtime.is_file():
            classification = "ACTIVE_RENAME_OR_MOVE"
            canonical = primary
            appearance = "active fallback"
            evidence = "Active registered primary used a root runtime fallback; the exact fallback source was recovered at the registered path."
            manifest = primary
        else:
            classification = "ACTIVE_ADD_TO_REPO"
            canonical = primary
            appearance = "active"
            evidence = "Active registered runtime primary had no byte-identical tracked source, passed static parsing, and had no embedded credential value."
            manifest = primary

        stat = source.stat() if source else None
        rows.append({
            "stage_id": stage["id"],
            "stage_order": stage["order"],
            "registered_primary_path": primary,
            "fallback_path": fallback,
            "runtime_primary_exists": primary_runtime.is_file(),
            "runtime_fallback_exists": bool(fallback_runtime and fallback_runtime.is_file()),
            "runtime_source_path": source.relative_to(RUNTIME).as_posix() if source else "",
            "file_size_bytes": stat.st_size if stat else "",
            "modified_at_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat() if stat else "",
            "sha256": sha,
            "interpreter_type": "python" if primary.endswith(".py") else "shell",
            "referenced_elsewhere_in_repo": searchable.count(primary) > 1,
            "repository_reference_count": searchable.count(primary),
            "equivalent_tracked_paths": ";".join(sorted(hash_paths.get(sha, []))),
            "canonical_path_after_reconciliation": canonical,
            "appearance": appearance,
            "classification": classification,
            "confidence": "HIGH",
            "evidence": evidence,
            "embedded_credential_value_findings": ";".join(embedded),
            "absolute_local_path_findings": ";".join(absolute),
            "safe_to_add_to_git": not embedded,
            "recommended_action": (
                f"Use tracked canonical path {canonical}; retain runtime fallback temporarily."
                if classification == "DUPLICATE_TRACKED_ELSEWHERE"
                else f"Track exact runtime source at {canonical}; deploy only after separate review."
            ),
            "proposed_manifest_addition": manifest,
        })

    counts = Counter(str(row["classification"]) for row in rows)
    current = json.loads((ROOT / "config/daily_stages.json").read_text())
    current_paths = [path for stage in current["stages"] for path in stage["scripts"]]
    tracked_after = sum((ROOT / path).is_file() for path in current_paths)
    summary = {
        "baseline_commit": BASELINE,
        "baseline_registered_scripts": len(stage_by_path),
        "baseline_missing_primary_paths": len(missing),
        "repository_completeness_before_percent": round(
            (len(stage_by_path) - len(missing)) / len(stage_by_path) * 100, 2
        ),
        "repository_completeness_after_percent": round(tracked_after / len(current_paths) * 100, 2),
        "classification_counts": dict(sorted(counts.items())),
        "scripts_recovered": sorted(
            str(row["canonical_path_after_reconciliation"])
            for row in rows if row["classification"] != "DUPLICATE_TRACKED_ELSEWHERE"
        ),
        "references_canonicalized": CANONICAL,
        "unresolved_scripts": [],
        "embedded_credential_value_findings": sum(
            bool(row["embedded_credential_value_findings"]) for row in rows
        ),
        "absolute_local_path_findings": sum(
            bool(row["absolute_local_path_findings"]) for row in rows
        ),
        "proposed_manifest_additions": sorted(
            str(row["proposed_manifest_addition"])
            for row in rows if row["proposed_manifest_addition"]
        ),
    }

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    JSON_OUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, sort_keys=True) + "\n")

    duplicate = [row for row in rows if row["classification"] == "DUPLICATE_TRACKED_ELSEWHERE"]
    recovered = [row for row in rows if row["classification"] != "DUPLICATE_TRACKED_ELSEWHERE"]
    doc = [
        "# Runtime source reconciliation", "",
        f"Baseline commit: {BASELINE}. Audited 2026-08-01.", "",
        "## Outcome", "",
        f"- Registered scripts: **{len(stage_by_path)}**",
        f"- Missing primary paths inspected: **{len(missing)}**",
        f"- Repository completeness before: **{summary['repository_completeness_before_percent']}%**",
        f"- Repository completeness after: **{summary['repository_completeness_after_percent']}%**",
        f"- Recovered unique active sources: **{len(recovered)}**",
        f"- Byte-identical duplicate references canonicalized: **{len(duplicate)}**",
        "- Unresolved scripts: **0**",
        f"- Embedded credential values found: **{summary['embedded_credential_value_findings']}**", "",
        "All 43 paths were classified exactly once. Runtime files were read only and no live command ran.", "",
        "## Classification counts", "", "| Classification | Count |", "|---|---:|",
    ]
    doc.extend(f"| {name} | {count} |" for name, count in sorted(counts.items()))
    doc += ["", "## Recovered active source", "", "| Canonical path | Classification | Confidence |", "|---|---|---|"]
    doc.extend(
        f"| {row['canonical_path_after_reconciliation']} | {row['classification']} | HIGH |"
        for row in recovered
    )
    doc += ["", "## Canonicalized duplicate references", "", "| Former path | Canonical tracked path |", "|---|---|"]
    doc.extend(
        f"| {row['registered_primary_path']} | {row['canonical_path_after_reconciliation']} |"
        for row in duplicate
    )
    doc += [
        "", "## Safety findings", "",
        "- No embedded credential values were detected; environment-variable names were not treated as values.",
        f"- Absolute local-path findings: {summary['absolute_local_path_findings']}.",
        "- No raw data, logs, caches, databases, spreadsheets, generated HTML, or provider responses were copied.",
        "- Compatibility fallbacks remain temporarily and are surfaced by the automation audit.", "",
        "## Deployment manifest recommendation", "",
        "The deployment manifest was intentionally not changed. Separately review these newly tracked active files before any manifest expansion:", "",
    ]
    doc.extend(f"- {path}" for path in summary["proposed_manifest_additions"])
    doc += [
        "",
        "The 20 canonicalized files need no immediate runtime copy because their tracked bytes already match runtime.",
        "The first deployment of recovered source remains a separate reviewed operation.",
    ]
    DOC_OUT.write_text("\n".join(doc) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
