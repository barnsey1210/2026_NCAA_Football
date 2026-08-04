#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
SUMMARY = ROOT / "data/research/market_implied_ratings/summary.json"
HISTORY = ROOT / "data/ratings/market_implied_ratings_history.csv"
LATEST = ROOT / "data/ratings/market_implied_ratings_latest.csv"

assert SUMMARY.exists(), f"Missing {SUMMARY}"
assert HISTORY.exists(), f"Missing {HISTORY}"
assert LATEST.exists(), f"Missing {LATEST}"

summary = json.loads(SUMMARY.read_text())
history = pd.read_csv(HISTORY, low_memory=False)
latest = pd.read_csv(LATEST, low_memory=False)

required = {
    "season", "through_week", "team", "market_implied_rating",
    "market_implied_rank", "games_used", "market_move_1w",
    "market_move_4w",
}
missing = required - set(history.columns)
assert not missing, f"Missing history columns: {sorted(missing)}"
assert latest.team.nunique() >= 100, "Latest market rating coverage below 100 teams"
assert summary["holdout_2025"]["n"] > 0, "No 2025 holdout rows"
assert summary["production_policy"]["blend_into_fundamental_rating"] is False

print("PASS: market-implied ratings research")
print(json.dumps(summary["parameter_selection"], indent=2))
print(json.dumps(summary["validation_2024"], indent=2))
print(json.dumps(summary["holdout_2025"], indent=2))
print("latest teams:", latest.team.nunique())
