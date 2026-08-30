#!/usr/bin/env python3
"""Build genuine 2026 completed-game features for frozen Shadow inference.

No model fitting against 2026 outcomes occurs here.

Historical transform state is reconstructed strictly from 2021-2023 rows in the
approved saved historical feature table. Those states are then applied forward
to completed 2026 team-games.

A row is emitted to production inference only when:
- final result exists
- closing spread and total exist
- required PBP features exist
- required drive features exist
- Game Control exists
- an SP+ snapshot strictly before kickoff exists
- the team's next scheduled game is mapped
"""

from __future__ import annotations

import json
import math
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULTS = ROOT / "data/canonical/game_results_2026.json"

PBP = (
    ROOT
    / "data/canonical/postgame/2026/features/"
      "team_game_tendencies_2026.csv"
)
DRIVES = (
    ROOT
    / "data/canonical/postgame/2026/features/"
      "team_game_drive_context_2026.csv"
)
GAME_CONTROL = (
    ROOT
    / "data/canonical/postgame/2026/features/"
      "team_game_game_control_2026.csv"
)

RATINGS_HISTORY = ROOT / "data/ratings/ratings_history.csv"
MARKET_HISTORY = ROOT / "data/ratings/market_implied_ratings_history.csv"
SCHEDULE = ROOT / "data/snapshots/preseason/preseason_db.json"

HIST_FEATURES = (
    ROOT
    / "data/research/team_rating_movement_model/"
      "repeatable_performance_features.csv"
)

OUT_DIR = ROOT / "data/research/shadow_live_feature_constructor"
OUT_CSV = OUT_DIR / "team_game_features_2026.csv"
OUT_JSON = OUT_DIR / "team_game_features_2026.json"
AUDIT = ROOT / "data/audits/shadow_team_game_features_2026_audit.json"

TRAIN_SEASONS = {2021, 2022, 2023}

PERSISTENT = [
    "off_ppa",
    "off_success_rate",
    "off_explosiveness",
    "off_rush_success_rate",
    "off_pass_success_rate",
    "def_ppa_allowed",
    "def_success_allowed",
    "def_explosiveness_allowed",
    "def_havoc_rate",
    "off_plays",
    "drive_off_points_per_opportunity",
    "drive_def_points_per_opportunity_allowed",
    "gc_game_control_index",
]

Z_COMPONENTS = [
    "off_ppa",
    "off_success_rate",
    "off_explosiveness",
    "def_ppa_allowed",
    "def_success_allowed",
    "def_explosiveness_allowed",
    "drive_off_points_per_opportunity",
    "drive_def_points_per_opportunity_allowed",
    "drive_off_avg_start_ytg",
    "drive_def_opponent_avg_start_ytg",
]

CORE_PBP = [
    "off_ppa",
    "off_success_rate",
    "off_explosiveness",
    "off_rush_success_rate",
    "off_pass_success_rate",
    "def_ppa_allowed",
    "def_success_allowed",
    "def_explosiveness_allowed",
    "def_rush_success_allowed",
    "def_pass_success_allowed",
    "def_havoc_rate",
    "off_plays",
]

CORE_DRIVE = [
    "drive_off_points_per_opportunity",
    "drive_def_points_per_opportunity_allowed",
]

OUTPUT_META = [
    "season",
    "completed_week",
    "completed_game_id",
    "game_date",
    "team",
    "opponent",
    "home_away",
    "neutral_site",
    "next_game_id",
    "next_game_week",
    "next_opponent",
    "next_home_away",
    "next_neutral_site",
    "feature_cutoff",
    "results_available",
    "close_available",
    "pbp_available",
    "game_control_available",
    "entering_ratings_available",
    "next_game_mapping_status",
    "no_lookahead_pass",
    "missing_reasons",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite(value: Any):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def norm_id(value: Any) -> str:
    s = str(value or "").strip()
    return s[:-2] if s.endswith(".0") else s


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        dir=path.parent,
        delete=False,
        encoding="utf-8",
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    tmp.replace(path)


def clean(value: Any):
    if value is None:
        return None
    if isinstance(value, dict):
        return {
            str(key): clean(item)
            for key, item in value.items()
        }
    if isinstance(value, (pd.Series, np.ndarray)):
        return [clean(item) for item in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.integer,)):
        return int(value)
    missing = pd.isna(value)
    if isinstance(missing, (bool, np.bool_)) and missing:
        return None
    return value.item() if hasattr(value, "item") else value


def standardize_fit(frame: pd.DataFrame, features: list[str]):
    x = frame[features].apply(
        pd.to_numeric,
        errors="coerce",
    ).to_numpy(float)

    med = np.nanmedian(x, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)

    x = np.where(np.isfinite(x), x, med)

    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std = np.where(std > 1e-9, std, 1.0)

    return med, mean, std, (x - mean) / std


def standardize_apply(
    frame: pd.DataFrame,
    features: list[str],
    state,
):
    med, mean, std = state

    x = frame[features].apply(
        pd.to_numeric,
        errors="coerce",
    ).to_numpy(float)

    x = np.where(np.isfinite(x), x, med)
    return (x - mean) / std


