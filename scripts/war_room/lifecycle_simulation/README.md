# War Room lifecycle simulation

Offline-only validation tooling for the lifecycle architecture. Nothing in this directory is registered in `daily_market_update.sh`, `config/daily_stages.json`, a scheduler, a public builder, or a publisher.

Run synthetic reducer scenarios:

```bash
python3 scripts/war_room/lifecycle_simulation/simulate_reducer_scenarios.py
```

Run the upcoming 2026 schedule/artifact rehearsal:

```bash
python3 scripts/war_room/lifecycle_simulation/simulate_weekend_rehearsal.py --week 0 --dry-run
```

Run the full Week 1 to Week 2 operational rehearsal:

```bash
python3 scripts/war_room/lifecycle_simulation/simulate_week1_week2_rehearsal.py --dry-run
```

This rehearsal covers active/final games, first-final cycle creation, delayed
CFBD postgame evidence and retry, partial/ready Shadow states, market-before-
Shadow ordering, unchanged/rejected/corrected provider panels, independent
spread/total authority transitions, carry-forward/stale labels, deterministic
replay, duplicate suppression, and simulated build/validation. Validation may
request publication review, but the rehearsal never invokes a publisher.

The rehearsal reads current schedule, projection, market, health, and War Room artifacts. Numeric forecast events are explicitly marked simulation fixtures; the reducer does not calculate projections, authority thresholds, markets, or edges. No output is written unless a caller supplies `--output-dir`, which should point to an isolated temporary or research location.
