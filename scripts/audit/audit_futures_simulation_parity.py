#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = Path(os.environ.get("NCAAF_RUNTIME_ROOT") or SOURCE_ROOT)

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from scripts.site.team_identity import canonical_team_name

FUTURES = RUNTIME_ROOT / "data/site/futures_view.json"
SIMS = RUNTIME_ROOT / "data/site/season_simulations_2026.json"
SCHEDULE = RUNTIME_ROOT / "data/canonical/cfbd_schedule_2026.json"
PRESEASON = RUNTIME_ROOT / "data/snapshots/preseason/preseason_db.json"
RESULTS = RUNTIME_ROOT / "data/canonical/game_results_2026.json"

PARITY_TOLERANCE = 0.05


def canon(value):
    raw = str(value or "").strip()
    return canonical_team_name(raw) or raw or None


def load(path):
    if not path.exists():
        raise SystemExit(f"FAIL missing required file: {path}")
    return json.loads(path.read_text())


def main():
    futures = load(FUTURES)
    sims = load(SIMS)
    schedule = load(SCHEDULE)
    preseason = load(PRESEASON)
    results = load(RESULTS)

    rows = futures.get("rows", [])
    modeled = {canon(row.get("team")) for row in rows if row.get("team")}

    canonical_counts = {team: 0 for team in modeled}
    preseason_counts = {team: 0 for team in modeled}

    for game in schedule.get("games", []):
        if str(game.get("season_type") or "regular").lower() != "regular":
            continue
        away = canon(game.get("away_team"))
        home = canon(game.get("home_team"))
        if away in canonical_counts:
            canonical_counts[away] += 1
        if home in canonical_counts:
            canonical_counts[home] += 1

    for game in preseason.get("games", []):
        if game.get("week") == 14:
            continue
        away = canon(game.get("away_team"))
        home = canon(game.get("home_team"))
        if away in preseason_counts:
            preseason_counts[away] += 1
        if home in preseason_counts:
            preseason_counts[home] += 1

    schedule_failures = []
    for team in sorted(modeled):
        if canonical_counts.get(team) != preseason_counts.get(team):
            schedule_failures.append(
                (
                    team,
                    canonical_counts.get(team),
                    preseason_counts.get(team),
                )
            )

    coverage_failures = []
    parity_failures = []
    parity_rows = []

    for row in rows:
        team = row.get("team")
        remaining = row.get("games_remaining")
        covered = row.get("win_probability_games_remaining")
        sim = row.get("projected_wins")
        projected = (row.get("projected_record") or {}).get("wins")

        if remaining != covered:
            coverage_failures.append((team, remaining, covered))
            continue

        if sim is None or projected is None:
            coverage_failures.append((team, remaining, covered))
            continue

        delta = float(sim) - float(projected)
        parity_rows.append((abs(delta), delta, team, float(sim), float(projected)))

        if abs(delta) > PARITY_TOLERANCE:
            parity_failures.append(
                (team, float(sim), float(projected), delta)
            )

    valid_completed_results = 0
    for game in results.get("games", []):
        if not game.get("completed"):
            continue
        away_score = game.get("away_score")
        home_score = game.get("home_score")
        if away_score is None or home_score is None:
            continue
        try:
            if float(away_score) == float(home_score):
                continue
        except (TypeError, ValueError):
            continue
        valid_completed_results += 1

    frozen = sims.get("completed_finals_frozen")
    frozen_ok = frozen == valid_completed_results

    parity_rows.sort(reverse=True)
    mean_abs = (
        sum(row[0] for row in parity_rows) / len(parity_rows)
        if parity_rows
        else None
    )

    print(f"teams_total={len(rows)}")
    print(f"schedule_count_pass={len(modeled) - len(schedule_failures)}/{len(modeled)}")
    print(f"coverage_pass={len(rows) - len(coverage_failures)}/{len(rows)}")
    print(f"parity_comparable={len(parity_rows)}")
    print(f"parity_within_{PARITY_TOLERANCE:.2f}={len(parity_rows) - len(parity_failures)}/{len(parity_rows)}")
    print(f"mean_absolute_difference={mean_abs:.6f}" if mean_abs is not None else "mean_absolute_difference=None")
    print(f"completed_results={valid_completed_results}")
    print(f"completed_finals_frozen={frozen}")
    print(f"completed_finals_match={'PASS' if frozen_ok else 'FAIL'}")

    print()
    print("WORST PARITY DELTAS")
    for _, delta, team, sim, projected in parity_rows[:10]:
        print(
            f"{team:24} sim={sim:7.4f} "
            f"sum={projected:7.4f} delta={delta:+7.4f}"
        )

    if schedule_failures:
        print()
        print("SCHEDULE COUNT FAILURES")
        for team, canonical_count, preseason_count in schedule_failures:
            print(
                f"{team}: canonical={canonical_count} "
                f"simulation_schedule={preseason_count}"
            )

    if coverage_failures:
        print()
        print("COVERAGE FAILURES")
        for team, remaining, covered in coverage_failures:
            print(f"{team}: remaining={remaining} covered={covered}")

    if parity_failures:
        print()
        print("PARITY FAILURES")
        for team, sim, projected, delta in parity_failures:
            print(
                f"{team}: sim={sim:.4f} "
                f"sum={projected:.4f} delta={delta:+.4f}"
            )

    failed = (
        bool(schedule_failures)
        or bool(coverage_failures)
        or bool(parity_failures)
        or not frozen_ok
        or len(rows) != 138
        or len(parity_rows) != 138
    )

    if failed:
        raise SystemExit("FAIL futures/simulation parity audit")

    print()
    print("PASS futures/simulation parity audit")


if __name__ == "__main__":
    main()
