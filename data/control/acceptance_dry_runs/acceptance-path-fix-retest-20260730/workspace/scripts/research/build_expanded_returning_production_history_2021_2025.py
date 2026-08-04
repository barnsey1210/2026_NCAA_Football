from pathlib import Path
import re
import unicodedata
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

RAW_DIR = BASE / "data/research/returning_production_raw"
RAW_2021 = RAW_DIR / "returning_production_2021.txt"
RAW_2022 = RAW_DIR / "returning_production_2022.txt"

RP_2023_2025_FILE = (
    BASE
    / "data/research/returning_production_clv/"
      "returning_production_games_with_clv.csv"
)

CONF_SOURCE = (
    BASE
    / "data/research/conference_matchup_history_2021_2025.csv"
)

MARKET_CANDIDATES = [
    BASE / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv",
    BASE / "data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv",
    BASE / "data/research/conference_matchup_betting_history_2021_2025.csv",
]

OUT_TEAM_RP = (
    BASE
    / "data/research/returning_production_2021_2025_team.csv"
)

OUT_GAMES = (
    BASE
    / "data/research/returning_production_games_2021_2025_expanded.csv"
)

OUT_AUDIT = (
    BASE
    / "data/audits/returning_production_2021_2025_expansion_audit.csv"
)

OUT_UNMATCHED_TEAMS = (
    BASE
    / "data/audits/returning_production_2021_2025_unmatched_teams.csv"
)

WEEKS = {1, 2, 3, 4}


ALIASES = {
    "app st": "Appalachian State",
    "app state": "Appalachian State",
    "appalachian state": "Appalachian State",
    "appalachian st": "Appalachian State",
    "arizona st": "Arizona State",
    "arkansas st": "Arkansas State",
    "ball st": "Ball State",
    "baylor": "Baylor",
    "bgsu": "Bowling Green",
    "boise st": "Boise State",
    "boston coll": "Boston College",
    "bowling green": "Bowling Green",
    "byu": "BYU",
    "c michigan": "Central Michigan",
    "california": "California",
    "central florida": "UCF",
    "central michigan": "Central Michigan",
    "cmu": "Central Michigan",
    "charlotte": "Charlotte",
    "coastal caro": "Coastal Carolina",
    "coastal carolina": "Coastal Carolina",
    "colorado st": "Colorado State",
    "ecu": "East Carolina",
    "e michigan": "Eastern Michigan",
    "emu": "Eastern Michigan",
    "fau": "Florida Atlantic",
    "florida atlantic": "Florida Atlantic",
    "florida intl": "FIU",
    "florida international": "FIU",
    "florida st": "Florida State",
    "fresno st": "Fresno State",
    "ga southern": "Georgia Southern",
    "ga tech": "Georgia Tech",
    "georgia southern": "Georgia Southern",
    "georgia st": "Georgia State",
    "hawaii": "Hawaii",
    "hawai i": "Hawaii",
    "iowa st": "Iowa State",
    "kansas st": "Kansas State",
    "kent st": "Kent State",
    "la tech": "Louisiana Tech",
    "liberty": "Liberty",
    "louisiana": "Louisiana",
    "louisiana tech": "Louisiana Tech",
    "louisville": "Louisville",
    "miami ohio": "Miami (OH)",
    "miami oh": "Miami (OH)",
    "massachusetts": "UMass",
    "michigan st": "Michigan State",
    "middle tenn": "Middle Tennessee",
    "miss st": "Mississippi State",
    "mississippi st": "Mississippi State",
    "mtsu": "Middle Tennessee",
    "n carolina": "North Carolina",
    "n texas": "North Texas",
    "nc st": "NC State",
    "nevada": "Nevada",
    "new mexico st": "New Mexico State",
    "niu": "Northern Illinois",
    "north texas": "North Texas",
    "northern illinois": "Northern Illinois",
    "ohio st": "Ohio State",
    "oklahoma st": "Oklahoma State",
    "oregon st": "Oregon State",
    "penn st": "Penn State",
    "pittsburgh": "Pittsburgh",
    "s alabama": "South Alabama",
    "s carolina": "South Carolina",
    "san diego st": "San Diego State",
    "san jose st": "San Jose State",
    "san jose state": "San Jose State",
    "san josé state": "San Jose State",
    "so miss": "Southern Miss",
    "southern miss": "Southern Miss",
    "texas am": "Texas A&M",
    "texas st": "Texas State",
    "texas tech": "Texas Tech",
    "troy": "Troy",
    "ucf": "UCF",
    "uconn": "UConn",
    "ul monroe": "UL Monroe",
    "ulm": "UL Monroe",
    "umass": "UMass",
    "unlv": "UNLV",
    "usf": "South Florida",
    "utep": "UTEP",
    "utsa": "UTSA",
    "utah st": "Utah State",
    "va tech": "Virginia Tech",
    "w kentucky": "Western Kentucky",
    "w michigan": "Western Michigan",
    "w virginia": "West Virginia",
    "wash st": "Washington State",
    "washington st": "Washington State",
    "west virginia": "West Virginia",
    "wku": "Western Kentucky",
    "wmu": "Western Michigan",
}


