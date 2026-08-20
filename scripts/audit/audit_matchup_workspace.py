#!/usr/bin/env python3
"""Focused regression checks for the shared Scheduled Game Workspace."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / "matchup_workspace.js").read_text()
DATA = json.loads((ROOT / "data/site/matchups_view.json").read_text())


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def role(team, game):
    spread = game["model"].get("home_spread")
    if spread is None or abs(float(spread)) < .05:
        return "Pick'em"
    home = team["team"] == game["game"]["home_team"]
    return "Favorite" if (home and spread < 0) or (not home and spread > 0) else "Underdog"


def main():
    compact_js = re.sub(r"\s+", "", JS)

    # The shared workspace exposes rankClass through its test hook. Validate the
    # classes and thresholds directly without trying to parse a JavaScript
    # function body with a fragile regular expression.
    require("mwRankGood" in JS, "green rank class missing")
    require("mwRankGoodWarn" in JS, "green-yellow rank class missing")
    require("mwRankWarn" in JS, "yellow rank class missing")
    require("mwRankWarnBad" in JS, "yellow-red rank class missing")
    require("mwRankBad" in JS, "red rank class missing")
    require("mwRankMissing" in JS, "missing-rank class missing")
    require("n<=28" in compact_js, "green rank threshold must remain 28")
    require("n<=55" in compact_js, "green-yellow rank threshold must remain 55")
    require("n<=83" in compact_js, "yellow rank threshold must remain 83")
    require("n<=110" in compact_js, "yellow-red rank threshold must remain 110")
    require("__matchupWorkspaceTest={rankClass" in compact_js,
            "rankClass test hook missing")
    require(
        re.search(r"minimum\s*=\s*period\s*===\s*['\"]Full Game['\"]\s*\?\s*25\s*:\s*12", JS),
        "canonical coach sample thresholds (25 full game / 12 halves) missing",
    )
    require(
        re.search(r"games\s*>=\s*minimum", JS),
        "coach sample threshold is defined but not enforced",
    )
    require("Opposing coach poor ${period} ATS" in JS,
            "negative coach direction must support the opponent")
    require("Supports ${opp.team}" in JS, "negative coach evidence must name supported side")
    require("overall_rank_gap" not in JS, "generic overall-rating-gap context still present")
    require("opening_possession_1h" in JS and "receive vs defer" in JS,
            "opening-possession receive/defer context missing")
    require("staff_continuity" in JS and "Number(game.game.week)<=4" in JS,
            "staff-continuity context or early-season gate missing")
    require("Number(game.game.week)>=3" in JS and "competition_context" in JS,
            "Week 3 competition step-up/down context missing")
    require("mwSpotValue" in JS and "b2b,bye,look,travel" in compact_js,
            "deterministic schedule-spot rendering missing")
    require("'Yes':'No'" in JS and "'Watch':'No'" in JS,
            "schedule-spot Yes/No/Watch states missing")
    require(
        "cutoff.setDate(cutoff.getDate()-7)" in JS
        and "daily.filter" in JS
        and ".reverse()" in JS,
        "line history must use rolling seven-day window and display newest snapshots first",
    )
    require("Opening ATS line:" in JS and "Opening O/U:" in JS,
            "opening ATS/O-U lines missing from line-history header")
    require("NCAAFMatchupContextSummaryFromText" in JS,
            "Openers row-text context summary export is missing")
    require("NCAAFMatchupContextSummary" in JS,
            "Openers cannot consume the matchup qualifying-context summary")
    require("constrpCandidates=(game.angles||[])" in compact_js,
            "historical RP study is not consumed by matchup betting context")
    require("id:'rp_study_signal'" in compact_js and "historical_ats_record" in compact_js,
            "historical RP study context evidence is missing")
    require("Line history — ATS spread and O/U total" in JS,
            "permanently visible ATS/O-U line-history section missing")
    require("<th>Book</th>" in JS and "<th>Total move</th>" in JS,
            "line-history sportsbook source or Total move column missing")
    require("advancedTable" not in JS and "mwMissing" not in JS,
            "obsolete advanced-metric notice/renderer still present")
    require(JS.count("new MutationObserver(decorateLinks)") == 1,
            "shared link observer duplicated")

    negative = []
    for game in DATA["games"]:
        for side in ("away", "home"):
            team = game["teams"][side]
            expected_role = role(team, game)
            coach = next((x for x in game["matchup"].get("coaches", [])
                          if x.get("team") == team["team"]), {})
            split = next((x for x in coach.get("role_splits", [])
                          if x.get("role") == expected_role and x.get("period") == "Full Game"), {})
            if (split.get("games") or 0) >= 20 and (split.get("ats_pct") or 1) <= .46 \
                    and (split.get("ats_margin") or 0) <= -1.5:
                other = game["teams"]["home" if side == "away" else "away"]["team"]
                negative.append((game["game"]["game_id"], team["team"], other,
                                 split.get("ats_record"), expected_role))
    require(negative, "no negative coach-role fixture available for directionality validation")

    weeks = {int(g["game"].get("week", -1)) for g in DATA["games"]}
    require(any(w <= 3 for w in weeks) and any(w >= 4 for w in weeks),
            "payload lacks both early- and later-week fixtures")
    require(any(g["teams"]["away"].get("staff_continuity") or g["teams"]["home"].get("staff_continuity") for g in DATA["games"]),
            "payload has no staff-continuity records")
    require(all("competition_context" in g["teams"][side] for g in DATA["games"] for side in ("away", "home")),
            "competition context missing from team payload")
    require(all("opening_possession" in g["matchup"] for g in DATA["games"]),
            "opening-possession object missing from matchup payload")
    market = next(g for g in DATA["games"] if g["market"].get("spread", {}).get("home_line") is not None)
    incomplete = next(g for g in DATA["games"] if g["market"].get("spread", {}).get("home_line") is None)

    print("PASS: shared matchup workspace regression audit")
    print(f"games checked: {len(DATA['games'])}")
    print(f"negative coach fixtures: {len(negative)}; example={negative[0]}")
    print(f"market fixture: {market['game']['game_id']}")
    print(f"incomplete-market fixture: {incomplete['game']['game_id']}")


if __name__ == "__main__":
    main()
