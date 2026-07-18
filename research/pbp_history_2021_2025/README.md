# Historical PBP tendency foundation, 2021-2025

## Purpose

This directory contains the football-feature foundation for later style-matchup
research. It intentionally contains no betting results, spreads, totals, ATS records,
or profitability tests.

## Coverage

| Season | FBS teams | Team-games | Havoc rows |
|---:|---:|---:|---:|
| 2021 | 130 | 1,581 | 1,581 |
| 2022 | 131 | 1,588 | 1,588 |
| 2023 | 133 | 1,618 | 1,601 |
| 2024 | 134 | 1,619 | 1,610 |
| 2025 | 136 | 1,650 | 1,650 |
| **Total** | **136 unique** | **8,056** | **8,030** |

- Unique games: 4,329
- Raw weekly PBP rows cached: 1,191,065
- Team-games missing offensive or defensive PBP: 0
- PBP play counts within two plays of CFBD advanced counts: 94.7% offense and defense

## Outputs

- `team_game_tendencies.csv`: observed team-game football features.
- `rolling_pregame_tendencies.csv`: expanding averages using earlier games only.
- `rolling_pregame_opponent_adjusted.csv`: regularized opponent-adjusted pregame
  effects and matchup expectations.
- `audit.json`: coverage and reconciliation metrics.

## Why local opponent adjustment is used

CFBD opponent-adjusted endpoints are aggregated products and are not enabled for the
current free-tier key. More importantly, a published full-season adjusted rating can
leak future games into a historical Week 5 prediction.

The local adjustment is refit before every week using only games from earlier weeks in
that season. It uses an iterative regularized two-way model:

```text
observed metric = league mean + offense/team effect + opponent/defense effect
```

Each effect is shrunk using a three-game prior weight. This reduces early-season
extremes and small-opponent artifacts.

For neutral pass rate:

- Offensive effect: how much more or less the team passes than expected.
- Defensive effect: how much more or less opponents pass against that defense; a
  positive value is pass-funnel direction.
- Matchup expectation: league rate plus the offense effect and opposing defense effect.

The same structure is used for success rate, explosiveness, PPA, and pace. Havoc is
modeled with the defense as the primary actor and opposing offense as the context.

## Leakage protection

- The first game for every team-season has `prior_games = 0`.
- Current-week and future games are excluded from every rolling and adjusted value.
- All opponent-adjusted metrics are populated once a team has at least three prior
  games; early rows remain low-confidence even when an estimate is available.
- Betting markets and outcomes were not loaded while defining or validating features.

## Garbage-time handling

Competitive-play features exclude plays when the pre-play score margin exceeds:

- 38 points in the second quarter;
- 28 points in the third quarter;
- 22 points in the fourth quarter.

First-quarter plays are retained, and overtime is excluded because its field position
and possession structure are not comparable to regulation. Drive pace uses the same
filter based on the score and period at the start of the drive.

This removes 49,873 of 537,901 offensive scrimmage plays (9.27%). Raw play counts and
excluded-play counts remain in the team-game file for audit and sensitivity testing.
Before modeling, the primary filter should be compared with at least one stricter and
one looser definition; the locked 2025 season must not be used to select the threshold.

## Pace handling

Historical PBP clocks are not reliable enough for pace: some feeds repeat `15:00` or
another fixed clock across consecutive plays. Drive-level start/end periods and clocks
are therefore used instead.

The raw recomputed field is retained as `off_drive_elapsed_seconds_per_play_raw`.
Game-level pace outside 12-45 seconds per play is treated as a corrupted-clock value
and excluded. This removes 257 of 8,056 team-games; 7,799 valid pace rows remain.

Clean raw pace has a median of 26.1 seconds/play. For rows with at least three prior
games, adjusted matchup pace ranges from 19.9 to 32.7 seconds/play.

## Interpretation

- Positive offensive pass effect: more pass-oriented than average.
- Positive defensive pass-allowed effect: pass-funnel direction.
- Positive offensive success/PPA/explosiveness effect: stronger offense.
- Positive defensive success/PPA/explosiveness-allowed effect: weaker defense.
- Lower pace seconds: faster offense/game environment.
- Positive defensive havoc effect: more disruptive defense.

These are continuous behavioral features, not categorical betting angles.

## Known limitations

- QB run share combines designed runs and scrambles.
- Sacks count as pass plays.
- Neutral game state currently means first through third quarter and score within 14.
- Success from raw PBP uses positive PPA; CFBD advanced success is retained separately.
- FBS games against FCS opponents are retained, with regularization limiting sparse
  opponent effects.
- The current adjustment uses same-season history only; a prior-season/coordinator
  prior can be added for Weeks 1-4 in live 2026 operation.
- Regular season only; bowls and playoff games are not included yet.

## Next locked research step

1. Join pregame features to the existing historical closing market table by game ID.
2. Keep 2025 isolated as a locked final test.
3. Develop candidate models on 2021-2023 and select them using 2024 only.
4. Compare a market/control baseline with the same model plus PBP features.
5. Evaluate calibration, ATS/total residual error, vig-adjusted ROI, seasonal stability,
   shrinkage, and false-discovery-adjusted exploratory results.
6. Do not publish human-readable matchup angles until the locked 2025 test passes.
