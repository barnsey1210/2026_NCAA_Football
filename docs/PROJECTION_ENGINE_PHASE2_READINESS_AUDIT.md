# Projection Engine Phase 2 Readiness Audit

Date: 2026-08-16  
Status: original readiness audit plus implementation update  
Scope: the owner inventory below records the pre-migration state

## Implementation update

The strict canonical resolver is now active in the shared Matchups and Shadow
page-data adapters. It does not change any model formula and does not create
fallback substitutions. Current availability is:

- Standard Spread: 41 available, 861 unavailable.
- Standard Total: 902 unavailable because required live total inputs are not ready.
- Shadow Spread: 902 unavailable because the live Shadow adapters are not ready.
- Shadow Total: 902 unavailable because the exact live enhanced SP+ O/D adapter is not ready.

The normalized source artifact now includes current SP+, FPI, TeamRankings and
Sagarin Rating spread components plus matched DRatings rows. Massey 2026 totals
remain not ready. The sections below retain the original migration audit for
provenance; statements labeled as current production describe the pre-resolver
state unless superseded by this update.

## Executive conclusion

The canonical contract is structurally ready for dual-run comparison, but production migration is **not ready to switch on**.

The principal blockers are:

1. the normalized 2026 game-source artifact is not current or complete;
2. 2026 scheduled-game Sagarin spreads/totals are not ready;
3. live Shadow Sagarin does not exist;
4. the exact Enhanced Shadow Total live feature/inference identity is not connected;
5. the Team Rating Engine has since been aligned to the required SP+/FPI/TeamRankings/Sagarin-only composite, but it remains a separate contract and is not a scheduled-game fallback;
6. several downstream systems independently calculate edges or provider/rating projections;
7. simulations can fall back to rating composites for scheduled games, contrary to the new strict rule when a canonical scheduled-game projection should exist.

The safe next action is source normalization and dual-run parity at the game adapter—not page migration.

## 1. Enforced architecture boundary

### Game Projection Engine

For actual scheduled games only:

- Standard Spread: fixed 20% SP+, FPI, TeamRankings, Sagarin Rating and DRatings; all five required.
- Standard Total: 40% SP+, 40% Massey Dual and 20% Sagarin; all three required.
- Shadow Spread: 50% Shadow SP+ and 50% Shadow Sagarin; both required.
- Shadow Total: exact Enhanced SP+ offense/defense Shadow model.

No missing-source renormalization or fallback substitution is allowed. An
unavailable canonical model remains unavailable.

### Team Rating Engine

For team ratings, hypothetical matchups and other approved rating-based analysis:

- equal-weight SP+, FPI, TeamRankings and Sagarin;
- DRatings excluded;
- Massey and Powers research/future only.

For conference/playoff simulations, an actual scheduled game must use the Game Projection Engine. The Team Rating Engine may estimate only a genuinely hypothetical matchup. It must not replace an unavailable scheduled-game projection.

## 2. Current projection-owner inventory

### Calculation and mutation owners

