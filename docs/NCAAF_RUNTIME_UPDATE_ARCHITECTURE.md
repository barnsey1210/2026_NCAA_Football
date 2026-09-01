# Canonical NCAAF Runtime Update Architecture

_Canonical repository and runtime execution boundary: 2026-08-24_  
_Status: architecture contract; current and future capabilities are identified explicitly_

## Purpose

This document is the canonical operational map from provider observations to
public pages. It defines where source code lives, where production work runs,
how the full daily build coexists with bounded fast paths, and which components
may own data, lifecycle decisions, builds, and publication.

This document does not authorize a provider request, scheduler, workflow,
controller, UI, credential, or deployment change. Code present in
`NCAAF_MAIN_REPO` is not evidence that the corresponding production execution
is active in `NCAAF_AUTO`.

Related authority documents:

- `docs/WAR_ROOM_DATA_ARCHITECTURE.md`
- `docs/WAR_ROOM_EVENT_SCHEMA.md`
- `docs/WAR_ROOM_LIFECYCLE_OPERATIONAL_MODEL.md`
- `docs/WAR_ROOM_PROJECTION_AUTHORITY.md`
- `docs/WAR_ROOM_PROVIDER_SERVICES_AND_API_BUDGETS.md`
- `docs/DAILY_AUTOMATION.md`
- `config/public_page_data_contracts.json`

## 1. System architecture overview

```text
PROVIDERS / SOURCE OWNERS
  The Odds API | CFBD Tier 2 | rating providers | projection inputs
                              |
                              v
RUNTIME PROVIDER SERVICES (NCAAF_AUTO)
  Market Service | Postgame Service | Ratings Service
                              |
                    validated observations
                              v
CANONICAL DOMAIN OWNERS AND CONTRACTS
  market | results/postgame | ratings/provider versions | projections
                              |
                    immutable lifecycle events
                              v
LIFECYCLE CONTROLLER / REDUCER (future production component)
  ingest events | idempotency | reduce state | request tasks | track retries
                              |
                  existing builders and validators
                              v
BUILD / PUBLICATION LAYER
  build/public_site | allowlist | validation | MAIN_REPO publication
                              |
                              v
PUBLIC PAGES
  War Room | Matchups | Ratings | Odds | Futures | simulations | other pages
```

Ownership flows downward; authority does not. Providers own source evidence,
domain pipelines own canonical acceptance and calculations, the future
controller owns orchestration, and the publisher owns release gates. The
controller does not own formulas, provider truth, projection authority, market
selection, betting edges, page rendering, or publication approval.

Public pages consume canonical artifacts. They must not call providers,
choose a provider, calculate API budgets, or create page-local data authority.

## 2. MAIN_REPO and NCAAF_AUTO boundary

### `NCAAF_MAIN_REPO` owns

- architecture and operating documentation;
- schemas and canonical data-contract definitions;
- production source code and deployment manifests;
- tests, simulations, audits, and validators;
- reviewed changes before runtime deployment; and
- the canonical GitHub Pages publishing repository.

### `NCAAF_AUTO` owns

- the deployed, manifest-controlled runtime copy;
- scheduled and operator-triggered execution;
- protected credentials and environment variables;
- runtime locks, task attempts, logs, ledgers, and state;
- provider acquisition and production orchestration; and
- generated runtime and staged public artifacts.

### Direction of travel

```text
reviewed source change
MAIN_REPO -- deploy/source_manifest.txt + deploy/deploy_to_auto.sh --> AUTO

validated public artifact
AUTO/build/public_site -- explicit public allowlist --> MAIN_REPO --> GitHub Pages
```

Deployment is explicit, manifest-only, and non-destructive. `AUTO` is not a
development fork and must not become an independent source of production
behavior. A runtime-only correction must be promoted to `MAIN_REPO`, reviewed,
validated, and redeployed before it is canonical.

Secrets, credential values, machine-local environment files, runtime locks,
execution logs, mutable controller state, provider budget ledgers, and
unreviewed runtime source must never flow into `MAIN_REPO`. Raw or derived data
may flow back only when its canonical contract and public/research retention
policy explicitly allow it. Public release copies only allowlisted artifacts;
it never recursively synchronizes the runtime data tree.

