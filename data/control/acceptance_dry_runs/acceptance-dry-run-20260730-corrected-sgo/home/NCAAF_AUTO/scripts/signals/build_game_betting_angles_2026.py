from pathlib import Path
import pandas as pd
import numpy as np
import json
import re
from difflib import SequenceMatcher

GAMES = Path("data/projections/game_projection_blend_2026.csv")
SITE = Path("index.html")
VAR = Path("data/ratings/ratings_system_variance.csv")
RP_BADGES = Path("data/site/rp_support_badges.json")
RP_SIGNALS = Path("data/signals/returning_production_early_season_signals.csv")
TRAVEL_1H = Path("data/signals/travel_1h_signals_2026.csv")
COACH_CONTEXT = Path("data/coach/game_coach_fav_dog_context.csv")
INJURY_GAMES = Path("data/injuries/game_injury_alerts.csv")
PBP_MOVEMENT = Path("data/signals/pbp_line_movement_signals_2026.csv")
CROSS_BOOK = Path("data/signals/cross_book_opener_signals_2026.csv")
OUT = Path("data/signals/game_betting_angles_2026.csv")

def num(x):
    try:
        if pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan

def clean(x):
    if pd.isna(x):
        return ""
    return str(x)

def norm_team(x):
    return re.sub(r"[^a-z0-9]+", " ", clean(x).lower()).strip()

def load_games():
    if SITE.exists():
        txt = SITE.read_text(errors="ignore")
        m = re.search(r'<script id="db" type="application/json">(.*?)</script>', txt, flags=re.S)
        if m:
            db = json.loads(m.group(1))
            games = pd.DataFrame(db.get("games", []))
            if len(games):
                return games
    return pd.read_csv(GAMES)

def market_spread_home(row):
    for c in [
        "market_spread_home",
        "consensus_spread_home",
        "sgo_spread_home",
        "spread_home",
    ]:
        if c in row.index:
            v = num(row.get(c))
            if np.isfinite(v):
                return v
    return np.nan

def add_angle(rows, g, angle_key, angle_label, side_team, reason, metric_value=np.nan, tier="", sort_score=np.nan, extras=None):
    row = {
        "game_id": clean(g.get("game_id")),
        "week": g.get("week"),
        "date": clean(g.get("date")),
        "away_team": clean(g.get("away_team")),
        "home_team": clean(g.get("home_team")),
        "angle_key": angle_key,
        "angle_label": angle_label,
        "side_team": clean(side_team),
        "reason": reason,
        "metric_value": metric_value,
        "tier": tier,
        "sort_score": sort_score if np.isfinite(num(sort_score)) else metric_value,
    }
    if extras:
        row.update(extras)
    rows.append(row)

def make_game_lookup(games):
    by_id = {}
    by_match = {}
    for _, g in games.iterrows():
        gid = clean(g.get("game_id"))
        if gid:
            by_id[gid] = g
        key = (clean(g.get("date")), norm_team(g.get("away_team")), norm_team(g.get("home_team")))
        by_match[key] = g
    return by_id, by_match

def add_ratings_variance(rows, games, var_by_team):
    for _, g in games.iterrows():
        away = clean(g.get("away_team"))
        home = clean(g.get("home_team"))

        away_v = var_by_team.get(away, {})
        home_v = var_by_team.get(home, {})

        away_range = num(away_v.get("rating_range"))
        home_range = num(home_v.get("rating_range"))
        max_range = np.nanmax([away_range, home_range]) if any(np.isfinite(x) for x in [away_range, home_range]) else np.nan

        if np.isfinite(max_range) and max_range >= 6.0:
            side = away if away_range >= home_range else home
            v = away_v if side == away else home_v
            add_angle(
                rows, g,
                "high_variance",
                "High model variance",
                side,
                f"{side} rating range {num(v.get('rating_range')):.1f} across SP+/FPI/TeamRankings; high source {clean(v.get('highest_source'))}, low source {clean(v.get('lowest_source'))}.",
                max_range,
                "high",
                max_range,
            )

        if np.isfinite(max_range) and max_range >= 3.0:
            side = away if away_range >= home_range else home
            v = away_v if side == away else home_v
            tier = "high" if max_range >= 6 else "medium"
            add_angle(
                rows, g,
                "medium_variance",
                "Medium+ model variance",
                side,
                f"{side} rating range {num(v.get('rating_range')):.1f} across SP+/FPI/TeamRankings.",
                max_range,
                tier,
                max_range,
            )

