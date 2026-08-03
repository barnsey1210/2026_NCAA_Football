# Betting Model Performance reconciliation

Reconciled on 2026-08-02 from the current operational runtime into the authoritative source repository.

## Source comparison

The active files under `scripts/model_tracking/`, `scripts/control/run_data_refresh.py`, `tests/test_model_tracking_phase1.py`, and `data/model_tracking/{config.json,schema.json}` existed only in `NCAAF_AUTO`. `data/site/model_performance_view.json` and the existing site build/publish sources were already byte-identical before this work. The production source repository did not yet contain `betting_v2.html`; its tracked `betting.html` was an assembled canonical page without Model Performance.

Runtime ledgers and generated files were not promoted. This excludes JSONL ledgers, `last_capture_preview.json`, generated `model_performance_view.json`, backups, and preview output.

## Preserved runtime safeguards

- `NON_NEUTRAL_HFA = 2.6`; neutral games use `0.0`.
- Capture eligibility is the calendar day before the game, with same-day fallback.
- Completed/final/closed games are excluded.
- Existing accepted `(canonical_game_id, market_type)` pairs block duplicate official opportunities.
- Pregame controller flow calls capture with `--accept`, settlement with `--accept`, and view building.
- Postgame controller flow calls settlement with `--accept` and view building.
- Empty eligibility produces no accepted writes.

Accepted ledger baseline before reconciliation: zero rows in all six JSONL ledgers. No accepted capture was run during development or testing.

## UI and publication change

The reviewed preview renderer is now the canonical `betting_v2.html` source. My Bets remains the active default and retains its existing activity and matchup fetches. Model Performance is a read-only sibling view. The canonical site builder rebuilds the model view; the publisher stages `model_performance_view.json`; and public validation requires both buttons, the view container, and the v2 JSON contract.

