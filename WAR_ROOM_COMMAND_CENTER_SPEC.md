# War Room Command Center Specification

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

Answers:
- Where is my current model edge?
- Is the edge still available?
- Has the market matured?
- Have ratings/models updated?
- Are the sportsbooks / exchanges healthy in the latest fast refresh?
- Are there warnings?
- How fresh is the fast market data?

### Openers Page

Research/detail layer.

Answers:
- Why does this matchup have value?
- What betting angles exist?
- What matchup context supports the edge?

### Matchups Page

Deep analysis layer.

Contains:
- advanced metrics
- player context
- coaching
- injuries
- schedule context

### Betting Page

Portfolio layer.

Contains:
- placed bets
- EV tracking
- performance tracking

The War Room should link outward and avoid duplicating these systems.

------------------------------------------------------------------------

## Architecture Principle

The War Room is not another independent provider stack.

It is an operational view built from canonical project sources plus a
separate fast-market operational layer.

Core rule:

**One normalization / contract path per data domain, many downstream
consumers.**

The fast War Room layer may have stricter execution-health rules than the
normal site, but those rules must not alter the normal Openers, Odds,
Matchups, Futures, or other canonical site behavior.

------------------------------------------------------------------------

## State Model

Displayed state represents model and market readiness.

Canonical authority policy is owned by
`docs/WAR_ROOM_PROJECTION_AUTHORITY.md`. Spread and Total are evaluated
independently. Active Spread uses SP+, FPI, TeamRankings, and DRatings (4/4
Official; 2-3/4 Hybrid). Active Total uses SP+ Total, Massey Dual, and DRatings
Total (3/3 Official; 2/3 Hybrid). Sagarin is not an active Standard
authority/health source; it remains relevant to Shadow/research. Available
projection values remain visible with explicit partial/degraded state.

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

Required identity fields:
- game_id
- season
- week
- date
- kickoff_time
- away_team
- home_team
- market_release_timestamp

The release timestamp is permanently stored for historical research.

### Primary Market Matrix Hierarchy

The operational market hierarchy is:

1. Primary bettable sportsbooks
2. Best Bettable
3. Best Exchange
4. Pinnacle sharp reference
5. Fair / model line
6. Edge
7. Signal
8. State

Preferred compact sportsbook columns:

- DK
- FD
- MGM
- CZR
- BEST BOOK
- BEST EXCH
- PINN
- FAIR
- EDGE
- SIGNAL
- STATE

------------------------------------------------------------------------

## Market Display

### Primary Bettable Sportsbooks

- DraftKings
- FanDuel
- BetMGM
- Caesars

Best Bettable is selected only from these four sportsbooks.

### Exchanges

Tracked separately from normal sportsbooks:

- Novig
- ProphetX
- Kalshi

Best Exchange is selected from this group only.

### Sharp Reference

- Pinnacle

Pinnacle remains a separate sharp/reference market and should not be mixed
into Best Bettable or Best Exchange.

### Spread

Display:
- model_spread
- individual primary-book lines/prices
- best_spread_book
- best_spread_line
- best_spread_price
- best_exchange_spread
- pinnacle_spread
- spread_edge

### Total

Display:
- model_total
- individual primary-book lines/prices
- best_total_book
- best_total_line
- best_total_price
- best_exchange_total
- pinnacle_total
- total_edge

------------------------------------------------------------------------

## Normal Market Contract vs Fast War Room Market

These are intentionally different operational layers.

### Normal Canonical Market

Used by:
- Odds
- Openers
- Matchups
- other normal site consumers

Policy:
- The Odds API is primary.
- Action Network is an approved fallback where configured.
- Normal quote freshness / stale-data rules apply.
- Caesars may remain valid via Action fallback when current under the
  canonical market policy.
- Normal pages are not subject to the War Room latest-fast-pull rule.

### Fast War Room Market

Used by:
- War Room Command Center
- fast Best Bettable
- fast Best Exchange
- fast Pinnacle reference
- sportsbook / exchange operational health

Policy:
- Uses the dedicated fast The Odds API pull.
- Spread and total markets only.
- A venue participates in fast market selection only when it appeared
  with usable data in the latest fast pull.
- Participation remains tied to the latest fast pull until another fast
  pull occurs.
- There is no arbitrary 20-minute participation expiration.
- Quote age is displayed / studied separately from pull participation.

------------------------------------------------------------------------

## Sportsbook / Exchange Health

The Command Center should show a compact health strip for the upcoming
market board.

Example:

`DK ●   FD ●   MGM ◐   CZR ●   |   PINN ●   NOVIG ●   PROPHET ◐   KALSHI ○`

Health and board breadth are separate concepts.

### GREEN

The venue:
- participated in the latest fast pull, and
- returned structurally healthy spread / total data for the markets it
  currently offers.

### YELLOW

