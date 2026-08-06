# 2026 NCAAF — Current Priorities and Project Roadmap

_Last updated: 2026-08-06_

This file is the authoritative working backlog for the 2026 NCAAF project. Update it whenever a major decision, regression, completed milestone, or new priority is identified.

## Current production architecture

- Canonical public site: V2 only.
- Main source repository: `/Users/jameslindesmith/NCAAF_MAIN_REPO`
- Main GitHub repository: `barnsey1210/2026_NCAA_Football`
- Operational runtime workspace: `/Users/jameslindesmith/NCAAF_AUTO`
- Manual control repository: `/Users/jameslindesmith/NCAAF_CONTROL`
- Canonical publishing repository: `/Users/jameslindesmith/NCAAF_MAIN_REPO`
- Generated public artifacts: `/Users/jameslindesmith/NCAAF_AUTO/build/public_site`
- LaunchAgent: `com.jim.ncaaf.marketupdate`
- Scheduled daily run: 8:00 AM local time.
- Runtime generates and validates; the canonical main repository publishes.
- Never restore or publish legacy V1, Dashboard, or legacy public-owner artifacts.
- Never broadly synchronize the complete `scripts/` tree from the main repository into the runtime workspace.
- Deploy only explicitly approved source files through the reviewed manifest.
- Publish only through `scripts/publish/publish_site.sh --push` after validation.

## Completed stabilization milestones

### Repository roles clarified

Completed 2026-08-01.

- `NCAAF_MAIN_REPO` is the authoritative source-code repository.
- `NCAAF_AUTO` is the non-Git operational runtime workspace.
- `NCAAF_CONTROL` is limited to guarded/manual refresh and acceptance tooling.
- `NCAAF_SITE` is the public deployment repository.
- Main repository stabilization commit: `9318203` — `Stabilize daily odds and email automation`.

### SGO all-upcoming-games acceptance

Completed 2026-08-01.

Latest validated coverage:

- provider events: 111
- raw pages fetched: 2
- canonical upcoming games expected: 110
- canonical games mapped: 110
- missing canonical games: 0
- games with accepted quotes: 105
- mapped games without accepted quotes: 5
- accepted quote rows: 1,636
- weeks represented: 0, 1, 2, 3, 10, 13
- coverage status: `COMPLETE`
- acceptance eligibility: `True`

The five games without accepted current quotes remain explicitly unavailable rather than being populated with stale lines.

### Daily email regression gate

Completed 2026-08-01.

Latest passing result:

- CSV rows: 48
- Game line moves: 7
- Game line edges: 18
- Exact duplicate rows: 0
- HTML bytes: 33,988
- Visible `nan` values: 0
- Malformed giant prices: 0

The regression gate runs after HTML generation and before email sending.

### Legacy injury-source isolation

Completed 2026-08-05.

- The June-era CFBDepth public-page injury/depth pipeline is isolated from active production.
- Retired injury CSVs must not be interpreted as current or as proof of zero injuries.
- `data/injuries/injury_source_status.json` explicitly reports source, freshness, and coverage state.
- Player-level injury reporting remains unavailable until a validated source is configured.
- Missing current injury reports no longer produce a traceback or block the daily workflow.

### Legacy V1 daily work removed

Completed 2026-08-01.

Removed from recurring daily automation:

- legacy market-futures workbook build,
- legacy site rebuild,
- legacy market-move and arbitrage HTML injectors,
- direct promotion of `index_auto_market.html` into `v1.html`,
- legacy V1 odds-screen build.

Canonical V2 remains the only public-site authority.


### Phase 3 canonical workflow, public ownership, and publishing

Completed 2026-08-05.

Key commits:

- `81f7f79` — canonical current-market contract Phase 1.
- `95f3a75` — Action Network Eastern date mapping and missing-market guard.
- `e352d7d` — shared shell and compact matchup payload.
- `6f9b435` — canonical Openers matchup drawer everywhere.
- `fe852c7` — retired Dashboard, V1, and legacy public ownership.
- `c99e5cc` — tracked Phase 3 helpers and deployment manifest.
- `0f4f9ed` — cached-futures resilience in the daily workflow.
- `97d8611` — daily War Room homepage build and validation.
- `163d173` — first successful canonical publication after Phase 3.