def ridge_fit(x, y, alpha: float):
    x1 = np.column_stack([np.ones(len(x)), x])
    y = np.asarray(y, float)

    penalty = alpha * np.eye(x1.shape[1])
    penalty[0, 0] = 0

    return np.linalg.solve(
        x1.T @ x1 + penalty,
        x1.T @ y,
    )


def ridge_predict(x, beta):
    return np.column_stack(
        [np.ones(len(x)), x]
    ) @ beta


def load_historical_transform_state():
    if not HIST_FEATURES.exists():
        raise SystemExit(
            f"Missing approved historical feature table: {HIST_FEATURES}"
        )

    hist = pd.read_csv(HIST_FEATURES, low_memory=False)
    hist["season"] = pd.to_numeric(
        hist["season"],
        errors="coerce",
    )

    train = hist["season"].isin(TRAIN_SEASONS)

    required = sorted(
        set(
            PERSISTENT
            + Z_COMPONENTS
            + [
                "actual_market_rating_change",
                "final_margin",
            ]
        )
    )

    missing = [c for c in required if c not in hist.columns]
    if missing:
        raise SystemExit(
            "Historical transform table is missing required columns: "
            + ", ".join(missing)
        )

    z_state = {}
    for col in Z_COMPONENTS:
        values = pd.to_numeric(
            hist.loc[train, col],
            errors="coerce",
        )
        mu = float(values.mean())
        sd = float(values.std())

        if not math.isfinite(mu):
            mu = 0.0
        if not math.isfinite(sd) or sd <= 1e-9:
            sd = 1.0

        z_state[col] = {
            "mean": mu,
            "std": sd,
        }

    eligible_market = (
        train
        & pd.to_numeric(
            hist["actual_market_rating_change"],
            errors="coerce",
        ).notna()
    )

    regularized_state = standardize_fit(
        hist.loc[eligible_market],
        PERSISTENT,
    )

    regularized_beta = ridge_fit(
        regularized_state[3],
        pd.to_numeric(
            hist.loc[
                eligible_market,
                "actual_market_rating_change",
            ],
            errors="coerce",
        ).to_numpy(float),
        20.0,
    )

    eligible_margin = (
        train
        & pd.to_numeric(
            hist["final_margin"],
            errors="coerce",
        ).notna()
    )

    margin_state = standardize_fit(
        hist.loc[eligible_margin],
        PERSISTENT,
    )

    margin_beta = ridge_fit(
        margin_state[3],
        pd.to_numeric(
            hist.loc[
                eligible_margin,
                "final_margin",
            ],
            errors="coerce",
        ).to_numpy(float),
        30.0,
    )

    return {
        "z": z_state,
        "regularized_state": regularized_state[:3],
        "regularized_beta": regularized_beta,
        "margin_state": margin_state[:3],
        "margin_beta": margin_beta,
        "historical_rows": len(hist),
        "training_rows_market": int(eligible_market.sum()),
        "training_rows_margin": int(eligible_margin.sum()),
    }


def load_results() -> list[dict]:
    if not RESULTS.exists():
        raise SystemExit(f"Missing {RESULTS}")

    payload = json.loads(RESULTS.read_text())
    return [
        r for r in payload.get("games", [])
        if r.get("completed")
    ]


def load_schedule() -> list[dict]:
    payload = json.loads(SCHEDULE.read_text())
    return payload.get("games", [])


def next_game_map(schedule: list[dict]):
    rows = []

    for g in schedule:
        try:
            week = int(g.get("week"))
        except Exception:
            continue

        date = pd.to_datetime(
            g.get("cfbd_start_date")
            or g.get("start_date")
            or g.get("date"),
            errors="coerce",
            utc=True,
        )

        for side in ("home", "away"):
            team = g.get(f"{side}_team")
            opponent = g.get(
                "away_team" if side == "home" else "home_team"
            )

            if not team:
                continue

            rows.append({
                "team": team,
                "game_id": norm_id(g.get("game_id")),
                "week": week,
                "date": date,
                "opponent": opponent,
                "home_away": side,
                "neutral_site": bool(g.get("neutral_site")),
            })

    by_team = {}
    for row in rows:
        by_team.setdefault(row["team"], []).append(row)

    for team in by_team:
        by_team[team].sort(
            key=lambda r: (
                r["week"],
                pd.Timestamp.max.tz_localize("UTC")
                if pd.isna(r["date"])
                else r["date"],
                r["game_id"],
            )
        )

    return by_team


def find_next_game(
    by_team,
    team: str,
    completed_game_id: str,
    completed_week: int,
):
    games = by_team.get(team, [])

    current_index = None
    for i, g in enumerate(games):
        if norm_id(g["game_id"]) == norm_id(completed_game_id):
            current_index = i
            break

    if current_index is not None:
        for g in games[current_index + 1:]:
            return g

    for g in games:
        if int(g["week"]) > int(completed_week):
            return g

    return None


