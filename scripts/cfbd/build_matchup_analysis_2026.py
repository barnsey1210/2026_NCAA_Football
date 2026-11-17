#!/usr/bin/env python3
"""Build the public CFBD opponent-adjusted matchup-analysis contract."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT = ROOT / "research/cfbd_tier1_adjusted_preview_audit_2026w12"
OUT = ROOT / "data/site/matchup_analysis_2026.json"
PROFILE_OVERLAYS = ROOT / "data/canonical/matchup_analysis_profile_overlays_2026.json"
CFBDEPTH_TEAMS = ROOT / "data/site/cfbdepth_teams_2026.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def value_at(row, path):
    value = row
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
        if value is None:
            return None
    return value


def band(rank, population):
    pct = rank / population if population else 1
    if pct <= .10:
        return "elite"
    if pct <= .30:
        return "strong"
    if pct <= .70:
        return "average"
    if pct <= .90:
        return "weak"
    return "poor"


def rank_rows(rows, value_path, *, lower_better=False, key="team"):
    values = [(str(row[key]), value_at(row, value_path)) for row in rows]
    values = [(name, value) for name, value in values if isinstance(value, (int, float))]
    values.sort(key=lambda item: item[1], reverse=not lower_better)
    result = {}
    for index, (name, value) in enumerate(values, 1):
        rank = 1 + sum(
            other < value if lower_better else other > value
            for _, other in values
        )
        result[name] = {
            "value": value,
            "rank": rank,
            "population": len(values),
            "band": band(rank, len(values)),
        }
    return result


def player_ranks(rows, metric, group_name):
    groups = defaultdict(list)
    for row in rows:
        position = str(row.get("position") or "ALL").upper()
        groups[position].append(row)
    ranked = []
    for row in rows:
        position = str(row.get("position") or "ALL").upper()
        peers = sorted(groups[position], key=lambda x: x.get(metric, float("-inf")), reverse=True)
        value = row.get(metric)
        rank = 1 + sum((peer.get(metric) or float("-inf")) > value for peer in peers)
        item = dict(row)
        item["metric"] = group_name
        item["rank"] = rank
        item["population"] = len(peers)
        item["band"] = band(rank, len(peers))
        ranked.append(item)
    return ranked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--passing", type=Path, required=True)
    parser.add_argument("--rushing", type=Path, required=True)
    parser.add_argument("--kicking", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    adjusted = load(args.audit_dir / "related/wepa_team_season_2026.json")
    core = load(args.audit_dir / "related/core_ratings_2026.json")
    advanced = load(args.audit_dir / "related/advanced_season_2026_fbs.json")
    profile_overlays = load(PROFILE_OVERLAYS) if PROFILE_OVERLAYS.exists() else {"profiles": {}}
    cfbdepth = load(CFBDEPTH_TEAMS).get("teams", {}) if CFBDEPTH_TEAMS.exists() else {}
    passing = player_ranks(load(args.passing), "wepa", "Passing WEPA")
    rushing = player_ranks(load(args.rushing), "wepa", "Rushing WEPA")
    kicking = player_ranks(load(args.kicking), "paar", "Kicking PAAR")

    metric_specs = [
        ("Adjusted EPA", "epa.total", "epaAllowed.total", "EPA/play"),
        ("Passing EPA", "epa.passing", "epaAllowed.passing", "EPA/pass"),
        ("Rushing EPA", "epa.rushing", "epaAllowed.rushing", "EPA/rush"),
        ("Success Rate", "successRate.total", "successRateAllowed.total", "percent"),
        ("Standard Down Success", "successRate.standardDowns", "successRateAllowed.standardDowns", "percent"),
        ("Passing Down Success", "successRate.passingDowns", "successRateAllowed.passingDowns", "percent"),
        ("Explosiveness", "explosiveness", "explosivenessAllowed", "number"),
        ("Line Yards", "rushing.lineYards", "rushingAllowed.lineYards", "yards"),
        ("Second-Level Yards", "rushing.secondLevelYards", "rushingAllowed.secondLevelYards", "yards"),
        ("Open-Field Yards", "rushing.openFieldYards", "rushingAllowed.openFieldYards", "yards"),
    ]
    metric_ranks = {}
    for _, offense_path, defense_path, _ in metric_specs:
        metric_ranks[offense_path] = rank_rows(adjusted, offense_path, lower_better=False)
        metric_ranks[defense_path] = rank_rows(adjusted, defense_path, lower_better=True)

    core_rank = rank_rows(core, "overall")
    run_rank = rank_rows(advanced, "offense.rushingPlays.rate")
    pass_rank = rank_rows(advanced, "offense.passingPlays.rate")
    talent_rows = [
        {"team": team, "value": value_at(row, "rotation.overall")}
        for team, row in cfbdepth.items()
    ]
    coach_rows = [
        {"team": team, "value": value_at(row, "coaching.overall_impact")}
        for team, row in cfbdepth.items()
    ]
    talent_rank = rank_rows(talent_rows, "value")
    coach_rank = rank_rows(coach_rows, "value")
    advanced_by_team = {row["team"]: row for row in advanced}
    core_by_team = {row["team"]: row for row in core}
    adjusted_by_team = {row["team"]: row for row in adjusted}
    by_team_players = defaultdict(lambda: {"passing": [], "rushing": [], "kicking": []})
    for key, rows in (("passing", passing), ("rushing", rushing), ("kicking", kicking)):
        for row in rows:
            by_team_players[row["team"]][key].append(row)

    games_payload = load(ROOT / "data/site/war_room_market_matrix.json")
    games = {}
    for game in games_payload.get("games", []):
        spread = value_at(game, "authority.spread.value")
        total = value_at(game, "authority.total.value")
        games[str(game["game_id"])] = {
            "game_id": game["game_id"],
            "away": game["away_team"],
            "home": game["home_team"],
            "week": game.get("week"),
            "kickoff": game.get("kickoff_time"),
            "spread": spread,
            "total": total,
        }

    teams = {}
    for team in sorted(adjusted_by_team):
        adv = advanced_by_team.get(team, {})
        offense = value_at(adv, "offense") or {}
        run_rate = value_at(offense, "rushingPlays.rate")
        pass_rate = value_at(offense, "passingPlays.rate")
        total_rate = (run_rate or 0) + (pass_rate or 0)
        metrics = []
        for label, offense_path, defense_path, unit in metric_specs:
            metrics.append({
                "label": label,
                "unit": unit,
                "offense": metric_ranks[offense_path].get(team),
                "defense": metric_ranks[defense_path].get(team),
            })
        players = by_team_players[team]
        for group in players.values():
            group.sort(key=lambda row: row.get("wepa", row.get("paar", -999)), reverse=True)
        overlay = profile_overlays.get("profiles", {}).get(team)
        if overlay:
            for group in players.values():
                for player in group:
                    player["availability"] = overlay.get("availability", {}).get(player.get("athleteName"))
        generic_profile = {
            "season": {
                "talent": talent_rank.get(team),
                "coach": coach_rank.get(team),
                "draftables": None,
                "runRank": run_rank.get(team),
                "passRank": pass_rank.get(team),
                "paceRank": None,
                "playsPerGame": None,
                "l2": None,
                "last2PerformanceVsModel": None,
                "last4PerformanceVsModel": None,
                "performanceVsModel": None,
            },
            "recent": {
                "performance": None,
                "sos": None,
                "trend": "Unavailable",
                "trendDelta": None,
                "opponents": [],
            },
        }
        if overlay:
            generic_profile = {
                "season": overlay.get("season", generic_profile["season"]),
                "recent": overlay.get("recent", generic_profile["recent"]),
            }
        teams[team] = {
            "metrics": metrics,
            "core": core_rank.get(team),
            "run_split": run_rate / total_rate if total_rate else None,
            "pass_split": pass_rate / total_rate if total_rate else None,
            "plays": value_at(adv, "offense.plays"),
            "players": players,
            "profile": generic_profile,
        }

    payload = {
        "schema_version": "matchup-analysis-v1",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "season": 2026,
        "through_week": 11,
        "rank_policy": {
            "teams": "ordinal rank among 138 FBS teams within the same offense/defense metric",
            "players": "ordinal rank within the same CFBD metric and listed position among qualified players",
            "bands": "five percentile tiers calculated independently within each ranking population",
        },
        "definitions": {
            "wepa": "CFBD opponent-adjusted model efficiency. Higher is better; plays show qualifying sample size.",
            "paar": "CFBD Points Added Above Replacement for kickers. Higher is better; attempts show qualifying sample size.",
        },
        "profile_sources": {
            "draft": profile_overlays.get("draft_source"),
            "availability_note": profile_overlays.get("availability_note"),
        },
        "games": games,
        "teams": teams,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "teams": len(teams),
        "games": len(games),
        "passing_players": len(passing),
        "rushing_players": len(rushing),
        "kickers": len(kicking),
    }, indent=2))


if __name__ == "__main__":
    main()
