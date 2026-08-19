# War Room Command Center — Phase 1 Operational Data Plan

Status: Phase 1 data projection and the standalone V1 page are implemented.
Canonical publication wiring is present; navigation and live-season acceptance
remain pending. The audit below is retained as the original design record.

Governing specification: `docs/WAR_ROOM_COMMAND_CENTER_SPEC.md`.

## Current implementation reconciliation

- Public route: `war-room.html`; Home remains `index.html`.
- Page owner: `scripts/site/build_war_room_page.py`.
- Health owner: `scripts/war_room/build_war_room_health.py`.
- Matrix owner: `scripts/war_room/build_war_room_market_matrix.py`.
- Interactive refresh owner: `scripts/war_room/run_fast_market_refresh.py`.
- Published contracts: `data/site/war_room_health.json` and
  `data/site/war_room_market_matrix.json`.

The current V1 does not publish a separate `war_room_signals.json`; signal and
projection fields are adapted into the matrix from existing canonical owners.

## Phase 1 objective

Build three atomic, canonical operational views from existing domain owners:

- `data/site/war_room_market_matrix.json`
- `data/site/war_room_health.json`
- `data/site/war_room_signals.json`

The War Room is a projection/adapter layer. It does not select raw providers independently, calculate a competing model, rebuild betting angles, or infer healthy data from stale artifacts.

## Repository audit summary

| Domain | Current owner | Audit result | Phase 1 treatment |
|---|---|---|---|
| Site game identity | `data/snapshots/preseason/preseason_db.json` with CFBD overlay from `data/canonical/cfbd_schedule_2026.json` | 902 unique site `game_id` values; 777 currently have CFBD IDs and kickoff timestamps | Reuse site `game_id`; retain `cfbd_game_id` as alias. Do not create another identity matcher. |
| Current markets | `data/site/current_market_contract.json`, built by `scripts/markets/build_current_market_contract.py` | 902 games; 111 LIVE, 4 BACKUP_SOURCE, 787 MISSING at audit time; approved per-book spreads/totals and best-side quotes already exist | Consume only this contract for current quote selection. Never read provider files directly. |
| Market history | `data/odds/game_line_history.csv`, built by `scripts/odds/append_game_line_history.py` | 18,308 changed game/source states; append is state-idempotent | Reuse as observation history and seed evidence. Add a write-once first-observed registry; do not replace history. |
| Game projections | `data/projections/game_projection_blend_2026.csv` and its existing blend builder | 902 games; 765 spread and 765 total projections | Extend centrally with an explicit sign/freshness/version contract before War Room consumption. |
| Page matchup projection | `data/site/matchups_view.json` | 902 games, but it is a page adapter and currently differs from the projection CSV on 764/765 comparable spreads and 37 totals | Do not use as projection authority. Add a parity gate and resolve ownership before Phase 1 acceptance. |
| Shadow projections | `data/site/saturday_shadow_lines.json`, `saturday_shadow_component_predictions.json`, `postgame_shadow_updates.json`, and status rules | Schemas/provenance exist, but current preseason artifacts contain no live Shadow fair values | Reuse when populated; expose unavailable state now. Do not recalculate Shadow in the War Room builder. |
| Rating/provider status | `data/ratings/ratings_source_status.csv`, live change status, source-specific control status | Per-source coverage and timestamps exist, but no accepted target-week aggregate SHADOW/HYBRID/UPDATED resolver exists | Add one model-readiness reducer owned centrally and consumed by matrix/health. |
| Betting angles | `data/signals/game_betting_angles_2026.csv`, built by `scripts/signals/build_game_betting_angles_2026.py` | 2,079 angles across 829 games, up to 7 per game | Add a compact adapter only; do not duplicate angle logic. |
| Injury context | `data/injuries/injury_source_status.json` is the authority | Explicitly `SOURCE_NOT_CONFIGURED`, `MISSING`, `UNAVAILABLE`; legacy inputs are prohibited | Return `injury_rank: null` and unavailable reason. Do not rank legacy zero scores. |
| Operational health | `data/control/daily_run_status.json`, `data/qa/page_health_status.json`, `data/health/daily_run_health.json`, ratings/injury/current-market status | Useful evidence is distributed; some snapshots are older than current artifacts | Add a War Room health projection with source timestamps and explicit freshness; never relabel by build time. |

## Canonical field mapping

### Game and schedule fields

| War Room field | Existing source | Status | Rule |
|---|---|---|---|
| `game_id` | `preseason_db.games[].game_id` | EXISTS | Canonical site ID and join key. |
| `cfbd_game_id` | `preseason_db.games[].cfbd_game_id` | EXISTS, optional | External alias only. |
| `season` | canonical schedule season / CFBD overlay | EXISTS | Persist explicitly as `2026`; never infer in browser. |
| `week` | `preseason_db.games[].week` | EXISTS | Site week convention is authoritative for current pages. Preserve CFBD week separately if needed. |
| `date` | `preseason_db.games[].date` | EXISTS | ET presentation date. |
| `kickoff_time` | `preseason_db.games[].cfbd_start_date` | EXISTS for 777/902 | UTC timestamp; null with schedule status when unscheduled/unmatched. |
| `away_team`, `home_team` | `preseason_db.games[]` | EXISTS | Canonical display identity. |
| `neutral_site` | `preseason_db.games[].neutral_site` | EXISTS | Context/projection provenance. |
| `detail_href` | canonical Openers/Matchups routing convention | DERIVED ADAPTER | Link only; no copied matchup content. |

