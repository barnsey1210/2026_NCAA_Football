#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np

SRC = Path("data/coach/coach_full_game_fav_dog_cfbd_game_rows.csv")
OUT_GAMES = Path("data/research/realignment_travel_signal_games.csv")
OUT_SUMMARY = Path("data/research/realignment_travel_signal_summary.csv")

ALIASES = {
    "Hawai'i": "Hawaii",
    "App State": "Appalachian State",
    "Arizona St.": "Arizona State",
    "Arizona St": "Arizona State",
    "Arkansas St.": "Arkansas State",
    "Arkansas St": "Arkansas State",
    "Boise St": "Boise State",
    "Boise St.": "Boise State",
    "Fresno St.": "Fresno State",
    "Fresno St": "Fresno State",
    "Florida International": "FIU",
    "Florida Int.": "FIU",
    "Florida Atl.": "Florida Atlantic",
    "San José State": "San Jose State",
    "Connecticut": "UConn",
    "Miami (FL)": "Miami-FL",
    "Miami Florida": "Miami-FL",
    "Miami (OH)": "Miami-OH",
}

TEAM_TZ = {
    "Hawaii": -10,

    # Pacific
    "Washington": -8, "Washington State": -8, "Oregon": -8, "Oregon State": -8,
    "California": -8, "Cal": -8, "Stanford": -8, "San Jose State": -8,
    "Fresno State": -8, "San Diego State": -8, "UCLA": -8, "USC": -8,
    "UNLV": -8, "Nevada": -8, "Idaho": -8,

    # Mountain
    "Arizona": -7, "Arizona State": -7, "Boise State": -7, "BYU": -7,
    "Utah": -7, "Utah State": -7, "Colorado": -7, "Colorado State": -7,
    "Air Force": -7, "Wyoming": -7, "New Mexico": -7, "New Mexico State": -7,
    "UTEP": -7,

    # Central
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
    "Missouri State": -6,

    # Eastern
    "Tennessee": -5,
    "Florida": -5, "Florida State": -5, "Miami-FL": -5, "UCF": -5,
    "South Florida": -5, "Florida Atlantic": -5, "FIU": -5,
    "Georgia": -5, "Georgia Tech": -5, "Georgia State": -5, "Georgia Southern": -5,
    "Kennesaw State": -5,
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
    "Delaware": -5, "Yale": -5,
}

BIG_TEN_2024 = {
    "Illinois", "Indiana", "Iowa", "Maryland", "Michigan", "Michigan State",
    "Minnesota", "Nebraska", "Northwestern", "Ohio State", "Oregon", "Penn State",
    "Purdue", "Rutgers", "UCLA", "USC", "Washington", "Wisconsin"
}

ACC_2024 = {
    "Boston College", "California", "Cal", "Clemson", "Duke", "Florida State",
    "Georgia Tech", "Louisville", "Miami-FL", "NC State", "North Carolina",
    "Pittsburgh", "SMU", "Stanford", "Syracuse", "Virginia", "Virginia Tech",
    "Wake Forest"
}

WESTERN_REALIGNMENT_TEAMS = {
    "USC", "UCLA", "Oregon", "Washington", "California", "Cal", "Stanford"
}

def clean_team(x):
    if pd.isna(x):
        return ""
    x = str(x).strip()
    return ALIASES.get(x, x)

def rec(s):
    return f"{(s=='W').sum()}-{(s=='L').sum()}-{(s=='P').sum()}"

def ou_rec(s):
    return f"{(s=='O').sum()} O / {(s=='U').sum()} U / {(s=='P').sum()} P"

def pct(s, win_label):
    valid = s.isin(["W", "L"]) if win_label == "W" else s.isin(["O", "U"])
    denom = valid.sum()
    return round(s.eq(win_label).sum() / denom * 100, 1) if denom else np.nan

def summarize(d, label):
    fav = d[d["traveler_role"].eq("Favorite")]
    dog = d[d["traveler_role"].eq("Underdog")]
    return {
        "bucket": label,
        "games": len(d),
        "traveler_ats": rec(d["ats_result"]) if len(d) else "",
        "traveler_ats_win_pct": pct(d["ats_result"], "W") if len(d) else np.nan,
        "avg_traveler_ats_margin": round(d["ats_margin"].mean(), 2) if len(d) else np.nan,
        "traveler_fav_ats": rec(fav["ats_result"]) if len(fav) else "",
        "traveler_fav_ats_win_pct": pct(fav["ats_result"], "W") if len(fav) else np.nan,
        "avg_traveler_fav_ats_margin": round(fav["ats_margin"].mean(), 2) if len(fav) else np.nan,
        "traveler_dog_ats": rec(dog["ats_result"]) if len(dog) else "",
        "traveler_dog_ats_win_pct": pct(dog["ats_result"], "W") if len(dog) else np.nan,
        "avg_traveler_dog_ats_margin": round(dog["ats_margin"].mean(), 2) if len(dog) else np.nan,
        "ou_record": ou_rec(d["total_result"]) if len(d) else "",
        "over_pct": pct(d["total_result"], "O") if len(d) else np.nan,
        "avg_total_margin": round(d["total_margin"].mean(), 2) if len(d) else np.nan,
    }

