#!/usr/bin/env python3
"""Build rating-system comparisons, movement provenance, and market-derived context."""

import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ratings_latest_path = ROOT / "data/ratings/ratings_latest.csv"
ratings_history_path = ROOT / "data/ratings/ratings_history.csv"
market_latest_path = ROOT / "data/ratings/market_implied_ratings_latest.csv"
market_audit_path = ROOT / "data/research/market_implied_ratings/production_2026_audit.json"

rows = list(csv.DictReader(ratings_latest_path.open()))
dates = sorted({r["snapshot_date"] for r in rows if r.get("snapshot_date")})
if not dates:
    raise SystemExit("No rating snapshot dates found")

latest = dates[-1]

active = {
    "SP+": "spplus",
    "FPI": "fpi",
    "TeamRankings": "teamrankings",
    "Brad Powers": "bradpowers",
}

vectors = defaultdict(dict)

for r in rows:
    if r.get("source") in active and r.get("snapshot_date"):
        try:
            vectors[(r["snapshot_date"], r["source"])][r["team"]] = float(r["rating"])
        except (ValueError, TypeError):
            pass

source_meta = {}

for label, key in active.items():
    available = [d for d in dates if vectors.get((d, label))]
    last_change = None

    for previous, current in zip(available, available[1:]):
        if vectors[(previous, label)] != vectors[(current, label)]:
            last_change = current

    current_rows = [
        r for r in rows
        if r.get("snapshot_date") == latest and r.get("source") == label
    ]

    previous = available[-2] if len(available) > 1 else None
    changed = (
        sum(
            vectors[(previous, label)].get(team) != value
            for team, value in vectors[(latest, label)].items()
        )
        if previous else 0
    )

    pulls = sorted({
        r.get("pulled_at")
        for r in current_rows
        if r.get("pulled_at")
    })

    provider = sorted({
        r.get("source_updated_at")
        for r in current_rows
        if r.get("source_updated_at")
    })

    source_meta[key] = {
        "label": label,
        "latest_snapshot": latest,
        "latest_pull": pulls[-1] if pulls else None,
        "provider_updated_at": provider[-1] if provider else None,
        "last_observed_value_change": last_change,
        "changed_teams_from_prior": changed,
        "previous_snapshot": previous,
    }

# Build equal-weight historical composites for preseason and recent movement.
history = defaultdict(dict)

for r in csv.DictReader(ratings_history_path.open()):
    if (
        r.get("season") != "2026"
        or r.get("source") not in active
        or not r.get("snapshot_date")
    ):
        continue

    try:
        history[(r["team"], r["snapshot_date"])][active[r["source"]]] = float(r["rating"])
    except (ValueError, TypeError):
        pass

team_series = defaultdict(list)

for (team, snapshot_date), sources in history.items():
    if len(sources) >= 3:
        team_series[team].append((
            snapshot_date,
            sum(sources.values()) / len(sources),
        ))

for series in team_series.values():
    series.sort()


def at_or_before(series, target):
    eligible = [x for x in series if x[0] <= target]
    return eligible[-1][1] if eligible else None


# Load the current four-source ratings.
by_team = {}

for r in rows:
    if r.get("snapshot_date") != latest or r.get("source") not in active:
        continue

    try:
        rating = float(r["rating"])
        rank = int(float(r["rank"]))
    except (ValueError, TypeError):
        continue

    by_team.setdefault(r["team"], {})[active[r["source"]]] = {
        "rating": rating,
        "rank": rank,
        "pulled_at": r.get("pulled_at"),
    }


# Load the latest market-derived ratings.
market_by_team = {}
market_rows = []

if market_latest_path.exists():
    market_rows = list(csv.DictReader(market_latest_path.open()))

    for r in market_rows:
        try:
            market_by_team[r["team"]] = {
                "rating": float(r["market_implied_rating"]),
                "rank": int(float(r["market_implied_rank"])),
                "games_used": int(float(r.get("games_used") or 0)),
                "games_in_rating": int(float(r.get("games_in_rating") or 0)),
                "effective_games_weight": float(r.get("effective_games_weight") or 0),
                "weighted_games_in_rating": float(r.get("weighted_games_in_rating") or 0),
                "component_size": int(float(r.get("component_size") or 0)),
                "sample_status": r.get("sample_status") or None,
                "snapshot_date": r.get("snapshot_date") or None,
                "snapshot_timestamp": r.get("snapshot_timestamp") or None,
                "board_cutoff": r.get("board_cutoff") or None,
                "source_line_cutoff": r.get("source_line_cutoff") or None,
                "market_move_1w": (
                    float(r["market_move_1w"])
                    if r.get("market_move_1w") not in (None, "", "nan")
                    else None
                ),
                "market_move_4w": (
                    float(r["market_move_4w"])
                    if r.get("market_move_4w") not in (None, "", "nan")
                    else None
                ),
            }
        except (ValueError, TypeError, KeyError):
            continue


