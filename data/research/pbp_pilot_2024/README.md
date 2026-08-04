# CFBD 2024 PBP tendency pilot

## Scope

- Teams: Army, Tennessee, Washington State, Iowa, Georgia
- Season: 2024 regular season, Weeks 1-16
- Team-games: 62
- Relevant raw PBP rows: 10,607
- Betting outcomes joined: none

## Go/no-go result

**Go for a broader historical feature build, with caveats.** CFBD provides sufficient
raw and aggregated data for rolling behavioral tendencies. Literal formations remain
out of scope. The pilot should not yet be used as a betting signal.

## Sanity-check profiles

| Team | Neutral pass rate | QB run share | Game-clock seconds/play | Defensive havoc |
|---|---:|---:|---:|---:|
| Army | 14.9% | 45.2% | 31.7 | 15.6% |
| Tennessee | 47.2% | 14.8% | 24.0 | 22.6% |
| Washington State | 52.0% | 31.6% | 25.0 | 14.7% |
| Iowa | 40.2% | 6.7% | 32.6 | 17.9% |
| Georgia | 61.1% | 12.2% | 24.7 | 16.9% |

The profiles distinguish the intended extremes. Army is the clearest run/QB-run
outlier; Tennessee is the fastest; Iowa is the slowest; Georgia and Washington State
are more pass-oriented. Washington State's high QB run share is meaningful and is why
its raw pass rate is lower than a simple "pass-heavy" label might imply.

## Data-quality checks

- Offensive PBP play count exactly matches CFBD advanced stats in 57/62 games (91.9%).
- Defensive PBP play count exactly matches in 51/62 games (82.3%).
- Remaining discrepancies are 1-4 plays per game.
- Neutral pass rate, QB run share, PPA, and pace proxy are populated in all 62 games.
- Defensive havoc is populated in 61/62 games.
- The first rolling row for every team has zero prior games and null pregame features,
  confirming the rolling table does not use the current game's observations.
- 42/62 rows have at least four prior games and are suitable for provisional profiles.

## Important limitations

- QB run share is inferred from play descriptions and includes designed runs plus
  scrambles; it should not be labeled designed-run rate.
- Pass rate includes sacks as pass plays.
- Success uses positive PPA as the play-level definition.
- The pace field is a game-clock gap proxy. It is not formation, personnel, no-huddle,
  or true wall-clock snap interval data.
- Fumble and interception descriptions require normalization; the pilot handles the
  common 2024 forms, but future seasons need annual reconciliation audits.
- Funnel scores still require opponent adjustment and are not produced by this pilot.
- No ATS or totals results were inspected, intentionally preventing feature-definition
  tuning against betting outcomes.

## Outputs

- `game_tendencies.csv`: one row per pilot team-game.
- `rolling_pregame_tendencies.csv`: expanding pregame means using only earlier games.
- `team_summary.csv`: descriptive full-season pilot summary.
- `audit.json`: endpoint coverage and play-count reconciliation.

## Recommended next research phase

1. Freeze version 1 feature definitions and cleaning rules.
2. Pull all FBS PBP and advanced/havoc data for 2021-2025.
3. Build opponent-adjusted run/pass funnel and efficiency measures.
4. Use 2021-2023 for development, 2024 for validation, and keep 2025 locked.
5. Compare a market/control baseline against the same model plus PBP features.
6. Report shrinkage, uncertainty, false-discovery controls, threshold stability, and
   season-by-season results before promoting any finding to a betting signal.
