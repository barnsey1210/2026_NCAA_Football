#!/usr/bin/env python3
"""Build an isolated ACC conference logo-schedule prototype."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "build" / "conference_logo_schedule_preview"
OUT_FILE = OUT_DIR / "index.html"

CONF_PATH = ROOT / "data" / "site" / "conference_workspace.json"
MATCHUPS_PATH = ROOT / "data" / "site" / "matchups_view.json"

PREVIEW_CONFERENCE = "ACC"
SEASON_WEEKS = list(range(0, 15))


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
    team_side = teams.get("home" if is_home else "away", {})

    home_spread = model.get("home_spread")
    home_win_probability = model.get("home_win_probability")

    # home_spread is negative when the home team is favored.
    # Convert to expected team margin from this team's perspective.
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

    market_home_line = (
        market.get("spread", {}).get("home_line")
        if isinstance(market.get("spread"), dict)
        else None
    )

    team_market_line = None
    if market_home_line is not None:
        team_market_line = (
            float(market_home_line)
            if is_home
            else -float(market_home_line)
        )

    spread_edge = None
    if team_margin is not None and team_market_line is not None:
        # Positive = model is more favorable to this team than the market.
        spread_edge = team_margin + team_market_line

    coaches = matchup.get("coaches") or []
    team_coach = next(
        (coach for coach in coaches if coach.get("team") == team),
        None,
    )

    location = "N" if neutral else ("H" if is_home else "@")

    return {
        "game_id": game.get("game_id"),
        "week": game.get("week"),
        "date": game.get("date"),
        "team": team,
        "opponent": opponent,
        "location": location,
        "opponent_logo": opponent_side.get("logo_slug"),
        "opponent_rank": opponent_side.get("overall_rank"),
        "team_rank": team_side.get("overall_rank"),
        "model_margin": team_margin,
        "win_probability": team_win_probability,
        "model_total": model.get("total"),
        "market_spread": team_market_line,
        "market_total": (
            market.get("total", {}).get("line")
            if isinstance(market.get("total"), dict)
            else None
        ),
        "spread_book": (
            market.get("spread", {}).get("book")
            if isinstance(market.get("spread"), dict)
            else None
        ),
        "spread_edge": spread_edge,
        "coach": team_coach,
        "completed": bool(game.get("completed")),
        "team_score": game.get("home_score") if is_home else game.get("away_score"),
        "opponent_score": game.get("away_score") if is_home else game.get("home_score"),
    }


def coach_summary(coach: dict[str, Any] | None) -> str:
    if not coach:
        return "Coach betting context unavailable"

    periods = coach.get("periods") or []
    full_game = next(
        (
            period
            for period in periods
            if isinstance(period, dict)
            and period.get("period") == "full_game"
        ),
        None,
    )

    coach_name = coach.get("coach") or "Coach"
    if not full_game or not full_game.get("ats_record"):
        return f"{coach_name}: no matched full-game ATS sample"

    return (
        f"{coach_name}: {full_game.get('ats_record')} ATS, "
        f"avg margin {number(full_game.get('ats_margin'), 1)}"
    )


def game_cell(game: dict[str, Any]) -> str:
    logo_slug = game.get("opponent_logo")
    logo = (
        f'<img src="../../logos/{esc(logo_slug)}.png" '
        f'alt="{esc(game.get("opponent"))} logo">'
        if logo_slug
        else '<div class="logo-fallback">?</div>'
    )

    opponent_rank = game.get("opponent_rank")
    rank_badge = (
        f'<span class="rank-badge">#{int(opponent_rank)}</span>'
        if opponent_rank is not None and int(opponent_rank) <= 25
        else ""
    )

    probability = game.get("win_probability")
    color_class = health_class(probability)

    matchup_url = (
        f'../matchup.html?game={esc(game.get("game_id"))}'
        if game.get("game_id")
        else "#"
    )

    tooltip_lines = [
        f'{game.get("team")} vs {game.get("opponent")}',
        f'Date: {game.get("date")}',
        f'Location: {game.get("location")}',
        f'Model margin: {signed(game.get("model_margin"))}',
        f'Win probability: {pct(game.get("win_probability"))}',
        f'Market line: {signed(game.get("market_spread"))}',
        f'Spread edge: {signed(game.get("spread_edge"))}',
        f'Model total: {number(game.get("model_total"))}',
        f'Market total: {number(game.get("market_total"))}',
        coach_summary(game.get("coach")),
    ]

    tooltip = "&#10;".join(esc(line) for line in tooltip_lines)

    if game.get("completed"):
        result = (
            f'{game.get("team_score")}–{game.get("opponent_score")}'
            if game.get("team_score") is not None
            else "FINAL"
        )
        primary = f'<span class="final-score">{esc(result)}</span>'
    else:
        primary = (
            f'<span class="margin">{signed(game.get("model_margin"))}</span>'
            f'<span class="probability">{pct(game.get("win_probability"))}</span>'
        )

    return f"""
    <a class="schedule-cell {color_class}"
       href="{matchup_url}"
       title="{tooltip}"
       aria-label="{esc(game.get("team"))} {esc(game.get("location"))}
                   {esc(game.get("opponent"))};
                   model margin {signed(game.get("model_margin"))};
                   win probability {pct(game.get("win_probability"))}">
      <div class="cell-top">
        <span class="location">{esc(game.get("location"))}</span>
        {rank_badge}
      </div>
      <div class="logo-wrap">{logo}</div>
      <div class="opponent-name">{esc(game.get("opponent"))}</div>
      <div class="projection">{primary}</div>
    </a>
    """


def render_team_row(
    team: dict[str, Any],
    schedule: dict[int, dict[str, Any]],
    all_games_by_week: dict[int, bool],
) -> str:
    week_cells = []

    for week in SEASON_WEEKS:
        conf_game = schedule.get(week)

        if conf_game:
            week_cells.append(f"<td>{game_cell(conf_game)}</td>")
        elif all_games_by_week.get(week):
            week_cells.append(
                '<td><div class="schedule-cell nonconf" '
                'aria-label="Nonconference game omitted">—</div></td>'
            )
        else:
            week_cells.append(
                '<td><div class="schedule-cell bye" '
                'aria-label="Bye week">BYE</div></td>'
            )

    projected_record = (
        f'{number(team.get("projected_conf_wins"))}–'
        f'{number(team.get("projected_conf_losses"))}'
    )

    return f"""
    <tr>
      <td class="sticky-left team-column">
        <div class="team-name">
          <img src="../../logos/{esc(team.get("slug"))}.png"
               alt="{esc(team.get("team"))} logo">
          <div>
            <strong>{esc(team.get("team"))}</strong>
            <span>#{esc(team.get("rank"))} overall</span>
          </div>
        </div>
      </td>
      <td class="sticky-left rating-column">
        <strong>{number(team.get("rating"))}</strong>
        <span>#{esc(team.get("rank"))}</span>
      </td>
      {''.join(week_cells)}
      <td class="outcome projected-record">{projected_record}</td>
      <td class="outcome finish">#{esc(team.get("projected_finish"))}</td>
      <td class="outcome">{pct(team.get("make_title_game_pct"))}</td>
      <td class="outcome title-prob">{pct(team.get("title_pct"))}</td>
    </tr>
    """


def main() -> None:
    conference_data = load_json(CONF_PATH)
    matchup_data = load_json(MATCHUPS_PATH)

    conference = next(
        (
            item
            for item in conference_data["conferences"]
            if item["conference"] == PREVIEW_CONFERENCE
        ),
        None,
    )
    if not conference:
        raise SystemExit(f"Conference not found: {PREVIEW_CONFERENCE}")

    conference_teams = {team["team"] for team in conference["teams"]}

    conference_schedules: dict[str, dict[int, dict[str, Any]]] = {
        team: {} for team in conference_teams
    }
    all_games: dict[str, dict[int, bool]] = {
        team: {} for team in conference_teams
    }

    for row in matchup_data["games"]:
        game = row.get("game", {})
        away = game.get("away_team")
        home = game.get("home_team")
        week = game.get("week")

        if week is None:
            continue

        for team in (away, home):
            if team in conference_teams:
                all_games[team][int(week)] = True

        # Conference-only inclusion: both teams must be members.
        if away not in conference_teams or home not in conference_teams:
            continue

        conference_schedules[away][int(week)] = game_for_team(row, away)
        conference_schedules[home][int(week)] = game_for_team(row, home)

    rows = []
    for team in conference["teams"]:
        rows.append(
            render_team_row(
                team,
                conference_schedules[team["team"]],
                all_games[team["team"]],
            )
        )

    week_headers = "".join(
        f"<th class='week-header'>W{week}</th>" for week in SEASON_WEEKS
    )

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(PREVIEW_CONFERENCE)} Logo Schedule Preview</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #07101d;
  --panel: #0d1726;
  --panel-2: #111e30;
  --line: #243247;
  --text: #edf4ff;
  --muted: #8fa0b7;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
               "Segoe UI", sans-serif;
}}
.page {{
  padding: 18px;
}}
.header {{
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: end;
  margin-bottom: 14px;
}}
h1 {{
  margin: 0;
  font-size: 25px;
}}
.subtitle {{
  color: var(--muted);
  margin-top: 5px;
  font-size: 13px;
}}
.legend {{
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--muted);
}}
.legend span {{
  padding: 5px 8px;
  border-radius: 6px;
  border: 1px solid var(--line);
}}
.table-shell {{
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--panel);
}}
table {{
  border-collapse: separate;
  border-spacing: 0;
  min-width: 1780px;
  width: 100%;
}}
th, td {{
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  padding: 4px;
  vertical-align: middle;
  text-align: center;
}}
th {{
  position: sticky;
  top: 0;
  z-index: 5;
  background: #101c2c;
  color: var(--muted);
  font-size: 10px;
  letter-spacing: .07em;
  text-transform: uppercase;
}}
tbody tr:hover td {{
  background-color: rgba(255,255,255,.025);
}}
.sticky-left {{
  position: sticky;
  z-index: 4;
  background: var(--panel);
}}
.team-column {{
  left: 0;
  width: 180px;
  min-width: 180px;
  text-align: left;
}}
.rating-column {{
  left: 180px;
  width: 68px;
  min-width: 68px;
}}
.rating-column span,
.team-name span {{
  display: block;
  color: var(--muted);
  font-size: 10px;
}}
.team-name {{
  display: flex;
  align-items: center;
  gap: 8px;
}}
.team-name img {{
  width: 30px;
  height: 30px;
  object-fit: contain;
}}
.week-header {{
  width: 83px;
  min-width: 83px;
}}
.schedule-cell {{
  width: 75px;
  min-height: 88px;
  border-radius: 7px;
  padding: 5px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  text-decoration: none;
  color: var(--text);
  border: 1px solid rgba(255,255,255,.08);
}}
.cell-top {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 14px;
}}
.location {{
  font-weight: 800;
  font-size: 10px;
}}
.rank-badge {{
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 5px;
  background: #e6bd50;
  color: #111;
  font-weight: 800;
}}
.logo-wrap {{
  height: 30px;
  display: grid;
  place-items: center;
}}
.logo-wrap img {{
  width: 28px;
  height: 28px;
  object-fit: contain;
}}
.opponent-name {{
  font-size: 8px;
  line-height: 1.05;
  color: rgba(255,255,255,.86);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}}
.projection {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 4px;
}}
.margin {{
  font-size: 12px;
  font-weight: 800;
}}
.probability {{
  font-size: 10px;
  font-weight: 700;
}}
.strong-win {{ background: #0b5f3d; }}
.lean-win {{ background: #1c5742; }}
.coin-flip {{ background: #394557; }}
.lean-loss {{ background: #714a27; }}
.strong-loss {{ background: #702d32; }}
.unknown {{ background: #293342; }}
.bye,
.nonconf {{
  justify-content: center;
  align-items: center;
  color: #718197;
  background: #151f2d;
  font-size: 10px;
  font-weight: 800;
}}
.nonconf {{
  color: #455368;
}}
.outcome {{
  width: 92px;
  min-width: 92px;
  font-weight: 800;
  background: var(--panel-2);
}}
.projected-record {{
  width: 108px;
  min-width: 108px;
}}
.finish {{
  width: 78px;
  min-width: 78px;
  font-size: 16px;
}}
.title-prob {{
  color: #79e9b4;
}}
.note {{
  color: var(--muted);
  font-size: 11px;
  margin-top: 10px;
}}
@media (max-width: 700px) {{
  .page {{ padding: 10px; }}
  .header {{ display: block; }}
  .legend {{ margin-top: 10px; }}
  .team-column {{
    width: 145px;
    min-width: 145px;
  }}
  .rating-column {{
    left: 145px;
  }}
}}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div>
      <h1>{esc(PREVIEW_CONFERENCE)} Logo Schedule</h1>
      <div class="subtitle">
        Conference games only · BYE weeks shown · model margin and win probability
      </div>
    </div>
    <div class="legend" aria-label="Win probability legend">
      <span>Dark green ≥80%</span>
      <span>Green 62–79%</span>
      <span>Slate 45–61%</span>
      <span>Amber 25–44%</span>
      <span>Red &lt;25%</span>
    </div>
  </div>

  <div class="table-shell">
    <table>
      <thead>
        <tr>
          <th class="sticky-left team-column">Team</th>
          <th class="sticky-left rating-column">Rating</th>
          {week_headers}
          <th>Proj Conf</th>
          <th>Finish</th>
          <th>Make Title</th>
          <th>Win Title</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>

  <div class="note">
    Muted dashes represent omitted nonconference games. BYE means the team has
    no scheduled game that week. Hover a conference game for model, market, and
    coaching context.
  </div>
</div>
</body>
</html>
"""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(page)
    print(f"Wrote: {OUT_FILE}")
    print(f"Conference teams: {len(conference['teams'])}")
    print(
        "Conference games represented:",
        sum(len(schedule) for schedule in conference_schedules.values()) // 2,
    )


if __name__ == "__main__":
    main()