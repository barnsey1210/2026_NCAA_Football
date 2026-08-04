#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np

SRC = Path("SGO/sgo_ncaaf_2024_2025_halves_odds.csv")
OUT_GAMES = Path("data/research/realignment_travel_1h_signal_games.csv")
OUT_SUMMARY = Path("data/research/realignment_travel_1h_signal_summary.csv")

ALIASES = {
    "Hawai'i": "Hawaii",
    "California": "Cal",
    "Miami (FL)": "Miami-FL",
    "Florida Int.": "FIU",
    "Florida International": "FIU",
    "Arizona St.": "Arizona State",
    "Boise St": "Boise State",
    "Fresno St.": "Fresno State",
}

TEAM_TZ = {
    "Hawaii": -10,

    "Washington": -8, "Oregon": -8, "Oregon State": -8, "Washington State": -8,
    "USC": -8, "UCLA": -8, "Stanford": -8, "Cal": -8, "California": -8,
    "San Jose State": -8, "Fresno State": -8, "San Diego State": -8, "Nevada": -8, "UNLV": -8,

    "Arizona": -7, "Arizona State": -7, "Boise State": -7, "BYU": -7, "Utah": -7,
    "Utah State": -7, "Colorado": -7, "Colorado State": -7, "Air Force": -7,
    "Wyoming": -7, "New Mexico": -7, "New Mexico State": -7, "UTEP": -7,

    "Nebraska": -6, "Iowa": -6, "Minnesota": -6, "Wisconsin": -6, "Illinois": -6,
    "Northwestern": -6, "Texas": -6, "Texas A&M": -6, "Baylor": -6, "TCU": -6,
    "SMU": -6, "Houston": -6, "Oklahoma": -6, "Oklahoma State": -6, "Kansas": -6,
    "Kansas State": -6, "Missouri": -6, "Arkansas": -6, "LSU": -6, "Tulane": -6,
    "Memphis": -6, "Alabama": -6, "Auburn": -6, "Mississippi State": -6, "Ole Miss": -6,

    "Michigan": -5, "Michigan State": -5, "Ohio State": -5, "Penn State": -5,
    "Rutgers": -5, "Maryland": -5, "Indiana": -5, "Purdue": -5,
    "Boston College": -5, "Syracuse": -5, "Pittsburgh": -5, "Virginia": -5,
    "Virginia Tech": -5, "North Carolina": -5, "NC State": -5, "Duke": -5,
    "Wake Forest": -5, "Clemson": -5, "Georgia Tech": -5, "Florida State": -5,
    "Miami-FL": -5, "Louisville": -5,
}

BIG_TEN_2024 = {
    "Illinois", "Indiana", "Iowa", "Maryland", "Michigan", "Michigan State",
    "Minnesota", "Nebraska", "Northwestern", "Ohio State", "Oregon", "Penn State",
    "Purdue", "Rutgers", "UCLA", "USC", "Washington", "Wisconsin"
}

ACC_2024 = {
    "Boston College", "Cal", "California", "Clemson", "Duke", "Florida State",
    "Georgia Tech", "Louisville", "Miami-FL", "NC State", "North Carolina",
    "Pittsburgh", "SMU", "Stanford", "Syracuse", "Virginia", "Virginia Tech",
    "Wake Forest"
}

WESTERN_REALIGNMENT_TEAMS = {"USC", "UCLA", "Oregon", "Washington", "Stanford", "Cal", "California"}

def clean_team(x):
    if pd.isna(x):
        return ""
    x = str(x).strip()
    return ALIASES.get(x, x)

def ats_result(m):
    if pd.isna(m):
        return None
    if m > 0:
        return "W"
    if m < 0:
        return "L"
    return "P"

def ou_result(m):
    if pd.isna(m):
        return None
    if m > 0:
        return "O"
    if m < 0:
        return "U"
    return "P"

def rec(s):
    return f"{(s=='W').sum()}-{(s=='L').sum()}-{(s=='P').sum()}"

def ou_rec(s):
    return f"{(s=='O').sum()} O / {(s=='U').sum()} U / {(s=='P').sum()} P"

def pct(s, label, valid):
    denom = s.isin(valid).sum()
    return round(s.eq(label).sum() / denom * 100, 1) if denom else np.nan

def summarize(d, label):
    fav = d[d["traveler_role"].eq("Favorite")]
    dog = d[d["traveler_role"].eq("Underdog")]

    return {
        "bucket": label,
        "games": len(d),

        "traveler_1h_ats": rec(d["traveler_1h_ats_result"]) if len(d) else "",
        "traveler_1h_ats_win_pct": pct(d["traveler_1h_ats_result"], "W", ["W", "L"]) if len(d) else np.nan,
        "avg_traveler_1h_ats_margin": round(d["traveler_1h_ats_margin"].mean(), 2) if len(d) else np.nan,

        "traveler_fav_1h_ats": rec(fav["traveler_1h_ats_result"]) if len(fav) else "",
        "traveler_fav_1h_ats_win_pct": pct(fav["traveler_1h_ats_result"], "W", ["W", "L"]) if len(fav) else np.nan,
        "avg_traveler_fav_1h_ats_margin": round(fav["traveler_1h_ats_margin"].mean(), 2) if len(fav) else np.nan,

        "traveler_dog_1h_ats": rec(dog["traveler_1h_ats_result"]) if len(dog) else "",
        "traveler_dog_1h_ats_win_pct": pct(dog["traveler_1h_ats_result"], "W", ["W", "L"]) if len(dog) else np.nan,
        "avg_traveler_dog_1h_ats_margin": round(dog["traveler_1h_ats_margin"].mean(), 2) if len(dog) else np.nan,

        "one_h_ou_record": ou_rec(d["one_h_total_result_calc"]) if len(d) else "",
        "one_h_over_pct": pct(d["one_h_total_result_calc"], "O", ["O", "U"]) if len(d) else np.nan,
        "avg_one_h_total_margin": round(d["one_h_total_margin"].mean(), 2) if len(d) else np.nan,
    }