`NCAAF_CONTROL` remains the boundary for guarded/manual acceptance tooling.
`/Users/jameslindesmith/Sites/NCAAF_SITE` is legacy and has no canonical runtime
or publication role.

## 3. Full 8 AM daily rebuild

The existing scheduled 8 AM run is the full production backbone. The
machine-local launcher loads protected runtime environment values and invokes
the deployed `NCAAF_AUTO/daily_market_update.sh`. The stage registry is
`config/daily_stages.json`.

The full run is responsible for:

1. acquiring approved market, ratings, schedule/result, injury, and futures
   inputs according to stage policy;
2. validating and normalizing source data;
3. building canonical market, ratings, projection, matchup, line-history,
   Shadow, odds, futures, simulation, and site artifacts;
4. assembling `build/public_site`;
5. running blocking public and propagation validation; and
6. when enabled, publishing the allowlisted validated bundle through
   `scripts/publish/publish_site.sh`.

Principal canonical artifacts include:

- `data/site/current_market_contract.json`;
- `data/ratings/ratings_master_latest.csv` and source-status/history outputs;
- `data/site/current_game_projection_contract.json`;
- canonical schedule, results, and postgame feature artifacts;
- `data/site/matchups_view.json` and `data/site/matchup_line_history.json`;
- `data/site/odds_screen_v2.json` and futures/simulation views;
- `data/site/war_room_health.json` and
  `data/site/war_room_market_matrix.json`; and
- the complete validated `build/public_site` bundle.

The public build covers the War Room, Ratings, Matchups, Openers, Odds,
Schedule, Futures, Conferences, Playoff, simulations, Betting, team and other
allowlisted site pages. Exact page-to-contract ownership remains governed by
`config/public_page_data_contracts.json` and the public publish manifest.

The full rebuild is a batch process. Source release discovery, near-real-time
final detection, provider-version monitoring, and targeted ratings/postgame
publication remain batch-only or manual unless a fast path below is explicitly
implemented and activated. Fast updates supplement the 8 AM rebuild; they do
not replace, skip, or weaken it.

## 4. Fast runtime update architecture

Each fast path is an independent, scope-limited runtime transaction:

```text
request/event -> provider service decision -> acquisition/acceptance
              -> canonical contract -> affected build -> validation
              -> allowlisted publication -> observable completion
```

No fast path may modify a page directly, bypass a domain owner, publish an
unvalidated artifact, use a different budget gate, or promote cached data as
current after a failed refresh.

### 4A. Market refresh

**Current status:** bounded War Room market acquisition and targeted
publication exist. Broader event-driven market orchestration does not.

```text
MARKET_REFRESH_REQUESTED or future MARKET_FIRST_SEEN observation
  -> Market Service (The Odds API)
  -> quota/reserve/cooldown/lock decision
  -> accepted fast market snapshot
  -> war_room_health.json + war_room_market_matrix.json
  -> War Room build and fast-bundle validation
  -> allowlisted three-file publication
```

Current fast publication is limited to:

- `war-room.html`;
- `data/site/war_room_health.json`; and
- `data/site/war_room_market_matrix.json`.

It does not replace `current_market_contract.json` or silently rebuild Odds,
Openers, Matchups, or Futures. Expanding the fast contract to those pages
requires a separately approved central contract and propagation audit.

Manual and automatic requests use the same Market Service budget, credential,
reserve, lock, cooldown, freshness, and coverage gates. Browser reload of
already published JSON is a zero-credit action. Target: a validated approved
fast refresh should reach publication in seconds to a few minutes, with the
actual latency recorded rather than inferred.

### 4B. Ratings refresh

**Current status:** ratings stages and canonical builders exist in the full
pipeline. Provider-event monitoring and targeted fast publication are not yet
production-wired.

```text
RATING_SOURCE_UPDATED
  -> Ratings Service validates and accepts a new immutable provider version
  -> existing projection-authority owner evaluates spread and total separately
  -> projection rebuild requested only when required
  -> affected contracts/pages built and validated
  -> scoped publication
```

