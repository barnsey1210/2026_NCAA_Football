#!/usr/bin/env python3
"""Run the 2026-27 12-team CFP model from the canonical preseason JSON DB.

Project access/seeding policy encoded here:
* ACC, Big Ten, Big 12 and SEC champions qualify.
* Exactly one G6 team qualifies: the highest-ranked champion from
  American/CUSA/MAC/MW/PAC12/Sun Belt.
* The G6 qualifier is always seeded No. 12.
* The next seven highest-ranked eligible teams qualify at large.
* Non-champion G6 teams are excluded from at-large selection.
* Seeds follow modeled committee rank; seeds 1-4 receive byes.
* The bracket is fixed: 5/12 -> 4, 6/11 -> 3, 7/10 -> 2, 8/9 -> 1.

The selection committee ranking itself is necessarily a model.  The proxy combines
simulated record, production power rating, schedule strength and small ranking noise.
All assumptions are written to DB.playoff_model.metadata.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/snapshots/preseason/preseason_db.json"

# Project-wide fixed home-field advantage.
FIXED_HFA = 2.6

# Canonical 2026 Game Projection Consensus win-probability model.
WIN_PROB_LOGISTIC_SCALE = 6.5
WIN_PROB_MODEL_VERSION = "logistic_margin_scale_6_5_v1"
POWER_CONFS = {"ACC", "B1G", "B12", "SEC"}
G6_CONFS = {"American", "CUSA", "MAC", "MW", "PAC12", "Sun Belt"}
RESUME_WEIGHTS = {
    # Mean leave-one-season-out weights from the best prospective 2021-24
    # variant. Inputs are converted to within-simulation percentiles first.
    "game_control": 0.055,
    "quality_wins": 0.120,
    "top25_wins": 0.111,
    "losses": 0.553,
    "bad_losses": 0.065,
    "avg_capped_mov": 0.069,
    "avg_weighted_mol": 0.027,
    "power_championship_bonus": 8.0,
    "g6_championship_bonus": 5.0,
}

OFFICIAL_CFP_2026 = ROOT / "data/models/cfp_rankings_official_2026.csv"


def load_official_cfp_top25() -> tuple[set[str], str]:
    """Return the latest published CFP Top 25; never substitute a model ranking."""
    if not OFFICIAL_CFP_2026.exists():
        return set(), "unavailable_pre_first_cfp_release"
    rows = list(csv.DictReader(OFFICIAL_CFP_2026.open(encoding="utf-8")))
    if not rows:
        return set(), "official_file_empty"
    latest = max(str(r.get("ranking_date") or r.get("date") or "") for r in rows)
    teams = {str(r.get("team")) for r in rows
             if str(r.get("ranking_date") or r.get("date") or "") == latest and fnum(r.get("rank"), 999) <= 25}
    return teams, f"official_cfp_top25_{latest}"


def load_conf_module():
    path = ROOT / "rerun_conference_sims_2026.py"
    spec = importlib.util.spec_from_file_location("conference_sim_2026", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


CONF = load_conf_module()


def load_played_game_control() -> Dict[Tuple[str, str], float]:
    path = ROOT / "data/research/game_control_history_2026/team_game_game_control.csv"
    values = {}
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                values[(str(row.get("game_id")), str(row.get("team")))] = fnum(row.get("raw_game_control"), 0.5)
    return values


def fnum(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def schedule_strength(games: List[dict], teams: Dict[str, dict]) -> Dict[str, float]:
    opponents: Dict[str, List[float]] = defaultdict(list)
    for g in games:
        away, home = g.get("away_team"), g.get("home_team")
        if away in teams and home in teams:
            opponents[away].append(CONF.team_rating(teams[home]))
            opponents[home].append(CONF.team_rating(teams[away]))
    return {team: sum(vals) / len(vals) if vals else 0.0 for team, vals in opponents.items()}


def percentile_scores(metrics: Dict[str, Dict[str, float]], key: str, negative: bool = False) -> Dict[str, float]:
    """Average-tie percentiles matching the historical validation pipeline."""
    ordered = sorted((float(row[key]), team) for team, row in metrics.items())
    out, n, i = {}, len(ordered), 0
    while i < n:
        j = i + 1
        while j < n and ordered[j][0] == ordered[i][0]:
            j += 1
        pct = ((i + 1 + j) / 2) / n
        if negative:
            pct = 1.0 - pct
        for _, team in ordered[i:j]:
            out[team] = pct
        i = j
    return out


def apply_validated_resume_score(metrics: Dict[str, Dict[str, float]]) -> None:
    negative = {"losses", "bad_losses", "avg_weighted_mol"}
    features = ["game_control", "quality_wins", "top25_wins", "losses", "bad_losses", "avg_capped_mov", "avg_weighted_mol"]
    pct = {key: percentile_scores(metrics, key, key in negative) for key in features}
    for team, row in metrics.items():
        score = 100.0 * sum(RESUME_WEIGHTS[key] * pct[key][team] for key in features)
        score += RESUME_WEIGHTS["power_championship_bonus"] * row["power_championship_wins"]
        score += RESUME_WEIGHTS["g6_championship_bonus"] * row["g6_championship_wins"]
        row["resume_score"] = score


def canonical_win_prob_from_margin(margin: float) -> float:
    """Canonical production margin -> straight-up win probability."""
    p = 1.0 / (1.0 + math.exp(-float(margin) / WIN_PROB_LOGISTIC_SCALE))
    return max(0.001, min(0.999, p))


def simulated_margin_with_canonical_winner(
    expected_margin: float,
    win_prob_positive_side: float,
    rng: random.Random,
    sigma: float,
) -> float:
    """Choose the winner from the canonical probability model.

    Preserve the legacy Normal sigma only for simulated margin magnitude,
    because CFP resume metrics were validated with that margin framework.
    Sigma no longer determines the straight-up winner probability.
    """
    positive_side_wins = rng.random() < win_prob_positive_side
    raw_margin = rng.gauss(float(expected_margin), sigma)
    magnitude = max(0.01, abs(raw_margin))
    return magnitude if positive_side_wins else -magnitude


def game_winner(a: str, b: str, teams: Dict[str, dict], rng: random.Random, sigma: float, home: str | None = None) -> str:
    ta, tb = teams[a], teams[b]
    margin_b = CONF.team_rating(tb) - CONF.team_rating(ta)

    if home == b:
        margin_b += FIXED_HFA
    elif home == a:
        margin_b -= FIXED_HFA

    p_b = canonical_win_prob_from_margin(margin_b)
    return b if rng.random() < p_b else a


def select_field(
    ranked: List[str],
    champs: Dict[str, str],
    teams: Dict[str, dict],
) -> Tuple[List[str], set]:
    """Select a 12-team field with exactly one G6 participant at seed 12.

    Four power-conference champions receive automatic bids. The highest-ranked
    G6 champion receives the fifth automatic bid. All other G6 teams are
    excluded from at-large consideration. Seeds 1-11 follow modeled committee
    rank among the selected non-G6 teams, and the G6 qualifier is always seed 12.
    """
    power_auto = {champs[c] for c in POWER_CONFS if c in champs}
    g6_candidates = {champs[c] for c in G6_CONFS if c in champs}
    rank_index = {team: i for i, team in enumerate(ranked)}
    g6_auto = min(g6_candidates, key=lambda t: rank_index.get(t, 9999)) if g6_candidates else None
    auto = power_auto | ({g6_auto} if g6_auto else set())

    def is_g6(team: str) -> bool:
        return CONF.norm_conf(teams.get(team, {}).get("conference")) in G6_CONFS

    # Seven at-large teams, excluding all G6 teams except the selected auto bid.
    at_large = [
        team
        for team in ranked
        if team not in auto and not is_g6(team)
    ][:7]

    # Seeds 1-11: power-conference autos plus the seven at-large teams,
    # ordered by modeled committee rank.
    non_g6_field = power_auto | set(at_large)
    field = [team for team in ranked if team in non_g6_field]

    # Defensive inclusion of any low-ranked power automatic qualifier.
    for team in sorted(power_auto, key=lambda x: rank_index.get(x, 9999)):
        if team not in field:
            field.append(team)

    # Fill to 11 non-G6 teams if a conference auto is missing for any reason.
    field = field[:11]
    if len(field) < 11:
        for team in ranked:
            if team in field or team == g6_auto or is_g6(team):
                continue
            field.append(team)
            if len(field) == 11:
                break

    if g6_auto is None:
        raise RuntimeError("CFP field invariant failed: no eligible G6 champion found")

    # Project policy: G6 automatic qualifier is always the No. 12 seed.
    field.append(g6_auto)

    g6_field = [team for team in field if is_g6(team)]
    if len(field) != 12:
        raise RuntimeError(
            f"CFP field invariant failed: expected 12 teams, got {len(field)}"
        )
    if len(g6_field) != 1:
        raise RuntimeError(
            f"CFP field invariant failed: expected exactly one G6 team, got "
            f"{len(g6_field)} ({g6_field})"
        )
    if field[11] != g6_auto:
        raise RuntimeError(
            f"CFP seeding invariant failed: G6 qualifier is not seed 12 "
            f"({g6_auto=}, seed12={field[11]})"
        )

    return field, auto


def simulate_bracket(field: List[str], teams: Dict[str, dict], rng: random.Random, sigma: float, counters: dict):
    seeded = {i + 1: team for i, team in enumerate(field)}
    for seed, team in seeded.items():
        counters["seed"][team][seed] += 1
        if seed <= 4:
            counters["bye"][team] += 1
            counters["quarterfinal"][team] += 1

    first_round_pairs = [(5, 12, 4), (6, 11, 3), (7, 10, 2), (8, 9, 1)]
    quarters = []
    for high, low, bye_seed in first_round_pairs:
        winner = game_winner(seeded[low], seeded[high], teams, rng, sigma, home=seeded[high])
        counters["quarterfinal"][winner] += 1
        quarters.append((winner, seeded[bye_seed]))

    semifinalists = []
    for first_round_winner, bye_team in quarters:
        winner = game_winner(first_round_winner, bye_team, teams, rng, sigma)
        counters["semifinal"][winner] += 1
        semifinalists.append(winner)

    finalists = []
    for a, b in [(semifinalists[0], semifinalists[3]), (semifinalists[1], semifinalists[2])]:
        winner = game_winner(a, b, teams, rng, sigma)
        counters["title_game"][winner] += 1
        finalists.append(winner)
    champion = game_winner(finalists[0], finalists[1], teams, rng, sigma)
    counters["champion"][champion] += 1


def run_model(db: dict, sims: int, seed: int, sigma: float) -> dict:
    rng = random.Random(seed)
    teams = {t["team"]: t for t in db.get("teams", [])}
    games = CONF.build_regular_games(db)
    played_game_control = load_played_game_control()
    official_top25, official_top25_status = load_official_cfp_top25()
    game_counts = Counter()
    conf_games: Dict[str, List[dict]] = defaultdict(list)
    conf_teams: Dict[str, List[str]] = defaultdict(list)
    for team, row in teams.items():
        conf = CONF.norm_conf(row.get("conference"))
        if conf and conf != "Independent":
            conf_teams[conf].append(team)
    for g in games:
        game_counts[g.get("away_team")] += 1
        game_counts[g.get("home_team")] += 1
        ac, hc = CONF.norm_conf(g.get("away_conference")), CONF.norm_conf(g.get("home_conference"))
        if g.get("is_conference_game") and ac == hc:
            conf_games[ac].append(g)

    title_rules = CONF.load_eligibility_rules(ROOT / "conference_eligibility_rules_2026.csv")
    game_probs = [(g, CONF.game_home_prob(g, teams, sigma)) for g in games]
    metric_names = [
        "game_control", "power_championship_wins", "g6_championship_wins", "quality_wins",
        "top25_wins", "losses", "avg_capped_mov", "avg_weighted_mol", "bad_losses",
        "sos", "resume_score",
    ]
    metric_sums = {name: Counter() for name in metric_names}
    rank_sums, top25_count = Counter(), Counter()
    counters = {
        "playoff": Counter(), "auto": Counter(), "bye": Counter(),
        "quarterfinal": Counter(), "semifinal": Counter(), "title_game": Counter(),
        "champion": Counter(), "seed": defaultdict(Counter), "field": Counter(),
    }

    for _ in range(sims):
        wins, losses, conf_wins = Counter(), Counter(), Counter()
        results, played = {}, []
        opponents, sos_opponents = defaultdict(list), defaultdict(list)
        defeated, lost_to = defaultdict(list), defaultdict(list)
        mov_values, mol_values, raw_game_control = defaultdict(list), defaultdict(list), defaultdict(list)
        for g, p_home in game_probs:
            away, home = g.get("away_team"), g.get("home_team")
            if g.get("cfbd_completed") and g.get("away_score") is not None and g.get("home_score") is not None:
                margin_home = fnum(g.get("home_score")) - fnum(g.get("away_score"))
            else:
                expected = g.get("projected_margin_home")
                if expected is None:
                    expected = CONF.estimate_margin_home(
                        teams[home],
                        teams[away],
                        bool(g.get("neutral_site")),
                    )

                # game_probs is sourced from CONF.game_home_prob(), which uses
                # the canonical logistic /6.5 probability for consensus games.
                margin_home = simulated_margin_with_canonical_winner(
                    fnum(expected),
                    p_home,
                    rng,
                    sigma,
                )
            winner, loser = (home, away) if margin_home > 0 else (away, home)
            margin = abs(margin_home)
            wins[winner] += 1
            losses[loser] += 1
            results[(away, home)] = winner
            opponents[away].append(home); opponents[home].append(away)
            venue = 0.0 if g.get("neutral_site") else 0.025
            sos_opponents[away].append((home, venue)); sos_opponents[home].append((away, -venue))
            defeated[winner].append(loser); lost_to[loser].append(winner)
            mov_values[winner].append(min(21.0, margin))
            game_id = str(g.get("game_id") or g.get("id") or "")
            if g.get("cfbd_completed") and (game_id, winner) in played_game_control:
                winner_gc = played_game_control[(game_id, winner)]
                loser_gc = played_game_control.get((game_id, loser), 1.0 - winner_gc)
            else:
                winner_gc = 1.0 / (1.0 + math.exp(-min(35.0, margin) / 12.0))
                loser_gc = 1.0 - winner_gc
            raw_game_control[winner].append(winner_gc)
            raw_game_control[loser].append(loser_gc)
            played.append((winner, loser, margin))
            ac, hc = CONF.norm_conf(g.get("away_conference")), CONF.norm_conf(g.get("home_conference"))
            if g.get("is_conference_game") and ac == hc:
                conf_wins[winner] += 1

        champs, power_champs, g6_champs = {}, set(), set()
        for conf, names in conf_teams.items():
            eligible = [t for t in names if CONF.eligible_for_title(conf, t, title_rules)]
            if len(eligible) < 2:
                continue
            ranked_conf = CONF.rank_conference_teams(conf, eligible, conf_wins, teams, results, conf_games[conf], rng)
            a, b = ranked_conf[0], ranked_conf[1]
            expected_margin_b = (
                CONF.team_rating(teams[b]) -
                CONF.team_rating(teams[a])
            )
            p_b = canonical_win_prob_from_margin(expected_margin_b)
            margin_b = simulated_margin_with_canonical_winner(
                expected_margin_b,
                p_b,
                rng,
                sigma,
            )
            champ, runner = (b, a) if margin_b > 0 else (a, b)
            margin = max(0.01, abs(margin_b))
            champs[conf] = champ
            wins[champ] += 1; losses[runner] += 1
            opponents[champ].append(runner); opponents[runner].append(champ)
            sos_opponents[champ].append((runner, 0.0)); sos_opponents[runner].append((champ, 0.0))
            defeated[champ].append(runner); lost_to[runner].append(champ)
            mov_values[champ].append(min(21.0, margin)); played.append((champ, runner, margin))
            champ_gc = 1.0 / (1.0 + math.exp(-min(35.0, margin) / 12.0))
            raw_game_control[champ].append(champ_gc); raw_game_control[runner].append(1.0 - champ_gc)
            if conf in POWER_CONFS: power_champs.add(champ)
            elif conf in G6_CONFS: g6_champs.add(champ)

        games_played = {t: wins[t] + losses[t] for t in teams}
        win_pct = {t: wins[t] / games_played[t] if games_played[t] else 0.0 for t in teams}
        opp_wp = {}
        for t in teams:
            vals = [win_pct[o] for o in opponents[t]]
            opp_wp[t] = sum(vals) / len(vals) if vals else 0.0
        metrics = {}
        for t in teams:
            opp_vals = [max(0.0, min(1.0, win_pct[o] + venue_adj)) for o, venue_adj in sos_opponents[t]]
            opp_opp_vals = [opp_wp[o] for o in opponents[t]]
            sos_value = (2 / 3) * (sum(opp_vals) / len(opp_vals) if opp_vals else 0.0) + (1 / 3) * (sum(opp_opp_vals) / len(opp_opp_vals) if opp_opp_vals else 0.0)
            weighted_mol = [margin * (0.6 + 0.8 * (1 - win_pct[opp])) for winner, loser, margin in played if loser == t for opp in [winner]]
            m = {
                # Future games do not have a play-state curve.  Their raw GC is a
                # calibrated margin proxy; the season value is then SOS-adjusted.
                "game_control": max(0.0, min(1.0,
                    (sum(raw_game_control[t]) / len(raw_game_control[t]) if raw_game_control[t] else 0.5)
                    + 0.35 * (sos_value - 0.5))),
                "power_championship_wins": 1.0 if t in power_champs else 0.0,
                "g6_championship_wins": 1.0 if t in g6_champs else 0.0,
                "quality_wins": float(sum(1 for o in defeated[t] if win_pct[o] > 0.5)),
                "top25_wins": 0.0,
                "losses": float(losses[t]),
                "avg_capped_mov": sum(mov_values[t]) / len(mov_values[t]) if mov_values[t] else 0.0,
                "avg_weighted_mol": sum(weighted_mol) / len(weighted_mol) if weighted_mol else 0.0,
                "bad_losses": float(sum(1 for o in lost_to[t] if win_pct[o] <= 0.5)),
                "sos": sos_value,
            }
            metrics[t] = m
        for t in teams:
            metrics[t]["top25_wins"] = float(sum(1 for o in defeated[t] if o in official_top25))
        apply_validated_resume_score(metrics)
        ranked = sorted(teams, key=lambda t: (metrics[t]["resume_score"], CONF.team_rating(teams[t])), reverse=True)
        for rank, t in enumerate(ranked, 1):
            rank_sums[t] += rank
            if rank <= 25: top25_count[t] += 1
            for name in metric_names: metric_sums[name][t] += metrics[t][name]
        field, auto = select_field(ranked, champs, teams)
        if len(field) != 12:
            continue
        counters["field"][tuple(field)] += 1
        for t in field:
            counters["playoff"][t] += 1
        for t in auto:
            counters["auto"][t] += 1
        simulate_bracket(field, teams, rng, sigma, counters)

    rows = []
    for team, t in teams.items():
        seed_dist = {str(k): round(v / sims, 4) for k, v in sorted(counters["seed"][team].items())}
        row = {
            "team": team, "conference": CONF.norm_conf(t.get("conference")),
            "playoff_pct": round(counters["playoff"][team] / sims, 4),
            "auto_bid_pct": round(counters["auto"][team] / sims, 4),
            "playoff_bye_pct": round(counters["bye"][team] / sims, 4),
            "quarterfinal_pct": round(counters["quarterfinal"][team] / sims, 4),
            "semifinal_pct": round(counters["semifinal"][team] / sims, 4),
            "national_title_game_pct": round(counters["title_game"][team] / sims, 4),
            "national_title_pct": round(counters["champion"][team] / sims, 4),
            "projected_cfp_rank": round(rank_sums[team] / sims, 2),
            "top25_pct": round(top25_count[team] / sims, 4),
            "seed_distribution": seed_dist,
        }
        row.update({name: round(metric_sums[name][team] / sims, 4) for name in metric_names})
        row["game_control_index"] = round(100.0 * (row["game_control"] - 0.5), 2)
        rows.append(row)
        t.update({k: v for k, v in row.items() if k not in {"team", "conference"}})

    for rank, row in enumerate(sorted(rows, key=lambda r: r["sos"], reverse=True), 1):
        row["sos_rank"] = rank
        teams[row["team"]]["sos_rank"] = rank

    rows.sort(key=lambda r: (r["playoff_pct"], r["national_title_pct"]), reverse=True)
    # A representative bracket should not be the most common *exact* Monte Carlo
    # field (that combination can be rare and visually unstable).  Build it from
    # expected wins and each conference's most likely champion instead.
    expected_champs = {}
    for conf, names in conf_teams.items():
        eligible = [t for t in names if CONF.eligible_for_title(conf, t, title_rules)]
        if eligible:
            expected_champs[conf] = max(
                eligible,
                key=lambda t: (fnum(teams[t].get("conference_title_pct")), CONF.team_rating(teams[t])),
            )
    expected_ranked = [r["team"] for r in sorted(rows, key=lambda r: r["projected_cfp_rank"])]
    projected_field, projected_auto = select_field(expected_ranked, expected_champs, teams)
    db["playoff_model"] = {
        "schema_version": "cfp-2026-v7-g6-seed12-causal-percentile-resume",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "trials": sims,
        "metadata": {
            "format": "2026-27 12-team CFP with exactly one G6 qualifier, locked to seed 12",
            "automatic_bids": "ACC, B1G, B12, SEC champions plus the highest-ranked champion from American/CUSA/MAC/MW/PAC12/Sun Belt",
            "g6_at_large_policy": "Exactly one G6 team is allowed in the field; all non-selected G6 teams are excluded from at-large bids.",
            "g6_seeding_policy": "The selected G6 automatic qualifier is always assigned seed 12.",
            "at_large_bids": 7,
            "byes": "Seeds 1-4",
            "ranking_proxy": "Prospective percentile resume blend validated with leave-one-season-out 2021-24 weekly CFP polls; schedule-adjusted Game Control, quality wins, prior-poll Top-25 wins, losses, bad losses, capped MOV and weighted MOL.",
            "resume_weights": RESUME_WEIGHTS,
            "mov_cap": 21,
            "game_control_method": "NCAAF Game Control Index = 100 * (schedule-adjusted control AUC - .500). Played games use time-weighted PBP curves; future games use logistic(final margin / 12), capped at 35. This is an open index, not the proprietary SportSource/Matrix value.",
            "cfp_sos_method": "CFP-specific SOS = (2/3 * opponents' winning percentage) + (1/3 * opponents' opponents' winning percentage), with a small home/road adjustment. It is distinct from the site's power-rating SOS and is embedded in Game Control rather than separately weighted in the resume score.",
            "top25_method": "For the next projected poll, wins over teams in the latest already-published official CFP Top 25. This is causal prior-poll information; no model-ranking substitute is used before the first CFP release.",
            "historical_validation": "2021-24 leave-one-season-out: 81.3% Top-12 recall, 82.5% Top-25 recall, 4.86 Top-25 MAE, 0.808 Spearman. Championship bonuses are applied only because these simulations include the completed conference-title round.",
            "top25_status": official_top25_status,
            "game_model": (
                "Canonical win probabilities use logistic margin scale 6.5. "
                "Scheduled games use Game Projection Consensus margins when available; "
                "hypothetical conference-title and CFP matchups use Site Composite "
                "rating margins. CFP first-round hosts receive fixed 2.6 HFA; later "
                "rounds are neutral. Legacy Normal sigma is retained only for simulated "
                "margin magnitude used by validated CFP resume metrics."
            ),
            "win_probability_model_version": WIN_PROB_MODEL_VERSION,
            "win_probability_logistic_scale": WIN_PROB_LOGISTIC_SCALE,
            "fixed_home_field_advantage": FIXED_HFA,
            "resume_margin_sigma": sigma,
        },
        "projected_field": [
            {"seed": i + 1, "team": t, "automatic_qualifier": t in projected_auto}
            for i, t in enumerate(projected_field)
        ],
        "teams": rows,
    }
    db.setdefault("meta", {})["playoff_model_built_at"] = db["playoff_model"]["built_at"]
    db["meta"]["playoff_model_trials"] = sims
    return db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/snapshots/preseason/preseason_db.json")
    ap.add_argument("--sims", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20260718)
    ap.add_argument(
        "--sigma",
        type=float,
        default=14.0,
        help="Margin-magnitude sigma for validated CFP resume metrics only",
    )
    ap.add_argument("--output", default="data/site/playoff_model_2026.json")
    args = ap.parse_args()

    db_path = ROOT / args.db
    if not db_path.exists():
        raise SystemExit(f"Missing canonical preseason DB: {db_path}")

    db = json.loads(db_path.read_text(encoding="utf-8"))
    db = run_model(db, args.sims, args.seed, args.sigma)

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(db["playoff_model"], indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Playoff model: {args.sims} trials")
    print(f"Source DB: {db_path}")
    print(f"Wrote {out}")
    print(f"Win probability model: {WIN_PROB_MODEL_VERSION}")
    print(f"First-round HFA: {FIXED_HFA}")

    for row in db["playoff_model"]["teams"][:15]:
        print(
            f"{row['team']:<22} "
            f"CFP {row['playoff_pct']:.1%}  "
            f"Bye {row['playoff_bye_pct']:.1%}  "
            f"Title {row['national_title_pct']:.1%}"
        )


if __name__ == "__main__":
    main()