### Market fields

| War Room field | Existing source | Status | Rule |
|---|---|---|---|
| `market_release_timestamp` | no write-once canonical owner | NEW CONTRACT | Store first accepted observation permanently. Semantics must be labeled `FIRST_ACCEPTED_OBSERVATION`, not claimed sportsbook-post time. |
| `market_release_source`, `market_release_quote_id` | current market/history evidence | NEW CONTRACT | Provenance for the immutable first-observed value. |
| `market_freshness_status` | current market contract | EXISTS | Preserve LIVE/BACKUP_SOURCE/STALE/MISSING semantics. |
| `market_updated_at` | `current_market_updated_at` and selected quote timestamps | EXISTS | Source timestamp, not War Room build time. |
| `approved_book_quotes` | `current_market_contract.games[].quotes` | EXISTS | Pass through compact fresh per-book spread/total quotes. |
| `best_spread_book`, `best_spread_line`, `best_spread_price` | current contract `best.home_spread` / `best.away_spread` | DERIVED ADAPTER | Choose the model-supported side; source selection remains owned by current-market contract. |
| `best_total_book`, `best_total_line`, `best_total_price` | current contract `best.over` / `best.under` | DERIVED ADAPTER | Choose the model-supported side. |
| Pinnacle reference | current contract `quotes.Pinnacle` / `reference` | EXISTS | Retain as sharp context and historical input; it does not override executable BEST. |

The write-once release registry should be a small central domain contract, proposed as `data/odds/game_market_first_seen_2026.json`. It is reduced from accepted market observations, atomically updated, and immutable per `game_id × market` after first acceptance. Existing history remains the detailed authority.

### Projection, edge, and state fields

| War Room field | Existing source | Status | Rule |
|---|---|---|---|
| `model_spread` | current game-projection blend | EXISTS BUT CONTRACT GAP | Publish in bookmaker home-line convention: negative means home favored. Include version, sources, cutoff, and built/source timestamps. |
| `model_total` | current game-projection blend | EXISTS BUT CONTRACT GAP | Include version, sources, cutoff, and timestamps. |
| `spread_edge`, `spread_side` | model + current contract best-side quote | DERIVED ADAPTER | Home edge = `best_home_line - model_home_line`; away edge = `best_away_line - (-model_home_line)`. Select the larger positive executable edge. No minimum display filter. |
| `total_edge`, `total_side` | model + best over/under | DERIVED ADAPTER | Over edge = `model_total - best_over_line`; under edge = `best_under_line - model_total`. Select the larger positive executable edge. |
| edge color | numeric edge | DERIVED ADAPTER | Green ≥3; yellow 2–2.9; red <2, as specified. Color is presentation metadata, not a data filter. |
| `state` | Shadow artifacts + provider readiness + freshness | NEW REDUCER | STALE/SHADOW/HYBRID/UPDATED with evidence; never infer from clock alone. |
| `state_reason`, `provider_states`, `required_providers` | ratings/Shadow status | NEW REDUCER | Explain which components are actual, Shadow, missing, or stale. |

Before implementation, the projection owner must expose one normalized contract, proposed as `data/site/current_game_projection_contract.json`, built by extending the existing projection flow. It must not be produced from `matchups_view.json` or scraped HTML. The current disagreement between projection CSV and page adapter is a Phase 1 blocking acceptance issue, not permission to choose whichever value is convenient.

State rules:

- `STALE`: a required market or model/rating input violates freshness policy. This warning overrides normal readiness display.
- `SHADOW`: a new market exists and an accepted Shadow projection is available while required current provider updates are incomplete.
- `HYBRID`: at least one required provider component is accepted current and at least one remains an accepted Shadow estimate.
- `UPDATED`: all scheduled required components are accepted current for the target week and no Shadow estimate remains.

### Signal and injury fields

| War Room field | Existing source | Status | Rule |
|---|---|---|---|
| `signal_count` | game betting angles grouped by `game_id` | DERIVED ADAPTER | Count existing angles only. |
| `signal_badges` | angle label/type/tier/direction | DERIVED ADAPTER | Compact top-priority subset with source row references. |
| `signal_detail_href` | existing Openers/Matchups route | DERIVED ADAPTER | Navigate outward; no copied explanation engine. |
| `injury_rank` | no safe current source | MISSING/BLOCKED | Null while source status is unavailable. |
| `injury_status`, `injury_reason`, `injury_updated_at` | injury source status | EXISTS | Explicitly show unavailable/stale rather than healthy/zero. |

