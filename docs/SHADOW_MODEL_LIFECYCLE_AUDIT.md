# Shadow Model Lifecycle Audit and Historical Rehearsal

_Audit date: 2026-08-24_  
_Scope: production architecture and an offline 2025 artifact replay; no provider calls, formula changes, resolver changes, UI changes, or publication_

## Executive conclusion

The repository contains every major computational building block needed to move from a final game to a next-game Shadow projection. It does **not** yet contain one event-driven, persisted lifecycle that proves the whole sequence automatically.

The scheduled `full` profile is the closest end-to-end implementation: it refreshes ratings and projections, builds results and postgame features, applies the frozen Shadow models, rebuilds the canonical projection contract, and publishes downstream artifacts. The dedicated `postgame` profile is intentionally narrower: it refreshes schedule/results/postgame data and rebuilds Shadow outputs, but it does **not** refresh ratings or the ordinary projection sources. Neither profile is triggered by a newly final game; both are operator/schedule initiated.

The offline 2025 rehearsal proves the historical information-state chain at the artifact level. For a representative Week 8 to Week 9 transition, preserved final scores, pregame provider states, frozen Shadow forecasts, later provider updates, first market observations, subsequent checkpoints, and closing lines all join deterministically by canonical game/team identifiers. It does not prove that the current 2026 live scripts can replay that historical week from raw inputs, because the live scripts are season/path specific and no immutable workflow event ledger or complete historical raw CFBD cache is wired to them.

## Status definitions

- **COMPLETE**: executable owner, durable output, validation, and an active trigger/path exist.
- **PARTIAL**: the computation and artifacts exist, but activation, orchestration, persistence, or current-season proof is incomplete.
- **NOT IMPLEMENTED**: the required production behavior has no owner.

## Lifecycle map

```text
CFBD schedule/result state
        |
        v
canonical game_results_2026.json/.csv
        |
        v
week-scoped plays/drives/havoc caches
        |
        v
postgame team-game feature tables
        |
        +---------------- stale pregame SP+/Sagarin + closing market
        v
no-lookahead Shadow team-game features
        |
        +---------------- frozen model_artifacts.json (no refit)
        v
Shadow SP+, Shadow Sagarin, enhanced SP+ O/D components
        |
        v
current_game_projection_contract.json
        |
        v
saturday_shadow_lines.json + War Room market matrix
        |
        +---------------- current/first/history market contracts
        v
opener and later-market comparison
```

This is a data-flow graph, not a persisted workflow state machine. The War Room derives a current display state from the latest artifacts each time it builds.

## Component inventory

