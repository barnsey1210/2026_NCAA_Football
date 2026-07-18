# Recent PBP Change and Line Movement

- Bovada same-provider open/close
- Week 5+, at least four prior team games
- Recent change compares the last two games with all earlier same-season games
- 2021-2023 development, 2024 validation, 2025 locked
- Fixed features: offensive success, rush/pass success, rush/pass explosiveness,
  neutral pass rate, QB-run share, pace, defensive success improvement, havoc,
  and points per drive
- Market-only versus market-plus-change ridge comparison
- Shallow regression trees: maximum depth 3, minimum 100 development games per
  leaf, split candidates at within-node 20th-80th deciles
- Submitted leaves require a PBP-change condition, absolute development movement
  >= 0.75 spread or 1.0 total, and >= 0.5 points beyond the market-only parent
- 2024 validation requires n >= 30, signed mean >= 0.5 spread or 0.75 total, and
  BH q <= 0.10
- No ATS or game-result outcomes
