# War Room Command Center Specification

## Implementation status

The production V1 is a standalone page at `war-room.html`, built by
`scripts/site/build_war_room_page.py`. It does not replace or inject content
into `index.html`. The page consumes `data/site/war_room_market_matrix.json`
and `data/site/war_room_health.json`; their owners remain the corresponding
builders in `scripts/war_room/`.

The canonical site build packages the page and its two JSON contracts. The
weekend interactive acquisition path remains
`scripts/war_room/run_fast_market_refresh.py`. Navigation exposure, Cloudflare
work, and alternate fast endpoints are outside V1 release preparation.

## Purpose

The War Room Command Center is the operational execution layer for the
2026 NCAAF betting workflow.

Primary objective:

Identify actionable spread and total edges during market formation and
maturity windows without leaving one page.

The War Room does not replace existing pages. It connects existing
systems into a decision layer.

------------------------------------------------------------------------

## Page Relationship

### War Room Command Center

Execution layer.

Answers: - Where is my current model edge? - Is the edge still
available? - Has the market matured? - Have ratings/models updated? -
Are there warnings?

### Openers Page

Research/detail layer.

Answers: - Why does this matchup have value? - What betting angles
exist? - What matchup context supports the edge?

### Matchups Page

Deep analysis layer.

Contains: - advanced metrics - player context - coaching - injuries -
schedule context

### Betting Page

Portfolio layer.

Contains: - placed bets - EV tracking - performance tracking

The War Room should link outward and avoid duplicating these systems.

------------------------------------------------------------------------

## State Model

Displayed state represents model and market readiness.

### STALE

Market exists, but ratings/model inputs are from the prior update cycle.

### SHADOW

New market exists and shadow projections are available.

### HYBRID

Some new ratings/models have updated, but not all required inputs are
complete.

### UPDATED

All scheduled ratings/models have been refreshed for the upcoming week.

Future: LIVE may be added for real-time adjustments beyond normal model
cycles.

------------------------------------------------------------------------

## Main Market Matrix

The primary table contains all games.

Default sorting: Largest actionable edge.

Users can sort by clicking column headers.

Required fields: - game_id - season - week - date - kickoff_time -
away_team - home_team - market_release_timestamp

The release timestamp is permanently stored for historical research.

------------------------------------------------------------------------

## Market Display

Spread: - model_spread - best_spread_book - best_spread_line -
best_spread_price - spread_edge

Totals: - model_total - best_total_book - best_total_line -
best_total_price - total_edge

Primary displayed books: - DraftKings - FanDuel - BetMGM - Caesars

Sharp reference: - Pinnacle

Pinnacle should be stored for historical/closing analysis but does not
need to dominate live display space.

------------------------------------------------------------------------

## Edge Colors

No minimum edge filter.

All games remain visible.

Green: \>=3 points

Yellow: 2-2.9 points

Red: \<2 points

Future enhancement: Half-point EV calculator to compare equivalent
prices.

------------------------------------------------------------------------

## Signal Column

The Signal column connects existing Betting Angles.

No duplicate angle engine.

Existing matchup/openers betting angle engine -\> War Room signal
adapter -\> small display badge.

Example: Team logo + x2

Clicking navigates to deeper matchup information.

------------------------------------------------------------------------

## Injury Column

Version 1: Display injury rank only.

Scale: 1 = healthiest 138 = largest injury concern

Color: - Green: 1-30 - Yellow: 31-70 - Orange: 71-110 - Red: 111-138

Do not initially adjust model spreads.

Use as context/warning.

------------------------------------------------------------------------

## Refresh Architecture

Existing daily pipeline remains unchanged.

War Room fast layer:

Saturday/Sunday: - 30-60 minute refresh - manual refresh option

Monday-Friday: Lower cadence.

The War Room should not require a complete site rebuild.

------------------------------------------------------------------------

## Phase Roadmap

### Phase 0 --- Architecture

Complete: - purpose - UI concept - state definitions - market hierarchy

### Phase 1 --- Data Contract

Next: Build canonical War Room dataset.

Outputs: - war_room_market_matrix.json - war_room_health.json -
war_room_signals.json

Audit: - market contract - line history - projections - betting angles -
injury data - provider health

### Phase 2 --- UI

Build War Room page from canonical JSON.

### Phase 3 --- Live Operations

Add: - manual refresh - weekend refresh cadence - live alerts

### Phase 4 --- Advanced Signals

Future: - injury adjustments - coaching edges - matchup interactions -
shadow improvements

------------------------------------------------------------------------

## Architecture Principle

The War Room is not another independent data system.

It is an operational view built from existing canonical sources.