Spread and total authority transition independently through `SHADOW`,
`HYBRID`, and `OFFICIAL` according to
`docs/WAR_ROOM_PROJECTION_AUTHORITY.md`. The controller records authority facts;
it does not calculate thresholds or formulas. Rejected panels retain the last
accepted version. Corrections create a new version. Carry-forward values remain
visible with explicit stale/freshness labels and never masquerade as updated.

Target: accepted provider version to validated affected publication in a few
minutes. This is a future service-level objective, not a claim about current
production automation.

### 4C. Postgame refresh

**Current status:** postgame scripts/profile and isolated lifecycle rehearsal
exist. Automatic final polling, persisted production events, and event-driven
dispatch are not yet active.

```text
GAME_FINAL (canonical result using accepted CFBD Tier 2 evidence)
  -> Postgame Service requests/acquires required completed-game data
  -> validation and accepted postgame feature version
  -> POSTGAME_READY
  -> Shadow lifecycle tasks/events
  -> affected contracts/pages built and validated
  -> scoped publication
```

CFBD owns schedule/status observations, final evidence, plays, drives, havoc,
advanced game statistics, and preserved historical source evidence. It does
not own canonical result identity, Shadow formulas, authority, market values,
edges, or publication.

Missing or delayed CFBD data yields pending/retryable state, not a fabricated
`POSTGAME_READY`. Retries must be bounded, idempotent, budget-aware, and retain
attempt history. Accepted corrections append versions instead of overwriting
history. Target: final detection and basic public state in minutes; feature and
Shadow readiness follows actual provider availability and is reported
separately.

## 5. Future Command Center operator controls

| Control | Execution owner | Service | Gate | Affected scope | Publication |
|---|---|---|---|---|---|
| Refresh Market | `NCAAF_AUTO`, requested through guarded operator boundary | Market | The Odds API budget, reserve, quota, lock, cooldown | Canonical fast market contracts; currently War Room only | Targeted, validated allowlist |
| Refresh Ratings | `NCAAF_AUTO` | Ratings | provider policy, acceptance/version validation, overlap lock | Accepted provider versions, authority/projections if changed, affected pages | Targeted only after all gates |
| Refresh Postgame | `NCAAF_AUTO` | Postgame | CFBD Tier 2 budget, game eligibility, lock, retry policy | Result/postgame/Shadow artifacts and affected pages | Targeted only after all gates |
| Full Rebuild | `NCAAF_AUTO` | canonical daily orchestrator | all stage, validation, and publication gates | complete daily contract and public bundle | full allowlisted publication |

Buttons or operator commands request runtime work; they never execute provider
calls in browser JavaScript or edit public pages. Every action records requester,
request time, correlation/idempotency keys, service decision, attempts, budget
facts without secrets, outputs, validation, publication result, and failure.
Manual actions receive no quota, emergency-reserve, validation, or authority
bypass.

Only Refresh Market has a bounded existing operator path. The other controls
are architectural requirements, not implemented UI commitments.

## 6. Automatic refresh behavior

The full rebuild remains schedule-triggered. Future fast execution may be
triggered by an approved schedule, a persisted lifecycle event, or bounded
provider polling after cadence and budget approval. All triggers enter the same
service gates and idempotent task path as manual requests.

Retryable failures use bounded backoff and persist each attempt. Terminal,
quota, reserve, validation, configuration, or stale-source failures fail closed
and preserve the last-known-good public artifact with its original timestamp.
They must not relabel it as current. Overlapping work is deduplicated or blocked
by task identity and runtime locks.

Once publication completes, GitHub Pages receives the new allowlisted artifact.
Public JSON requests should use the established cache-busting/no-store policy
where applicable. A normal browser navigation or cache revalidation should show
the release; there is no current promise of server push, SSE, or an always-open
page updating without any browser request. Publication time, source time, data
age, health, and last failure should be exposed through existing health/status
contracts rather than invented by page code.

## 7. Runtime latency observability

Every provider-backed or publication task must retain these UTC timestamps:

- `request_time`;
- `provider_start` and `provider_complete`;
- `build_start` and `build_complete`;
- `validation_start` and `validation_complete`; and
- `publication_start` and `publication_complete`.

