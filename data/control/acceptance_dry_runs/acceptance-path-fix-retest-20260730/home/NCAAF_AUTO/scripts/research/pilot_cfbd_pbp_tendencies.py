#!/usr/bin/env python3
"""Build a small CFBD play-by-play tendency pilot without betting outcomes.

The pilot intentionally validates football feature quality before any ATS/OU join.
Raw API responses are cached so reruns do not spend additional calls.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests


BASE_URL = "https://api.collegefootballdata.com"
DEFAULT_TEAMS = ["Army", "Tennessee", "Washington State", "Iowa", "Georgia"]
RUN_TYPES = {"Rush", "Rushing Touchdown"}
PASS_TYPES = {
    "Pass Reception", "Pass Incompletion", "Passing Touchdown", "Interception",
    "Pass Interception Return", "Interception Return", "Interception Return Touchdown", "Sack",
}
NON_SCRIMMAGE_TYPES = {
    "Kickoff", "Kickoff Return (Offense)", "Kickoff Return Touchdown",
    "Punt", "Punt Return Touchdown", "Field Goal Good", "Field Goal Missed",
    "Blocked Field Goal", "Blocked Punt", "Extra Point Good", "Extra Point Missed",
    "Timeout", "Penalty", "End Period", "End of Game", "Uncategorized",
}
METRIC_COLUMNS = [
    "off_plays", "off_pass_rate", "off_neutral_pass_rate", "off_early_down_pass_rate",
    "off_qb_run_share", "off_rush_success_rate", "off_pass_success_rate",
    "off_success_rate", "off_explosiveness", "off_explosive_rush_rate", "off_explosive_pass_rate", "off_ppa",
    "off_game_clock_seconds_per_play", "def_plays", "def_pass_rate_faced",
    "def_rush_success_allowed", "def_pass_success_allowed",
    "def_success_allowed", "def_explosiveness_allowed", "def_explosive_rush_allowed", "def_explosive_pass_allowed", "def_ppa_allowed",
    "def_havoc_rate", "def_front_seven_havoc_rate", "def_db_havoc_rate",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def safe_div(num: float, den: float) -> Optional[float]:
    return num / den if den else None


def mean(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [float(v) for v in values if v is not None and pd.notna(v)]
    return sum(clean) / len(clean) if clean else None


def clock_seconds(play: Dict[str, Any]) -> Optional[int]:
    clock = play.get("clock") or {}
    try:
        return int(clock.get("minutes", 0)) * 60 + int(clock.get("seconds", 0))
    except (TypeError, ValueError):
        return None


def score_diff(play: Dict[str, Any]) -> int:
    return int(play.get("offenseScore") or 0) - int(play.get("defenseScore") or 0)


def is_run(play: Dict[str, Any]) -> bool:
    if play.get("playType") in RUN_TYPES:
        return True
    if str(play.get("playType") or "").startswith("Fumble"):
        return " run for" in str(play.get("playText") or "").lower()
    return False


def is_pass(play: Dict[str, Any]) -> bool:
    if play.get("playType") in PASS_TYPES:
        return True
    if str(play.get("playType") or "").startswith("Fumble"):
        text = str(play.get("playText") or "").lower()
        return " pass " in text or "pass complete" in text or " sacked" in text
    return False


def is_scrimmage(play: Dict[str, Any]) -> bool:
    return is_run(play) or is_pass(play)


def player_before(text: str, marker: str) -> str:
    if not text or marker not in text.lower():
        return ""
    idx = text.lower().find(marker)
    return re.sub(r"\s+", " ", text[:idx].strip())


def passer_from_text(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text or "").strip())
    patterns = [
        r"^(.+?) pass(?:es| complete| incomplete| intercepted| INTERCEPTED|$)",
        r"^(.+?) steps back to pass",
        r"pass from (.+?)(?: \(|$)",
        r"^(.+?) sacked(?: by| for|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            name = match.group(1).strip(" .,()")
            if name and len(name) <= 40:
                return name
    return ""


def identify_passers(plays: List[Dict[str, Any]]) -> set[str]:
    passers: set[str] = set()
    for play in plays:
        if not is_pass(play) or play.get("playType") == "Sack":
            continue
        name = passer_from_text(str(play.get("playText") or ""))
        if name:
            passers.add(name)
    for play in plays:
        if play.get("playType") == "Sack":
            name = passer_from_text(str(play.get("playText") or ""))
            if name:
                passers.add(name)
    return passers


class CFBDClient:
    def __init__(self, key: str, cache_dir: Path, max_calls: int, sleep_seconds: float = 0.2):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_calls = max_calls
        self.calls = 0
        self.sleep_seconds = sleep_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "ncaaf-pbp-tendency-pilot/0.1",
        })

    def get(self, endpoint: str, params: Dict[str, Any], cache_name: str) -> List[Dict[str, Any]]:
        path = self.cache_dir / cache_name
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload.get("data", payload) if isinstance(payload, dict) else payload
        if self.calls >= self.max_calls:
            raise RuntimeError(f"API call cap of {self.max_calls} reached")
        response = self.session.get(BASE_URL + endpoint, params=params, timeout=120)
        self.calls += 1
        if response.status_code in (401, 403, 429):
            raise RuntimeError(f"CFBD {endpoint} failed HTTP {response.status_code}: {response.text[:300]}")
        response.raise_for_status()
        data = response.json()
        path.write_text(json.dumps({
            "fetched_at": utc_now(), "endpoint": endpoint, "params": params, "data": data,
        }, indent=2), encoding="utf-8")
        time.sleep(self.sleep_seconds)
        return data


def load_key(path: Path) -> str:
    key = os.environ.get("CFBD_API_KEY", "").strip()
    if not key and path.exists():
        key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise SystemExit("CFBD key unavailable; set CFBD_API_KEY or provide --key-file")
    return key


def group_by_game(rows: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("gameId") is not None:
            grouped[int(row["gameId"])].append(row)
    return grouped


def game_clock_seconds_per_play(plays: List[Dict[str, Any]]) -> Optional[float]:
    """Approximate pace using game-clock gaps between consecutive plays in a drive."""
    gaps: List[int] = []
    by_drive: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for play in plays:
        if is_scrimmage(play) and play.get("driveId") is not None:
            by_drive[str(play["driveId"])].append(play)
    for drive_plays in by_drive.values():
        ordered = sorted(drive_plays, key=lambda p: int(p.get("playNumber") or 0))
        for current, following in zip(ordered, ordered[1:]):
            if current.get("period") != following.get("period"):
                continue
            start, end = clock_seconds(current), clock_seconds(following)
            if start is not None and end is not None and 0 <= start - end <= 90:
                gaps.append(start - end)
    return mean(gaps)


def summarize_offense(team: str, plays: List[Dict[str, Any]]) -> Dict[str, Any]:
    scrimmage = [p for p in plays if is_scrimmage(p)]
    runs = [p for p in scrimmage if is_run(p)]
    passes = [p for p in scrimmage if is_pass(p)]
    neutral = [p for p in scrimmage if int(p.get("period") or 0) <= 3 and abs(score_diff(p)) <= 14]
    early = [p for p in scrimmage if int(p.get("down") or 0) in (1, 2)]
    passers = identify_passers(scrimmage)
    qb_runs = [p for p in runs if player_before(str(p.get("playText") or ""), " run") in passers]
    ppa = [p.get("ppa") for p in scrimmage if p.get("ppa") is not None]
    successful_ppa = [value for value in ppa if float(value) > 0]
    return {
        "off_plays": len(scrimmage),
        "off_rushes": len(runs),
        "off_passes_including_sacks": len(passes),
        "off_pass_rate": safe_div(len(passes), len(scrimmage)),
        "off_neutral_plays": len(neutral),
        "off_neutral_pass_rate": safe_div(sum(is_pass(p) for p in neutral), len(neutral)),
        "off_early_down_plays": len(early),
        "off_early_down_pass_rate": safe_div(sum(is_pass(p) for p in early), len(early)),
        "off_qb_runs": len(qb_runs),
        "off_qb_run_share": safe_div(len(qb_runs), len(runs)),
        "off_rush_success_rate": safe_div(sum((p.get("ppa") or 0) > 0 for p in runs if p.get("ppa") is not None), sum(p.get("ppa") is not None for p in runs)),
        "off_pass_success_rate": safe_div(sum((p.get("ppa") or 0) > 0 for p in passes if p.get("ppa") is not None), sum(p.get("ppa") is not None for p in passes)),
        "off_success_rate": safe_div(len(successful_ppa), len(ppa)),
        "off_explosiveness": mean(successful_ppa),
        "off_explosive_rush_rate": safe_div(sum(float(p.get("yardsGained") or 0) >= 10 for p in runs), len(runs)),
        "off_explosive_pass_rate": safe_div(sum(float(p.get("yardsGained") or 0) >= 20 for p in passes), len(passes)),
        "off_ppa": mean(ppa),
        "off_game_clock_seconds_per_play": game_clock_seconds_per_play(scrimmage),
        "off_passers": "|".join(sorted(passers)),
        "off_play_type_count": len(Counter(p.get("playType") for p in plays)),
    }


def summarize_defense(plays: List[Dict[str, Any]]) -> Dict[str, Any]:
    scrimmage = [p for p in plays if is_scrimmage(p)]
    runs = [p for p in scrimmage if is_run(p)]
    passes = [p for p in scrimmage if is_pass(p)]
    ppa = [p.get("ppa") for p in scrimmage if p.get("ppa") is not None]
    successful_ppa = [value for value in ppa if float(value) > 0]
    return {
        "def_plays": len(scrimmage),
        "def_rushes_faced": len(runs),
        "def_passes_faced_including_sacks": len(passes),
        "def_pass_rate_faced": safe_div(len(passes), len(scrimmage)),
        "def_rush_success_allowed": safe_div(sum((p.get("ppa") or 0) > 0 for p in runs if p.get("ppa") is not None), sum(p.get("ppa") is not None for p in runs)),
        "def_pass_success_allowed": safe_div(sum((p.get("ppa") or 0) > 0 for p in passes if p.get("ppa") is not None), sum(p.get("ppa") is not None for p in passes)),
        "def_success_allowed": safe_div(len(successful_ppa), len(ppa)),
        "def_explosiveness_allowed": mean(successful_ppa),
        "def_explosive_rush_allowed": safe_div(sum(float(p.get("yardsGained") or 0) >= 10 for p in runs), len(runs)),
        "def_explosive_pass_allowed": safe_div(sum(float(p.get("yardsGained") or 0) >= 20 for p in passes), len(passes)),
        "def_ppa_allowed": mean(ppa),
    }


def flatten_advanced(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not row:
        return {}
    offense = row.get("offense") or {}
    defense = row.get("defense") or {}
    return {
        "adv_off_plays": offense.get("plays"),
        "adv_off_success_rate": offense.get("successRate"),
        "adv_off_explosiveness": offense.get("explosiveness"),
        "adv_off_ppa": offense.get("ppa"),
        "adv_def_plays": defense.get("plays"),
        "adv_def_success_rate": defense.get("successRate"),
        "adv_def_explosiveness": defense.get("explosiveness"),
        "adv_def_ppa": defense.get("ppa"),
    }


def flatten_havoc(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not row:
        return {}
    defense = row.get("defense") or {}
    return {
        "def_havoc_events": defense.get("totalHavocEvents"),
        "def_havoc_rate": defense.get("havocRate"),
        "def_front_seven_havoc_rate": defense.get("frontSevenHavocRate"),
        "def_db_havoc_rate": defense.get("dbHavocRate"),
    }


def build_rolling(game_df: pd.DataFrame) -> pd.DataFrame:
    output = []
    for team, group in game_df.sort_values(["team", "week", "game_id"]).groupby("team"):
        history: List[Dict[str, Any]] = []
        for row in group.to_dict("records"):
            record = {
                "season": row["season"], "week": row["week"], "game_id": row["game_id"],
                "team": team, "opponent": row["opponent"], "prior_games": len(history),
            }
            for col in METRIC_COLUMNS:
                record[f"pregame_{col}"] = mean(h.get(col) for h in history)
            output.append(record)
            history.append(row)
    return pd.DataFrame(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2024)
    parser.add_argument("--teams", nargs="+", default=DEFAULT_TEAMS)
    parser.add_argument("--key-file", type=Path, default=Path("/private/tmp/ncaaf_cfbd_api_key"))
    parser.add_argument("--max-calls", type=int, default=30)
    parser.add_argument("--weeks", nargs="+", type=int)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    cache_dir = args.cache_dir or Path(f"cfbd_cache/pbp_pilot_{args.season}")
    output_dir = args.output_dir or Path(f"data/research/pbp_pilot_{args.season}")
    output_dir.mkdir(parents=True, exist_ok=True)
    client = CFBDClient(load_key(args.key_file), cache_dir, args.max_calls)
    params_base = {"year": args.season, "seasonType": "regular"}
    game_rows: List[Dict[str, Any]] = []
    audit_teams: Dict[str, Any] = {}

    play_types = client.get("/plays/types", {}, "play_types.json")
    if args.weeks:
        weeks = sorted(set(args.weeks))
    else:
        calendar = client.get("/calendar", {"year": args.season}, "calendar.json")
        weeks = sorted({
            int(row["week"]) for row in calendar
            if str(row.get("seasonType") or row.get("season_type") or "").lower() == "regular"
        })
    if not weeks:
        raise RuntimeError("No regular-season weeks returned by CFBD calendar")

    weekly_plays: List[Dict[str, Any]] = []
    pilot_team_set = set(args.teams)
    for week in weeks:
        rows = client.get(
            "/plays", {**params_base, "week": week}, f"plays_week_{week:02d}.json"
        )
        for row in rows:
            if row.get("offense") not in pilot_team_set and row.get("defense") not in pilot_team_set:
                continue
            copied = dict(row)
            copied["_week"] = week
            weekly_plays.append(copied)
        del rows

    for team in args.teams:
        tag = slug(team)
        off_plays = [row for row in weekly_plays if row.get("offense") == team]
        def_plays = [row for row in weekly_plays if row.get("defense") == team]
        advanced = client.get("/stats/game/advanced", {**params_base, "team": team}, f"advanced_{tag}.json")
        havoc = client.get("/stats/game/havoc", {**params_base, "team": team}, f"havoc_{tag}.json")
        off_games, def_games = group_by_game(off_plays), group_by_game(def_plays)
        advanced_map = {int(r["gameId"]): r for r in advanced if r.get("gameId") is not None}
        havoc_map = {int(r["gameId"]): r for r in havoc if r.get("gameId") is not None}
        game_ids = sorted(set(off_games) | set(def_games) | set(advanced_map) | set(havoc_map))
        audit_teams[team] = {
            "offense_play_rows": len(off_plays), "defense_play_rows": len(def_plays),
            "advanced_rows": len(advanced), "havoc_rows": len(havoc),
            "unique_games": len(game_ids),
        }
        for game_id in game_ids:
            op = off_games.get(game_id, [])
            dp = def_games.get(game_id, [])
            adv = advanced_map.get(game_id) or {}
            sample = (op or dp or [adv])[0]
            opponent = adv.get("opponent") or sample.get("defense") or sample.get("offense") or ""
            row = {
                "season": int(adv.get("season") or args.season),
                "week": int(adv.get("week") or sample.get("_week") or 0),
                "game_id": game_id, "team": team, "opponent": opponent,
            }
            row.update(summarize_offense(team, op))
            row.update(summarize_defense(dp))
            row.update(flatten_advanced(advanced_map.get(game_id)))
            row.update(flatten_havoc(havoc_map.get(game_id)))
            game_rows.append(row)

    game_df = pd.DataFrame(game_rows).sort_values(["team", "week", "game_id"])
    if not game_df.empty:
        game_df["off_play_count_diff_vs_advanced"] = game_df["off_plays"] - pd.to_numeric(game_df["adv_off_plays"], errors="coerce")
        game_df["def_play_count_diff_vs_advanced"] = game_df["def_plays"] - pd.to_numeric(game_df["adv_def_plays"], errors="coerce")
    rolling_df = build_rolling(game_df)
    summary_df = game_df.groupby("team", as_index=False).agg({
        "game_id": "nunique", "off_plays": "sum", "off_pass_rate": "mean",
        "off_neutral_pass_rate": "mean", "off_early_down_pass_rate": "mean",
        "off_qb_run_share": "mean", "off_rush_success_rate": "mean",
        "off_pass_success_rate": "mean", "off_explosive_rush_rate": "mean",
        "off_explosive_pass_rate": "mean", "off_ppa": "mean",
        "off_game_clock_seconds_per_play": "mean", "def_pass_rate_faced": "mean",
        "def_rush_success_allowed": "mean", "def_pass_success_allowed": "mean",
        "def_ppa_allowed": "mean", "def_havoc_rate": "mean",
    }).rename(columns={"game_id": "games"})

    game_path = output_dir / "game_tendencies.csv"
    rolling_path = output_dir / "rolling_pregame_tendencies.csv"
    summary_path = output_dir / "team_summary.csv"
    audit_path = output_dir / "audit.json"
    game_df.to_csv(game_path, index=False)
    rolling_df.to_csv(rolling_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    audit = {
        "built_at": utc_now(), "season": args.season, "teams": args.teams,
        "api_calls_this_run": client.calls, "cached_files": len(list(cache_dir.glob("*.json"))),
        "weeks": weeks, "weekly_play_rows": len(weekly_plays),
        "api_play_types": len(play_types), "team_coverage": audit_teams,
        "game_rows": len(game_df), "rolling_rows": len(rolling_df),
        "off_play_count_exact_matches": int((game_df["off_play_count_diff_vs_advanced"] == 0).sum()),
        "def_play_count_exact_matches": int((game_df["def_play_count_diff_vs_advanced"] == 0).sum()),
        "off_play_count_comparable_rows": int(game_df["adv_off_plays"].notna().sum()),
        "def_play_count_comparable_rows": int(game_df["adv_def_plays"].notna().sum()),
        "off_play_count_exact_match_rate": float((game_df["off_play_count_diff_vs_advanced"] == 0).mean()),
        "def_play_count_exact_match_rate": float((game_df["def_play_count_diff_vs_advanced"] == 0).mean()),
        "max_absolute_off_play_count_diff": int(game_df["off_play_count_diff_vs_advanced"].abs().max()),
        "max_absolute_def_play_count_diff": int(game_df["def_play_count_diff_vs_advanced"].abs().max()),
        "notes": [
            "No betting outcomes were loaded or joined.",
            "QB run share is a text-derived proxy using players identified as passers in the same game.",
            "Pass attempts include sacks; success uses PPA > 0; explosive thresholds are 10 rush/20 pass yards.",
            "Pace proxy uses game-clock gaps between consecutive scrimmage plays in the same drive.",
        ],
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    print("\nTeam summary:\n", summary_df.to_string(index=False))
    print("\nWrote:", game_path, rolling_path, summary_path, audit_path, sep="\n")


if __name__ == "__main__":
    main()
