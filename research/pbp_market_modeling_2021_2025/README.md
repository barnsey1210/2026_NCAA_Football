# PBP market-modeling foundation

## Locked protocol

- Development: 2021-2023
- Validation/model selection: 2024
- Locked final test: 2025, not evaluated
- Primary sample: games where both teams have at least four prior games
- No human-readable betting-angle permutations are generated

## Full-game market coverage

- All provider rows: 16,689
- Selected market games: 6,654
- Joined FBS-vs-FBS games: 3,727
- Development games: 2,216
- Validation games: 749
- Locked 2025 games: 762
- Week 5+ eligible games: 2,628
- Same-provider opening spreads: 1,904
- Same-provider opening totals: 1,773

The selected provider follows a deterministic priority. All provider rows are retained
so future testing can compare consensus, book-specific, and provider-stability results.

## Opening versus closing lines

Closing lines are the main benchmark because they represent the market's strongest
pregame estimate. Opening lines should be tested separately for three purposes:

1. Estimate whether the PBP model identifies value before market movement.
2. Predict opening-to-closing movement and measure expected CLV.
3. Simulate a realistic early-week decision using only information available then.

Opening and closing values must come from the same provider when measuring movement.
An opening-line model should be developed and validated separately rather than adding
open and close indiscriminately to the same backtest.

## Initial 2024 full-game validation

The first regularized baseline uses twelve continuous matchup inputs: opponent-adjusted
neutral pass tendency, success, explosiveness, PPA, pace, and havoc for both sides.
Alpha selection occurs through season-held-out testing inside 2021-2023 only.

| Target/model | 2024 MAE | 2024 RMSE |
|---|---:|---:|
| Margin: closing market | 12.02 | 15.22 |
| Margin: football-only PBP | 12.38 | 15.58 |
| Margin: closing market + PBP residual | 12.10 | 15.33 |
| Total: closing market | 13.05 | 16.48 |
| Total: football-only PBP | 13.17 | 16.50 |
| Total: closing market + PBP residual | 12.97 | 16.40 |

Interpretation:

- The current PBP feature set does not add spread value.
- The totals residual model shows a small validation improvement of about 0.09 MAE and
  0.08 RMSE, with residual correlation of only 0.076.
- This is a weak positive research result, not a betting edge.
- The locked 2025 test must remain closed until feature and model specifications are
  finalized using 2021-2024 only.

## Half-market inventory

The existing SGO file contains 2,863 games for 2024-2025:

| Market | Available rows |
|---|---:|
| Full-game spread | 2,863 |
| Full-game total | 2,863 |
| First-half spread | 1,941 |
| First-half total | 2,056 |
| Second-half spread | 1,776 |
| Second-half total | 1,768 |

First-half models can use pregame information and first-half-specific historical PBP
features. Second-half markets are different: their lines are set at halftime, so a
valid model must use halftime score, first-half possessions, efficiency, pace, injuries,
and the actual halftime market line. A pregame-only second-half backtest would not
represent the information available when the wager is offered.

The SGO archive stores a market-level baseline quote but does not explicitly prove that
every historical quote is the final closing line. Market-timestamp semantics must be
verified before treating these half lines as closes.

## Recommended model sequence

1. Full-game totals: enrich the locked feature specification using scoring opportunity,
   field position, drive efficiency, explosive-play mix, and offense/defense interaction.
2. Opening totals: model market residual and subsequent closing movement separately.
3. First-half totals and spreads: build period-1/2 historical features and validate only
   on the available 2024-2025 market sample using an internal chronological split.
4. Second-half model: build a halftime-state dataset; do not reuse the pregame framework.
5. Only after all specifications are frozen, evaluate the 2025 full-game locked test.

## Files

- `provider_market_rows.csv`: every CFBD provider quote.
- `full_game_modeling_rows.csv`: joined pregame feature/market rows with locked split.
- `audit.json`: join and opening-line coverage.
- `validation_2024.json`: 2024 baseline model results; contains no 2025 evaluation.
