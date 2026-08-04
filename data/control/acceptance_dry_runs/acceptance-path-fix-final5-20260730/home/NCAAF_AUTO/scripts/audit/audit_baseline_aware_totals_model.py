#!/usr/bin/env python3
from pathlib import Path
import csv
import json

ROOT=Path.home()/"NCAAF_AUTO"
base=ROOT/"data/research/postgame_total_market_update_baseline_aware_2021_2025"
summary=base/"summary.json"
pred=base/"holdout_2025_predictions_baseline_aware.csv"

assert summary.exists(), f"Missing {summary}"
assert pred.exists(), f"Missing {pred}"

s=json.loads(summary.read_text())
with pred.open(newline="",encoding="utf-8") as f:
    reader=csv.DictReader(f)
    fields=set(reader.fieldnames or [])
    rows=list(reader)

required={
    "home_prev_game_id","away_prev_game_id",
    "home_has_prior_game","away_has_prior_game",
    "home_games_played_before","away_games_played_before",
    "prior_data_state","score_only_prediction",
    "score_plus_pbp_prediction",
}
missing=required-fields
assert not missing, f"Missing columns: {sorted(missing)}"
assert any(r["prior_data_state"]=="one_prior" for r in rows), "No one-prior holdout rows"
assert any(r["prior_data_state"]=="both_prior" for r in rows), "No both-prior holdout rows"

print("PASS: baseline-aware totals model")
print(json.dumps(s["rows"],indent=2))
print(json.dumps(s["holdout_by_prior_data_state"],indent=2))
