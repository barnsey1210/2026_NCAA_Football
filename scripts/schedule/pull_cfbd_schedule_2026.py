#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts.schedule.kickoff_quality import classify_kickoff
from scripts.site.team_identity import canonical_team_name

YEAR = 2026
BASE_URL = "https://api.collegefootballdata.com/games"
OUT_DIR = Path("data/canonical")
RAW_JSON = OUT_DIR / "cfbd_schedule_2026_raw.json"
OUT_JSON = OUT_DIR / "cfbd_schedule_2026.json"
AUDIT_JSON = Path("data/audits/cfbd_schedule_2026_audit.json")
PRESEASON_DB = Path("data/snapshots/preseason/preseason_db.json")

def schedule_team(value):
    raw = str(value or "").strip()
    return canonical_team_name(raw) or raw or None


def normalized_pair(game):
    return (
        schedule_team(game.get("away_team")),
        schedule_team(game.get("home_team")),
    )


def parse_game_date(game):
    raw = str(game.get("date") or game.get("start_date") or "")[:10]
    try:
        return date.fromisoformat(raw)
    except Exception:
        return None


def merge_preseason_fallbacks(games):
    """Preserve only unambiguous future preseason games omitted by CFBD."""
    if not PRESEASON_DB.exists():
        return games, []

    db = json.loads(PRESEASON_DB.read_text())

    modeled_teams = {
        schedule_team(team.get("team"))
        for team in db.get("teams", [])
        if team.get("team")
    }

    preseason_counts = {}
    current_counts = {}

    for team in modeled_teams:
        preseason_counts[team] = 0
        current_counts[team] = 0

    for game in db.get("games", []):
        if game.get("week") == 14:
            continue
        away, home = normalized_pair(game)
        if away in modeled_teams:
            preseason_counts[away] += 1
        if home in modeled_teams:
            preseason_counts[home] += 1

    for game in games:
        away, home = normalized_pair(game)
        if away in modeled_teams:
            current_counts[away] += 1
        if home in modeled_teams:
            current_counts[home] += 1

    by_pair = {}
    for game in games:
        by_pair.setdefault(normalized_pair(game), []).append(game)

    today = datetime.now(timezone.utc).date()
    fallback_rows = []

    for game in sorted(
        db.get("games", []),
        key=lambda g: (
            str(g.get("date") or ""),
            int(g.get("week") or 99),
            str(g.get("away_team") or ""),
            str(g.get("home_team") or ""),
        ),
    ):
        week = game.get("week")
        away, home = normalized_pair(game)

        if week == 14:
            continue

        modeled = [team for team in (away, home) if team in modeled_teams]
        if not modeled:
            continue

        preseason_date = parse_game_date(game)
        if preseason_date is None or preseason_date <= today:
            continue

        # Exact canonicalized matchup already exists.
        if by_pair.get((away, home)):
            continue

        # Safe reversed-orientation match near the same date.
        reversed_candidates = by_pair.get((home, away), [])
        reversed_match = False
        for candidate in reversed_candidates:
            candidate_date = parse_game_date(candidate)
            if (
                candidate_date is not None
                and abs((candidate_date - preseason_date).days) <= 2
            ):
                reversed_match = True
                break
        if reversed_match:
            continue

        # Generic FCS-name-change protection:
        # if CFBD already has a game on the same date involving the same
        # modeled FBS participant, treat it as the same scheduled game.
        same_date_modeled_match = False
        for candidate in games:
            candidate_date = parse_game_date(candidate)
            if candidate_date != preseason_date:
                continue

            ca, ch = normalized_pair(candidate)
            candidate_modeled = {
                team for team in (ca, ch) if team in modeled_teams
            }

            if candidate_modeled.intersection(modeled):
                same_date_modeled_match = True
                break

        if same_date_modeled_match:
            continue

        # Every modeled FBS participant must currently have a genuine deficit.
        if not all(
            current_counts.get(team, 0) < preseason_counts.get(team, 0)
            for team in modeled
        ):
            continue

        fallback = {
            "cfbd_game_id": None,
            "season": YEAR,
            "week": week,
            "provider_week": None,
            "season_type": "regular",
            "date": str(game.get("date") or "")[:10] or None,
            "start_date": game.get("cfbd_start_date"),
            "start_time_tbd": True,
            "kickoff_status": "UNRESOLVED",
            "kickoff_time_verified": False,
            "completed": bool(
                game.get("cfbd_completed") or game.get("completed")
            ),
            "neutral_site": bool(game.get("neutral_site")),
            "conference_game": bool(game.get("is_conference_game")),
            "home_team": game.get("home_team"),
            "away_team": game.get("away_team"),
            "home_points": game.get("home_points"),
            "away_points": game.get("away_points"),
            "home_postgame_win_probability": None,
            "away_postgame_win_probability": None,
            "pgwe_status": "missing",
            "status": game.get("cfbd_status"),
            "cfbd_last_updated": None,
            "pulled_at": None,
            "schedule_source": "PRESEASON_FALLBACK",
            "preseason_game_id": game.get("game_id"),
        }

        games.append(fallback)
        by_pair.setdefault((away, home), []).append(fallback)

        for team in modeled:
            current_counts[team] += 1

        fallback_rows.append({
            "preseason_game_id": game.get("game_id"),
            "week": week,
            "date": fallback["date"],
            "away_team": game.get("away_team"),
            "home_team": game.get("home_team"),
            "reason": "FUTURE_SCHEDULE_DEFICIT",
        })

    return games, fallback_rows