def clean_key(value):
    if pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = text.replace("&", " and ")
    text = re.sub(r"[^A-Za-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()

    for suffix in [" university", " college"]:
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()

    return text


def canonical_team(value):
    key = clean_key(value)
    return ALIASES.get(key, str(value).strip())


def parse_rp_text(path, season):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing raw input file: {path}\n"
            f"Create it by copying the {season} table into that file."
        )

    raw_text = path.read_text(encoding="utf-8")

    # Chat/browser copying can collapse the entire table into one long line.
    # Normalize all whitespace and parse records globally instead of line by line.
    normalized = re.sub(r"\s+", " ", raw_text).strip()

    pattern = re.compile(
        r"(?<!\d)"
        r"(\d{1,3})\.\s+"          # overall rank
        r"(.+?)\s+"                # team
        r"(\d{1,3})%\s+"           # overall RP
        r"(\d{1,3})%\s+\((\d{1,3})\)\s+"  # offense RP and rank
        r"(\d{1,3})%\s+\((\d{1,3})\)"     # defense RP and rank
        r"(?=\s+\d{1,3}\.|\s*$)"  # next record or end of file
    )

    rows = []

    for match in pattern.finditer(normalized):
        overall_rank = int(match.group(1))
        raw_team = match.group(2).strip()
        overall = int(match.group(3))
        offense = int(match.group(4))
        offense_rank = int(match.group(5))
        defense = int(match.group(6))
        defense_rank = int(match.group(7))

        rows.append(
            {
                "season": season,
                "team": canonical_team(raw_team),
                "raw_team": raw_team,
                "overall_returning_production": overall,
                "offense_returning_production": offense,
                "defense_returning_production": defense,
                "overall_rank": overall_rank,
                "offense_rank": offense_rank,
                "defense_rank": defense_rank,
                "source": "manual_table",
            }
        )

    parsed = pd.DataFrame(rows)

    expected_minimum = 120

    if len(parsed) < expected_minimum:
        preview = normalized[:500]
        raise ValueError(
            f"Only {len(parsed)} rows parsed from {path}; expected at least "
            f"{expected_minimum}. The source may be incomplete or copied in an "
            f"unexpected format. First 500 normalized characters:\n{preview}"
        )

    duplicate_ranks = parsed["overall_rank"].duplicated().sum()
    if duplicate_ranks:
        raise ValueError(
            f"{path} contains {duplicate_ranks} duplicated overall ranks."
        )

    print(f"{season} parse check: {len(parsed)} rows")
    print(
        f"{season} rank range: "
        f"{parsed['overall_rank'].min()}-{parsed['overall_rank'].max()}"
    )

    return parsed


