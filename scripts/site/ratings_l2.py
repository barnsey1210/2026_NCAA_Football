"""Canonical four-source historical baselines for Ratings-page L2 change."""

import csv
import statistics
from collections import defaultdict
from datetime import date


HISTORICAL_SOURCES = {
    "SP+": "spplus",
    "FPI": "fpi",
    "TeamRankings": "teamrankings",
    # The canonical ratings master zero-centers Sagarin's main Rating field.
    "Sagarin Rating": "sagarin",
}


def _cycle_key(snapshot_date):
    iso = date.fromisoformat(snapshot_date).isocalendar()
    return iso.year, iso.week


def canonical_cycle_snapshots(history_path, season="2026", min_teams=130):
    """Return the latest complete four-source snapshot in each ISO week.

    Repeated accepted rows within a day are collapsed to the latest pull. A
    team is included only when all four canonical sources are present. Sagarin
    is zero-centered cross-sectionally exactly as the canonical ratings master
    does; reference-only feeds never enter this calculation.
    """
    latest_rows = {}

    with history_path.open() as handle:
        for row in csv.DictReader(handle):
            source = row.get("source")
            snapshot_date = row.get("snapshot_date")
            team = row.get("team")
            if (
                row.get("season") != str(season)
                or source not in HISTORICAL_SOURCES
                or not snapshot_date
                or not team
            ):
                continue
            try:
                float(row["rating"])
                date.fromisoformat(snapshot_date)
            except (KeyError, TypeError, ValueError):
                continue

            key = (snapshot_date, source, team)
            prior = latest_rows.get(key)
            if prior is None or (row.get("pulled_at") or "") >= (
                prior.get("pulled_at") or ""
            ):
                latest_rows[key] = row

    by_date = defaultdict(lambda: defaultdict(dict))
    for (snapshot_date, source, team), row in latest_rows.items():
        by_date[snapshot_date][source][team] = float(row["rating"])

    complete_by_date = {}
    for snapshot_date, sources in by_date.items():
        if not all(source in sources for source in HISTORICAL_SOURCES):
            continue
        complete_teams = set.intersection(
            *(set(sources[source]) for source in HISTORICAL_SOURCES)
        )
        if len(complete_teams) < min_teams:
            continue

        sagarin_values = sources["Sagarin Rating"].values()
        sagarin_mean = statistics.mean(sagarin_values)
        composites = {}
        for team in complete_teams:
            composites[team] = statistics.mean((
                sources["SP+"][team],
                sources["FPI"][team],
                sources["TeamRankings"][team],
                sources["Sagarin Rating"][team] - sagarin_mean,
            ))
        complete_by_date[snapshot_date] = composites

    by_cycle = {}
    for snapshot_date, composites in complete_by_date.items():
        cycle = _cycle_key(snapshot_date)
        if cycle not in by_cycle or snapshot_date > by_cycle[cycle]["snapshot_date"]:
            by_cycle[cycle] = {
                "cycle": cycle,
                "snapshot_date": snapshot_date,
                "ratings": composites,
            }

    return [by_cycle[key] for key in sorted(by_cycle)]


def two_cycle_ago_baseline(
    history_path, current_snapshot_date, season="2026", min_teams=130
):
    """Resolve the latest complete snapshot from two cycle buckets ago."""
    current_cycle = _cycle_key(current_snapshot_date)
    prior_cycles = [
        snapshot
        for snapshot in canonical_cycle_snapshots(
            history_path, season=season, min_teams=min_teams
        )
        if snapshot["cycle"] < current_cycle
    ]
    return prior_cycles[-2] if len(prior_cycles) >= 2 else None


def absolute_movement_ranks(changes):
    """Return unique ordinal ranks by absolute move, then team name.

    The alphabetical tie-break makes equal absolute moves deterministic while
    preserving a complete 1..N rank sequence for the compact site display.
    Missing movements are not ranked.
    """
    ranked_teams = sorted(
        (team for team, change in changes.items() if change is not None),
        key=lambda team: (-abs(changes[team]), team.casefold(), team),
    )
    return {team: rank for rank, team in enumerate(ranked_teams, start=1)}
