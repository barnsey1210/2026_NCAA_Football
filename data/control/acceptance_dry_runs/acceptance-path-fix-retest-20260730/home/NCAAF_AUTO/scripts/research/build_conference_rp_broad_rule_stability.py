from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

INPUT = BASE / "data/research/conference_rp_broad_rule_games.csv"

OUT_SEASON = BASE / "data/research/conference_rp_broad_rule_season_stability.csv"
OUT_ROLLUP = BASE / "data/research/conference_rp_broad_rule_stability_rollup.csv"
OUT_CANDIDATES = BASE / "data/research/conference_rp_broad_rule_candidates.csv"
OUT_AUDIT = BASE / "data/audits/conference_rp_broad_rule_stability_audit.csv"

MIN_TOTAL_GAMES = 15
MIN_SEASONS = 2


def confidence_tier(games):
    if games >= 50:
        return "Supported"
    if games >= 30:
        return "Promising"
    if games >= 15:
        return "Exploratory"
    return "Insufficient"


def signal_direction(win_pct):
    if pd.isna(win_pct):
        return "Neutral"
    if win_pct >= 0.55:
        return "Back"
    if win_pct <= 0.45:
        return "Fade"
    return "Neutral"


def season_summary(df):
    out = (
        df.groupby(
            ["season", "rp_band", "broad_spread_band"],
            dropna=False,
        )
        .agg(
            games=("rp_team_ats_result", "count"),
            wins=("rp_team_ats_result", lambda x: (x == "W").sum()),
            losses=("rp_team_ats_result", lambda x: (x == "L").sum()),
            pushes=("rp_team_ats_result", lambda x: (x == "P").sum()),
            avg_ats_margin=("rp_team_ats_margin", "mean"),
            avg_clv=("rp_team_clv", "mean"),
            clv_games=("rp_team_clv", "count"),
        )
        .reset_index()
    )

    decisions = out["wins"] + out["losses"]

    out["ats_win_pct"] = (
        out["wins"] / decisions.where(decisions > 0)
    )

    out["ats_edge_pct"] = (
        out["ats_win_pct"] * 100 - 50
    )

    out["season_signal"] = out["ats_win_pct"].apply(signal_direction)

    return out


def rollup_summary(season_df):
    rows = []

    for (rp_band, spread_band), group in season_df.groupby(
        ["rp_band", "broad_spread_band"],
        dropna=False,
    ):
        total_games = int(group["games"].sum())
        total_wins = int(group["wins"].sum())
        total_losses = int(group["losses"].sum())
        total_pushes = int(group["pushes"].sum())

        decisions = total_wins + total_losses
        ats_win_pct = (
            total_wins / decisions
            if decisions > 0
            else pd.NA
        )

        seasons_present = int(group["season"].nunique())
        winning_seasons = int((group["ats_win_pct"] > 0.50).sum())
        losing_seasons = int((group["ats_win_pct"] < 0.50).sum())
        neutral_seasons = int((group["ats_win_pct"] == 0.50).sum())

        positive_margin_seasons = int(
            (group["avg_ats_margin"] > 0).sum()
        )
        negative_margin_seasons = int(
            (group["avg_ats_margin"] < 0).sum()
        )

        avg_season_win_pct = group["ats_win_pct"].mean()
        std_season_win_pct = group["ats_win_pct"].std()

        weighted_avg_margin = (
            (group["avg_ats_margin"] * group["games"]).sum()
            / total_games
            if total_games > 0
            else pd.NA
        )

        total_clv_games = int(group["clv_games"].sum())

        weighted_avg_clv = (
            (group["avg_clv"].fillna(0) * group["clv_games"]).sum()
            / total_clv_games
            if total_clv_games > 0
            else pd.NA
        )

        overall_signal = signal_direction(ats_win_pct)

        consistent_direction = (
            (overall_signal == "Back" and winning_seasons >= 2)
            or
            (overall_signal == "Fade" and losing_seasons >= 2)
        )

        rows.append(
            {
                "rp_band": rp_band,
                "broad_spread_band": spread_band,
                "games": total_games,
                "wins": total_wins,
                "losses": total_losses,
                "pushes": total_pushes,
                "ats_win_pct": ats_win_pct,
                "ats_edge_pct": (
                    ats_win_pct * 100 - 50
                    if pd.notna(ats_win_pct)
                    else pd.NA
                ),
                "avg_ats_margin": weighted_avg_margin,
                "avg_clv": weighted_avg_clv,
                "clv_games": total_clv_games,
                "seasons_present": seasons_present,
                "winning_seasons": winning_seasons,
                "losing_seasons": losing_seasons,
                "neutral_seasons": neutral_seasons,
                "positive_margin_seasons": positive_margin_seasons,
                "negative_margin_seasons": negative_margin_seasons,
                "avg_season_win_pct": avg_season_win_pct,
                "std_season_win_pct": std_season_win_pct,
                "confidence": confidence_tier(total_games),
                "signal": overall_signal,
                "consistent_direction": consistent_direction,
            }
        )

    out = pd.DataFrame(rows)

    if out.empty:
        return out

    return out.sort_values(
        ["games", "ats_win_pct"],
        ascending=[False, False],
        na_position="last",
    )


def main():
    print("Loading broad-rule game detail")

    df = pd.read_csv(INPUT)

    print("Rows loaded:", len(df))

    required = [
        "season",
        "rp_band",
        "broad_spread_band",
        "rp_team_ats_result",
        "rp_team_ats_margin",
        "rp_team_clv",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    season = season_summary(df)
    rollup = rollup_summary(season)

    candidates = rollup[
        (rollup["games"] >= MIN_TOTAL_GAMES)
        &
        (rollup["seasons_present"] >= MIN_SEASONS)
        &
        (rollup["signal"] != "Neutral")
        &
        (rollup["consistent_direction"])
    ].copy()

    candidates["priority_score"] = (
        candidates["ats_edge_pct"].abs()
        *
        (candidates["games"].clip(upper=100) / 100)
        *
        (candidates["seasons_present"] / candidates["seasons_present"].max())
    )

    candidates = candidates.sort_values(
        ["priority_score", "games"],
        ascending=[False, False],
    )

    OUT_SEASON.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    season.to_csv(OUT_SEASON, index=False)
    rollup.to_csv(OUT_ROLLUP, index=False)
    candidates.to_csv(OUT_CANDIDATES, index=False)

    audit = pd.DataFrame(
        [
            {"metric": "detail_rows", "value": len(df)},
            {"metric": "seasons", "value": df["season"].nunique()},
            {"metric": "season_rule_rows", "value": len(season)},
            {"metric": "rollup_rules", "value": len(rollup)},
            {"metric": "candidate_rules", "value": len(candidates)},
            {"metric": "minimum_total_games", "value": MIN_TOTAL_GAMES},
            {"metric": "minimum_seasons", "value": MIN_SEASONS},
        ]
    )

    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("Created:")
    print(OUT_SEASON)
    print(OUT_ROLLUP)
    print(OUT_CANDIDATES)
    print(OUT_AUDIT)

    print()
    print("Stable candidate rules:")

    if candidates.empty:
        print("No broad rules met the stability requirements.")
    else:
        print(candidates.head(50).to_string(index=False))


if __name__ == "__main__":
    main()
