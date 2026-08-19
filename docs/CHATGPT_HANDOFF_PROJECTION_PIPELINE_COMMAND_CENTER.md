# ChatGPT Handoff — Projection Pipeline and War Room Command Center

Date: 2026-08-17  
Repository: `/Users/jameslindesmith/NCAAF_MAIN_REPO`  
Runtime workspace: `/Users/jameslindesmith/NCAAF_AUTO`

## Objective

Finish the 2026 operational data pipeline so the historically validated game
projection models populate automatically, the daily 8 AM process refreshes all
required inputs safely, and the War Room Command Center supports Saturday-night
through Sunday-night opener operations from canonical data.

The Command Center must be built as an operational view over existing domain
contracts. It must not become another projection, market, signal, or identity
owner.

## Paste-ready opening prompt

Use this handoff and the attached governing files as the current source of
truth. Continue the 2026 NCAAF projection-pipeline and War Room Command Center
work. Historical betting studies own the formulas; do not retrain, optimize,
renormalize missing sources, or invent fallbacks.

First reconcile the current state and return a path-to-closure plan with:

1. the target-week eligible-game denominator and provider publication states;
2. a source-by-source blocker matrix for Standard Spread, Standard Total,
   Shadow Spread, and Shadow Total;
3. the exact 8 AM pipeline order and the separate Saturday/Sunday fast loop;
4. the Command Center data-contract sequence before UI;
5. acceptance gates, rollback boundaries, and the exact files proposed for the
   first bounded implementation phase.

Then proceed only with the first approved bounded phase. Preserve the separate
roles of `NCAAF_AUTO` as runtime and `NCAAF_MAIN_REPO` as source/publisher. Do
not change page layouts, replace Openers, duplicate pipelines, publish, commit,
stage, or make paid/API calls without explicit authorization. Report any stale
documentation or artifact conflicts instead of silently choosing one.

## Governing model architecture

### Team Rating Engine

- SP+: 25%
- FPI: 25%
- TeamRankings: 25%
- Sagarin: 25%

Brad Powers, Massey, and DRatings are reference/research sources only for team
ratings.

### Game Projection Engine

- Standard Spread: SP+ 20%, FPI 20%, TeamRankings 20%, Sagarin Rating 20%,
  DRatings game prediction 20%.
- Standard Total: SP+ 40%, Massey Dual 40%, Sagarin total 20%.
- Massey Dual: equal weight of Massey's published total and the sum of its
  predicted team scores.
- Shadow Spread: SP+ Shadow 50%, Sagarin Shadow 50%.
- Shadow Total: frozen enhanced SP+ offense/defense model only.

All required components are strict. Missing inputs remain unavailable. Do not
renormalize weights or substitute team ratings, market ratings, legacy blends,
generic totals, or alternate Sagarin variants.

## Current implemented state

- Canonical contract: `data/site/current_game_projection_contract.json`.
- Strict resolver: `scripts/projections/projection_resolver.py`.
- Contract builder: `scripts/projections/build_current_game_projection_contract.py`.
- Normalized source builder: `scripts/projections/build_game_projection_sources_2026.py`.
- Shared Matchups and Shadow page-data adapters consume the strict resolver.
- Resolver validation passes for all 902 unique scheduled games.
- Historical formula validation passes:
  - Standard Spread: 3,843 complete historical games; max difference about
    `7.1e-15`.
  - Standard Total: 2,509 strict-overlap games; max difference `0`.
  - Shadow Spread: 394 2025 games; max difference about `7.1e-15`.
  - Shadow Total: 252 exact-state 2024 games; max difference about `1.42e-14`.
- Current canonical availability:
  - Standard Spread: 41 available, 861 unavailable.
  - Standard Total: 0 available.
  - Shadow Spread: 0 available.
  - Shadow Total: 0 available.
