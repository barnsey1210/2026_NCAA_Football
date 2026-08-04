# PBP Line-Movement Study Preregistration

Frozen before analyzing opening-to-closing movement relationships.

## Data

- Primary provider: Bovada, because it has same-provider opening and closing
  prices in every season
- Development: 2021-2023
- Validation: 2024
- Locked movement holdout: 2025
- FBS-vs-FBS games, Week 5 and later
- Spread target: `opening_home_spread - closing_home_spread`; positive means the
  market upgraded the home team
- Total target: `closing_total - opening_total`; positive means movement upward

## Incremental prediction test

Compare on 2024:

1. Opener baseline: predict zero movement
2. Market-only ridge regression: opening line, other opening market, and home
   underdog indicator where applicable
3. Market-plus-PBP ridge regression: market features plus the frozen matchup
   features listed in the analysis script

Primary metrics are MAE and RMSE. PBP must reduce 2024 MAE versus market-only to
claim incremental value.

## Interaction discovery

- Separate shallow regression trees for spread and total movement
- Maximum depth 3
- Minimum 100 development games per leaf
- Split candidates restricted to within-node 20th-80th deciles
- A submitted leaf must contain a PBP condition, have at least 100 games, have
  absolute mean development movement of at least 0.75 spread points or 1.0 total
  points, and differ from its market-only parent mean by at least 0.50 points
- Validation requires at least 30 games, same direction, signed mean movement of
  at least 0.50 spread points or 0.75 total points, and BH q <= 0.10
- No ATS or game-total outcomes are used
