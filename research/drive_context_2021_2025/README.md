# Drive Context History

Leakage-safe drive features derived from cached CFBD drives and play-by-play.

- 8,056 team-game rows
- 4,329 unique games
- 2021-2025 coverage
- Regulation only
- Garbage time removed with the same thresholds as the PBP tendency pipeline
- Pregame rows use earlier games in the same season only

Definitions:

- Scoring opportunity: drive reaches the opponent's 40-yard line
- Short field: drive starts 60 or fewer yards from goal
- Finishing: points or touchdowns per scoring opportunity
- Starting field position: average starting yards to goal

`team_game_drive_context.csv` contains game results. The edge analysis uses only
`rolling_pregame_drive_context.csv`.
