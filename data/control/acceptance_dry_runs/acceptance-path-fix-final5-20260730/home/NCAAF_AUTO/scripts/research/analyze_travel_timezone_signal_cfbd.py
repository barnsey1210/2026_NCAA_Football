#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np

SRC = Path("data/coach/coach_full_game_fav_dog_cfbd_game_rows.csv")
OUT_GAMES = Path("data/research/travel_timezone_signal_cfbd_games.csv")
OUT_SUMMARY = Path("data/research/travel_timezone_signal_cfbd_summary.csv")

TEAM_TZ = {
    "Hawaii": -10,

    "Washington": -8, "Washington State": -8, "Oregon": -8, "Oregon State": -8,
    "California": -8, "Cal": -8, "Stanford": -8, "San Jose State": -8, "Fresno State": -8,
    "San Diego State": -8, "UCLA": -8, "USC": -8, "UNLV": -8, "Nevada": -8,

    "Arizona": -7, "Arizona State": -7, "Boise State": -7, "BYU": -7, "Utah": -7,
    "Utah State": -7, "Colorado": -7, "Colorado State": -7, "Air Force": -7,
    "Wyoming": -7, "New Mexico": -7, "New Mexico State": -7, "UTEP": -7,

    "Texas": -6, "Texas A&M": -6, "Texas Tech": -6, "Baylor": -6, "TCU": -6,
    "SMU": -6, "Houston": -6, "Rice": -6, "North Texas": -6, "UTSA": -6,
    "Texas State": -6, "Sam Houston": -6,
    "Oklahoma": -6, "Oklahoma State": -6, "Tulsa": -6,
    "Kansas": -6, "Kansas State": -6,
    "Nebraska": -6, "Iowa": -6, "Iowa State": -6,
    "Minnesota": -6, "Wisconsin": -6, "Illinois": -6, "Northwestern": -6,
    "Northern Illinois": -6,
    "Missouri": -6, "Arkansas": -6, "Arkansas State": -6,
    "LSU": -6, "Louisiana": -6, "Louisiana Tech": -6, "UL-Monroe": -6, "Tulane": -6,
    "Memphis": -6, "Middle Tennessee": -6, "Vanderbilt": -6,
    "Alabama": -6, "Auburn": -6, "South Alabama": -6, "Troy": -6,
    "Ole Miss": -6, "Mississippi State": -6, "Southern Miss": -6,
    "UAB": -6, "Jacksonville State": -6, "Western Kentucky": -6,

    "Florida": -5, "Florida State": -5, "Miami": -5, "Miami-FL": -5, "UCF": -5,
    "South Florida": -5, "Florida Atlantic": -5, "FIU": -5,
    "Georgia": -5, "Georgia Tech": -5, "Georgia State": -5, "Georgia Southern": -5,
    "Clemson": -5, "South Carolina": -5, "Coastal Carolina": -5,
    "North Carolina": -5, "NC State": -5, "Duke": -5, "Wake Forest": -5,
    "East Carolina": -5, "Charlotte": -5, "Appalachian State": -5,
    "Virginia": -5, "Virginia Tech": -5, "Old Dominion": -5, "Liberty": -5, "James Madison": -5,
    "Maryland": -5, "Navy": -5,
    "Penn State": -5, "Pittsburgh": -5, "Temple": -5,
    "Rutgers": -5, "Syracuse": -5, "Buffalo": -5, "Army": -5,
    "Boston College": -5, "Massachusetts": -5, "UConn": -5, "Connecticut": -5,
    "Ohio State": -5, "Cincinnati": -5, "Miami-OH": -5, "Miami (OH)": -5, "Ohio": -5,
    "Bowling Green": -5, "Toledo": -5, "Kent State": -5, "Akron": -5,
    "Michigan": -5, "Michigan State": -5, "Eastern Michigan": -5,
    "Central Michigan": -5, "Western Michigan": -5,
    "Indiana": -5, "Purdue": -5, "Notre Dame": -5, "Ball State": -5,
    "Louisville": -5, "Kentucky": -5, "Marshall": -5, "West Virginia": -5,
}

ALIASES = {
    "Arizona St.": "Arizona State",
    "Arizona St": "Arizona State",
    "Arkansas St.": "Arkansas State",
    "Arkansas St": "Arkansas State",
    "Appalachian St.": "Appalachian State",
    "Appalachian St": "Appalachian State",
    "Boise St": "Boise State",
    "Boise St.": "Boise State",
    "Fresno St.": "Fresno State",
    "Fresno St": "Fresno State",
    "San José State": "San Jose State",
    "Florida Atl.": "Florida Atlantic",
    "Florida Atl": "Florida Atlantic",
    "Florida Int.": "FIU",
    "Florida Int": "FIU",
    "FIU Panthers": "FIU",
    "Connecticut": "UConn",
    "UMass": "Massachusetts",
    "Miami (FL)": "Miami-FL",
    "Miami Florida": "Miami-FL",
    "Miami (OH)": "Miami-OH",
    "UL Monroe": "UL-Monroe",
    "Louisiana Monroe": "UL-Monroe",
}

def clean_team(x):
    if pd.isna(x):
        return ""
    x = str(x).strip()
    return ALIASES.get(x, x)

def rec(series):
    return f"{(series=='W').sum()}-{(series=='L').sum()}-{(series=='P').sum()}"

def ou_rec(series):
    return f"{(series=='O').sum()} O / {(series=='U').sum()} U / {(series=='P').sum()} P"

