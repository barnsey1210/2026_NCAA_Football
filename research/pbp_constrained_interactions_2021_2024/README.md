# Constrained PBP Interaction Results

## Bottom line

The constrained search found three ATS hypotheses that met the development and
market-parent lift requirements and remained directionally positive in 2024.
None passed formal multiple-testing validation. No totals rule survived.

### Candidate 1: explosive-rush underdog

Bet the underdog when its expected pass-success matchup is at least 1.67
percentage points worse than the favorite's, but its expected explosive-rush
rate is more than 1.13 percentage points better.

| Season | Record | Win rate | Mean ATS margin |
|---:|---:|---:|---:|
| 2021 | 38-30 | 55.9% | +2.55 |
| 2022 | 39-20 | 66.1% | +3.47 |
| 2023 | 39-22 | 63.9% | +0.84 |
| 2024 validation | 41-34 | 54.7% | +2.71 |

The 2024 shrunk win rate is 53.7%, incremental lift over its market-only parent
is 3.7 points, and adjusted q-value is 0.39. This is promising, not proven.

### Candidate 2: moderate/large favorite against neutral-pass-matchup dog

Bet the favorite when the spread exceeds 4.5 and the underdog's pass-success
matchup advantage is between -1.67 and +1.62 percentage points.

| Season | Record | Win rate | Mean ATS margin |
|---:|---:|---:|---:|
| 2021 | 43-18 | 70.5% | +5.92 |
| 2022 | 33-21 | 61.1% | +2.63 |
| 2023 | 40-31 | 56.3% | +3.12 |
| 2024 validation | 36-27-1 | 57.1% | +3.16 |

The 2024 shrunk win rate is 55.4%, incremental lift over its market-only parent
is 8.3 points, and adjusted q-value is 0.39. This is the strongest candidate,
but it was selected by the tree and therefore still needs the locked holdout.

### Candidate 3: small underdog with a drive-efficiency disadvantage

Bet the underdog at +4.5 or shorter when its pass-success matchup is better than
-1.67 percentage points and its points-per-drive matchup advantage is no more
than +0.048.

It went 105-82-2 in development and 37-35 in 2024. Its validation shrunk win
rate was only 51.1%, so this is considerably weaker than the other two.

## Totals and walk-forward warning

No totals leaf passed validation. The full shallow-tree totals strategy was
55.3% in the 2023 walk-forward test but fell to 45.4% in 2024. The ATS tree was
approximately 50% in every walk-forward test. This instability is why the
individual candidates are not yet production signals.

## Next decision

The three rules are now frozen. Testing them once on 2025 would be a legitimate
final holdout test, but it would consume the last untouched season. No threshold,
direction, or eligibility changes should be allowed after viewing 2025.

Files:

- `PREREGISTRATION.md`: search constraints frozen before execution
- `admitted_rule_validation.csv`: admitted leaves and annual results
- `walk_forward_audit.csv`: whole-tree walk-forward performance
- `ats_tree.json` and `total_tree.json`: transparent fitted trees