| Component | Implemented | Builder / controller | Primary input | Primary output | Refresh trigger | Status |
|---|---|---|---|---|---|---|
| Schedule and final detection | Yes | `scripts/schedule/pull_cfbd_schedule_2026.py`; `scripts/results/build_game_results_2026.py` | CFBD schedule overlay; canonical preseason game IDs | `data/canonical/cfbd_schedule_2026.json`; `data/canonical/game_results_2026.json`; `.csv`; audit | Scheduled `full` or `postgame` profile | **PARTIAL**: automatic within a run, not event-triggered |
| Postgame raw acquisition | Yes | `scripts/postgame/pull_cfbd_postgame_2026.py` | Completed canonical results; CFBD plays/drives/havoc | `data/canonical/postgame/2026/week_XX/*.json.gz`; audit | `full` or `postgame` profile | **PARTIAL**: live 2026 final-game acceptance not yet proved |
| Postgame feature construction | Yes | `scripts/postgame/build_postgame_features_2026.py` | Results and week caches | three season-to-date team-game CSVs; audit | Immediately after raw postgame acquisition | **PARTIAL**: zero completed 2026 games in checked artifacts |
| Ratings acquisition | Yes | live-source wrappers plus `scripts/ratings/*`, `ratings/pull_sagarin_ratings.py`, reference pullers | SP+, FPI, TeamRankings, Sagarin and references | candidates, accepted files, raw archives/status | `full` and `openers`; schedule/operator initiated | **PARTIAL** to lifecycle: not triggered by finals |
| Ratings normalization/history | Yes | `build_all_ratings_latest.py`; `build_active_2026_ratings_master.py`; change-status/history/movement builders | accepted source panels | latest/master/status/history/movement files | after ratings acquisition | **COMPLETE** as a scheduled batch path |
| Shadow team-game feature state | Yes | `scripts/postgame/build_shadow_team_game_features_2026.py` | finals, closing market, entering ratings, SP+/Sagarin snapshots, postgame features, next-game schedule | `data/research/shadow_live_feature_constructor/team_game_features_2026.{csv,json}`; audit | `shadow_models` stage | **PARTIAL**: current artifact awaits finalized games |
| Shadow component inference | Yes | `scripts/site/build_saturday_shadow_component_predictions.py` | frozen validated model artifact; eligible team-game features; source states; matchup list | `data/site/saturday_shadow_component_predictions.json` | `shadow_models` stage | **PARTIAL**: executable and fixture-tested, no live activated 2026 rows checked |
| Canonical Shadow projections | Yes | `scripts/projections/build_current_game_projection_contract.py` | component predictions and canonical game/source projections | `data/site/current_game_projection_contract.json`; audit | projection stage and Shadow stage | **PARTIAL**: activation depends on complete named inputs |
| Site-facing Shadow lines | Yes | `scripts/site/build_saturday_shadow_lines.py` | canonical projection contract and component/status context | `data/site/saturday_shadow_lines.{json,csv}`; append-only snapshots when available | `shadow_models` stage | **PARTIAL**: current output has no available canonical Shadow rows |
| Market comparison | Yes | projection/War Room/history adapters | Shadow values; fast/current market; line history | War Room matrix, matchup history, Saturday Shadow snapshots | Market/Shadow/site builds | **PARTIAL**: first-release timing and lifecycle transitions are not centrally persisted |
| Lifecycle controller | No | none | would consume final/provider/market events | would own transition/event ledger and checkpoints | none | **NOT IMPLEMENTED** |

## 1. Results ingest

### Current implementation

`scripts/results/build_game_results_2026.py` reads `data/canonical/cfbd_schedule_2026.json`, selects rows marked completed with valid scores, maps them deterministically to the canonical schedule, and writes:

- `data/canonical/game_results_2026.json`
- `data/canonical/game_results_2026.csv`
- `data/audits/game_results_2026_audit.json`

The audit records completed, matched, unmatched, ambiguous, and closing-market coverage counts. The JSON records `generated_at`; completed rows contain the canonical game identity, scores, schedule context, and available market-close fields.

`scripts/postgame/pull_cfbd_postgame_2026.py` then selects the latest completed week by default. It writes gzip-preserved plays, drives, and havoc responses under `data/canonical/postgame/2026/week_XX/`, records request and cache metadata, and fails if a completed game is missing required PBP. Its `--check-cache-only` mode can validate cache readiness without network access.

### Answers

- **Are completed games automatically ingested?** Within an invoked `full` or `postgame` run, yes. There is no watcher or final-game event trigger; ingestion is only as automatic as the external schedule/operator that invokes the profile.
- **Are results stored canonically?** Yes, in the canonical JSON/CSV above, with mapping audit evidence.
- **Is there a completion state?** Yes at the source/result-row level (`completed` and final scores) and in audit counts. There is no durable `GAME_FINAL` transition event or processed-through watermark owned by a central controller.

### Current proof

The checked 2026 artifacts were generated on 2026-08-10 and report zero completed games. That is an expected preseason state, but it means real final detection, PBP acceptance, and idempotent rerun behavior have not yet been accepted on a live 2026 game.

## 2. Ratings refresh

### Source inventory

