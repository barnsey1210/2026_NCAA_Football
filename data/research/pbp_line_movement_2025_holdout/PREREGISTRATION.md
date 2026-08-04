# 2025 Line-Movement Holdout

Frozen before evaluating 2025 movement.

Primary provider: Bovada. DraftKings and ESPN Bet are secondary replication.

1. Bet/flag the away underdog at the opener when
   `home_overall_success_adv <= -0.0001814671671235002` and
   `opening_home_spread <= -3.0`. Expected movement is toward the away team.
2. Bet/flag the under at the opener when
   `combined_overall_success <= 0.9310875830918766`,
   `combined_field_position > -139.80758013111537`, and
   `combined_fast_pace <= -26.013869254679115`. Expected movement is downward.

Week 5+ only. No thresholds or directions may change. Primary confirmation
requires at least 30 Bovada games, mean signed CLV >= 0.50 spread points or 0.75
total points, direction accuracy above 50%, and one-sided p <= 0.05 for the two
individually frozen rules. No ATS or total game results are used.
