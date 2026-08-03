#!/usr/bin/env python3
"""Build the canonical production Conference Logo Schedule page."""

from __future__ import annotations

from datetime import date, datetime
import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "build" / "public_site"
OUT_FILE = OUT_DIR / "conferences.html"

CONF_PATH = ROOT / "data" / "site" / "conference_workspace.json"
MATCHUPS_PATH = ROOT / "data" / "site" / "matchups_view.json"
DEFAULT_CONFERENCE = "ACC"

# Logos that are too dark on the navy table background receive a light badge.
DARK_TEAM_LOGO_SLUGS = {
    "california", "wake-forest", "penn-state", "iowa", "michigan-state",
    "navy", "army", "vanderbilt", "baylor", "colorado", "purdue",
}

SPORTSBOOK_LOGO_CANDIDATES = {
    "fanduel": [
        "logos/books/fanduel.png", "logos/sportsbooks/fanduel.svg", "logos/sportsbooks/fanduel.png",
        "sportsbook_logos/fanduel.svg", "sportsbook_logos/fanduel.png",
        "assets/sportsbooks/fanduel.svg", "assets/sportsbooks/fanduel.png",
        "logos/fanduel.svg", "logos/fanduel.png",
    ],
    "draftkings": [
        "logos/books/draftkings.png", "logos/sportsbooks/draftkings.svg", "logos/sportsbooks/draftkings.png",
        "sportsbook_logos/draftkings.svg", "sportsbook_logos/draftkings.png",
        "assets/sportsbooks/draftkings.svg", "assets/sportsbooks/draftkings.png",
        "logos/draftkings.svg", "logos/draftkings.png",
    ],
    "betmgm": [
        "logos/books/betmgm.png", "logos/sportsbooks/betmgm.svg", "logos/sportsbooks/betmgm.png",
        "sportsbook_logos/betmgm.svg", "sportsbook_logos/betmgm.png",
        "assets/sportsbooks/betmgm.svg", "assets/sportsbooks/betmgm.png",
        "logos/betmgm.svg", "logos/betmgm.png",
    ],
    "caesars": [
        "logos/books/caesars.png", "logos/sportsbooks/caesars.svg", "logos/sportsbooks/caesars.png",
        "sportsbook_logos/caesars.svg", "sportsbook_logos/caesars.png",
        "assets/sportsbooks/caesars.svg", "assets/sportsbooks/caesars.png",
        "logos/caesars.svg", "logos/caesars.png",
    ],
    "hard rock bet": [
        "logos/sportsbooks/hard-rock-bet.svg", "logos/sportsbooks/hard-rock-bet.png",
        "sportsbook_logos/hard-rock-bet.svg", "sportsbook_logos/hard-rock-bet.png",
        "assets/sportsbooks/hard-rock-bet.svg", "assets/sportsbooks/hard-rock-bet.png",
    ],
    "bet365": [
        "logos/sportsbooks/bet365.svg", "logos/sportsbooks/bet365.png",
        "sportsbook_logos/bet365.svg", "sportsbook_logos/bet365.png",
        "assets/sportsbooks/bet365.svg", "assets/sportsbooks/bet365.png",
        "logos/bet365.svg", "logos/bet365.png",
    ],
}


def load_json(path: Path) -> Any:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text())


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def pct(value: Any, digits: int = 0) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.{digits}f}%"


def number(value: Any, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}"


def signed(value: Any, digits: int = 1) -> str:
    if value is None:
        return "—"
    value = float(value)
    if abs(value) < 0.05:
        return "0.0"
    return f"{value:+.{digits}f}"


def date_label(value: Any) -> str:
    if not value:
        return "TBD"
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%b %-d")
    except ValueError:
        return str(value)


def rank_tone(rank: Any) -> str:
    """Color ranks by equal thirds of the 138-team FBS field."""
    if rank is None:
        return "rank-unknown"
    rank = int(rank)
    if rank <= 46:
        return "rank-good"
    if rank <= 92:
        return "rank-mid"
    return "rank-low"


def sportsbook_logo(book: Any) -> str | None:
    if not book:
        return None
    key = str(book).strip().lower()
    candidates = SPORTSBOOK_LOGO_CANDIDATES.get(key, [])
    for candidate in candidates:
        if (ROOT / candidate).exists():
            return candidate
    return None


def health_class(win_prob: float | None) -> str:
    if win_prob is None:
        return "unknown"
    if win_prob >= 0.80:
        return "strong-win"
    if win_prob >= 0.62:
        return "lean-win"
    if win_prob >= 0.45:
        return "coin-flip"
    if win_prob >= 0.25:
        return "lean-loss"
    return "strong-loss"


def coach_summary(coach: dict[str, Any] | None) -> str:
    if not coach:
        return "Coach betting context unavailable"
    periods = coach.get("periods") or []
    full_game = next(
        (
            period
            for period in periods
            if isinstance(period, dict) and period.get("period") == "full_game"
        ),
        None,
    )
    coach_name = coach.get("coach") or "Coach"
    if not full_game or not full_game.get("ats_record"):
        return f"{coach_name}: no matched full-game ATS sample"
    return (
        f"{coach_name}: {full_game.get('ats_record')} ATS, "
        f"avg ATS margin {number(full_game.get('ats_margin'), 1)}"
    )


def game_for_team(row: dict[str, Any], team: str) -> dict[str, Any]:
    game = row.get("game", {})
    teams = row.get("teams", {})
    model = row.get("model", {})
    market = row.get("market", {})
    matchup = row.get("matchup", {})

    away = game.get("away_team")
    home = game.get("home_team")
    neutral = bool(game.get("neutral_site"))
    is_home = team == home
    opponent = away if is_home else home
    opponent_side = teams.get("away" if is_home else "home", {})

    home_spread = model.get("home_spread")
    home_win_probability = model.get("home_win_probability")
    team_margin = None
    if home_spread is not None:
        team_margin = -float(home_spread) if is_home else float(home_spread)

    team_win_probability = None
    if home_win_probability is not None:
        team_win_probability = (
            float(home_win_probability)
            if is_home
            else 1.0 - float(home_win_probability)
        )

    spread = market.get("spread") if isinstance(market.get("spread"), dict) else {}
    total = market.get("total") if isinstance(market.get("total"), dict) else {}
    market_home_line = spread.get("home_line")
    team_market_line = None
    if market_home_line is not None:
        team_market_line = float(market_home_line) if is_home else -float(market_home_line)

    spread_edge = None
    if team_margin is not None and team_market_line is not None:
        spread_edge = team_margin + team_market_line

    coaches = matchup.get("coaches") or []
    team_coach = next((coach for coach in coaches if coach.get("team") == team), None)

    return {
        "game_id": game.get("game_id"),
        "week": int(game.get("week")) if game.get("week") is not None else None,
        "date": game.get("date"),
        "team": team,
        "opponent": opponent,
        "location": "N" if neutral else ("H" if is_home else "@"),
        "opponent_logo": opponent_side.get("logo_slug"),
        "opponent_rank": opponent_side.get("overall_rank"),
        "model_margin": team_margin,
        "win_probability": team_win_probability,
        "model_total": model.get("total"),
        "market_spread": team_market_line,
        "market_total": total.get("line"),
        "spread_book": spread.get("book"),
        "spread_edge": spread_edge,
        "coach_summary": coach_summary(team_coach),
        "completed": bool(game.get("completed")),
        "team_score": game.get("home_score") if is_home else game.get("away_score"),
        "opponent_score": game.get("away_score") if is_home else game.get("home_score"),
    }