| File | Function/section | Current formula | Current source/output | Replacement target | Migration risk |
| --- | --- | --- | --- | --- | --- |
| `scripts/projections/build_game_projection_sources_2026.py` | `load_rating_game_projections`, `load_massey`, `load_sagarin`, `load_dratings` | SP+/FPI/TR spread from `home rating - away rating + 2.6 HFA`; provider game rows passed through | Ratings master and external matchup files → `game_projection_sources_2026.csv` | Remain the normalized-source adapter, but emit explicit provider observations/provenance required by the canonical contract | **High**: rating-difference approximations may not equal historical provider game projections; Sagarin sign/date matching; sparse output |
| `scripts/projections/build_game_projection_blend_2026.py` | `equal_available_weights`, `weighted_avg`, `main` | Equal mean of enabled available spread/total sources; weights change with missingness | Source CSV plus preserved schedule projection → `game_projection_blend_2026.csv` | `current_game_projection_contract.json` fixed model IDs | **Critical**: directly violates strict required-component formulas |
| `scripts/projections/apply_game_projection_blend_to_preseason_db.py` | `main` | Writes legacy blend into `projected_margin_home`, aliases, total and win probability | Blend CSV → `preseason_db.json` | Future game-projection adapter should read canonical contract; preseason DB stops being projection authority | **Critical**: overwrites shared fields consumed broadly |
| `scripts/site/recalculate_game_projections_from_active_combo.py` | `recalc` | Home team `combo - away combo + team HFA`; logistic win probability | Embedded legacy HTML DBs | No scheduled-game replacement; hypothetical use belongs to Team Rating Engine | **Critical**: independent scheduled-game formula and direct HTML mutation |
| `scripts/site/install_projection_blend_site_wiring.py` | top-level installer that rewrites builders | Installs older 4-of-5 spread and SP+/DRatings total ownership | Rewrites projection source/overlay scripts | Retain as migration history only; do not execute; eventually retire after parity | **Critical**: script-generating script can restore obsolete formulas |
| `scripts/site/install_dratings_2026_production_projection.py` | top-level installer | Installs DRatings into the mutable blend and legacy metadata | Rewrites projection scripts/config | Retain as historical installer only | **Critical**: can reintroduce deprecated ownership |
| `scripts/site/build_saturday_shadow_component_predictions.py` | `predict`, `main` | Spread is 50% target-excluded market + 50% predicted updated SP+, or SP+ fallback. Total is `0.60 * predicted SP+ component total + 0.40 * existing total - 1.1573` | Frozen bridge artifacts, live features, market ratings and matchups → component JSON | Exact Shadow SP+/Sagarin and Enhanced O/D canonical model IDs | **Critical**: neither live formula is the validated historical formula |
| `scripts/site/build_saturday_shadow_lines.py` | `market_total_baseline`, `main` | Repackages current component Shadow values; separately derives market-rating baseline `-(home-away+2.5)` | Component JSON, market ratings, existing model → `saturday_shadow_lines.json/csv` | Read named canonical Shadow projections after exact activation | **High**: multiple baselines and fallback sources can be confused with canonical Shadow |
| `scripts/ratings/build_active_2026_ratings_master.py` | `main` | Equal available mean of SP+, FPI, TeamRankings, DRatings and Sagarin | `ratings_latest.csv` → ratings master | Separate four-source Team Rating Engine: SP+/FPI/TR/Sagarin only | **Critical**: DRatings improperly included; available-source reweighting not an all-four invariant |
| `scripts/site/build_ratings_view.py` | composite construction and metadata | Equal-weight across available active rating sources | Ratings latest/master → ratings view | Consume corrected Team Rating contract only | **High**: may become a second rating-composite policy owner |
| `scripts/model_tracking/capture_model_tracking.py` | individual rating loop, `spread_core`, `available_average` | Independently derives provider spreads from team ratings +2.6 HFA and constructs configured spread consensus; total reads production total | Matchups + ratings master → tracking ledgers | Capture canonical projection snapshots and component provenance without recalculation | **Critical**: duplicate projection calculation changes tracked model identity |
| `rerun_conference_sims_2026.py` | `estimate_margin_home`, `estimate_total`, `game_home_prob` | Scheduled consensus when recognized; otherwise team `combo` + HFA. Total fallback uses SP-like O/D components and clamps 32–82 | Preseason DB and team records → conference simulations | Scheduled games use canonical Game Projection Engine; hypothetical title matchups use Team Rating Engine | **Critical**: scheduled fallback can violate engine boundary; hypothetical total has separate formula |
| `scripts/simulations/run_playoff_model_2026.py` | `run_model`, `game_winner` | Scheduled `projected_margin_home`; if missing, Team Rating estimate. Bracket/hypothetical games use rating margin + fixed HFA | Preseason DB and conference simulation module → playoff model | Scheduled lookup by canonical `game_id`; Team Rating only for hypothetical games | **Critical**: missing scheduled projection silently becomes rating projection |

### Storage and adapter owners

