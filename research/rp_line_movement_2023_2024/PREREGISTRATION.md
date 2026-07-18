# Returning Production and Early Line Movement

- Bovada same-provider open/close
- Weeks 1-4
- 2023 development, 2024 validation, 2025 locked
- Features: home overall RP advantage, home offense-vs-defense RP advantage,
  home defense-vs-offense RP advantage, combined overall RP, combined offense
  RP, and combined defense RP
- Low/high tails fixed at 2023 25th/75th percentiles
- Spread features predict movement toward the advantaged side; totals tails are
  tested directionally only as frozen low=down/high=up hypotheses
- 12 tests total, BH correction, minimum 15 validation games
- Validation requires same direction, signed mean move >= 0.5 spread or 0.75
  total, and q <= 0.10
- No ATS or game-result outcomes