def pgwe_pair(g):
    """Return the provider PGWE pair only when it is valid and complementary."""
    home = g.get("homePostgameWinProbability")
    away = g.get("awayPostgameWinProbability")
    if home is None and away is None:
        return None, None, "missing"
    try:
        home = float(home)
        away = float(away)
    except (TypeError, ValueError):
        return None, None, "invalid"
    if not (0 <= home <= 1 and 0 <= away <= 1):
        return None, None, "invalid"
    if abs(home + away - 1.0) > 1e-6:
        return None, None, "non_complementary"
    return home, away, "available"

def require_key():
    key = os.environ.get("CFBD_API_KEY")
    if not key:
        raise SystemExit("Missing CFBD_API_KEY")
    return key

def main():
    pulled_at = datetime.now(timezone.utc).isoformat()
    r = requests.get(
        BASE_URL,
        headers={"Authorization": f"Bearer {require_key()}"},
        params={"year": YEAR, "seasonType": "regular"},
        timeout=45,
    )
    if r.status_code != 200:
        raise SystemExit(f"CFBD games request failed: HTTP {r.status_code}\\n{r.text[:800]}")
    raw = r.json()
    if not isinstance(raw, list):
        raise SystemExit(f"Unexpected CFBD response type: {type(raw)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    RAW_JSON.write_text(json.dumps(raw, indent=2) + "\n")

    games = []
    pgwe_status_counts = {"available": 0, "missing": 0, "invalid": 0, "non_complementary": 0}
    for g in raw:
        start = g.get("startDate")
        local_date = None
        if start:
            try:
                dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
                local_date = dt.astimezone(ZoneInfo("America/New_York")).date().isoformat()
            except Exception:
                local_date = str(start)[:10]

        provider_week = g.get("week")

        # Canonical 2026 site week convention:
        # Saturday, Aug. 29 is Week 0 even though CFBD currently labels it
        # Week 1. Normalize here so every downstream consumer receives the
        # same canonical week numbering.
        canonical_week = provider_week
        if local_date == "2026-08-29":
            canonical_week = 0

        kickoff_status = classify_kickoff(start, g.get("startTimeTBD"))
        home_pgwe, away_pgwe, pgwe_status = pgwe_pair(g)
        pgwe_status_counts[pgwe_status] += 1
        games.append({
            "cfbd_game_id": g.get("id"),
            "season": g.get("season"),
            "week": canonical_week,
            "provider_week": provider_week,
            "season_type": g.get("seasonType"),
            "date": local_date,
            "start_date": start,
            "start_time_tbd": g.get("startTimeTBD"),
            "kickoff_status": kickoff_status,
            "kickoff_time_verified": kickoff_status == "VERIFIED_KICKOFF",
            "completed": g.get("completed"),
            "neutral_site": g.get("neutralSite"),
            "conference_game": g.get("conferenceGame"),
            "home_team": g.get("homeTeam"),
            "away_team": g.get("awayTeam"),
            "home_points": g.get("homePoints"),
            "away_points": g.get("awayPoints"),
            # Preserve valid provider probabilities on the 0-1 scale. Invalid
            # or non-complementary pairs fail closed.
            "home_postgame_win_probability": home_pgwe,
            "away_postgame_win_probability": away_pgwe,
            "pgwe_status": pgwe_status,
            "status": g.get("status"),
            "cfbd_last_updated": g.get("lastUpdated"),
            "pulled_at": pulled_at,
        })
    games = [g for g in games if g["home_team"] and g["away_team"]]
    games, preseason_fallbacks = merge_preseason_fallbacks(games)
    games.sort(key=lambda g: (g["date"] or "", g["week"] or 0, g["away_team"], g["home_team"]))

    OUT_JSON.write_text(json.dumps({
        "schema_version": "cfbd-schedule-2026-v1",
        "season": YEAR,
        "source": "CollegeFootballData /games",
        "pulled_at": pulled_at,
        "games": games,
    }, indent=2) + "\n")

    audit = {
        "schema_version": "cfbd-schedule-2026-audit-v1",
        "pulled_at": pulled_at,
        "raw_rows": len(raw),
        "normalized_rows": len(games),
        "preseason_fallback_rows": len(preseason_fallbacks),
        "preseason_fallbacks": preseason_fallbacks,
        "dated_rows": sum(bool(g["date"]) for g in games),
        "tbd_rows": sum(bool(g["start_time_tbd"]) for g in games),
        "kickoff_quality": {
            status: sum(g["kickoff_status"] == status for g in games)
            for status in ("VERIFIED_KICKOFF", "TBD", "DATE_PLACEHOLDER", "MISSING", "UNRESOLVED")
        },
        "canonical_week_overrides": sum(
            g.get("week") != g.get("provider_week") for g in games
        ),
        "pgwe": pgwe_status_counts,
        "completed_games_with_pgwe": sum(
            bool(g["completed"]) and g["pgwe_status"] == "available" for g in games
        ),
        "first_date": min((g["date"] for g in games if g["date"]), default=None),
        "last_date": max((g["date"] for g in games if g["date"]), default=None),
    }
    AUDIT_JSON.write_text(json.dumps(audit, indent=2) + "\n")
    print(f"Wrote {OUT_JSON}: {len(games)} games")
    print(json.dumps(audit, indent=2))

if __name__ == "__main__":
    main()