Validated unattended daily workflow result:

- workflow exit code: `0`
- infrastructure audit: `PASS`
- project validators: `PASS`
- public pages checked: 12
- current-market contract games: 902
- stale current quotes displayed: 0
- matchup payload size: 14,772,400 bytes
- main repository unchanged and clean during the unattended run
- email disabled successfully
- live publication disabled successfully

Current public ownership:

- Home is owned by `scripts/site/build_war_room_home.py`.
- Individual game clicks route to the canonical Openers matchup drawer.
- `dashboard.html`, `legacy.html`, and public `v1.html` are retired.
- Shared page shell and navigation are applied through one controlled build path.
- Runtime-generated public artifacts are validated before synchronization into the canonical repository.
- Publication is explicit and no longer occurs accidentally during testing.


### CFBDepth canonical import and shared team asset

Completed 2026-08-06.

Key commits:

- `ff79d95` — deterministic CFBDepth import audit.
- `1835c27` — research CFBDepth matchup enrichment.
- `e4110a8` — expanded matchup preview schema.
- `b53bd3f` — shared CFBDepth team asset.

Validated source coverage:

- 15 official CFBDepth CSV exports archived under `data/raw/cfbdepth/2026-08-05/`.
- 7 team-level datasets imported.
- 12,381 player rows imported and mapped.
- 140 teams with player data; all 138 site teams covered.
- Idaho and UTRGV preserved as non-site teams.
- 1,110 team-position groups generated.
- zero unmapped player-school codes and zero import warnings.

Canonical outputs include team profiles, player ratings, position-group aggregates, top-player summaries, and audit artifacts. The reusable site layer is:

`data/site/cfbdepth_teams_2026.json`

Architecture decision:

- Store each team once in the shared team-indexed asset.
- Let the standalone Matchups page, team pages, and a future lightweight matchup-drawer enhancement pull only the fields they need.
- Do not duplicate full player/team objects into all 902 game records.
- Do not read raw CFBDepth exports directly from page builders.
- Keep the current Openers matchup drawer unchanged until a curated team-level subset is designed.

Next implementation sequence:

1. Design the standalone Matchups UI using the Ohio State–Texas prototype.
2. Connect the shared asset to the standalone Matchups page.
3. Connect the same asset to individual team pages.
4. Add a small curated team-level subset to the existing matchup drawer.
5. Add player-level injury/depth reporting only after a validated source exists.

### Canonical data architecture status

Updated 2026-08-05.

Strongest completed areas:

- current-market contract,
- current/reference/best-side separation,
- current-versus-history audit boundaries,
- controlled page adapters and public ownership,
- explicit deployment manifest,
- staged validation and canonical publishing.

Still incomplete:

- `injury_contract.json`,
- `ratings_contract.json`,
- `schedule_contract.json`,
- `futures_contract.json`,
- `betting_contract.json`,
- `coach_contract.json`,
- smaller domain-driven matchup payloads.

The injury domain still requires a validated player-level source and canonical injury contract. The CFBDepth team/player domain now follows the target pattern, while the future injury domain should follow:

`raw sources → normalization → injury contract → recency-weighted scoring → matchup adapter → Openers drawer`


## Completed priority 1: Safe source deployment

Completed 2026-08-05.

The manifest-based deployment workflow from `NCAAF_MAIN_REPO` to `NCAAF_AUTO` is operational.

Implemented files:

- `deploy/source_manifest.txt`
- `deploy/deploy_to_auto.sh`

Required behavior:

- accept only explicit manifest-listed paths,
- print the main-repository Git commit being deployed,
- create a timestamped backup of every runtime file being replaced,
- never use `--delete`,
- refuse paths outside the approved repository/runtime roots,
- run `bash -n` for shell scripts,
- run `python3 -m py_compile` for changed Python files,
- run the daily betting email regression test,
- stop on validation failure,
- leave runtime data, logs, caches, raw provider responses, and generated site output untouched.

Normal source changes now follow:

1. edit in `NCAAF_MAIN_REPO`,
2. test and commit,
3. deploy through the manifest,
4. validate in `NCAAF_AUTO`,
5. allow the daily runtime to execute,
6. synchronize validated `build/public_site` assets into `NCAAF_MAIN_REPO`,
7. publish explicitly to GitHub Pages.

