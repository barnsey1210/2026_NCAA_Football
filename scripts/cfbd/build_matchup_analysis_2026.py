#!/usr/bin/env python3
"""Build the public CFBD opponent-adjusted matchup-analysis contract."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT = ROOT / "research/cfbd_tier1_adjusted_preview_audit_2026w12"
OUT = ROOT / "data/site/matchup_analysis_2026.json"
PROFILE_OVERLAYS = ROOT / "data/canonical/matchup_analysis_profile_overlays_2026.json"
CFBDEPTH_TEAMS = ROOT / "data/site/cfbdepth_teams_2026.json"
RECEIVING = ROOT / "data/canonical/cfbd_receiving_impact_2026.json"
DRAFT_COUNTS = ROOT / "data/canonical/nfl_draft_2027_top175_team_counts.json"
RATINGS = ROOT / "data/site/ratings_view.json"
MODEL_FIT = ROOT / "data/site/team_game_evaluations_2026.json"
MARKET_MATRIX = ROOT / "data/site/war_room_market_matrix.json"
SITE_TO_CFBD = {
    "Appalachian State": "App State",
    "Central Florida": "UCF",
    "Connecticut": "UConn",
    "Hawaii": "Hawai'i",
    "Miami-FL": "Miami",
    "Miami-OH": "Miami (OH)",
    "San Jose State": "San José State",
    "UL-Monroe": "UL Monroe",
}


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
            "tied": sum(other == value for _, other in values) > 1,
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


def completed_games_by_team(games, through_week):
    rows = defaultdict(list)
    for row in games:
        value = row.get("performance_vs_model")
        if row.get("week", 999) > through_week or not isinstance(value, (int, float)):
            continue
        rows[SITE_TO_CFBD.get(row["team"], row["team"])].append(row)
    for team in rows:
        rows[team].sort(key=lambda row: (row.get("kickoff") or "", row.get("week") or 0))
    return rows


def rolling_average(rows, count):
    values = [row["performance_vs_model"] for row in rows[-count:]]
    return mean(values) if values else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--adjusted", type=Path)
    parser.add_argument("--advanced", type=Path)
    parser.add_argument("--passing", type=Path, required=True)
    parser.add_argument("--rushing", type=Path, required=True)
    parser.add_argument("--kicking", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    adjusted = load(args.adjusted or args.audit_dir / "related/wepa_team_season_2026.json")
    core = load(args.audit_dir / "related/core_ratings_2026.json")
    advanced = load(args.advanced or args.audit_dir / "related/advanced_season_2026_fbs.json")
    profile_overlays = load(PROFILE_OVERLAYS) if PROFILE_OVERLAYS.exists() else {"profiles": {}}
    cfbdepth = load(CFBDEPTH_TEAMS).get("teams", {}) if CFBDEPTH_TEAMS.exists() else {}
    receiving_source = load(RECEIVING).get("players", []) if RECEIVING.exists() else []
    fbs_teams = {row["team"] for row in adjusted}
    receiving_by_team = defaultdict(list)
    for row in receiving_source:
        if row.get("team") in fbs_teams:
            receiving_by_team[row["team"]].append(row)
    receiving_source = [
        row
        for team_rows in receiving_by_team.values()
        for row in sorted(team_rows, key=lambda item: item.get("usage", 0), reverse=True)[:5]
    ]
    draft_source = load(DRAFT_COUNTS) if DRAFT_COUNTS.exists() else {"team_counts": {}}
    ratings_source = load(RATINGS).get("teams", [])
    model_fit_source = load(MODEL_FIT)
    passing = player_ranks(load(args.passing), "wepa", "Passing WEPA")
    rushing = player_ranks(load(args.rushing), "wepa", "Rushing WEPA")
    kicking = player_ranks(load(args.kicking), "paar", "Kicking PAAR")
    receiving = player_ranks(receiving_source, "averagePPA", "Receiving PPA")

    adjusted_metric_specs = [
        ("Adjusted EPA / Play", "epa.total", "epaAllowed.total", "decimal"),
        ("Adjusted Passing EPA", "epa.passing", "epaAllowed.passing", "decimal"),
        ("Adjusted Rushing EPA", "epa.rushing", "epaAllowed.rushing", "decimal"),
        ("Adjusted Success Rate", "successRate.total", "successRateAllowed.total", "percent"),
        ("Adjusted Standard-Down Success", "successRate.standardDowns", "successRateAllowed.standardDowns", "percent"),
        ("Adjusted Passing-Down Success", "successRate.passingDowns", "successRateAllowed.passingDowns", "percent"),
        ("Adjusted Rushing Explosiveness", "explosiveness", "explosivenessAllowed", "decimal"),
        ("Adjusted Line Yards", "rushing.lineYards", "rushingAllowed.lineYards", "yards"),
        ("Adjusted Second-Level Yards", "rushing.secondLevelYards", "rushingAllowed.secondLevelYards", "yards"),
        ("Adjusted Open-Field Yards", "rushing.openFieldYards", "rushingAllowed.openFieldYards", "yards"),
        ("Adjusted Highlight Yards", "rushing.highlightYards", "rushingAllowed.highlightYards", "yards"),
    ]
    raw_metric_specs = [
        ("EPA / Play", "offense.ppa", "defense.ppa", "decimal", False, True),
        ("Success Rate", "offense.successRate", "defense.successRate", "percent", False, True),
        ("Explosiveness (Successful-Play EPA)", "offense.explosiveness", "defense.explosiveness", "decimal", False, True),
        ("Points / Opportunity", "offense.pointsPerOpportunity", "defense.pointsPerOpportunity", "decimal2", False, True),
        ("Havoc (OFF Allowed / DEF Created)", "offense.havoc.total", "defense.havoc.total", "percent", True, False),
        ("Standard-Down Success", "offense.standardDowns.successRate", "defense.standardDowns.successRate", "percent", False, True),
        ("Passing-Down Success", "offense.passingDowns.successRate", "defense.passingDowns.successRate", "percent", False, True),
    ]
    metric_ranks = {}
    for _, offense_path, defense_path, _ in adjusted_metric_specs:
        metric_ranks[offense_path] = rank_rows(adjusted, offense_path, lower_better=False)
        metric_ranks[defense_path] = rank_rows(adjusted, defense_path, lower_better=True)
    raw_metric_ranks = {}
    for _, offense_path, defense_path, _, offense_lower, defense_lower in raw_metric_specs:
        raw_metric_ranks[offense_path] = rank_rows(advanced, offense_path, lower_better=offense_lower)
        raw_metric_ranks[defense_path] = rank_rows(advanced, defense_path, lower_better=defense_lower)

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
    ratings_by_team = {SITE_TO_CFBD.get(row["team"], row["team"]): row for row in ratings_source}
    fit_by_team = {
        SITE_TO_CFBD.get(row["team"], row["team"]): row
        for row in model_fit_source.get("team_aggregates", [])
    }
    recent_games = completed_games_by_team(model_fit_source.get("team_games", []), 11)
    last2_rank = rank_rows(
        [{"team": team, "value": rolling_average(rows, 2)} for team, rows in recent_games.items()],
        "value",
    )
    last4_rank = rank_rows(
        [{"team": team, "value": rolling_average(rows, 4)} for team, rows in recent_games.items()],
        "value",
    )
    core_values = {row["team"]: row.get("overall") for row in core}
    sos_rows = []
    for team, rows in recent_games.items():
        values = [core_values.get(SITE_TO_CFBD.get(row.get("opponent"), row.get("opponent"))) for row in rows[-4:]]
        values = [value for value in values if isinstance(value, (int, float))]
        sos_rows.append({"team": team, "value": mean(values) if values else None})
    sos_rank = rank_rows(sos_rows, "value")

    games_payload = load(MARKET_MATRIX)
    scheduled_counts = defaultdict(int)
    for game in games_payload.get("games", []):
        if (game.get("week") or 999) <= 11:
            scheduled_counts[SITE_TO_CFBD.get(game["away_team"], game["away_team"])] += 1
            scheduled_counts[SITE_TO_CFBD.get(game["home_team"], game["home_team"])] += 1
    pace_rows = []
    for row in advanced:
        count = scheduled_counts.get(row["team"], 0)
        plays = value_at(row, "offense.plays")
        pace_rows.append({"team": row["team"], "value": plays / count if count and isinstance(plays, (int, float)) else None})
    pace_rank = rank_rows(pace_rows, "value")

    draft_counts = draft_source.get("team_counts", {})
    draft_rank = rank_rows(
        [{"team": row["team"], "value": int(draft_counts.get(row["team"], 0))} for row in adjusted],
        "value",
    )
    for item in draft_rank.values():
        if item["value"] == 0:
            item.update(rank=len(adjusted), band="poor")
    advanced_by_team = {row["team"]: row for row in advanced}
    core_by_team = {row["team"]: row for row in core}
    adjusted_by_team = {row["team"]: row for row in adjusted}
    by_team_players = defaultdict(lambda: {"passing": [], "rushing": [], "receiving": [], "kicking": []})
    for key, rows in (("passing", passing), ("rushing", rushing), ("receiving", receiving), ("kicking", kicking)):
        for row in rows:
            by_team_players[row["team"]][key].append(row)

    games = {}
    for game in games_payload.get("games", []):
        spread = value_at(game, "authority.spread.value")
        total = value_at(game, "authority.total.value")
        games[str(game["game_id"])] = {
            "game_id": game["game_id"],
            "away": SITE_TO_CFBD.get(game["away_team"], game["away_team"]),
            "home": SITE_TO_CFBD.get(game["home_team"], game["home_team"]),
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
        for label, offense_path, defense_path, unit in adjusted_metric_specs:
            metrics.append({
                "label": label,
                "unit": unit,
                "offense": metric_ranks[offense_path].get(team),
                "defense": metric_ranks[defense_path].get(team),
            })
        raw_metrics = []
        for label, offense_path, defense_path, unit, _, _ in raw_metric_specs:
            raw_metrics.append({
                "label": label,
                "unit": unit,
                "offense": raw_metric_ranks[offense_path].get(team),
                "defense": raw_metric_ranks[defense_path].get(team),
            })
        players = by_team_players[team]
        for key, group in players.items():
            sort_key = "usage" if key == "receiving" else "wepa" if key in {"passing", "rushing"} else "paar"
            group.sort(key=lambda row: row.get(sort_key, -999), reverse=True)
        overlay = profile_overlays.get("profiles", {}).get(team)
        if overlay:
            for group in players.values():
                for player in group:
                    player["availability"] = overlay.get("availability", {}).get(player.get("athleteName"))
        rating = ratings_by_team.get(team, {})
        fit = fit_by_team.get(team, {})
        season_fit = None
        if isinstance(fit.get("performance_vs_model"), (int, float)):
            fit_rank = fit.get("performance_vs_model_rank")
            fit_population = fit.get("rank_population", 138)
            season_fit = {
                "value": fit["performance_vs_model"],
                "rank": fit_rank,
                "population": fit_population,
                "band": band(fit_rank, fit_population) if fit_rank else None,
                "games": fit.get("performance_games_available"),
            }
        l2 = None
        if isinstance(rating.get("l2_change"), (int, float)):
            l2_rank = rating.get("l2_movement_rank")
            l2 = {
                "value": rating["l2_change"],
                "rank": l2_rank,
                "population": len(ratings_source),
                "band": band(l2_rank, len(ratings_source)) if l2_rank else None,
            }
        last2 = last2_rank.get(team)
        last4 = last4_rank.get(team)
        pace = pace_rank.get(team)
        season_value = season_fit.get("value") if season_fit else None
        recent_value = last4.get("value") if last4 else None
        trend_delta = recent_value - season_value if isinstance(recent_value, (int, float)) and isinstance(season_value, (int, float)) else None
        trend = "Stable"
        if isinstance(trend_delta, (int, float)):
            trend = "Improving" if trend_delta > 1 else "Declining" if trend_delta < -1 else "Stable"
        generic_profile = {
            "season": {
                "talent": talent_rank.get(team),
                "coach": coach_rank.get(team),
                "draftables": draft_rank.get(team),
                "runRank": run_rank.get(team),
                "passRank": pass_rank.get(team),
                "paceRank": pace,
                "playsPerGame": pace.get("value") if pace else None,
                "l2": l2,
                "last2PerformanceVsModel": last2,
                "last4PerformanceVsModel": last4,
                "performanceVsModel": season_fit,
            },
            "recent": {
                "performance": last4,
                "sos": sos_rank.get(team),
                "trend": trend,
                "trendDelta": trend_delta,
                "opponents": [
                    {
                        "team": SITE_TO_CFBD.get(row.get("opponent"), row.get("opponent")),
                        "week": row.get("week"),
                        "core": core_values.get(SITE_TO_CFBD.get(row.get("opponent"), row.get("opponent"))),
                    }
                    for row in recent_games.get(team, [])[-4:]
                ],
            },
        }
        teams[team] = {
            "metrics": metrics,
            "raw_metrics": raw_metrics,
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
            "adjustedTeamMetrics": "CFBD opponent-adjusted season metrics from /wepa/team/season. These are not transformed for the specific opponent.",
            "teamEfficiency": "CFBD unadjusted advanced-season team efficiency. Explosiveness is EPA on successful plays; offensive havoc is allowed and defensive havoc is created.",
            "wepa": "CFBD opponent-adjusted model efficiency. Higher is better; plays show qualifying sample size.",
            "paar": "CFBD Points Added Above Replacement for kickers. Higher is better; attempts show qualifying sample size.",
            "receivingPPA": "CFBD receiving average PPA per pass involvement, shown with pass usage and total PPA. This is not WEPA.",
        },
        "profile_sources": {
            "draft": {
                "name": "TheDraftroom consensus top 175",
                "asOf": draft_source.get("source_updated_at"),
                "url": draft_source.get("source"),
            },
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
