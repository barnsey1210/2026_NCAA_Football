from pathlib import Path
import pandas as pd
import numpy as np
import json

GAMES = Path("data/projections/game_projection_blend_2026.csv")
VAR = Path("data/ratings/ratings_system_variance.csv")
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

def add_angle(rows, g, angle_key, angle_label, side_team, reason, metric_value=np.nan, tier="", sort_score=np.nan):
    rows.append({
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
    })

def main():
    games = pd.read_csv(GAMES)
    var = pd.read_csv(VAR)

    var_by_team = {
        r["team"]: r.to_dict()
        for _, r in var.iterrows()
    }

    rows = []

    for _, g in games.iterrows():
        away = clean(g.get("away_team"))
        home = clean(g.get("home_team"))

        away_v = var_by_team.get(away, {})
        home_v = var_by_team.get(home, {})

        away_range = num(away_v.get("rating_range"))
        home_range = num(home_v.get("rating_range"))
        max_range = np.nanmax([away_range, home_range]) if any(np.isfinite(x) for x in [away_range, home_range]) else np.nan

        # High / medium model variance.
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

        # Coin toss / near pick.
        proj = num(g.get("projected_margin_home"))
        mkt = market_spread_home(g)

        coin_reasons = []
        coin_metric = np.nan

        if np.isfinite(proj) and abs(proj) <= 3.0:
            fav = home if proj >= 0 else away
            coin_reasons.append(f"model spread {fav} -{abs(proj):.1f}")
            coin_metric = abs(proj)

        if np.isfinite(mkt) and abs(mkt) <= 3.0:
            fav = home if mkt <= 0 else away
            coin_reasons.append(f"market spread {fav} -{abs(mkt):.1f}")
            coin_metric = min(coin_metric, abs(mkt)) if np.isfinite(coin_metric) else abs(mkt)

        if coin_reasons:
            add_angle(
                rows, g,
                "coin_toss",
                "Coin toss / near pick",
                "",
                "; ".join(coin_reasons),
                coin_metric,
                "medium",
                3.0 - coin_metric if np.isfinite(coin_metric) else 0,
            )

        # Schedule spot heuristics from existing columns, if present.
        all_text = " ".join(f"{c}:{clean(g.get(c))}" for c in games.columns).lower()

        if "lookahead" in all_text or "look ahead" in all_text or "sandwich" in all_text:
            add_angle(rows, g, "lookahead", "Schedule spot: lookahead", "", "Schedule spot text contains lookahead/sandwich.", np.nan, "medium", 5)

        if "b2b road" in all_text or "back-to-back road" in all_text or "consecutive road" in all_text or "2nd straight road" in all_text:
            add_angle(rows, g, "b2b_road", "Schedule spot: b2b road", "", "Schedule spot text indicates back-to-back/consecutive road game.", np.nan, "medium", 5)

        if "injury alert" in all_text or "injuries" in all_text or "injury" in all_text:
            score_cols = [c for c in games.columns if "injury" in c.lower() and ("score" in c.lower() or "alert" in c.lower())]
            score_vals = [num(g.get(c)) for c in score_cols]
            score_vals = [x for x in score_vals if np.isfinite(x)]
            metric = max(score_vals) if score_vals else np.nan
            add_angle(rows, g, "injury", "Injury alert", "", "Game has injury-related alert/score fields.", metric, "high" if np.isfinite(metric) and metric > 0 else "medium", metric if np.isfinite(metric) else 1)

        # Placeholders that can be upgraded once we normalize coach/RP/travel source files.
        if "rp support" in all_text or "returning production" in all_text or "off_vs_def" in all_text:
            add_angle(rows, g, "rp_support", "Returning production support", "", "Returning production support detected in game fields.", np.nan, "medium", 4)

        if "coach" in all_text and "1h" in all_text:
            add_angle(rows, g, "coach_1h", "Coach 1H support", "", "Coach 1H support detected in game fields.", np.nan, "medium", 4)

        if "coach" in all_text and "ats" in all_text:
            add_angle(rows, g, "coach_ats", "Coach ATS support", "", "Coach ATS support detected in game fields.", np.nan, "medium", 4)

        if "travel" in all_text and "1h" in all_text:
            add_angle(rows, g, "travel_1h", "Travel / 1H travel angle", "", "Travel/1H angle detected in game fields.", np.nan, "medium", 4)

    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame(columns=[
            "game_id","week","date","away_team","home_team","angle_key","angle_label",
            "side_team","reason","metric_value","tier","sort_score"
        ])

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
        print(out.head(40).to_string(index=False))

if __name__ == "__main__":
    main()
