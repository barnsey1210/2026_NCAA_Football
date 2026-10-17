#!/usr/bin/env python3
"""Build review artifacts from the deterministic CFP selector replay."""

import argparse
import csv
import json
from pathlib import Path


CURRENT = "baseline_percentile_resume_v1"
B = "marginal_loss_penalty_v1"
C = "record_first_at_large_v1"
POLICIES = (("current", CURRENT), ("candidate_b", B), ("candidate_c", C))
FOCUS_TEAMS = [
    "Houston", "Texas Tech", "Utah", "UCLA", "Wake Forest",
    "James Madison", "Ohio State", "LSU", "Alabama", "Oregon", "BYU",
    "Iowa", "Miami-FL", "Georgia", "Notre Dame",
]


def pct(value):
    return round(100.0 * value, 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audit")
    parser.add_argument("prior_audit")
    parser.add_argument("csv_output")
    parser.add_argument("summary_output")
    args = parser.parse_args()

    audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    prior = json.loads(Path(args.prior_audit).read_text(encoding="utf-8"))
    for policy in (CURRENT, "loss_gate_exception_v1", B):
        for section in (
            "teams", "all_fbs_record_champion_buckets",
            "all_fbs_non_champion_loss_buckets", "field_size_counts",
        ):
            if prior[section][policy] != audit[section][policy]:
                raise RuntimeError(f"Replay mismatch for {section}/{policy}")

    conferences = {
        row["team"]: row["conference"]
        for row in csv.DictReader(
            Path("reports/cfp_selector_all_138_before_after_2026-10-17.csv").open()
        )
    }
    rows = []
    for team in sorted(audit["teams"][CURRENT]):
        row = {"team": team, "conference": conferences.get(team, "")}
        for label, policy in POLICIES:
            row[f"{label}_cfp_pct"] = pct(audit["teams"][policy][team]["cfp_probability"])
        row["candidate_c_change_pp"] = round(
            row["candidate_c_cfp_pct"] - row["current_cfp_pct"], 3
        )
        rows.append(row)

    with Path(args.csv_output).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    top_movers = sorted(
        rows, key=lambda row: abs(row["candidate_c_change_pp"]), reverse=True
    )[:20]
    houston = {
        label: audit["teams"][policy]["Houston"]
        for label, policy in POLICIES
    }
    loss_rates = {
        label: {
            loss: {
                "candidate_trials": bucket["trials"],
                "at_large_selections": bucket["at_large"],
                "at_large_rate_pct": pct(bucket["at_large_rate"]),
            }
            for loss, bucket in audit["all_fbs_non_champion_loss_buckets"][policy].items()
        }
        for label, policy in POLICIES
    }
    summary = {
        "schema_version": "cfp-selector-candidate-c-report-v1",
        "trials": audit["trials"],
        "seed": audit["seed"],
        "accepted_replay_match": True,
        "field_size_counts": {
            label: audit["field_size_counts"][policy] for label, policy in POLICIES
        },
        "candidate_c_emergency_fill_trials": audit["emergency_fill_trials"][C],
        "houston": houston,
        "non_champion_at_large_by_loss": loss_rates,
        "focus_team_probabilities": {
            team: {
                label: pct(audit["teams"][policy][team]["cfp_probability"])
                for label, policy in POLICIES
            }
            for team in FOCUS_TEAMS
        },
        "top_20_absolute_movers_current_to_candidate_c": top_movers,
    }
    Path(args.summary_output).write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
