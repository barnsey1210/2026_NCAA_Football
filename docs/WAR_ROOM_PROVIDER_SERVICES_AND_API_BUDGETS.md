# War Room Provider Services and API Budgets

_Canonical provider-service and API-budget architecture: 2026-08-24_

_Status: architecture only; no provider, workflow, scheduler, or controller changes_

## Purpose and authority

This document is the canonical owner of provider-service responsibilities,
API-budget boundaries, calendar-month accounting, provider-task approval, and
cost observability for the War Room lifecycle.

It complements:

- `docs/NCAAF_RUNTIME_UPDATE_ARCHITECTURE.md`;
- `docs/WAR_ROOM_EVENT_SCHEMA.md`;
- `docs/WAR_ROOM_LIFECYCLE_OPERATIONAL_MODEL.md`;
- `docs/WAR_ROOM_SYSTEM_LIFECYCLE.md`; and
- `docs/WAR_ROOM_DATA_ARCHITECTURE.md`.

Provider services own acquisition truth and API economics. The lifecycle
controller may request provider work and consume provider decisions, but it
cannot approve its own request, calculate provider costs, or redefine a
provider's data authority.

## 1. Provider service ownership

### Market Service

**Approved provider:** The Odds API.

The Market Service owns:

- market acquisition and refresh execution;
- validation of market-refresh requests against provider policy;
- accepted raw and normalized market snapshots;
- provider quota-header capture and reconciliation;
- request and credit-consumption accounting;
- calendar-month budget state;
- refresh approval, deferral, rejection, and quota-exceeded decisions; and
- lock, cooldown, and available-budget gating before an API call.

The Market Service does **not** own:

- betting edges or recommendations;
- projection formulas or authority;
- model selection;
- UI state or publication decisions; or
- lifecycle-controller policy.

Market normalization and canonical market authority remain with the existing
market contract owner. Provider acquisition does not grant The Odds API
authority over projections or betting decisions.

### Postgame Service

**Approved provider:** CollegeFootballData API Tier 1.

The Postgame Service owns acquisition and preservation of:

- schedule and game-status observations;
- evidence used by the canonical results owner for `GAME_FINAL`;
- postgame plays;
- drives;
- havoc;
- completed-game havoc statistics; and
- historical raw/accepted data for replay and future research.

CFBD Tier 1 is the locked production tier. Free-tier sufficiency is closed and
must not be re-investigated as an implementation prerequisite. Future CFBD
research acquisition may expand, but it does not change these authority
boundaries.

The Postgame Service does **not** own:

- ratings authority;
- projection formulas or authority;
- market authority;
- betting edges; or
- lifecycle or publication approval.

Canonical result mapping and postgame feature acceptance remain downstream
validated responsibilities. A provider response alone is not `POSTGAME_READY`.

### Ratings Service

The Ratings Service owns:

- source-specific rating acquisition/checks;
- candidate validation and accepted provider versions;
- immutable changed, rejected, and corrected version history;
- source freshness and source/pull/acceptance timestamps; and
- provider release/change detection.

The Ratings Service does **not** own:

- projection formulas or forecast calculations;
- authority selection or authority thresholds;
- market calculations; or
- betting edges.

Accepted provider versions are inputs to projection and authority owners. A
rating release event does not itself calculate a projection or select an
authority tier.

## 2. Calendar-month budget contract

All API budgets are calendar-month budgets.

```text
Budget period begins: 00:00:00 UTC on day 1 of the calendar month
Budget period ends:   23:59:59.999... UTC on the final calendar day
Next reset:           00:00:00 UTC on day 1 of the next calendar month
```

Budgets must not be represented as football-week, season, weekend, or rolling
30-day budgets. Daily and weekend measurements are subdivisions of the active
calendar-month ledger, not independent credit pools.

Every provider budget state requires:

- provider and credential/account identity without secret material;
- calendar month in `YYYY-MM` UTC form;
- period start and end in UTC;
- configured monthly allocation when the provider exposes one;
- consumed units and source of truth for that value;
- remaining provider units;
- protected reserve when applicable;
- remaining normal-operating units;
- request history and latest reconciliation time; and
- status such as `NORMAL`, `DEFERRED`, `RESERVE_ONLY`, `EXHAUSTED`, or
  `UNAVAILABLE`.

Month rollover opens a new ledger period. Prior monthly usage remains immutable
for audit and research.

## 3. The Odds API budget

Locked values:

| Item | Credits |
|---|---:|
| Calendar-month allocation | 20,000 |
| Protected emergency reserve | 2,000 |
| Maximum normal-operating budget | 18,000 |

The emergency reserve is unavailable to normal scheduled, fast, manual, test,
or ancillary acquisition. Credits above the reserve are available for normal
operations subject to quota reconciliation, approved cadence, locks,
cooldowns, request-cost policy, and validation gates.

The Market Service tracks:

- monthly allocation;
- credits consumed;
- provider-reported remaining credits;
- remaining normal-operating credits;
- emergency-reserve status;
- per-request estimated and actual cost;
- quota headers and reconciliation status; and
- immutable request/decision history.

The Market Service records these outcomes:

- `REQUESTED`: refresh requested but not yet decided;
- `APPROVED`: budget and execution gates permit acquisition;
- `DEFERRED`: acquisition may be retried after a specified time/condition;
- `REJECTED`: policy denies the request;
- `QUOTA_EXCEEDED`: provider balance or protected reserve blocks it; and
- `COMPLETED` / `FAILED`: execution result after an approved request.

The lifecycle controller consumes those facts. It does not calculate request
cost, pricing, consumption, reserve availability, or approval.

### Current operating paths

#### Daily acquisition

Purpose: one full daily baseline refresh through the canonical daily market
pipeline. It preserves raw response evidence, normalized market data, quota
headers, and request accounting.

#### Fast Command Center acquisition

Purpose: operational spreads/totals updates for Saturday-night releases,
Sunday movement windows, and guarded manual operator refresh.

The fast path must preserve:

- dedicated credential isolation;
- provider quota headers;
- estimated and actual request accounting;
- single-instance lock protection;
- quota/reserve and cooldown gates;
- source and pull timestamps;
- freshness and coverage validation; and
- explicit failure without stale-data promotion.

Browser reload of already published state consumes zero provider credits.
A manual acquisition request uses the same Market Service budget and gates as
scheduled acquisition; it receives no alternate reserve or bypass.

## 4. CFBD Tier 1 budget architecture

CFBD has a separate calendar-month provider ledger. Its budget and usage must
never be combined with The Odds API credits.

The Postgame Service architecture supports:

- configured Tier 1 monthly allocation/limits when available;
- requests and provider units consumed;
- endpoint-level usage history;
- successful, failed, deferred, and rejected request counts;
- remaining budget/allowance;
- retry consumption; and
- UTC calendar-month rollover history.

Current intended usage:

| Domain | Purpose |
|---|---|
| Schedule/status | Canonical schedule changes and `GAME_FINAL` evidence |
| Postgame plays | Completed-game play sequence and feature inputs |
| Drives | Completed-game drive context |
| Havoc | Completed-game havoc statistics |
| Historical preservation | Replayable raw and accepted research evidence |

The Tier 1 key is loaded only through the established protected
secret/environment pattern. No credential belongs in events, JSON contracts,
logs, documentation examples, browser code, or public artifacts.

Controlled `GAME_FINAL` polling is implemented behind a disabled activation
flag and a schedule-driven window. Activation still requires fixture validation,
runtime deployment, and a separately reviewed machine-local scheduler.

## 5. Lifecycle and provider-budget interaction

Provider services make budget decisions. The controller records the request,
decision, and execution result.

### Postgame example

```text
GAME_FINAL
    |
    v
POSTGAME_REQUESTED
    |
    v
Postgame Service / CFBD budget check
    |
    +-- APPROVED --> provider execution --> POSTGAME_READY or POSTGAME_FAILED
    |
    +-- DEFERRED --> retry-after recorded; no provider call
    |
    +-- REJECTED / QUOTA_EXCEEDED --> failure/health evidence; no provider call
```

### Market example

```text
MARKET_REFRESH_REQUESTED
    |
    v
Market Service / The Odds API budget check
    |
    +-- APPROVED --> provider execution --> MARKET_UPDATED or failure evidence
    |
    +-- DEFERRED --> retry-after recorded; no provider call
    |
    +-- REJECTED / QUOTA_EXCEEDED --> health evidence; no provider call
```

The controller may retry only when the provider decision says retry is allowed.
It cannot reinterpret `REJECTED` as `APPROVED`, spend emergency reserve, change
request scope to evade cost, or substitute another provider.

Canonical budget-interaction records are:

- `PROVIDER_TASK_REQUESTED` or the domain-specific request event;
- `PROVIDER_BUDGET_DECIDED`;
- provider execution result through the domain event or task-attempt evidence;
- a linked correlation ID, task ID, provider account identity, and calendar
  month; and
- no secret or raw authorization material.

## 6. Cost observability

Each provider service must eventually expose protected operational metrics for:

- calendar-month usage;
- daily usage within the month;
- Saturday/Sunday weekend usage;
- request count;
- successful requests;
- failed requests;
- deferred requests;
- rejected requests;
- quota-exceeded requests;
- endpoint or request-scope usage;
- estimated versus actual cost when applicable;
- remaining provider budget;
- remaining normal-operating budget;
- emergency-reserve status where applicable; and
- last successful reconciliation timestamp.

Sanitized aggregates and health state should eventually feed
`data/site/war_room_health.json`. Detailed request history, account identity,
headers, operator identity, and secrets remain protected and must not be
published.

## 7. Controller boundary

The lifecycle controller owns event ingestion, idempotency, deterministic state
reduction, task orchestration, retry requests, and recovery tracking.

It does not own formulas, projections, rating truth, rating acceptance, market
calculations, API economics, provider pricing, credit consumption, provider
approval, projection authority, ratings authority, market authority, betting
edges, UI, validation verdicts, or publication approval.

This separation is mandatory in automatic and manual modes.

## 8. Deferred implementation work

This contract does not authorize implementation. Later work must separately:

1. define provider-ledger storage and retention;
2. confirm sanitized cost-unit fields for CFBD Tier 1;
3. reconcile all current quota displays to the UTC calendar-month boundary;
4. define provider decision-event JSON Schemas;
5. measure CFBD final-detection and weekend-monitoring cadence before activation;
6. add health-contract fields and propagation audits; and
7. validate that manual actions cannot bypass provider budget decisions.