| File/artifact | Function/role | Current stored meaning | Replacement target | Migration risk |
| --- | --- | --- | --- | --- |
| `data/projections/game_projection_blend_config.json` | Mutable source selection | Enables SP+/FPI/TR/DRatings spread, disables Sagarin; enables SP+/DRatings total | Canonical model definitions with fixed weights | Critical |
| `data/projections/game_projection_blend_2026.csv` | Legacy game blend | 902 mutable equal-available projections | Dual-run comparison only | High |
| `data/snapshots/preseason/preseason_db.json` | Shared schedule DB | Stores `projected_margin_home`, `projected_total` and aliases after overlay | Schedule identity remains; projection values come from canonical adapter | Critical |
| `scripts/site/build_matchups_view.py` | `main` around `model_home` | Copies DB projected home margin and total into `matchups_view.json`; converts positive home margin to bookmaker home line | First production adapter to canonical named projections | Critical sign/fan-out risk |
| `data/site/matchups_view.json` | Current page hub | Ambiguous `model.home_spread` and `model.total` without canonical formula identity | Adapter representation of canonical contract with model ID/version/state | Critical |
| `data/site/saturday_shadow_component_predictions.json` | Shadow intermediate | Current noncanonical Market/SP+ spread and 60/40 total bridge | Comparison artifact until exact Shadow inference exists | Critical label risk |
| `data/site/saturday_shadow_lines.json` | Current Shadow page payload | 902 rows; current Shadow values/statuses | Canonical Shadow adapter | High |
| `scripts/site/build_schedule_live_enrichment.py` | projection enrichment | Copies Saturday Shadow spread/total into schedule fields | Named canonical projection/state | Medium |
| `scripts/snapshots/create_preseason_snapshot.py` | snapshot capture | Persists generic projected margin/total | Add model identity/version before future capture | High historical-identity risk |
| `scripts/history/append_game_line_model_history.py` | `main` | Stores generic projected margin, negated home spread and total | Capture canonical model ID/version/state and explicit orientation | Critical chronology/sign risk |
| `scripts/history/build_matchup_line_history_clean.py` | `read_source`, `main` | Backfills missing historical projection fields from current matchup data | Observation-time canonical snapshots only; no current-value backfill | Critical lookback contamination risk |
| `scripts/model_tracking/settle_model_tracking.py` | `main` | Settles previously captured generic projections | Settle immutable captured version; never relabel legacy rows | High |

### Edge and recommendation owners

| File/page | Function | Current edge calculation | Replacement target | Migration risk |
| --- | --- | --- | --- | --- |
| `scripts/agents/build_home_command_center.py` | `spread_edge_row`, `total_edge_row` | DB margin/total versus market fields | Canonical projection plus canonical current-market contract | High: server-side duplicate edge owner |
| `scripts/signals/build_game_betting_angles_2026.py` | `add_coin_toss`; other angle adapters | Reads generic projected margin; produces contextual angle rows | Canonical projection adapter; betting-angle engine remains separate | Medium |
| `scripts/signals/build_travel_1h_signals_2026.py` | `main` | Reads generic projected home margin for context | Canonical named Standard projection | Medium |
| `index.html` | `spreadEdge`, `totalEdge` | Spread `market home line - model home line`; total `model - market` | Eventually receive canonical precomputed/adapter-consistent edges | High: page-local edge calculation |
| `matchups.html` | `spreadOffer`, `totalOffer` | Chooses side and best quote, calculates absolute model-market difference | Canonical projection and central edge semantics | High: page-local recommendation logic |
| `openers.html` | `activeHomeSpread`, `activeTotal`, `spreadOffer`, `totalOffer` | Selects Standard vs current Shadow payload in browser, then calculates side/edge | Canonical model/state selection in adapter; page formats only | **Critical**: browser selects projection owner/formula |
| `team.html` | `teamGame` | Converts home model/market to team perspective and calculates `teamMarket - teamModel` | Adapter-provided canonical projection with tested team-relative conversion | High sign risk |
| `matchup_workspace.js` | `projectedPoints`, edge blocks, signal blocks | Derives projected team points from total/spread and calculates spread/total edges and thresholds | Consume canonical values; central signal engine owns actionable recommendation | **Critical**: page-local projection derivative and signal thresholding |
| `schedule.html` plus injected schedule scripts | schedule render/context helpers | Uses model fields and injected angle reasons | Canonical schedule adapter | Medium |
| `betting.html` | live matchup context | Reads matchups projection beside portfolio/history; Shadow performance separately | Canonical live projection; historical performance remains separate | Medium |