def main():
    df = pd.read_csv(SRC, low_memory=False)

    d = df.copy()
    d = d[d["completed"].astype(str).str.lower().eq("true") | d["completed"].eq(True)].copy()

    d["away_team_clean"] = d["away_team"].map(clean_team)
    d["home_team_clean"] = d["home_team"].map(clean_team)

    d["away_tz"] = d["away_team_clean"].map(TEAM_TZ)
    d["home_tz"] = d["home_team_clean"].map(TEAM_TZ)
    d["tz_delta"] = d["home_tz"] - d["away_tz"]
    d["tz_abs"] = d["tz_delta"].abs()
    d["travel_direction"] = np.where(d["tz_delta"] > 0, "Eastbound", np.where(d["tz_delta"] < 0, "Westbound", "Same/no major"))

    d["season_year"] = pd.to_numeric(d["season_year"], errors="coerce")
    d["away_1h_spread"] = pd.to_numeric(d["away_1h_spread"], errors="coerce")
    d["away_game_spread"] = pd.to_numeric(d["away_game_spread"], errors="coerce")

    d["away_1h_margin"] = pd.to_numeric(d["away_1h_points"], errors="coerce") - pd.to_numeric(d["home_1h_points"], errors="coerce")
    d["traveler_1h_ats_margin"] = d["away_1h_margin"] + d["away_1h_spread"]
    d["traveler_1h_ats_result"] = d["traveler_1h_ats_margin"].map(ats_result)

    d["one_h_total_margin"] = pd.to_numeric(d["one_h_total_points"], errors="coerce") - pd.to_numeric(d["one_h_total"], errors="coerce")
    d["one_h_total_result_calc"] = d["one_h_total_margin"].map(ou_result)

    d["traveler_role"] = np.where(d["away_game_spread"] < 0, "Favorite", np.where(d["away_game_spread"] > 0, "Underdog", "Pick"))

    d["conference_family_2024"] = np.where(
        d["away_team_clean"].isin(BIG_TEN_2024) & d["home_team_clean"].isin(BIG_TEN_2024),
        "Big Ten 2024 alignment",
        np.where(
            d["away_team_clean"].isin(ACC_2024) & d["home_team_clean"].isin(ACC_2024),
            "ACC 2024 alignment",
            "Other"
        )
    )

    d["in_2024_alignment_conf_game"] = d["conference_family_2024"].ne("Other")
    d["involves_western_realignment_team"] = d["away_team_clean"].isin(WESTERN_REALIGNMENT_TEAMS) | d["home_team_clean"].isin(WESTERN_REALIGNMENT_TEAMS)

    known = d[
        d["away_tz"].notna() &
        d["home_tz"].notna() &
        d["traveler_1h_ats_result"].isin(["W", "L", "P"])
    ].copy()

    recent = known[known["season_year"].isin([2024, 2025])].copy()
    conf = recent[recent["in_2024_alignment_conf_game"]].copy()
    conf_3tz = conf[conf["tz_abs"] >= 3].copy()
    realign_3tz = conf_3tz[conf_3tz["involves_western_realignment_team"]].copy()

    rows = [
        summarize(recent, "2024-25 all road games"),
        summarize(recent[recent["tz_abs"] >= 3], "2024-25 all 3+ TZ road games"),
        summarize(conf, "2024-25 Big Ten/ACC alignment road games"),
        summarize(conf_3tz, "2024-25 Big Ten/ACC 3+ TZ road games"),
        summarize(conf_3tz[conf_3tz["travel_direction"].eq("Eastbound")], "2024-25 Big Ten/ACC 3+ TZ eastbound"),
        summarize(conf_3tz[conf_3tz["travel_direction"].eq("Westbound")], "2024-25 Big Ten/ACC 3+ TZ westbound"),
        summarize(realign_3tz[realign_3tz["away_team_clean"].isin(WESTERN_REALIGNMENT_TEAMS)], "Western expansion team travels 3+ TZ"),
        summarize(realign_3tz[realign_3tz["home_team_clean"].isin(WESTERN_REALIGNMENT_TEAMS)], "Non-west team travels 3+ TZ to western expansion team"),
    ]

    OUT_GAMES.parent.mkdir(parents=True, exist_ok=True)
    realign_3tz.to_csv(OUT_GAMES, index=False)
    pd.DataFrame(rows).to_csv(OUT_SUMMARY, index=False)

    print("known recent rows:", len(recent))
    print("2024-25 Big Ten/ACC alignment rows:", len(conf))
    print("2024-25 Big Ten/ACC 3+ TZ rows:", len(conf_3tz))
    print()
    print(pd.DataFrame(rows).to_string(index=False))

    print("\nFocused 1H games:")
    cols = [
        "season_year", "starts_at", "away_team_clean", "home_team_clean",
        "conference_family_2024", "travel_direction", "tz_abs",
        "away_1h_spread", "away_1h_margin", "traveler_1h_ats_margin", "traveler_1h_ats_result",
        "one_h_total", "one_h_total_points", "one_h_total_margin", "one_h_total_result_calc",
    ]
    print(realign_3tz[cols].sort_values(["season_year", "starts_at", "away_team_clean"]).to_string(index=False))

if __name__ == "__main__":
    main()
