# Recent PBP Change Line-Movement Result

Recent two-game changes did not add reliable incremental closing-line prediction
beyond the opening market.

2024 MAE:

| Market | Market-only | Market + recent PBP |
|---|---:|---:|
| Spread | 1.299 | 1.303 |
| Total | 1.431 | 1.432 |

The spread RMSE improved slightly (1.791 to 1.786), but MAE and direction
accuracy worsened. Totals also failed to improve.

One discovered spread leaf reached 63.6% direction accuracy in 33 validation
games and had a small p-value, but its mean movement was only +0.44 points versus
the frozen +0.50 requirement. It is classified as rejected/inconclusive and was
not submitted to the 2025 holdout.

- Submitted interaction leaves: 1
- Validated in 2024: 0
- 2025 was not evaluated

This result suggests that noisy two-game changes are generally incorporated or
mean-revert. The already-confirmed absolute matchup movement signals remain the
only PBP movement angles approved for 2026.
