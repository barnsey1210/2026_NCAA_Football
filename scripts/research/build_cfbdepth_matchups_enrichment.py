#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

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

MATCHUP_COMPONENTS = [
    ("qb_passing_vs_db_coverage", "QB", "rotation_passing_avg", "DB", "rotation_coverage_avg"),
    ("qb_pressure_vs_dl_pass_rush", "QB", "rotation_pressure_avg", "DL", "rotation_pass_rush_avg"),
    ("qb_pressure_vs_lb_pass_rush", "QB", "rotation_pressure_avg", "LB", "rotation_pass_rush_avg"),
    ("rb_running_vs_dl_run_defense", "RB", "rotation_running_avg", "DL", "rotation_run_d_avg"),
    ("rb_running_vs_lb_run_defense", "RB", "rotation_running_avg", "LB", "rotation_run_d_avg"),
    ("rb_receiving_vs_lb_coverage", "RB", "rotation_receiving_avg", "LB", "rotation_coverage_avg"),
    ("wr_routes_vs_db_coverage", "WR", "rotation_routes_avg", "DB", "rotation_coverage_avg"),
    ("wr_hands_vs_db_coverage", "WR", "rotation_hands_avg", "DB", "rotation_coverage_avg"),
    ("wr_explosive_vs_db_coverage", "WR", "rotation_explosive_avg", "DB", "rotation_coverage_avg"),
    ("te_routes_vs_lb_coverage", "TE", "rotation_routes_avg", "LB", "rotation_coverage_avg"),
    ("te_hands_vs_db_coverage", "TE", "rotation_hands_avg", "DB", "rotation_coverage_avg"),
    ("ol_pass_block_vs_dl_pass_rush", "OL", "rotation_pass_block_avg", "DL", "rotation_pass_rush_avg"),
    ("ol_pass_block_vs_lb_pass_rush", "OL", "rotation_pass_block_avg", "LB", "rotation_pass_rush_avg"),
    ("ol_run_block_vs_dl_run_defense", "OL", "rotation_run_block_avg", "DL", "rotation_run_d_avg"),
    ("ol_run_block_vs_lb_run_defense", "OL", "rotation_run_block_avg", "LB", "rotation_run_d_avg"),
]


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    return value


def row_to_dict(row: pd.Series, excluded: set[str] | None = None) -> dict[str, Any]:
    excluded = excluded or set()
    return {str(k): clean_value(v) for k, v in row.items() if k not in excluded}


def load_team_datasets(canonical: Path) -> tuple[dict[str, dict[str, dict[str, Any]]], set[str]]:
    datasets: dict[str, dict[str, dict[str, Any]]] = {}
    teams: set[str] = set()
    for key, filename in TEAM_FILES.items():
        path = canonical / filename
        if not path.exists():
            raise SystemExit(f"Missing canonical input: {path}")
        frame = pd.read_csv(path)
        if "team" not in frame.columns:
            raise SystemExit(f"{path}: missing team column")
        if frame["team"].duplicated().any():
            dupes = sorted(frame.loc[frame["team"].duplicated(False), "team"].astype(str).unique())
            raise SystemExit(f"{path}: duplicate teams: {dupes[:10]}")
        datasets[key] = {
            str(row["team"]): row_to_dict(row, {"team"}) for _, row in frame.iterrows()
        }
        teams.update(datasets[key])
    return datasets, teams


def load_positions(canonical: Path) -> dict[str, dict[str, dict[str, Any]]]:
    path = canonical / POSITION_FILE
    if not path.exists():
        raise SystemExit(f"Missing canonical input: {path}")
    frame = pd.read_csv(path)
    required = {"team", "position_group"}
    if not required.issubset(frame.columns):
        raise SystemExit(f"{path}: missing {sorted(required - set(frame.columns))}")
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for _, row in frame.iterrows():
        team = str(row["team"])
        pos = str(row["position_group"])
        out.setdefault(team, {})[pos] = row_to_dict(row, {"team", "position_group"})
    return out


def load_top_players(canonical: Path) -> dict[str, list[dict[str, Any]]]:
    path = canonical / TOP_PLAYERS_FILE
    if not path.exists():
        raise SystemExit(f"Missing canonical input: {path}")
    payload = json.loads(path.read_text())
    return payload.get("teams", {})


