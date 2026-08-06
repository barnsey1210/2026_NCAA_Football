#!/usr/bin/env python3
"""Build one shared, deterministic CFBDepth team asset for site consumers.

This builder reads canonical CFBDepth outputs only. It does not alter HTML,
Matchups records, team pages, or the existing matchup drawer.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT_IMPORT = Path(__file__).resolve().parents[2]
if str(ROOT_IMPORT) not in sys.path:
    sys.path.insert(0, str(ROOT_IMPORT))
try:
    from scripts.lib.ncaaf_config import canonical_team
except ModuleNotFoundError:
    try:
        from lib.ncaaf_config import canonical_team
    except ModuleNotFoundError:
        def canonical_team(value: Any) -> str:
            return str(value or "").strip()

TEAM_FILES = {
    "air": "cfbdepth_air_ratings_2026.csv",
    "coaching": "cfbdepth_coaching_impacts_2026.csv",
    "depth": "cfbdepth_depth_grades_2026.csv",
    "rotation": "cfbdepth_rotation_talent_2026.csv",
    "injury": "cfbdepth_team_injury_impact_2026.csv",
    "offense_profile": "cfbdepth_offense_profile_2026.csv",
    "defense_profile": "cfbdepth_defense_profile_2026.csv",
}
POSITION_FILE = "cfbdepth_position_groups_2026.csv"
TOP_PLAYERS_FILE = "cfbdepth_team_top_players_2026.json"
PLAYERS_FILE = "cfbdepth_players_2026.csv"

SOURCE_TO_SITE_ALIASES = {
    "FIU": "Florida International",
    "Louisiana-Monroe": "UL-Monroe",
    "Miami FL": "Miami-FL",
    "Miami OH": "Miami-OH",
    "UCF": "Central Florida",
    "UMass": "Massachusetts",
}


def clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
        lower = value.lower()
        if lower in {"nan", "none", "null"}:
            return None
        try:
            number = float(value)
        except ValueError:
            return value
        return int(number) if number.is_integer() else round(number, 4)
    if isinstance(value, float):
        return round(value, 4)
    return value


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Missing canonical input: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def resolve_team_name(raw_team: Any, site_by_canonical: dict[str, str]) -> str:
    raw = str(clean(raw_team) or "").strip()
    canonical = canonical_team(raw)
    return site_by_canonical.get(canonical, raw)


def index_by_team(rows: list[dict[str, Any]], path: Path, site_by_canonical: dict[str, str]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for row in rows:
        team = clean(row.get("team"))
        if not team:
            raise SystemExit(f"{path}: row missing team")
        team = resolve_team_name(team, site_by_canonical)
        if team in indexed:
            duplicates.append(team)
        indexed[team] = {key: value for key, value in row.items() if key != "team"}
    if duplicates:
        raise SystemExit(f"{path}: duplicate teams: {sorted(set(duplicates))[:10]}")
    return indexed


def load_site_teams(index_path: Path) -> set[str]:
    if not index_path.exists():
        raise SystemExit(f"Missing site source: {index_path}")
    html = index_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise SystemExit(f"Missing embedded DB in {index_path}")
    payload = json.loads(match.group(1))
    teams = {
        str(row.get("team")).strip()
        for row in payload.get("teams", [])
        if str(row.get("team") or "").strip()
    }
    if not teams:
        raise SystemExit(f"No site teams found in {index_path}")
    return teams


def load_position_groups(path: Path, site_by_canonical: dict[str, str]) -> dict[str, dict[str, dict[str, Any]]]:
    rows = read_csv(path)
    output: dict[str, dict[str, dict[str, Any]]] = {}
    seen: set[tuple[str, str]] = set()
    for row in rows:
        team = resolve_team_name(row.get("team"), site_by_canonical)
        position = str(clean(row.get("position_group")) or "")
        if not team or not position:
            raise SystemExit(f"{path}: row missing team or position_group")
        key = (team, position)
        if key in seen:
            raise SystemExit(f"{path}: duplicate team-position row: {key}")
        seen.add(key)
        output.setdefault(team, {})[position] = {
            field: value
            for field, value in row.items()
            if field not in {"team", "position_group"}
        }
    return output


def load_top_players(path: Path, site_by_canonical: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        raise SystemExit(f"Missing canonical input: {path}")
    payload = json.loads(path.read_text())
    teams = payload.get("teams")
    if not isinstance(teams, dict):
        raise SystemExit(f"{path}: expected top-level teams object")
    resolved: dict[str, list[dict[str, Any]]] = {}
    for team, players in teams.items():
        resolved[resolve_team_name(team, site_by_canonical)] = players
    return resolved


def player_counts(path: Path, site_by_canonical: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in read_csv(path):
        team = resolve_team_name(row.get("team"), site_by_canonical)
        if team:
            counts[team] = counts.get(team, 0) + 1
    return counts


def first_present(row: dict[str, Any] | None, candidates: tuple[str, ...]) -> Any:
    if not row:
        return None
    for key in candidates:
        value = row.get(key)
        if value is not None:
            return value
    return None


def summary_for(team_record: dict[str, Any]) -> dict[str, Any]:
    """Expose a small, stable summary suitable for future compact UI consumers."""
    air = team_record.get("air") or {}
    depth = team_record.get("depth") or {}
    rotation = team_record.get("rotation") or {}
    injury = team_record.get("injury") or {}
    positions = team_record.get("position_groups") or {}

    position_overall = {
        position: first_present(values, ("rotation_overall_avg", "overall_avg", "overall"))
        for position, values in positions.items()
    }
    available_position_values = {
        position: value for position, value in position_overall.items() if isinstance(value, (int, float))
    }
    strongest = max(available_position_values, key=available_position_values.get) if available_position_values else None
    weakest = min(available_position_values, key=available_position_values.get) if available_position_values else None

    return {
        "air_overall": first_present(air, ("air", "air_rating", "overall", "overall_rating")),
        "air_offense": first_present(air, ("air_offense", "offense", "offense_rating")),
        "air_defense": first_present(air, ("air_defense", "defense", "defense_rating")),
        "depth_overall": first_present(depth, ("depth", "depth_grade", "overall", "overall_grade")),
        "rotation_overall": first_present(rotation, ("rotation", "rotation_talent", "overall", "overall_rating")),
        "injury_count": first_present(injury, ("injury_number", "injury_count", "injuries", "players_injured", "total_injuries")),
        "injury_impact": first_present(injury, ("injury_impact", "impact", "total_impact", "impact_points")),
        "strongest_position_group": strongest,
        "strongest_position_rating": available_position_values.get(strongest) if strongest else None,
        "weakest_position_group": weakest,
        "weakest_position_rating": available_position_values.get(weakest) if weakest else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the shared CFBDepth team site asset.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--as-of", default="2026-08-05")
    parser.add_argument("--index", default="v1.html", help="Site HTML containing the embedded team DB")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    canonical = root / "data/canonical"
    out_path = root / "data/site/cfbdepth_teams_2026.json"
    audit_path = root / "data/audits/cfbdepth_team_asset_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    site_teams = load_site_teams(root / args.index)
    site_by_canonical = {canonical_team(team): team for team in site_teams}
    for source_name, site_name in SOURCE_TO_SITE_ALIASES.items():
        if site_name in site_teams:
            site_by_canonical[canonical_team(source_name)] = site_name

    datasets: dict[str, dict[str, dict[str, Any]]] = {}
    all_teams: set[str] = set()
    for section, filename in TEAM_FILES.items():
        path = canonical / filename
        datasets[section] = index_by_team(read_csv(path), path, site_by_canonical)
        all_teams.update(datasets[section])

    positions = load_position_groups(canonical / POSITION_FILE, site_by_canonical)
    top_players = load_top_players(canonical / TOP_PLAYERS_FILE, site_by_canonical)
    counts = player_counts(canonical / PLAYERS_FILE, site_by_canonical)
    all_teams.update(positions)
    all_teams.update(top_players)
    all_teams.update(counts)

    teams_payload: dict[str, Any] = {}
    for team in sorted(all_teams):
        record = {
            "team": team,
            "is_site_team": team in site_teams,
            "coverage": {
                section: team in values for section, values in datasets.items()
            } | {
                "position_groups": team in positions,
                "top_players": team in top_players,
                "players": team in counts,
            },
            "air": datasets["air"].get(team),
            "coaching": datasets["coaching"].get(team),
            "depth": datasets["depth"].get(team),
            "rotation": datasets["rotation"].get(team),
            "injury": datasets["injury"].get(team),
            "offense_profile": datasets["offense_profile"].get(team),
            "defense_profile": datasets["defense_profile"].get(team),
            "position_groups": positions.get(team, {}),
            "top_players": top_players.get(team, []),
            "player_count": counts.get(team, 0),
        }
        record["summary"] = summary_for(record)
        teams_payload[team] = record

    missing_site_teams = sorted(site_teams - all_teams)
    non_site_teams = sorted(all_teams - site_teams)
    site_teams_with_full_team_coverage = sorted(
        team for team in site_teams
        if all(team in dataset for dataset in datasets.values())
    )

    payload = {
        "schema_version": "cfbdepth-site-teams-v1",
        "as_of": args.as_of,
        "built_at": f"{args.as_of}T00:00:00+00:00",
        "source_scope": "official CFBDepth CSV exports normalized through canonical datasets",
        "consumer_contract": {
            "shared_asset": True,
            "team_records_stored_once": True,
            "html_modified": False,
            "matchups_records_modified": False,
            "team_pages_modified": False,
            "matchup_drawer_modified": False,
            "injury_scope": "aggregate team-level impact only; not player-level injury reporting",
            "raw_matchup_differences_are_betting_scores": False,
        },
        "coverage": {
            "site_team_count": len(site_teams),
            "asset_team_count": len(all_teams),
            "site_teams_with_full_team_dataset_coverage": len(site_teams_with_full_team_coverage),
            "site_teams_missing_from_asset": missing_site_teams,
            "non_site_teams_preserved": non_site_teams,
        },
        "teams": teams_payload,
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    dataset_coverage = {
        section: {
            "team_count": len(values),
            "missing_site_teams": sorted(site_teams - set(values)),
            "non_site_teams": sorted(set(values) - site_teams),
        }
        for section, values in datasets.items()
    }
    audit = {
        "schema_version": "cfbdepth-team-asset-audit-v1",
        "as_of": args.as_of,
        "built_at": f"{args.as_of}T00:00:00+00:00",
        "output": str(out_path.relative_to(root)),
        "site_team_count": len(site_teams),
        "asset_team_count": len(all_teams),
        "site_teams_missing_from_asset": missing_site_teams,
        "non_site_teams_preserved": non_site_teams,
        "teams_with_position_groups": len(positions),
        "teams_with_top_players": len(top_players),
        "teams_with_player_rows": len(counts),
        "player_rows": sum(counts.values()),
        "dataset_coverage": dataset_coverage,
        "warnings": [],
    }
    if missing_site_teams:
        audit["warnings"].append(f"Site teams missing from shared asset: {missing_site_teams}")
    if len(site_teams) != 138:
        audit["warnings"].append(f"Expected 138 site teams; found {len(site_teams)}")
    if len(all_teams) != 140:
        audit["warnings"].append(f"Expected 140 CFBDepth asset teams; found {len(all_teams)}")
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    print("CFBDepth shared team asset complete")
    print("site teams:", len(site_teams))
    print("asset teams:", len(all_teams))
    print("site teams missing:", len(missing_site_teams))
    print("non-site teams preserved:", non_site_teams)
    print("player rows:", sum(counts.values()))
    print("warnings:", len(audit["warnings"]))
    print("asset:", out_path)
    print("audit:", audit_path)


if __name__ == "__main__":
    main()
