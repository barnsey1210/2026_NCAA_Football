#!/usr/bin/env python3
"""Audit normalized matchup-card data for missing, inconsistent, or suspicious values.

Hard failures are fields expected for every 2026 FBS team:
- identity/logo/conference
- overall/offense/defense ratings and ranks
- returning production overall/offense/defense percentages and ranks

Conditional gaps (coach history, injuries, market prices, QB depth, weather, etc.)
are reported as warnings rather than failures.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import csv
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
VIEW = ROOT / "data/site/matchups_view.json"
OUT_DIR = ROOT / "data/audits"
CSV_OUT = OUT_DIR / "matchup_card_data_gaps.csv"
JSON_OUT = OUT_DIR / "matchup_card_data_audit.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.ncaaf_config import canonical_team


def blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def nested(obj, path):
    cur = obj
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


HARD_FIELDS = {
    "team": "team",
    "logo_slug": "logo_slug",
    "conference": "conference",
    "overall_rank": "overall_rank",
    "rating": "rating",
    "offense_rank": "offense_rank",
    "defense_rank": "defense_rank",
    "rp_overall_pct": "returning_production.overall_pct",
    "rp_overall_rank": "returning_production.overall_rank",
    "rp_offense_pct": "returning_production.offense_pct",
    "rp_offense_rank": "returning_production.offense_rank",
    "rp_defense_pct": "returning_production.defense_pct",
    "rp_defense_rank": "returning_production.defense_rank",
}

WARN_FIELDS = {
    "style_profile": "style_profile",
    "quarterbacks": "quarterbacks",
    "rating_trend": "rating_trend",
}

TEAM_SNAPSHOT_FIELDS = [
    "logo_slug", "conference", "overall_rank", "rating", "offense_rank",
    "defense_rank", "returning_production",
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not VIEW.exists():
        raise SystemExit(f"Missing matchup view: {VIEW}")

    payload = json.loads(VIEW.read_text())
    games = payload.get("games", [])
    if not games:
        raise SystemExit("matchups_view.json contains no games")

    # Canonical source returning-production map embedded in the retained V1
    # data artifact; the production index is the V2 dashboard shell.
    # Parse this directly instead of depending on extract_index_data(), whose
    # return signature may change as the site builder evolves.
    index_path = ROOT / "v1.html"
    if not index_path.exists():
        raise SystemExit(f"Missing canonical v1.html: {index_path}")
    index_html = index_path.read_text(errors="ignore")
    match = re.search(
        r"const\s+RETURNING_PRODUCTION_2026\s*=\s*(\{.*?\});",
        index_html,
        re.S,
    )
    if not match:
        raise SystemExit("RETURNING_PRODUCTION_2026 not found in v1.html")
    source_rp_raw = json.loads(match.group(1))

    def norm_name(value):
        text = canonical_team(value) or str(value or "")
        text = text.lower().replace("&", "and")
        return "".join(ch for ch in text if ch.isalnum())

    rp_aliases = {
        "floridainternational": ["fiu"],
        "fresnostate": ["fresnost"],
        "louisiana": ["ullafayette", "louisianalafayette", "ull", "ul"],
        "samhouston": ["samhoustonstate", "shsu"],
        "sandiegostate": ["sdsu", "sandiegost"],
        "southflorida": ["usf"],
    }

    source_rp_by_norm = {}
    source_rp_key_by_norm = {}
    for raw_name, value in source_rp_raw.items():
        key = norm_name(raw_name)
        source_rp_by_norm[key] = value
        source_rp_key_by_norm[key] = raw_name

    def source_rp_for(team_name):
        keys = [norm_name(team_name), *rp_aliases.get(norm_name(team_name), [])]
        for key in keys:
            if key in source_rp_by_norm:
                return source_rp_by_norm[key], source_rp_key_by_norm[key]
        return None, None

    source_rp = {
        canonical_team(raw_name): value
        for raw_name, value in source_rp_raw.items()
    }

    snapshots = defaultdict(list)
    coaches = {}
    for game in games:
        for side in ("away", "home"):
            team = game.get("teams", {}).get(side, {})
            name = canonical_team(team.get("team"))
            if name:
                snapshots[name].append((game.get("game", {}).get("game_id"), team))
        for coach in game.get("matchup", {}).get("coaches", []):
            name = canonical_team(coach.get("team"))
            if name and name not in coaches:
                coaches[name] = coach

    rows = []
    hard_teams = set()
    warning_teams = set()
    inconsistent = []

    # The view also includes FCS opponents and conference placeholders.
    # Restrict universal-card requirements to the 138 FBS teams, identified by
    # the presence of a site rating/rank or a returning-production source row.
    fbs_teams = set()
    for team_name, samples in snapshots.items():
        first = samples[0][1]
        source_value, _ = source_rp_for(team_name)
        if (
            not blank(first.get("rating"))
            or not blank(first.get("overall_rank"))
            or source_value is not None
        ):
            if " No. " not in team_name and team_name not in {"Sun Belt East", "Sun Belt West"}:
                fbs_teams.add(team_name)

    for team_name in sorted(fbs_teams):
        samples = snapshots[team_name]
        first = samples[0][1]

        # Universal matchup-card fields.
        for field_name, path in HARD_FIELDS.items():
            value = nested(first, path)
            if blank(value):
                hard_teams.add(team_name)
                rows.append({
                    "severity": "ERROR",
                    "team": team_name,
                    "field": field_name,
                    "path": path,
                    "value": "",
                    "reason": "Required matchup-card field is blank",
                    "source_status": "",
                })

        # Compare view RP to canonical source RP to distinguish source vs join failures.
        rp = first.get("returning_production")
        src, src_key = source_rp_for(team_name)
        if not rp:
            source_status = "source_missing" if src is None else "source_present_view_missing"
            rows.append({
                "severity": "ERROR",
                "team": team_name,
                "field": "returning_production_object",
                "path": "returning_production",
                "value": "",
                "reason": "Returning-production object missing",
                "source_status": source_status if not src_key else f"{source_status}:{src_key}",
            })
            hard_teams.add(team_name)
        elif src is None:
            rows.append({
                "severity": "ERROR",
                "team": team_name,
                "field": "returning_production_source",
                "path": "v1.html returning production",
                "value": json.dumps(rp, sort_keys=True),
                "reason": "View has RP but canonical embedded source lookup is missing",
                "source_status": "source_missing",
            })
            hard_teams.add(team_name)

        # Fields with legitimate coverage gaps.
        for field_name, path in WARN_FIELDS.items():
            value = nested(first, path)
            if blank(value) or value == []:
                warning_teams.add(team_name)
                rows.append({
                    "severity": "WARN",
                    "team": team_name,
                    "field": field_name,
                    "path": path,
                    "value": "",
                    "reason": "Conditional matchup-card field is blank",
                    "source_status": "allowed_gap",
                })

        coach = coaches.get(team_name, {})
        if not coach.get("coach"):
            warning_teams.add(team_name)
            rows.append({
                "severity": "WARN",
                "team": team_name,
                "field": "current_coach",
                "path": "matchup.coaches.coach",
                "value": "",
                "reason": "Current coach name missing",
                "source_status": "review",
            })
        periods = coach.get("periods") or []
        labels = ("full_game", "first_half", "second_half")
        for idx, label in enumerate(labels):
            period = periods[idx] if idx < len(periods) else None
            if not period:
                warning_teams.add(team_name)
                rows.append({
                    "severity": "WARN",
                    "team": team_name,
                    "field": f"coach_{label}",
                    "path": f"matchup.coaches.periods[{idx}]",
                    "value": "",
                    "reason": "Coach historical period missing; may be legitimate for a new coach",
                    "source_status": "allowed_if_no_history",
                })

        # The same team appears in many games. Core card values must remain identical.
        for field in TEAM_SNAPSHOT_FIELDS:
            values = {}
            for game_id, sample in samples:
                encoded = json.dumps(sample.get(field), sort_keys=True, default=str)
                values.setdefault(encoded, []).append(game_id)
            if len(values) > 1:
                inconsistent.append((team_name, field, values))
                rows.append({
                    "severity": "ERROR",
                    "team": team_name,
                    "field": field,
                    "path": field,
                    "value": " | ".join(values.keys()),
                    "reason": "Team card value is inconsistent across matchup records",
                    "source_status": "inconsistent_snapshots",
                })
                hard_teams.add(team_name)

    # Canonical RP source should cover every team appearing in the matchup view.
    view_teams = set(fbs_teams)
    source_missing_teams = sorted(
        team for team in view_teams if source_rp_for(team)[0] is None
    )
    matched_source_keys = {
        source_rp_for(team)[1] for team in view_teams if source_rp_for(team)[1]
    }
    source_extra_teams = sorted(
        raw_name for raw_name in source_rp_raw if raw_name not in matched_source_keys
    )

    # Coverage summaries for game-level/conditional fields.
    coverage = {
        "teams_in_view": len(view_teams),
        "games": len(games),
        "teams_with_complete_required_fields": len(view_teams - hard_teams),
        "teams_with_required_errors": len(hard_teams),
        "teams_with_warnings": len(warning_teams),
        "source_rp_teams": len(source_rp),
        "source_rp_missing_from_view_team_set": len(source_missing_teams),
        "inconsistent_team_snapshots": len(inconsistent),
        "games_with_market_spread": sum(
            nested(g, "market.spread.home_line") is not None for g in games
        ),
        "games_with_market_total": sum(
            nested(g, "market.total.line") is not None for g in games
        ),
        "games_with_injuries": sum(
            bool(nested(g, "teams.away.injuries") or nested(g, "teams.home.injuries"))
            for g in games
        ),
        "games_with_weather": sum(g.get("weather") is not None for g in games),
    }

    severity_counts = Counter(row["severity"] for row in rows)
    result = {
        "status": "fail" if hard_teams else "pass",
        "coverage": coverage,
        "severity_counts": dict(severity_counts),
        "required_error_teams": sorted(hard_teams),
        "warning_teams": sorted(warning_teams),
        "source_rp_missing_teams": source_missing_teams,
        "source_rp_extra_teams": source_extra_teams,
        "sam_houston": {
            "source": source_rp_for("Sam Houston")[0],
            "source_key": source_rp_for("Sam Houston")[1],
            "view": snapshots.get("Sam Houston", [(None, None)])[0][1].get("returning_production")
                if snapshots.get("Sam Houston") else None,
        },
    }

    with CSV_OUT.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "severity", "team", "field", "path", "value", "reason",
                "source_status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True))

    print("MATCHUP CARD DATA AUDIT")
    print(json.dumps(coverage, indent=2))
    print("severity:", dict(severity_counts))
    print("Sam Houston source key:", result["sam_houston"].get("source_key"))
    print("Sam Houston source RP:", result["sam_houston"]["source"])
    print("Sam Houston view RP:", result["sam_houston"]["view"])
    print("wrote:", CSV_OUT)
    print("wrote:", JSON_OUT)

    if hard_teams:
        print("\nREQUIRED DATA ERRORS:")
        for team in sorted(hard_teams):
            fields = sorted({r["field"] for r in rows if r["team"] == team and r["severity"] == "ERROR"})
            print(f"  {team}: {', '.join(fields)}")
        raise SystemExit(1)

    print("PASS: all universally required matchup-card fields are complete and consistent")


if __name__ == "__main__":
    main()