def derive_2023_2025_team_rp():
    df = pd.read_csv(RP_2023_2025_FILE)

    required = [
        "season",
        "team",
        "opponent",
        "team_overall",
        "team_offense",
        "team_defense",
        "opp_overall",
        "opp_offense",
        "opp_defense",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(
            f"Cannot derive 2023-2025 RP team table. Missing columns: {missing}"
        )

    team_side = df[
        [
            "season",
            "team",
            "team_overall",
            "team_offense",
            "team_defense",
        ]
    ].rename(
        columns={
            "team_overall": "overall_returning_production",
            "team_offense": "offense_returning_production",
            "team_defense": "defense_returning_production",
        }
    )

    opponent_side = df[
        [
            "season",
            "opponent",
            "opp_overall",
            "opp_offense",
            "opp_defense",
        ]
    ].rename(
        columns={
            "opponent": "team",
            "opp_overall": "overall_returning_production",
            "opp_offense": "offense_returning_production",
            "opp_defense": "defense_returning_production",
        }
    )

    out = pd.concat([team_side, opponent_side], ignore_index=True)
    out["team"] = out["team"].apply(canonical_team)
    out["source"] = "derived_from_2023_2025_game_file"

    value_cols = [
        "overall_returning_production",
        "offense_returning_production",
        "defense_returning_production",
    ]

    # Use median in case repeated case rows carry the same team value.
    out = (
        out.groupby(["season", "team"], as_index=False)
        .agg(
            {
                "overall_returning_production": "median",
                "offense_returning_production": "median",
                "defense_returning_production": "median",
                "source": "first",
            }
        )
    )

    # Ranks are recalculated from the full available team table.
    for value_col, rank_col in [
        ("overall_returning_production", "overall_rank"),
        ("offense_returning_production", "offense_rank"),
        ("defense_returning_production", "defense_rank"),
    ]:
        out[rank_col] = (
            out.groupby("season")[value_col]
            .rank(method="min", ascending=False)
            .astype("Int64")
        )

    out["raw_team"] = out["team"]

    return out


def first_existing_market_file():
    for path in MARKET_CANDIDATES:
        if path.exists():
            return path

    raise FileNotFoundError(
        "None of the expected 2021-2025 market-history files exists:\n"
        + "\n".join(str(p) for p in MARKET_CANDIDATES)
    )


def find_col(df, aliases, required=True):
    lookup = {clean_key(c).replace(" ", "_"): c for c in df.columns}

    for alias in aliases:
        key = clean_key(alias).replace(" ", "_")
        if key in lookup:
            return lookup[key]

    if required:
        raise KeyError(
            f"Could not find any of {aliases}. Available columns:\n"
            f"{df.columns.tolist()}"
        )

    return None


def build_directional_market_rows(path):
    raw = pd.read_csv(path)

    season_col = find_col(raw, ["season", "year"])
    week_col = find_col(raw, ["week"])

    team_col = find_col(raw, ["team", "team_name"], required=False)
    opp_col = find_col(raw, ["opponent", "opponent_name"], required=False)

    # Preferred: already one team-side row per game.
    if team_col and opp_col:
        out = pd.DataFrame(
            {
                "season": pd.to_numeric(raw[season_col], errors="coerce"),
                "week": pd.to_numeric(raw[week_col], errors="coerce"),
                "team": raw[team_col].apply(canonical_team),
                "opponent": raw[opp_col].apply(canonical_team),
            }
        )

        optional_map = {
            "date": ["date", "game_date", "start_date"],
            "game_id": ["game_id", "id", "event_id"],
            "spread": [
                "team_closing_spread",
                "closing_spread",
                "spread",
                "team_spread",
            ],
            "ats_result": ["ats_result", "team_ats_result"],
            "ats_margin": ["ats_margin", "team_ats_margin"],
            "team_clv": ["team_clv", "clv"],
        }

        for output_col, aliases in optional_map.items():
            source_col = find_col(raw, aliases, required=False)
            out[output_col] = raw[source_col] if source_col else pd.NA

        return out, raw.columns.tolist(), "directional"

    # Secondary: one home/away row per game.
    home_col = find_col(raw, ["home_team", "home"])
    away_col = find_col(raw, ["away_team", "away"])

    home_spread_col = find_col(
        raw,
        ["home_spread", "closing_home_spread", "spread"],
        required=False,
    )
    home_score_col = find_col(
        raw,
        ["home_score", "final_home_score"],
        required=False,
    )
    away_score_col = find_col(
        raw,
        ["away_score", "final_away_score"],
        required=False,
    )

    game_id_col = find_col(raw, ["game_id", "id", "event_id"], required=False)
    date_col = find_col(raw, ["date", "game_date", "start_date"], required=False)

    rows = []

    for index, r in raw.iterrows():
        season = pd.to_numeric(r[season_col], errors="coerce")
        week = pd.to_numeric(r[week_col], errors="coerce")
        game_id = r[game_id_col] if game_id_col else f"{int(season)}_{index}"
        date = r[date_col] if date_col else pd.NA

        home = canonical_team(r[home_col])
        away = canonical_team(r[away_col])

        home_spread = (
            pd.to_numeric(r[home_spread_col], errors="coerce")
            if home_spread_col
            else pd.NA
        )

        home_margin = pd.NA
        if home_score_col and away_score_col:
            home_score = pd.to_numeric(r[home_score_col], errors="coerce")
            away_score = pd.to_numeric(r[away_score_col], errors="coerce")

            if pd.notna(home_score) and pd.notna(away_score):
                home_margin = home_score - away_score

        home_ats_margin = (
            home_margin + home_spread
            if pd.notna(home_margin) and pd.notna(home_spread)
            else pd.NA
        )

        if pd.isna(home_ats_margin):
            home_result = pd.NA
        elif home_ats_margin > 0:
            home_result = "W"
        elif home_ats_margin < 0:
            home_result = "L"
        else:
            home_result = "P"

        away_ats_margin = (
            -home_ats_margin
            if pd.notna(home_ats_margin)
            else pd.NA
        )
        away_result = (
            "L" if home_result == "W"
            else "W" if home_result == "L"
            else home_result
        )

        rows.extend(
            [
                {
                    "season": season,
                    "week": week,
                    "date": date,
                    "game_id": game_id,
                    "team": home,
                    "opponent": away,
                    "spread": home_spread,
                    "ats_result": home_result,
                    "ats_margin": home_ats_margin,
                    "team_clv": pd.NA,
                },
                {
                    "season": season,
                    "week": week,
                    "date": date,
                    "game_id": game_id,
                    "team": away,
                    "opponent": home,
                    "spread": (
                        -home_spread
                        if pd.notna(home_spread)
                        else pd.NA
                    ),
                    "ats_result": away_result,
                    "ats_margin": away_ats_margin,
                    "team_clv": pd.NA,
                },
            ]
        )

    return pd.DataFrame(rows), raw.columns.tolist(), "home_away"


def add_conference_context(games):
    if not CONF_SOURCE.exists():
        games["conference_matchup_type"] = pd.NA
        return games

    conf = pd.read_csv(CONF_SOURCE)

    required = ["season", "team", "opponent", "conference_matchup_type"]
    missing = [c for c in required if c not in conf.columns]

    if missing:
        games["conference_matchup_type"] = pd.NA
        return games

    conf = conf.copy()
    conf["team"] = conf["team"].apply(canonical_team)
    conf["opponent"] = conf["opponent"].apply(canonical_team)

    keep = [
        c
        for c in [
            "season",
            "team",
            "opponent",
            "team_conference",
            "opponent_conference",
            "team_tier",
            "opponent_tier",
            "conference_matchup_type",
        ]
        if c in conf.columns
    ]

    conf = conf[keep].drop_duplicates(
        subset=["season", "team", "opponent"]
    )

    return games.merge(
        conf,
        on=["season", "team", "opponent"],
        how="left",
        validate="many_to_one",
    )


def main():
    print("Parsing 2021 and 2022 returning-production tables")

    rp_2021 = parse_rp_text(RAW_2021, 2021)
    rp_2022 = parse_rp_text(RAW_2022, 2022)
    rp_2023_2025 = derive_2023_2025_team_rp()

    team_rp = pd.concat(
        [rp_2021, rp_2022, rp_2023_2025],
        ignore_index=True,
        sort=False,
    )

    team_rp = (
        team_rp.sort_values(["season", "team"])
        .drop_duplicates(subset=["season", "team"], keep="first")
        .copy()
    )

    OUT_TEAM_RP.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    team_rp.to_csv(OUT_TEAM_RP, index=False)

    print("2021 teams parsed:", len(rp_2021))
    print("2022 teams parsed:", len(rp_2022))
    print("2023-2025 team-season rows derived:", len(rp_2023_2025))
    print("Combined team-season RP rows:", len(team_rp))

    market_file = first_existing_market_file()

    print()
    print("Using market file:")
    print(market_file)

    games, market_columns, market_shape = build_directional_market_rows(
        market_file
    )

    games["season"] = pd.to_numeric(
        games["season"], errors="coerce"
    ).astype("Int64")
    games["week"] = pd.to_numeric(
        games["week"], errors="coerce"
    ).astype("Int64")

    games = games[
        games["season"].isin([2021, 2022, 2023, 2024, 2025])
        &
        games["week"].isin(WEEKS)
    ].copy()

    games["team"] = games["team"].apply(canonical_team)
    games["opponent"] = games["opponent"].apply(canonical_team)

    # Deduplicate only true team-side game rows.
    dedupe_key = ["season", "week", "team", "opponent"]
    if "game_id" in games.columns and games["game_id"].notna().any():
        dedupe_key = ["season", "game_id", "team", "opponent"]

    raw_directional_rows = len(games)

    games = (
        games.sort_values(dedupe_key)
        .drop_duplicates(subset=dedupe_key, keep="first")
        .copy()
    )

    games = add_conference_context(games)

    team_values = team_rp[
        [
            "season",
            "team",
            "overall_returning_production",
            "offense_returning_production",
            "defense_returning_production",
        ]
    ].rename(
        columns={
            "overall_returning_production": "team_overall",
            "offense_returning_production": "team_offense",
            "defense_returning_production": "team_defense",
        }
    )

    opp_values = team_rp[
        [
            "season",
            "team",
            "overall_returning_production",
            "offense_returning_production",
            "defense_returning_production",
        ]
    ].rename(
        columns={
            "team": "opponent",
            "overall_returning_production": "opp_overall",
            "offense_returning_production": "opp_offense",
            "defense_returning_production": "opp_defense",
        }
    )

    games = games.merge(
        team_values,
        on=["season", "team"],
        how="left",
        validate="many_to_one",
    )

    games = games.merge(
        opp_values,
        on=["season", "opponent"],
        how="left",
        validate="many_to_one",
    )

    games["overall_rp_edge"] = (
        games["team_overall"] - games["opp_overall"]
    )
    games["off_vs_def_rp_edge"] = (
        games["team_offense"] - games["opp_defense"]
    )
    games["def_vs_off_rp_edge"] = (
        games["team_defense"] - games["opp_offense"]
    )

    games.to_csv(OUT_GAMES, index=False)

    missing_team = games[games["team_overall"].isna()][
        ["season", "team"]
    ].drop_duplicates()
    missing_team["side"] = "team"

    missing_opp = games[games["opp_overall"].isna()][
        ["season", "opponent"]
    ].drop_duplicates().rename(columns={"opponent": "team"})
    missing_opp["side"] = "opponent"

    unmatched = pd.concat(
        [missing_team, missing_opp],
        ignore_index=True,
    ).drop_duplicates()

    unmatched.to_csv(OUT_UNMATCHED_TEAMS, index=False)

    complete_rows = games[
        games["team_overall"].notna()
        &
        games["opp_overall"].notna()
    ]

    audit_rows = [
        {"metric": "rp_2021_teams", "value": len(rp_2021)},
        {"metric": "rp_2022_teams", "value": len(rp_2022)},
        {
            "metric": "rp_2023_2025_team_seasons",
            "value": len(rp_2023_2025),
        },
        {
            "metric": "combined_rp_team_seasons",
            "value": len(team_rp),
        },
        {
            "metric": "market_file",
            "value": str(market_file),
        },
        {
            "metric": "market_shape",
            "value": market_shape,
        },
        {
            "metric": "market_columns",
            "value": " | ".join(market_columns),
        },
        {
            "metric": "raw_directional_rows_weeks_1_4",
            "value": raw_directional_rows,
        },
        {
            "metric": "deduplicated_team_side_rows",
            "value": len(games),
        },
        {
            "metric": "complete_rp_team_side_rows",
            "value": len(complete_rows),
        },
        {
            "metric": "unmatched_team_season_names",
            "value": len(unmatched),
        },
        {
            "metric": "unique_games_with_complete_rp",
            "value": (
                complete_rows[["season", "game_id"]]
                .drop_duplicates()
                .shape[0]
                if "game_id" in complete_rows.columns
                else complete_rows[
                    ["season", "week", "team", "opponent"]
                ].shape[0] // 2
            ),
        },
    ]

    for season in [2021, 2022, 2023, 2024, 2025]:
        season_rows = complete_rows[complete_rows["season"] == season]

        audit_rows.append(
            {
                "metric": f"complete_team_side_rows_{season}",
                "value": len(season_rows),
            }
        )

    audit = pd.DataFrame(audit_rows)
    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("Created:")
    print(OUT_TEAM_RP)
    print(OUT_GAMES)
    print(OUT_UNMATCHED_TEAMS)
    print(OUT_AUDIT)

    print()
    print("Expansion summary:")
    print(audit.to_string(index=False))

    if not unmatched.empty:
        print()
        print("First unmatched names:")
        print(unmatched.head(50).to_string(index=False))


if __name__ == "__main__":
    main()
