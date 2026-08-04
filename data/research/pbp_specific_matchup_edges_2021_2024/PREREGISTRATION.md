# Frozen Specific Matchup Feature Test

This specification was written before running the second-pass result scan.

- Development seasons: 2021-2023
- Validation season: 2024
- Locked and excluded: 2025
- Eligible games: Week 5 or later
- Fixed thresholds: development 20th and 80th percentiles
- Markets: full-game closing spread and closing total
- Feature families: rush success, pass success, explosive rush, explosive pass,
  QB-run stress, and disruption/havoc
- ATS construction: home expected matchup value minus away expected matchup value
- Total construction: combined expected matchup values
- Tests: low and high tail for each of 12 feature families (24 tests total)
- Multiplicity control: Benjamini-Hochberg across all 24 validation tests
- Win-rate shrinkage: 20 decisions centered at 50%
- No favorite/underdog splits, additional location splits, alternate thresholds,
  interaction permutations, or post-result feature changes

Finishing drives and starting field position are excluded because the current
rolling pregame table does not contain clean, leakage-safe versions of them.
