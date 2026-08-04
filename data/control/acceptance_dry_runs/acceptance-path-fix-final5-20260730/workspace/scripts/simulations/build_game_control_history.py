#!/usr/bin/env python3
"""Build an open, reproducible Game Control proxy from cached CFBD play states.

This is not the proprietary SportSource Analytics metric.  For every regulation
play, it estimates the home team's win probability from score, time remaining,
possession, field position, down, and distance.  The raw game value is the
time-weighted area under that curve.  Season/weekly values are schedule-adjusted
later, once opponent win percentages are known.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fnum(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def remaining_seconds(play):
    period = int(fnum(play.get("period"), 0))
    if period < 1 or period > 4:
        return None
    clock = play.get("clock") or {}
    return (4 - period) * 900 + int(fnum(clock.get("minutes"))) * 60 + int(fnum(clock.get("seconds")))


def play_scores(play):
    home, away, offense = play.get("home"), play.get("away"), play.get("offense")
    offense_score, defense_score = fnum(play.get("offenseScore")), fnum(play.get("defenseScore"))
    if offense == home:
        return offense_score, defense_score
    if offense == away:
        return defense_score, offense_score
    return 0.0, 0.0


def home_win_probability(play, seconds_left):
    """Transparent play-state model used only for this open Game Control proxy."""
    home, away, offense = play.get("home"), play.get("away"), play.get("offense")
    home_score, away_score = play_scores(play)
    offense_sign = 1.0 if offense == home else -1.0 if offense == away else 0.0
    yards_to_goal = max(1.0, min(100.0, fnum(play.get("yardsToGoal"), 75.0)))
    down = max(1.0, min(4.0, fnum(play.get("down"), 1.0)))
    distance = max(0.0, min(40.0, fnum(play.get("distance"), 10.0)))
    possession_value = offense_sign * (0.45 + 1.65 * (1.0 - yards_to_goal / 100.0))
    possession_value -= offense_sign * (0.14 * (down - 1.0) + 0.025 * max(0.0, distance - 10.0))
    state_margin = (home_score - away_score) + possession_value
    # Early-game state needs much more evidence than late-game state.
    scale = 2.8 + 11.2 * math.sqrt(max(0.0, seconds_left) / 3600.0)
    z = max(-20.0, min(20.0, state_margin / scale))
    return 1.0 / (1.0 + math.exp(-z))


def game_rows(plays):
    by_game = defaultdict(list)
    for play in plays:
        seconds = remaining_seconds(play)
        if seconds is not None and play.get("gameId") is not None:
            by_game[str(play["gameId"])].append((seconds, play))
    output = []
    for game_id, states in by_game.items():
        states.sort(key=lambda item: (-item[0], fnum(item[1].get("playNumber"))))
        first = states[0][1]
        home, away = first.get("home"), first.get("away")
        if not home or not away:
            continue
        area, previous = 0.0, 3600
        last_probability = 0.5
        for seconds, play in states:
            if seconds > previous:
                continue
            area += last_probability * (previous - seconds)
            last_probability = home_win_probability(play, seconds)
            previous = seconds
        area += last_probability * previous
        home_gc = area / 3600.0
        output.extend([
            {"game_id": game_id, "team": home, "opponent": away, "home_away": "home", "raw_game_control": home_gc,
             "control_auc": home_gc, "game_control_index": 100.0 * (home_gc - 0.5), "play_states": len(states)},
            {"game_id": game_id, "team": away, "opponent": home, "home_away": "away", "raw_game_control": 1.0 - home_gc,
             "control_auc": 1.0 - home_gc, "game_control_index": 100.0 * (0.5 - home_gc), "play_states": len(states)},
        ])
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-root", type=Path, default=ROOT / "cfbd_cache/pbp_history")
    parser.add_argument("--output", type=Path, default=ROOT / "data/research/game_control_history_2021_2025/team_game_game_control.csv")
    args = parser.parse_args()
    rows = []
    for path in sorted(args.cache_root.rglob("plays_week_*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        season = next((part for part in path.parts if part.isdigit() and len(part) == 4), "")
        week = path.stem.split("_")[-1].split(".")[0]
        for row in game_rows(payload.get("data", [])):
            row.update({"season": season, "week": week, "source_file": str(path.relative_to(ROOT))})
            rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["season", "week", "game_id", "team", "opponent", "home_away", "raw_game_control", "control_auc",
              "game_control_index", "play_states", "source_file"]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {len(rows)} team-game Game Control rows to {args.output}")


if __name__ == "__main__":
    main()
