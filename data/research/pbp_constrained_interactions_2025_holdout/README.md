# Final 2025 Holdout Results

## Decision

Neither frozen ATS rule confirmed in the untouched 2025 holdout. Both are
rejected as production betting signals. The 2025 holdout is now consumed and
must not be used to revise their thresholds or conditions.

| Rule | Record | Win rate | Shrunk rate | Mean ATS margin | Net at -110 | Incremental vs parent |
|---|---:|---:|---:|---:|---:|---:|
| Explosive-rush underdog | 28-40 | 41.2% | 43.2% | -3.16 | -16.0 units | -7.3 points |
| Favorite vs neutral-pass dog | 24-24 | 50.0% | 50.0% | +1.58 | -2.4 units | -0.9 points |

The favorite rule's positive average ATS margin alongside a 50% record means
its wins tended to be larger than its losses; it still failed both profitability
and incremental-lift requirements. It is not evidence of a tradable edge.

The rules had no overlapping games. All 536 eligible 2025 games were Week 5 or
later, and only the two exact rules in `PREREGISTRATION.md` were evaluated.

## Implication

The earlier 2021-2024 performance was not stable out of sample. We should not
continue modifying these rules against 2025. The PBP feature store remains
useful for weekly team profiling, matchup explanation, and future prospective
research, but this historical sample does not support deploying a betting angle
from the tested rules.

Any new interaction family now requires genuinely new validation data—most
cleanly, prospective 2026 results—or a separately sourced historical period that
was not involved in feature discovery.
