#!/usr/bin/env python3
"""Build a normalized, read-only Matchups page view model and coverage audit."""

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.lib.ncaaf_config import canonical_team, production_model
except ModuleNotFoundError:
    # Source repository layout keeps shared configuration under lib/.
    from lib.ncaaf_config import canonical_team, production_model

INDEX = ROOT / "v1.html"
PRESEASON_DB = ROOT / "data/snapshots/preseason/preseason_db.json"
OUT = ROOT / "data/site/matchups_view.json"
AUDIT = ROOT / "data/audits/matchups_view_audit.json"


def clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def number(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def integer(value):
    value = number(value)
    return int(value) if value is not None else None


def boolish(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def csv_rows(path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        return list(csv.DictReader(handle))


def extract_index_data():
    # Canonical game data comes from the normalized preseason DB.
    # v1.html remains only as a temporary source for legacy supplemental JS constants.
    html = INDEX.read_text(errors="ignore")
    if not PRESEASON_DB.exists():
        raise SystemExit(f"Missing canonical preseason DB: {PRESEASON_DB}")
    db = json.loads(PRESEASON_DB.read_text())

    def js_const(name):
        found = re.search(r"const\s+" + re.escape(name) + r"\s*=\s*(\{.*?\});", html, re.S)
        return json.loads(found.group(1)) if found else {}

    return db, js_const("RATING_TRENDS"), js_const("RETURNING_PRODUCTION_2026"), js_const("STAFF_2026")


def canonical_map(rows, key="team"):
    return {canonical_team(row.get(key)): row for row in rows if clean(row.get(key))}


def team_ranks(teams):
    conference_groups = defaultdict(list)
    for team in teams:
        conference_groups[clean(team.get("conference"))].append(team)
    ranks = {}
    for conference, group in conference_groups.items():
        ordered = sorted(group, key=lambda row: number(row.get("combo")) or -999, reverse=True)
        for rank, row in enumerate(ordered, 1):
            ranks[(canonical_team(row.get("team")), conference)] = rank
    return ranks


def style_metric(row, metric, side):
    keys = {
        ("success", "off"): ("success_rate_score", "off_success_score", "offense_score"),
        ("success", "def"): ("success_prevent_score", "def_success_score", "defense_score"),
        ("explosiveness", "off"): ("explosive_score", "explosiveness_score"),
        ("explosiveness", "def"): ("expl_prevent_score", "explosive_prevention_score", "def_explosive_score"),
        ("finishing_drives", "off"): ("finishing_drives_score", "finishing_score", "offense_score"),
        ("finishing_drives", "def"): ("finishing_prevent_score", "red_zone_def_score", "defense_score"),
        ("field_position", "off"): ("field_position_score", "tempo_score", "offense_score"),
        ("field_position", "def"): ("field_position_prevent_score", "defense_score"),
        ("havoc", "off"): ("havoc_avoid_score", "ball_security_score", "offense_score"),
        ("havoc", "def"): ("havoc_creation_score", "pressure_score", "defense_score"),
    }
    for key in keys[(metric, side)]:
        value = number(row.get(key))
        if value is not None:
            return value
    return None


def metric_rank(score):
    return max(1, min(138, round(139 - score * 1.38))) if score is not None else None


def five_factors(offense, defense, style_by_team):
    off = style_by_team.get(canonical_team(offense), {})
    deff = style_by_team.get(canonical_team(defense), {})
    result = []
    for metric in ("success", "explosiveness", "finishing_drives", "field_position", "havoc"):
        off_score = style_metric(off, metric, "off")
        def_score = style_metric(deff, metric, "def")
        off_rank, def_rank = metric_rank(off_score), metric_rank(def_score)
        edge = None
        if off_rank is not None and def_rank is not None and abs(def_rank - off_rank) >= 8:
            edge = offense if off_rank < def_rank else defense
        result.append({"metric": metric, "offense_rank": off_rank, "defense_rank": def_rank, "edge_team": edge})
    return result


def coach_record(row, period, ou_rank=None):
    if not row:
        return None
    if period == "full_game":
        return {
            "period": period, "ats_record": clean(row.get("ats_record")), "ats_rank": integer(row.get("ats_rank")),
            "ats_margin": number(row.get("avg_ats_margin")), "ou_record": clean(row.get("ou_record")),
            "total_margin": number(row.get("avg_total_margin")), "ou_rank": ou_rank, "sample": integer(row.get("ats_w")) + integer(row.get("ats_l")) + integer(row.get("ats_push"))
            if integer(row.get("ats_w")) is not None else None,
        }
    return {
        "period": period,
        "ats_record": f"{integer(row.get('ats_w')) or 0}-{integer(row.get('ats_l')) or 0}-{integer(row.get('ats_push')) or 0}",
        "ats_rank": integer(row.get("ats_rank")), "ats_margin": number(row.get("avg_ats")),
        "ou_record": f"{integer(row.get('overs')) or 0}-{integer(row.get('unders')) or 0}-{integer(row.get('total_push')) or 0}",
        "total_margin": number(row.get("avg_total")), "ou_rank": ou_rank,
        "sample": integer(row.get("ats_games")),
        "ats_sample": integer(row.get("ats_games")),
        "total_sample": integer(row.get("over_games")),
    }


def coach_role_split(row):
    if not row:
        return None
    ats_values = [integer(value) for value in re.findall(r"\d+", clean(row.get("ats_record")) or "")]
    ats_w = integer(row.get("ats_w")) if integer(row.get("ats_w")) is not None else (ats_values[0] if len(ats_values) > 0 else 0)
    ats_l = integer(row.get("ats_l")) if integer(row.get("ats_l")) is not None else (ats_values[1] if len(ats_values) > 1 else 0)
    ats_push = integer(row.get("ats_push")) if integer(row.get("ats_push")) is not None else (ats_values[2] if len(ats_values) > 2 else 0)
    ou_text = clean(row.get("ou_record")) or ""
    over_match, under_match, push_match = re.search(r"(\d+)\s*O\b", ou_text, re.I), re.search(r"(\d+)\s*U\b", ou_text, re.I), re.search(r"(\d+)\s*P\b", ou_text, re.I)
    overs = integer(row.get("overs")) if integer(row.get("overs")) is not None else (integer(over_match.group(1)) if over_match else 0)
    unders = integer(row.get("unders")) if integer(row.get("unders")) is not None else (integer(under_match.group(1)) if under_match else 0)
    total_push = integer(row.get("total_push")) if integer(row.get("total_push")) is not None else (integer(push_match.group(1)) if push_match else 0)
    return {
        "period": clean(row.get("period")), "role": clean(row.get("fav_dog")), "games": integer(row.get("games")),
        "ats_record": f"{ats_w}-{ats_l}-{ats_push}",
        "ats_pct": number(row.get("ats_win_pct")), "ats_margin": number(row.get("avg_ats_margin")),
        "ou_record": f"{overs}-{unders}-{total_push}",
        "over_pct": number(row.get("over_pct")), "total_margin": number(row.get("avg_total_margin")),
        "average_spread": number(row.get("avg_spread")), "seasons": clean(row.get("seasons")), "source": clean(row.get("source")),
    }


def compact_signal(row):
    return {key: clean(row.get(key)) for key in (
        "signal_group", "signal_type", "market", "period", "team", "opponent", "direction", "strength",
        "confidence", "headline", "detail", "source", "historical_games", "historical_ats_record",
        "historical_ats_pct", "historical_avg_ats_margin"
    )}


def compact_angle(row):
    """Normalize game-angle rows while preserving validated study evidence."""
    tier = clean(row.get("tier")) or "low"
    is_rp_study = (
        clean(row.get("angle_key")) == "rp_support"
        and integer(row.get("historical_games"))
        and clean(row.get("historical_ats_record"))
    )
    return {
        "signal_group": clean(row.get("signal_group")) if is_rp_study else "betting_angle",
        "signal_type": clean(row.get("signal_type")) if is_rp_study else clean(row.get("angle_key")),
        "market": clean(row.get("market")) if is_rp_study else None,
        "period": clean(row.get("period")) if is_rp_study else None,
        "team": clean(row.get("side_team")),
        "opponent": clean(row.get("opponent")) if is_rp_study else None,
        "direction": clean(row.get("direction")) if is_rp_study else clean(row.get("side_team")),
        "strength": clean(row.get("rp_strength")) if is_rp_study else tier,
        "confidence": clean(row.get("confidence")) if is_rp_study else tier,
        "headline": clean(row.get("headline")) if is_rp_study else clean(row.get("angle_label")),
        "detail": clean(row.get("detail")) if is_rp_study else clean(row.get("reason")),
        "source": clean(row.get("source")) if is_rp_study else "game_betting_angles_2026.csv",
        "historical_games": integer(row.get("historical_games")) if is_rp_study else None,
        "historical_ats_record": clean(row.get("historical_ats_record")) if is_rp_study else None,
        "historical_ats_pct": number(row.get("historical_ats_pct")) if is_rp_study else None,
        "historical_avg_ats_margin": number(row.get("historical_avg_ats_margin")) if is_rp_study else None,
    }


def main():
    db, rating_trends, returning_prod, staff_2026 = extract_index_data()
    teams = db.get("teams", [])
    games = db.get("games", [])
    team_by_name = canonical_map(teams)
    conference_ranks = team_ranks(teams)
    style_by_team = canonical_map(db.get("team_style_profiles", []))
    coach_full = canonical_map(db.get("coach_betting", []))
    coach_1h = canonical_map(db.get("coach_1h_betting", []), "current_team")
    coach_2h = canonical_map(db.get("coach_2h_betting", []), "current_team")
    def ou_ranks(rows, team_key, value_key):
        ordered = sorted((row for row in rows if number(row.get(value_key)) is not None), key=lambda row: abs(number(row.get(value_key))), reverse=True)
        return {canonical_team(row.get(team_key)): rank for rank, row in enumerate(ordered, 1)}
    coach_ou_full = ou_ranks(db.get("coach_betting", []), "team", "avg_total_margin")
    coach_ou_1h = ou_ranks(db.get("coach_1h_betting", []), "current_team", "avg_total")
    coach_ou_2h = ou_ranks(db.get("coach_2h_betting", []), "current_team", "avg_total")
    coach_role_rows = csv_rows(ROOT / "data/coach/coach_fav_dog_splits_all_periods.csv")
    coach_role_full_history = csv_rows(ROOT / "data/coach/coach_fav_dog_splits_hybrid.csv")
    coach_role_by_team = {}
    for row in coach_role_rows:
        team = canonical_team(row.get("current_team"))
        current_coach = clean(coach_full.get(team, {}).get("head_coach"))
        period, role = clean(row.get("period")), clean(row.get("fav_dog"))
        if clean(row.get("coach")) == current_coach and period in {"1H", "2H"} and role in {"Favorite", "Underdog"}:
            row["source"] = "2024-25 all-period role sample"
            coach_role_by_team[(team, period, role)] = row
    # The hybrid artifact has already remapped the longer CFBD full-game history
    # to active 2026 coach/team assignments. The recent source remains 1H/2H only.
    for row in coach_role_full_history:
        team = canonical_team(row.get("current_team"))
        current_coach = clean(coach_full.get(team, {}).get("head_coach"))
        period, role = clean(row.get("period")), clean(row.get("fav_dog"))
        if clean(row.get("coach")) == current_coach and period == "Full Game" and role in {"Favorite", "Underdog"}:
            coach_role_by_team[(team, "Full Game", role)] = row
    trend_by_team = {canonical_team(team): value for team, value in rating_trends.items()}
    rp_by_team = {canonical_team(team): value for team, value in returning_prod.items()}

    # Returning-production source labels do not always match the canonical
    # team names used by the site. Map the known aliases explicitly.
    rp_source_aliases = {
        "Florida International": "FIU",
        "Fresno State": "Fresno St.",
        "Louisiana": "UL-Lafayette",
        "Sam Houston": "Sam Houston State",
        "San Diego State": "SDSU",
        "South Florida": "USF",
    }
    for canonical_name, source_name in rp_source_aliases.items():
        source_value = rp_by_team.get(canonical_team(source_name))
        if source_value is not None:
            rp_by_team[canonical_team(canonical_name)] = source_value
    staff_by_team = {canonical_team(team): value for team, value in staff_2026.items()}


    # STAFF_2026 uses short labels for several FBS teams while the matchup
    # payload uses canonical full names. Preserve the verified source data.
    staff_source_aliases = {
        "Florida Atlantic": "FAU",
        "Florida International": "FIU",
        "South Florida": "USF",
    }
    for canonical_name, source_name in staff_source_aliases.items():
        source_value = staff_by_team.get(canonical_team(source_name))
        if source_value is not None:
            staff_by_team[canonical_team(canonical_name)] = source_value
    source_status_rows = csv_rows(ROOT / "data/ratings/ratings_source_status.csv")
    movement_rows = csv_rows(ROOT / "data/ratings/ratings_movement.csv")
    active_labels = {source["label"] for source in production_model()["sources"]}
    movement_by_source = defaultdict(list)
    for row in movement_rows:
        movement_by_source[clean(row.get("source"))].append(row)
    freshness_sources = []
    for row in source_status_rows:
        source = clean(row.get("source"))
        if source not in active_labels:
            continue
        movement = movement_by_source.get(source, [])
        actual_changes = [item for item in movement if abs(number(item.get("rating_change")) or 0) > 0.0001]
        freshness_sources.append({
            "source": source, "snapshot_date": clean(row.get("snapshot_date")), "pulled_at": clean(row.get("pulled_at")),
            "source_updated_at": clean(row.get("source_updated_at")), "previous_snapshot": clean(movement[0].get("snapshot_prev")) if movement else None,
            "latest_snapshot": clean(movement[0].get("snapshot_latest")) if movement else clean(row.get("snapshot_date")),
            "changed_teams": len(actual_changes),
            "largest_absolute_change": max((abs(number(item.get("rating_change")) or 0) for item in actual_changes), default=0),
        })
    ratings_latest = ROOT / "data/ratings/ratings_latest.csv"
    applied_to_projection = INDEX.stat().st_mtime >= ratings_latest.stat().st_mtime if ratings_latest.exists() else None
    rating_freshness = {
        "sources": freshness_sources, "applied_to_projection": applied_to_projection,
        "ratings_artifact_modified_at": datetime.fromtimestamp(ratings_latest.stat().st_mtime, timezone.utc).isoformat() if ratings_latest.exists() else None,
        "projection_artifact_modified_at": datetime.fromtimestamp(INDEX.stat().st_mtime, timezone.utc).isoformat(),
        "proof": "v1.html embedded projection artifact is at or after ratings_latest.csv" if applied_to_projection else "projection artifact predates ratings artifact",
    }

    # These are current production ranks. They are useful opponent context, but
    # must not be represented as historical, point-in-time ranks for 2025 games.
    overall_rank_by_team = {canonical_team(row.get("team")): integer(row.get("rank")) for row in teams}
    offense_order = sorted((row for row in teams if number(row.get("sp_offense")) is not None), key=lambda row: number(row.get("sp_offense")), reverse=True)
    defense_order = sorted((row for row in teams if number(row.get("sp_defense")) is not None), key=lambda row: number(row.get("sp_defense")))
    offense_rank_by_team = {canonical_team(row.get("team")): rank for rank, row in enumerate(offense_order, 1)}
    defense_rank_by_team = {canonical_team(row.get("team")): rank for rank, row in enumerate(defense_order, 1)}

    def rank_snapshot(team):
        team = canonical_team(team)
        return {"overall": overall_rank_by_team.get(team), "offense": offense_rank_by_team.get(team), "defense": defense_rank_by_team.get(team)}

    line_history = json.loads((ROOT / "data/site/matchup_line_history.json").read_text()) if (ROOT / "data/site/matchup_line_history.json").exists() else {}

    injury_status_path = ROOT / "data/injuries/injury_source_status.json"
    if injury_status_path.exists():
        try:
            injury_source_status = json.loads(injury_status_path.read_text())
        except (OSError, json.JSONDecodeError):
            injury_source_status = {
                "source_state": "SOURCE_STATUS_INVALID",
                "freshness_state": "UNKNOWN",
                "coverage_state": "UNAVAILABLE",
                "legacy_inputs_allowed": False,
                "reason": "Unable to read injury source status.",
            }
    else:
        injury_source_status = {
            "source_state": "SOURCE_STATUS_MISSING",
            "freshness_state": "MISSING",
            "coverage_state": "UNAVAILABLE",
            "legacy_inputs_allowed": False,
            "reason": "Injury source status file is missing.",
        }

    # Player-level injuries remain unavailable until a validated canonical
    # injury source is configured. Never infer zero injuries from missing data.
    injuries_by_team = defaultdict(list)

    recent_games_by_team = defaultdict(list)
    record_2025_by_team = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0})
    for row in csv_rows(ROOT / "data/import/coach_halves_team_games_2024_2025.csv"):
        if str(row.get("Season")) != "2025":
            continue
        team = canonical_team(row.get("Historical Team"))
        if team:
            team_points, opponent_points = integer(row.get("Game Team Points")), integer(row.get("Game Opp Points"))
            if team_points is not None and opponent_points is not None:
                outcome = "wins" if team_points > opponent_points else "losses" if team_points < opponent_points else "ties"
                record_2025_by_team[team][outcome] += 1
            recent_games_by_team[team].append({
                "date": clean(row.get("Date")), "opponent": canonical_team(row.get("Opponent")), "site": clean(row.get("Home/Away")),
                "team_points": integer(row.get("Game Team Points")), "opponent_points": integer(row.get("Game Opp Points")),
                "spread": number(row.get("Game Spread")), "total_line": number(row.get("Game Total Line")),
                "ats_result": clean(row.get("Game ATS Result")), "ats_margin": number(row.get("Game ATS +/-")),
                "total_result": clean(row.get("Game Total Result")), "total_margin": number(row.get("Game Total +/-")),
                "opponent_ranks": rank_snapshot(row.get("Opponent")), "rank_basis": "current_2026_production",
            })
    for team, rows in recent_games_by_team.items():
        rows.sort(key=lambda row: row.get("date") or "", reverse=True)
        recent_games_by_team[team] = rows[:3]

    # Quarterback depth data from the June-era Ourlads pipeline is isolated.
    # Leave this empty until a validated canonical depth source is configured.
    qb_by_team = defaultdict(list)

    # Opening-possession / coin-toss tendency inputs used by the shared V2 workspace.
    opening_tendency_by_team = canonical_map(
        csv_rows(ROOT / "data/coach/coach_opening_possession_tendency_2026.csv")
    )
    opening_pair_by_match = {}
    for row in csv_rows(ROOT / "data/signals/opening_possession_projection_pairs_2026.csv"):
        team_a, team_b = canonical_team(row.get("team_a")), canonical_team(row.get("team_b"))
        if team_a and team_b:
            opening_pair_by_match[(team_a, team_b)] = row
            opening_pair_by_match[(team_b, team_a)] = row

    weather_by_game = {str(row.get("game_id")): row for row in csv_rows(ROOT / "data/weather/game_weather_latest.csv") if clean(row.get("game_id"))}
    betting_activity_path = ROOT / "data/site/betting_activity_view.json"
    betting_records = json.loads(betting_activity_path.read_text()).get("records", []) if betting_activity_path.exists() else []
    betting_by_game = defaultdict(list)
    for row in betting_records:
        if clean(row.get("game_id")) and row.get("is_open"):
            betting_by_game[str(row["game_id"])].append(row)
    signals_by_game = defaultdict(list)
    for row in csv_rows(ROOT / "data/signals/game_betting_signals.csv"):
        if clean(row.get("game_id")):
            signals_by_game[str(row["game_id"])].append(compact_signal(row))
    for row in csv_rows(ROOT / "data/signals/game_betting_angles_2026.csv"):
        if clean(row.get("game_id")):
            signals_by_game[str(row["game_id"])].append(compact_angle(row))

    upcoming_by_team = defaultdict(list)
    for game in games:
        away, home = canonical_team(game.get("away_team")), canonical_team(game.get("home_team"))
        model_home = number(game.get("projected_margin_home"))
        model_home = -model_home if model_home is not None else None
        market_home = number(game.get("market_spread_home"))
        for team, opponent, site, multiplier in ((away, home, "Away", -1), (home, away, "Home", 1)):
            upcoming_by_team[team].append({
                "game_id": str(game.get("game_id")), "date": clean(game.get("date")), "week": integer(game.get("week")),
                "opponent": opponent, "site": site, "opponent_ranks": rank_snapshot(opponent),
                "model_spread": model_home * multiplier if model_home is not None else None,
                "market_spread": market_home * multiplier if market_home is not None else None,
                "model_total": number(game.get("projected_total")), "market_total": number(game.get("market_total")),
                "rank_basis": "current_2026_production",
            })
    for rows in upcoming_by_team.values():
        rows.sort(key=lambda row: (row.get("date") or "", row.get("week") or 0))

    def staff_view(team):
        row = staff_by_team.get(team) or {}
        statuses = {
            "hc": (clean(row.get("head_coach_status")) or "unverified").lower(),
            "oc": (clean(row.get("oc_status")) or "unverified").lower(),
            "dc": (clean(row.get("dc_status")) or "unverified").lower(),
        }
        counts = {status: sum(1 for value in statuses.values() if value == status)
                  for status in ("returning", "new", "partial", "unverified")}
        first_season = integer(row.get("head_coach_first_season"))
        return {
            "head_coach": clean(row.get("head_coach")),
            "head_coach_status": statuses["hc"],
            "head_coach_first_season": first_season,
            "head_coach_tenure_year": (2026 - first_season + 1) if first_season else None,
            "offensive_coordinator": clean(row.get("offensive_coordinator")),
            "oc_status": statuses["oc"],
            "defensive_coordinator": clean(row.get("defensive_coordinator")),
            "dc_status": statuses["dc"],
            "returning_count": counts["returning"],
            "new_count": counts["new"],
            "partial_count": counts["partial"],
            "unverified_count": counts["unverified"],
            "verified_count": 3 - counts["unverified"],
            "record_2025": clean(row.get("record_2025")),
            "conf_record_2025": clean(row.get("conf_record_2025")),
        }

    def competition_view(team, opponent, schedule, schedule_index, week):
        if week is None or week < 3:
            return {"eligible": False, "reason": "Available beginning Week 3"}
        prior = schedule[:schedule_index]
        prior_ranks = [item.get("opponent_ranks", {}).get("overall") for item in prior]
        prior_ranks = [rank for rank in prior_ranks if rank is not None]
        current_rank = overall_rank_by_team.get(opponent)
        if current_rank is None or not prior_ranks:
            return {"eligible": False, "reason": "Insufficient ranked prior-opponent sample"}
        average = sum(prior_ranks) / len(prior_ranks)
        gap = average - current_rank
        direction = "step_up" if gap > 30 else "step_down" if gap < -30 else None
        return {
            "eligible": True, "prior_opponents": len(prior_ranks),
            "prior_opponent_average_rank": round(average, 1),
            "current_opponent": opponent, "current_opponent_rank": current_rank,
            "rank_gap": round(gap, 1), "direction": direction,
            "qualifies": direction is not None, "threshold": 30,
        }

    records = []
    duplicate_ids = []
    seen = set()
    for game in games:
        game_id = str(game.get("game_id"))
        if game_id in seen:
            duplicate_ids.append(game_id)
        seen.add(game_id)
        away, home = canonical_team(game.get("away_team")), canonical_team(game.get("home_team"))
        history_rows = line_history.get(game_id, [])
        away_row, home_row = team_by_name.get(away, {}), team_by_name.get(home, {})
        away_conf, home_conf = clean(game.get("away_conference")), clean(game.get("home_conference"))

        def team_view(team, row, conference, opponent):
            rp = rp_by_team.get(team)
            schedule = upcoming_by_team.get(team, [])
            schedule_index = next((idx for idx, item in enumerate(schedule) if item.get("game_id") == game_id), 0)
            staff = staff_view(team)
            competition = competition_view(team, opponent, schedule, schedule_index, integer(game.get("week")))
            style = style_by_team.get(team, {})
            tempo = number(style.get("tempo_score"))
            pace = "Super fast" if tempo is not None and tempo >= 80 else "Fast" if tempo is not None and tempo >= 65 else "Normal" if tempo is not None and tempo >= 40 else "Slow" if tempo is not None and tempo >= 25 else "Very slow" if tempo is not None else None
            pressure, front, defense = number(style.get("pressure_score")), number(style.get("front_score")), number(style.get("defense_score"))
            defense_type = "Aggressive front" if pressure is not None and front is not None and pressure >= 70 and front >= 70 else "Pressure defense" if pressure is not None and pressure >= 70 else "Run-front defense" if front is not None and front >= 70 else "Efficiency prevention" if defense is not None and defense >= 70 else "Balanced defense"
            return {
                "team": team, "logo_slug": clean(row.get("slug")), "conference": conference, "overall_rank": integer(row.get("rank")),
                "conference_rank": conference_ranks.get((team, conference)), "offense_rank": offense_rank_by_team.get(team), "defense_rank": defense_rank_by_team.get(team), "rating": number(row.get("combo")),
                "record": {"season": 2026, "wins": 0, "losses": 0, "ties": 0, "status": "No completed 2026 results in current site DB"},
                "betting_record": {"season": 2026, "ats": "0-0-0", "ou": "0-0-0", "status": "No completed 2026 results in current site DB"},
                "style_profile": {"source_season": integer(style.get("season")), "offense_type": clean(style.get("play_call_style")), "defense_type": defense_type, "pace": pace, "tempo_score": tempo, "summary": clean(style.get("style_summary"))} if style else None,
                "returning_production": ({"overall_rank": integer(rp.get("rank")), "overall_pct": number(rp.get("overall")),
                    "offense_rank": integer(rp.get("offRank")), "offense_pct": number(rp.get("off")),
                    "defense_rank": integer(rp.get("defRank")), "defense_pct": number(rp.get("def"))} if rp else None),
                "staff_continuity": staff,
                "competition_context": competition,
                "rating_trend": trend_by_team.get(team),
                "recent_form": recent_games_by_team.get(team, []),
                "upcoming_schedule": schedule[max(0, schedule_index - 1):schedule_index + 3],
                "quarterbacks": qb_by_team.get(team, []),
                "injuries": injuries_by_team.get(team, []),
            }

        coaches = []
        for team in (away, home):
            full = coach_full.get(team, {})
            role_splits = []
            for period in ("Full Game", "1H", "2H"):
                for role in ("Favorite", "Underdog"):
                    split = coach_role_split(coach_role_by_team.get((team, period, role)))
                    role_splits.append(split or {"period": period, "role": role, "available": False, "source": "No matched current-coach sample"})
            coaches.append({"team": team, "coach": clean(full.get("head_coach")), "through_season": integer(full.get("betting_stats_through")),
                "periods": [coach_record(full, "full_game", coach_ou_full.get(team)), coach_record(coach_1h.get(team), "first_half", coach_ou_1h.get(team)), coach_record(coach_2h.get(team), "second_half", coach_ou_2h.get(team))],
                "role_splits": role_splits})

        away_tendency = opening_tendency_by_team.get(away)
        home_tendency = opening_tendency_by_team.get(home)
        opening_pair = opening_pair_by_match.get((away, home))
        opening_possession = {
            "away": away_tendency, "home": home_tendency,
            "projected_opening_receiver": clean(opening_pair.get("projected_opening_receiver")) if opening_pair else None,
            "edge_pct_points": number(opening_pair.get("edge_pct_points")) if opening_pair else None,
            "away_projected_receive_pct": None, "home_projected_receive_pct": None,
        }
        if opening_pair:
            if canonical_team(opening_pair.get("team_a")) == away:
                opening_possession["away_projected_receive_pct"] = number(opening_pair.get("team_a_projected_receive_opening_kick_pct"))
                opening_possession["home_projected_receive_pct"] = number(opening_pair.get("team_b_projected_receive_opening_kick_pct"))
            else:
                opening_possession["away_projected_receive_pct"] = number(opening_pair.get("team_b_projected_receive_opening_kick_pct"))
                opening_possession["home_projected_receive_pct"] = number(opening_pair.get("team_a_projected_receive_opening_kick_pct"))

        market_spread_home = number(game.get("market_spread_home"))
        model_home = number(game.get("projected_margin_home"))
        if model_home is not None:
            model_home = -model_home
        records.append({
            "game": {"game_id": game_id, "cfbd_game_id": clean(game.get("cfbd_game_id")), "week": integer(game.get("week")),
                "date": clean(game.get("date")), "away_team": away, "home_team": home, "neutral_site": boolish(game.get("neutral_site")),
                "status": clean(game.get("cfbd_status")), "completed": boolish(game.get("cfbd_completed")),
                "away_score": integer(game.get("away_score") if game.get("away_score") is not None else game.get("cfbd_away_score")),
                "home_score": integer(game.get("home_score") if game.get("home_score") is not None else game.get("cfbd_home_score")),
                "cfbd_last_updated": clean(game.get("cfbd_last_updated"))},
            "teams": {"away": team_view(away, away_row, away_conf, home), "home": team_view(home, home_row, home_conf, away)},
            "model": {
                "family": clean(game.get("projection_model_family")) or "Game Projection Consensus",
                "home_spread": model_home,
                "total": number(game.get("projected_total")),
                "home_win_probability": number(game.get("home_win_prob")),
                "spread_version": clean(game.get("projection_spread_model_version")),
                "spread_source_count": integer(game.get("projection_spread_source_count")),
                "spread_source_max": integer(game.get("projection_spread_source_max")),
                "spread_coverage": clean(game.get("projection_spread_coverage")),
                "spread_sources": game.get("projection_spread_sources") or [],
                "spread_source_label": clean(game.get("projection_spread_source_label")),
                "total_version": clean(game.get("projection_total_model_version")),
                "total_source_count": integer(game.get("projection_total_source_count")),
                "total_source_max": integer(game.get("projection_total_source_max")),
                "total_coverage": clean(game.get("projection_total_coverage")),
                "total_sources": [
                    "SP+" if source == "Site Projection" else ("DRatings" if source == "DRatings Predictions" else source)
                    for source in (game.get("projection_total_sources") or [])
                ],
                "total_source_label": (
                    (clean(game.get("projection_total_source_label")) or "")
                    .replace("Site Projection", "SP+")
                    .replace("DRatings Predictions", "DRatings")
                    or None
                ),
            },
            "market": {"spread": {"home_line": market_spread_home, "price": number(game.get("market_spread_price")), "book": clean(game.get("market_spread_book")), "updated_at": clean(game.get("market_spread_last_update")),
                    "best_home": {"home_line": number(game.get("market_best_home_spread_home")), "price": number(game.get("market_best_home_spread_price")), "book": clean(game.get("market_best_home_spread_book"))},
                    "best_away": {"home_line": number(game.get("market_best_away_spread_home")), "price": number(game.get("market_best_away_spread_price")), "book": clean(game.get("market_best_away_spread_book"))}},
                "total": {"line": number(game.get("market_total")), "over_price": number(game.get("market_total_over_price")), "under_price": number(game.get("market_total_under_price")), "book": clean(game.get("market_total_book")), "updated_at": clean(game.get("market_total_last_update")),
                    "best_over": {"line": number(game.get("market_best_over_total")), "price": number(game.get("market_best_over_price")), "book": clean(game.get("market_best_over_book"))},
                    "best_under": {"line": number(game.get("market_best_under_total")), "price": number(game.get("market_best_under_price")), "book": clean(game.get("market_best_under_book"))}},
                "moneyline": {"away": number(game.get("market_away_moneyline")), "home": number(game.get("market_home_moneyline")), "away_book": clean(game.get("market_away_moneyline_book")), "home_book": clean(game.get("market_home_moneyline_book"))},
                "line_history": {"asset_key": game_id, "points": len(history_rows),
                    "first_timestamp": clean(history_rows[0].get("snapshot_date")) if history_rows else None,
                    "last_timestamp": clean(history_rows[-1].get("snapshot_date")) if history_rows else None}},
            "matchup": {"away_offense_vs_home_defense": five_factors(away, home, style_by_team), "home_offense_vs_away_defense": five_factors(home, away, style_by_team), "coaches": coaches, "opening_possession": opening_possession},
            "weather": weather_by_game.get(game_id), "angles": signals_by_game.get(game_id, []),
            "activity": {"wagers": [row for row in betting_by_game.get(game_id, []) if row.get("actor", {}).get("type") == "owned_wager"],
                "expert_picks": [row for row in betting_by_game.get(game_id, []) if row.get("actor", {}).get("type") == "tracked_pick"],
                "unassigned": [row for row in betting_by_game.get(game_id, []) if row.get("actor", {}).get("type") == "unassigned"],
                "notes": [], "decision": None, "persistence_status": "google_sheet_snapshot_plus_local_candidate_state"},
        })

    total = len(records)
    def count(test):
        return sum(1 for record in records if test(record))
    coverage = {
        "games": total,
        "model_spread": count(lambda r: r["model"]["home_spread"] is not None),
        "model_total": count(lambda r: r["model"]["total"] is not None),
        "market_spread": count(lambda r: r["market"]["spread"]["home_line"] is not None),
        "market_total": count(lambda r: r["market"]["total"]["line"] is not None),
        "line_history": count(lambda r: r["market"]["line_history"]["points"] > 0),
        "five_factors_complete": count(lambda r: all(x["offense_rank"] is not None and x["defense_rank"] is not None for side in ("away_offense_vs_home_defense", "home_offense_vs_away_defense") for x in r["matchup"][side])),
        "returning_production_both_teams": count(lambda r: r["teams"]["away"]["returning_production"] is not None and r["teams"]["home"]["returning_production"] is not None),
        "staff_continuity_both_teams": count(lambda r: r["teams"]["away"]["staff_continuity"].get("verified_count", 0) > 0 and r["teams"]["home"]["staff_continuity"].get("verified_count", 0) > 0),
        "opening_possession_pairs": count(lambda r: bool(r["matchup"].get("opening_possession", {}).get("projected_opening_receiver"))),
        "competition_context_eligible": count(lambda r: r["teams"]["away"]["competition_context"].get("eligible") or r["teams"]["home"]["competition_context"].get("eligible")),
        "coach_full_both_teams": count(lambda r: all(c["periods"][0] is not None for c in r["matchup"]["coaches"])),
        "coach_halves_both_teams": count(lambda r: all(c["periods"][1] is not None and c["periods"][2] is not None for c in r["matchup"]["coaches"])),
        "injury_players": count(lambda r: bool(r["teams"]["away"]["injuries"] or r["teams"]["home"]["injuries"])),
        "weather_rows": count(lambda r: r["weather"] is not None),
        "angles": count(lambda r: bool(r["angles"])),
        "recent_form": count(lambda r: bool(r["teams"]["away"]["recent_form"] and r["teams"]["home"]["recent_form"])),
        "quarterback_depth_both_teams": count(lambda r: bool(r["teams"]["away"]["quarterbacks"] and r["teams"]["home"]["quarterbacks"])),
        "canonical_wager_game_links": count(lambda r: bool(r["activity"]["wagers"])), "expert_picks": count(lambda r: bool(r["activity"]["expert_picks"])), "notes": 0, "watch_pass": 0,
    }
    coach_views = {}
    for record in records:
        for coach in record["matchup"]["coaches"]:
            if coach.get("coach"):
                coach_views[coach["team"]] = coach
    periods = ("Full Game", "1H", "2H")
    coach_coverage = {
        "teams_with_current_coach": len(coach_views),
        "full_game_summary": sum(bool(c["periods"][0]) for c in coach_views.values()),
        "first_half_summary": sum(bool(c["periods"][1]) for c in coach_views.values()),
        "second_half_summary": sum(bool(c["periods"][2]) for c in coach_views.values()),
    }
    missing_roles = {}
    for period in periods:
        missing = []
        for team, coach in sorted(coach_views.items()):
            available = {row["role"] for row in coach["role_splits"] if row["period"] == period and row.get("available") is not False}
            if available != {"Favorite", "Underdog"}:
                missing.append(team)
        coach_coverage[f"{period.lower().replace(' ', '_')}_both_roles"] = len(coach_views) - len(missing)
        missing_roles[period] = missing
    coach_coverage["all_period_role_rows"] = sum(not any(team in teams for teams in missing_roles.values()) for team in coach_views)
    audit = {"schema_version": "matchups-view-v2-context", "built_at": datetime.now(timezone.utc).isoformat(), "coverage": coverage,
        "coverage_pct": {key: round(value / total * 100, 1) if total else 0 for key, value in coverage.items() if key != "games"},
        "coach_coverage": coach_coverage,
        "coach_missing_role_teams": missing_roles,
        "duplicate_game_ids": duplicate_ids,
        "known_gaps": [
            "Recent form currently uses each team's final three 2025 game rows; an in-season opponent-adjusted trajectory still needs to be built.",
            "Quarterback depth and importance come from Ourlads/player-importance data, not a CFBDepth player rating or national QB ranking.",
            "bets_enriched.csv does not expose a canonical game_id for reliable site-wide joins.",
            "expert picks, notes, and Watch/Pass require the authenticated persistence service.",
            "CFBDepth normalization exists, but current player-level coverage may be empty outside the active injury-news window.",
            "Market rows are current best fields; a quote-level atomic-offer array should be added before production EV selection.",
        ]}
    payload = {"schema_version": "matchups-view-v2-context", "built_at": audit["built_at"], "production_model": production_model(), "site_composite_model": production_model(), "game_projection_model": db.get("projection_model_metadata") or {}, "rating_freshness": rating_freshness,
        "assets": {"line_history": "data/site/matchup_line_history.json", "betting_activity": "data/site/betting_activity_view.json"},
        "injury_source_status": injury_source_status,
        "audit_summary": coverage,
        "games": records}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")
    print("games:", total)
    print("view:", OUT, OUT.stat().st_size, "bytes")
    print("audit:", AUDIT)
    print(json.dumps(coverage, indent=2))


if __name__ == "__main__":
    main()
