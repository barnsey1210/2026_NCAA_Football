#!/usr/bin/env python3
"""Audit season-by-season RP signal stability and find matching 2026 games.

Historical validation:
- 2021-2025
- Weeks 1-4
- One row per game
- Uses expanded_rp_game_level_2021_2025.csv

2026 matching:
- Reads the embedded DB and RETURNING_PRODUCTION_2026 from index.html
- Uses the same Power/Group conference classification as the historical RP work
- Identifies exact matches for the production candidate rules
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import re
import sys
from typing import Any

import numpy as np
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

HISTORICAL = BASE / "data/research/expanded_rp_game_level_2021_2025.csv"
INDEX = BASE / "index.html"

OUT_STABILITY = BASE / "data/research/expanded_rp_rule_stability_by_season_2021_2025.csv"
OUT_LOSO = BASE / "data/research/expanded_rp_rule_leave_one_season_out_2021_2025.csv"
OUT_RULE_SUMMARY = BASE / "data/research/expanded_rp_rule_summary_2021_2025.csv"
OUT_2026 = BASE / "data/signals/returning_production_validated_matches_2026.csv"
OUT_AUDIT = BASE / "data/audits/returning_production_validated_matches_2026_audit.csv"


POWER_CONFERENCES = {
    "ACC",
    "Big Ten",
    "Big 12",
    "SEC",
    "Pac-12",
}

GROUP_CONFERENCES = {
    "American Athletic",
    "American",
    "AAC",
    "Conference USA",
    "CUSA",
    "Mid-American",
    "MAC",
    "Mountain West",
    "MWC",
    "Sun Belt",
}

INDEPENDENT_FBS = {
    "Notre Dame",
    "Connecticut",
    "UConn",
    "UMass",
    "Massachusetts",
}


TEAM_ALIASES = {
    "app st": "appalachian state",
    "app state": "appalachian state",
    "appalachian st": "appalachian state",
    "arizona st": "arizona state",
    "arkansas st": "arkansas state",
    "ball st": "ball state",
    "boise st": "boise state",
    "boston college": "boston college",
    "boston coll": "boston college",
    "central florida": "ucf",
    "central michigan": "central michigan",
    "cmu": "central michigan",
    "colorado st": "colorado state",
    "east carolina": "east carolina",
    "ecu": "east carolina",
    "e michigan": "eastern michigan",
    "emu": "eastern michigan",
    "fau": "florida atlantic",
    "fiu": "florida international",
    "florida int l": "florida international",
    "florida st": "florida state",
    "fresno st": "fresno state",
    "ga southern": "georgia southern",
    "ga tech": "georgia tech",
    "georgia st": "georgia state",
    "hawai i": "hawaii",
    "iowa st": "iowa state",
    "kansas st": "kansas state",
    "kent st": "kent state",
    "la tech": "louisiana tech",
    "massachusetts": "umass",
    "miami oh": "miami ohio",
    "miami ohio": "miami ohio",
    "michigan st": "michigan state",
    "mississippi st": "mississippi state",
    "miss st": "mississippi state",
    "mtsu": "middle tennessee",
    "n carolina": "north carolina",
    "nc st": "nc state",
    "new mexico st": "new mexico state",
    "north texas": "north texas",
    "n texas": "north texas",
    "northern illinois": "northern illinois",
    "niu": "northern illinois",
    "ohio st": "ohio state",
    "oklahoma st": "oklahoma state",
    "oregon st": "oregon state",
    "penn st": "penn state",
    "san diego st": "san diego state",
    "san jose st": "san jose state",
    "san josé state": "san jose state",
    "south carolina": "south carolina",
    "s carolina": "south carolina",
    "south florida": "south florida",
    "usf": "south florida",
    "southern miss": "southern miss",
    "so miss": "southern miss",
    "texas a m": "texas a&m",
    "texas st": "texas state",
    "utah st": "utah state",
    "va tech": "virginia tech",
    "wash st": "washington state",
    "washington st": "washington state",
    "w kentucky": "western kentucky",
    "wku": "western kentucky",
    "w michigan": "western michigan",
    "w virginia": "west virginia",
}


@dataclass(frozen=True)
class Rule:
    key: str
    label: str
    historical_record: str
    historical_games: int
    historical_ats_pct: float
    priority: int


RULES = {
    "P4_G6_EITHER_COMPONENT_25_PLUS": Rule(
        key="P4_G6_EITHER_COMPONENT_25_PLUS",
        label="P4 vs G6: either RP component edge 25+",
        historical_record="50-31",
        historical_games=81,
        historical_ats_pct=61.7284,
        priority=1,
    ),
    "P4_G6_DEFENSE_15_PLUS": Rule(
        key="P4_G6_DEFENSE_15_PLUS",
        label="P4 vs G6: defensive RP edge 15+",
        historical_record="46-32",
        historical_games=78,
        historical_ats_pct=58.9744,
        priority=2,
    ),
    "P4_P4_OVERALL_15_TO_24_9": Rule(
        key="P4_P4_OVERALL_15_TO_24_9",
        label="P4 vs P4: overall RP edge 15-24.9",
        historical_record="29-22-1",
        historical_games=52,
        historical_ats_pct=56.8627,
        priority=3,
    ),
}


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def number(value: Any) -> float:
    try:
        if value is None or clean(value) == "":
            return np.nan
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def norm_team(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9&]+", " ", clean(value).lower()).strip()
    return TEAM_ALIASES.get(normalized, normalized)


def norm_conference(value: Any) -> str:
    value = re.sub(r"\s+", " ", clean(value)).strip()

    mapping = {
        "American Athletic Conference": "American",
        "AAC": "American",
        "Big 10": "Big Ten",
        "Big Ten Conference": "Big Ten",
        "Big 12 Conference": "Big 12",
        "Atlantic Coast Conference": "ACC",
        "Southeastern Conference": "SEC",
        "Conference USA": "CUSA",
        "Mid-American Conference": "MAC",
        "Mountain West Conference": "MWC",
        "Sun Belt Conference": "Sun Belt",
        "Pac 12": "Pac-12",
    }

    return mapping.get(value, value)


def conference_tier(team: str, conference: str) -> str:
    conference = norm_conference(conference)

    if conference in POWER_CONFERENCES:
        return "P4"

    if conference in GROUP_CONFERENCES:
        return "G6"

    if team in INDEPENDENT_FBS:
        return "Independent"

    return "Other"


def extract_index_objects() -> tuple[dict[str, Any], dict[str, Any]]:
    if not INDEX.exists():
        raise FileNotFoundError(f"Missing index.html: {INDEX}")

    html = INDEX.read_text(encoding="utf-8", errors="ignore")

    db_match = re.search(
        r'<script id="db" type="application/json">(.*?)</script>',
        html,
        flags=re.S,
    )

    if not db_match:
        raise RuntimeError("Could not locate embedded DB in index.html")

    db = json.loads(db_match.group(1))

    rp_patterns = [
        r"const\s+RETURNING_PRODUCTION_2026\s*=\s*(\{.*?\});",
        r"let\s+RETURNING_PRODUCTION_2026\s*=\s*(\{.*?\});",
        r"var\s+RETURNING_PRODUCTION_2026\s*=\s*(\{.*?\});",
    ]

    rp = {}

    for pattern in rp_patterns:
        match = re.search(pattern, html, flags=re.S)
        if match:
            rp = json.loads(match.group(1))
            break

    if not rp:
        raise RuntimeError(
            "Could not locate RETURNING_PRODUCTION_2026 in index.html"
        )

    return db, rp


def get_rp_value(record: dict[str, Any], kind: str) -> float:
    candidates = {
        "overall": [
            "overall",
            "overall_pct",
            "returning_production",
            "returning_production_overall",
            "rp_overall",
        ],
        "offense": [
            "offense",
            "offense_pct",
            "off",
            "off_rp",
            "returning_production_offense",
            "rp_offense",
        ],
        "defense": [
            "defense",
            "defense_pct",
            "def",
            "def_rp",
            "returning_production_defense",
            "rp_defense",
        ],
    }

    for key in candidates[kind]:
        if key in record:
            value = number(record.get(key))
            if np.isfinite(value):
                return value

    return np.nan


def historical_rule_mask(df: pd.DataFrame, rule_key: str) -> pd.Series:
    if rule_key == "P4_G6_EITHER_COMPONENT_25_PLUS":
        return (
            df["conference_matchup_type"].eq("P4_vs_G6")
            &
            (
                (df["offense_vs_defense_edge"] >= 25)
                |
                (df["defense_vs_offense_edge"] >= 25)
            )
        )

    if rule_key == "P4_G6_DEFENSE_15_PLUS":
        return (
            df["conference_matchup_type"].eq("P4_vs_G6")
            &
            (df["defense_vs_offense_edge"] >= 15)
        )

    if rule_key == "P4_P4_OVERALL_15_TO_24_9":
        return (
            df["conference_matchup_type"].eq("P4_vs_P4")
            &
            (df["overall_rp_edge"] >= 15)
            &
            (df["overall_rp_edge"] < 25)
        )

    raise KeyError(f"Unknown rule: {rule_key}")


def summarize_results(
    df: pd.DataFrame,
    rule: Rule,
    season_label: Any,
) -> dict[str, Any]:
    result = df["rp_team_ats_result"].astype(str)

    wins = int((result == "W").sum())
    losses = int((result == "L").sum())
    pushes = int((result == "P").sum())
    decisions = wins + losses
    games = len(df)

    return {
        "rule_key": rule.key,
        "rule_label": rule.label,
        "season": season_label,
        "games": games,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "ats_record": f"{wins}-{losses}" + (f"-{pushes}" if pushes else ""),
        "ats_win_pct": wins / decisions if decisions else np.nan,
        "avg_ats_margin": pd.to_numeric(
            df["rp_team_ats_margin"],
            errors="coerce",
        ).mean(),
        "median_ats_margin": pd.to_numeric(
            df["rp_team_ats_margin"],
            errors="coerce",
        ).median(),
        "positive_season": bool(decisions and wins / decisions > 0.5),
        "profitable_55_pct": bool(decisions and wins / decisions >= 0.55),
    }


def build_stability() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not HISTORICAL.exists():
        raise FileNotFoundError(
            f"Missing historical game-level file: {HISTORICAL}"
        )

    historical = pd.read_csv(HISTORICAL)

    required = {
        "season",
        "game_id",
        "conference_matchup_type",
        "overall_rp_edge",
        "offense_vs_defense_edge",
        "defense_vs_offense_edge",
        "rp_team_ats_result",
        "rp_team_ats_margin",
    }

    missing = sorted(required - set(historical.columns))
    if missing:
        raise KeyError(f"Historical file missing columns: {missing}")

    stability_rows = []
    loso_rows = []
    summary_rows = []

    seasons = sorted(
        pd.to_numeric(historical["season"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
    )

    for rule in RULES.values():
        selected = historical[historical_rule_mask(historical, rule.key)].copy()

        for season in seasons:
            season_df = selected[
                pd.to_numeric(selected["season"], errors="coerce").eq(season)
            ]
            stability_rows.append(
                summarize_results(season_df, rule, season)
            )

            excluding = selected[
                ~pd.to_numeric(selected["season"], errors="coerce").eq(season)
            ]
            row = summarize_results(
                excluding,
                rule,
                f"All except {season}",
            )
            row["excluded_season"] = season
            loso_rows.append(row)

        overall = summarize_results(selected, rule, "2021-2025")
        positive_seasons = 0
        profitable_seasons = 0
        evaluated_seasons = 0

        for season in seasons:
            season_df = selected[
                pd.to_numeric(selected["season"], errors="coerce").eq(season)
            ]

            if len(season_df) == 0:
                continue

            evaluated_seasons += 1
            record = summarize_results(season_df, rule, season)

            if record["positive_season"]:
                positive_seasons += 1

            if record["profitable_55_pct"]:
                profitable_seasons += 1

        overall["positive_seasons"] = positive_seasons
        overall["profitable_55_pct_seasons"] = profitable_seasons
        overall["evaluated_seasons"] = evaluated_seasons
        overall["positive_season_rate"] = (
            positive_seasons / evaluated_seasons
            if evaluated_seasons
            else np.nan
        )
        summary_rows.append(overall)

    stability = pd.DataFrame(stability_rows)
    loso = pd.DataFrame(loso_rows)
    summary = pd.DataFrame(summary_rows)

    return stability, loso, summary


def build_2026_matches() -> tuple[pd.DataFrame, pd.DataFrame]:
    db, rp_raw = extract_index_objects()

    games = pd.DataFrame(db.get("games", []))
    teams = pd.DataFrame(db.get("teams", []))

    if games.empty:
        raise RuntimeError("Embedded DB has no games")

    if teams.empty:
        raise RuntimeError("Embedded DB has no teams")

    team_meta = {}

    for _, row in teams.iterrows():
        name = clean(row.get("team"))
        if not name:
            continue

        team_meta[norm_team(name)] = {
            "team": name,
            "conference": norm_conference(row.get("conference")),
        }

    rp_lookup = {}

    for raw_name, raw_record in rp_raw.items():
        if not isinstance(raw_record, dict):
            continue

        rp_lookup[norm_team(raw_name)] = {
            "raw_team": raw_name,
            "overall": get_rp_value(raw_record, "overall"),
            "offense": get_rp_value(raw_record, "offense"),
            "defense": get_rp_value(raw_record, "defense"),
        }

    candidate_rows = []
    unmatched_teams = set()

    games = games.copy()
    games["week_num"] = pd.to_numeric(games.get("week"), errors="coerce")
    games = games[
        games["week_num"].between(1, 4, inclusive="both")
    ].copy()

    for _, game in games.iterrows():
        away = clean(game.get("away_team"))
        home = clean(game.get("home_team"))

        away_key = norm_team(away)
        home_key = norm_team(home)

        away_meta = team_meta.get(
            away_key,
            {"team": away, "conference": clean(game.get("away_conference"))},
        )
        home_meta = team_meta.get(
            home_key,
            {"team": home, "conference": clean(game.get("home_conference"))},
        )

        away_rp = rp_lookup.get(away_key)
        home_rp = rp_lookup.get(home_key)

        if away_rp is None:
            unmatched_teams.add(away)
        if home_rp is None:
            unmatched_teams.add(home)

        if away_rp is None or home_rp is None:
            continue

        if not all(
            np.isfinite(value)
            for value in [
                away_rp["overall"],
                away_rp["offense"],
                away_rp["defense"],
                home_rp["overall"],
                home_rp["offense"],
                home_rp["defense"],
            ]
        ):
            continue

        away_tier = conference_tier(
            away_meta["team"],
            away_meta["conference"],
        )
        home_tier = conference_tier(
            home_meta["team"],
            home_meta["conference"],
        )

        side_specs = [
            {
                "team": away,
                "opponent": home,
                "team_conference": away_meta["conference"],
                "opponent_conference": home_meta["conference"],
                "team_tier": away_tier,
                "opponent_tier": home_tier,
                "team_rp": away_rp,
                "opp_rp": home_rp,
            },
            {
                "team": home,
                "opponent": away,
                "team_conference": home_meta["conference"],
                "opponent_conference": away_meta["conference"],
                "team_tier": home_tier,
                "opponent_tier": away_tier,
                "team_rp": home_rp,
                "opp_rp": away_rp,
            },
        ]

        game_matches = []

        for side in side_specs:
            overall_edge = (
                side["team_rp"]["overall"]
                -
                side["opp_rp"]["overall"]
            )
            offense_edge = (
                side["team_rp"]["offense"]
                -
                side["opp_rp"]["defense"]
            )
            defense_edge = (
                side["team_rp"]["defense"]
                -
                side["opp_rp"]["offense"]
            )

            matched_rules = []

            if (
                side["team_tier"] == "P4"
                and side["opponent_tier"] == "G6"
            ):
                if offense_edge >= 25 or defense_edge >= 25:
                    matched_rules.append(
                        RULES["P4_G6_EITHER_COMPONENT_25_PLUS"]
                    )

                if defense_edge >= 15:
                    matched_rules.append(
                        RULES["P4_G6_DEFENSE_15_PLUS"]
                    )

            if (
                side["team_tier"] == "P4"
                and side["opponent_tier"] == "P4"
                and 15 <= overall_edge < 25
            ):
                matched_rules.append(
                    RULES["P4_P4_OVERALL_15_TO_24_9"]
                )

            for rule in matched_rules:
                game_matches.append(
                    {
                        "game_id": clean(game.get("game_id")),
                        "week": int(game["week_num"]),
                        "date": clean(game.get("date")),
                        "away_team": away,
                        "home_team": home,
                        "signal_team": side["team"],
                        "signal_opponent": side["opponent"],
                        "signal_team_conference": side["team_conference"],
                        "signal_opponent_conference": side["opponent_conference"],
                        "signal_team_tier": side["team_tier"],
                        "signal_opponent_tier": side["opponent_tier"],
                        "rule_key": rule.key,
                        "rule_label": rule.label,
                        "rule_priority": rule.priority,
                        "historical_record": rule.historical_record,
                        "historical_games": rule.historical_games,
                        "historical_ats_pct": rule.historical_ats_pct / 100,
                        "team_overall_rp": side["team_rp"]["overall"],
                        "opponent_overall_rp": side["opp_rp"]["overall"],
                        "overall_rp_edge": overall_edge,
                        "team_offense_rp": side["team_rp"]["offense"],
                        "opponent_defense_rp": side["opp_rp"]["defense"],
                        "offense_vs_defense_edge": offense_edge,
                        "team_defense_rp": side["team_rp"]["defense"],
                        "opponent_offense_rp": side["opp_rp"]["offense"],
                        "defense_vs_offense_edge": defense_edge,
                        "market_spread_home": first_numeric(
                            game,
                            [
                                "market_spread_home",
                                "consensus_spread_home",
                                "sgo_spread_home",
                                "spread_home",
                            ],
                        ),
                        "projected_margin_home": first_numeric(
                            game,
                            [
                                "projected_margin_home",
                                "model_margin_home",
                                "projected_spread_home",
                            ],
                        ),
                    }
                )

        candidate_rows.extend(game_matches)

    candidates = pd.DataFrame(candidate_rows)

    if not candidates.empty:
        overlap_counts = (
            candidates.groupby(["game_id", "signal_team"])
            .size()
            .rename("matched_rule_count")
            .reset_index()
        )

        candidates = candidates.merge(
            overlap_counts,
            on=["game_id", "signal_team"],
            how="left",
        )

        candidates["primary_signal"] = (
            candidates["rule_priority"]
            ==
            candidates.groupby(["game_id", "signal_team"])[
                "rule_priority"
            ].transform("min")
        )

        candidates.sort_values(
            [
                "week",
                "date",
                "rule_priority",
                "historical_ats_pct",
                "signal_team",
            ],
            ascending=[True, True, True, False, True],
            inplace=True,
        )

    audit_rows = [
        {
            "metric": "games_in_index",
            "value": len(db.get("games", [])),
        },
        {
            "metric": "weeks_1_4_games",
            "value": len(games),
        },
        {
            "metric": "rp_teams_in_index",
            "value": len(rp_lookup),
        },
        {
            "metric": "candidate_signal_rows",
            "value": len(candidates),
        },
        {
            "metric": "unique_candidate_games",
            "value": (
                candidates["game_id"].nunique()
                if not candidates.empty
                else 0
            ),
        },
        {
            "metric": "unique_candidate_teams",
            "value": (
                candidates["signal_team"].nunique()
                if not candidates.empty
                else 0
            ),
        },
        {
            "metric": "unmatched_schedule_teams",
            "value": len(unmatched_teams),
        },
        {
            "metric": "unmatched_schedule_team_names",
            "value": " | ".join(sorted(unmatched_teams)),
        },
        {
            "metric": "conference_classification_note",
            "value": (
                "Pac-12 classified as P4 to match historical analysis; "
                "Notre Dame/UConn/UMass excluded from P4-G6 rules."
            ),
        },
    ]

    return candidates, pd.DataFrame(audit_rows)


def first_numeric(row: pd.Series, columns: list[str]) -> float:
    for column in columns:
        if column in row.index:
            value = number(row.get(column))
            if np.isfinite(value):
                return value

    return np.nan


def print_stability(summary: pd.DataFrame, stability: pd.DataFrame) -> None:
    print()
    print("RULE STABILITY SUMMARY")
    print("=" * 100)

    for rule in RULES.values():
        overall = summary[summary["rule_key"] == rule.key].iloc[0]

        print()
        print(rule.label)
        print(
            f"Overall: {overall['ats_record']} ATS, "
            f"{overall['ats_win_pct']:.1%}, "
            f"avg ATS margin {overall['avg_ats_margin']:+.2f}"
        )
        print(
            f"Positive seasons: "
            f"{int(overall['positive_seasons'])}/"
            f"{int(overall['evaluated_seasons'])}; "
            f"55%+ seasons: "
            f"{int(overall['profitable_55_pct_seasons'])}/"
            f"{int(overall['evaluated_seasons'])}"
        )

        rows = stability[stability["rule_key"] == rule.key]

        for _, row in rows.iterrows():
            pct = (
                f"{row['ats_win_pct']:.1%}"
                if pd.notna(row["ats_win_pct"])
                else "N/A"
            )
            margin = (
                f"{row['avg_ats_margin']:+.2f}"
                if pd.notna(row["avg_ats_margin"])
                else "N/A"
            )
            print(
                f"  {int(row['season'])}: "
                f"{row['ats_record']} ATS, {pct}, "
                f"avg margin {margin}, n={int(row['games'])}"
            )


def print_candidates(candidates: pd.DataFrame) -> None:
    print()
    print("2026 MATCHING GAMES")
    print("=" * 100)

    if candidates.empty:
        print("No Weeks 1-4 games matched the validated RP rules.")
        return

    display_cols = [
        "week",
        "date",
        "away_team",
        "home_team",
        "signal_team",
        "rule_label",
        "historical_record",
        "historical_ats_pct",
        "overall_rp_edge",
        "offense_vs_defense_edge",
        "defense_vs_offense_edge",
        "matched_rule_count",
        "primary_signal",
    ]

    printable = candidates[display_cols].copy()
    printable["historical_ats_pct"] = (
        printable["historical_ats_pct"] * 100
    ).round(1)

    for column in [
        "overall_rp_edge",
        "offense_vs_defense_edge",
        "defense_vs_offense_edge",
    ]:
        printable[column] = printable[column].round(1)

    print(printable.to_string(index=False))


def main() -> None:
    print("Building RP season stability and 2026 candidate matches")

    stability, loso, summary = build_stability()
    candidates, audit = build_2026_matches()

    for path in [
        OUT_STABILITY,
        OUT_LOSO,
        OUT_RULE_SUMMARY,
        OUT_2026,
        OUT_AUDIT,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    stability.to_csv(OUT_STABILITY, index=False)
    loso.to_csv(OUT_LOSO, index=False)
    summary.to_csv(OUT_RULE_SUMMARY, index=False)
    candidates.to_csv(OUT_2026, index=False)
    audit.to_csv(OUT_AUDIT, index=False)

    print_stability(summary, stability)
    print_candidates(candidates)

    print()
    print("Created:")
    print(OUT_STABILITY)
    print(OUT_LOSO)
    print(OUT_RULE_SUMMARY)
    print(OUT_2026)
    print(OUT_AUDIT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