def add_near_pick(rows, games):
    for _, g in games.iterrows():
        proj = num(g.get("projected_margin_home"))
        mkt = market_spread_home(g)

        coin_reasons = []
        coin_metric = np.nan

        if np.isfinite(proj) and abs(proj) <= 3.0:
            fav = clean(g.get("home_team")) if proj >= 0 else clean(g.get("away_team"))
            coin_reasons.append(f"model spread {fav} -{abs(proj):.1f}")
            coin_metric = abs(proj)

        if np.isfinite(mkt) and abs(mkt) <= 3.0:
            fav = clean(g.get("home_team")) if mkt <= 0 else clean(g.get("away_team"))
            coin_reasons.append(f"market spread {fav} -{abs(mkt):.1f}")
            coin_metric = min(coin_metric, abs(mkt)) if np.isfinite(coin_metric) else abs(mkt)

        if coin_reasons:
            add_angle(
                rows, g,
                "near_pick",
                "Near pick’em game",
                "",
                "; ".join(coin_reasons),
                coin_metric,
                "medium",
                3.0 - coin_metric if np.isfinite(coin_metric) else 0,
            )

def add_rp_badges(rows, by_match):
    # Only validated 2023-25 early-season RP study signals are actionable.
    # rp_support_badges.json remains descriptive context and is excluded here.
    if not RP_SIGNALS.exists():
        return

    df = pd.read_csv(RP_SIGNALS)
    by_gid = {}
    for _, r in df.iterrows():
        gid = clean(r.get("game_id"))
        if gid:
            by_gid.setdefault(gid, []).append(r)

    for gid, rs in by_gid.items():
        valid = [r for r in rs if num(r.get("historical_games")) > 0 and clean(r.get("historical_ats_record"))]
        if not valid:
            continue
        r = sorted(valid, key=lambda x: abs(num(x.get("score"))), reverse=True)[0]
        g = pd.Series({
            "game_id": gid,
            "week": r.get("week"),
            "date": r.get("date"),
            "away_team": r.get("away_team"),
            "home_team": r.get("home_team"),
        })
        score = num(r.get("score"))
        team = clean(r.get("team"))
        headline = clean(r.get("headline"))
        detail = clean(r.get("detail"))
        supporting = clean(r.get("supporting_data"))
        reason = detail or supporting or headline or "Validated returning-production study signal."
        extras = {
            "signal_group": clean(r.get("signal_group")) or "Returning Production",
            "signal_type": clean(r.get("signal_type")),
            "market": clean(r.get("market")) or "Spread",
            "period": clean(r.get("period")) or "Full Game",
            "opponent": clean(r.get("opponent")),
            "direction": clean(r.get("direction")) or team,
            "rp_strength": clean(r.get("strength")),
            "confidence": clean(r.get("confidence")),
            "headline": headline,
            "detail": detail,
            "supporting_data": supporting,
            "source": clean(r.get("source")),
            "historical_games": num(r.get("historical_games")),
            "historical_ats_record": clean(r.get("historical_ats_record")),
            "historical_ats_pct": num(r.get("historical_ats_pct")),
            "historical_avg_ats_margin": num(r.get("historical_avg_ats_margin")),
        }
        add_angle(rows, g, "rp_support", "Returning production study", team, reason,
                  abs(score), clean(r.get("confidence")).lower() or "medium",
                  abs(score), extras=extras)