Audit and research scripts that merely verify or compare projections are not production owners. Installer scripts are included because executing them mutates production-owner code even if they are not in the normal daily path.

## 3. Production formula discrepancies

### Standard Spread

Target: strict 20% each SP+, FPI, TeamRankings, Sagarin and DRatings.

Current differences:

- blend configuration disables Sagarin;
- output uses equal-available weights and changes formula when sources are absent;
- current normalized source CSV contains only 16 Massey rows, so the checked-in blend is not backed by the currently expected provider inventory;
- rating-derived SP+/FPI/TR game spreads use a fixed 2.6 HFA and require parity evidence against the provider game projections used historically;
- generic schedule fields do not reliably identify the formula version.

### Standard Total

Target: 40% SP+, 40% Massey Dual, 20% Sagarin.

Current differences:

- blend configuration enables SP+ and DRatings, with Massey and Sagarin disabled;
- DRatings is not a canonical Standard Total component;
- equal-available renormalization is allowed;
- legacy code may recover SP+ from a generic `projected_total` already containing a blend;
- Massey Dual is not the active production formula despite 16 calculable current rows.

### Shadow Spread

Target: strict 50% Shadow SP+ and 50% Shadow Sagarin, both in bookmaker home-line orientation.

Current differences:

- current production uses 50% market-rating spread and 50% updated SP+ when possible;
- it falls back to SP+ alone;
- no live Shadow Sagarin component exists;
- Openers selects this noncanonical Shadow payload client-side.

### Shadow Total

Target: exact Enhanced SP+ O/D provider-delta model and deterministic O/D matchup assembly.

Current differences:

- current production first predicts an SP+ component total through a separate conversion model;
- it then blends 60% of that result with 40% of the existing production total and subtracts 1.1573;
- the existing production total is itself a mutable nonhistorical blend;
- exact historical enhanced feature identity is not asserted in live rows;
- no live row currently activates the canonical Enhanced Shadow Total model.

### Team Rating Engine

Target and current production Ratings-page policy: strict/equal SP+, FPI,
TeamRankings and Sagarin at 25% each; DRatings and Brad Powers excluded.

The remaining migration concern is consumer identity: scheduled-game pages and
simulations must not interpret the Team Rating Engine as a substitute Standard
Spread projection.

## 4. Page-local calculations that must be removed or constrained

Pages are presently more than formatters in these locations:

1. `openers.html` selects Standard versus Shadow source in the browser and calculates spread/total sides and edge magnitudes.
2. `matchups.html` selects the side/best quote and calculates spread/total edges.
3. `index.html` calculates spread and total edges.
4. `team.html` converts projections to team perspective and calculates betting edge.
5. `matchup_workspace.js` derives team projected points from spread/total, calculates edges, and creates thresholded model-edge signals.
6. Schedule injection scripts calculate or explain projection-based angles from generic fields.

Formatting a canonical home-line into a team-facing label is acceptable. Selecting a model formula, substituting a fallback, defining recommendation ownership, or creating a signal threshold in the page is not. Those decisions belong in central contracts/adapters.

## 5. 2025 architecture compatibility

No historical output was changed. Existing 2025/historical evidence confirms:

- Sagarin participates correctly in strict Standard Spread, Standard Total and Shadow Spread formulas;
- the canonical adapter's explicit `value_home_margin` and `value_home_line` fields resolve historical sign differences;
- the fixed missing-component policy reproduces historical complete-case behavior;
- the four model IDs and per-game projection object structure can represent all historical formulas without page-local source selection;
- the Enhanced Shadow Total assembly matches stored exact-state game totals within floating-point tolerance.

This is compatibility proof, not 2026 source readiness. The current 2026 Sagarin game-prediction feed remains a blocker.