def main():
    df = pd.read_csv(SRC, low_memory=False)

    # Away rows only, because travel burden is on the away team.
    d = df[df["home_away"].astype(str).str.lower().eq("away")].copy()
    d["team_clean"] = d["team"].map(clean_team)
    d["opponent_clean"] = d["opponent"].map(clean_team)

    d["away_tz"] = d["team_clean"].map(TEAM_TZ)
    d["home_tz"] = d["opponent_clean"].map(TEAM_TZ)
    d["tz_delta"] = d["home_tz"] - d["away_tz"]
    d["tz_abs"] = d["tz_delta"].abs()
    d["travel_direction"] = np.where(d["tz_delta"] > 0, "Eastbound", np.where(d["tz_delta"] < 0, "Westbound", "Same/no major"))

    d["season"] = pd.to_numeric(d["season"], errors="coerce")
    d["team_spread"] = pd.to_numeric(d["team_spread"], errors="coerce")
    d["ats_margin"] = pd.to_numeric(d["ats_margin"], errors="coerce")
    d["total_margin"] = pd.to_numeric(d["total_margin"], errors="coerce")

    d["traveler_role"] = np.where(d["team_spread"] < 0, "Favorite", np.where(d["team_spread"] > 0, "Underdog", "Pick"))
    d["conference_family_2024"] = np.where(
        d["team_clean"].isin(BIG_TEN_2024) & d["opponent_clean"].isin(BIG_TEN_2024),
        "Big Ten 2024 alignment",
        np.where(
            d["team_clean"].isin(ACC_2024) & d["opponent_clean"].isin(ACC_2024),
            "ACC 2024 alignment",
            "Other"
        )
    )
    d["in_2024_alignment_conf_game"] = d["conference_family_2024"].ne("Other")
    d["involves_western_realignment_team"] = d["team_clean"].isin(WESTERN_REALIGNMENT_TEAMS) | d["opponent_clean"].isin(WESTERN_REALIGNMENT_TEAMS)

    known = d[
        d["away_tz"].notna() &
        d["home_tz"].notna() &
        d["ats_result"].isin(["W", "L", "P"])
    ].copy()

    recent = known[known["season"].isin([2024, 2025])].copy()
    conf = recent[recent["in_2024_alignment_conf_game"]].copy()
    conf_3tz = conf[conf["tz_abs"] >= 3].copy()
    realign_3tz = conf_3tz[conf_3tz["involves_western_realignment_team"]].copy()

    rows = []
    rows.append(summarize(recent, "2024-25 all road games"))
    rows.append(summarize(recent[recent["tz_abs"] >= 3], "2024-25 all 3+ TZ road games"))
    rows.append(summarize(conf, "2024-25 Big Ten/ACC alignment road games"))
    rows.append(summarize(conf_3tz, "2024-25 Big Ten/ACC 3+ TZ road games"))
    rows.append(summarize(conf_3tz[conf_3tz["travel_direction"].eq("Eastbound")], "2024-25 Big Ten/ACC 3+ TZ eastbound"))
    rows.append(summarize(conf_3tz[conf_3tz["travel_direction"].eq("Westbound")], "2024-25 Big Ten/ACC 3+ TZ westbound"))
    rows.append(summarize(realign_3tz, "2024-25 Big Ten/ACC 3+ TZ involving western expansion team"))
    rows.append(summarize(realign_3tz[realign_3tz["team_clean"].isin(WESTERN_REALIGNMENT_TEAMS)], "Western expansion team travels 3+ TZ"))
    rows.append(summarize(realign_3tz[realign_3tz["opponent_clean"].isin(WESTERN_REALIGNMENT_TEAMS)], "Non-west team travels 3+ TZ to western expansion team"))

    OUT_GAMES.parent.mkdir(parents=True, exist_ok=True)
    realign_3tz.to_csv(OUT_GAMES, index=False)
    pd.DataFrame(rows).to_csv(OUT_SUMMARY, index=False)

    print("known recent rows:", len(recent))
    print("2024-25 Big Ten/ACC alignment rows:", len(conf))
    print("2024-25 Big Ten/ACC 3+ TZ rows:", len(conf_3tz))
    print("2024-25 Big Ten/ACC 3+ TZ western realignment rows:", len(realign_3tz))
    print()
    print(pd.DataFrame(rows).to_string(index=False))

    print("\nGames in focused sample:")
    cols = ["season", "date", "team_clean", "opponent_clean", "conference_family_2024", "travel_direction", "tz_abs", "team_spread", "ats_margin", "ats_result", "total_line", "total_margin", "total_result"]
    print(realign_3tz[cols].sort_values(["season", "date", "team_clean"]).to_string(index=False))

if __name__ == "__main__":
    main()