When a validated current 138-team injury score exists, injury rank may be added as a deterministic central injury-contract field (`1` healthiest, `138` greatest concern, stable tie policy). The War Room must consume that rank, not calculate a page-local ranking.

### Health fields

`war_room_health.json` requires a new operational projection, not a new acquisition path. It should include:

- `generated_at`, `schema_version`, `overall_status`
- schedule, projection, market, market-history, Shadow, ratings, signals, and injuries components
- for each component: `status`, `source_artifact`, `source_updated_at`, `observed_at`, `age_seconds`, `freshness_limit_seconds`, `coverage`, `warnings`, and `blocking`
- market coverage counts by spread/total and freshness status
- projection coverage counts and model versions
- provider current/Shadow/missing counts used by the readiness reducer
- first-seen registry coverage and last successful append
- existing run ID/stage status where available

Build time alone must never turn stale source data green.

## Proposed output boundaries

### `war_room_market_matrix.json`

One row per canonical game. Contains identity/schedule, normalized current model, compact approved-book market projection, selected executable spread/total opportunities, edge/color metadata, readiness state/evidence, release timestamp provenance, injury rank/status, and signal count/link. It contains no matchup-detail payloads.

### `war_room_signals.json`

One compact entry per game with zero or more existing angle references: `game_id`, count, highest tier, badges, supported side/direction, source keys, and detail link. It performs sorting/compaction only.

### `war_room_health.json`

One coherent operational status projection described above. It is the only War Room health input.

## Phase 1 implementation sequence

1. **Freeze schemas and semantics.** Add central contract declarations for `current_game_projection`, `market_first_seen`, `war_room_market_matrix`, `war_room_signals`, and `war_room_health`. Freeze spread sign convention, edge formulas, freshness limits, state precedence, and release-timestamp semantics.
2. **Resolve projection authority.** Trace and eliminate the current projection CSV/page-adapter divergence through the existing projection propagation path. Do not patch War Room values independently. Add parity audits from projection owner to downstream page adapters.
3. **Build the write-once market-first-seen reducer.** Seed only from accepted historical observations with provenance. New runs may fill missing keys but may never rewrite an existing first timestamp. Add replay/idempotency and chronological tests.
4. **Build the model-readiness reducer.** Consume accepted Shadow output and provider status; emit state plus component evidence. It must return unavailable before genuine postgame values exist.
5. **Build the signals adapter.** Group existing `game_betting_angles_2026.csv` rows without recomputing angles.
6. **Build the health projector.** Merge existing status evidence and calculate freshness/coverage under explicit policy.
7. **Build the market-matrix projector.** Join only by canonical `game_id`, apply the frozen sign/edge formulas, preserve all games, and write atomically.
8. **Add audits and propagation checks.** Validate source ownership, one-row-per-game identity, quote selection parity, sign correctness, first-seen immutability, signal parity, unavailable-injury behavior, state evidence, timestamps, and no stale-as-current behavior.
9. **Run dark in NCAAF_AUTO after separate approval.** Generate the three files without page consumers or publication. Compare repeated runs and current domain owners before Phase 2 is considered.

## Proposed implementation surfaces

Exact names may be finalized with the schemas, but responsibility should remain separated:

- `scripts/war_room/build_market_first_seen.py`
- `scripts/war_room/build_model_readiness.py`
- `scripts/war_room/build_war_room_signals.py`
- `scripts/war_room/build_war_room_health.py`
- `scripts/war_room/build_war_room_market_matrix.py`
- `scripts/audit/audit_war_room_contracts.py`

These are reducers/adapters only. They make no network calls and do not invoke provider acquisition.

## Acceptance gates

- Exactly one market-matrix row per canonical site `game_id`; no fuzzy identity joins.
- Every scheduled game remains present even when markets, projections, signals, or injuries are missing.
- Schedule identity equals the existing 902-game registry; CFBD alias mismatches quarantine rather than remap.
- Projection values and versions match the resolved central projection owner exactly.
- Current quote values and source/freshness match `current_market_contract.json` exactly.
- Side-aware spread and total tests cover home/away favorite, over/under, pick'em, equal lines with different prices, unavailable sides, and neutral games.
- First-observed timestamps survive replay and later line movement unchanged.
- Signal counts and referenced angle IDs/keys reconcile to the existing angle artifact.
- Injury rank is null while `legacy_inputs_allowed=false`; zero is never inferred.
- SHADOW/HYBRID/UPDATED requires component evidence; STALE cannot be hidden by a newer build timestamp.
- All outputs use atomic writes, schema versions, source timestamps, input hashes/versions, and an audit summary.
- No Openers, Matchups, Betting, homepage, publish manifest, or current acquisition job changes in Phase 1 dark mode.

## Phase 1 exit condition

The original target required three dark-run artifacts. The implemented V1 uses
two published contracts: health and market matrix. Production acceptance still
requires deterministic outputs, source parity, freshness evidence, and explicit
unavailable states. Unavailable injury or projection sources must not be
bypassed to make the dataset appear complete.
