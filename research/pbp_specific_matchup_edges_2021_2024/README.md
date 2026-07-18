# Specific PBP Matchup Edge Validation

## Result

No feature qualified as a validated betting edge. One of 24 frozen tests is
classified as `promising_unconfirmed`; the other 23 are inconclusive or
rejected. The 2025 season was excluded and remains a locked holdout.

The hypothesis-level result is the low tail of
`ats_explosive_rush_mismatch`: games in which the away offense's explosive-rush
profile, paired with the home defense's explosive-rush rate allowed, exceeded
the corresponding home matchup by at least 2.91 percentage points.

| Season | Games | ATS wins | ATS losses | Win rate | Mean ATS margin |
|---:|---:|---:|---:|---:|---:|
| 2021 | 112 | 61 | 50 | 55.0% | +2.03 |
| 2022 | 106 | 49 | 55 | 47.1% | +0.04 |
| 2023 | 95 | 50 | 44 | 53.2% | +1.78 |
| 2024 validation | 106 | 55 | 51 | 51.9% | +0.95 |

Its 2024 win rate shrinks to 51.6%, and its Benjamini-Hochberg q-value is 0.77.
It is therefore not actionable. It can be tracked prospectively, but using it
as a betting rule would overstate the evidence.

## Frozen protocol

- 2021-2023 development; 2024 validation
- Week 5 and later only
- Development 20th/80th percentile thresholds
- 12 predefined feature families, two tails each
- Closing full-game spreads and totals
- A 20-decision, 50% prior for shrunk win rates
- False-discovery correction over all 24 validation tests
- No favorite/underdog splits, alternate thresholds, or interaction search

See `PREREGISTRATION.md` for the specification written before execution.

## Interpretation

Broad PBP behavior is measurable, but the market appears to price most of these
simple one-dimensional matchup extremes adequately. The next useful expansion
is to build leakage-safe drive finishing and starting-field-position features,
then freeze them as a separate hypothesis family. They should not be appended
retroactively to this test.

## Files

- `PREREGISTRATION.md`: frozen design
- `feature_edge_validation.csv`: all test results
- `summary.json`: result counts and sample sizes