| Source | Refresh/parse owner | Normalized or accepted output | Timestamp/change handling | Lifecycle note |
|---|---|---|---|---|
| SP+ | live rating wrapper -> `test_rating_sources.py` / `parse_rating_source_tables.py` / `accept_live_rating_candidates_with_status.py` | `data/ratings/spplus_2026_latest.csv`; consolidated into `ratings_latest.csv` | `snapshot_date`, `pulled_at`; accepted-candidate comparison stores `change_status`, `last_changed_at`, changed teams/fields | Active team composite and projection source |
| FPI | same candidate/acceptance path | `data/ratings/fpi_2026_latest.csv`; consolidated latest/master | same content-change state for accepted panels | Active team composite and projection source |
| TeamRankings | same candidate/acceptance path | `data/ratings/teamrankings_2026_latest.csv`; consolidated latest/master | same content-change state for accepted panels | Active team composite and projection source |
| Sagarin | `ratings/pull_sagarin_ratings.py` | `data/ratings/external_sources/sagarin_latest.csv`; game predictions and observed history; consolidated latest/master | raw HTML, `snapshot_date`, `pulled_at`, parse audit/history | Sagarin Rating is in team composite; named game/Shadow inputs remain separate |
| DRatings/Donchess | `ratings/pull_donchess_ratings.py`; game feed `scripts/projections/pull_dratings_ncaaf_predictions.py` | Donchess reference rating; `dratings_ncaaf_predictions_latest.csv` | snapshot/pull timestamps and game-feed audit | DRatings game prediction is Standard Spread input; rating is reference only |
| Massey | `ratings/parse_massey_visible_ratings.py`; game projections `refresh_massey_game_projections_2026.py` | reference rating and `massey_game_projections_2026.csv` | parsed snapshot/pull metadata | Massey Dual is Standard Total input; not a team-composite source |

Normalization produces:

```text
ratings_latest.csv
  -> ratings_master_latest.csv
  -> ratings_source_status.csv
  -> ratings_history.csv
  -> ratings_movement.csv
  -> ratings_view.json
```

The active team composite in `ratings_master_latest.csv` is SP+ / FPI / TeamRankings / Sagarin Rating at 25% each. Other sources remain reference or game-projection inputs.

### Trigger answer

Ratings refresh is **schedule/profile based**, not triggered by game completion or provider release. `full` and `openers` run ratings acquisition/normalization. The `postgame` profile explicitly skips both. Therefore “game finished” does not itself cause a provider poll, and a postgame-only run may legitimately calculate Shadow from stale entering panels while awaiting later published provider updates.

## 3. Shadow calculations

### Formula authority (unchanged by this audit)

The live canonical frozen artifact is `data/research/shadow_validated_models_v1/model_artifacts.json` (`shadow-validated-2026.1`). It applies standardized ridge models trained on preserved 2025 provider deltas and validated out of sample on 2024 without refitting.

- **Shadow Spread**: predict the forthcoming SP+ rating change and Sagarin Predictor change for each team; construct provider-specific home fair spreads using their defined HFA/sign convention; final canonical spread is `(Shadow SP+ home fair spread + Shadow Sagarin home fair spread) / 2`.
- **Shadow Total**: predict updated SP+ offense and defense components; assemble `0.5 * (home updated offense + away updated defense) + 0.5 * (away updated offense + home updated defense)`.

The frozen ridge coefficients, standardization means/standard deviations, feature order, model version, training season, and OOS validation claim are persisted in that artifact. FPI and TeamRankings are explicitly excluded from Shadow inference.

`config/market_shadow_production.json` still contains older experimental market/SP+ and 60/40 total formula metadata. Current canonical component and line builders take model identities/formulas from the validated model artifact and projection contract. The stale config is a documentation/legacy-risk item and must not be mistaken for formula authority.

### Dependencies and activation

The feature constructor requires, per completed team-game, a canonical final, usable closing spread/total, an entering SP+ snapshot strictly before kickoff, an entering Sagarin snapshot strictly before kickoff, the frozen historical transform state, applicable postgame PBP features, and a deterministically mapped next game. It records rejection reasons and snapshot timestamps.

Component inference can distinguish baseline/context rows from genuine postgame-updated rows. Canonical availability is model-specific:

- Shadow Spread requires valid predicted Shadow SP+ **and** Shadow Sagarin values for the scheduled game.
- Shadow Total requires the enhanced SP+ offense/defense inputs for both teams.
- Missing inputs remain unavailable with explicit missing reasons; the canonical models are not silently renormalized or replaced.

