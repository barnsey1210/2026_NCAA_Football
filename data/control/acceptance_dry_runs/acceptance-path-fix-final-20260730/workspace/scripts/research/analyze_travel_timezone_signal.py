#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np

SRC = Path("SGO/sgo_ncaaf_2024_2025_halves_odds.csv")
OUT_GAMES = Path("data/research/travel_timezone_signal_games.csv")
OUT_SUMMARY = Path("data/research/travel_timezone_signal_summary.csv")

# UTC offsets during football season, simplified by school location.
# This is enough for the core 3+ timezone travel signal.
TEAM_TZ = {
    # Hawaii / Alaska
    "Hawaii": -10,

    # Pacific
    "Washington": -8, "Washington State": -8, "Oregon": -8, "Oregon State": -8,
    "California": -8, "Stanford": -8, "San Jose State": -8, "Fresno State": -8,
    "San Diego State": -8, "UCLA": -8, "USC": -8, "UNLV": -8, "Nevada": -8,

    # Mountain / Arizona
    "Arizona": -7, "Arizona State": -7, "Boise State": -7, "BYU": -7, "Utah": -7,
    "Utah State": -7, "Colorado": -7, "Colorado State": -7, "Air Force": -7,
    "Wyoming": -7, "New Mexico": -7, "New Mexico State": -7, "UTEP": -7,

    # Central
    "Texas": -6, "Texas A&M": -6, "Texas Tech": -6, "Baylor": -6, "TCU": -6,
    "SMU": -6, "Houston": -6, "Rice": -6, "North Texas": -6, "UTSA": -6,
    "Texas State": -6, "Sam Houston": -6,
    "Oklahoma": -6, "Oklahoma State": -6, "Tulsa": -6,
    "Kansas": -6, "Kansas State": -6,
    "Nebraska": -6, "Iowa": -6, "Iowa State": -6,
    "Minnesota": -6, "Wisconsin": -6, "Illinois": -6, "Northwestern": -6,
    "Northern Illinois": -6, "Western Illinois": -6,
    "Missouri": -6, "Arkansas": -6, "Arkansas State": -6,
    "LSU": -6, "Louisiana": -6, "Louisiana Tech": -6, "UL-Monroe": -6, "Tulane": -6,
    "Memphis": -6, "Middle Tennessee": -6, "Vanderbilt": -6,
    "Alabama": -6, "Auburn": -6, "South Alabama": -6, "Troy": -6,
    "Ole Miss": -6, "Mississippi State": -6, "Southern Miss": -6,
    "UAB": -6, "Jacksonville State": -6,

    # Eastern
    "Florida": -5, "Florida State": -5, "Miami-FL": -5, "UCF": -5,
    "South Florida": -5, "Florida Atlantic": -5, "FIU": -5,
    "Georgia": -5, "Georgia Tech": -5, "Georgia State": -5, "Georgia Southern": -5,
    "Clemson": -5, "South Carolina": -5, "Coastal Carolina": -5,
    "North Carolina": -5, "NC State": -5, "Duke": -5, "Wake Forest": -5,
    "East Carolina": -5, "Charlotte": -5, "Appalachian State": -5,
    "Virginia": -5, "Virginia Tech": -5, "Old Dominion": -5, "Liberty": -5, "James Madison": -5,
    "Maryland": -5, "Navy": -5,
    "Penn State": -5, "Pittsburgh": -5, "Temple": -5,
    "Rutgers": -5, "Syracuse": -5, "Buffalo": -5, "Army": -5,
    "Boston College": -5, "Massachusetts": -5, "UConn": -5,
    "Ohio State": -5, "Cincinnati": -5, "Miami-OH": -5, "Ohio": -5,
    "Bowling Green": -5, "Toledo": -5, "Kent State": -5, "Akron": -5,
    "Michigan": -5, "Michigan State": -5, "Eastern Michigan": -5,
    "Central Michigan": -5, "Western Michigan": -5,
    "Indiana": -5, "Purdue": -5, "Notre Dame": -5, "Ball State": -5,
    "Louisville": -5, "Kentucky": -5, "Marshall": -5, "West Virginia": -5,
}

ALIASES = {
    "Hawai'i": "Hawaii",
    "Miami (FL)": "Miami-FL",
    "Miami Florida": "Miami-FL",
    "Miami (OH)": "Miami-OH",
    "UMass": "Massachusetts",
    "Louisiana Monroe": "UL-Monroe",
    "UL Monroe": "UL-Monroe",
    "James Madison": "James Madison",
    "N Dakota St": "North Dakota State",
    "North Dakota State": "North Dakota State",
    "Montana State Bobcats": "Montana State",
    "Arkansas-Pine Bluff Golden Lions": "Arkansas-Pine Bluff",
    "Alabama Crimson Tide": "Alabama",
    "Auburn Tigers": "Auburn",
    "Western Kentucky Hilltoppers": "Western Kentucky",
}

