#!/usr/bin/env python3
"""
Rerun 2026 conference simulations from the corrected embedded index.html DB.

Purpose:
- Uses DB.games as the schedule source of truth after schedule/rule patches.
- Uses DB.teams power ratings/projections for game probabilities.
- Applies conference-game overrides and title-eligibility rules if CSVs exist.
- Updates DB.teams and DB.conferences with fresh:
    avg_total_wins
    avg_conference_wins
    bowl_eligibility_pct
    win_distribution
    make_title_game_pct
    conference_title_pct
    lose_title_game_pct
    championship_game.projected_matchup / projected_spread / projected_total / home_win_pct

Notes:
- Regular-season title qualification uses games before week 14 only.
- Total wins include all scheduled non-placeholder regular-season games, including Army-Navy if present.
- Conference-game overrides can mark games like Army-Navy and NDSU/SJSU non-conference.
- NDSU MW title ineligibility can be handled by conference_eligibility_rules_2026.csv or built-in default.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

DB_RE = re.compile(r'(<script id="db" type="application/json">)(.*?)(</script>)', re.S)

CONF_ALIASES = {
    "AAC": "American",
    "American Athletic": "American",
    "American Athletic Conference": "American",
    "Big 12": "B12",
    "Big Ten": "B1G",
    "Conference USA": "CUSA",
    "Mid-American": "MAC",
    "Mid-American Conference": "MAC",
    "Mountain West": "MW",
    "MWC": "MW",
    "Pac-12": "PAC12",
    "Pac 12": "PAC12",
    "PAC-12": "PAC12",
    "PAC12": "PAC12",
}

# Built-in 2026 eligibility rules. CSV can add/override these.
# North Dakota State is now treated as Mountain West title eligible.
DEFAULT_TITLE_INELIGIBLE = {}

# Known 2026 game-count exceptions for audit/reporting only.
ACC_EIGHT_GAME_TEAMS_2026 = {
    "Boston College", "Clemson", "Florida State", "Georgia Tech", "North Carolina",
}
EXPECTED_CONFERENCE_GAMES_2026 = {
    "ACC": None,  # team-specific
    "American": 8,
    "B12": 9,
    "B1G": 9,
    "CUSA": 8,
    "MAC": 8,
    "MW": 8,
    "PAC12": 8,
    "SEC": 9,
    "Sun Belt": 8,
}


def norm_conf(x: Any) -> str:
    s = str(x or "").strip()
    return CONF_ALIASES.get(s, s)


def norm_team(x: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()


def to_bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    s = str(x or "").strip().lower()
    return s in {"1", "true", "t", "yes", "y"}


def to_int(x: Any, default: int = 0) -> int:
    try:
        if x is None or x == "":
            return default
        return int(float(x))
    except Exception:
        return default


def fnum(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def american_from_prob(p: float) -> Optional[int]:
    if p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


WIN_PROB_LOGISTIC_SCALE = 6.5
WIN_PROB_MODEL_VERSION = "logistic_margin_scale_6_5_v1"

def canonical_home_prob_from_margin(margin_home: float) -> float:
    """Canonical 2026 Game Projection Consensus win-probability conversion."""
    p = 1.0 / (1.0 + math.exp(-float(margin_home) / WIN_PROB_LOGISTIC_SCALE))
    return max(0.001, min(0.999, p))

def implied_home_prob_from_margin(margin_home: float, sigma: float) -> float:
    # Legacy/fallback probability path only.
    return max(0.001, min(0.999, normal_cdf(margin_home / sigma)))


def load_db_from_index(path: Path) -> Tuple[str, Dict[str, Any], re.Match]:
    html = path.read_text(encoding="utf-8")
    m = DB_RE.search(html)
    if not m:
        raise SystemExit(f"Could not find embedded DB script in {path}")
    return html, json.loads(m.group(2)), m


def write_db_to_index(path: Path, html: str, match: re.Match, db: Dict[str, Any]) -> None:
    db_txt = json.dumps(db, separators=(",", ":"))
    new_html = html[:match.start(2)] + db_txt + html[match.end(2):]
    path.write_text(new_html, encoding="utf-8")


def load_game_overrides(path: Path) -> Dict[Tuple[str, str, str], bool]:
    """Return overrides keyed by unordered team pair plus optional date.

    Keys:
      (date, team_norm_a, team_norm_b)
      ("", team_norm_a, team_norm_b)
    """
    overrides: Dict[Tuple[str, str, str], bool] = {}
    if not path.exists():
        return overrides
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            raw = str(row.get("override_conf_game", "")).strip()
            if raw == "":
                continue
            val = raw.lower() in {"true", "1", "yes", "y"}
            a = norm_team(row.get("away_team"))
            h = norm_team(row.get("home_team"))
            if not a or not h:
                continue
            x, y = sorted([a, h])
            date = str(row.get("date") or "").strip()
            overrides[(date, x, y)] = val
            overrides[("", x, y)] = val
    return overrides


def load_eligibility_rules(path: Path) -> Dict[Tuple[str, str], str]:
    rules = dict(DEFAULT_TITLE_INELIGIBLE)
    if not path.exists():
        return rules
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            conf = norm_conf(row.get("conference"))
            team = str(row.get("team") or "").strip()
            if not conf or not team:
                continue
            title_eligible = str(row.get("title_game_eligible", row.get("title_winner_eligible", ""))).strip().lower()
            winner_eligible = str(row.get("title_winner_eligible", "")).strip().lower()
            eligible = not (title_eligible in {"false", "0", "no", "n"} or winner_eligible in {"false", "0", "no", "n"})
            if not eligible:
                rules[(conf, team)] = row.get("notes") or "Not eligible for 2026 conference title."
    return rules


def apply_game_overrides(db: Dict[str, Any], overrides: Dict[Tuple[str, str, str], bool]) -> int:
    changed = 0
    for g in db.get("games", []):
        a = norm_team(g.get("away_team"))
        h = norm_team(g.get("home_team"))
        if not a or not h:
            continue
        x, y = sorted([a, h])
        date = str(g.get("date") or "").strip()
        val = overrides.get((date, x, y), overrides.get(("", x, y)))
        if val is not None and bool(g.get("is_conference_game")) != bool(val):
            g["is_conference_game"] = bool(val)
            g["conference_game_override_applied"] = True
            changed += 1
    return changed


def team_rating(team: Dict[str, Any]) -> float:
    return fnum(team.get("combo"), 0.0)


def estimate_margin_home(home: Dict[str, Any], away: Dict[str, Any], neutral: bool = False) -> float:
    margin = team_rating(home) - team_rating(away)
    if not neutral:
        margin += fnum(home.get("hfa"), 0.0)
    return margin


def estimate_total(home: Dict[str, Any], away: Dict[str, Any]) -> float:
    # Use SP offense/defense-like components if available; fallback to 53.
    ho = fnum(home.get("sp_offense"), 28.0)
    hd = fnum(home.get("sp_defense"), 24.0)
    ao = fnum(away.get("sp_offense"), 28.0)
    ad = fnum(away.get("sp_defense"), 24.0)
    total = ((ao + hd) / 2.0) + ((ho + ad) / 2.0)
    return round(max(32.0, min(82.0, total)), 1)


def game_home_prob(g: Dict[str, Any], team_by_name: Dict[str, Dict[str, Any]], sigma: float) -> float:
    # Current scheduled-game projection consensus is canonical when present.
    # Legacy win_prob_home values may still reflect an old Active Combo / Site Projection.
    model_version = str(g.get("projection_spread_model_version") or "")
    consensus_margin = g.get("projected_margin_home")
    if model_version.startswith("spread_consensus_") and consensus_margin is not None:
        # Scheduled production games use one canonical margin -> probability model.
        return canonical_home_prob_from_margin(fnum(consensus_margin))

    p = g.get("win_prob_home")
    if p is not None and 0 < fnum(p, -1) < 1:
        return fnum(p)

    home = team_by_name.get(g.get("home_team"))
    away = team_by_name.get(g.get("away_team"))
    if not home or not away:
        return 0.5
    margin = g.get("projected_margin_home")
    if margin is None:
        margin = estimate_margin_home(home, away, bool(g.get("neutral_site")))
    return implied_home_prob_from_margin(fnum(margin), sigma)


def eligible_for_title(conf: str, team: str, rules: Dict[Tuple[str, str], str]) -> bool:
    return (conf, team) not in rules


def head_to_head_score(team: str, tied: set, simulated_results: Dict[Tuple[str, str], str], conf_games: List[Dict[str, Any]]) -> int:
    score = 0
    for g in conf_games:
        a, h = g.get("away_team"), g.get("home_team")
        if team not in {a, h}:
            continue
        opp = h if team == a else a
        if opp not in tied:
            continue
        winner = simulated_results.get((a, h))
        if winner == team:
            score += 1
    return score


def rank_conference_teams(
    conf: str,
    teams: List[str],
    conf_wins: Dict[str, int],
    team_by_name: Dict[str, Dict[str, Any]],
    simulated_results: Dict[Tuple[str, str], str],
    conf_games: List[Dict[str, Any]],
    rng: random.Random,
) -> List[str]:
    # Group by conference wins first. Within tied groups use head-to-head wins among tied teams,
    # then rating, then deterministic random jitter for residual ties.
    groups: Dict[int, List[str]] = defaultdict(list)
    for t in teams:
        groups[conf_wins.get(t, 0)].append(t)

    ranked: List[str] = []
    for wins in sorted(groups.keys(), reverse=True):
        group = groups[wins]
        tied = set(group)
        group_sorted = sorted(
            group,
            key=lambda t: (
                head_to_head_score(t, tied, simulated_results, conf_games),
                team_rating(team_by_name.get(t, {})),
                rng.random() * 1e-6,
            ),
            reverse=True,
        )
        ranked.extend(group_sorted)
    return ranked


def build_regular_games(db: Dict[str, Any]) -> List[Dict[str, Any]]:
    games = []
    valid_teams = {t.get("team") for t in db.get("teams", [])}
    for g in db.get("games", []):
        week = to_int(g.get("week"), 0)
        away = g.get("away_team")
        home = g.get("home_team")
        # Exclude placeholder championship templates. Keep Army-Navy week 15 because real teams.
        if away not in valid_teams or home not in valid_teams:
            continue
        if week == 14:
            continue
        games.append(g)
    return games


def expected_conf_games(conf: str, team: str) -> Optional[int]:
    if conf == "ACC":
        return 8 if team in ACC_EIGHT_GAME_TEAMS_2026 else 9
    return EXPECTED_CONFERENCE_GAMES_2026.get(conf)


def audit_conference_counts(db: Dict[str, Any], out_path: Path) -> None:
    counts = defaultdict(lambda: defaultdict(int))
    for g in build_regular_games(db):
        if not bool(g.get("is_conference_game")):
            continue
        a, h = g.get("away_team"), g.get("home_team")
        ac, hc = norm_conf(g.get("away_conference")), norm_conf(g.get("home_conference"))
        if ac == hc:
            counts[ac][a] += 1
            counts[hc][h] += 1
    rows = []
    for conf in sorted(counts):
        vals = sorted(set(counts[conf].values()))
        for team, cnt in sorted(counts[conf].items()):
            exp = expected_conf_games(conf, team)
            rows.append({
                "conference": conf,
                "team": team,
                "current_conf_games": cnt,
                "expected_conf_games": exp if exp is not None else "",
                "delta_vs_expected": cnt - exp if exp is not None else "",
                "conference_unique_counts": "|".join(map(str, vals)),
                "issue_flag": "TRUE" if exp is not None and cnt != exp else "FALSE",
            })
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["conference"])
        w.writeheader(); w.writerows(rows)


def rerun_sims(db: Dict[str, Any], sims: int, seed: int, sigma: float, title_sigma: float) -> Dict[str, Any]:
    rng = random.Random(seed)
    teams = db.get("teams", [])
    team_by_name = {t.get("team"): t for t in teams}
    conf_to_teams: Dict[str, List[str]] = defaultdict(list)
    for t in teams:
        conf = norm_conf(t.get("conference"))
        if conf and conf != "Independent":
            conf_to_teams[conf].append(t.get("team"))

    title_rules = load_eligibility_rules(Path("conference_eligibility_rules_2026.csv"))

    regular_games = build_regular_games(db)
    conf_games_by_conf: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for g in regular_games:
        ac, hc = norm_conf(g.get("away_conference")), norm_conf(g.get("home_conference"))
        if bool(g.get("is_conference_game")) and ac == hc:
            conf_games_by_conf[ac].append(g)

    total_wins_sum = Counter()
    conf_wins_sum = Counter()
    bowl_count = Counter()
    win_dist: Dict[str, Counter] = defaultdict(Counter)
    make_title = Counter()
    conf_title = Counter()
    title_matchups = Counter()

    # Precompute regular game probabilities.
    game_probs = []
    for g in regular_games:
        p_home = game_home_prob(g, team_by_name, sigma)
        game_probs.append((g, p_home))

    for _ in range(sims):
        total_wins = Counter()
        conf_wins = Counter()
        simulated_results: Dict[Tuple[str, str], str] = {}

        for g, p_home in game_probs:
            away, home = g.get("away_team"), g.get("home_team")
            if rng.random() < p_home:
                winner = home
            else:
                winner = away
            simulated_results[(away, home)] = winner
            total_wins[winner] += 1

            ac, hc = norm_conf(g.get("away_conference")), norm_conf(g.get("home_conference"))
            if bool(g.get("is_conference_game")) and ac == hc and winner in {away, home}:
                conf_wins[winner] += 1

        for t in team_by_name:
            tw = total_wins.get(t, 0)
            cw = conf_wins.get(t, 0)
            total_wins_sum[t] += tw
            conf_wins_sum[t] += cw
            win_dist[t][tw] += 1
            if tw >= 6:
                bowl_count[t] += 1

        for conf, names in conf_to_teams.items():
            eligible = [t for t in names if eligible_for_title(conf, t, title_rules)]
            if len(eligible) < 2:
                continue
            ranked = rank_conference_teams(conf, eligible, conf_wins, team_by_name, simulated_results, conf_games_by_conf.get(conf, []), rng)
            no1, no2 = ranked[0], ranked[1]
            make_title[no1] += 1
            make_title[no2] += 1
            title_matchups[(conf, no1, no2)] += 1

            # Title game: No. 1 is home/host except neutral_site template.
            cobj = next((c for c in db.get("conferences", []) if c.get("conference") == conf), {})
            cg = cobj.get("championship_game") or {}
            neutral = bool(cg.get("neutral_site"))
            home_team = team_by_name.get(no1, {})
            away_team = team_by_name.get(no2, {})
            margin_home = estimate_margin_home(home_team, away_team, neutral)
            p_home = canonical_home_prob_from_margin(margin_home)
            champ = no1 if rng.random() < p_home else no2
            conf_title[champ] += 1

    # Update team rows globally.
    for t in teams:
        name = t.get("team")
        t["avg_total_wins"] = round(total_wins_sum[name] / sims, 4)
        t["avg_conference_wins"] = round(conf_wins_sum[name] / sims, 4)
        t["bowl_eligibility_pct"] = round(bowl_count[name] / sims, 4)
        t["make_title_game_pct"] = round(make_title[name] / sims, 4)
        t["conference_title_pct"] = round(conf_title[name] / sims, 4)
        t["lose_title_game_pct"] = round(max(0.0, make_title[name] / sims - conf_title[name] / sims), 4)
        t["win_distribution"] = [
            {"wins": wins, "probability": round(count / sims, 4)}
            for wins, count in sorted(win_dist[name].items())
        ]

        conf = norm_conf(t.get("conference"))
        if (conf, name) in title_rules:
            t["make_title_game_pct"] = 0.0
            t["conference_title_pct"] = 0.0
            t["lose_title_game_pct"] = 0.0
            t["conference_title_ineligible"] = True
            t["conference_title_ineligible_note"] = title_rules[(conf, name)]

    # Update conference objects and their copied team rows.
    team_by_name = {t.get("team"): t for t in teams}
    for c in db.get("conferences", []):
        conf = norm_conf(c.get("conference"))
        c["conference"] = conf
        names = conf_to_teams.get(conf, [])
        # Keep original order/ranking if possible, but use updated team objects.
        existing_order = [t.get("team") for t in c.get("teams", [])]
        ordered_names = [n for n in existing_order if n in team_by_name] + [n for n in names if n not in existing_order]
        c["teams"] = [deepcopy(team_by_name[n]) for n in ordered_names]
        c["num_teams"] = len(c["teams"])
        if c["teams"]:
            c["average_strength"] = round(sum(fnum(t.get("combo")) for t in c["teams"]) / len(c["teams"]), 4)

        cg = c.get("championship_game")
        eligible = [n for n in names if eligible_for_title(conf, n, title_rules)]
        ranked = sorted(
            eligible,
            key=lambda n: (
                fnum(team_by_name[n].get("make_title_game_pct")),
                fnum(team_by_name[n].get("conference_title_pct")),
                fnum(team_by_name[n].get("avg_conference_wins")),
                fnum(team_by_name[n].get("combo")),
            ),
            reverse=True,
        )
        if cg and len(ranked) >= 2:
            home_name, away_name = ranked[0], ranked[1]
            cg["projected_matchup"] = {"away_team": away_name, "home_team": home_name}
            home = team_by_name[home_name]
            away = team_by_name[away_name]
            neutral = bool(cg.get("neutral_site"))
            margin_home = round(estimate_margin_home(home, away, neutral), 1)
            total = estimate_total(home, away)
            cg["projected_spread"] = margin_home
            cg["projected_total"] = total
            cg["home_win_pct"] = canonical_home_prob_from_margin(margin_home)
            if any((conf, n) in title_rules for n in names):
                notes = [f"{team} excluded: {note}" for (rule_conf, team), note in title_rules.items() if rule_conf == conf]
                cg["eligibility_note"] = " ".join(notes)

    db.setdefault("meta", {})["conference_sims_rerun_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    db["meta"]["conference_sims_num_trials"] = sims
    db["meta"]["conference_sims_model"] = (
        "Monte Carlo from canonical Game Projection Consensus margins/probabilities "
        "for scheduled games and Site Composite rating-derived margins for hypothetical "
        "conference title games; all model margins convert to win probability with "
        "logistic scale 6.5."
    )
    db["meta"]["win_probability_model_version"] = WIN_PROB_MODEL_VERSION
    db["meta"]["win_probability_logistic_scale"] = WIN_PROB_LOGISTIC_SCALE
    return db


def write_probability_audit(before: Dict[str, Any], after: Dict[str, Any], out_path: Path) -> None:
    def cteams(db):
        out = {}
        for c in db.get("conferences", []):
            conf = c.get("conference")
            for t in c.get("teams", []):
                out[(conf, t.get("team"))] = t
        return out
    b, a = cteams(before), cteams(after)
    rows = []
    for key in sorted(a):
        at = a[key]
        bt = b.get(key, {})
        row = {"conference": key[0], "team": key[1]}
        for col in ["avg_total_wins", "avg_conference_wins", "make_title_game_pct", "conference_title_pct", "lose_title_game_pct", "bowl_eligibility_pct"]:
            bv, av = fnum(bt.get(col)), fnum(at.get(col))
            row[f"before_{col}"] = round(bv, 6)
            row[f"after_{col}"] = round(av, 6)
            row[f"delta_{col}"] = round(av - bv, 6)
        rows.append(row)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["conference", "team"])
        w.writeheader(); w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="index.html", help="Path to index.html to update")
    ap.add_argument("--sims", type=int, default=20000, help="Number of Monte Carlo trials")
    ap.add_argument("--seed", type=int, default=20260511)
    ap.add_argument("--sigma", type=float, default=14.0, help="Regular-game margin sigma for fallback win probs")
    ap.add_argument("--title-sigma", type=float, default=14.0, help="Title-game margin sigma")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    path = Path(args.index)
    html, db, m = load_db_from_index(path)
    before = deepcopy(db)

    overrides = load_game_overrides(Path("conference_game_overrides_2026.csv"))
    changed = apply_game_overrides(db, overrides)

    backup = path.with_name(f"{path.stem}_before_conference_sims_rerun_{datetime.now():%Y%m%d_%H%M%S}{path.suffix}")
    if not args.dry_run:
        backup.write_text(html, encoding="utf-8")

    db = rerun_sims(db, args.sims, args.seed, args.sigma, args.title_sigma)

    audit_counts_path = Path("conference_game_count_audit_after_conference_sims_2026.csv")
    audit_probs_path = Path("conference_probability_rerun_audit_2026.csv")
    audit_conference_counts(db, audit_counts_path)
    write_probability_audit(before, db, audit_probs_path)

    if not args.dry_run:
        write_db_to_index(path, html, m, db)

    print("Done." if not args.dry_run else "Dry run complete; index not written.")
    print(f"Index: {path}")
    if not args.dry_run:
        print(f"Backup: {backup}")
    print(f"Applied game override changes before sim: {changed}")
    print(f"Trials: {args.sims}")
    print(f"Wrote: {audit_counts_path}")
    print(f"Wrote: {audit_probs_path}")

    # Quick key conference summary.
    for conf in ["CUSA", "MW"]:
        c = next((x for x in db.get("conferences", []) if x.get("conference") == conf), None)
        if not c:
            continue
        print(f"\n{conf} title game:", c.get("championship_game", {}).get("projected_matchup"))
        print("title sum:", round(sum(fnum(t.get("conference_title_pct")) for t in c.get("teams", [])), 6))
        print("make-title sum:", round(sum(fnum(t.get("make_title_game_pct")) for t in c.get("teams", [])), 6))
        top = sorted(c.get("teams", []), key=lambda t: fnum(t.get("conference_title_pct")), reverse=True)[:5]
        for t in top:
            print(f"  {t.get('team')}: conf_wins={fnum(t.get('avg_conference_wins')):.3f}, make={fnum(t.get('make_title_game_pct')):.4f}, title={fnum(t.get('conference_title_pct')):.4f}")


if __name__ == "__main__":
    main()
