#!/usr/bin/env python3
"""Build deterministic CFBDepth ranks, percentiles, color bands, and tied coaching scores."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LOWER_IS_BETTER = {
    ("injury", "injury_number"), ("injury", "injury_new"),
    ("injury", "injury_impact"), ("injury", "impact_pp"),
}
COACHING_DISCRETE = {"hc_rating", "opc_rating", "dpc_rating"}
GRADE_VALUES = {
    "A+": 13, "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8,
    "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3, "D-": 2, "F": 1,
}
META_KEYS = {
    "as_of", "team", "conference", "conf", "style", "play_caller",
    "head_coach", "off_play_caller", "def_play_caller", "best_player",
    "position_group", "player", "source_school", "team_mapping_status",
}


def number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    if not text or text in {"—", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def rank_band(rank: int, total: int) -> str:
    share = rank / max(total, 1)
    if share <= 0.10:
        return "elite"
    if share <= 1 / 3:
        return "good"
    if share <= 2 / 3:
        return "average"
    if share <= 0.90:
        return "poor"
    return "bad"


def score_band(value: float) -> str:
    if value >= 9:
        return "elite"
    if value >= 7:
        return "good"
    if value >= 6:
        return "average"
    if value >= 5:
        return "poor"
    return "bad"


def score_tier(value: float) -> str:
    if value >= 9:
        return "Elite"
    if value >= 8:
        return "Strong"
    if value >= 7:
        return "Above average"
    if value >= 6:
        return "Average"
    if value >= 5:
        return "Below average"
    return "Weak"


def ranked(values: dict[str, float], higher_is_better: bool = True) -> dict[str, dict[str, Any]]:
    ordered = sorted(values.items(), key=lambda item: ((-item[1] if higher_is_better else item[1]), item[0]))
    counts = Counter(values.values())
    result: dict[str, dict[str, Any]] = {}
    previous = None
    current_rank = 0
    for index, (key, value) in enumerate(ordered, 1):
        if previous is None or value != previous:
            current_rank = index
        previous = value
        total = len(ordered)
        tie_count = counts[value]
        result[key] = {
            "value": value,
            "rank": current_rank,
            "rank_label": f"T-{current_rank}" if tie_count > 1 else f"#{current_rank}",
            "tie_count": tie_count,
            "total": total,
            "percentile": round(100 * (1 - (current_rank - 1) / max(total - 1, 1)), 1),
            "band": rank_band(current_rank, total),
            "direction": "higher" if higher_is_better else "lower",
        }
    return result


def add_conference_ranks(
    rank_rows: dict[str, dict[str, Any]],
    values: dict[str, float],
    conferences: dict[str, str],
    higher_is_better: bool = True,
) -> None:
    grouped: dict[str, dict[str, float]] = defaultdict(dict)
    for key, value in values.items():
        conference = conferences.get(key)
        if conference:
            grouped[conference][key] = value
    for conference, conference_values in grouped.items():
        conference_rows = ranked(conference_values, higher_is_better=higher_is_better)
        for key, conference_row in conference_rows.items():
            rank_rows[key]["conference"] = conference
            rank_rows[key]["conference_rank"] = conference_row["rank"]
            rank_rows[key]["conference_rank_label"] = conference_row["rank_label"]
            rank_rows[key]["conference_tie_count"] = conference_row["tie_count"]
            rank_rows[key]["conference_total"] = conference_row["total"]
            rank_rows[key]["conference_percentile"] = conference_row["percentile"]
            rank_rows[key]["conference_band"] = conference_row["band"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    asset_path = root / "data/site/cfbdepth_teams_2026.json"
    players_path = root / "data/canonical/cfbdepth_players_2026.csv"
    out_path = root / "data/site/cfbdepth_rankings_2026.json"
    audit_path = root / "data/audits/cfbdepth_rankings_audit.json"
    if not asset_path.exists() or not players_path.exists():
        raise SystemExit("Missing shared team asset or canonical player file")

    asset = json.loads(asset_path.read_text())
    teams = {name: row for name, row in asset["teams"].items() if row.get("is_site_team")}
    team_conferences = {team: str(row.get("conference") or "").strip() for team, row in teams.items()}
    output: dict[str, Any] = {
        "schema_version": "cfbdepth-rankings-v3",
        "as_of": args.as_of,
        "built_at": f"{args.as_of}T00:00:00+00:00",
        "color_policy": {
            "elite": "top 10%",
            "good": "10th to 33rd percentile",
            "average": "middle third",
            "poor": "67th to 90th percentile",
            "bad": "bottom 10%",
            "coaching_discrete": "source score bands on a 3-10 scale",
        },
        "teams": {team: {"team_metrics": {}, "position_groups": {}, "top_players": []} for team in teams},
    }

    section_metrics: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for team, team_row in teams.items():
        for section in ("air", "coaching", "rotation", "injury", "offense_profile", "defense_profile"):
            row = team_row.get(section) or {}
            for metric, raw in row.items():
                if metric in META_KEYS:
                    continue
                value = number(raw)
                if value is not None:
                    section_metrics[(section, metric)][team] = value
        depth = team_row.get("depth") or {}
        for metric, raw in depth.items():
            grade = GRADE_VALUES.get(str(raw).strip())
            if grade is not None:
                section_metrics[("depth", metric)][team] = float(grade)

    for (section, metric), values in section_metrics.items():
        higher_is_better = (section, metric) not in LOWER_IS_BETTER
        ranks = ranked(values, higher_is_better=higher_is_better)
        add_conference_ranks(ranks, values, team_conferences, higher_is_better=higher_is_better)
        for team, rank_row in ranks.items():
            if section == "coaching" and metric in COACHING_DISCRETE:
                rank_row["band"] = score_band(rank_row["value"])
                rank_row["tier"] = score_tier(rank_row["value"])
                rank_row["scale"] = "3-10"
            output["teams"][team]["team_metrics"].setdefault(section, {})[metric] = rank_row
            if section == "depth":
                rank_row["grade"] = (teams[team].get("depth") or {}).get(metric)

    unit_values: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for team, team_row in teams.items():
        for position, group in (team_row.get("position_groups") or {}).items():
            output["teams"][team]["position_groups"].setdefault(position, {})
            for metric, raw in group.items():
                if metric in META_KEYS:
                    continue
                value = number(raw)
                if value is not None:
                    unit_values[(position, metric)][team] = value
    for (position, metric), values in unit_values.items():
        unit_ranks = ranked(values, higher_is_better=True)
        add_conference_ranks(unit_ranks, values, team_conferences, higher_is_better=True)
        for team, row in unit_ranks.items():
            output["teams"][team]["position_groups"].setdefault(position, {})[metric] = row

    player_rows = list(csv.DictReader(players_path.open(newline="", encoding="utf-8")))
    player_values: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    player_meta: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(player_rows):
        team = row.get("team", "").strip()
        if team not in teams:
            continue
        position = row.get("position_group", "").strip()
        player = row.get("player", "").strip()
        player_id = f"{team}|{position}|{player}|{index}"
        player_meta[player_id] = {
            "team": team,
            "conference": team_conferences.get(team),
            "position_group": position,
            "player": player,
            "metrics": {},
        }
        for metric, raw in row.items():
            if metric in META_KEYS:
                continue
            value = number(raw)
            if value is not None:
                player_values[(position, metric)][player_id] = value
    for (_position, metric), values in player_values.items():
        player_ranks = ranked(values, higher_is_better=True)
        player_conferences = {player_id: player_meta[player_id].get("conference") or "" for player_id in values}
        add_conference_ranks(player_ranks, values, player_conferences, higher_is_better=True)
        for player_id, rank_row in player_ranks.items():
            player_meta[player_id]["metrics"][metric] = rank_row

    player_rank_path = root / "data/canonical/cfbdepth_player_rankings_2026.csv"
    player_rank_path.parent.mkdir(parents=True, exist_ok=True)
    player_fields = [
        "as_of", "team", "position_group", "player", "metric", "value",
        "rank", "rank_label", "tie_count", "total", "percentile", "band", "direction",
        "conference", "conference_rank", "conference_rank_label", "conference_tie_count",
        "conference_total", "conference_percentile", "conference_band",
    ]
    with player_rank_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=player_fields)
        writer.writeheader()
        for player_id in sorted(player_meta):
            meta = player_meta[player_id]
            for metric in sorted(meta["metrics"]):
                writer.writerow({
                    "as_of": args.as_of,
                    "team": meta["team"],
                    "position_group": meta["position_group"],
                    "player": meta["player"],
                    "metric": metric,
                    **meta["metrics"][metric],
                })

    lookup = {(row["team"], row["position_group"], row["player"]): row for row in player_meta.values()}
    for team, team_row in teams.items():
        for player in team_row.get("top_players") or []:
            ranked_player = lookup.get((team, player.get("position_group"), player.get("player")))
            if ranked_player:
                output["teams"][team]["top_players"].append(ranked_player)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    audit = {
        "schema_version": "cfbdepth-rankings-audit-v3",
        "as_of": args.as_of,
        "built_at": f"{args.as_of}T00:00:00+00:00",
        "site_teams": len(teams),
        "team_metric_families": len(section_metrics),
        "position_metric_families": len(unit_values),
        "ranked_players": len(player_meta),
        "coaching_discrete_metrics": sorted(COACHING_DISCRETE),
        "warnings": [],
        "output": str(out_path.relative_to(root)),
        "player_rank_output": str(player_rank_path.relative_to(root)),
    }
    if len(teams) != 138:
        audit["warnings"].append(f"Expected 138 site teams; found {len(teams)}")
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print("CFBDepth rankings complete")
    print("site teams:", len(teams))
    print("team metric families:", len(section_metrics))
    print("position metric families:", len(unit_values))
    print("ranked players:", len(player_meta))
    print("warnings:", len(audit["warnings"]))
    print("output:", out_path)
    print("player ranks:", player_rank_path)
    print("audit:", audit_path)


if __name__ == "__main__":
    main()