Where a stage is not applicable, it is explicitly null/skipped; timestamps are
never backfilled from file modification times. Records also require task/run
identity, trigger type, attempt number, outcome, and failure/retry status.

Latency classes:

| Path | Architectural target | Measurement |
|---|---|---|
| Fast market | seconds to a few minutes | request to publication, plus each segment |
| Fast ratings | a few minutes after accepted provider version | acceptance to publication |
| Fast postgame | final detection in minutes; readiness follows provider availability | observed final, acquisition, readiness, publication separately |
| Full rebuild | batch; no fast SLA | complete stage/run duration |

These are initial operational targets, not guaranteed SLAs. Production
measurements must establish alert thresholds. Command Center health should show
last successful refresh, source age, active/retry state, and last failure without
exposing credentials or provider response bodies.

## 8. API budget integration

The provider service, not the lifecycle controller, owns cost estimation,
ledger reconciliation, and approval.

### The Odds API

- 20,000 credits per UTC calendar month;
- 2,000-credit protected emergency reserve;
- 18,000 credits maximum for normal operations; and
- one shared gate for scheduled, fast, and manual acquisition.

### CFBD

- Tier 2 is approved;
- it has an independent UTC calendar-month ledger; and
- its protected key will be wired later through runtime secret/environment
  handling.

The controller records service decisions and resulting events. It does not
calculate provider cost, approve spending, release reserve credits, or combine
provider ledgers.

## 9. Page dependency model

| Page/domain | Full daily canonical inputs | Fast input today | Future affected fast path |
|---|---|---|---|
| War Room | market, projection, ratings, Shadow, results/health contracts | War Room health and market matrix | market, ratings, postgame |
| Matchups/Openers | matchup view, current market, line history, projections | none | market/status only after central contract approval |
| Ratings | ratings view/status/history | none | accepted rating versions |
| Odds | production odds-screen/futures contracts | none | market only after central contract approval |
| Futures | futures view and simulations | none | approved market/futures path |
| Simulations/other pages | their registered canonical site contracts | none | only explicitly registered dependencies |

“Affected” means a canonical contract changed and its registered consumer must
be rebuilt. It does not authorize broad publication. Pages never call The Odds
API, CFBD, or rating providers directly and never substitute a page-local cache
for a failed canonical refresh.

## 10. Implementation roadmap

### Architecture complete

- MAIN/AUTO authority and allowlisted publication boundary;
- provider-service ownership and budget boundaries;
- lifecycle, event, projection-authority, and replay contracts;
- full daily orchestration and public validation model; and
- fast-path safety and observability requirements.

### Built and operating

- scheduled 8 AM full batch backbone in `NCAAF_AUTO`;
- manifest-controlled MAIN-to-AUTO deployment;
- canonical builders, validators, full public build, and publisher;
- guarded fast War Room market acquisition/publication path; and
- current health and market-matrix artifacts.

### Built only as simulation or isolated tooling

- lifecycle reducer/rehearsal and event-schema compatibility;
- historical Shadow lifecycle rehearsal; and
- manual/profile subsets that do not constitute event-driven production.

### Future runtime work in `NCAAF_AUTO`

1. persist the append-only event log, task attempts, and reducer snapshots;
2. implement the controller as orchestration only;
3. wire CFBD Tier 2 credentials and measured Postgame Service cadence;
4. implement accepted ratings-version monitoring and targeted rebuilds;
5. add scoped artifact dependency planning and publication gates;
6. add recovery/replay commands and operational telemetry; and
7. complete a real 2026 game-final acceptance test before automatic activation.

### Future scheduler work

- approve and install bounded market windows;
- approve final/status polling cadence from measured CFBD Tier 2 usage;
- schedule provider-release checks without duplicating work; and
- define retry, blackout, and escalation policy.

### Future UI work

- add guarded Ratings/Postgame/Full operator requests only after runtime owners
  exist;
- display service decision, task, freshness, latency, and failure facts from
  canonical health contracts; and
- preserve zero-credit reload separately from acquisition.

No roadmap item is active merely because its interface, simulation, or source
file exists in `NCAAF_MAIN_REPO`.
