#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.site.team_identity import canonical_team_key

RESULTS = ROOT / "data/canonical/game_results_2026.json"
POSTGAME_ROOT = ROOT / "data/canonical/postgame/2026"

OUT_DIR = ROOT / "data/canonical/postgame/2026/features"
PBP_OUT = OUT_DIR / "team_game_tendencies_2026.csv"
DRIVE_OUT = OUT_DIR / "team_game_drive_context_2026.csv"
GC_OUT = OUT_DIR / "team_game_game_control_2026.csv"
AUDIT_OUT = ROOT / "data/audits/postgame_features_2026_audit.json"

RUN_TYPES = {"Rush", "Rushing Touchdown"}
PASS_TYPES = {
    "Pass Reception", "Pass Incompletion", "Passing Touchdown", "Interception",
    "Pass Interception Return", "Interception Return", "Interception Return Touchdown", "Sack",
}


def read_gzip(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def finite(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def mean(values):
    vals = [float(v) for v in values if finite(v) is not None]
    return sum(vals) / len(vals) if vals else None


def safe_div(a, b):
    return a / b if b else None


def is_run(play):
    if play.get("playType") in RUN_TYPES:
        return True
    if str(play.get("playType") or "").startswith("Fumble"):
        return " run for" in str(play.get("playText") or "").lower()
    return False


def is_pass(play):
    if play.get("playType") in PASS_TYPES:
        return True
    if str(play.get("playType") or "").startswith("Fumble"):
        text = str(play.get("playText") or "").lower()
        return " pass " in text or "pass complete" in text or " sacked" in text
    return False


def is_scrimmage(play):
    return is_run(play) or is_pass(play)


def competitive_play(play):
    try:
        period = int(play.get("period") or 0)
        margin = abs(
            int(play.get("offenseScore") or 0)
            - int(play.get("defenseScore") or 0)
        )
    except Exception:
        return True

    if period <= 0:
        return True
    if period > 4:
        return False

    thresholds = {2: 38, 3: 28, 4: 22}
    return period == 1 or margin <= thresholds.get(period, 10000)


def clock_seconds(play):
    clock = play.get("clock") or {}
    try:
        return int(clock.get("minutes") or 0) * 60 + int(clock.get("seconds") or 0)
    except Exception:
        return None


def game_clock_seconds_per_play(plays):
    gaps = []
    by_drive = defaultdict(list)

    for play in plays:
        if is_scrimmage(play) and play.get("driveId") is not None:
            by_drive[str(play["driveId"])].append(play)

    for dplays in by_drive.values():
        ordered = sorted(dplays, key=lambda p: int(p.get("playNumber") or 0))
        for current, following in zip(ordered, ordered[1:]):
            if current.get("period") != following.get("period"):
                continue
            start = clock_seconds(current)
            end = clock_seconds(following)
            if start is not None and end is not None and 0 <= start - end <= 90:
                gaps.append(start - end)

    return mean(gaps)


def summarize_offense(plays):
    scrimmage = [p for p in plays if is_scrimmage(p)]
    runs = [p for p in scrimmage if is_run(p)]
    passes = [p for p in scrimmage if is_pass(p)]

    ppa = [finite(p.get("ppa")) for p in scrimmage]
    ppa = [x for x in ppa if x is not None]
    successful = [x for x in ppa if x > 0]

    return {
        "off_plays": len(scrimmage),
        "off_rush_success_rate": safe_div(
            sum((finite(p.get("ppa")) or 0) > 0 for p in runs if finite(p.get("ppa")) is not None),
            sum(finite(p.get("ppa")) is not None for p in runs),
        ),
        "off_pass_success_rate": safe_div(
            sum((finite(p.get("ppa")) or 0) > 0 for p in passes if finite(p.get("ppa")) is not None),
            sum(finite(p.get("ppa")) is not None for p in passes),
        ),
        "off_success_rate": safe_div(len(successful), len(ppa)),
        "off_explosiveness": mean(successful),
        "off_ppa": mean(ppa),
        "off_game_clock_seconds_per_play": game_clock_seconds_per_play(scrimmage),
    }


def summarize_defense(plays):
    scrimmage = [p for p in plays if is_scrimmage(p)]
    runs = [p for p in scrimmage if is_run(p)]
    passes = [p for p in scrimmage if is_pass(p)]

    ppa = [finite(p.get("ppa")) for p in scrimmage]
    ppa = [x for x in ppa if x is not None]
    successful = [x for x in ppa if x > 0]

    return {
        "def_rush_success_allowed": safe_div(
            sum((finite(p.get("ppa")) or 0) > 0 for p in runs if finite(p.get("ppa")) is not None),
            sum(finite(p.get("ppa")) is not None for p in runs),
        ),
        "def_pass_success_allowed": safe_div(
            sum((finite(p.get("ppa")) or 0) > 0 for p in passes if finite(p.get("ppa")) is not None),
            sum(finite(p.get("ppa")) is not None for p in passes),
        ),
        "def_success_allowed": safe_div(len(successful), len(ppa)),
        "def_explosiveness_allowed": mean(successful),
        "def_ppa_allowed": mean(ppa),
    }


def havoc_value(row):
    if not row:
        return None

    for key in (
        "total",
        "havoc",
        "totalHavoc",
        "havocRate",
        "total_havoc",
    ):
        x = finite(row.get(key))
        if x is not None:
            return x

    total = row.get("total") or {}
    if isinstance(total, dict):
        for key in ("total", "havoc", "rate"):
            x = finite(total.get(key))
            if x is not None:
                return x

    return None


def build_pbp_rows(week, results, plays, havoc):
    offense = defaultdict(list)
    defense = defaultdict(list)

    for p in plays:
        gid = str(p.get("gameId") or "")
        off = canonical_team_key(p.get("offense"))
        deff = canonical_team_key(p.get("defense"))

        if gid and off:
            offense[(gid, off)].append(p)
        if gid and deff:
            defense[(gid, deff)].append(p)

    havoc_map = {}
    for h in havoc:
        gid = str(h.get("gameId") or "")
        team = canonical_team_key(h.get("team"))
        if gid and team:
            havoc_map[(gid, team)] = h

    rows = []
    for r in results:
        gid = str(r.get("cfbd_game_id") or "")
        for team, opp in (
            (r["home_team"], r["away_team"]),
            (r["away_team"], r["home_team"]),
        ):
            team_key = canonical_team_key(team)
            op = [p for p in offense.get((gid, team_key), []) if competitive_play(p)]
            dp = [p for p in defense.get((gid, team_key), []) if competitive_play(p)]

            row = {
                "season": 2026,
                "week": week,
                "game_id": r["game_id"],
                "cfbd_game_id": gid,
                "team": team,
                "opponent": opp,
            }
            row.update(summarize_offense(op))
            row.update(summarize_defense(dp))
            row["def_havoc_rate"] = havoc_value(havoc_map.get((gid, team_key)))
            rows.append(row)

    return rows


def competitive_drive(d):
    try:
        period = int(d.get("startPeriod") or 0)
        margin = abs(
            int(d.get("startOffenseScore") or 0)
            - int(d.get("startDefenseScore") or 0)
        )
        plays = int(d.get("plays") or 0)
    except Exception:
        return False

    if period < 1 or period > 4 or plays < 1:
        return False

    return period == 1 or margin <= {2: 38, 3: 28, 4: 22}.get(period, 10000)


def build_drive_rows(week, results, plays, drives):
    closest = {}

    for p in plays:
        drive_id = p.get("driveId")
        ytg = finite(p.get("yardsToGoal"))
        if drive_id is None or ytg is None:
            continue
        key = str(drive_id)
        closest[key] = min(ytg, closest.get(key, 1000.0))

    grouped = defaultdict(list)

    result_by_cfbd = {
        str(r.get("cfbd_game_id")): r
        for r in results
    }

    for d in drives:
        gid = str(d.get("gameId") or "")
        result = result_by_cfbd.get(gid)
        if not result or not competitive_drive(d):
            continue

        offense = canonical_team_key(d.get("offense"))
        defense = canonical_team_key(d.get("defense"))

        result_team_keys = {
            canonical_team_key(result["home_team"]),
            canonical_team_key(result["away_team"]),
        }
        if offense not in result_team_keys:
            continue

        start_ytg = finite(d.get("startYardsToGoal"))
        end_ytg = finite(d.get("endYardsToGoal"))

        if start_ytg is None or not 0 <= start_ytg <= 100:
            continue

        points = max(
            0.0,
            (finite(d.get("endOffenseScore")) or 0)
            - (finite(d.get("startOffenseScore")) or 0),
        )

        min_ytg = min(
            start_ytg,
            end_ytg if end_ytg is not None and 0 <= end_ytg <= 100 else 100,
            closest.get(str(d.get("id")), 100),
        )

        grouped[(gid, offense, defense)].append({
            "start_ytg": start_ytg,
            "opportunity": min_ytg <= 40,
            "opp_points": points if min_ytg <= 40 else 0.0,
        })

    offense_rows = {}
    for (gid, team, opp), ds in grouped.items():
        opportunities = sum(x["opportunity"] for x in ds)

        offense_rows[(gid, team)] = {
            "off_drives": len(ds),
            "off_avg_start_ytg": mean(x["start_ytg"] for x in ds),
            "off_opportunities": opportunities,
            "off_points_per_opportunity": (
                sum(x["opp_points"] for x in ds) / opportunities
                if opportunities
                else None
            ),
        }

    rows = []
    for r in results:
        gid = str(r.get("cfbd_game_id") or "")
        for team, opp in (
            (r["home_team"], r["away_team"]),
            (r["away_team"], r["home_team"]),
        ):
            own = offense_rows.get((gid, canonical_team_key(team)), {})
            opponent = offense_rows.get((gid, canonical_team_key(opp)), {})

            rows.append({
                "season": 2026,
                "week": week,
                "game_id": r["game_id"],
                "cfbd_game_id": gid,
                "team": team,
                "opponent": opp,
                "off_drives": own.get("off_drives"),
                "off_avg_start_ytg": own.get("off_avg_start_ytg"),
                "off_opportunities": own.get("off_opportunities"),
                "off_points_per_opportunity": own.get("off_points_per_opportunity"),
                "def_drives": opponent.get("off_drives"),
                "def_opponent_avg_start_ytg": opponent.get("off_avg_start_ytg"),
                "def_opportunities_allowed": opponent.get("off_opportunities"),
                "def_points_per_opportunity_allowed": opponent.get("off_points_per_opportunity"),
            })

    return rows


def remaining_seconds(play):
    period = int(finite(play.get("period")) or 0)
    if period < 1 or period > 4:
        return None

    clock = play.get("clock") or {}
    return (
        (4 - period) * 900
        + int(finite(clock.get("minutes")) or 0) * 60
        + int(finite(clock.get("seconds")) or 0)
    )


def play_scores(play):
    home = canonical_team_key(play.get("home"))
    away = canonical_team_key(play.get("away"))
    offense = canonical_team_key(play.get("offense"))

    offense_score = finite(play.get("offenseScore")) or 0
    defense_score = finite(play.get("defenseScore")) or 0

    if offense == home:
        return offense_score, defense_score
    if offense == away:
        return defense_score, offense_score
    return 0.0, 0.0


def home_win_probability(play, seconds_left):
    home = canonical_team_key(play.get("home"))
    away = canonical_team_key(play.get("away"))
    offense = canonical_team_key(play.get("offense"))

    home_score, away_score = play_scores(play)

    offense_sign = (
        1.0 if offense == home
        else -1.0 if offense == away
        else 0.0
    )

    yards_to_goal = max(
        1.0,
        min(100.0, finite(play.get("yardsToGoal")) or 75.0),
    )
    down = max(1.0, min(4.0, finite(play.get("down")) or 1.0))
    distance = max(0.0, min(40.0, finite(play.get("distance")) or 10.0))

    possession_value = offense_sign * (
        0.45 + 1.65 * (1.0 - yards_to_goal / 100.0)
    )
    possession_value -= offense_sign * (
        0.14 * (down - 1.0)
        + 0.025 * max(0.0, distance - 10.0)
    )

    state_margin = (home_score - away_score) + possession_value
    scale = 2.8 + 11.2 * math.sqrt(max(0.0, seconds_left) / 3600.0)
    z = max(-20.0, min(20.0, state_margin / scale))

    return 1.0 / (1.0 + math.exp(-z))


def build_game_control_rows(week, results, plays):
    by_game = defaultdict(list)

    for p in plays:
        seconds = remaining_seconds(p)
        gid = str(p.get("gameId") or "")
        if gid and seconds is not None:
            by_game[gid].append((seconds, p))

    result_by_cfbd = {
        str(r.get("cfbd_game_id")): r
        for r in results
    }

    rows = []

    for gid, states in by_game.items():
        result = result_by_cfbd.get(gid)
        if not result:
            continue

        states.sort(
            key=lambda item: (
                -item[0],
                finite(item[1].get("playNumber")) or 0,
            )
        )

        area = 0.0
        previous = 3600
        last_probability = 0.5

        for seconds, play in states:
            if seconds > previous:
                continue

            area += last_probability * (previous - seconds)
            last_probability = home_win_probability(play, seconds)
            previous = seconds

        area += last_probability * previous
        home_gc = area / 3600.0

        home = result["home_team"]
        away = result["away_team"]

        rows.extend([
            {
                "season": 2026,
                "week": week,
                "game_id": result["game_id"],
                "cfbd_game_id": gid,
                "team": home,
                "opponent": away,
                "home_away": "home",
                "raw_game_control": home_gc,
                "control_auc": home_gc,
                "game_control_index": 100.0 * (home_gc - 0.5),
                "play_states": len(states),
            },
            {
                "season": 2026,
                "week": week,
                "game_id": result["game_id"],
                "cfbd_game_id": gid,
                "team": away,
                "opponent": home,
                "home_away": "away",
                "raw_game_control": 1.0 - home_gc,
                "control_auc": 1.0 - home_gc,
                "game_control_index": 100.0 * (0.5 - home_gc),
                "play_states": len(states),
            },
        ])

    return rows


def write_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)

    with tempfile.NamedTemporaryFile(
        "w",
        dir=path.parent,
        delete=False,
        encoding="utf-8",
    ) as handle:
        frame.to_csv(handle.name, index=False)
        tmp = Path(handle.name)

    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int)
    args = parser.parse_args()

    if not RESULTS.exists():
        raise SystemExit(f"Missing {RESULTS}")

    payload = json.loads(RESULTS.read_text())
    all_results = [
        r for r in payload.get("games", [])
        if r.get("completed")
    ]

    weeks = sorted({
        int(r["week"])
        for r in all_results
        if r.get("week") is not None
    })

    week = args.week if args.week is not None else (weeks[-1] if weeks else None)

    if week is None:
        audit = {
            "schema_version": "postgame-features-2026-audit-v1",
            "season": 2026,
            "status": "NO_COMPLETED_GAMES",
            "week": None,
            "completed_games": 0,
            "team_game_rows_expected": 0,
            "pbp_rows": 0,
            "drive_rows": 0,
            "game_control_rows": 0,
        }
        AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_OUT.write_text(json.dumps(audit, indent=2) + "\n")
        print(json.dumps(audit, indent=2))
        return

    target_weeks = [args.week] if args.week is not None else weeks

    pbp_rows = []
    drive_rows = []
    gc_rows = []
    processed_weeks = []
    missing_week_caches = []

    for week in target_weeks:
        results = [
            r for r in all_results
            if int(r["week"]) == int(week)
        ]
        if not results:
            continue

        week_dir = POSTGAME_ROOT / f"week_{week:02d}"
        plays_path = week_dir / "plays.json.gz"
        drives_path = week_dir / "drives.json.gz"
        havoc_path = week_dir / "havoc.json.gz"

        missing = [
            str(path.relative_to(ROOT))
            for path in (plays_path, drives_path, havoc_path)
            if not path.exists()
        ]
        if missing:
            missing_week_caches.append({
                "week": week,
                "missing": missing,
            })
            continue

        plays = read_gzip(plays_path)
        drives = read_gzip(drives_path)
        havoc = read_gzip(havoc_path)

        pbp_rows.extend(
            build_pbp_rows(week, results, plays, havoc)
        )
        drive_rows.extend(
            build_drive_rows(week, results, plays, drives)
        )
        gc_rows.extend(
            build_game_control_rows(week, results, plays)
        )
        processed_weeks.append(week)

    write_csv(pbp_rows, PBP_OUT)
    write_csv(drive_rows, DRIVE_OUT)
    write_csv(gc_rows, GC_OUT)

    completed_in_processed_weeks = [
        r for r in all_results
        if int(r["week"]) in set(processed_weeks)
    ]
    expected = len(completed_in_processed_weeks) * 2

    def coverage(rows, key):
        return sum(finite(r.get(key)) is not None for r in rows)

    audit = {
        "schema_version": "postgame-features-2026-audit-v1",
        "season": 2026,
        "status": (
            "READY"
            if not missing_week_caches
            and len(pbp_rows) == expected
            and len(drive_rows) == expected
            and len(gc_rows) == expected
            else "PARTIAL"
        ),
        "week": max(processed_weeks) if processed_weeks else None,
        "weeks_requested": target_weeks,
        "weeks_processed": processed_weeks,
        "missing_week_caches": missing_week_caches,
        "completed_games": len(completed_in_processed_weeks),
        "team_game_rows_expected": expected,
        "pbp_rows": len(pbp_rows),
        "drive_rows": len(drive_rows),
        "game_control_rows": len(gc_rows),
        "pbp_core_coverage": {
            "off_ppa": coverage(pbp_rows, "off_ppa"),
            "off_success_rate": coverage(pbp_rows, "off_success_rate"),
            "off_explosiveness": coverage(pbp_rows, "off_explosiveness"),
            "def_ppa_allowed": coverage(pbp_rows, "def_ppa_allowed"),
            "def_success_allowed": coverage(pbp_rows, "def_success_allowed"),
            "def_explosiveness_allowed": coverage(pbp_rows, "def_explosiveness_allowed"),
            "def_havoc_rate": coverage(pbp_rows, "def_havoc_rate"),
            "off_plays": coverage(pbp_rows, "off_plays"),
        },
        "drive_core_coverage": {
            "off_points_per_opportunity": coverage(drive_rows, "off_points_per_opportunity"),
            "def_points_per_opportunity_allowed": coverage(
                drive_rows,
                "def_points_per_opportunity_allowed",
            ),
        },
        "game_control_coverage": coverage(
            gc_rows,
            "game_control_index",
        ),
        "outputs": {
            "pbp": str(PBP_OUT.relative_to(ROOT)),
            "drive": str(DRIVE_OUT.relative_to(ROOT)),
            "game_control": str(GC_OUT.relative_to(ROOT)),
        },
    }

    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(
        json.dumps(audit, indent=2, allow_nan=False) + "\n"
    )

    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