The status rules distinguish pending, partial, and complete. A bye opponent may retain its unchanged state. One updated team can support a partial operational state only when the contract's eligibility rules are met; it does not manufacture a missing provider component.

### Availability and persistence answers

- **When does Shadow become available?** After a completed prior game is canonical, all required postgame/input cutoffs pass, a next game maps, and the named model's complete required component set is present. It is not tied to a wall-clock hour in code.
- **What happens when sources are missing?** Feature/component audits record reasons and the canonical Shadow model remains unavailable for the affected game/model.
- **Are historical Shadow values stored?** Yes. Research-grade 2024/2025 predictions and comparisons are durable under `data/research/historical/shadow/`. Production `saturday_shadow_lines` appends `data/history/saturday_shadow_line_snapshots.csv` only when canonical Shadow rows are available. Component JSON itself is a latest-state artifact, not an append-only forecast ledger.

## 4. Next-week projections

The next-game map in `build_shadow_team_game_features_2026.py` selects the next scheduled game after the completed week and records `completed_week`, `next_game_week`, opponent, kickoff, and game ID. `build_saturday_shadow_component_predictions.py` converts the latest eligible team state into scheduled-game components. The canonical projection-contract builder then creates strict named game projections, and `build_saturday_shadow_lines.py` emits site-facing lines.

This can run automatically inside a profile, but the lifecycle has three timing limitations:

1. `postgame` does not refresh source ratings or ordinary projections.
2. `full` runs ratings/projections **before** postgame/Shadow in its stage order, but it is a fixed daily batch, not a provider-release watcher.
3. Latest component/projection artifacts have `generated_at`/`built_at`, source snapshot timestamps, and missing reasons, but there is no immutable per-version forecast ledger connecting “stale,” “Shadow,” “refreshed,” and “market first seen” transitions for every game.

The current fields can distinguish states analytically when source timestamps are present. They cannot guarantee a replayable operational sequence because current-state files may be overwritten and a page rebuild re-derives status.

## 5. Market comparison capability

### Production

Production can compare a named canonical Shadow projection with the current/reference/best-side market in `war_room_market_matrix.json` and `saturday_shadow_lines.json`. Durable market observations live in `data/odds/game_line_history.csv`, `data/odds/game_book_line_history.csv`, and `data/site/matchup_line_history.json`. The War Room fast path can append new market observations without recalculating model forecasts.

### Historical

The authoritative historical support is stronger:

- `historical_shadow_v1_premarket_game_predictions_2025.csv` contains stale, predicted Shadow, and later updated provider/game values frozen before market joining.
- `historical_game_market_timeline_2021_2025.csv` contains first observed, Saturday 11 PM, Sunday 12 AM/1 AM/2 AM/9 AM/2 PM/4 PM/9 PM, Monday, and close checkpoints with timestamps, consensus values, book counts, and per-book observations.
- `historical_market_line_history_2021_2025.csv` remains the authoritative long-form quote history.
- Shadow baseline/primary/checkpoint artifacts preserve provider-state provenance and stale-versus-Shadow comparisons.

Thus the repository can compare Shadow, stale rating forecasts, first available/consensus market states, later checkpoints, and close. “Consensus opener” must be named carefully: the timeline's `first_observed_consensus_*` is the consensus at the first preserved checkpoint, not necessarily the first quote from one book.

## 6. Historical rehearsal: 2025 Week 8 completion to Week 9 opener

### Method

The rehearsal was deliberately read-only. It did not rerun research builders that write canonical research outputs. Existing immutable CSV artifacts were joined by exact `game_id` and exact `row_id`; no fuzzy matching and no provider calls were used.

Selected following game:

- `game_id=401752746`, Auburn at Arkansas, 2025 Week 9, kickoff `2025-10-25T16:45:00Z`.
- Source team-games: `401752739:Arkansas` (Texas A&M at Arkansas, final 45-42) and `401752740:Auburn` (Missouri at Auburn, final 23-17), both Week 8.

### Replayed lifecycle evidence

