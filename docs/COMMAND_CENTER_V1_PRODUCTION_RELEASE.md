# Command Center V1 Production Release

Date: 2026-08-19

## Release boundary

Command Center V1 remains the standalone `war-room.html` page. This release
does not modify Home, add navigation, redesign the page, change Shadow or
market logic, or add Cloudflare/fast-endpoint behavior.

## Production source group

- `scripts/site/build_war_room_page.py`
- `scripts/war_room/analyze_fast_market_latency.py`
- `scripts/war_room/build_war_room_health.py`
- `scripts/war_room/build_war_room_market_matrix.py`
- `scripts/war_room/record_fast_refresh_history.py`
- `scripts/war_room/run_fast_market_refresh.py`

## Publication and orchestration group

- `config/daily_stages.json`
- `config/public_page_data_contracts.json`
- `config/public_publish_manifest.json`
- `daily_market_update.sh`
- `scripts/site/build_public_site.py`
- `scripts/publish/check_public_site.py`
- `scripts/publish/publish_site.sh`

Canonical site-build order is health, market matrix, page build, then public
packaging and validation. `run_fast_market_refresh.py` remains the sole
interactive Saturday operator acquisition path.

## Release artifacts

- `war-room.html`
- `data/site/war_room_health.json`
- `data/site/war_room_market_matrix.json`

The JSON artifacts retain their existing schema versions and owners. Generated
artifacts must be rebuilt from accepted runtime inputs and validated immediately
before publication; checked-in copies are not proof of current market freshness.

## Documentation group

- `docs/WAR_ROOM_COMMAND_CENTER_SPEC.md`
- `docs/WAR_ROOM_COMMAND_CENTER_PHASE1_PLAN.md`
- `docs/WAR_ROOM_DATA_ARCHITECTURE.md`
- `docs/PROJECTION_CONSUMER_MIGRATION_MAP.md`
- `docs/PROJECTION_ENGINE_PHASE2_READINESS_AUDIT.md`
- `docs/CHATGPT_HANDOFF_PROJECTION_PIPELINE_COMMAND_CENTER.md`
- `docs/COMMAND_CENTER_V1_PRODUCTION_RELEASE.md`
- `CURRENT_PRIORITIES_2026_NCAAF_UPDATED_2026-08-11.md`

## Explicit exclusions

- `index.html` and `scripts/site/build_war_room_home.py`
- navigation shell changes
- model formulas, Shadow calculations, and state-machine logic
- market calculations and provider selection
- Cloudflare or alternate fast endpoints
- runtime raw odds data, research trees, reports, archives, backups, prototypes,
  local audits, and credential files

## Release acceptance

1. All listed source and artifact paths exist.
2. Python sources pass offline syntax validation.
3. Both JSON contracts parse and retain their declared V1 schemas.
4. `war-room.html` references both JSON contracts.
5. The public-site validator passes on the packaged site.
6. Home has no release diff.
7. Stage and commit only the explicit groups above after reviewing generated
   artifact freshness; never use `git add .`.
