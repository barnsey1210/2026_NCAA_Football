#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

GAMES = ROOT / "data/research/historical_totals/master_totals_game_matrix_2021_2025.csv"

SAGARIN = (
    ROOT
    / "data/research/historical_totals/sagarin/"
    / "sagarin_totals_all_snapshots_2021_2025_deduped.csv"
)

OUT = (
    ROOT
    / "data/research/historical_totals/sagarin/"
    / "sagarin_totals_game_level_2021_2025.csv"
)

UNMATCHED = (
    ROOT
    / "data/research/historical_totals/sagarin/"
    / "sagarin_totals_unmatched_games_2021_2025.csv"
)


ALIASES = {
    "miami oh": "miami ohio",
    "ul monroe": "louisiana monroe",
    "app state": "appalachian state",
    "sam houston": "sam houston state",
    "southern california": "usc",
    "miami florida": "miami",
    "miami fl": "miami",
    "fla international": "florida international",
    "fla international fiu": "florida international",
    "florida international fiu": "florida international",
    "central florida ucf": "ucf",
    "central florida": "ucf",
    "louisiana monroe ulm": "louisiana monroe",
    "louisianamonroe ulm": "louisiana monroe",
    "louisiana lafayette": "louisiana",
    "army west point": "army",
    "connecticut": "uconn",
    "massachusetts": "umass",
    "hawai i": "hawaii",
    "hawaii": "hawaii",
    "nc state": "nc state",
    "north carolina state": "nc state",
    "ole miss": "mississippi",
    "mississippi": "mississippi",
}


def norm_team(value: str) -> str:
    s = (value or "").strip()

    # Sagarin 2024+ location markers.
    s = re.sub(r"^\s*[NC]\s+@\s+", "", s, flags=re.I)
    s = re.sub(r"^\s*@\s+", "", s)
    s = re.sub(r"^\s*[NC]\s+", "", s, flags=re.I)

    s = s.replace("_", " ")
    s = s.replace("&", " and ")

    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))

    s = s.lower()

    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    return ALIASES.get(s, s)


def pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((norm_team(a), norm_team(b))))


def parse_snapshot(ts: str) -> datetime:
    return datetime.strptime(
        ts,
        "%Y%m%d%H%M%S",
    ).replace(tzinfo=timezone.utc)


def parse_kickoff(value: str) -> datetime:
    # Example:
    # 2021-11-26T20:30:00.000Z
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def main() -> None:
    with SAGARIN.open(newline="") as f:
        sag_rows = list(csv.DictReader(f))

    with GAMES.open(newline="") as f:
        games = list(csv.DictReader(f))

    # Index every Sagarin snapshot by season + unordered matchup.
    index = defaultdict(list)

    for r in sag_rows:
        key = (
            r["season"],
            pair_key(
                r["favorite_raw"],
                r["underdog_raw"],
            ),
        )

        index[key].append(r)

    for rows in index.values():
        rows.sort(
            key=lambda r: r["snapshot_timestamp"]
        )

    matched = []
    unmatched = []

    for g in games:
        season = g["season"]

        key = (
            season,
            pair_key(
                g["home_team"],
                g["away_team"],
            ),
        )

        kickoff = parse_kickoff(g["start_date"])

        candidates = []

        for r in index.get(key, []):
            snap = parse_snapshot(
                r["snapshot_timestamp"]
            )

            # Strictly pregame.
            if snap < kickoff:
                candidates.append((snap, r))

        if not candidates:
            unmatched.append({
                "game_id": g["game_id"],
                "season": season,
                "week": g["week"],
                "start_date": g["start_date"],
                "away_team": g["away_team"],
                "home_team": g["home_team"],
                "opening_total": g["opening_total"],
                "closing_total": g["closing_total"],
                "actual_total": g.get(
                    "actual_total",
                    g.get("actual_total_points", ""),
                ),
                "normalized_away": norm_team(
                    g["away_team"]
                ),
                "normalized_home": norm_team(
                    g["home_team"]
                ),
            })
            continue

        snap, r = candidates[-1]

        age_hours = (
            kickoff - snap
        ).total_seconds() / 3600.0

        matched.append({
            "game_id": g["game_id"],
            "season": season,
            "week": g["week"],
            "start_date": g["start_date"],
            "away_team": g["away_team"],
            "home_team": g["home_team"],
            "opening_total": g["opening_total"],
            "closing_total": g["closing_total"],
            "actual_total": g.get(
                "actual_total",
                g.get("actual_total_points", ""),
            ),
            "sagarin_total": r["sagarin_total"],
            "sagarin_snapshot_timestamp":
                r["snapshot_timestamp"],
            "sagarin_snapshot_age_hours":
                round(age_hours, 2),
            "sagarin_snapshot_age_days":
                round(age_hours / 24.0, 2),
            "sagarin_format": r["format"],
            "sagarin_source_url": r["source_url"],
        })

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    matched_fields = [
        "game_id",
        "season",
        "week",
        "start_date",
        "away_team",
        "home_team",
        "opening_total",
        "closing_total",
        "actual_total",
        "sagarin_total",
        "sagarin_snapshot_timestamp",
        "sagarin_snapshot_age_hours",
        "sagarin_snapshot_age_days",
        "sagarin_format",
        "sagarin_source_url",
    ]

    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=matched_fields,
        )
        w.writeheader()
        w.writerows(matched)

    unmatched_fields = [
        "game_id",
        "season",
        "week",
        "start_date",
        "away_team",
        "home_team",
        "opening_total",
        "closing_total",
        "actual_total",
        "normalized_away",
        "normalized_home",
    ]

    with UNMATCHED.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=unmatched_fields,
        )
        w.writeheader()
        w.writerows(unmatched)

    print("===== SAGARIN GAME-LEVEL COVERAGE =====")
    print("historical games:", len(games))
    print("matched:", len(matched))
    print("unmatched:", len(unmatched))

    print()
    print("===== BY SEASON =====")

    for season in [
        "2021",
        "2022",
        "2023",
        "2024",
        "2025",
    ]:
        total = sum(
            g["season"] == season
            for g in games
        )

        m = [
            r for r in matched
            if r["season"] == season
        ]

        pct = (
            100 * len(m) / total
            if total else 0
        )

        print(
            season,
            f"games={total}",
            f"matched={len(m)}",
            f"coverage={pct:.1f}%",
        )

    print()
    print("===== SNAPSHOT AGE =====")

    buckets = Counter()

    for r in matched:
        h = float(
            r["sagarin_snapshot_age_hours"]
        )

        if h <= 24:
            bucket = "<=24h"
        elif h <= 72:
            bucket = "24-72h"
        elif h <= 168:
            bucket = "3-7d"
        elif h <= 336:
            bucket = "7-14d"
        else:
            bucket = ">14d"

        buckets[bucket] += 1

    for bucket in [
        "<=24h",
        "24-72h",
        "3-7d",
        "7-14d",
        ">14d",
    ]:
        print(
            bucket,
            buckets[bucket],
        )

    print()
    print("===== MOST COMMON UNMATCHED TEAMS =====")

    c = Counter()

    for r in unmatched:
        c[r["home_team"]] += 1
        c[r["away_team"]] += 1

    for team, n in c.most_common(30):
        print(f"{team}: {n}")

    print()
    print("wrote:", OUT)
    print("unmatched:", UNMATCHED)


if __name__ == "__main__":
    main()