# Add FCS / special teams commonly appearing in the 2024-25 SGO file where needed.
TEAM_TZ.update({
    "North Dakota State": -6,
    "South Dakota State": -6,
    "Montana State": -7,
    "Sacramento State": -8,
    "UAlbany": -5,
    "Bethune-Cookman": -5,
    "Arkansas-Pine Bluff": -6,
})

def team_key(x):
    if pd.isna(x):
        return ""
    x = str(x).strip()
    return ALIASES.get(x, x)

def ats_result_from_margin(margin):
    if pd.isna(margin):
        return None
    if margin > 0:
        return "W"
    if margin < 0:
        return "L"
    return "P"

def ou_result_from_margin(margin):
    if pd.isna(margin):
        return None
    if margin > 0:
        return "O"
    if margin < 0:
        return "U"
    return "P"

def summarize(df, label):
    d = df.copy()
    if d.empty:
        return {
            "bucket": label, "games": 0,
            "traveler_ats": "", "traveler_ats_win_pct": np.nan, "avg_traveler_ats_margin": np.nan,
            "favorite_ats": "", "favorite_ats_win_pct": np.nan, "avg_favorite_ats_margin": np.nan,
            "underdog_ats": "", "underdog_ats_win_pct": np.nan, "avg_underdog_ats_margin": np.nan,
            "ou_record": "", "over_pct": np.nan, "avg_total_margin": np.nan,
            "one_h_traveler_ats": "", "one_h_traveler_ats_win_pct": np.nan,
            "one_h_ou_record": "", "one_h_over_pct": np.nan, "avg_one_h_total_margin": np.nan,
        }

    def rec(series):
        return f"{(series=='W').sum()}-{(series=='L').sum()}-{(series=='P').sum()}"

    def ou_rec(series):
        return f"{(series=='O').sum()} O / {(series=='U').sum()} U / {(series=='P').sum()} P"

    fav = d[d["traveler_role"] == "Favorite"]
    dog = d[d["traveler_role"] == "Underdog"]

    return {
        "bucket": label,
        "games": len(d),

        "traveler_ats": rec(d["traveler_ats_result"]),
        "traveler_ats_win_pct": round((d["traveler_ats_result"].eq("W").sum() / d["traveler_ats_result"].isin(["W","L"]).sum()) * 100, 1) if d["traveler_ats_result"].isin(["W","L"]).sum() else np.nan,
        "avg_traveler_ats_margin": round(d["traveler_ats_margin"].mean(), 2),

        "favorite_ats": rec(fav["traveler_ats_result"]),
        "favorite_ats_win_pct": round((fav["traveler_ats_result"].eq("W").sum() / fav["traveler_ats_result"].isin(["W","L"]).sum()) * 100, 1) if fav["traveler_ats_result"].isin(["W","L"]).sum() else np.nan,
        "avg_favorite_ats_margin": round(fav["traveler_ats_margin"].mean(), 2) if len(fav) else np.nan,

        "underdog_ats": rec(dog["traveler_ats_result"]),
        "underdog_ats_win_pct": round((dog["traveler_ats_result"].eq("W").sum() / dog["traveler_ats_result"].isin(["W","L"]).sum()) * 100, 1) if dog["traveler_ats_result"].isin(["W","L"]).sum() else np.nan,
        "avg_underdog_ats_margin": round(dog["traveler_ats_margin"].mean(), 2) if len(dog) else np.nan,

        "ou_record": ou_rec(d["game_total_result_calc"]),
        "over_pct": round((d["game_total_result_calc"].eq("O").sum() / d["game_total_result_calc"].isin(["O","U"]).sum()) * 100, 1) if d["game_total_result_calc"].isin(["O","U"]).sum() else np.nan,
        "avg_total_margin": round(d["game_total_margin"].mean(), 2),

        "one_h_traveler_ats": rec(d["traveler_1h_ats_result"]),
        "one_h_traveler_ats_win_pct": round((d["traveler_1h_ats_result"].eq("W").sum() / d["traveler_1h_ats_result"].isin(["W","L"]).sum()) * 100, 1) if d["traveler_1h_ats_result"].isin(["W","L"]).sum() else np.nan,

        "one_h_ou_record": ou_rec(d["one_h_total_result_calc"]),
        "one_h_over_pct": round((d["one_h_total_result_calc"].eq("O").sum() / d["one_h_total_result_calc"].isin(["O","U"]).sum()) * 100, 1) if d["one_h_total_result_calc"].isin(["O","U"]).sum() else np.nan,
        "avg_one_h_total_margin": round(d["one_h_total_margin"].mean(), 2),
    }