## 6. Required migration sequence and gates

### 1. Canonical contract validation

Safe now:

- keep dual-run;
- reconcile normalized 2026 source coverage without changing consumers;
- create representative 2025 Sagarin fixtures requested by the Phase 1 plan;
- add row-level provider timestamp and sign audits;
- reconcile the Team Rating builder/artifact separately.

Gate: complete required components produce exact fixed formulas; incomplete rows remain unavailable; source provenance is current.

### 2. Migrate game projection adapter

First production code target should be `scripts/site/build_matchups_view.py`, not a page. Add a dual-read comparison mode before switching fields.

Gate: 902 one-to-one IDs, no sign discrepancies, expected missingness, no old output overwritten, and parity report reviewed.

### 3. Migrate Matchups

Consume adapter fields only. Move model selection and edge semantics out of `matchups.html` while preserving display behavior.

Gate: side, line, price and edge parity fixtures for home/away favorites, pick'em and missing markets.

### 4. Migrate Openers

Replace browser selection of `saturday_shadow_lines.json` with named canonical model/state fields only after exact Shadow models activate. Do not redesign.

Gate: Standard/Shadow state transitions, no forbidden fallback IDs, and explicit unavailable display.

### 5. Migrate Betting

Use canonical live projections while leaving historical performance contracts unchanged.

Gate: prospective rows preserve exact model ID/version and historical rows are not relabeled.

### 6. Migrate Team pages

Use the same canonical adapter with a tested team-perspective sign transform. Team Rating remains a separate panel/domain.

Gate: home/away sign fixtures and no team page formula selection.

### 7. Migrate signals, line history and model tracking

Signals must consume named projections; history/tracking must record immutable identity and timestamps rather than recompute.

Gate: no duplicate projection arithmetic, no observation-time backfill, and old records retain legacy model identity.

### 8. Build Command Center data layer

Implemented reconciliation (2026-08-19): the standalone V1 consumes canonical
projections, current market, existing signal context, and health through
`war_room_market_matrix.json` and `war_room_health.json`. It does not calculate
provider blends. Live-season acceptance remains required.

### 9. Build Command Center UI

Implemented reconciliation (2026-08-19): `war-room.html` is the standalone V1
and is packaged by the canonical public build. It does not replace `index.html`.
Navigation remains a separate, not-yet-authorized release decision.

## 7. Simulation migration rule

The safest implementation pattern is an explicit resolver:

```text
if canonical scheduled game_id exists:
    require Game Projection Engine result/status
    use its projection when AVAILABLE
    preserve unavailable state when incomplete
else if the matchup is genuinely hypothetical:
    use Team Rating Engine
```

Do not fall back from a known scheduled game to the Team Rating Engine. Missing
required provider inputs must remain explicitly unavailable.

Conference championship and playoff bracket games that are generated by the simulation and do not yet have canonical scheduled IDs are hypothetical; the Team Rating Engine is appropriate there.

## 8. Safe next work

Safe, bounded work before any switch:

1. Reconcile `build_active_2026_ratings_master.py` with the required four-source Team Rating policy and explain why the checked-in master reflects a different older formula. This should be a separate authorized change.
2. Rebuild/audit `game_projection_sources_2026.csv` through its existing source pipeline in a controlled dual-run location, not by adding provider logic to page code.
3. Produce exact-match coverage by provider and required model for all 902 games.
4. Create 2025 Sagarin adapter fixtures with source timestamps and both sign orientations.
5. Specify the live Shadow Sagarin owner.
6. Build and parity-test the exact Enhanced Shadow Total live feature adapter.
7. Add a read-only `build_matchups_view.py` dual-run comparison report.
8. Review those results before authorizing any production consumer migration.

## Original readiness decision and current disposition

The original audit decision was **Phase 2 audit complete; production consumer
migration hold**. The subsequently authorized resolver migration has now moved
the shared Matchups and Shadow data adapters to strict canonical selection.
Source-readiness holds remain enforced as unavailable states rather than being
bypassed: Massey 2026 totals and both live Shadow adapters are still not ready.
