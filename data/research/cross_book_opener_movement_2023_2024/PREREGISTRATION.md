# Cross-Book Opener Mean-Reversion Study

- Same game/provider opening and closing prices from CFBD
- 2023 development, 2024 validation, 2025 locked
- One observation per game/market: the provider opener farthest from that game's
  median opener
- Spread trigger: absolute deviation from median >= 1.0 point
- Total trigger: absolute deviation from median >= 1.5 points
- Prediction: the outlier provider's close moves toward the cross-book opening
  median
- Validation requires n >= 30, mean movement toward consensus >= 0.5 spread or
  0.75 total, direction accuracy > 50%, and BH q <= 0.10 across two tests
- No game outcomes or post-open feature selection