- Current component coverage across the 902-game season registry:
  - SP+, FPI, TeamRankings, Sagarin Rating spread components: 765 each.
  - DRatings game spreads: 71; strict five-source overlap: 41.
  - Massey Dual: 155 contract rows with exact arithmetic propagation.
  - Explicit SP+ total: 0.
  - Sagarin total: 0.
  - Shadow SP+ component fields: 66, but canonical Shadow models are not
    activated.
  - Shadow Sagarin: 0.
- Massey warning: 155/155 normalized rows have source URLs, but 0/155 retain a
  normalized pull timestamp. There are 730 external rows and 155 canonical
  matches; the remaining 575 need classification rather than fuzzy matching.
- The repository worktree contains substantial uncommitted research and
  production changes. Audit and preserve them before any branch, commit, or
  deployment operation.

## Critical clarification for coverage

The 902-game season registry is the identity backbone, not the correct
operational denominator for every Sunday.

Before calling a live source incomplete, define a canonical target-week
eligibility contract containing:

- target season/week;
- scheduled FBS games expected to receive a projection;
- provider publication window;
- whether FCS opponents are in or out for each source/model;
- status per provider: `NOT_YET_PUBLISHED`, `AVAILABLE`, `PARTIAL`, `STALE`,
  `FAILED`, or `NOT_APPLICABLE`;
- source timestamp and information cutoff;
- expected versus observed board rows.

Production readiness should be measured against eligible target-week games,
while still retaining all 902 games with explicit unavailable states.

## Remaining projection-source work

### Standard Spread

1. Define the target-week denominator.
2. Audit the 71 matched DRatings rows and explain why only 41 have all four
   rating components plus DRatings.
3. Separate legitimate FCS/rating-universe exclusions from identity failures.
4. Preserve DRatings board timestamps and provider publication state.
5. Validate neutral-site handling, HFA, and home-margin/home-line signs on live
   fixtures.

### Standard Total

1. Build the explicit live SP+ total component using the same convention
   validated historically. Never read a generic blended `projected_total` as
   SP+.
2. Finish the current Sagarin game-total adapter and target-week matching with
   provenance. Do not use Predictor/Golden Mean/Recent/Strong Recent rating
   variants as total substitutes.
3. Preserve Massey source observation timestamps through normalization.
4. Classify the 575 external Massey rows not represented in the canonical
   contract using deterministic identity and schedule-scope reasons.
5. Activate Standard Total only where SP+, Massey Dual, and Sagarin are all
   present; retain 40/40/20 without renormalization.

### Shadow models

1. Prove exact live Shadow SP+ input, feature, coefficient, and cutoff identity.
2. Implement and validate a provenance-safe live Shadow Sagarin adapter.
3. Activate Shadow Spread only when both components exist.
4. Implement the frozen enhanced SP+ offense/defense total inference exactly;
   reject the old 60/40 bridge under the canonical model ID.
5. Test Saturday completed-game transitions and no-lookahead behavior before
   exposing any Shadow value operationally.

## Daily 8 AM pipeline closure

The runtime owner is `NCAAF_AUTO`; `NCAAF_MAIN_REPO` is the source/publishing
repository. Do not collapse those roles.

The 8 AM pipeline needs this ordered contract:

1. Refresh canonical schedule and determine target week.
2. Pull rating panels and accepted game-prediction boards.
3. Preserve raw responses/pages and provider timestamps.
4. Normalize with deterministic identities and explicit quarantine reasons.
5. Build target-week provider readiness.
6. Build `game_projection_sources_2026.csv`.
7. Build `current_game_projection_contract.json`.
8. Run historical-formula invariants, resolver validation, sign tests, and
   coverage gates.
9. Build shared page adapters.
10. Build current-market, signals, health, and Command Center data artifacts.
11. Validate the public staging tree.
12. Publish only through the allowlisted publisher after separate approval.

Required operational behaviors:

- source-specific failure isolation;
- no stale-as-current behavior;
- atomic writes and preservation of the prior accepted artifact on failure;
- raw/provenance retention;
- explicit quota and network error reporting;
- no recursive runtime-tree publication;
- no page build timestamp used as provider freshness;
- separate daily 8 AM cadence from the Saturday/Sunday fast loop.

## Saturday-night through Sunday-night fast loop

The Command Center needs a 30–60 minute reducer/refresh loop that does not rerun
unnecessary weekly acquisitions or rebuild the whole site.

Operational sequence:

1. Detect and permanently register first accepted spread/total observations.
2. Refresh accepted current-market quotes and preserve per-book provenance.
3. Refresh completed-game/postgame inputs when genuinely available.
4. Run exact Shadow inference adapters.
5. Rebuild the canonical projection contract and readiness state.
6. Rebuild War Room signals, health, and market matrix atomically.
7. Validate freshness, coverage, signs, edge arithmetic, and state evidence.
8. Surface `STALE`, `SHADOW`, `HYBRID`, or `UPDATED` only from component
   evidence—not from the clock or build time.

## Command Center implementation path

The standalone V1 data projections and `war-room.html` now exist. The sequence
below is retained as the implementation record; remaining work is live-season
acceptance, propagation verification, and separately authorized navigation.

1. Freeze schemas in `config/public_page_data_contracts.json`.
2. Build immutable `data/odds/game_market_first_seen_2026.json`.
3. Build a central target-week/model-readiness reducer.
4. Build `data/site/war_room_signals.json` from existing betting angles only.
5. Build `data/site/war_room_health.json` from existing health/status owners.
6. Build `data/site/war_room_market_matrix.json` by canonical `game_id` only.
7. Add propagation, replay/idempotency, sign, freshness, and stale-data audits.
8. Run dark in `NCAAF_AUTO` and compare repeated outputs.
9. The standalone Command Center V1 is implemented without replacing Home,
   Openers, Matchups, Betting, or existing pipelines.
10. Add the weekend refresh/manual-refresh operating layer and alerts last.

## Additional unresolved gates

- Reconcile the `ratings_source_status.csv` snapshot date with
  `ratings_latest.csv` without losing provenance fields.
- Classify remaining current-market/history mismatches; do not assume every
  difference is an error because current and historical semantics differ.
- Add immutable first-observed market timestamps.
- Establish explicit provider freshness thresholds and weekend publication
  windows.
- Verify runtime/source checkout parity for every new builder before publishing.
- Add target-week eligible-game coverage to health and acceptance gates.
- Capture immutable model ID/version/component timestamps in model tracking and
  line history; do not recompute historical records from current values.
- Preserve injury status as unavailable until a validated current source exists.
- Complete a dirty-worktree audit and decide how the current uncommitted changes
  will be reviewed and committed in bounded groups.

## Definition of closure

The project is operationally complete when:

- every eligible target-week game has a deterministic status for all four
  canonical models;
- available models reproduce the frozen formulas exactly;
- unavailable models have no substituted values;
- the 8 AM pipeline produces accepted artifacts automatically with provenance;
- the weekend fast loop updates market, Shadow, readiness, health, and matrix
  artifacts without a full rebuild;
- the three Command Center data contracts pass replay, freshness, identity,
  sign, and propagation audits;
- the Command Center UI consumes only those contracts;
- Openers, Matchups, Betting, Team, signals, tracking, and simulations use the
  same canonical projection identity;
- runtime staging and allowlisted publication gates pass;
- rollback artifacts and an operator runbook exist.

## Guardrails

- Historical betting studies own formula identity.
- Do not optimize formulas or thresholds during pipeline implementation.
- No fuzzy game/team matching.
- No missing-source renormalization or fallback substitution.
- Do not use post-start mutable projections as pregame values.
- Do not replace Openers or duplicate existing pipelines.
- Do not redesign or replace the standalone Command Center V1 before its
  operational contracts pass live-season acceptance.
- Do not stage, commit, publish, or make paid/API calls without explicit
  authorization.
