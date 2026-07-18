# Drive-Context Matchup Edge Preregistration

Frozen before the drive-context features were joined to betting outcomes.

- Development: 2021-2023
- Validation: 2024
- Locked and excluded: 2025
- Week 5 and later only
- Thresholds: development 20th and 80th percentiles
- Outcomes: closing full-game spread and total residuals
- Ten feature families, low and high tails (20 tests)
- Benjamini-Hochberg correction across all validation tests
- Win-rate shrinkage: 20-decision prior centered at 50%

ATS feature families compare the home and away matchup expectations for:

1. Starting field position
2. Scoring-opportunity creation rate
3. Points per scoring opportunity
4. Touchdown rate per scoring opportunity
5. Points per drive

Totals feature families combine both teams' expectations for the same five
concepts. A scoring opportunity is a competitive-regulation drive reaching the
opponent's 40. No favorite/underdog splits, alternate thresholds, interactions,
or post-result feature changes are permitted.