def load_entering_sp_plus():
    if not RATINGS_HISTORY.exists():
        raise SystemExit(f"Missing {RATINGS_HISTORY}")

    frame = pd.read_csv(
        RATINGS_HISTORY,
        low_memory=False,
    )

    frame = frame[
        pd.to_numeric(
            frame["season"],
            errors="coerce",
        ).eq(2026)
        & frame["source"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("sp+")
    ].copy()

    frame["_pulled"] = pd.to_datetime(
        frame["pulled_at"],
        errors="coerce",
        utc=True,
    )

    frame = frame[
        frame["_pulled"].notna()
    ].copy()

    return frame


def load_entering_sagarin():
    if not RATINGS_HISTORY.exists():
        raise SystemExit(f"Missing {RATINGS_HISTORY}")

    frame = pd.read_csv(
        RATINGS_HISTORY,
        low_memory=False,
    )

    frame = frame[
        pd.to_numeric(
            frame["season"],
            errors="coerce",
        ).eq(2026)
        & frame["source"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("sagarin predictor")
    ].copy()

    frame["_pulled"] = pd.to_datetime(
        frame["pulled_at"],
        errors="coerce",
        utc=True,
    )

    frame = frame[
        frame["_pulled"].notna()
    ].copy()

    return frame


def pregame_sagarin(
    sag: pd.DataFrame,
    team: str,
    kickoff,
):
    if pd.isna(kickoff):
        return None

    rows = sag[
        sag["team"].eq(team)
        & (sag["_pulled"] < kickoff)
    ].sort_values(
        ["_pulled", "snapshot_date"]
    )

    if rows.empty:
        return None

    return rows.iloc[-1].to_dict()



def pregame_sp_plus(
    sp: pd.DataFrame,
    team: str,
    kickoff,
):
    if pd.isna(kickoff):
        return None

    rows = sp[
        sp["team"].eq(team)
        & (sp["_pulled"] < kickoff)
    ].sort_values(
        ["_pulled", "snapshot_date"]
    )

    if rows.empty:
        return None

    return rows.iloc[-1].to_dict()


def load_market_history():
    if not MARKET_HISTORY.exists():
        return pd.DataFrame()

    d = pd.read_csv(
        MARKET_HISTORY,
        low_memory=False,
    )

    d["season"] = pd.to_numeric(
        d["season"],
        errors="coerce",
    )
    d["through_week"] = pd.to_numeric(
        d["through_week"],
        errors="coerce",
    )

    return d[d["season"].eq(2026)].copy()


def entering_market_rating(
    market: pd.DataFrame,
    team: str,
    week: int,
    inference_time=None,
):
    if market.empty:
        return None

    accepted = market.get("accepted_for_shadow", False)
    if not isinstance(accepted, pd.Series):
        accepted = pd.Series(False, index=market.index)
    accepted = accepted.astype(str).str.lower().isin({"true", "1"})
    state_kind = market.get("state_kind", pd.Series(None, index=market.index))
    state_cutoff = pd.to_datetime(
        market.get("state_cutoff", market.get("snapshot_timestamp")),
        errors="coerce",
        utc=True,
    )
    inference = pd.to_datetime(inference_time, errors="coerce", utc=True)
    cutoff_ok = state_cutoff.notna()
    if pd.notna(inference):
        cutoff_ok &= state_cutoff.le(inference)
    rows = market[
        market["team"].eq(team)
        & market["through_week"].eq(week)
        & accepted
        & state_kind.eq("COMPLETED_WEEK_FROZEN_CLOSES")
        & cutoff_ok
    ].copy()
    rows["_state_cutoff"] = state_cutoff.loc[rows.index]
    rows = rows.sort_values(["_state_cutoff", "snapshot_timestamp"])

    if rows.empty:
        return None

    return finite(
        rows.iloc[-1].get("market_implied_rating")
    )


def feature_cutoff_for_result(result: dict):
    return pd.to_datetime(
        result.get("start_date")
        or result.get("date"),
        errors="coerce",
        utc=True,
    )


def combine_team_games(
    results,
    pbp,
    drives,
    gc,
    sp,
    sag,
    market_history,
    schedule_by_team,
    inference_time=None,
):
    inference_time = inference_time or now_iso()
    pbp_idx = {
        (
            norm_id(r.game_id),
            str(r.team),
        ): r._asdict()
        for r in pbp.itertuples(index=False)
    }

    drive_idx = {
        (
            norm_id(r.game_id),
            str(r.team),
        ): r._asdict()
        for r in drives.itertuples(index=False)
    }

    gc_idx = {
        (
            norm_id(r.game_id),
            str(r.team),
        ): r._asdict()
        for r in gc.itertuples(index=False)
    }

    raw = []
    audit_rows = []

    for result in results:
        gid = norm_id(result.get("game_id"))
        week = int(result.get("week") or 0)

        kickoff = feature_cutoff_for_result(result)

        home = result.get("home_team")
        away = result.get("away_team")

        for side, team, opponent in (
            ("home", home, away),
            ("away", away, home),
        ):
            p = pbp_idx.get((gid, team))
            d = drive_idx.get((gid, team))
            g = gc_idx.get((gid, team))

            entering = pregame_sp_plus(
                sp,
                team,
                kickoff,
            )
            opp_entering = pregame_sp_plus(
                sp,
                opponent,
                kickoff,
            )

            entering_sagarin = pregame_sagarin(
                sag,
                team,
                kickoff,
            )
            opp_entering_sagarin = pregame_sagarin(
                sag,
                opponent,
                kickoff,
            )

            next_game = find_next_game(
                schedule_by_team,
                team,
                gid,
                week,
            )

            close_spread_home = finite(
                result.get("closing_home_spread")
            )
            close_total = finite(
                result.get("closing_total")
            )

            close_spread = (
                close_spread_home
                if side == "home"
                else (
                    -close_spread_home
                    if close_spread_home is not None
                    else None
                )
            )

            points_scored = finite(
                result.get(
                    "home_score"
                    if side == "home"
                    else "away_score"
                )
            )
            points_allowed = finite(
                result.get(
                    "away_score"
                    if side == "home"
                    else "home_score"
                )
            )

            final_margin = (
                points_scored - points_allowed
                if points_scored is not None
                and points_allowed is not None
                else None
            )

            market_margin_team = (
                -close_spread
                if close_spread is not None
                else None
            )

            expected_team_points = (
                (close_total + market_margin_team) / 2.0
                if close_total is not None
                and market_margin_team is not None
                else None
            )

            expected_opponent_points = (
                (close_total - market_margin_team) / 2.0
                if close_total is not None
                and market_margin_team is not None
                else None
            )

            margin_surprise_team = (
                final_margin - market_margin_team
                if final_margin is not None
                and market_margin_team is not None
                else None
            )

            scoring_surprise_team = (
                points_scored - expected_team_points
                if points_scored is not None
                and expected_team_points is not None
                else None
            )

            total_surprise = (
                points_scored + points_allowed - close_total
                if points_scored is not None
                and points_allowed is not None
                and close_total is not None
                else None
            )

            opponent_scoring_surprise = (
                points_allowed - expected_opponent_points
                if points_allowed is not None
                and expected_opponent_points is not None
                else None
            )

            reasons = []

            results_available = (
                points_scored is not None
                and points_allowed is not None
            )
            if not results_available:
                reasons.append("MISSING_RESULT")

            close_available = (
                close_spread is not None
                and close_total is not None
            )
            if not close_available:
                reasons.append("MISSING_CLOSE")

            pbp_available = p is not None
            if pbp_available:
                for col in CORE_PBP:
                    if finite(p.get(col)) is None:
                        pbp_available = False
                        break
            if not pbp_available:
                reasons.append("PENDING_PBP")

            drive_available = d is not None
            if drive_available:
                for col in CORE_DRIVE:
                    if finite(d.get(col)) is None:
                        drive_available = False
                        break
            if not drive_available:
                reasons.append("PENDING_DRIVE_CONTEXT")

            game_control_available = (
                g is not None
                and finite(g.get("game_control_index"))
                is not None
            )
            if not game_control_available:
                reasons.append("PENDING_GAME_CONTROL")

            entering_ratings_available = (
                entering is not None
                and finite(entering.get("rating")) is not None
                and finite(entering.get("off_rating")) is not None
                and finite(entering.get("def_rating")) is not None
                and opp_entering is not None
                and finite(opp_entering.get("rating")) is not None
            )
            if not entering_ratings_available:
                reasons.append("MISSING_ENTERING_SP_PLUS")

            entering_sagarin_available = (
                entering_sagarin is not None
                and finite(entering_sagarin.get("rating")) is not None
                and opp_entering_sagarin is not None
                and finite(opp_entering_sagarin.get("rating")) is not None
            )

            if not entering_sagarin_available:
                reasons.append("MISSING_ENTERING_SAGARIN")

            next_status = (
                "mapped"
                if next_game is not None
                else "no_next_game"
            )
            if next_game is None:
                reasons.append("NEXT_GAME_NOT_MAPPED")

            snapshot_ts = (
                entering.get("_pulled")
                if entering is not None
                else None
            )

            sagarin_snapshot_ts = (
                entering_sagarin.get("_pulled")
                if entering_sagarin is not None
                else None
            )

            sp_plus_no_lookahead = bool(
                entering_ratings_available
                and pd.notna(kickoff)
                and pd.notna(snapshot_ts)
                and snapshot_ts < kickoff
            )

            sagarin_no_lookahead = bool(
                entering_sagarin_available
                and pd.notna(kickoff)
                and pd.notna(sagarin_snapshot_ts)
                and sagarin_snapshot_ts < kickoff
            )

            no_lookahead = sp_plus_no_lookahead

            if not sp_plus_no_lookahead:
                reasons.append("SP_PLUS_NO_LOOKAHEAD_FAIL")

            if not sagarin_no_lookahead:
                reasons.append("SAGARIN_NO_LOOKAHEAD_FAIL")

            pregame_market_rating = entering_market_rating(
                market_history,
                team,
                week,
                inference_time,
            )
            opponent_market_power_rating = entering_market_rating(
                market_history,
                opponent,
                week,
                inference_time,
            )
            if (
                pregame_market_rating is None
                or opponent_market_power_rating is None
            ):
                reasons.append("MISSING_EXACT_COMPLETED_WEEK_MARKET_STATE")

            row = {
                "season": 2026,
                "week": week,
                "completed_week": week,
                "game_id": gid,
                "completed_game_id": gid,
                "game_date": result.get("date"),
                "team": team,
                "opponent": opponent,
                "home_away": side,
                "neutral_site": bool(
                    result.get("neutral_site")
                ),

                "points_scored": points_scored,
                "points_allowed": points_allowed,
                "final_margin": final_margin,
                "closing_spread": close_spread,
                "closing_total": close_total,
                "ats_margin": (
                    final_margin + close_spread
                    if final_margin is not None
                    and close_spread is not None
                    else None
                ),
                "total_residual": (
                    points_scored
                    + points_allowed
                    - close_total
                    if points_scored is not None
                    and points_allowed is not None
                    and close_total is not None
                    else None
                ),

                # Validated historical Shadow feature contract.
                "expected_team_points": expected_team_points,
                "expected_opponent_points": expected_opponent_points,
                "margin_surprise_team": margin_surprise_team,
                "scoring_surprise_team": scoring_surprise_team,
                "total_surprise": total_surprise,
                "opponent_scoring_surprise": opponent_scoring_surprise,
                "closing_spread_team": close_spread,
                "favorite": (
                    int(close_spread < 0)
                    if close_spread is not None
                    else None
                ),
                "home_flag": int(side == "home"),

                "current_sp_plus_overall": (
                    finite(entering.get("rating"))
                    if entering
                    else None
                ),
                "current_sp_plus_offense": (
                    finite(entering.get("off_rating"))
                    if entering
                    else None
                ),
                "current_sp_plus_defense": (
                    finite(entering.get("def_rating"))
                    if entering
                    else None
                ),
                "sp_plus_entering": (
                    finite(entering.get("rating"))
                    if entering
                    else None
                ),
                "sp_plus_offense_entering": (
                    finite(entering.get("off_rating"))
                    if entering
                    else None
                ),
                "sp_plus_defense_entering": (
                    finite(entering.get("def_rating"))
                    if entering
                    else None
                ),
                "sp_plus_snapshot_timestamp": (
                    snapshot_ts.isoformat()
                    if pd.notna(snapshot_ts)
                    else None
                ),
                "opponent_sp_plus_rating": (
                    finite(opp_entering.get("rating"))
                    if opp_entering
                    else None
                ),

                "stale_spplus": (
                    finite(entering.get("rating"))
                    if entering
                    else None
                ),
                "stale_spplus_offense": (
                    finite(entering.get("off_rating"))
                    if entering
                    else None
                ),
                "stale_spplus_defense": (
                    finite(entering.get("def_rating"))
                    if entering
                    else None
                ),

                "stale_sagarin_predictor": (
                    finite(entering_sagarin.get("rating"))
                    if entering_sagarin
                    else None
                ),
                "opponent_sagarin_predictor": (
                    finite(opp_entering_sagarin.get("rating"))
                    if opp_entering_sagarin
                    else None
                ),
                "sagarin_snapshot_timestamp": (
                    entering_sagarin.get("_pulled").isoformat()
                    if entering_sagarin is not None
                    and pd.notna(entering_sagarin.get("_pulled"))
                    else None
                ),

                "pregame_market_rating": pregame_market_rating,
                "opponent_market_power_rating": opponent_market_power_rating,

                "next_game_id": (
                    next_game["game_id"]
                    if next_game
                    else None
                ),
                "next_game_week": (
                    next_game["week"]
                    if next_game
                    else None
                ),
                "next_opponent": (
                    next_game["opponent"]
                    if next_game
                    else None
                ),
                "next_home_away": (
                    next_game["home_away"]
                    if next_game
                    else None
                ),
                "next_neutral_site": (
                    next_game["neutral_site"]
                    if next_game
                    else None
                ),

                "feature_cutoff": (
                    kickoff.isoformat()
                    if pd.notna(kickoff)
                    else None
                ),
                "results_available": results_available,
                "close_available": close_available,
                "pbp_available": pbp_available,
                "drive_context_available": drive_available,
                "game_control_available": game_control_available,
                "entering_ratings_available": entering_ratings_available,
                "entering_sagarin_available": entering_sagarin_available,
                "sp_plus_no_lookahead_pass": sp_plus_no_lookahead,
                "sagarin_no_lookahead_pass": sagarin_no_lookahead,
                "next_game_mapping_status": next_status,
                "no_lookahead_pass": no_lookahead,
                "missing_reasons": reasons,
            }

            if p:
                for key, value in p.items():
                    if key in {
                        "season",
                        "week",
                        "game_id",
                        "cfbd_game_id",
                        "team",
                        "opponent",
                    }:
                        continue
                    row[key] = clean(value)

            # Exact names expected by the historically validated
            # Shadow provider-update regressions.
            row["success_rate"] = finite(row.get("off_success_rate"))
            row["ppa"] = finite(row.get("off_ppa"))
            row["explosiveness"] = finite(row.get("off_explosiveness"))
            row["def_success_rate_allowed"] = finite(
                row.get("def_success_allowed")
            )
            row["def_ppa_allowed"] = finite(
                row.get("def_ppa_allowed")
            )
            row["def_explosiveness_allowed"] = finite(
                row.get("def_explosiveness_allowed")
            )

            if d:
                mapping = {
                    "off_avg_start_ytg":
                        "drive_off_avg_start_ytg",
                    "off_points_per_opportunity":
                        "drive_off_points_per_opportunity",
                    "def_opponent_avg_start_ytg":
                        "drive_def_opponent_avg_start_ytg",
                    "def_points_per_opportunity_allowed":
                        "drive_def_points_per_opportunity_allowed",
                }
                for source, target in mapping.items():
                    row[target] = finite(d.get(source))

            if g:
                row["gc_game_control_index"] = finite(
                    g.get("game_control_index")
                )
                row["gc_raw_game_control"] = finite(
                    g.get("raw_game_control")
                )

            raw.append(row)

            audit_rows.append({
                "completed_game_id": gid,
                "week": week,
                "team": team,
                "opponent": opponent,
                "results_available": results_available,
                "close_available": close_available,
                "pbp_available": pbp_available,
                "drive_context_available": drive_available,
                "game_control_available": game_control_available,
                "entering_ratings_available": entering_ratings_available,
                "next_game_mapping_status": next_status,
                "no_lookahead_pass": no_lookahead,
                "missing_reasons": reasons,
            })

    return pd.DataFrame(raw), audit_rows


def add_rolling_features(frame: pd.DataFrame):
    if frame.empty:
        return frame

    d = frame.sort_values(
        [
            "season",
            "team",
            "week",
            "game_date",
            "game_id",
        ]
    ).copy()

    base = {
        "ats_margin": "ats",
        "off_ppa": "ppa",
        "off_success_rate": "off_eff",
        "def_ppa_allowed": "def_eff",
    }

    for col, label in base.items():
        values = pd.to_numeric(
            d[col],
            errors="coerce",
        )

        d[col] = values

        for n in (2, 3):
            d[f"trailing_{n}_game_{label}"] = (
                d.groupby(
                    ["season", "team"]
                )[col]
                .transform(
                    lambda x:
                    x.rolling(
                        n,
                        min_periods=1,
                    ).mean()
                )
            )

        d[f"season_to_date_{label}"] = (
            d.groupby(
                ["season", "team"]
            )[col]
            .transform(
                lambda x:
                x.expanding().mean()
            )
        )

        d[f"ewm_{label}"] = (
            d.groupby(
                ["season", "team"]
            )[col]
            .transform(
                lambda x:
                x.ewm(
                    alpha=0.5,
                    adjust=False,
                ).mean()
            )
        )

    d["recent_form_vs_season"] = (
        d["trailing_3_game_ats"]
        - d["season_to_date_ats"]
    )

    d["opponent_strength"] = -(
        d.groupby(
            ["season", "week"]
        )["pregame_market_rating"]
        .transform(
            lambda x: x.rank(pct=True)
        )
    )

    d["opponent_adjusted_recent_form"] = (
        d["recent_form_vs_season"]
        + d["opponent_strength"]
    )

    d["games_played"] = (
        d.groupby(
            ["season", "team"]
        ).cumcount()
        + 1
    )

    return d


def apply_repeatable_transform(
    frame: pd.DataFrame,
    state,
):
    if frame.empty:
        return frame

    d = frame.copy()

    z = {}
    for col in Z_COMPONENTS:
        values = pd.to_numeric(
            d[col],
            errors="coerce",
        )

        mu = state["z"][col]["mean"]
        sd = state["z"][col]["std"]

        z[col] = (
            (values - mu) / sd
        ).fillna(0.0)

    d["raw_ats_performance"] = d["ats_margin"]

    d["raw_score_performance"] = (
        d["final_margin"]
        + d["closing_spread"]
    )

    d["raw_pbp_performance"] = (
        2.0 * z["off_ppa"]
        + 1.2 * z["off_success_rate"]
        + 0.5 * z["off_explosiveness"]
        - 2.0 * z["def_ppa_allowed"]
        - 1.2 * z["def_success_allowed"]
        - 0.5 * z["def_explosiveness_allowed"]
    )

    d["rules_repeatable_spread"] = (
        d["raw_pbp_performance"]
        + 0.4 * z[
            "drive_off_points_per_opportunity"
        ]
        - 0.4 * z[
            "drive_def_points_per_opportunity_allowed"
        ]
        - 0.2 * z[
            "drive_off_avg_start_ytg"
        ]
        + 0.2 * z[
            "drive_def_opponent_avg_start_ytg"
        ]
    )

    regularized_x = standardize_apply(
        d,
        PERSISTENT,
        state["regularized_state"],
    )

    d["regularized_repeatable_spread"] = (
        ridge_predict(
            regularized_x,
            state["regularized_beta"],
        )
    )

    margin_x = standardize_apply(
        d,
        PERSISTENT,
        state["margin_state"],
    )

    d["persistent_expected_margin"] = (
        ridge_predict(
            margin_x,
            state["margin_beta"],
        )
    )

    d["nonpersistent_margin_residual"] = (
        d["final_margin"]
        - d["persistent_expected_margin"]
    )

    d["residualized_repeatable_spread"] = (
        d["persistent_expected_margin"]
        + d["closing_spread"]
    )

    d["repeatable_spread_performance"] = (
        d["regularized_repeatable_spread"]
    )

    d["repeatable_offense_performance"] = (
        1.7 * z["off_ppa"]
        + z["off_success_rate"]
        + 0.4
        * z["drive_off_points_per_opportunity"]
    )

    d["repeatable_defense_performance"] = (
        -1.7 * z["def_ppa_allowed"]
        - z["def_success_allowed"]
        - 0.4
        * z[
            "drive_def_points_per_opportunity_allowed"
        ]
    )

    d["repeatable_total_performance"] = (
        d["repeatable_offense_performance"]
        - d["repeatable_defense_performance"]
    )

    d["cleanup_method"] = (
        "regularized regression on "
        "efficiency/drive/game-control features; "
        "noisy residual excluded"
    )

    return d


def main():
    results = load_results()

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not results:
        empty = pd.DataFrame(
            columns=OUTPUT_META
        )

        atomic_text(
            OUT_CSV,
            empty.to_csv(index=False),
        )

        payload = {
            "schema_version":
                "shadow-team-game-features-v1",
            "generated_at": now_iso(),
            "season": 2026,
            "rows": [],
            "status": "awaiting_finalized_2026_games",
            "fixture_only": False,
        }

        atomic_text(
            OUT_JSON,
            json.dumps(
                payload,
                indent=2,
            ) + "\n",
        )

        audit = {
            "schema_version":
                "shadow-team-game-features-2026-audit-v1",
            "generated_at": now_iso(),
            "season": 2026,
            "status": "NO_COMPLETED_GAMES",
            "completed_games": 0,
            "team_game_candidates": 0,
            "eligible_rows": 0,
            "rejected_rows": 0,
        }

        atomic_text(
            AUDIT,
            json.dumps(
                audit,
                indent=2,
            ) + "\n",
        )

        print(
            json.dumps(
                audit,
                indent=2,
            )
        )
        return

    for path in (
        PBP,
        DRIVES,
        GAME_CONTROL,
        RATINGS_HISTORY,
        SCHEDULE,
        HIST_FEATURES,
    ):
        if not path.exists():
            raise SystemExit(
                f"Missing required input: {path}"
            )

    pbp = pd.read_csv(
        PBP,
        low_memory=False,
    )
    drives = pd.read_csv(DRIVES)
    try:
        gc = pd.read_csv(GAME_CONTROL)
    except pd.errors.EmptyDataError:
        gc = pd.DataFrame(columns=["game_id", "team"])

    for frame in (pbp, drives, gc):
        frame["game_id"] = frame[
            "game_id"
        ].map(norm_id)

    sp = load_entering_sp_plus()
    sag = load_entering_sagarin()
    market_history = load_market_history()

    schedule_by_team = next_game_map(
        load_schedule()
    )

    transform_state = (
        load_historical_transform_state()
    )

    features, audit_rows = combine_team_games(
        results,
        pbp,
        drives,
        gc,
        sp,
        sag,
        market_history,
        schedule_by_team,
    )

    features = add_rolling_features(features)

    required_transform_columns = sorted(
        set(
            PERSISTENT
            + Z_COMPONENTS
            + [
                "ats_margin",
                "final_margin",
                "closing_spread",
            ]
        )
    )

    for col in required_transform_columns:
        if col not in features.columns:
            features[col] = np.nan

    features = apply_repeatable_transform(
        features,
        transform_state,
    )

    validated_advanced_columns = [
        "success_rate",
        "ppa",
        "explosiveness",
        "def_success_rate_allowed",
        "def_ppa_allowed",
        "def_explosiveness_allowed",
    ]

    for col in validated_advanced_columns:
        if col not in features.columns:
            features[col] = np.nan

    advanced_ready = features[
        validated_advanced_columns
    ].notna().all(axis=1)

    features["validated_shadow_spread_ready"] = (
        features["results_available"].eq(True)
        & features["close_available"].eq(True)
        & features["entering_ratings_available"].eq(True)
        & features["entering_sagarin_available"].eq(True)
        & advanced_ready
        & features["next_game_mapping_status"].eq("mapped")
        & features["sp_plus_no_lookahead_pass"].eq(True)
        & features["sagarin_no_lookahead_pass"].eq(True)
    )

    total_required = [
        "opponent_market_power_rating",
        "stale_spplus",
        "stale_spplus_offense",
        "stale_spplus_defense",
    ]

    for col in total_required:
        if col not in features.columns:
            features[col] = np.nan

    features["validated_shadow_total_ready"] = (
        features["results_available"].eq(True)
        & features["close_available"].eq(True)
        & features["entering_ratings_available"].eq(True)
        & advanced_ready
        & features[total_required].notna().all(axis=1)
        & features["next_game_mapping_status"].eq("mapped")
        & features["no_lookahead_pass"].eq(True)
    )

    # Preserve the former bridge eligibility as audit/research metadata.
    features["legacy_bridge_ready"] = (
        features["results_available"].eq(True)
        & features["close_available"].eq(True)
        & features["pbp_available"].eq(True)
        & features["drive_context_available"].eq(True)
        & features["game_control_available"].eq(True)
        & features["entering_ratings_available"].eq(True)
        & features["next_game_mapping_status"].eq("mapped")
        & features["no_lookahead_pass"].eq(True)
    )

    # Production output is governed by the historically validated
    # Shadow model contracts. Drives and Game Control are supplemental
    # metadata and must not block validated Shadow inference.
    features["validated_shadow_any_ready"] = (
        features["validated_shadow_spread_ready"].eq(True)
        | features["validated_shadow_total_ready"].eq(True)
    )

    eligibility = features["validated_shadow_any_ready"].eq(True)

    eligible = features[
        eligibility
    ].copy()

    rejected = features[
        ~eligibility
    ].copy()

    eligible["completed_week"] = pd.to_numeric(
        eligible["completed_week"],
        errors="coerce",
    ).astype("Int64")

    eligible["completed_game_id"] = (
        eligible["completed_game_id"]
        .map(norm_id)
    )

    eligible["next_game_id"] = (
        eligible["next_game_id"]
        .map(norm_id)
    )

    rows = []

    for record in eligible.to_dict("records"):
        rows.append({
            k: clean(v)
            for k, v in record.items()
        })

    payload = {
        "schema_version":
            "shadow-team-game-features-v1",
        "generated_at": now_iso(),
        "season": 2026,
        "rows": rows,
        "status": (
            "ready"
            if rows
            else "completed_games_not_yet_shadow_ready"
        ),
        "fixture_only": False,
        "eligibility_rule": (
            "validated Shadow production row when "
            "validated_shadow_spread_ready OR "
            "validated_shadow_total_ready; "
            "drive/game-control retained as supplemental metadata"
        ),
        "validated_model_readiness": {
            "spread": (
                "result + close + pre-kickoff SP+ + "
                "pre-kickoff Sagarin + six advanced efficiency "
                "features + next-game mapping + no-lookahead"
            ),
            "total": (
                "result + close + pre-kickoff SP+ O/D + "
                "opponent market-power state + six advanced "
                "efficiency features + next-game mapping + "
                "SP+ no-lookahead"
            ),
        },
        "transform_provenance": {
            "historical_training_seasons":
                [2021, 2022, 2023],
            "historical_feature_table":
                str(
                    HIST_FEATURES.relative_to(ROOT)
                ),
            "historical_rows":
                transform_state[
                    "historical_rows"
                ],
            "market_transform_training_rows":
                transform_state[
                    "training_rows_market"
                ],
            "margin_transform_training_rows":
                transform_state[
                    "training_rows_margin"
                ],
            "uses_2026_outcomes_for_training":
                False,
        },
    }

    atomic_text(
        OUT_JSON,
        json.dumps(
            payload,
            indent=2,
            allow_nan=False,
        ) + "\n",
    )

    atomic_text(
        OUT_CSV,
        eligible.to_csv(
            index=False,
        ),
    )

    reason_counts = {}

    for row in audit_rows:
        for reason in row["missing_reasons"]:
            reason_counts[reason] = (
                reason_counts.get(
                    reason,
                    0,
                )
                + 1
            )

    audit = {
        "schema_version":
            "shadow-team-game-features-2026-audit-v1",
        "generated_at": now_iso(),
        "season": 2026,
        "status": (
            "READY"
            if len(eligible)
            else "NOT_READY"
        ),
        "completed_games": len(results),
        "team_game_candidates": len(features),
        "eligible_rows": len(eligible),
        "rejected_rows": len(rejected),
        "missing_reason_counts": reason_counts,
        "historical_transform_state": {
            "training_seasons":
                [2021, 2022, 2023],
            "market_rows":
                transform_state[
                    "training_rows_market"
                ],
            "margin_rows":
                transform_state[
                    "training_rows_margin"
                ],
        },
        "candidate_rows": audit_rows,
        "outputs": {
            "json":
                str(
                    OUT_JSON.relative_to(ROOT)
                ),
            "csv":
                str(
                    OUT_CSV.relative_to(ROOT)
                ),
        },
    }

    atomic_text(
        AUDIT,
        json.dumps(
            audit,
            indent=2,
            allow_nan=False,
        ) + "\n",
    )

    print(
        json.dumps(
            {
                "status": audit["status"],
                "completed_games":
                    len(results),
                "team_game_candidates":
                    len(features),
                "eligible_rows":
                    len(eligible),
                "rejected_rows":
                    len(rejected),
                "missing_reason_counts":
                    reason_counts,
                "output":
                    str(
                        OUT_JSON.relative_to(ROOT)
                    ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
