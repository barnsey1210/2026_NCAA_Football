#!/usr/bin/env python3

"""
Build historical team conference membership reference table.

Source:
    cfbd_cache/pbp_history/YYYY/teams_fbs.json.gz

Outputs:
    data/reference/team_conference_history.csv
    data/audits/conference_history_changes.csv

Used for:
    - historical conference tier analysis
    - P4 vs G6 betting research
    - realignment research
    - travel effects
    - matchup database enrichment
"""

from pathlib import Path
import gzip
import json
import csv


ROOT = Path(__file__).resolve().parents[2]

CACHE_DIR = ROOT / "cfbd_cache" / "pbp_history"

OUT_REFERENCE = ROOT / "data" / "reference" / "team_conference_history.csv"
OUT_AUDIT = ROOT / "data" / "audits" / "conference_history_changes.csv"


YEARS = range(2021, 2026)


# --------------------------------------------------
# Conference normalization
# --------------------------------------------------

def normalize_conference(conf):

    if not conf:
        return "Independent"

    c = conf.strip()

    replacements = {

        "Big Ten Conference": "Big Ten",
        "Big 10": "Big Ten",

        "Big 12 Conference": "Big 12",

        "Atlantic Coast Conference": "ACC",

        "Southeastern Conference": "SEC",

        "American Athletic Conference": "American",
        "American Athletic": "American",

        "Mid-American Conference": "MAC",
        "Mid-American": "MAC",

        "Mountain West Conference": "Mountain West",
        "Mountain West": "Mountain West",

        "Sun Belt Conference": "Sun Belt",
        "Sun Belt": "Sun Belt",

        "Conference USA": "Conference USA",

        "Pac-12 Conference": "Pac-12",
        "Pac-12": "Pac-12",

        "FBS Independents": "Independent",
        "Independent": "Independent",
    }

    return replacements.get(c, c)


# --------------------------------------------------
# Conference tier classification
# --------------------------------------------------

def conference_classification(conf):

    p4 = {
        "SEC",
        "Big Ten",
        "Big 12",
        "ACC",
    }

    g6 = {
        "American",
        "Mountain West",
        "Sun Belt",
        "MAC",
        "Conference USA",
    }

    if conf in p4:
        return "P4", "P4"

    if conf in g6:
        return "G6", "G6"

    if conf == "Pac-12":
        return "Legacy_P5", "Special"

    if conf == "Independent":
        return "Independent", "Independent"

    return "Other", "Other"


# --------------------------------------------------
# Load CFBD cached team files
# --------------------------------------------------

def load_year(year):

    path = CACHE_DIR / str(year) / "teams_fbs.json.gz"

    if not path.exists():
        raise FileNotFoundError(path)

    with gzip.open(path, "rt") as f:
        payload = json.load(f)

    return payload["data"]


# --------------------------------------------------
# Build history
# --------------------------------------------------

def build_history():

    rows = []

    for year in YEARS:

        teams = load_year(year)

        for team in teams:

            conference = normalize_conference(
                team.get("conference")
            )

            tier, group = conference_classification(
                conference
            )

            rows.append(
                {
                    "season": year,
                    "team": team["school"],
                    "conference": conference,
                    "conference_tier": tier,
                    "conference_group": group,
                }
            )


    rows.sort(
        key=lambda x: (
            x["team"],
            x["season"]
        )
    )


    previous_conf = {}
    tenure = {}

    history_rows = []
    change_rows = []


    for row in rows:

        team = row["team"]
        conference = row["conference"]

        previous = previous_conf.get(team)

        changed = False

        if previous and previous != conference:

            changed = True

            change_rows.append(
                {
                    "team": team,
                    "season": row["season"],
                    "from_conference": previous,
                    "to_conference": conference,
                }
            )


        if previous == conference:
            tenure[team] = tenure.get(team, 0) + 1
        else:
            tenure[team] = 1


        row.update(
            {
                "conference_changed": changed,
                "previous_conference": previous if previous else "",
                "conference_tenure_years": tenure[team],
            }
        )


        history_rows.append(row)

        previous_conf[team] = conference


    return history_rows, change_rows


# --------------------------------------------------
# Write CSV
# --------------------------------------------------

def write_csv(path, rows, columns):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(path, "w", newline="") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(rows)



def main():

    history, changes = build_history()


    write_csv(
        OUT_REFERENCE,
        history,
        [
            "season",
            "team",
            "conference",
            "conference_tier",
            "conference_group",
            "conference_changed",
            "previous_conference",
            "conference_tenure_years",
        ],
    )


    write_csv(
        OUT_AUDIT,
        changes,
        [
            "team",
            "season",
            "from_conference",
            "to_conference",
        ],
    )


    print("Created:")
    print(OUT_REFERENCE)

    print("Rows:", len(history))

    print()

    print("Conference changes:")
    print(OUT_AUDIT)

    print("Changes:", len(changes))


if __name__ == "__main__":
    main()