## Completed priority 2: Daily automation stabilization

Completed 2026-08-05.

The daily workflow now runs through one repo-owned canonical orchestration path.

Implemented behavior:

- keep the `$HOME/Scripts/NCAAF/daily_market_update.sh` launcher thin,
- ensure the launcher contains no business logic,
- maintain one canonical runtime script,
- add a stage manifest,
- add stage-order tests,
- preserve protected loading of SGO and email credentials,
- confirm `NCAAF_SEND_EMAIL=0` disables sending without disabling report generation,
- confirm `NCAAF_AUTO_PUBLISH=0` disables publication without disabling validation,
- preserve canonical V2-only publication,
- keep optional provider failures nonfatal when cached data is explicitly preserved,
- make critical audit failures block sending or publication as appropriate.

## Completed priority 3: Unified current sportsbook quote inventory

Completed substantially through the canonical current-market contract and provider-normalization pipeline.

Current inputs include:

- SportsGameOdds,
- approved current-market fallbacks,
- Action Network where available.

One row per:

`canonical_game_id × sportsbook × market_type × side`

Required fields:

- canonical game ID,
- date,
- week,
- away team,
- home team,
- sportsbook,
- market type,
- side,
- line,
- price,
- source,
- provider event ID,
- provider quote timestamp,
- pull completion timestamp,
- fresh-today flag,
- mapping status.

Canonical output now includes:

- `data/site/current_market_contract.json`

A separate long-form quote inventory may still be retained or expanded for QA and research, but public pages must consume the canonical contract rather than independently select sources.

Apply source priority independently to each game/book/market/side:

1. fresh SportsGameOdds,
2. fresh The Odds API,
3. fresh Action Network,
4. unavailable.

Do not select one provider for an entire game when another fresh provider can fill a missing sportsbook or market.

## Locked game-odds policy

### Current-source priority

For each individual game, sportsbook, market, and side:

1. Fresh SportsGameOdds
2. Fresh The Odds API
3. Fresh Action Network
4. Unavailable

CFBD is not a current sportsbook-odds source. It may be used only for opener/reference or historical context when clearly labeled.

### Freshness

Never display stale odds as current odds.

- Current quotes must come from a successful current-day provider pull.
- Prior-day quotes remain only in line-history data.
- When no current quote exists, display `Odds unavailable`.
- Surface the provider failure or missing-market reason.
- Required publication assertion: `stale_current_quotes_displayed = 0`.

### Target sportsbooks

Primary board:

- DraftKings
- FanDuel
- BetMGM
- Caesars
- Hard Rock Bet

Fanatics should appear only when a provider actually supplies it.

## Priority 1: Injury and depth-chart canonical pipeline

Begin Phase 4 with the first complete non-market canonical domain implementation.

Target flow:

`raw injury and depth-chart sources → normalized events → injury_contract.json → recency-weighted team/game scores → matchup adapter → canonical Openers drawer`

Required work:

- define the `injury_contract.json` schema before UI changes,
- normalize team, player, position, status, source, report date, and update timestamp,
- add approved `report_age_days` and `recency_weight` upstream,
- distinguish report freshness from injury severity,
- incorporate starter status, positional depth, quarterback importance, and replacement quality,
- replace `build_game_injury_scores.py` dependence on legacy embedded V1 HTML,
- distinguish `no injuries found`, `no current report`, `source unavailable`, and `report stale`,
- produce team-level and game-level injury impact,
- expose source provenance and last-updated information,
- build graceful empty and unavailable states,
- add injury-domain propagation and freshness audits,
- integrate the resulting adapter into the canonical Openers matchup drawer,
- include injury status on the System QA page.

Completion gate:

- no public injury component reads legacy V1 data,
- every displayed injury claim maps to the canonical contract,
- recency weighting is applied before page rendering,
- stale or missing reports cannot appear as current,
- injury contract and matchup propagation audits pass.


## Priority 2: Provider-comparison and System QA

Create:

- `data/qa/game_odds_provider_comparison.csv`
- `data/qa/odds_market_status.json`
- `data/qa/odds_market_coverage.csv`
- `data/site/odds_market_status.json`

Report:

- provider pull status,
- last successful pull,
- source freshness,
- games/events returned,
- quotes returned,
- spread, total, and moneyline coverage,
- coverage by target sportsbook,
- selected-source counts,
- fallback counts,
- unavailable markets,
- exact source for each displayed quote,
- stale current quotes displayed,
- API usage and remaining credits when exposed.

Add a compact Odds Data Status panel to the Odds screen and link it to the broader System QA page.

## Dedicated System QA page

Build a first-class QA page summarizing every major site domain.

Suggested artifacts:

- `data/qa/system_status.json`
- `data/qa/system_status_details.csv`
- `data/site/system_status.json`

Each domain card should show:

- Pass / Warning / Fail,
- last successful update,
- age,
- expected records,
- actual records,
- coverage percentage,
- primary source,
- fallback source,
- missing records,
- stale records,
- warnings,
- artifact build timestamp.

Critical failures should block publication. Warnings may publish but must appear prominently.

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

## Daily betting email

Preserve the known-good sequence:

1. `build_daily_betting_angles.py`
2. `append_daily_game_line_edges.py`
3. `prepend_game_line_moves_to_daily_betting_angles.py`
4. `prepend_injury_alerts_to_daily_betting_angles.py`
5. `clean_daily_game_line_moves.py`
6. `build_daily_betting_angles_html.py`
7. `test_daily_betting_email_regression.py`
8. send email only after the gate passes.

Continue protecting against:

- juice-only/price-only movement,
- malformed prices,
- duplicate cards,
- visible `nan`,
- missing game-line moves,
- missing game-line edges.

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

- returning production,
- Five Factors,
- coaching ATS,
- coach first-half and second-half performance,
- coach totals performance,
- schedule spots,
- rest and travel,
- back-to-back road games,
- step-up/step-down in competition,
- ratings movement,
- injuries,
- quarterback importance,
- market movement,
- matchup style,
- luck and consistency.

For each signal, display:

- supporting or contradictory direction,
- historical sample size,
- ATS or over/under record,
- ROI,
- confidence,
- applicable splits,
- closing-line comparison,
- evidence quality.

Saved research priority:

Study the last three years of Weeks 0–4 games involving high-returning-production teams versus low-returning-production teams. Test favorite/underdog permutations, identify matching 2026 games, and integrate validated findings into the signal engine.

Next historical validation areas:

1. Five Factors
2. Coaching
3. Schedule spots
4. Ratings movement

## Matchup page

- Preserve Five Factors prominence.
- Improve offense-versus-opponent-defense comparisons.
- Convert betting snapshot categories into validated signals.
- Add evidence/confidence instead of unsupported labels.
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

## Injury and roster follow-on work

After the canonical injury pipeline is live:

- add depth-chart movement history,
- track estimated replacement value by position,
- retain historical injury snapshots for betting research,
- compare injury signal performance against closing lines and results,
- add team-dashboard roster availability trends.

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
- Write a release manifest with run ID, inputs, outputs, source commit, and warnings.
- Confirm publication contains current canonical HTML and assets.
- Prevent silent fallback to legacy artifacts.

## Recommended execution order

1. Complete Phase 4 injury and depth-chart canonical pipeline.
2. Add injury propagation, freshness, and source-state audits.
3. Integrate the injury adapter into the canonical Openers drawer.
4. Build provider-comparison QA and the broader System QA page.
5. Formalize ratings and schedule canonical contracts.
6. Formalize futures, betting, and coach canonical contracts.
7. Reduce the 14.8 MB matchup payload through domain-driven adapters.
8. Repair remaining futures freshness and coverage gaps.
9. Resume Betting Signal Engine historical validation.
10. Continue matchup, ratings, schedule, simulation, and in-season improvements.

## Current next action

Audit the existing injury and depth-chart scripts, inputs, outputs, data freshness, and legacy dependencies. From that audit, define the first version of `injury_contract.json` before changing the public matchup UI.

## Change-log rule

Whenever a major item is completed or reprioritized:

1. Update this file in `NCAAF_MAIN_REPO`.
2. Commit it to the main GitHub repository.
3. Deploy it to `NCAAF_AUTO` through the approved manifest.
4. Replace the copy in the ChatGPT project Source Files.
5. Include completion dates, validation results, and relevant run/commit IDs.
6. Keep completed milestones in this file rather than deleting their history.