out = []

for team, sources in by_team.items():
    values = [x["rating"] for x in sources.values()]

    if len(values) < 3:
        continue

    current = sum(values) / len(values)

    item = {
        "team": team,
        "rating": current,
        "sources": sources,
        "variance": max(values) - min(values),
        "high_source": max(sources, key=lambda k: sources[k]["rating"]),
        "low_source": min(sources, key=lambda k: sources[k]["rating"]),
    }

    market = market_by_team.get(team)
    item["market"] = dict(market) if market else None
    item["market_delta"] = None

    out.append(item)


# Put raw market-implied ratings onto the same cross-sectional scale as the
# official four-source composite. This preserves ordering and relative market
# separation while making Market Delta interpretable in composite-rating points.
matched_for_scale = [x for x in out if x.get("market")]

if len(matched_for_scale) >= 2:
    import statistics

    composite_values = [x["rating"] for x in matched_for_scale]
    raw_market_values = [x["market"]["rating"] for x in matched_for_scale]

    composite_mean = statistics.mean(composite_values)
    composite_stdev = statistics.stdev(composite_values)
    raw_market_mean = statistics.mean(raw_market_values)
    raw_market_stdev = statistics.stdev(raw_market_values)

    if raw_market_stdev <= 0:
        raise SystemExit("Raw market rating standard deviation is zero")

    for item in matched_for_scale:
        raw_rating = item["market"]["rating"]
        z_score = (raw_rating - raw_market_mean) / raw_market_stdev
        scaled_rating = composite_mean + z_score * composite_stdev

        item["market"]["raw_rating"] = raw_rating
        item["market"]["scaled_rating"] = scaled_rating
        item["market"]["rating"] = scaled_rating
        item["market"]["scale_z_score"] = z_score
        item["market_delta"] = scaled_rating - item["rating"]
else:
    composite_mean = None
    composite_stdev = None
    raw_market_mean = None
    raw_market_stdev = None


# Rank the official four-source composite independently of matchup-page
# metadata. The Ratings page must display this rank and this rating together.
composite_ranked = sorted(out, key=lambda x: x["rating"], reverse=True)

for rank, item in enumerate(composite_ranked, 1):
    item["overall_rank"] = rank


# Maintain the official 2026 preseason composite until the first scheduled
# game date. Before kickoff, every ratings refresh updates this baseline so
# Current and Preseason remain identical. On and after 2026-08-29, the final
# saved baseline becomes immutable unless deliberately replaced by an operator.
baseline_path = ROOT / "data/ratings/ratings_preseason_2026.csv"
preseason_freeze_date = date(2026, 8, 29)
preseason_mode = date.today() < preseason_freeze_date

current_ranked = sorted(out, key=lambda x: x["rating"], reverse=True)
current_baseline = {
    item["team"]: {
        "rating": item["rating"],
        "rank": rank,
    }
    for rank, item in enumerate(current_ranked, 1)
}

if preseason_mode:
    baseline = current_baseline

    with baseline_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["team", "rating", "rank", "snapshot_date"],
        )
        writer.writeheader()

        for item in current_ranked:
            writer.writerow({
                "team": item["team"],
                "rating": item["rating"],
                "rank": baseline[item["team"]]["rank"],
                "snapshot_date": latest,
            })

    print(
        "preseason baseline refreshed:",
        baseline_path,
        "snapshot:",
        latest,
    )

elif baseline_path.exists():
    baseline = {
        row["team"]: {
            "rating": float(row["rating"]),
            "rank": int(row["rank"]),
        }
        for row in csv.DictReader(baseline_path.open())
    }

