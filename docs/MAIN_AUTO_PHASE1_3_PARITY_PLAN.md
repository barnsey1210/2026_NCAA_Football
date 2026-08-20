# MAIN to AUTO parity plan — Phases 1–3

Date: 2026-08-20

Scope: source audit, dependency-closure correction, and deployment rehearsal only. No files were copied to `NCAAF_AUTO`; no provider requests, publication, or navigation changes were made.

## 1. Fast publication wrapper reconciliation

The AUTO wrapper contained production safety behavior that had regressed in MAIN. The reviewed MAIN source now matches AUTO byte-for-byte and preserves:

- quota preflight before a provider request;
- fail-closed behavior when quota state is unavailable or at reserve;
- a bundle composed from MAIN `war-room.html` and AUTO runtime health/matrix JSON;
- targeted `--war-room-check` / `--war-room-push` publication;
- no direct copy of runtime JSON into MAIN before bundle validation.

The unsafe MAIN behavior removed by this reconciliation directly copied the runtime JSON into MAIN and invoked the unrestricted `--check` / `--push` modes.

## 2. AUTO-only source promoted for parity

`config/market_shadow_production.json` exists in AUTO and is an active dependency of the Saturday Shadow builder and its production-layer audit. It is now represented in MAIN and in the deployment manifest as the existing operational configuration. This promotion does not change the Shadow formula and does not characterize that formula as the canonical historical model.

No other AUTO-only implementation was identified as safer or newer than MAIN in this bounded audit. The remaining differing files require MAIN-to-AUTO replacement, not reverse promotion.

## 3. Corrected manifest closure

The manifest now contains 156 unique regular files. It includes:

- every script named by `config/daily_stages.json` (87 unique scripts);
- projection resolver and Massey helper dependencies required by those scripts;
- the active Shadow production configuration;
- public page and publish contracts;
- War Room builders and validation;
- every static HTML/JavaScript input copied by the public builder;
- the Matchups monolith and canonical preseason database required to rebuild the matchup payload;
- the deployment-closure audit itself.

The three retired SportsGameOdds acquisition/normalization scripts were removed from the deploy manifest. Their copies may remain in AUTO as inert legacy files until a separate, approved cleanup; they are not part of the canonical daily registry or parity deployment.

`scripts/audit/audit_deployment_manifest_closure.py` validates source existence, uniqueness, daily-registry inclusion, local `scripts.*` Python imports, and optional byte parity against a deployment target.

## 4. Current MAIN/AUTO delta

Against the corrected 156-file manifest:

- byte-identical: 105
- missing from AUTO: 16
- different in AUTO: 35

### Missing from AUTO

- `data/site/shadow_model_performance.json`
- `config/public_page_data_contracts.json`
- `scripts/projections/build_current_game_projection_contract.py`
- `scripts/projections/build_massey_game_projections_2026.py`
- `scripts/projections/collect_massey_games_2026_safari.py`
- `scripts/projections/projection_resolver.py`
- `scripts/projections/refresh_massey_game_projections_2026.py`
- `scripts/site/build_shadow_model_performance.py`
- `scripts/site/build_war_room_page.py`
- `scripts/audit/audit_projection_fbs_production_coverage.py`
- `scripts/audit/validate_projection_resolver.py`
- `schedule.html`
- `team.html`
- `scripts/audit/audit_deployment_manifest_closure.py`
- `scripts/odds/append_current_market_book_history.py`
- `scripts/site/build_projection_source_status_view.py`

### Different in AUTO

- `betting_v2.html`
- `conferences.html`
- `dashboard_playoff_edges.js`
- `data/snapshots/preseason/preseason_db.json`
- `config/daily_stages.json`
- `config/public_publish_manifest.json`
- `daily_market_update.sh`
- `matchup.html`
- `matchup_workspace.js`
- `matchups.html`
- `openers.html`
- `ratings/append_ratings_history.py`
- `ratings/pull_sagarin_ratings.py`
- `scripts/audit/audit_data_propagation.py`
- `scripts/control/run_data_refresh.py`
- `scripts/markets/build_current_market_contract.py`
- `scripts/projections/build_game_projection_blend_2026.py`
- `scripts/projections/build_game_projection_sources_2026.py`
- `scripts/publish/check_public_site.py`
- `scripts/site/apply_shared_war_room_shell.py`
- `scripts/site/build_matchups_view.py`
- `scripts/site/build_public_site.py`
- `scripts/site/build_ratings_view.py`
- `tests/test_betting_model_performance_integration.py`
- `config/team_aliases.json`
- `scripts/site/build_odds_screen_v2.py`
- `team_coach_card.js`
- `scripts/postgame/build_shadow_team_game_features_2026.py`
- `scripts/ratings/build_all_ratings_latest.py`
- `scripts/ratings/build_active_2026_ratings_master.py`
- `scripts/ratings/merge_live_rating_change_status.py`
- `scripts/history/build_matchup_line_history_clean.py`
- `scripts/agents/build_daily_betting_angles_html.py`
- `scripts/audit/audit_current_market_propagation.py`
- `scripts/site/build_saturday_shadow_component_predictions.py`

## 5. Rehearsal result

An isolated deployment to a new directory under `/private/tmp` copied all 156 allowlisted files and passed pre-copy and post-copy shell/Python syntax checks. The closure audit then confirmed byte parity for all 156 files. The market profile plan resolved successfully and included market acquisition, line history, matchup, Shadow, odds payload, site build, validation, and publication stages. No network stage was executed. The public build and validator passed after seeding the isolated runtime with a snapshot of current generated `data/site` artifacts; those mutable artifacts intentionally remain outside the source deployment manifest.

The AUTO-only `build_schedule_persistent.py` was not promoted because it hardcodes the AUTO checkout and depends on additional AUTO-only sources. Its optional execution hook was removed from the MAIN-owned public builder, making the leftover AUTO file inert after parity deployment. The two stale SGO stage identifiers were also removed from the canonical shell order; neither the MAIN daily registry nor entrypoint contains an active SGO stage.

The rehearsal initially exposed that `deploy/deploy_to_auto.sh` rejected the repository's configured `github-ncaaf-site` SSH host alias. The exact canonical repository alias was added to the existing remote allowlist; the deployer then passed. The remote identity check remains restrictive.

## 6. Approved deployment sequence (not executed)

1. Review and commit the bounded MAIN source changes.
2. Re-run the manifest closure audit from the clean committed revision.
3. Record current AUTO source parity and preserve the deployer's automatic per-file rollback copy.
4. Run `deploy/deploy_to_auto.sh` against the explicit `/Users/jameslindesmith/NCAAF_AUTO` target without `--allow-dirty`.
5. Run the closure audit with `--target /Users/jameslindesmith/NCAAF_AUTO` and require 156/156 byte parity.
6. Run offline syntax and profile-plan validation in AUTO.
7. Run projection resolver, public contract, propagation, and public-site validation gates using existing local artifacts only.
8. Only after those gates pass, separately authorize a controlled runtime build. Provider acquisition and publication remain separate approvals.
9. Keep navigation unchanged until runtime and publication parity are proven.

## 7. Stop conditions

Do not proceed to runtime execution or publication if any manifest file is missing/different, any daily-stage script is outside the manifest, the AUTO worktree contains an unexpected overlapping modification, a projection/market contract validator fails, or the public bundle would include files outside the explicit publish allowlist.