def build_payload(
    conference_data: dict[str, Any], matchup_data: dict[str, Any]
) -> dict[str, Any]:
    all_matchups = matchup_data.get("games", [])
    conferences: list[dict[str, Any]] = []

    for conference in conference_data.get("conferences", []):
        teams = conference.get("teams", [])
        team_names = {team.get("team") for team in teams}
        schedules = {team: {} for team in team_names}
        all_games = {team: {} for team in team_names}
        week_dates: dict[int, str] = {}
        conf_weeks: set[int] = set()

        for row in all_matchups:
            game = row.get("game", {})
            away = game.get("away_team")
            home = game.get("home_team")
            week = game.get("week")
            if week is None:
                continue
            week = int(week)

            for team in (away, home):
                if team in team_names:
                    all_games[team][week] = {
                        "date": game.get("date"),
                        "opponent": home if team == away else away,
                    }

            if away not in team_names or home not in team_names:
                continue

            conf_weeks.add(week)
            if game.get("date") and week not in week_dates:
                week_dates[week] = game.get("date")
            schedules[away][week] = game_for_team(row, away)
            schedules[home][week] = game_for_team(row, home)

        if conf_weeks:
            all_team_weeks = {week for team_games in all_games.values() for week in team_games}
            first_week = min(all_team_weeks) if all_team_weeks else min(conf_weeks)
            last_week = max(conf_weeks)
            weeks = list(range(first_week, last_week + 1))
        else:
            weeks = []

        rows: list[dict[str, Any]] = []
        for team in teams:
            team_name = team.get("team")
            cells = []
            for week in weeks:
                if week in schedules[team_name]:
                    cells.append({"type": "conference", **schedules[team_name][week]})
                elif week in all_games[team_name]:
                    cells.append(
                        {
                            "type": "nonconference",
                            "week": week,
                            "date": all_games[team_name][week].get("date"),
                            "opponent": all_games[team_name][week].get("opponent"),
                        }
                    )
                else:
                    cells.append({"type": "bye", "week": week, "date": week_dates.get(week)})

            rows.append(
                {
                    "team": team_name,
                    "slug": team.get("slug"),
                    "rank": team.get("rank"),
                    "rank_tone": rank_tone(team.get("rank")),
                    "rating": team.get("rating"),
                    "dark_logo": team.get("slug") in DARK_TEAM_LOGO_SLUGS,
                    "current_conf_wins": team.get("current_conf_wins", 0),
                    "current_conf_losses": team.get("current_conf_losses", 0),
                    "projected_conf_wins": team.get("projected_conf_wins"),
                    "projected_conf_losses": team.get("projected_conf_losses"),
                    "projected_finish": team.get("projected_finish"),
                    "make_title_game_pct": team.get("make_title_game_pct"),
                    "title_pct": team.get("title_pct"),
                    "title_price": team.get("title_price"),
                    "title_book": team.get("title_book"),
                    "title_book_logo": sportsbook_logo(team.get("title_book")),
                    "title_market_prob": team.get("title_market_prob"),
                    "title_edge": team.get("title_edge"),
                    "conf_sos_rank": team.get("conf_sos_rank"),
                    "remaining_sos_rank": team.get("remaining_sos_rank"),
                    "conference_size": len(teams),
                    "cells": cells,
                }
            )

        conferences.append(
            {
                "conference": conference.get("conference"),
                "slug": conference.get("slug"),
                "conference_rank": conference.get("conference_rank"),
                "average_team_rating": conference.get("average_team_rating"),
                "weeks": [
                    {
                        "week": week,
                        "date": week_dates.get(week)
                        or next((g.get("date") for games in all_games.values() if (g := games.get(week)) and g.get("date")), None),
                    }
                    for week in weeks
                ],
                "rows": rows,
            }
        )

    return {"default_conference": DEFAULT_CONFERENCE, "conferences": conferences}