else:
    raise SystemExit(
        "Preseason freeze date reached but ratings_preseason_2026.csv is missing"
    )


for item in out:
    baseline_item = baseline.get(
        item["team"],
        {"rating": item["rating"], "rank": None},
    )

    item["preseason_rating"] = baseline_item["rating"]
    item["preseason_rank"] = baseline_item["rank"]
    item["preseason_delta"] = item["rating"] - baseline_item["rating"]

    series = team_series.get(item["team"], [])
    current_date = date.fromisoformat(latest)

    l2 = at_or_before(
        series,
        (current_date - timedelta(days=14)).isoformat(),
    )

    item["l2_change"] = (
        0.0
        if preseason_mode
        else item["rating"] - l2
        if l2 is not None
        else None
    )


# Build market summary metadata.
audit = {}

if market_audit_path.exists():
    try:
        audit = json.loads(market_audit_path.read_text())
    except json.JSONDecodeError:
        audit = {}

readiness = audit.get("readiness_distribution") or {}

ratings_page_matched = sum(1 for x in out if x.get("market"))
ratings_page_missing = sum(1 for x in out if not x.get("market"))

market_meta = {
    "label": "Market-Derived",
    "snapshot_date": market_rows[0].get("snapshot_date") if market_rows else None,
    "snapshot_timestamp": market_rows[0].get("snapshot_timestamp") if market_rows else None,
    "board_cutoff": market_rows[0].get("board_cutoff") if market_rows else None,
    "board_games": audit.get("board_games"),
    "board_teams_rated": len(market_by_team),
    "ratings_page_matched": ratings_page_matched,
    "ratings_page_missing": ratings_page_missing,
    "independent_ready": readiness.get("independent_market_ready", 0),
    "context_only": readiness.get("market_context_only", 0),
    "model_version": market_rows[0].get("model_version") if market_rows else None,
    "lookback_weeks": (
        int(float(market_rows[0]["lookback_weeks"]))
        if market_rows and market_rows[0].get("lookback_weeks")
        else None
    ),
    "half_life_weeks": (
        float(market_rows[0]["half_life_weeks"])
        if market_rows and market_rows[0].get("half_life_weeks")
        else None
    ),
    "hfa": (
        float(market_rows[0]["hfa"])
        if market_rows and market_rows[0].get("hfa")
        else None
    ),
    "display_scale": "z_score_to_composite_distribution",
    "composite_mean_matched": composite_mean,
    "composite_stdev_matched": composite_stdev,
    "raw_market_mean_matched": raw_market_mean,
    "raw_market_stdev_matched": raw_market_stdev,
}


payload = {
    "snapshot_date": latest,
    "weights": {key: 0.25 for key in active.values()},
    "source_meta": source_meta,
    "market_meta": market_meta,
    "teams": out,
}

target = ROOT / "data/site/ratings_view.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload, separators=(",", ":")) + "\n")

print(target, len(out))
print("market ratings matched:", sum(1 for x in out if x["market"]))
print("market ratings missing:", sum(1 for x in out if not x["market"]))

if len(out) < 130:
    raise SystemExit("ratings view coverage below 130")

# Basic invariants.
for item in out:
    expected = sum(
        item["sources"][key]["rating"]
        for key in active.values()
        if key in item["sources"]
    ) / len(item["sources"])

    if abs(item["rating"] - expected) > 1e-9:
        raise SystemExit(f"Composite changed unexpectedly for {item['team']}")

    if item["market"]:
        expected_delta = item["market"]["scaled_rating"] - item["rating"]

        if abs(item["market_delta"] - expected_delta) > 1e-9:
            raise SystemExit(f"Market delta mismatch for {item['team']}")

        if item["market"]["rating"] != item["market"]["scaled_rating"]:
            raise SystemExit(f"Displayed market rating mismatch for {item['team']}")

# Scaling must preserve the exact raw-market rank ordering.
raw_ranked = sorted(
    [x for x in out if x.get("market")],
    key=lambda x: x["market"]["raw_rating"],
    reverse=True,
)

scaled_ranked = sorted(
    [x for x in out if x.get("market")],
    key=lambda x: x["market"]["scaled_rating"],
    reverse=True,
)

if [x["team"] for x in raw_ranked] != [x["team"] for x in scaled_ranked]:
    raise SystemExit("Market scaling changed team ordering")
