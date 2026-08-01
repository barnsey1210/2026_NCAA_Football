# 2026 NCAAF — Current Priorities and Project Roadmap

_Last updated: 2026-08-01_

This file is the authoritative working backlog for the 2026 NCAAF project. Update it whenever a major decision, regression, completed milestone, or new priority is identified.

## Current production status

- Canonical site: V2 only.
- Preservation repository: `/Users/jameslindesmith/NCAAF_CONTROL`
- Working repository: `/Users/jameslindesmith/NCAAF_AUTO`
- Publication repository: `/Users/jameslindesmith/Sites/NCAAF_SITE`
- LaunchAgent: `com.jim.ncaaf.marketupdate`
- Scheduled daily run: 8:00 AM local time.
- Never restore or publish legacy V1 artifacts.

## Immediate blocker: SGO all-upcoming-games acceptance

The fresh SportsGameOdds pull is working and the API key is restored.

Latest successful raw pull:

- Fresh raw response written on 2026-08-01.
- Two pages fetched.
- SGO returned odds beyond Week 0.
- Week 0 accepted output contained 198 quote rows across DraftKings, FanDuel, BetMGM, Caesars, and Bovada.

However, the attempted all-upcoming-games patch did not take effect. Current coverage output still reports:

- `schema_version: canonical-market-coverage-v1`
- `scope: FBS-vs-FBS canonical site week`
- `selected_week: 0`
- `expected_canonical_games: 8`
- `mapped_canonical_games: 8`

This means production acceptance is still restricted to the selected canonical week.

### Required fix

Update the actual active code path so SGO accepts every upcoming canonical game represented in the fresh provider response. The default week on the Odds page must remain a UI-only setting and must not constrain provider acceptance.

Files to inspect first:

- `scripts/control/sgo_preview_adapter.py`
- `scripts/markets/build_sgo_canonical_artifacts.py`
- `scripts/markets/build_sgo_daily_canonical.py`
- `scripts/control/run_data_refresh.py`
- SGO acceptance tests under `scripts/audit/`

Required coverage output after repair:

- all upcoming canonical games in scope
- weeks represented
- mapped and missing games by week
- accepted quotes by sportsbook and market
- unmatched and ambiguous provider events
- pagination completion
- freshness status
- no selected-week restriction in acceptance logic

Do not publish the all-games change until the coverage artifact proves more than eight games and multiple weeks are accepted.

## Locked game-odds policy

### Source priority

For each individual game, sportsbook, market, and side:

1. Fresh SportsGameOdds
2. Fresh The Odds API
3. Fresh Action Network
4. Unavailable

CFBD is not a current sportsbook-odds source. It may be used only for opener/reference or historical context when clearly labeled.

### Freshness rule

Never show stale odds as current odds.

- Current quotes must come from a successful current-day provider pull.
- Prior-day quotes remain only in line-history data.
- When no current quote exists, display `Odds unavailable` and surface the provider failure or missing-market reason.
- Required publication assertion: `stale_current_quotes_displayed = 0`.

### Target sportsbooks

Primary board:

- DraftKings
- FanDuel
- BetMGM
- Caesars
- Hard Rock Bet

Fanatics should be added only when a provider actually supplies it.

### Current provider findings

SportsGameOdds:

- Includes Caesars.
- Includes moneylines, spreads, and totals.
- Current accepted output is artificially limited to Week 0 by our code.

The Odds API:

- Raw file exists at `data/odds/theodds_ncaaf_lines_2026_raw.json`.
- Current raw comparison contained 126 events.
- FanDuel: 110 events.
- DraftKings: 75 events.
- BetMGM: 48 events.
- Hard Rock Bet: 69 events.
- Caesars: unavailable in the free feed.
- Fanatics: unavailable.
- Existing season normalizer collapses the raw book-level inventory to one selected spread and total book; this must not drive the new sportsbook comparison board.

Action Network:

- Daily supplemental/fallback source.
- Important Caesars fallback when SGO is unavailable.
- Must retain exact provider provenance and timestamps.

## Immediate implementation sequence