| Lifecycle point | Arkansas | Auburn | Evidence/result |
|---|---:|---:|---|
| Week 8 game kickoff | `2025-10-18T19:30:00Z` | `2025-10-18T23:45:00Z` | Historical master; final scores preserved |
| Stale SP+ state | 10.7 | 13.4 | Snapshot `2025-10-15T13:37:06Z`, through provider Week 7, verified pre-Saturday |
| Stale Sagarin state | 77.96 | 81.79 | Snapshot `2025-10-15T20:51:55Z`, through provider Week 7, verified pre-Saturday |
| Postgame features | margin surprise +5.5 | -4.5 | Exact team-game feature rows; PBP success rate/PPA present |
| Predicted Shadow SP+ | 10.9302 | 13.0114 | Frozen premarket prediction |
| Predicted Shadow Sagarin | 78.5229 | 81.4660 | Frozen premarket prediction |
| Later updated SP+ | 9.3 | 12.1 | Snapshot `2025-10-22T03:32:57Z` |
| Later updated Sagarin | 78.55 | 81.66 | Snapshot `2025-10-23T05:41:39Z` |

Following-game fair values:

| State | Home spread (Arkansas) | Total |
|---|---:|---:|
| Stale 50/50 SP+/Sagarin spread; stale SP+ O/D total | -0.200 | 55.250 |
| Shadow 50/50 SP+/Sagarin spread; enhanced SP+ O/D total | -0.953 | 56.689 |
| Later updated 50/50 spread; updated SP+ O/D total | -0.510 | 56.550 |

Market path for the target game:

| Market state | Timestamp / provenance | Home spread | Total |
|---|---|---:|---:|
| First preserved consensus | `2025-10-19T09:00:00-04:00` | +0.5 | 55.5 |
| Sunday 9 AM consensus | `2025-10-19T09:00:00-04:00` | +0.5 | 55.5 |
| Sunday 2 PM consensus | preserved in next-game target | +1.5 | 56.0 |
| Sunday 9 PM consensus | preserved in next-game target | +1.5 | 57.5 |
| Close consensus | value preserved; close timestamp absent on this row | -2.5 | 55.5 |

This proves the logical order and identities: final game evidence -> postgame feature row -> stale provider inputs -> frozen Shadow forecast -> first/later opener market -> later provider update -> close. It also demonstrates that the Shadow prediction was frozen before the market join (`prediction_freeze_before_market_join=true`; early market inputs used in the provider model = 0).

### Cohort-level rehearsal checks

Across the preserved 2025 premarket artifact:

- 394 following-game predictions exist, covering target Weeks 6-15.
- All 394 join to a first-observed spread in the historical market timeline.
- Sunday 9 AM spread coverage exists for 307 of 394 rows.
- Close spread values exist for all 394 rows.
- The underlying build audit records 761 completed games, 1,408 team-week observations, 1,382 updated SP+ targets, 1,222 Sagarin targets, and 1,290 next-game rows.

### What the rehearsal does not prove

- Exact final-detection time is not preserved for the Week 8 games; kickoff and final scores are preserved, not a `GAME_FINAL` event timestamp.
- The live 2026 postgame scripts were not executed against 2025 because their paths, season, schedule, and output contracts are hard-coded for 2026.
- The archived research features are not the same thing as complete raw CFBD response caches replayed through today's production scripts.
- This does not prove atomic multi-artifact publication, crash recovery, duplicate-event handling, or automatic provider-release polling.
- The representative target lacks a close timestamp even though its close values are preserved, showing why timestamp completeness must be audited separately from value coverage.

The rehearsal therefore passes **data-level lifecycle reproducibility** and fails **controller-level replayability**.

## Existing, missing, manual, and risk summary

### Existing

- Canonical completed-result mapping and audits.
- Week-scoped raw postgame cache contract and cache-only validation.
- Season-to-date PBP, drive, and game-control feature builders.
- No-lookahead feature construction with entering provider timestamps and rejection reasons.
- Frozen/versioned Shadow inference with no live refit.
- Strict named canonical Shadow projection identities and missing-input behavior.
- Next-game mapping, current contract propagation, market joins, and public adapters.
- Durable historical 2024/2025 stale/Shadow/updated and market-checkpoint evidence.

