#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.signals.build_returning_production_spplus_signals import (
    load_hist_rp,
    pull_games,
    team_key,
    classify_role,
    ats_result,
)

OUT = Path("data/research/returning_production_threshold_sensitivity.csv")
OUT_DETAILS = Path("data/research/returning_production_threshold_sensitivity_games.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

THRESHOLDS = [
    (0.75, 0.25, "top25_bottom25"),
    (0.70, 0.30, "top30_bottom30"),
    (0.67, 0.33, "top33_bottom33"),
    (0.65, 0.35, "top35_bottom35"),
    (0.60, 0.40, "top40_bottom40"),
]

GAPS = [10, 15, 20, 25, 30]

SPREAD_BUCKETS = [
    (-999, -21.5, "favorite_22plus"),
    (-21.5, -14.5, "favorite_15_to_21"),
    (-14.5, -7.5, "favorite_8_to_14"),
    (-7.5, -0.5, "favorite_1_to_7"),
    (0.5, 7.5, "underdog_1_to_7"),
    (7.5, 14.5, "underdog_8_to_14"),
    (14.5, 21.5, "underdog_15_to_21"),
    (21.5, 999, "underdog_22plus"),
]

def spread_bucket(spread):
    if pd.isna(spread):
        return "unknown"
    for lo, hi, name in SPREAD_BUCKETS:
        if lo <= spread < hi:
            return name
    return "unknown"

def prep_games(games, rp):
    rp_small = rp[[
        "season", "team", "team_key",
        "overall", "overall_rank",
        "offense", "offense_rank",
        "defense", "defense_rank"
    ]].copy()

    g = games.copy()
    g["home_key"] = g["home_team"].map(team_key)
    g["away_key"] = g["away_team"].map(team_key)

    g = g.merge(
        rp_small.add_prefix("home_rp_").rename(columns={
            "home_rp_season": "season",
            "home_rp_team_key": "home_key"
        }),
        on=["season", "home_key"],
        how="left"
    ).merge(
        rp_small.add_prefix("away_rp_").rename(columns={
            "away_rp_season": "season",
            "away_rp_team_key": "away_key"
        }),
        on=["season", "away_key"],
        how="left"
    )

    rows = []
    for _, x in g.iterrows():
        for side, opp in [("home", "away"), ("away", "home")]:
            spread = x[f"{side}_spread"]
            ats_margin = x[f"{side}_ats_margin"]

            rows.append({
                "season": x["season"],
                "week": x["week"],
                "date": x["date"],
                "game_id": x["game_id"],
                "team": x[f"{side}_team"],
                "opponent": x[f"{opp}_team"],
                "side": side,
                "role": classify_role(spread),
                "spread": spread,
                "spread_bucket": spread_bucket(spread),
                "ats_margin": ats_margin,
                "ats_result": ats_result(ats_margin),

                "team_overall": x[f"{side}_rp_overall"],
                "team_offense": x[f"{side}_rp_offense"],
                "team_defense": x[f"{side}_rp_defense"],
                "opp_overall": x[f"{opp}_rp_overall"],
                "opp_offense": x[f"{opp}_rp_offense"],
                "opp_defense": x[f"{opp}_rp_defense"],

                "overall_gap": x[f"{side}_rp_overall"] - x[f"{opp}_rp_overall"],
                "off_vs_def_gap": x[f"{side}_rp_offense"] - x[f"{opp}_rp_defense"],
                "def_vs_off_gap": x[f"{side}_rp_defense"] - x[f"{opp}_rp_offense"],
            })

    return pd.DataFrame(rows)

def summarize(df, label, group_cols):
    if df.empty:
        return None

    s = df.groupby(group_cols, dropna=False).agg(
        games=("game_id", "count"),
        ats_w=("ats_result", lambda x: int((x == "W").sum())),
        ats_l=("ats_result", lambda x: int((x == "L").sum())),
        ats_p=("ats_result", lambda x: int((x == "P").sum())),
        avg_ats_margin=("ats_margin", "mean"),
        avg_spread=("spread", "mean"),
        median_spread=("spread", "median"),
    ).reset_index()

    denom = s["ats_w"] + s["ats_l"]
    s["ats_pct"] = np.where(denom > 0, s["ats_w"] / denom, np.nan)
    s["ats_record"] = s["ats_w"].astype(str) + "-" + s["ats_l"].astype(str) + "-" + s["ats_p"].astype(str)
    s.insert(0, "test", label)
    return s

def main():
    rp = load_hist_rp()
    games = pull_games()
    base = prep_games(games, rp)
    base = base.dropna(subset=["team_overall", "team_offense", "team_defense", "opp_overall", "opp_offense", "opp_defense", "ats_margin"])

    all_summaries = []
    detail_rows = []

    # Percentile threshold tests
    for hi, lo, name in THRESHOLDS:
        tmp = base.copy()

        for metric in ["overall", "offense", "defense"]:
            tmp[f"team_{metric}_pct"] = tmp.groupby("season")[f"team_{metric}"].rank(pct=True)
            tmp[f"opp_{metric}_pct"] = tmp.groupby("season")[f"opp_{metric}"].rank(pct=True)

        cases = [
            ("overall_high_low", (tmp["team_overall_pct"] >= hi) & (tmp["opp_overall_pct"] <= lo)),
            ("offense_high_vs_def_low", (tmp["team_offense_pct"] >= hi) & (tmp["opp_defense_pct"] <= lo)),
            ("defense_high_vs_off_low", (tmp["team_defense_pct"] >= hi) & (tmp["opp_offense_pct"] <= lo)),
        ]

        for case, mask in cases:
            d = tmp[mask].copy()
            d["case"] = case
            d["threshold"] = name
            detail_rows.append(d)

            s = summarize(
                d,
                f"percentile_{name}_{case}",
                ["case", "threshold", "role"]
            )
            if s is not None:
                all_summaries.append(s)

            s2 = summarize(
                d,
                f"percentile_{name}_{case}_spread_bucket",
                ["case", "threshold", "role", "spread_bucket"]
            )
            if s2 is not None:
                all_summaries.append(s2)

    # Gap tests
    gap_cases = [
        ("overall_gap", "overall_gap"),
        ("off_vs_def_gap", "off_vs_def_gap"),
        ("def_vs_off_gap", "def_vs_off_gap"),
    ]

    for case, gap_col in gap_cases:
        for gap in GAPS:
            d = base[base[gap_col] >= gap].copy()
            d["case"] = case
            d["threshold"] = f"gap_{gap}+"
            detail_rows.append(d)

            s = summarize(d, f"{case}_gap_{gap}", ["case", "threshold", "role"])
            if s is not None:
                all_summaries.append(s)

            s2 = summarize(d, f"{case}_gap_{gap}_spread_bucket", ["case", "threshold", "role", "spread_bucket"])
            if s2 is not None:
                all_summaries.append(s2)

    out = pd.concat(all_summaries, ignore_index=True, sort=False)
    details = pd.concat(detail_rows, ignore_index=True, sort=False)

    # Useful ordering
    out["abs_avg_ats_margin"] = out["avg_ats_margin"].abs()
    out = out.sort_values(["games", "avg_ats_margin"], ascending=[False, False])

    out.to_csv(OUT, index=False)
    details.to_csv(OUT_DETAILS, index=False)

    print("wrote:", OUT, "rows:", len(out))
    print("wrote:", OUT_DETAILS, "rows:", len(details))

    print("\nBest positive buckets, minimum 20 games:")
    cols = ["test","case","threshold","role","spread_bucket","games","ats_record","ats_pct","avg_ats_margin","avg_spread"]
    show = out[out["games"] >= 20].sort_values("avg_ats_margin", ascending=False)
    print(show[cols].head(30).to_string(index=False))

    print("\nWorst fade buckets, minimum 20 games:")
    show = out[out["games"] >= 20].sort_values("avg_ats_margin", ascending=True)
    print(show[cols].head(30).to_string(index=False))

    print("\nAll role-only summaries, minimum 20 games:")
    role_only = out[out["spread_bucket"].isna() if "spread_bucket" in out.columns else [True]*len(out)]
    role_only = out[out["spread_bucket"].isna()] if "spread_bucket" in out.columns else out
    role_only = role_only[role_only["games"] >= 20].sort_values(["case","threshold","role"])
    print(role_only[cols].to_string(index=False))

if __name__ == "__main__":
    main()