def metric(positions: dict[str, dict[str, dict[str, Any]]], team: str, pos: str, field: str) -> float | None:
    value = positions.get(team, {}).get(pos, {}).get(field)
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def offense_vs_defense(
    positions: dict[str, dict[str, dict[str, Any]]],
    offense_team: str,
    defense_team: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, off_pos, off_field, def_pos, def_field in MATCHUP_COMPONENTS:
        offense_value = metric(positions, offense_team, off_pos, off_field)
        defense_value = metric(positions, defense_team, def_pos, def_field)
        difference = None
        leader = "unavailable"
        if offense_value is not None and defense_value is not None:
            difference = round(offense_value - defense_value, 4)
            if difference > 0:
                leader = offense_team
            elif difference < 0:
                leader = defense_team
            else:
                leader = "even"
        rows.append({
            "component": name,
            "offense_team": offense_team,
            "offense_position": off_pos,
            "offense_metric": off_field,
            "offense_value": offense_value,
            "defense_team": defense_team,
            "defense_position": def_pos,
            "defense_metric": def_field,
            "defense_value": defense_value,
            "raw_difference": difference,
            "leader": leader,
            "interpretation_note": "Raw CFBDepth rating differential only; no betting weight or calibrated edge score applied.",
        })
    return rows


def build_matchup(positions: dict[str, dict[str, dict[str, Any]]], away: str, home: str) -> dict[str, Any]:
    return {
        "away_team": away,
        "home_team": home,
        "away_offense_vs_home_defense": offense_vs_defense(positions, away, home),
        "home_offense_vs_away_defense": offense_vs_defense(positions, home, away),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build research-only CFBDepth Matchups enrichment payloads.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--as-of", default="2026-08-05")
    parser.add_argument("--away")
    parser.add_argument("--home")
    args = parser.parse_args()

    if bool(args.away) != bool(args.home):
        raise SystemExit("Provide both --away and --home, or neither.")

    root = args.repo_root.resolve()
    canonical = root / "data/canonical"
    out_dir = root / "data/research/cfbdepth_matchups"
    audit_dir = root / "data/audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    datasets, teams = load_team_datasets(canonical)
    positions = load_positions(canonical)
    top_players = load_top_players(canonical)
    teams.update(positions)
    teams.update(top_players)

    team_payload: dict[str, Any] = {
        "schema_version": "cfbdepth-matchups-team-enrichment-v1",
        "as_of": args.as_of,
        "research_only": True,
        "notes": [
            "No public site or production Matchups payload consumes this file.",
            "Team injury data is aggregate team-level impact only, not player-level injury reporting.",
            "Raw component differentials are not calibrated betting scores.",
        ],
        "teams": {},
    }
    for team in sorted(teams):
        team_payload["teams"][team] = {
            "team": team,
            "air": datasets["air"].get(team),
            "coaching": datasets["coaching"].get(team),
            "depth": datasets["depth"].get(team),
            "rotation": datasets["rotation"].get(team),
            "injury": datasets["injury"].get(team),
            "offense_profile": datasets["offense_profile"].get(team),
            "defense_profile": datasets["defense_profile"].get(team),
            "position_groups": positions.get(team, {}),
            "top_players": top_players.get(team, []),
        }

    team_out = out_dir / "cfbdepth_matchups_team_enrichment_2026.json"
    team_out.write_text(json.dumps(team_payload, indent=2, sort_keys=True) + "\n")

    matchup_out = None
    if args.away and args.home:
        missing = [team for team in (args.away, args.home) if team not in team_payload["teams"]]
        if missing:
            raise SystemExit(f"Unknown team name(s): {missing}. Use exact canonical team names.")
        matchup_comparisons = build_matchup(
            positions,
            args.away,
            args.home,
        )

        matchup_payload = {
            "schema_version": "cfbdepth-matchup-preview-v2",
            "as_of": args.as_of,
            "research_only": True,
            "matchup": {
                "away_team": args.away,
                "home_team": args.home,
            },
            "away": team_payload["teams"][args.away],
            "home": team_payload["teams"][args.home],
            "comparisons": {
                "away_offense_vs_home_defense": matchup_comparisons[
                    "away_offense_vs_home_defense"
                ],
                "home_offense_vs_away_defense": matchup_comparisons[
                    "home_offense_vs_away_defense"
                ],
            },
        }
        safe_away = args.away.lower().replace(" ", "_")
        safe_home = args.home.lower().replace(" ", "_")
        matchup_out = out_dir / f"preview_{safe_away}_at_{safe_home}.json"
        matchup_out.write_text(json.dumps(matchup_payload, indent=2, sort_keys=True) + "\n")

    dataset_coverage = {
        key: {
            "teams": len(value),
            "missing_from_union": sorted(teams - set(value)),
        }
        for key, value in datasets.items()
    }
    audit = {
        "schema_version": "cfbdepth-matchups-enrichment-audit-v1",
        "as_of": args.as_of,
        "built_at": f"{args.as_of}T00:00:00+00:00",
        "research_only": True,
        "team_union_count": len(teams),
        "teams_with_position_groups": len(positions),
        "teams_with_top_players": len(top_players),
        "dataset_coverage": dataset_coverage,
        "team_output": str(team_out.relative_to(root)),
        "matchup_preview_output": str(matchup_out.relative_to(root)) if matchup_out else None,
        "warnings": [],
    }
    if len(datasets["air"]) != 138:
        audit["warnings"].append(f"Expected 138 AIR teams; found {len(datasets['air'])}")
    if not positions:
        audit["warnings"].append("No position-group data loaded")

    audit_out = audit_dir / "cfbdepth_matchups_enrichment_audit.json"
    audit_out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    print("CFBDepth Matchups research enrichment complete")
    print("team union:", len(teams))
    print("AIR teams:", len(datasets["air"]))
    print("teams with position groups:", len(positions))
    print("teams with top players:", len(top_players))
    print("warnings:", len(audit["warnings"]))
    print("team payload:", team_out)
    if matchup_out:
        print("matchup preview:", matchup_out)
    print("audit:", audit_out)


if __name__ == "__main__":
    main()
