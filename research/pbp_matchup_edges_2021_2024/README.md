# PBP Matchup Feature Edge Scan (2021-2024)

This directory contains a controlled first-pass search for betting edges from
pregame, opponent-adjusted play-by-play tendencies. It is an edge analysis,
not a model for creating fair spreads or totals.

## Outcome

No feature passed the validation standard. All 20 preregistered tail tests are
classified as `rejected_or_inconclusive`. This is a useful negative result: the
current broad tendency features do not yet justify a betting rule.

The high-tail low-disruption totals test was directionally interesting in both
samples, but it did not survive multiple-testing correction and must be treated
only as a hypothesis for future data.

## Protocol

- Development: 2021-2023, 1,565 games
- Validation: 2024, 527 games
- Locked holdout: 2025, excluded from this analysis
- Eligibility: Week 5 or later, so each team has an in-season tendency sample
- Thresholds: development-sample 20th and 80th percentiles
- Scope: 10 football-motivated feature families and 20 total tail tests
- Markets: closing full-game spread and total
- Win-rate shrinkage: 20-decision prior centered at 50%
- Multiplicity: Benjamini-Hochberg false-discovery correction across all tests
- Not searched: favorite/underdog splits, additional home/away splits, arbitrary
  interactions, or feature-threshold permutations

## Files

- `feature_edge_validation.csv`: full development and validation results
- `summary.json`: compact protocol and result counts

## Interpretation

The feature scan asks whether extreme matchup conditions consistently beat the
closing market, not merely whether they correlate with scoring or margin. A
positive result must have sensible development performance, repeat in 2024,
retain an adequate shrunk win rate, and survive correction for the number of
questions asked.

The next research pass should add a small preregistered set of more specific PBP
mismatches: rush/pass success splits, QB-designed-run and scramble involvement,
pressure and sack response, explosive rush/pass splits, finishing drives, and
field-position effects. The 2025 outcomes should remain locked until that
feature specification is frozen.