def main() -> None:
    conference_data = load_json(CONF_PATH)
    matchup_data = load_json(MATCHUPS_PATH)
    payload = build_payload(conference_data, matchup_data)
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NCAAF Conference Logo Schedule</title>
<link rel="stylesheet" href="page_health.css">
<script defer src="page_health.js"></script>
<style>
:root {{ color-scheme:dark; --bg:#07101d; --panel:#0d1726; --panel2:#111e30; --line:#243247; --text:#edf4ff; --muted:#8fa0b7; }}
* {{ box-sizing:border-box; }}
html,body {{ width:100%; max-width:100%; overflow-x:hidden; }}
body {{ margin:0; padding-bottom:52px; background:var(--bg); color:var(--text); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
button,select {{ font:inherit; }}
.page {{ width:100%; max-width:100vw; padding:18px; overflow:hidden; }}
.header {{ width:100%; min-width:0; display:flex; justify-content:space-between; gap:20px; align-items:end; margin-bottom:12px; }}
h1 {{ margin:0; font-size:25px; }}
.subtitle,.note {{ color:var(--muted); font-size:12px; }}
.controls {{ min-width:0; display:flex; gap:10px; flex-wrap:wrap; align-items:center; justify-content:flex-end; }}
select {{ color:var(--text); background:#101c2c; border:1px solid var(--line); border-radius:8px; padding:8px 10px; }}
.legend {{ display:flex; gap:7px; flex-wrap:wrap; margin:10px 0 12px; font-size:10px; color:var(--muted); }}
.legend span {{ padding:5px 7px; border:1px solid var(--line); border-radius:6px; }}
.schedule-layout {{ width:100%; max-width:100%; display:grid; grid-template-columns:226px minmax(0,1fr) 254px; border:1px solid var(--line); border-radius:10px; background:var(--panel); overflow:hidden; }}
.floating-table-header {{ position:fixed; top:0; left:0; z-index:75; display:none; grid-template-columns:226px minmax(0,1fr) 254px; background:#101c2c; border:1px solid var(--line); border-top:0; box-shadow:0 8px 18px rgba(0,0,0,.38); overflow:hidden; }}
.floating-table-header.visible {{ display:grid; }}
.floating-table-header table {{ border-collapse:separate; border-spacing:0; width:100%; table-layout:fixed; }}
.floating-table-header .floating-schedule {{ min-width:0; overflow:hidden; background:#101c2c; }}
.floating-table-header .floating-schedule table {{ width:max-content; min-width:100%; table-layout:auto; will-change:transform; }}
.floating-table-header th {{ position:static; height:46px; background:#101c2c; }}
.floating-table-header .floating-left {{ border-right:1px solid var(--line); box-shadow:8px 0 14px rgba(0,0,0,.22); z-index:2; }}
.floating-table-header .floating-right {{ border-left:1px solid var(--line); box-shadow:-8px 0 14px rgba(0,0,0,.22); z-index:2; }}
.fixed-pane {{ min-width:0; overflow:hidden; background:var(--panel); position:relative; z-index:6; }}
.left-pane {{ border-right:1px solid var(--line); box-shadow:8px 0 14px rgba(0,0,0,.22); }}
.right-pane {{ border-left:1px solid var(--line); box-shadow:-8px 0 14px rgba(0,0,0,.22); }}
.schedule-scroll {{ min-width:0; overflow-x:auto; overflow-y:hidden; scrollbar-gutter:stable; background:var(--panel); }}
.schedule-scroll table {{ width:max-content; min-width:100%; }}
.fixed-pane table {{ width:100%; table-layout:fixed; }}
table {{ border-collapse:separate; border-spacing:0; }}
thead tr {{ height:46px; }}
tbody tr {{ height:112px; }}
tbody td {{ height:112px; }}
th,td {{ border-right:1px solid var(--line); border-bottom:1px solid var(--line); padding:4px; text-align:center; vertical-align:middle; background:var(--panel); }}
th {{ position:sticky; top:0; z-index:8; background:#101c2c; color:var(--muted); font-size:10px; letter-spacing:.04em; text-transform:uppercase; }}
th.sortable {{ cursor:pointer; user-select:none; }}
th.sortable:hover {{ color:var(--text); }}
th .sort-arrow {{ margin-left:4px; opacity:.35; }}
th.sorted .sort-arrow {{ opacity:1; }}
.sticky-left {{ z-index:7; }}
.team-column {{ width:168px; text-align:left; }}
.record-column {{ width:58px; }}
th.sticky-left {{ z-index:10; }}
.team-name {{ display:flex; align-items:center; gap:8px; }}
.team-name img {{ width:32px; height:32px; object-fit:contain; }}
.team-logo-badge {{ width:38px; height:38px; display:grid; place-items:center; border-radius:9px; flex:0 0 38px; }}
.team-logo-badge.light-logo {{ background:#f7f8fb; box-shadow:0 0 0 1px rgba(255,255,255,.30) inset; }}
.team-logo-badge.light-logo img {{ width:30px; height:30px; }}
.team-primary {{ font-size:15px; line-height:1.1; }}
.team-meta {{ display:flex; align-items:center; gap:5px; margin-top:4px; font-size:13px; line-height:1; font-weight:800; }}
.team-meta .rating-value {{ color:var(--muted); }}
.rank-good {{ color:#49e99a; }} .rank-mid {{ color:#f4c451; }} .rank-low {{ color:#ff6877; }} .rank-unknown {{ color:var(--muted); }}
.sos-lines {{ display:grid; gap:2px; margin-top:5px; font-size:9px; line-height:1.15; font-weight:750; }}
.sos-easy {{ color:#49e99a; }} .sos-mid {{ color:#f4c451; }} .sos-hard {{ color:#ff6877; }} .sos-unknown {{ color:var(--muted); }}
.record-column strong {{ font-size:15px; }}
.week-header {{ width:84px; min-width:84px; }}
.week-header strong,.week-header small {{ display:block; }}
.week-header strong {{ color:var(--text); font-size:10px; }}
.week-header small {{ margin-top:2px; color:var(--muted); font-size:8px; }}
.schedule-cell {{ width:76px; height:102px; min-height:102px; border-radius:7px; padding:5px; display:flex; flex-direction:column; justify-content:space-between; text-decoration:none; color:var(--text); border:1px solid rgba(255,255,255,.08); cursor:pointer; }}
.cell-top,.projection {{ display:flex; justify-content:space-between; align-items:center; gap:4px; }}
.location {{ font-size:10px; font-weight:800; }}
.rank-badge {{ font-size:9px; padding:1px 4px; border-radius:5px; background:#e6bd50; color:#111; font-weight:800; }}
.logo-wrap {{ height:30px; display:grid; place-items:center; }}
.logo-wrap img {{ width:28px; height:28px; object-fit:contain; }}
.logo-wrap.light-logo {{ width:36px; height:36px; margin:0 auto; border-radius:8px; background:#f7f8fb; box-shadow:0 0 0 1px rgba(255,255,255,.28) inset; }}
.logo-wrap.light-logo img {{ width:27px; height:27px; }}
.opponent-name {{ font-size:8px; line-height:1.05; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.margin {{ font-size:12px; font-weight:800; }}
.probability {{ font-size:10px; font-weight:700; }}
.win-elite {{ background:linear-gradient(160deg,#00371f,#005f35); border-color:#19b968; }} .win-strong {{ background:linear-gradient(160deg,#006338,#087c49); border-color:#23c475; }} .win-lean {{ background:linear-gradient(160deg,#2d654b,#3e825f); border-color:#62a980; }} .toss-up {{ background:linear-gradient(160deg,#766113,#9b7f18); border-color:#d3ad2a; }} .loss-lean {{ background:linear-gradient(160deg,#805024,#a1652d); border-color:#d1843f; }} .loss-strong {{ background:linear-gradient(160deg,#842d34,#a33a42); border-color:#d34d57; }} .loss-elite {{ background:linear-gradient(160deg,#a81825,#cf2634); border-color:#ff4e59; }} .final-win {{ background:#007f45; border-color:#22be72; }} .final-loss {{ background:#b51f2d; border-color:#ee4652; }} .unknown {{ background:#293342; }}
.bye,.nonconf {{ justify-content:center; align-items:center; background:#151f2d; color:#718197; font-size:9px; font-weight:800; }}
.nonconf {{ color:#55647a; }}
.nonconf small {{ display:block; max-width:68px; margin-top:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:8px; font-weight:500; }}
.sticky-right {{ z-index:7; background:var(--panel2); }}
th.sticky-right {{ z-index:10; background:#101c2c; }}
.win-title {{ width:82px; }}
.make-title {{ width:78px; }}
.proj-finish {{ width:94px; }}
.outcome {{ font-weight:800; font-size:13px; }}
.proj-finish .finish-rank,.proj-finish .record {{ font-size:13px; line-height:1.15; display:block; }}
.proj-finish .record {{ margin-top:4px; color:var(--muted); }}
.title-prob {{ color:#79e9b4; }}
.market-price {{ display:block; margin-top:4px; font-size:11px; color:#d8e2ef; }}
.market-edge {{ display:block; margin-top:2px; font-size:10px; }}
.edge-pos {{ color:#53e38f; }} .edge-near {{ color:#f0c74b; }} .edge-neg {{ color:#ff6b70; }}
.outcome-link {{ color:inherit; text-decoration:none; display:block; }}
.book-line {{ display:flex; align-items:center; justify-content:center; gap:5px; margin-top:4px; min-height:18px; }}
.sportsbook-logo-wrap {{ display:inline-flex; align-items:center; justify-content:center; width:34px; height:26px; border-radius:7px; background:rgba(255,255,255,.96); border:1px solid rgba(255,255,255,.24); }}
.sportsbook-logo {{ max-width:27px; max-height:22px; object-fit:contain; display:block; }}
.sportsbook-wordmark {{ display:none; }}
.book-icon {{ width:24px; height:24px; border-radius:7px; display:inline-grid; place-items:center; color:#fff; font-size:8px; font-weight:900; letter-spacing:-.03em; box-shadow:0 0 0 1px rgba(255,255,255,.20) inset; }}
.book-fd {{ background:#1261a0; }} .book-dk {{ background:#f36c21; }} .book-mgm {{ background:#b79b5b; color:#101010; }} .book-cz {{ background:#171717; }} .book-hr {{ background:#5b1c83; }} .book-b365 {{ background:#087b55; }} .book-generic {{ background:#44536a; }}
.futures-label {{ display:block; margin-top:4px; color:#a9b8cb; font-size:10px; font-weight:700; }}
.range-key {{ position:fixed; left:0; right:0; bottom:0; z-index:80; display:flex; align-items:center; justify-content:center; gap:18px; flex-wrap:nowrap; overflow-x:auto; color:#c5d2e4; font-size:11px; margin:0; padding:10px 14px; background:rgba(7,16,29,.97); border-top:1px solid var(--line); box-shadow:0 -8px 20px rgba(0,0,0,.28); scrollbar-width:thin; white-space:nowrap; }}
.range-key span {{ display:inline-flex; flex:0 0 auto; align-items:center; gap:6px; }}
.range-dot {{ width:12px; height:12px; border-radius:50%; display:inline-block; border:1px solid rgba(255,255,255,.2); }}
.range-dot.elite-win {{ background:#004f2d; }} .range-dot.strong-win {{ background:#087c49; }} .range-dot.lean-win {{ background:#3e825f; }} .range-dot.toss {{ background:#9b7f18; }} .range-dot.lean-loss {{ background:#a1652d; }} .range-dot.strong-loss {{ background:#a33a42; }} .range-dot.elite-loss {{ background:#cf2634; }}
.final-dot {{ width:13px; height:13px; display:inline-grid; place-items:center; border-radius:50%; background:#f5f7fa; color:#111; font-size:9px; font-weight:900; }}
.current-week-header {{ outline:2px solid #fff; outline-offset:-2px; color:#fff; }}
td.current-week-cell .schedule-cell {{ box-shadow:0 0 0 2px #fff inset; }}
.week-status {{ color:#f0c74b; font-weight:800; font-size:13px; }}
.popover {{ position:fixed; z-index:50; width:min(340px,calc(100vw - 24px)); background:#101c2c; border:1px solid #34445d; border-radius:10px; box-shadow:0 18px 45px rgba(0,0,0,.45); padding:12px; display:none; }}
.popover.open {{ display:block; }}
.popover-head {{ display:flex; justify-content:space-between; gap:10px; align-items:start; margin-bottom:8px; }}
.popover h3 {{ margin:0; font-size:15px; }}
.popover .meta {{ color:var(--muted); font-size:10px; margin-top:2px; }}
.popover-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px; margin:9px 0; }}
.popover-metric {{ background:#0b1523; border:1px solid var(--line); border-radius:7px; padding:7px; }}
.popover-metric span {{ display:block; color:var(--muted); font-size:9px; }}
.popover-metric b {{ display:block; margin-top:2px; }}
.popover-coach {{ color:#c5d2e4; font-size:10px; line-height:1.4; margin:8px 0; }}
.popover a {{ color:#83b7ff; font-size:11px; font-weight:700; text-decoration:none; }}
.close-popover {{ border:0; background:transparent; color:var(--muted); cursor:pointer; font-size:17px; padding:0; }}
.empty {{ padding:32px; color:var(--muted); text-align:center; }}
@media (max-width:1050px) {{ .schedule-layout{{grid-template-columns:202px minmax(0,1fr) 226px}} .team-column{{width:148px}} .record-column{{width:54px}} .proj-finish{{width:84px}} .make-title{{width:68px}} .win-title{{width:74px}} .page{{padding:12px}} }}
@media (max-width:700px) {{ body{{padding-bottom:48px}} .range-key{{justify-content:flex-start;gap:13px;padding:9px 10px;font-size:10px}} .page{{padding:10px}} .header{{display:block}} .controls{{margin-top:10px;justify-content:flex-start}} .schedule-layout{{grid-template-columns:176px minmax(0,1fr) 210px}} .team-column{{width:126px}} .record-column{{width:50px}} .team-primary{{font-size:13px}} .team-meta{{font-size:11px}} .sos-lines{{font-size:8px}} .proj-finish{{width:76px}} .make-title{{width:62px}} .win-title{{width:72px}} }}

.top {{ width:100%; display:flex; align-items:center; gap:16px; padding:12px 18px; border-bottom:1px solid var(--line); background:#071326; overflow-x:auto; }}
.top .brand {{ font-size:20px; font-weight:950; white-space:nowrap; }}
.top .brand a,.top .nav a {{ color:inherit; text-decoration:none; }}
.top .nav {{ display:flex; align-items:center; gap:4px; white-space:nowrap; }}
.top .nav a {{ color:var(--muted); padding:8px 10px; border-radius:9px; font-weight:850; }}
.top .nav a.active {{ background:#173b72; color:#fff; }}
.health-toggle {{ position:relative; margin-left:auto; }}
.health-toggle-button {{
  appearance:none; display:inline-flex; align-items:center; gap:7px; cursor:pointer;
  border:1px solid #294867; border-radius:999px; padding:6px 10px;
  background:#0d1d32; color:#c9d7e8; font-size:11px; font-weight:850;
  white-space:nowrap; user-select:none;
}}
.health-toggle.open .health-toggle-button {{ border-color:#5f8bb7; background:#132944; color:#fff; }}
.health-dot {{ width:9px; height:9px; border-radius:50%; display:inline-block; box-shadow:0 0 0 3px rgba(148,163,184,.12); background:#64748b; }}
.health-dot.green {{ background:#34d399; box-shadow:0 0 0 3px rgba(52,211,153,.14); }}
.health-dot.yellow {{ background:#fbbf24; box-shadow:0 0 0 3px rgba(251,191,36,.14); }}
.health-dot.red {{ background:#fb7185; box-shadow:0 0 0 3px rgba(251,113,133,.14); }}
#page-health-summary {{
  position:absolute; z-index:80; top:calc(100% + 8px); right:0;
  width:min(720px,calc(100vw - 28px)); margin:0;
  filter:drop-shadow(0 14px 30px rgba(0,0,0,.42));
}}
.health-details-panel {{ display:none; position:absolute; top:calc(100% + 8px); right:0; z-index:80; width:min(720px,calc(100vw - 28px)); max-height:70vh; overflow:auto; background:#0b1f38; border:1px solid #31577d; border-radius:12px; box-shadow:0 18px 50px rgba(0,0,0,.45); padding:12px; }}
.health-toggle.open .health-details-panel {{ display:block; }}
#page-health-summary {{ position:absolute !important; width:1px !important; height:1px !important; overflow:hidden !important; clip:rect(0 0 0 0) !important; white-space:nowrap !important; border:0 !important; padding:0 !important; margin:-1px !important; }}
@media (max-width:900px) {{ .health-toggle{{margin-left:0}} .health-details-panel{{left:0;right:auto}} }}
</style>
</head>
<body>
<div class="top"><div class="brand"><a href="index.html">NCAAF</a></div><div class="nav"><a href="index.html">Dashboard</a><a href="ratings.html">Ratings</a><a href="openers.html">Openers</a><a href="matchups.html">Matchups</a><a href="odds.html">ODDS</a><a href="schedule.html">Schedule</a><a href="futures.html">Futures</a><a class="active" href="conferences.html">Conferences</a><a href="playoff.html">Playoff</a><a href="simulations.html">Simulations</a><a href="betting.html">Betting</a><a href="v1.html">V1 Reference</a></div></div>
<div class="page">
  <div class="header">
    <div>
      <h1 id="pageTitle">Conference Logo Schedule</h1>
      <div class="subtitle">Conference games only · model margin and win probability · click any matchup for detail</div>
    </div>
    <div class="health-toggle" id="healthToggle">
      <button type="button" class="health-toggle-button" id="healthToggleButton" aria-expanded="false" aria-controls="healthDetailsPanel"><span class="health-dot" id="healthDot"></span><span id="healthLabel">Data health</span></button>
      <div id="page-health-summary"></div>
      <div class="health-details-panel" id="healthDetailsPanel"></div>
    </div>
    <div class="controls">
      <label for="conferenceSelect" class="subtitle">Conference</label>
      <select id="conferenceSelect"></select>
      <button type="button" id="thisWeekBtn" class="week-status">This Week</button>
      <span id="weekStatus" class="week-status"></span>
    </div>
  </div>

  <div class="legend">
    <span>Margin = projected result from team perspective</span>
    <span>Win % = model probability</span>
    <span>H / @ / N = site</span>
    <span>NON-CONF = omitted game</span>
    <span>BYE = no scheduled game</span>
  </div>

  <div class="schedule-layout" id="scheduleLayout">
    <div class="fixed-pane left-pane">
      <table aria-label="Team and conference record">
        <thead><tr id="leftHeaderRow"></tr></thead>
        <tbody id="leftBody"></tbody>
      </table>
    </div>
    <div class="schedule-scroll" id="scheduleScroll">
      <table id="scheduleTable" aria-label="Conference schedule">
        <thead><tr id="scheduleHeaderRow"></tr></thead>
        <tbody id="scheduleBody"></tbody>
      </table>
    </div>
    <div class="fixed-pane right-pane">
      <table aria-label="Projected finish and futures">
        <thead><tr id="rightHeaderRow"></tr></thead>
        <tbody id="rightBody"></tbody>
      </table>
    </div>
  </div>
  <div class="floating-table-header" id="floatingTableHeader" aria-hidden="true">
    <div class="floating-left"><table aria-hidden="true"><thead><tr id="floatingLeftHeaderRow"></tr></thead></table></div>
    <div class="floating-schedule" id="floatingScheduleViewport"><table id="floatingScheduleTable" aria-hidden="true"><thead><tr id="floatingScheduleHeaderRow"></tr></thead></table></div>
    <div class="floating-right"><table aria-hidden="true"><thead><tr id="floatingRightHeaderRow"></tr></thead></table></div>
  </div>
  <div class="range-key" aria-label="Projection color key">
    <span><i class="range-dot elite-win"></i>Dominant win (≥95% or +21)</span>
    <span><i class="range-dot strong-win"></i>Strong win (80–94% or +12)</span>
    <span><i class="range-dot lean-win"></i>Lean win (61–79% or +4)</span>
    <span><i class="range-dot toss"></i>Coin flip (40–60%)</span>
    <span><i class="range-dot lean-loss"></i>Lean loss (21–39% or −4)</span>
    <span><i class="range-dot strong-loss"></i>Strong loss (6–20% or −12)</span>
    <span><i class="range-dot elite-loss"></i>Dominant loss (≤5% or −21)</span>
    <span><i class="final-dot">✓</i>Final result</span>
  </div>
  <div class="note" id="pageNote"></div>
</div>

<div class="popover" id="gamePopover" role="dialog" aria-live="polite"></div>
<script id="conference-data" type="application/json">{payload_json}</script>
<script>
const DATA=JSON.parse(document.getElementById('conference-data').textContent);
const select=document.getElementById('conferenceSelect');
const leftHeaderRow=document.getElementById('leftHeaderRow');
const scheduleHeaderRow=document.getElementById('scheduleHeaderRow');
const rightHeaderRow=document.getElementById('rightHeaderRow');
const leftBody=document.getElementById('leftBody');
const scheduleBody=document.getElementById('scheduleBody');
const rightBody=document.getElementById('rightBody');
const scheduleScroll=document.getElementById('scheduleScroll');
const pop=document.getElementById('gamePopover');
const scheduleLayout=document.getElementById('scheduleLayout');
const scheduleTable=document.getElementById('scheduleTable');
const floatingTableHeader=document.getElementById('floatingTableHeader');
const floatingLeftHeaderRow=document.getElementById('floatingLeftHeaderRow');
const floatingScheduleHeaderRow=document.getElementById('floatingScheduleHeaderRow');
const floatingRightHeaderRow=document.getElementById('floatingRightHeaderRow');
const floatingScheduleTable=document.getElementById('floatingScheduleTable');
let activeConference=DATA.default_conference;
let sortState={{key:'projected_finish',dir:'asc'}};

const esc=s=>String(s??'—').replace(/[&<>'"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}}[c]));
const pct=v=>v==null?'—':`${{Math.round(Number(v)*100)}}%`;
const num=(v,d=1)=>v==null?'—':Number(v).toFixed(d);
const signed=v=>v==null?'—':`${{Number(v)>0?'+':''}}${{Number(v).toFixed(1)}}`;
const dlabel=v=>{{if(!v)return'TBD';const d=new Date(`${{String(v).slice(0,10)}}T12:00:00`);return d.toLocaleDateString(undefined,{{month:'short',day:'numeric'}})}};
const tone=(p,m,completed,teamScore,oppScore)=>{{
 if(completed&&teamScore!=null&&oppScore!=null)return Number(teamScore)>Number(oppScore)?'final-win':'final-loss';
 if(p==null)return'unknown';
 const prob=Number(p),margin=Number(m||0);
 // Symmetric probability bands around 50%. Margin can intensify a clear lean,
 // but never moves a 40–60% game out of the coin-flip band.
 if(prob>=.40 && prob<=.60)return'toss-up';
 if(prob>.60){{
   if(prob>=.95 || margin>=21)return'win-elite';
   if(prob>=.80 || margin>=12)return'win-strong';
   return'win-lean';
 }}
 if(prob<=.05 || margin<=-21)return'loss-elite';
 if(prob<=.20 || margin<=-12)return'loss-strong';
 return'loss-lean';
}};

function conf(){{return DATA.conferences.find(c=>c.conference===activeConference)||DATA.conferences[0]}}
function sortValue(row,key){{
 if(key==='team')return row.team||'';
 if(key==='conf_record')return (row.current_conf_wins??0)*100-(row.current_conf_losses??0);
 if(key==='projected_finish')return row.projected_finish??999;
 if(key==='make_title')return row.make_title_game_pct??-1;
 if(key==='win_title')return row.title_pct??-1;
 return 0;
}}
function compare(a,b){{const av=sortValue(a,sortState.key),bv=sortValue(b,sortState.key);let r=typeof av==='string'?av.localeCompare(bv):av-bv;return sortState.dir==='asc'?r:-r}}
function sortHeader(label,key,classes=''){{const active=sortState.key===key;return `<th class="sortable ${{classes}} ${{active?'sorted':''}}" data-sort="${{key}}">${{label}}<span class="sort-arrow">${{active?(sortState.dir==='asc'?'▲':'▼'):'↕'}}</span></th>`}}
function gameCell(g){{
 const darkLogos=new Set(['california','wake-forest','penn-state','iowa','michigan-state','navy','army','vanderbilt','baylor','colorado','purdue']); const lightClass=darkLogos.has(g.opponent_logo)?'light-logo':''; const logo=g.opponent_logo?`<img src="logos/${{esc(g.opponent_logo)}}.png" alt="${{esc(g.opponent)}} logo">`:'?';
 const rank=g.opponent_rank!=null&&Number(g.opponent_rank)<=25?`<span class="rank-badge">#${{Number(g.opponent_rank)}}</span>`:'';
 const data=encodeURIComponent(JSON.stringify(g));
 let projection;
 if(g.completed&&g.team_score!=null&&g.opponent_score!=null){{const won=Number(g.team_score)>Number(g.opponent_score);projection=`<span class="margin">${{won?'W':'L'}} ${{esc(g.team_score)}}–${{esc(g.opponent_score)}}</span><span class="probability">FINAL</span>`;}}
 else projection=`<span class="margin">${{signed(g.model_margin)}}</span><span class="probability">${{pct(g.win_probability)}}</span>`;
 return `<button class="schedule-cell ${{tone(g.win_probability,g.model_margin,g.completed,g.team_score,g.opponent_score)}}" data-game="${{data}}"><div class="cell-top"><span class="location">${{esc(g.location)}}</span>${{rank}}</div><div class="logo-wrap ${{lightClass}}">${{logo}}</div><div class="opponent-name">${{esc(g.opponent)}}</div><div class="projection">${{projection}}</div></button>`;
}}
function edgeClass(v){{if(v==null)return'';const n=Number(v);return n>=.03?'edge-pos':n<=-.03?'edge-neg':'edge-near'}}
function american(v){{if(v==null||v==='')return'—';const n=Number(v);return n>0?`+${{Math.round(n)}}`:`${{Math.round(n)}}`}}
function bookBadge(book,logo){{if(logo)return `<span class="sportsbook-logo-wrap" title="${{esc(book||'Sportsbook')}}"><img class="sportsbook-logo" src="${{esc(logo)}}" alt="${{esc(book||'Sportsbook')}}"></span>`;const key=String(book||'').toLowerCase();let code='SB',cls='book-generic';if(key.includes('fanduel')){{code='FD';cls='book-fd'}}else if(key.includes('draftkings')){{code='DK';cls='book-dk'}}else if(key.includes('betmgm')){{code='MGM';cls='book-mgm'}}else if(key.includes('caesars')){{code='C';cls='book-cz'}}else if(key.includes('hard rock')){{code='HR';cls='book-hr'}}else if(key.includes('bet365')){{code='365';cls='book-b365'}}return book?`<span class="book-icon ${{cls}}" title="${{esc(book)}}">${{code}}</span>`:''}}
function sosClass(rank,size){{
 if(rank==null||size==null||Number(size)<=0)return'sos-unknown';
 const r=Number(rank),n=Number(size);
 // Lower SOS rank = harder schedule (red); higher rank = easier schedule (green).
 if(r<=Math.ceil(n/3))return'sos-hard';
 if(r<=Math.ceil((2*n)/3))return'sos-mid';
 return'sos-easy';
}}
function sosText(rank,size){{return rank==null?'—':`#${{Number(rank)}} of ${{Number(size)}}`}}
function rowParts(row,currentWeek){{
 const scheduleCells=row.cells.map(c=>{{
   const weekClass=Number(c.week)===Number(currentWeek)?'current-week-cell':'';
   if(c.type==='conference')return `<td class="${{weekClass}}">${{gameCell(c)}}</td>`;
   if(c.type==='nonconference')return `<td class="${{weekClass}}"><div class="schedule-cell nonconf">NON-CONF<small>${{esc(c.opponent||'')}}</small></div></td>`;
   return `<td class="${{weekClass}}"><div class="schedule-cell bye">BYE</div></td>`;
 }}).join('');
 const confRecord=`${{Number(row.current_conf_wins||0)}}-${{Number(row.current_conf_losses||0)}}`;
 const futuresHref='futures.html';
 const bookMark=bookBadge(row.title_book,row.title_book_logo); const titleMarket=row.title_price!=null?`<span class="book-line"><span class="market-price">${{american(row.title_price)}}</span>${{bookMark}}</span><span class="market-edge ${{edgeClass(row.title_edge)}}">${{row.title_edge==null?'':`${{Number(row.title_edge)>=0?'+':''}}${{Math.round(Number(row.title_edge)*100)}}% edge`}}</span>`:'<span class="market-price">No market</span>';
 const confSosClass=sosClass(row.conf_sos_rank,row.conference_size),remSosClass=sosClass(row.remaining_sos_rank,row.conference_size);
 const left=`<tr><td class="team-column"><div class="team-name"><span class="team-logo-badge ${{row.dark_logo?'light-logo':''}}"><img src="logos/${{esc(row.slug)}}.png" alt="${{esc(row.team)}} logo"></span><div><strong class="team-primary">${{esc(row.team)}}</strong><span class="team-meta"><b class="${{esc(row.rank_tone)}}">#${{esc(row.rank)}}</b><span class="rating-value">| ${{num(row.rating)}}</span></span><span class="sos-lines"><span class="${{confSosClass}}">Conf SOS: ${{sosText(row.conf_sos_rank,row.conference_size)}}</span><span class="${{remSosClass}}">Rem SOS: ${{sosText(row.remaining_sos_rank,row.conference_size)}}</span></span></div></div></td><td class="record-column"><strong>${{confRecord}}</strong></td></tr>`;
 const schedule=`<tr>${{scheduleCells}}</tr>`;
 const right=`<tr><td class="proj-finish outcome"><span class="finish-rank">#${{esc(row.projected_finish)}}</span><span class="record">${{num(row.projected_conf_wins)}}–${{num(row.projected_conf_losses)}}</span></td><td class="make-title outcome"><a class="outcome-link" href="${{futuresHref}}"><span>${{pct(row.make_title_game_pct)}}</span><span class="futures-label">View futures</span></a></td><td class="win-title outcome title-prob"><a class="outcome-link" href="${{futuresHref}}"><span>${{pct(row.title_pct)}}</span>${{titleMarket}}</a></td></tr>`;
 return {{left,schedule,right}};
}}
function currentWeekFor(c){{const today=new Date();const dated=c.weeks.filter(w=>w.date).map(w=>({{...w,d:new Date(`${{String(w.date).slice(0,10)}}T12:00:00`)}})).sort((a,b)=>a.d-b.d);if(!dated.length)return null;const upcoming=dated.find(w=>w.d>=today);return (upcoming||dated[dated.length-1]).week}}
function scrollCurrentWeek(currentWeek,behavior='auto'){{
 const th=scheduleHeaderRow.querySelector('.current-week-header');
 if(!th)return;
 const target=Math.max(0,th.offsetLeft-(scheduleScroll.clientWidth-th.offsetWidth)/2);
 scheduleScroll.scrollTo({{left:target,behavior}});
}}
function syncFloatingHeaderContent(){{
 if(!floatingTableHeader)return;
 floatingLeftHeaderRow.innerHTML=leftHeaderRow.innerHTML;
 floatingScheduleHeaderRow.innerHTML=scheduleHeaderRow.innerHTML;
 floatingRightHeaderRow.innerHTML=rightHeaderRow.innerHTML;
 floatingScheduleTable.style.width=`${{scheduleTable.scrollWidth}}px`;
 syncFloatingHeaderScroll();
}}
function syncFloatingHeaderScroll(){{
 if(floatingScheduleTable)floatingScheduleTable.style.transform=`translateX(${{-scheduleScroll.scrollLeft}}px)`;
}}
function updateFloatingHeader(){{
 if(!floatingTableHeader||!scheduleLayout)return;
 const rect=scheduleLayout.getBoundingClientRect();
 const headerHeight=46;
 const visible=rect.top<0&&rect.bottom>headerHeight;
 floatingTableHeader.classList.toggle('visible',visible);
 floatingTableHeader.setAttribute('aria-hidden',visible?'false':'true');
 if(visible){{
  floatingTableHeader.style.left=`${{rect.left}}px`;
  floatingTableHeader.style.width=`${{rect.width}}px`;
  floatingTableHeader.style.gridTemplateColumns=`226px minmax(0,1fr) 254px`;
  syncFloatingHeaderScroll();
 }}
}}
function render(){{
 const c=conf();const currentWeek=currentWeekFor(c);document.getElementById('pageTitle').textContent=`${{c.conference}} Logo Schedule`;
 const currentMeta=c.weeks.find(w=>Number(w.week)===Number(currentWeek));document.getElementById('weekStatus').textContent=currentMeta?`Week ${{currentWeek}} · ${{dlabel(currentMeta.date)}}`:'';
 leftHeaderRow.innerHTML=sortHeader('Team','team','team-column')+sortHeader('Conf Record','conf_record','record-column');
 scheduleHeaderRow.innerHTML=c.weeks.map(w=>`<th class="week-header ${{Number(w.week)===Number(currentWeek)?'current-week-header':''}}"><strong>${{dlabel(w.date)}}</strong><small>W${{w.week}}</small></th>`).join('');
 rightHeaderRow.innerHTML=sortHeader('Proj Finish / Record','projected_finish','proj-finish')+sortHeader('Make Title','make_title','make-title')+sortHeader('Win Title','win_title','win-title');
 const parts=[...c.rows].sort(compare).map(row=>rowParts(row,currentWeek));
 leftBody.innerHTML=parts.map(p=>p.left).join('')||'<tr><td class="empty">No team data.</td></tr>';
 scheduleBody.innerHTML=parts.map(p=>p.schedule).join('')||'<tr><td class="empty">No conference schedule data available.</td></tr>';
 rightBody.innerHTML=parts.map(p=>p.right).join('')||'<tr><td class="empty">No projection data.</td></tr>';
 document.getElementById('pageNote').textContent=`${{c.rows.length}} teams · completed games show final scores · current week outlined · side columns remain visible while the schedule scrolls.`;
 document.querySelectorAll('[data-sort]').forEach(th=>th.onclick=()=>{{const key=th.dataset.sort;if(sortState.key===key)sortState.dir=sortState.dir==='asc'?'desc':'asc';else{{sortState.key=key;sortState.dir=key==='team'?'asc':key==='make_title'||key==='win_title'?'desc':'asc'}}render()}});
 document.querySelectorAll('[data-game]').forEach(btn=>btn.onclick=e=>openPopover(JSON.parse(decodeURIComponent(btn.dataset.game)),e.currentTarget));
 document.getElementById('thisWeekBtn').onclick=()=>scrollCurrentWeek(currentWeek,'smooth');
 requestAnimationFrame(()=>{{
   scrollCurrentWeek(currentWeek,'auto');
   syncFloatingHeaderContent();
   updateFloatingHeader();
 }});
}}
function openPopover(g,target){{
 pop.innerHTML=`<div class="popover-head"><div><h3>${{esc(g.team)}} ${{esc(g.location)}} ${{esc(g.opponent)}}</h3><div class="meta">${{dlabel(g.date)}} · Week ${{esc(g.week)}}</div></div><button class="close-popover" aria-label="Close">×</button></div><div class="popover-grid"><div class="popover-metric"><span>Model margin</span><b>${{signed(g.model_margin)}}</b></div><div class="popover-metric"><span>Win probability</span><b>${{pct(g.win_probability)}}</b></div><div class="popover-metric"><span>Market spread</span><b>${{signed(g.market_spread)}} ${{g.spread_book?`· ${{esc(g.spread_book)}}`:''}}</b></div><div class="popover-metric"><span>Spread edge</span><b>${{signed(g.spread_edge)}}</b></div><div class="popover-metric"><span>Model total</span><b>${{num(g.model_total)}}</b></div><div class="popover-metric"><span>Market total</span><b>${{num(g.market_total)}}</b></div></div><div class="popover-coach">${{esc(g.coach_summary)}}</div><a href="matchup.html?game_id=${{encodeURIComponent(g.game_id)}}">View full matchup →</a>`;
 pop.classList.add('open');const r=target.getBoundingClientRect(),pw=Math.min(340,window.innerWidth-24),left=Math.min(window.innerWidth-pw-12,Math.max(12,r.left+r.width/2-pw/2)),top=Math.min(window.innerHeight-pop.offsetHeight-12,r.bottom+8);pop.style.left=`${{left}}px`;pop.style.top=`${{Math.max(12,top)}}px`;pop.querySelector('.close-popover').onclick=closePopover;
}}
function closePopover(){{pop.classList.remove('open')}}
document.addEventListener('click',e=>{{if(pop.classList.contains('open')&&!pop.contains(e.target)&&!e.target.closest('[data-game]'))closePopover()}});
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closePopover()}});
function syncHealthPill(){{
 const host=document.getElementById('page-health-summary');
 const panel=document.getElementById('healthDetailsPanel');
 const dot=document.getElementById('healthDot');
 const label=document.getElementById('healthLabel');
 if(!host||!panel||!dot||!label)return;
 panel.innerHTML=host.innerHTML||'<div class="muted">Health details are loading…</div>';
 const text=(host.textContent||'').toLowerCase();
 dot.className='health-dot';
 if(text.includes('healthy')||text.includes('(green)')){{dot.classList.add('green');label.textContent='Data health: Green'}}
 else if(text.includes('warning')||text.includes('(yellow)')||text.includes('usable')){{dot.classList.add('yellow');label.textContent='Data health: Yellow'}}
 else if(text.includes('red')||text.includes('failed')||text.includes('unavailable')){{dot.classList.add('red');label.textContent='Data health: Red'}}
 else{{label.textContent='Data health'}}
}}
window.toggleConferenceHealth=function(event){{
 if(event){{event.preventDefault();event.stopPropagation()}}
 const wrap=document.getElementById('healthToggle');
 const button=document.getElementById('healthToggleButton');
 if(!wrap||!button)return false;
 syncHealthPill();
 const open=!wrap.classList.contains('open');
 wrap.classList.toggle('open',open);
 button.setAttribute('aria-expanded',open?'true':'false');
 return false;
}};
const healthHost=document.getElementById('page-health-summary');
const healthToggle=document.getElementById('healthToggle');
const healthToggleButton=document.getElementById('healthToggleButton');
if(healthToggleButton){{healthToggleButton.onclick=window.toggleConferenceHealth}}
document.addEventListener('click',e=>{{if(healthToggle&&healthToggle.classList.contains('open')&&!healthToggle.contains(e.target)){{healthToggle.classList.remove('open');if(healthToggleButton)healthToggleButton.setAttribute('aria-expanded','false')}}}});
if(healthHost){{new MutationObserver(syncHealthPill).observe(healthHost,{{childList:true,subtree:true,characterData:true,attributes:true}});setTimeout(syncHealthPill,250);setTimeout(syncHealthPill,1200)}}
scheduleScroll.addEventListener('scroll',syncFloatingHeaderScroll,{{passive:true}});
window.addEventListener('scroll',updateFloatingHeader,{{passive:true}});
window.addEventListener('resize',()=>{{syncFloatingHeaderContent();updateFloatingHeader()}});
DATA.conferences.forEach(c=>select.add(new Option(c.conference,c.conference)));select.value=activeConference;select.onchange=()=>{{activeConference=select.value;sortState={{key:'projected_finish',dir:'asc'}};closePopover();render()}};render();
requestAnimationFrame(()=>{{syncFloatingHeaderContent();updateFloatingHeader()}});
</script>
</body>
</html>
"""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(page)
    (ROOT / "conferences.html").write_text(page)
    print(f"Wrote: {OUT_FILE}")
    print(f"Synced: {ROOT / 'conferences.html'}")
    print(f"Conferences: {len(payload['conferences'])}")
    print(
        "Teams:",
        sum(len(conference.get("rows", [])) for conference in payload["conferences"]),
    )


if __name__ == "__main__":
    main()