def add_travel(rows, by_id):
    if not TRAVEL_1H.exists():
        return
    df = pd.read_csv(TRAVEL_1H)
    for _, r in df.iterrows():
        gid = clean(r.get("game_id"))
        g = by_id.get(gid)
        if g is None:
            g = r
        side = clean(r.get("spread_side"))
        badge = clean(r.get("spread_badge"))
        title = clean(r.get("spread_title"))
        tz = num(r.get("tz_abs"))
        reason = f"{badge}: {title}" if title else badge
        add_angle(rows, g, "travel_1h", "Travel / 1H travel angle", side, reason, tz, "medium", tz)

def add_coach(rows, by_id):
    """Add canonical coach role/period ATS support and fade signals.

    Full game requires at least 25 games. First- and second-half signals require
    at least 12 games. A signal must clear both the ATS-rate and average-margin
    thresholds. Negative coach performance supports the opponent.
    """
    if not COACH_CONTEXT.exists():
        return

    df = pd.read_csv(COACH_CONTEXT)
    df = df[df["is_applicable"].astype(str).str.lower().isin(["true", "1", "yes"])].copy()
    df["avg_ats_margin_num"] = pd.to_numeric(df["avg_ats_margin"], errors="coerce")
    df["games_num"] = pd.to_numeric(df["games"], errors="coerce")
    df["ats_win_pct_num"] = pd.to_numeric(df["ats_win_pct"], errors="coerce")

    def opponent_for(g, team):
        away = clean(g.get("away_team"))
        home = clean(g.get("home_team"))
        if norm_team(team) == norm_team(away):
            return home
        if norm_team(team) == norm_team(home):
            return away
        return ""

    period_rules = {
        "Full Game": {"minimum": 25, "key": "coach_ats", "label": "Coach ATS"},
        "1H": {"minimum": 12, "key": "coach_1h", "label": "Coach 1H"},
        "2H": {"minimum": 12, "key": "coach_2h", "label": "Coach 2H"},
    }

    for period, rule in period_rules.items():
        candidates = df[
            df["period"].astype(str).eq(period)
            & (df["games_num"] >= rule["minimum"])
        ].copy()

        for _, r in candidates.iterrows():
            games = num(r.get("games"))
            margin = num(r.get("avg_ats_margin"))
            rate = num(r.get("ats_win_pct"))
            if not np.isfinite(games) or not np.isfinite(margin) or not np.isfinite(rate):
                continue

            # Normalize percentages that may be stored as 55.0 instead of 0.55.
            rate_decimal = rate / 100.0 if rate > 1.01 else rate
            positive = rate_decimal >= 0.55 and margin >= 1.5
            negative = rate_decimal <= 0.45 and margin <= -1.5
            if not positive and not negative:
                continue

            g = by_id.get(clean(r.get("game_id")))
            if g is None:
                g = r

            coach_team = clean(r.get("team"))
            supported_team = coach_team if positive else opponent_for(g, coach_team)
            if not supported_team:
                continue

            role = clean(r.get("fav_dog"))
            record = clean(r.get("ats_record"))
            pct_text = f"{rate_decimal * 100:.1f}%"
            margin_text = f"{margin:+.1f}"
            direction = "support" if positive else "fade"
            reason = (
                f"{clean(r.get('coach'))} {period} {role}: {record} ATS "
                f"({pct_text}), avg ATS margin {margin_text} over {int(games)} games. "
                f"{'Supports ' + coach_team if positive else 'Supports ' + supported_team + ' by fading ' + coach_team}."
            )

            tier = "high" if (
                (positive and rate_decimal >= 0.58 and margin >= 2.0)
                or (negative and rate_decimal <= 0.42 and margin <= -2.0)
            ) else "medium"

            add_angle(
                rows,
                g,
                rule["key"],
                f"{rule['label']} {direction}",
                supported_team,
                reason,
                abs(margin),
                tier,
                abs(margin),
            )

def add_injuries(rows, by_id):
    if not INJURY_GAMES.exists():
        return
    df = pd.read_csv(INJURY_GAMES)
    for _, r in df.iterrows():
        score = num(r.get("game_injury_score"))
        summary = clean(r.get("injury_summary"))
        tier = clean(r.get("game_injury_tier")).lower()
        if not np.isfinite(score) or score <= 0:
            continue
        g = by_id.get(clean(r.get("game_id")))
        if g is None:
            g = r
        reason = summary or f"Game injury score {score:.1f}."
        add_angle(rows, g, "injury", "Injury alert", "", reason, score, tier or "high", score)