### 1. Repair SGO all-upcoming-games acceptance

- Remove the canonical selected-week restriction from the active acceptance path.
- Preserve the UI default week separately.
- Update coverage schema and tests.
- Validate multiweek mapped game counts.

### 2. Normalize complete sportsbook quote inventories

Create quote-level outputs for:

- SportsGameOdds
- The Odds API
- Action Network

One row per:

`canonical_game_id × sportsbook × market_type × side`

Required fields:

- canonical game ID
- date, week, away team, home team
- sportsbook
- market type
- side
- line
- price
- source
- provider event ID
- provider quote timestamp
- pull completion timestamp
- fresh-today flag
- mapping status

### 3. Build unified current quote selection

Create:

- `data/odds/current_game_book_quotes.csv`

Apply the locked source hierarchy independently to every book/market/side. Do not select a single provider for an entire game when another provider can fill a missing book or market.

### 4. Build provider-comparison QA

Create:

- `data/qa/game_odds_provider_comparison.csv`
- `data/qa/odds_market_status.json`
- `data/qa/odds_market_coverage.csv`
- `data/site/odds_market_status.json`

Report:

- provider pull status and last successful pull
- source freshness
- games/events returned
- quotes returned
- spreads, totals, and moneyline coverage
- coverage by DraftKings, FanDuel, BetMGM, Caesars, and Hard Rock
- selected-source counts
- fallback counts
- unavailable markets
- exact source for every displayed quote
- stale current quotes displayed
- API usage and remaining credits when exposed

### 5. Update the Odds screen

Add a compact Odds Data Status panel showing:

- last successful pull for each source
- current/stale/failed status
- games and quote counts
- coverage by market and book
- displayed-source counts
- fallback counts
- unavailable markets
- stale quotes shown, required to be zero

The panel should link to the dedicated System QA page.

## Daily automation stabilization

The automation regression must remain a top priority after the SGO scope repair.

### Canonical orchestration

- Restore a thin LaunchAgent launcher.
- Use exactly one repo-owned canonical daily orchestration path.
- Remove duplicated pipeline business logic from `$HOME/Scripts/NCAAF/daily_market_update.sh`.
- Preserve canonical V2 only.
- Prevent legacy V1 builders and direct legacy `index.html` promotion.
- Ensure protected environment loading includes the SGO key and email credentials.
- Add a stage manifest and stage-order tests.
- Add a test proving the launcher contains no business logic.

### Required daily stages

Preserve and verify:

- SGO live pull and canonical processing
- The Odds API controlled pull
- Action Network game lines and futures
- game line history
- market movement
- ratings refresh
- ratings history and movement
- projection sources and blend
- matchup and site views
- injury alerts
- betting-angle generation
- email HTML build
- email sending
- canonical V2 validation and publication

## Daily betting email fixes

Restore the known-good sequence:

1. `build_daily_betting_angles.py`
2. `append_daily_game_line_edges.py`
3. `prepend_game_line_moves_to_daily_betting_angles.py`
4. `prepend_injury_alerts_to_daily_betting_angles.py`
5. `clean_daily_game_line_moves.py`
6. `build_daily_betting_angles_html.py`
7. send email

Required regression protections:

- exclude juice-only/price-only movement
- prevent malformed prices such as `+102204.0`
- remove duplicate cards
- remove `nan` output
- preserve injury alerts, betting angles, market movement, and ratings movement
- test rendering against saved fixtures
- verify email output before unattended sending resumes

## Dedicated System QA page

Build a first-class QA page summarizing every major site domain.

Suggested artifacts:

- `data/qa/system_status.json`
- `data/qa/system_status_details.csv`
- `data/site/system_status.json`

Each domain card should show:

- Pass / Warning / Fail
- last successful update
- age
- expected records
- actual records
- coverage percentage
- primary source
- fallback source
- missing records
- stale records
- warnings
- artifact build timestamp

Domains:

- Home / Command Center
- Ratings
- Team dashboards
- Schedule and results
- Matchups
- Game odds
- Futures
- Injuries
- Weather
- Coaching and ATS
- Projections and simulations
- Line history and movement
- Betting signals
- Model tracking
- Daily email
- Site publication

