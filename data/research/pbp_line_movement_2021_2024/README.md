# PBP Matchups and Opening-to-Closing Movement

## Outcome

Broadly adding PBP features did **not** improve closing-line prediction. On 2024
Bovada data, market-plus-PBP ridge regression had worse MAE than market-only for
both spreads (1.396 vs 1.299) and totals (1.440 vs 1.434).

Two constrained interactions did validate and replicated across available books.

### Spread: fade an unsupported home favorite at the opener

When the home team opened -3 or higher but its opponent-adjusted overall success
matchup advantage was no better than essentially zero, the market moved toward
the away underdog.

| Season | Games | Mean CLV toward away | Direction accuracy |
|---:|---:|---:|---:|
| 2021 | 56 | +0.45 | 60.7% |
| 2022 | 56 | +0.21 | 50.0% |
| 2023 | 78 | +2.03 | 69.2% |
| 2024 validation | 63 | +0.71 | 68.3% |

2024 provider replication: Bovada +0.71, DraftKings +2.67, ESPN Bet +0.57.

### Total: low-success, slow matchup moves downward

The total moved down when combined expected success was low, combined field
position met the frozen condition, and expected pace was at least 26.01 seconds
per play.

| Season | Games | Mean CLV toward under | Direction accuracy |
|---:|---:|---:|---:|
| 2021 | 35 | +0.73 | 65.7% |
| 2022 | 33 | +1.59 | 78.8% |
| 2023 | 98 | +1.62 | 73.5% |
| 2024 validation | 72 | +0.92 | 63.9% |

2024 replication was +0.92 at Bovada and +0.86 at ESPN Bet. DraftKings did not
have complete opening totals for qualifying games.

These results predict price movement, not game outcomes. Their intended use is
to flag potentially favorable opening numbers and measure subsequent CLV.
