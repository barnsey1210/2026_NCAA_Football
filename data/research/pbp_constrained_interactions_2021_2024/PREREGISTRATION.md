# Constrained PBP Interaction Discovery

Frozen before executing the interaction search.

## Samples

- Discovery: 2021-2023
- Walk-forward audits: train 2021/test 2022; train 2021-2022/test 2023;
  train 2021-2023/test 2024
- Formal validation: 2024
- Locked and excluded: 2025
- Week 5 and later only

## Search constraints

- One game row, expressed from the underdog's perspective for ATS
- Separate ATS and totals trees
- Maximum depth 3
- Minimum 100 discovery games per leaf
- Candidate split thresholds limited to within-node 20th through 80th deciles
- Market features: absolute spread, posted total, and underdog location (ATS)
- PBP features: rush/pass success, rush/pass explosiveness, QB-run stress,
  havoc/disruption, pace/pass environment, field position, opportunity creation,
  finishing, and points per drive
- No team identity, conference, coach, week, or arbitrary categorical filters

## Rule admission

A discovered leaf is submitted to 2024 only if it has at least 100 discovery
games, a shrunk discovery win rate of at least 53%, mean closing-line residual of
at least +0.5, and at least 1.5 percentage points of raw win-rate improvement
over the same rule's market-only parent. Win rates use a 20-decision prior at
50%. Formal validation uses Benjamini-Hochberg correction across admitted rules.

A validated rule must retain positive incremental lift, mean residual of at
least +0.5, shrunk win rate of at least 53%, and q <= 0.10 in 2024.