Critical failures should block publication. Warnings should publish but appear prominently on the QA page.

## Futures-market work

- Repair stale Action Network playoff futures pulls.
- Audit win totals, conference titles, CFP, national title, and Heisman.
- Track coverage and freshness by sportsbook.
- Preserve futures price history and movement.
- Add explicit stale/unavailable states.
- Improve futures board readability.
- Rebuild projections and simulations after ratings updates.

## Betting Signal Engine

The site should become an evidence-weighted decision engine rather than only a prediction model.

Signals to validate historically:

- returning production
- Five Factors
- coaching ATS
- coach first-half and second-half performance
- coach totals performance
- schedule spots
- rest and travel
- back-to-back road games
- step-up/step-down in competition
- ratings movement
- injuries
- quarterback importance
- market movement
- matchup style
- luck and consistency

For each signal, display:

- supporting or contradictory direction
- historical sample size
- ATS or over/under record
- ROI
- confidence
- applicable splits
- closing-line comparison
- evidence quality

Saved research priority:

Study the last three years of Weeks 0–4 games involving high-returning-production teams versus low-returning-production teams. Test favorite/underdog permutations, identify matching 2026 games, and integrate validated findings into the signal engine.

Next historical validation areas after returning production:

1. Five Factors
2. Coaching
3. Schedule spots
4. Ratings movement

## Matchup page

- Preserve Five Factors prominence.
- Improve offense-versus-opponent-defense comparisons.
- Convert betting snapshot categories into validated signals.
- Add evidence/confidence rather than unsupported labels.
- Improve missing coach, QB, injury, and style warnings.
- Ensure line-history provenance is correct.
- Add current-odds availability states.
- Connect ratings movement and model tracking.

## Ratings, projections, and model tracking

- Maintain SP+, FPI, TeamRankings, and Brad Powers blend.
- Audit source update dates.
- Maintain ratings history and movement.
- Rebuild projection sources and blend.
- Rerun season simulations after ratings updates.
- Update win totals and conference-title projections.
- Continue Donchess, DRatings, Sagarin, and Massey work.
- Retest DRatings when 2026 predictions become active.
- Track model ATS, total, moneyline, and closing-line performance.

## Injuries and roster data

- Implement approved `report_age_days` and `recency_weight` upstream.
- Repair injury scoring dependence on legacy `index.html`.
- Integrate player importance and QB depth consistently.
- Distinguish `no injuries found` from `source not current`.
- Include injury status on the System QA page.

## Schedule and in-season operations

- Complete later-season schedule sourcing.
- Pull current full-game spread and total odds.
- Pull final scores and completed results.
- Update records and conference records.
- Update team and coach ATS and totals records weekly.
- Maintain full-game, first-half, and second-half trends.
- Add forward-looking team dashboard metrics including luck, consistency, rating trends, ATS performance, schedule strength, and upcoming competition changes.

## Publication safeguards

- V2 is the only canonical public site.
- Validate staged assets before publication.
- Require critical QA gates.
- Preserve approved changes in `NCAAF_CONTROL`.
- Write a release manifest with run ID, inputs, outputs, commit, and warnings.
- Confirm GitHub publication contains current canonical HTML and assets.
- Prevent silent fallback to legacy artifacts.

## Recommended execution order

1. Repair and validate SGO all-upcoming-games acceptance.
2. Consolidate daily automation into one canonical orchestration path.
3. Finish daily email regression fixes and tests.
4. Build unified fresh sportsbook quote inventory.
5. Eliminate stale current odds.
6. Build Odds QA artifacts and Odds status panel.
7. Build the broader System QA page.
8. Repair futures freshness and coverage.
9. Resume Betting Signal Engine validation.
10. Continue matchup, ratings, injuries, schedule, and in-season improvements.

## Change-log rule

Whenever a major item is completed or reprioritized:

1. Update this file.
2. Commit it to `NCAAF_CONTROL`.
3. Keep a copy in the active project source files.
4. Add the completion date and relevant run/commit IDs.
