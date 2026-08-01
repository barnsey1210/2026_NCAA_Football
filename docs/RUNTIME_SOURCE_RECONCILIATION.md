# Runtime source reconciliation

Baseline commit: fb8389890ae02a03fd7834df0037f26c47b64682. Audited 2026-08-01.

## Outcome

- Registered scripts: **61**
- Missing primary paths inspected: **43**
- Repository completeness before: **29.51%**
- Repository completeness after: **100.0%**
- Recovered unique active sources: **23**
- Byte-identical duplicate references canonicalized: **20**
- Unresolved scripts: **0**
- Embedded credential values found: **0**

All 43 paths were classified exactly once. Runtime files were read only and no live command ran.

## Classification counts

| Classification | Count |
|---|---:|
| ACTIVE_ADD_TO_REPO | 21 |
| ACTIVE_RENAME_OR_MOVE | 2 |
| DUPLICATE_TRACKED_ELSEWHERE | 20 |

## Recovered active source

| Canonical path | Classification | Confidence |
|---|---|---|
| pull_actionnetwork_win_totals_api.py | ACTIVE_ADD_TO_REPO | HIGH |
| pull_fanduel_win_totals.py | ACTIVE_ADD_TO_REPO | HIGH |
| pull_bettingpros_caesars_win_totals.py | ACTIVE_ADD_TO_REPO | HIGH |
| append_market_history.py | ACTIVE_ADD_TO_REPO | HIGH |
| build_daily_market_movement_report.py | ACTIVE_ADD_TO_REPO | HIGH |
| build_market_arbitrage_report.py | ACTIVE_ADD_TO_REPO | HIGH |
| pull_cfbd_lines_2026.py | ACTIVE_ADD_TO_REPO | HIGH |
| build_season_game_lines_2026.py | ACTIVE_ADD_TO_REPO | HIGH |
| pull_theodds_ncaaf_lines_2026.py | ACTIVE_ADD_TO_REPO | HIGH |
| build_theodds_season_lines_2026.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/odds/append_sgo_game_book_line_history.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/odds/append_game_line_history.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/agents/clean_daily_game_line_moves.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/ratings/build_all_ratings_latest.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/projections/build_game_projection_sources_2026.py | ACTIVE_RENAME_OR_MOVE | HIGH |
| scripts/projections/build_game_projection_blend_2026.py | ACTIVE_RENAME_OR_MOVE | HIGH |
| scripts/research/build_market_implied_power_ratings.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/site/build_ratings_view.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/site/build_shadow_team_game_features.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/site/build_saturday_shadow_component_predictions.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/audit/audit_market_shadow_production_layer.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/audit/audit_saturday_shadow_production_integration.py | ACTIVE_ADD_TO_REPO | HIGH |
| scripts/markets/pull_actionnetwork_playoff_futures.py | ACTIVE_ADD_TO_REPO | HIGH |

## Canonicalized duplicate references

| Former path | Canonical tracked path |
|---|---|
| scripts/odds/pull_actionnetwork_visible_dk_win_totals.py | odds/pull_actionnetwork_visible_dk_win_totals.py |
| scripts/odds/merge_visible_dk_win_totals.py | odds/merge_visible_dk_win_totals.py |
| pull_actionnetwork_conference_futures_api.py | pulls/pull_actionnetwork_conference_futures_api.py |
| scripts/odds/quarantine_bad_draftkings_win_total_rows.py | odds/quarantine_bad_draftkings_win_total_rows.py |
| scripts/odds/pull_actionnetwork_ncaaf_game_lines_2026.py | odds/pull_actionnetwork_ncaaf_game_lines_2026.py |
| scripts/odds/build_actionnetwork_season_lines_2026.py | odds/build_actionnetwork_season_lines_2026.py |
| scripts/odds/build_game_line_movement_report.py | odds/build_game_line_movement_report.py |
| scripts/injuries/pull_cfbdepth_injuries.py | injuries/pull_cfbdepth_injuries.py |
| scripts/injuries/pull_cfbdepth_article_bodies.py | injuries/pull_cfbdepth_article_bodies.py |
| scripts/agents/build_daily_betting_angles.py | agents/build_daily_betting_angles.py |
| scripts/agents/append_daily_game_line_edges.py | agents/append_daily_game_line_edges.py |
| scripts/agents/prepend_game_line_moves_to_daily_betting_angles.py | agents/prepend_game_line_moves_to_daily_betting_angles.py |
| scripts/agents/prepend_injury_alerts_to_daily_betting_angles.py | agents/prepend_injury_alerts_to_daily_betting_angles.py |
| scripts/injuries/build_game_injury_scores.py | injuries/build_game_injury_scores.py |
| scripts/ratings/pull_sagarin_ratings.py | ratings/pull_sagarin_ratings.py |
| scripts/ratings/parse_massey_visible_ratings.py | ratings/parse_massey_visible_ratings.py |
| scripts/ratings/pull_donchess_ratings.py | ratings/pull_donchess_ratings.py |
| scripts/ratings/append_ratings_history.py | ratings/append_ratings_history.py |
| scripts/ratings/build_ratings_movement.py | ratings/build_ratings_movement.py |
| scripts/email/send_daily_betting_angles_email.py | email/send_daily_betting_angles_email.py |

## Safety findings

- No embedded credential values were detected; environment-variable names were not treated as values.
- Absolute local-path findings: 0.
- No raw data, logs, caches, databases, spreadsheets, generated HTML, or provider responses were copied.
- Compatibility fallbacks remain temporarily and are surfaced by the automation audit.

## Canonical runtime bootstrap

The permanent reviewed bootstrap allowlist is the explicit `CANONICAL_RUNTIME_BOOTSTRAP_PATHS` mapping in the reconciliation builder. It contains exactly 22 active registered sources: 20 canonicalized duplicate paths and two structured projection paths. Membership does not depend on whether a canonical runtime copy has already been installed.

The generated bootstrap artifact reports each path as `PENDING_INSTALL`, `INSTALLED_MATCH`, `INSTALLED_MISMATCH`, or `EQUIVALENT_MISSING`. Installed canonical copies are validated against repository source; pre-install compatibility copies are validated when they provide migration evidence. Old compatibility copies are not deleted.

Current bootstrap status: PENDING_INSTALL=22.

The authoritative bootstrap artifact is `data/audit/canonical_runtime_bootstrap_manifest.csv`.

## Other recovered source

These newly tracked active files already exist at their canonical runtime paths and are not part of the bootstrap manifest expansion:

- append_market_history.py
- build_daily_market_movement_report.py
- build_market_arbitrage_report.py
- build_season_game_lines_2026.py
- build_theodds_season_lines_2026.py
- pull_actionnetwork_win_totals_api.py
- pull_bettingpros_caesars_win_totals.py
- pull_cfbd_lines_2026.py
- pull_fanduel_win_totals.py
- pull_theodds_ncaaf_lines_2026.py
- scripts/agents/clean_daily_game_line_moves.py
- scripts/audit/audit_market_shadow_production_layer.py
- scripts/audit/audit_saturday_shadow_production_integration.py
- scripts/markets/pull_actionnetwork_playoff_futures.py
- scripts/odds/append_game_line_history.py
- scripts/odds/append_sgo_game_book_line_history.py
- scripts/ratings/build_all_ratings_latest.py
- scripts/research/build_market_implied_power_ratings.py
- scripts/site/build_ratings_view.py
- scripts/site/build_saturday_shadow_component_predictions.py
- scripts/site/build_shadow_team_game_features.py

The canonical bootstrap remains a separate controlled deployment after review and merge.
Removing obsolete compatibility copies remains out of scope and requires separate review.
