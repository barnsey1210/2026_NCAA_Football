# Drive-Context Edge Validation

## Outcome

No drive-context feature validated as a closing-market betting edge:

- 10 frozen feature families
- 20 tail tests
- 1,565 development games from 2021-2023
- 527 validation games from 2024
- 0 validated
- 0 promising but unconfirmed
- 20 rejected or inconclusive
- 2025 excluded and still locked

The strongest-looking 2024 totals observations were high favorable-field-position
environments (54.5% shrunk win rate, +1.51 points versus the closing total) and
high scoring-opportunity environments (54.9%, +2.02 points). They did not have
adequate development evidence, and every adjusted validation q-value was at
least 0.88. Neither is an actionable or watchlist signal under the frozen rules.

Several intuitively low-scoring environments also performed poorly as unders.
We do not reverse those bets after seeing the outcomes; doing so would be a new,
post-hoc hypothesis requiring fresh validation data.

## Method

Expected offensive drive values pair a team's prior offensive rate with the
opposing defense's prior rate allowed. ATS features compare the home expectation
with the away expectation. Totals features combine both teams. All inputs are
known before kickoff and use competitive regulation drives only.

See `PREREGISTRATION.md` for the design frozen before outcomes were joined.
