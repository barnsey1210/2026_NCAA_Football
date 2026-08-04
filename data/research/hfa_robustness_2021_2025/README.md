# HFA Robustness Study

Research-only cross-validation of generic, conference, current-site,
and blended home-field adjustments.

## Fixed parameters

- Conference shrinkage: 80
- Conference cap: 2.25 to 2.85
- Generic benchmark: 2.5

## Evaluation designs

1. Leave-one-season-out for every season from 2021 through 2025.
2. Temporal prior-season-only tests for 2023, 2024, and 2025.

## Important interpretation

The temporal tests are the stronger production evidence because they
do not use future seasons to estimate the held-out season.

The current-site HFA and blends are benchmark-only because their team
values come from the 2026 preseason database.

## Outputs

- `model_results_by_fold.csv`
- `aggregate_model_comparison.csv`
- `model_improvement_vs_generic.csv`
- `game_level_robustness_predictions.csv`
- `conference_estimates_by_fold.csv`
- `audit.json`