def main():
    if not SRC.exists():
        raise SystemExit(f"Missing {SRC}")

    df = pd.read_csv(SRC, low_memory=False)
    df = df[df["completed"].astype(str).str.lower().eq("true") | df["completed"].eq(True)].copy()

    df["away_team_clean"] = df["away_team"].map(team_key)
    df["home_team_clean"] = df["home_team"].map(team_key)

    df["away_tz"] = df["away_team_clean"].map(TEAM_TZ)
    df["home_tz"] = df["home_team_clean"].map(TEAM_TZ)
    df["tz_delta"] = df["home_tz"] - df["away_tz"]
    df["tz_abs"] = df["tz_delta"].abs()
    df["travel_direction"] = np.where(df["tz_delta"] > 0, "Eastbound", np.where(df["tz_delta"] < 0, "Westbound", "Same/no major"))

    # Away traveler ATS margin uses away perspective.
    # away spread + away margin = ATS margin.
    df["away_final_margin"] = pd.to_numeric(df["away_final_points"], errors="coerce") - pd.to_numeric(df["home_final_points"], errors="coerce")
    df["traveler_ats_margin"] = df["away_final_margin"] + pd.to_numeric(df["away_game_spread"], errors="coerce")
    df["traveler_ats_result"] = df["traveler_ats_margin"].map(ats_result_from_margin)

    df["traveler_role"] = np.where(pd.to_numeric(df["away_game_spread"], errors="coerce") < 0, "Favorite",
                          np.where(pd.to_numeric(df["away_game_spread"], errors="coerce") > 0, "Underdog", "Pick"))

    df["game_total_margin"] = pd.to_numeric(df["final_total_points"], errors="coerce") - pd.to_numeric(df["game_total"], errors="coerce")
    df["game_total_result_calc"] = df["game_total_margin"].map(ou_result_from_margin)

    df["away_1h_margin"] = pd.to_numeric(df["away_1h_points"], errors="coerce") - pd.to_numeric(df["home_1h_points"], errors="coerce")
    df["traveler_1h_ats_margin"] = df["away_1h_margin"] + pd.to_numeric(df["away_1h_spread"], errors="coerce")
    df["traveler_1h_ats_result"] = df["traveler_1h_ats_margin"].map(ats_result_from_margin)

    df["one_h_total_margin"] = pd.to_numeric(df["one_h_total_points"], errors="coerce") - pd.to_numeric(df["one_h_total"], errors="coerce")
    df["one_h_total_result_calc"] = df["one_h_total_margin"].map(ou_result_from_margin)

    df["travel_bucket"] = pd.cut(
        df["tz_abs"],
        bins=[-0.1, 0.1, 1.1, 2.1, 99],
        labels=["0 TZ", "1 TZ", "2 TZ", "3+ TZ"]
    )

    # Keep only rows where timezone known and full-game spread/total available for main metrics.
    known = df[df["away_tz"].notna() & df["home_tz"].notna()].copy()

    summary_parts = []
    summary_parts.append(summarize(known, "All known TZ road games"))

    for b in ["0 TZ", "1 TZ", "2 TZ", "3+ TZ"]:
        summary_parts.append(summarize(known[known["travel_bucket"].astype(str).eq(b)], f"Away travels {b}"))

    three = known[known["tz_abs"] >= 3].copy()
    summary_parts.append(summarize(three, "3+ TZ all"))
    summary_parts.append(summarize(three[three["travel_direction"].eq("Eastbound")], "3+ TZ eastbound"))
    summary_parts.append(summarize(three[three["travel_direction"].eq("Westbound")], "3+ TZ westbound"))
    summary_parts.append(summarize(three[three["traveler_role"].eq("Favorite")], "3+ TZ traveler favorite"))
    summary_parts.append(summarize(three[three["traveler_role"].eq("Underdog")], "3+ TZ traveler underdog"))

    early = three[pd.to_datetime(three["starts_at"], errors="coerce").dt.hour < 18]  # before 1pm ET-ish in UTC is imperfect; use later if local kickoff added
    summary_parts.append(summarize(early, "3+ TZ early UTC proxy"))

    out_cols = [
        "season_year", "starts_at", "away_team", "home_team",
        "away_tz", "home_tz", "tz_delta", "tz_abs", "travel_direction", "travel_bucket",
        "away_game_spread", "traveler_role", "away_final_margin",
        "traveler_ats_margin", "traveler_ats_result",
        "game_total", "final_total_points", "game_total_margin", "game_total_result_calc",
        "away_1h_spread", "traveler_1h_ats_margin", "traveler_1h_ats_result",
        "one_h_total", "one_h_total_points", "one_h_total_margin", "one_h_total_result_calc",
    ]

    OUT_GAMES.parent.mkdir(parents=True, exist_ok=True)
    known[out_cols].to_csv(OUT_GAMES, index=False)
    pd.DataFrame(summary_parts).to_csv(OUT_SUMMARY, index=False)

    print("rows raw:", len(df))
    print("rows with known TZ:", len(known))
    print("missing away TZ teams:", sorted(df[df["away_tz"].isna()]["away_team_clean"].dropna().unique())[:50])
    print("missing home TZ teams:", sorted(df[df["home_tz"].isna()]["home_team_clean"].dropna().unique())[:50])
    print("wrote:", OUT_GAMES)
    print("wrote:", OUT_SUMMARY)
    print()
    print(pd.DataFrame(summary_parts).to_string(index=False))

if __name__ == "__main__":
    main()