def add_pbp_movement(rows, by_id):
    if not PBP_MOVEMENT.exists():
        return
    df = pd.read_csv(PBP_MOVEMENT)
    for _, r in df.iterrows():
        gid = clean(r.get("game_id"))
        g = by_id.get(gid)
        if g is None:
            g = r
        status = clean(r.get("status"))
        label = clean(r.get("signal_label"))
        reason = clean(r.get("reason"))
        if status == "expected_move_already_started":
            reason += " Expected movement has already started; monitor rather than chase."
        add_angle(rows, g, clean(r.get("signal_key")), label, clean(r.get("side_team")), reason,
                  abs(num(r.get("historical_mean_clv"))), "high", abs(num(r.get("historical_mean_clv"))))

def add_cross_book_movement(rows, by_match):
    if not CROSS_BOOK.exists():
        return
    df = pd.read_csv(CROSS_BOOK)
    for _, r in df.iterrows():
        key = (clean(r.get("date")), norm_team(r.get("away_team")), norm_team(r.get("home_team")))
        g = by_match.get(key)
        if g is None:
            target_date = pd.to_datetime(r.get("date"), errors="coerce")
            candidates = []
            for (date, away, home), candidate in by_match.items():
                candidate_date = pd.to_datetime(date, errors="coerce")
                if pd.isna(target_date) or pd.isna(candidate_date) or abs((candidate_date - target_date).days) > 1:
                    continue
                score = SequenceMatcher(None, key[1], away).ratio() + SequenceMatcher(None, key[2], home).ratio()
                candidates.append((score, candidate))
            if candidates and max(candidates, key=lambda x: x[0])[0] >= 1.35:
                g = max(candidates, key=lambda x: x[0])[1]
        if g is None:
            continue
        reason = clean(r.get("reason"))
        if clean(r.get("status")) == "expected_move_already_started":
            reason += " Expected move has already started; do not chase."
        add_angle(rows, g, clean(r.get("signal_key")), clean(r.get("signal_label")), clean(r.get("side_team")),
                  reason, abs(num(r.get("historical_mean_move"))), "high", abs(num(r.get("historical_mean_move"))))

def dedupe(out):
    if out.empty:
        return out
    out["_dedupe_key"] = (
        out["game_id"].astype(str) + "|" +
        out["angle_key"].astype(str) + "|" +
        out["side_team"].astype(str) + "|" +
        out["reason"].astype(str).str.slice(0, 80)
    )
    out = out.sort_values(["angle_key","sort_score","week","date"], ascending=[True,False,True,True])
    out = out.drop_duplicates("_dedupe_key", keep="first").drop(columns=["_dedupe_key"])
    return out

def main():
    games = load_games()
    by_id, by_match = make_game_lookup(games)

    var = pd.read_csv(VAR)
    var_by_team = {r["team"]: r.to_dict() for _, r in var.iterrows()}

    rows = []
    add_ratings_variance(rows, games, var_by_team)
    add_near_pick(rows, games)
    add_rp_badges(rows, by_match)
    add_travel(rows, by_id)
    add_coach(rows, by_id)
    add_injuries(rows, by_id)
    add_pbp_movement(rows, by_id)
    add_cross_book_movement(rows, by_match)

    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame(columns=[
            "game_id","week","date","away_team","home_team","angle_key","angle_label",
            "side_team","reason","metric_value","tier","sort_score"
        ])

    out = dedupe(out)
    out = out.sort_values(["angle_key","sort_score","week","date"], ascending=[True,False,True,True])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"wrote {OUT}: {len(out)} rows")
    if len(out):
        print()
        print("Counts by angle:")
        print(out["angle_key"].value_counts().to_string())
        print()
        print("Sample:")
        print(out.head(60).to_string(index=False))

if __name__ == "__main__":
    main()
