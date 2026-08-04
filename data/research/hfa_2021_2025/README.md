# Historical HFA Study: 2021-2025

## Purpose

Research-only comparison of four home-field treatments:

1. Generic 2.5 points
2. Current 2026 site team HFA
3. Historical conference HFA
4. Historical conference HFA plus shrunk team adjustment

No production HFA values were changed.

## Design

- Development: 2021-2023
- Shrinkage selection: 2024
- Locked holdout: 2025
- Selected conference shrinkage: 80
- Selected team shrinkage: 15
- Development global HFA: 2.539
- Locked 2025 best MAE model: conference_team

## Target

`closing home margin - prior-week neutral SP+ difference`

Neutral-site games are excluded from HFA fitting and retained in
`neutral_site_control.csv`.

## Important limitation

The residual is not a pure physical stadium effect. It also includes
remaining SP+ model error and any market adjustment not captured by
the neutral SP+ rating difference.

The current-site HFA benchmark uses 2026 values and is therefore not
a leakage-safe historical model. It is included only because the goal
is to compare the site's current approach with generic and historically
estimated alternatives.

## Outputs

- `game_level_hfa_residuals.csv`
- `conference_hfa_estimates.csv`
- `team_hfa_estimates.csv`
- `model_comparison_by_season.csv`
- `holdout_2025_results.csv`
- `current_site_hfa_comparison.csv`
- `shrinkage_selection_2024.csv`
- `neutral_site_control.csv`
- `audit.json`
