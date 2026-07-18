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

from scripts.lib.ncaaf_config import canonical_team, production_model

INDEX = ROOT / "index.html"
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
    html = INDEX.read_text(errors="ignore")
    match = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise SystemExit("Missing embedded DB in index.html")
    db = json.loads(match.group(1))

    def js_const(name):
        found = re.search(r"const\s+" + re.escape(name) + r"\s*=\s*(\{.*?\});", html, re.S)
        return json.loads(found.group(1)) if found else {}

    return db, js_const("RATING_TRENDS"), js_const("RETURNING_PRODUCTION_2026")


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
        "total_margin": number(row.get("avg_total")), "ou_rank": ou_rank, "sample": integer(row.get("games")),
    }


def coach_role_split(row):
    if not row:
        return None
    return {
        "role": clean(row.get("fav_dog")), "games": integer(row.get("games")),
        "ats_record": f"{integer(row.get('ats_w')) or 0}-{integer(row.get('ats_l')) or 0}-{integer(row.get('ats_push')) or 0}",
        "ats_pct": number(row.get("ats_win_pct")), "ats_margin": number(row.get("avg_ats_margin")),
        "ou_record": f"{integer(row.get('overs')) or 0}-{integer(row.get('unders')) or 0}-{integer(row.get('total_push')) or 0}",
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
    """Normalize the broad game-angle feed to the same compact UI contract."""
    tier = clean(row.get("tier")) or "low"
    return {
        "signal_group": "betting_angle", "signal_type": clean(row.get("angle_key")),
        "market": None, "period": None, "team": clean(row.get("side_team")),
        "opponent": None, "direction": clean(row.get("side_team")), "strength": tier,
        "confidence": tier, "headline": clean(row.get("angle_label")),
        "detail": clean(row.get("reason")), "source": "game_betting_angles_2026.csv",
        "historical_games": None, "historical_ats_record": None,
        "historical_ats_pct": None, "historical_avg_ats_margin": clean(row.get("metric_value")),
    }


def main():
    db, rating_trends, returning_prod = extract_index_data()
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
    coach_role_rows = csv_rows(ROOT / "data/coach/coach_full_game_fav_dog_cfbd_splits.csv")
    coach_role_by_team = {}
    for row in coach_role_rows:
        team = canonical_team(row.get("current_team"))
        current_coach = clean(coach_full.get(team, {}).get("head_coach"))
        if clean(row.get("coach")) == current_coach and clean(row.get("period")) == "Full Game" and clean(row.get("fav_dog")) in {"Favorite", "Underdog"}:
            coach_role_by_team[(team, clean(row.get("fav_dog")))] = row
    trend_by_team = {canonical_team(team): value for team, value in rating_trends.items()}
    rp_by_team = {canonical_team(team): value for team, value in returning_prod.items()}

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
        "proof": "index.html modification time is at or after ratings_latest.csv" if applied_to_projection else "projection artifact predates ratings artifact",
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
    injury_rows = csv_rows(ROOT / "data/injuries/injury_events_normalized.csv")
    injuries_by_team = defaultdict(list)
    for row in injury_rows:
        team = canonical_team(row.get("team"))
        if team:
            injuries_by_team[team].append({
                "player": clean(row.get("player")), "position": clean(row.get("position")), "status": clean(row.get("status")),
                "importance_score": number(row.get("importance_score")), "impact_score": number(row.get("impact_score")),
                "tier": clean(row.get("alert_tier")), "source": clean(row.get("source")), "source_url": clean(row.get("source_url")),
                "updated_at": clean(row.get("built_at")),
            })
    for rows in injuries_by_team.values():
        rows.sort(key=lambda row: row.get("impact_score") or 0, reverse=True)

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

    qb_by_team = defaultdict(list)
    for row in csv_rows(ROOT / "data/rosters/player_importance_2026_normalized.csv"):
        if not str(row.get("position") or "").upper().startswith("QB"):
            continue
        team = canonical_team(row.get("team"))
        qb_by_team[team].append({
            "player": clean(row.get("player")), "depth_rank": integer(row.get("depth_rank")), "role": clean(row.get("role")),
            "importance_score": number(row.get("importance_score")), "source": clean(row.get("source")), "updated_at": clean(row.get("last_updated")),
        })
    for team, rows in qb_by_team.items():
        rows.sort(key=lambda row: row.get("depth_rank") or 99)
        for qb in rows[:2]:
            matched = next((inj for inj in injuries_by_team.get(team, []) if clean(inj.get("player")) == clean(qb.get("player"))), None)
            qb["health_status"] = matched.get("status") if matched else "No matched injury"
            qb["injury_impact"] = matched.get("impact_score") if matched else None
        qb_by_team[team] = rows[:2]

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

        def team_view(team, row, conference):
            rp = rp_by_team.get(team)
            schedule = upcoming_by_team.get(team, [])
            schedule_index = next((idx for idx, item in enumerate(schedule) if item.get("game_id") == game_id), 0)
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
                "rating_trend": trend_by_team.get(team),
                "recent_form": recent_games_by_team.get(team, []),
                "upcoming_schedule": schedule[max(0, schedule_index - 1):schedule_index + 3],
                "quarterbacks": qb_by_team.get(team, []),
                "injuries": injuries_by_team.get(team, []),
            }

        coaches = []
        for team in (away, home):
            full = coach_full.get(team, {})
            coaches.append({"team": team, "coach": clean(full.get("head_coach")), "through_season": integer(full.get("betting_stats_through")),
                "periods": [coach_record(full, "full_game", coach_ou_full.get(team)), coach_record(coach_1h.get(team), "first_half", coach_ou_1h.get(team)), coach_record(coach_2h.get(team), "second_half", coach_ou_2h.get(team))],
                "role_splits": [coach_role_split(coach_role_by_team.get((team, role))) for role in ("Favorite", "Underdog") if coach_role_by_team.get((team, role))]})

        market_spread_home = number(game.get("market_spread_home"))
        model_home = number(game.get("projected_margin_home"))
        if model_home is not None:
            model_home = -model_home
        records.append({
            "game": {"game_id": game_id, "cfbd_game_id": clean(game.get("cfbd_game_id")), "week": integer(game.get("week")),
                "date": clean(game.get("date")), "away_team": away, "home_team": home, "neutral_site": boolish(game.get("neutral_site"))},
            "teams": {"away": team_view(away, away_row, away_conf), "home": team_view(home, home_row, home_conf)},
            "model": {"home_spread": model_home, "total": number(game.get("projected_total")), "home_win_probability": number(game.get("home_win_prob"))},
            "market": {"spread": {"home_line": market_spread_home, "price": number(game.get("market_spread_price")), "book": clean(game.get("market_spread_book")), "updated_at": clean(game.get("market_spread_last_update")),
                    "best_home": {"home_line": number(game.get("market_best_home_spread_home")), "price": number(game.get("market_best_home_spread_price")), "book": clean(game.get("market_best_home_spread_book"))},
                    "best_away": {"home_line": number(game.get("market_best_away_spread_home")), "price": number(game.get("market_best_away_spread_price")), "book": clean(game.get("market_best_away_spread_book"))}},
                "total": {"line": number(game.get("market_total")), "over_price": number(game.get("market_total_over_price")), "under_price": number(game.get("market_total_under_price")), "book": clean(game.get("market_total_book")), "updated_at": clean(game.get("market_total_last_update"))},
                "moneyline": {"away": number(game.get("market_away_moneyline")), "home": number(game.get("market_home_moneyline")), "away_book": clean(game.get("market_away_moneyline_book")), "home_book": clean(game.get("market_home_moneyline_book"))},
                "line_history": {"asset_key": game_id, "points": len(history_rows),
                    "first_timestamp": clean(history_rows[0].get("snapshot_date")) if history_rows else None,
                    "last_timestamp": clean(history_rows[-1].get("snapshot_date")) if history_rows else None}},
            "matchup": {"away_offense_vs_home_defense": five_factors(away, home, style_by_team), "home_offense_vs_away_defense": five_factors(home, away, style_by_team), "coaches": coaches},
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
        "coach_full_both_teams": count(lambda r: all(c["periods"][0] is not None for c in r["matchup"]["coaches"])),
        "coach_halves_both_teams": count(lambda r: all(c["periods"][1] is not None and c["periods"][2] is not None for c in r["matchup"]["coaches"])),
        "injury_players": count(lambda r: bool(r["teams"]["away"]["injuries"] or r["teams"]["home"]["injuries"])),
        "weather_rows": count(lambda r: r["weather"] is not None),
        "angles": count(lambda r: bool(r["angles"])),
        "recent_form": count(lambda r: bool(r["teams"]["away"]["recent_form"] and r["teams"]["home"]["recent_form"])),
        "quarterback_depth_both_teams": count(lambda r: bool(r["teams"]["away"]["quarterbacks"] and r["teams"]["home"]["quarterbacks"])),
        "canonical_wager_game_links": count(lambda r: bool(r["activity"]["wagers"])), "expert_picks": count(lambda r: bool(r["activity"]["expert_picks"])), "notes": 0, "watch_pass": 0,
    }
    audit = {"schema_version": "matchups-view-v1", "built_at": datetime.now(timezone.utc).isoformat(), "coverage": coverage,
        "coverage_pct": {key: round(value / total * 100, 1) if total else 0 for key, value in coverage.items() if key != "games"},
        "duplicate_game_ids": duplicate_ids,
        "known_gaps": [
            "Recent form currently uses each team's final three 2025 game rows; an in-season opponent-adjusted trajectory still needs to be built.",
            "Quarterback depth and importance come from Ourlads/player-importance data, not a CFBDepth player rating or national QB ranking.",
            "bets_enriched.csv does not expose a canonical game_id for reliable site-wide joins.",
            "expert picks, notes, and Watch/Pass require the authenticated persistence service.",
            "CFBDepth normalization exists, but current player-level coverage may be empty outside the active injury-news window.",
            "Market rows are current best fields; a quote-level atomic-offer array should be added before production EV selection.",
        ]}
    payload = {"schema_version": "matchups-view-v1", "built_at": audit["built_at"], "production_model": production_model(), "rating_freshness": rating_freshness,
        "assets": {"line_history": "data/site/matchup_line_history.json", "betting_activity": "data/site/betting_activity_view.json"}, "audit_summary": coverage, "games": records}
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