def pct_win(series):
    denom = series.isin(["W","L"]).sum()
    return round(series.eq("W").sum() / denom * 100, 1) if denom else np.nan

def pct_over(series):
    denom = series.isin(["O","U"]).sum()
    return round(series.eq("O").sum() / denom * 100, 1) if denom else np.nan

def summarize(df, label):
    d = df.copy()
    fav = d[d["traveler_role"] == "Favorite"]
    dog = d[d["traveler_role"] == "Underdog"]

    return {
        "bucket": label,
        "games": len(d),

        "traveler_ats": rec(d["traveler_ats_result"]) if len(d) else "",
        "traveler_ats_win_pct": pct_win(d["traveler_ats_result"]) if len(d) else np.nan,
        "avg_traveler_ats_margin": round(d["traveler_ats_margin"].mean(), 2) if len(d) else np.nan,

        "traveler_fav_ats": rec(fav["traveler_ats_result"]) if len(fav) else "",
        "traveler_fav_ats_win_pct": pct_win(fav["traveler_ats_result"]) if len(fav) else np.nan,
        "avg_traveler_fav_ats_margin": round(fav["traveler_ats_margin"].mean(), 2) if len(fav) else np.nan,

        "traveler_dog_ats": rec(dog["traveler_ats_result"]) if len(dog) else "",
        "traveler_dog_ats_win_pct": pct_win(dog["traveler_ats_result"]) if len(dog) else np.nan,
        "avg_traveler_dog_ats_margin": round(dog["traveler_ats_margin"].mean(), 2) if len(dog) else np.nan,

        "ou_record": ou_rec(d["total_result"]) if len(d) else "",
        "over_pct": pct_over(d["total_result"]) if len(d) else np.nan,
        "avg_total_margin": round(d["total_margin"].mean(), 2) if len(d) else np.nan,
    }

def main():
    if not SRC.exists():
        raise SystemExit(f"Missing {SRC}")

    df = pd.read_csv(SRC, low_memory=False)

    # We only need away team rows for travel signal.
    d = df[df["home_away"].astype(str).str.lower().eq("away")].copy()

    d["team_clean"] = d["team"].map(clean_team)
    d["opponent_clean"] = d["opponent"].map(clean_team)

    d["away_tz"] = d["team_clean"].map(TEAM_TZ)
    d["home_tz"] = d["opponent_clean"].map(TEAM_TZ)
    d["tz_delta"] = d["home_tz"] - d["away_tz"]
    d["tz_abs"] = d["tz_delta"].abs()
    d["travel_direction"] = np.where(d["tz_delta"] > 0, "Eastbound", np.where(d["tz_delta"] < 0, "Westbound", "Same/no major"))

    d["team_spread"] = pd.to_numeric(d["team_spread"], errors="coerce")
    d["traveler_role"] = np.where(d["team_spread"] < 0, "Favorite", np.where(d["team_spread"] > 0, "Underdog", "Pick"))

    d["traveler_ats_margin"] = pd.to_numeric(d["ats_margin"], errors="coerce")
    d["traveler_ats_result"] = d["ats_result"]

    d["total_line"] = pd.to_numeric(d["total_line"], errors="coerce")
    d["total_points"] = pd.to_numeric(d["total_points"], errors="coerce")
    d["total_margin"] = pd.to_numeric(d["total_margin"], errors="coerce")
    d["total_result"] = d["total_result"]

    known = d[d["away_tz"].notna() & d["home_tz"].notna() & d["traveler_ats_result"].isin(["W","L","P"])].copy()

    known["travel_bucket"] = pd.cut(
        known["tz_abs"],
        bins=[-0.1, 0.1, 1.1, 2.1, 99],
        labels=["0 TZ", "1 TZ", "2 TZ", "3+ TZ"]
    )

    rows = []
    rows.append(summarize(known, "All known TZ road games"))

    for b in ["0 TZ", "1 TZ", "2 TZ", "3+ TZ"]:
        rows.append(summarize(known[known["travel_bucket"].astype(str).eq(b)], f"Away travels {b}"))

    three = known[known["tz_abs"] >= 3]
    rows.append(summarize(three, "3+ TZ all"))
    rows.append(summarize(three[three["travel_direction"].eq("Eastbound")], "3+ TZ eastbound"))
    rows.append(summarize(three[three["travel_direction"].eq("Westbound")], "3+ TZ westbound"))
    rows.append(summarize(three[three["traveler_role"].eq("Favorite")], "3+ TZ traveler favorite"))
    rows.append(summarize(three[three["traveler_role"].eq("Underdog")], "3+ TZ traveler underdog"))

    OUT_GAMES.parent.mkdir(parents=True, exist_ok=True)
    known.to_csv(OUT_GAMES, index=False)
    pd.DataFrame(rows).to_csv(OUT_SUMMARY, index=False)

    print("source rows:", len(df))
    print("away-team rows:", len(d))
    print("known TZ rows:", len(known))
    print("seasons:", known["season"].min(), "-", known["season"].max())
    print("missing teams:", sorted(set(d[d["away_tz"].isna()]["team_clean"].dropna()) | set(d[d["home_tz"].isna()]["opponent_clean"].dropna()))[:80])
    print("wrote:", OUT_GAMES)
    print("wrote:", OUT_SUMMARY)
    print()
    print(pd.DataFrame(rows).to_string(index=False))

if __name__ == "__main__":
    main()
