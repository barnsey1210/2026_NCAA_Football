# Final 2025 Holdout Protocol

Frozen before reading any 2025 outcomes for these rules.

Only two rules advance from the 2021-2024 analysis:

1. **Explosive-rush underdog**: bet the underdog when
   `dog_pass_success <= -0.016664752379848446` and
   `dog_explosive_rush > 0.011315135194059411`.
2. **Favorite versus neutral-pass-matchup dog**: bet the favorite when
   `dog_pass_success > -0.016664752379848446`, `abs_spread > 4.5`, and
   `dog_pass_success <= 0.01620248994322704`.

Rules use Week 5+ games and closing full-game spreads. Pushes are excluded from
win rate and included in sample reporting. No thresholds, directions, features,
or eligibility criteria may change after viewing 2025.

Confirmation requires at least 30 holdout decisions, positive incremental win
rate versus the rule's market-only parent, mean ATS residual of at least +0.5,
a 20-decision-prior shrunk win rate of at least 53%, and Benjamini-Hochberg
q-value <= 0.10 across these two tests. Profit assumes -110 pricing.
