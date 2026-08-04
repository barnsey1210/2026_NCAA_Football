# Frozen 2026 Opening-Price Alerts

## Eligibility

- Week 5 or later
- At least four prior same-season games for both teams
- Garbage-time-filtered, opponent-adjusted PBP inputs
- Evaluate immediately when a full-game opener is available
- Record provider, timestamp, opening price, bet/alert price, and every later
  snapshot through the final pre-kick close

## Signal A: away underdog

Trigger when:

```text
home_overall_success_adv <= -0.0001814671671235002
opening_home_spread <= -3.0
```

Interpretation: the home team is favored by at least three points even though
its opponent-adjusted expected success-rate matchup is no better than the away
team's. Flag the away underdog at the opening number.

Historical holdout expectation: approximately +0.8 spread points of CLV at
Bovada. Do not chase after the spread has already moved toward the away team.

## Signal B: under

Trigger when:

```text
combined_overall_success <= 0.9310875830918766
combined_field_position > -139.80758013111537
combined_fast_pace <= -26.013869254679115
```

`combined_fast_pace <= -26.0139` means expected pace is at least approximately
26.01 seconds per play because the stored feature is negative seconds per play.
Flag the opening full-game under.

Historical holdout expectation: approximately +0.85 total points of CLV at
Bovada. Do not chase after the total has already moved down.

## Prospective grading

Grade every alert, including passes and prices that moved before action:

```text
signal_id
game_id
provider
opening_timestamp
opening_price
alert_timestamp
available_price_at_alert
closing_price
clv_points
direction_correct
bet_placed
stake
game_result
profit_loss
```

Primary evaluation is mean CLV and percentage beating the close. Profitability
is secondary until a meaningful prospective sample exists. Do not revise these
thresholds during the 2026 season.