The venue participated in the latest fast pull but has a meaningful data
integrity / completeness concern, for example:
- spread missing on games where the venue otherwise returned data,
- total missing on games where the venue otherwise returned data,
- malformed or unusable returned markets,
- another operational feed anomaly.

Yellow should **not** be assigned merely because a sportsbook currently
offers fewer games than another sportsbook.

### RED

The venue:
- did not return usable data in the latest fast pull, or
- returned effectively unusable current data.

### Board Breadth

Display board breadth separately, for example:

- DK: 75 games
- FD: 110 games
- MGM: 50 games
- CZR: 52 games
- PINN: 45 games

A venue may be GREEN with narrower board breadth if its returned markets
are internally healthy.

------------------------------------------------------------------------

## Edge Colors

No minimum edge filter.

All games remain visible.

Green: >=3 points

Yellow: 2-2.9 points

Red: <2 points

Future enhancement: Half-point EV calculator to compare equivalent
prices.

------------------------------------------------------------------------

## Signal Column

The Signal column connects existing Betting Angles.

No duplicate angle engine.

Existing matchup/openers betting angle engine
-> War Room signal adapter
-> small display badge.

Example: Team logo + x2

Clicking navigates to deeper matchup information.

------------------------------------------------------------------------

## Injury Column

Version 1 target: Display injury rank only when a verified current injury
source is available.

Scale:
- 1 = healthiest
- 138 = largest injury concern

Color:
- Green: 1-30
- Yellow: 31-70
- Orange: 71-110
- Red: 111-138

Do not initially adjust model spreads.

Use as context/warning.

If the current injury source is unavailable or not configured, the War
Room must display injury data as unavailable / unknown. Missing injury
data must never be interpreted as zero injuries.

------------------------------------------------------------------------

## Refresh Architecture

### Existing Daily Pipeline

The existing daily pipeline remains unchanged.

Daily market credential:
- environment variable: `THE_ODDS_API_KEY`
- account role: 500-credit daily account
- primary schedule: existing 8 AM daily workflow
- markets: h2h, spreads, totals
- normal output namespace: `data/odds/`
- feeds the normal canonical site market system

### Dedicated Fast Command Center Layer

Fast market credential:
- environment variable: `THE_ODDS_API_KEY_FAST`
- account role: 20,000-credit Command Center account
- markets: spreads, totals only
- moneyline is explicitly disabled
- fast output namespace: `data/war_room/odds/`
- fast audits: `data/war_room/audits/`

The fast profile must fail closed if:
- `THE_ODDS_API_KEY_FAST` is missing, or
- moneyline / h2h is requested.

The fast pull must never overwrite the daily canonical raw/normalized
artifacts.

### Baseline Refresh Cadence

Saturday / Sunday:
- 30-60 minute scheduled baseline cadence
- manual refresh option while actively using the War Room

Monday-Friday:
- lower scheduled cadence
- manual refresh option

Special market windows may justify more frequent manual refreshes, for
example:
- Saturday-night opening
- Sunday market formation
- major injury / roster news
- suspected sharp market movement

The initial production plan does **not** assume continuous 30-second or
60-second polling.

The first several active Saturdays / Sundays should be used to determine
whether a faster cadence produces enough incremental information to
justify the additional API usage.

Authenticated manual actions use the protected `control.barnseywr.com`
popup/API. An expired Cloudflare Access session in an already-open popup can
fail before FastAPI sees the POST; reconnecting the operator session restores
the authenticated channel. This is an operator-session condition, not a
Market or quota defect.

------------------------------------------------------------------------

## Fast Latency / Timing Architecture

Measured August 18, 2026 fast-path validation:

- The Odds API request: spreads + totals only
- actual API cost: 2 credits
- API HTTP latency observed: approximately 0.29-0.34 seconds
- API pull + normalization observed: approximately 0.90-0.97 seconds
- War Room health build observed: approximately 0.07 seconds
- total local measured pipeline observed: approximately 1.0-1.1 seconds

Current measurable flow:

Sportsbook
-> The Odds API provider/cache
-> fast API request
-> fast normalization/write
-> War Room health
-> War Room market matrix
-> fast publication
-> browser refresh

The local acquisition / processing layer is already approximately one
second. Remaining end-to-end work is primarily:
- Market Matrix generation
- fast publication
- browser cache-busting / delivery
- measurement of provider / sportsbook update behavior

Target remains seconds-level browser refresh, with an operational goal of
less than approximately four seconds from manual refresh action to fresh
War Room data appearing when provider data is already available.

------------------------------------------------------------------------

## Quote Freshness vs Pull Participation

These are separate operational concepts.

### Pull Participation

Question:

Did the sportsbook / exchange return usable data in the latest fast API
pull?

Used for:
- fast sportsbook health
- fast Best Bettable eligibility
- fast Best Exchange eligibility
- fast Pinnacle-reference availability

### Quote / Provider Update Age

Question:

How long ago was the provider-reported market record last updated when
our response arrived?

Used for:
- diagnostics
- latency research
- provider-quality analysis
- future market-lead / lag research

An older provider update timestamp does not automatically prove that a
sportsbook line is stale. The line may simply not have changed recently.

------------------------------------------------------------------------

## Passive Fast-Market Movement / Latency Study

Every legitimate fast Command Center refresh should contribute to a
durable market-history study without causing any additional API call.

Preserve:
- complete raw fast snapshot
- refresh_id
- refresh timestamp
- API HTTP latency
- API credits used by the call
- credits remaining
- venue participation / health
- spread / total coverage
- provider update-age statistics

Primary artifacts:

- `data/war_room/odds/raw_archive/`
- `data/war_room/audits/fast_market_refresh_history.csv`
- `data/war_room/audits/fast_market_latency_study.json`
- `data/war_room/audits/fast_market_pipeline_timing.json`

Research questions to evaluate during the first several Saturdays /
Sundays:

- How often does a refresh contain any new spread or total information?
- How often are consecutive pulls effectively identical?
- Which venues are first observed moving?
- How quickly do retail books appear to follow Pinnacle / exchanges?
- How quickly does a model edge decay after a detected sharp-market move?
- Does a 30-minute cadence miss actionable information?
- When does 10-, 5-, 2-, or 1-minute refresh behavior become justified?
- What refresh cadence gives the best information value per API credit?

The recorder is passive: it analyzes and archives refreshes that were
already being made for Command Center operation. It should not by itself
trigger additional paid API calls.

------------------------------------------------------------------------

## API Quota Governance

### Monthly Reset

The Odds API usage credits reset on the **first day of every month**.

For operational planning, treat each quota period as the calendar month:
first day of the month through the final day of the month.

### Separate Quota Pools

Daily account:
- 500-credit account
- dedicated to the normal daily workflow
- retains moneyline + spread + total behavior

Command Center account:
- 20,000-credit account
- dedicated to fast War Room operation
- spread + total only

The two credentials and quota pools must remain operationally isolated.

### Fast Refresh Cost

Current verified Command Center request:
- spreads
- totals
- one fast current-odds request
- actual observed `x-requests-last`: 2 credits

Do not assume this forever. Continue recording provider response headers:
- `x-requests-last`
- `x-requests-used`
- `x-requests-remaining`

The provider response headers are the runtime source of truth for actual
quota consumption.

### Monthly Budget Controls

The Command Center should track:

- current calendar month
- credits used
- credits remaining
- last-call cost
- number of fast refreshes this month
- number of manual vs scheduled refreshes
- average credits per refresh
- estimated refreshes remaining
- days remaining until the first-of-month reset
- average allowable credits / refreshes per remaining day
- configurable emergency reserve

Recommended calculation:

`available_operating_credits = max(0, credits_remaining - emergency_reserve)`

`daily_operating_budget = available_operating_credits / days_remaining_in_month`

`estimated_fast_pulls_remaining = credits_remaining / recent_average_call_cost`

The Command Center should expose quota status in its health area.

Example:

- Last fast pull
- Last API cost
- Credits used
- Credits remaining
- Estimated fast pulls remaining
- Days until reset
- Current daily operating budget

Automated refresh should be capable of slowing or stopping when quota
health reaches a configured reserve threshold. Manual refresh may remain
available subject to an explicit safety policy.

------------------------------------------------------------------------

## Phase Roadmap

### Phase 0 --- Architecture

Complete:
- purpose
- UI concept
- state definitions
- market hierarchy
- normal-vs-fast market separation
- dedicated fast credential / output namespace
- sportsbook health concept
- latency instrumentation concept
- calendar-month quota-governance model

### Phase 1 --- Data Contract

In progress.

Canonical War Room outputs:
- `war_room_market_matrix.json`
- `war_room_health.json`
- `war_room_signals.json`

Supporting operational artifacts:
- fast normalized spread / total quotes
- fast raw archive
- fast latency audit
- fast pipeline timing audit
- fast refresh history / movement recorder
- API quota health

Audit:
- market contract
- line history
- projections
- betting angles
- injury data
- provider health
- fast sportsbook participation
- fast market completeness
- quota health

### Phase 2 --- UI

Build War Room page from canonical JSON.

Include:
- sportsbook / exchange G-Y-R health strip
- board breadth
- last fast refresh time
- API quota status
- Market Matrix
- model / market state
- signal badges

### Phase 3 --- Live Operations

Add:
- manual refresh
- weekend scheduled cadence
- fast publication
- browser cache-busting
- end-to-end browser timing measurement
- quota-aware automatic refresh controls
- live alerts where justified

### Phase 4 --- Advanced Signals

Future:
- injury adjustments
- coaching edges
- matchup interactions
- shadow improvements
- sharp / exchange lead-lag signals
- market-movement alerts
- edge-decay signals
