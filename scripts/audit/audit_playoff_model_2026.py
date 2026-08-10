#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "data/site/playoff_model_2026.json"

EXPECTED_TRIALS = 20000
EXPECTED_PROB_VERSION = "logistic_margin_scale_6_5_v1"
EXPECTED_SCALE = 6.5
EXPECTED_HFA = 2.6

G6_CONFS = {"American", "CUSA", "MAC", "MW", "PAC12", "Sun Belt"}

PROB_FIELDS = [
    "playoff_pct",
    "auto_bid_pct",
    "playoff_bye_pct",
    "quarterfinal_pct",
    "semifinal_pct",
    "national_title_game_pct",
    "national_title_pct",
    "top25_pct",
]


def fail(msg):
    raise SystemExit(f"STOP: playoff model audit failed: {msg}")


def main():
    if not MODEL.exists():
        fail(f"missing {MODEL}")

    d = json.loads(MODEL.read_text())
    meta = d.get("metadata") or {}
    teams = d.get("teams") or []
    field = d.get("projected_field") or []

    if d.get("trials") != EXPECTED_TRIALS:
        fail(f"expected {EXPECTED_TRIALS} trials, got {d.get('trials')}")

    if meta.get("win_probability_model_version") != EXPECTED_PROB_VERSION:
        fail(
            "wrong probability model version: "
            f"{meta.get('win_probability_model_version')}"
        )

    if abs(float(meta.get("win_probability_logistic_scale", -999)) - EXPECTED_SCALE) > 1e-9:
        fail(
            "wrong logistic scale: "
            f"{meta.get('win_probability_logistic_scale')}"
        )

    if abs(float(meta.get("fixed_home_field_advantage", -999)) - EXPECTED_HFA) > 1e-9:
        fail(
            "wrong first-round HFA: "
            f"{meta.get('fixed_home_field_advantage')}"
        )

    if len(field) != 12:
        fail(f"projected CFP field has {len(field)} teams instead of 12")

    if sorted(int(r.get("seed", -1)) for r in field) != list(range(1, 13)):
        fail("projected field seeds are not exactly 1 through 12")

    team_by_name = {
        str(r.get("team")): r
        for r in teams
        if r.get("team")
    }

    g6_field = []
    for row in field:
        team = str(row.get("team") or "")
        conf = str((team_by_name.get(team) or {}).get("conference") or "")
        if conf in G6_CONFS:
            g6_field.append(row)

    if len(g6_field) != 1:
        fail(
            f"expected exactly one G6 team in projected field, got "
            f"{len(g6_field)}: {[r.get('team') for r in g6_field]}"
        )

    if int(g6_field[0].get("seed", -1)) != 12:
        fail(
            f"G6 qualifier must be seed 12; got "
            f"{g6_field[0].get('team')} seed {g6_field[0].get('seed')}"
        )

    bad_probs = []
    for row in teams:
        for field_name in PROB_FIELDS:
            value = row.get(field_name)
            if value is None:
                continue
            try:
                x = float(value)
            except (TypeError, ValueError):
                bad_probs.append((row.get("team"), field_name, value))
                continue
            if not 0.0 <= x <= 1.0:
                bad_probs.append((row.get("team"), field_name, value))

    if bad_probs:
        fail(f"invalid probability values; sample={bad_probs[:10]}")

    title_sum = sum(float(r.get("national_title_pct") or 0.0) for r in teams)
    if abs(title_sum - 1.0) > 0.01:
        fail(f"national-title probabilities sum to {title_sum:.6f}")

    print("PASS: playoff model audit")
    print("trials:", d.get("trials"))
    print("teams:", len(teams))
    print("field size:", len(field))
    print(
        "G6 seed 12:",
        g6_field[0].get("team"),
    )
    print("title probability sum:", round(title_sum, 6))
    print(
        "probability model:",
        meta.get("win_probability_model_version"),
    )
    print(
        "logistic scale:",
        meta.get("win_probability_logistic_scale"),
    )
    print(
        "first-round HFA:",
        meta.get("fixed_home_field_advantage"),
    )


if __name__ == "__main__":
    main()