### Missing

- Event-driven final detection and a persisted `GAME_FINAL` event.
- One orchestration profile that explicitly models “postgame now, provider updates later” with transition checkpoints.
- Append-only forecast versions for stale, Shadow, hybrid/refreshed, and market comparison states.
- A provider-release watcher or release-calendar enforcement.
- An immutable first-market-release timestamp owned centrally for every live game.
- A production replay mode parameterized by season/input/output root.
- First real 2026 final-game acceptance evidence.

### Manual/external steps

- A scheduler, operator, or CONTROL action must invoke `full`/`postgame`; final scores do not trigger it.
- Ratings/provider releases are discovered by later scheduled pulls, not by the postgame run.
- Provider credentials and network availability are required for uncached live PBP and rating refreshes.
- A human currently interprets whether a weekend is in stale, Shadow, or updated operating phase beyond the derived per-build state.

### Weekend failure risks

1. A final arrives after the last scheduled postgame run, leaving Shadow pending until another run.
2. CFBD marks a game final but PBP is absent/incomplete; the puller correctly fails, but there is no retry queue keyed to that game.
3. A provider publishes after the full run; the postgame profile will not discover it.
4. A latest-state artifact is rebuilt partially or later overwritten, with no event ledger to reconstruct the exact operator-visible sequence.
5. Source snapshot timestamps may be present while provider information-cutoff semantics remain ambiguous.
6. A scheduled opponent change/cancellation can break deterministic next-game mapping.
7. Market values can exist without complete event timestamps, as the rehearsal's close row demonstrates.
8. Legacy Shadow metadata can be mistaken for canonical formula authority if a consumer bypasses the projection contract.

## Recommended implementation order

1. **Run a controlled first-final acceptance before adding orchestration.** Use the first eligible 2026 final to prove canonical mapping, cache completeness, idempotent rerun, feature cutoffs, both Shadow models, projection-contract propagation, and audits.
2. **Define an append-only lifecycle event/forecast contract.** At minimum persist `GAME_FINAL`, `POSTGAME_READY`, `SHADOW_READY/PARTIAL`, `PROVIDER_PANEL_CHANGED`, `OFFICIAL_READY`, `MARKET_FIRST_SEEN`, and `CLOSE`, each with game IDs, source timestamps, run ID, input fingerprints, model version, and status/reason.
3. **Make replay an explicit production capability.** Parameterize season, input root, and output root so fixtures/historical caches can run without touching current production artifacts or network services.
4. **Separate triggers from calculations.** Keep the current builders; add idempotent orchestration that invokes only the affected game/week after a final and only affected projections after a provider-panel change.
5. **Add provider-release and market-first-seen gates.** Content fingerprints already exist for major accepted rating panels; persist their transitions and connect them to affected-game rebuilds. Preserve the first accepted market observation immutably.
6. **Add failure/retry acceptance tests.** Cover late PBP, missing provider input, postponed games, one-team completion, duplicate final notifications, partial writes, and restart from the event ledger.
7. **Only then automate tighter weekend cadence.** Scheduler changes should call the same guarded orchestration and should not duplicate model or authority logic.

## Is a persisted state controller needed?

**Yes, if the operational requirement is the complete lifecycle in this audit.** The current derived War Room state is adequate for displaying what the latest artifacts imply at build time. It is not adequate to prove when a transition occurred, trigger downstream work exactly once, recover after failure, or reproduce what operators saw at opener release.

The future controller should be a thin event/reducer layer over the existing builders, not a new formula owner. It should persist lifecycle events and forecast versions, enforce idempotency/transition guards, and call the canonical scripts. Projection formulas, provider authority, and page rendering should remain outside it.

## Final assessment

- **Current state:** computational lifecycle substantially exists; scheduled batch integration exists; historical information-state evidence is strong.
- **Missing pieces:** event-driven orchestration, immutable transition/forecast history, replay parameterization, and live 2026 acceptance.
- **Next engineering milestone:** lifecycle contract plus first-final acceptance—not new UI and not model changes.
- **Historical rehearsal result:** artifact-level PASS; production-controller replay NOT PROVED.
