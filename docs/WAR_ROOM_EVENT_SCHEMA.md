# War Room Event Schema

_Canonical append-only lifecycle event contract: 2026-08-24_

_Status: architecture/schema only; no production controller is authorized_

## Purpose and authority

This document defines the canonical event language for a future War Room
lifecycle controller. It governs immutable event envelopes, domain payloads,
ownership, entity scope, idempotency, ordering, replay, correction, and task
attempt evidence.

It complements:

- `docs/WAR_ROOM_LIFECYCLE_OPERATIONAL_MODEL.md`;
- `docs/WAR_ROOM_SYSTEM_LIFECYCLE.md`;
- `docs/WAR_ROOM_PROJECTION_AUTHORITY.md`; and
- `docs/WAR_ROOM_DATA_ARCHITECTURE.md`.

Provider service ownership, API economics, and calendar-month budget policy are
owned by `docs/WAR_ROOM_PROVIDER_SERVICES_AND_API_BUDGETS.md`.

If a lifecycle implementation disagrees with this contract, the implementation
must fail validation rather than silently reinterpret an event.

## 1. Ownership model

The lifecycle controller owns:

- event ingestion and schema validation;
- idempotency and append-only persistence;
- deterministic ordering and state reduction;
- task-request orchestration;
- task-attempt, retry, and recovery tracking; and
- rebuildable lifecycle-state projections.

The lifecycle controller does **not** own:

- formulas, weights, HFA, projection calculations, or forecast values;
- projection-authority calculations or provider-count thresholds;
- provider truth, candidate acceptance, or source validation;
- market normalization, source selection, consensus, price, or edge calculations;
- UI labels, layout, or rendering; or
- validation verdicts or publication approval.

Domain owners create facts. The controller records those facts and requests
work from reviewed task owners. It never manufactures a successful source,
forecast, authority, market, validation, or publication result.

### Event ownership matrix

All canonical events are persisted. Current state and presentation labels are
derived from them.

| Event | Creator and data owner | Primary consumers | May request downstream work |
|---|---|---|:---:|
| `GAME_FINAL` | Canonical results owner using accepted CFBD Tier 2 evidence | Controller, postgame pipeline, settlement | Yes |
| `POSTGAME_REQUESTED` | Controller after accepted final | Postgame task owner, audit/status views | Yes |
| `POSTGAME_READY` | Postgame owner after required cache/feature audits | Controller, Shadow owner | Yes |
| `POSTGAME_FAILED` | Postgame task owner/orchestrator from an actual failed attempt | Controller, retry policy, operator health | Yes |
| `SHADOW_PARTIAL` | Shadow projection owner | Controller, diagnostics, War Room adapter | Yes, but never grants authority itself |
| `SHADOW_READY` | Canonical projection owner after strict Shadow validation | Authority owner, market comparison, War Room adapter | Yes |
| `MARKET_FIRST_SEEN` | Canonical market/history owner | Controller, projection comparison, history | Yes |
| `MARKET_UPDATED` | Canonical or fast market owner after quote acceptance | Controller, history, War Room adapter | Yes |
| `PROVIDER_PANEL_CHANGED` | Provider acceptance owner | Projection and authority owners, controller | Yes |
| `PROVIDER_PANEL_REJECTED` | Provider validation/acceptance owner | Controller, health/audit views | No projection rebuild |
| `PROVIDER_PANEL_CORRECTED` | Provider acceptance owner | Projection and authority owners, controller | Yes |
| `AUTHORITY_CHANGED` | Existing projection-authority owner | Controller, adapters, market comparison | Yes |
| `BUILD_REQUESTED` | Controller from an accepted state change | Existing canonical build owner | Yes |
| `BUILD_COMPLETED` | Existing build owner | Controller, validators | Yes |
| `VALIDATION_COMPLETED` | Existing validators | Controller, publication gate, operator health | Yes only when verdict permits review |
| `PUBLICATION_REQUESTED` | Controller or authorized operator after validation | Existing publisher/approval owner | Yes; request is not approval |
| `PUBLICATION_COMPLETED` | Existing publisher after an actual release attempt | Controller, release audit, operator health | No |
| `MARKET_REFRESH_REQUESTED` | Controller or authorized operator | Market Service | Yes, subject to provider budget decision |
| `PROVIDER_BUDGET_DECIDED` | Market, Postgame, or other approved provider service | Controller, task owner, operator health | Yes only when `decision = APPROVED` |

An event creator owns the truth expressed in its payload. The controller owns
only ingestion, chronology, reduction, and task consequences.

## 2. Canonical envelope

Every event uses this envelope:

```json
{
  "event_id": "evt_01J6...",
  "event_type": "GAME_FINAL",
  "event_version": 1,
  "created_at": "2026-09-05T20:00:02.184Z",
  "observed_at": "2026-09-05T20:00:01.742Z",
  "source_system": "canonical_results",
  "entity_type": "game",
  "entity_id": "g12",
  "cycle_id": "2026_WK2_PREP",
  "payload": {},
  "correlation_id": "run_20260905T200000Z_abc123",
  "idempotency_key": "GAME_FINAL:g12:cfbd-version-or-fingerprint"
}
```

### Required common fields

| Field | Type | Rule |
|---|---|---|
| `event_id` | string | Globally unique immutable event identity |
| `event_type` | enum string | One canonical type defined in this document |
| `event_version` | positive integer | Payload schema version for this event type; starts at `1` |
| `created_at` | timestamp | Time the authoritative event record was created |
| `observed_at` | timestamp | Time the source fact was first observed by the creating owner |
| `source_system` | string | Reviewed producer identity, never a secret or free-form credential context |
| `entity_type` | enum string | `game`, `week_cycle`, `provider_panel`, `market`, or `system` |
| `entity_id` | string | Stable identity within `entity_type` |
| `cycle_id` | string | Preparation-cycle identity; required even for global events linked to a cycle |
| `payload` | object | Versioned event-specific data; secrets prohibited |
| `correlation_id` | string | Groups one source observation, task chain, build, or operator request |
| `idempotency_key` | string | Stable semantic-deduplication identity defined by the event owner |

Unknown top-level fields must be rejected until the envelope versioning policy
explicitly permits them. Optional domain data belongs inside `payload`.

### Timestamp rules

1. Timestamps use RFC 3339 UTC with a `Z` suffix and millisecond or finer
   precision when available.
2. `observed_at` records when the producer first saw the fact. `created_at`
   records when it committed the event; therefore `created_at` must not precede
   `observed_at`.
3. Source-published, game-status, quote, provider-panel, task-start/completion,
   build, validation, and publication timestamps remain distinct payload fields.
4. Missing source time is `null` with an explicit reason. Build time must never
   substitute for source time.
5. Event ordering uses `(observed_at, created_at, event_id)` for reduction after
   schema validation. Arrival order is not authoritative.
6. Clock corrections create new evidence; persisted timestamps are never
   rewritten in place.

## 3. Entity scope

| Scope | `entity_type` | Identity example | Typical events |
|---|---|---|---|
| Game | `game` | `g12` | `GAME_FINAL`, postgame and Shadow events |
| Week preparation cycle | `week_cycle` | `2026_WK2_PREP` | Cycle-scoped build/task coordination |
| Provider panel/version | `provider_panel` | `SP+:2026:sp-v3` | Provider changed/rejected/corrected |
| Game market | `market` | `g102:spread` | First seen and updated market events |
| System/build/release | `system` | `war-room-fast-build:run-id` | Build, validation, publication events |

`AUTHORITY_CHANGED` uses `entity_type = week_cycle`. Its `entity_id` identifies
the authority domain inside the cycle, for example
`2026_WK2_PREP:spread`. Affected game IDs belong in the payload.

Provider events are global source facts but must name every preparation cycle
against whose frozen baseline the accepted version is being evaluated. One
provider observation may therefore produce separately idempotent cycle-linked
consequences without duplicating the accepted provider version itself.

## 4. Canonical event payloads

Fields listed below are required unless explicitly marked optional. IDs and
fingerprints refer to persisted artifacts or versions, never credentials.

### `GAME_FINAL`

- Entity: `game`.
- Payload: `season`, `week`, `game_id`, `away_team_id`, `home_team_id`,
  `away_score`, `home_score`, `kickoff_at`, `source_status`,
  `source_final_at` (nullable with reason), `source_version`,
  `result_artifact`, `result_fingerprint`, and mapping-validation result.
- Idempotency: game ID plus accepted source result version/fingerprint.
- Consequence: first canonical final opens the next preparation cycle and may
  request postgame work.

### `POSTGAME_REQUESTED`

- Entity: `game`.
- Payload: `game_id`, `task_id`, required inputs, requested endpoint/data classes,
  triggering `GAME_FINAL` event ID, attempt policy, and task-owner identity.
- Consequence: dispatches only the reviewed postgame task owner.

### `POSTGAME_READY`

- Entity: `game`.
- Payload: `game_id`, `task_id`, CFBD source/cache versions for plays, drives,
  havoc, and advanced game statistics; feature artifact versions; information
  cutoff; audit results; row counts; and completion time.
- Consequence: may request affected-team and next-game Shadow work.

### `POSTGAME_FAILED`

- Entity: `game`.
- Payload: `game_id`, `task_id`, `attempt_id`, failed step, normalized reason,
  `retryable`, attempt number, available/missing inputs, and next permitted
  retry time if any.
- Consequence: records failure and invokes bounded retry policy or operator
  escalation. It never marks postgame ready.

### `SHADOW_PARTIAL`

- Entity: target `game`.
- Payload: model IDs/versions, available and missing components, ready/missing
  teams, source/input versions, information cutoff, optional partial values,
  and projection artifact fingerprint.
- Consequence: diagnostic rebuild only. It does not grant Shadow authority.

### `SHADOW_READY`

- Entity: target `game`.
- Payload: complete Shadow model IDs/versions, values with explicit home-margin/
  line sign fields, component versions, source timestamps, information cutoff,
  strict validation status, and forecast fingerprint.
- Consequence: informs the authority owner and market comparison. The event
  carries projection output calculated elsewhere.

### `MARKET_FIRST_SEEN`

- Entity: `market`, one game and market domain.
- Payload: game ID, market type, accepted book/consensus semantics, first quote
  set, source/provider timestamps, observed timestamp, pull/run ID, freshness,
  market artifact, and quote fingerprint.
- Idempotency: immutable first accepted observation under the versioned first-
  seen rule.
- Consequence: compare with the currently selected authority value, including
  explicitly labeled stale or carry-forward values.

### `MARKET_UPDATED`

- Entity: `market`.
- Payload: game ID, market type, book, side, line, price, prior/new quote
  fingerprints, source/provider timestamps, freshness, and accepted market
  artifact version.
- Consequence: append history and request affected comparison/view rebuild.
  Market calculations remain with the market owner.

### `MARKET_REFRESH_REQUESTED`

- Entity: `system` or requested market scope.
- Payload: provider service, task/request ID, market scope, reason, requester,
  requested time, calendar month, estimated cost if supplied by the Market
  Service, and correlation ID.
- Consequence: asks the Market Service for a budget/execution decision. The
  request itself never calls the provider and never implies approval.

### `PROVIDER_BUDGET_DECIDED`

- Entity: provider account/budget period without secret material.
- Payload: provider service, linked task/request ID, UTC calendar month,
  decision (`APPROVED`, `DEFERRED`, `REJECTED`, or `QUOTA_EXCEEDED`), reason,
  retry-after when applicable, monthly allocation, consumed/remaining units,
  protected reserve and remaining normal-operating units when applicable,
  estimated cost, decision timestamp, and budget-state fingerprint.
- Consequence: only `APPROVED` permits the reviewed provider task to execute.
  The controller records and follows the decision but does not calculate it.

### `PROVIDER_PANEL_CHANGED`

- Entity: `provider_panel`.
- Payload: provider, season, prior accepted version, new accepted version,
  source/pull/acceptance timestamps, validation result, content fingerprint,
  coverage, and changed entities/fields when available.
- Consequence: request affected canonical projection and authority-owner work.

### `PROVIDER_PANEL_REJECTED`

- Entity: `provider_panel` candidate.
- Payload: provider, candidate version/fingerprint, observation/source times,
  validation failures, retained accepted version, and rejection artifact.
- Consequence: persist rejection and health evidence. Do not replace the
  accepted version or request projection promotion.

### `PROVIDER_PANEL_CORRECTED`

- Entity: new `provider_panel` version.
- Payload: all accepted-change fields plus `corrects_version`, correction
  reason, and new immutable version/fingerprint.
- Consequence: request affected projection and authority-owner work. It does
  not mutate or remove the corrected version.

### `AUTHORITY_CHANGED`

- Entity: `week_cycle`, with domain identity such as
  `2026_WK2_PREP:spread` or `2026_WK2_PREP:total`.
- Payload: domain, prior/new authority, selected model ID/version, selected
  forecast version, value state, updated provider versions, updated/required
  source counts, Hybrid weights when supplied by the authority owner, affected
  games, reason, and input event IDs.
- Consequence: persist the authority owner's decision and request affected
  comparison/adaptor/build work.
- Prohibition: the controller must not count providers, apply thresholds,
  renormalize weights, or calculate the selected value.

### `BUILD_REQUESTED`

- Entity: `system` or `week_cycle`.
- Payload: task ID, build profile/type, affected games/contracts, triggering
  event IDs, expected allowlisted outputs, and reviewed build-owner identity.
- Consequence: dispatch the existing builder only.

### `BUILD_COMPLETED`

- Entity: `system` build identity.
- Payload: task/attempt/build IDs, source commit, start/end times, output
  manifest, artifact hashes, warnings, and build-owner result.
- Consequence: request validation. Completion is not a validation verdict.

### `VALIDATION_COMPLETED`

- Entity: `system` build identity.
- Payload: build ID, verdict (`PASSED` or `FAILED`), validator versions, gates,
  failures/warnings, validated manifest, artifact hashes, and completion time.
- Consequence: a passing verdict may request publication review; failure blocks
  publication and remains recorded.

### `PUBLICATION_REQUESTED`

- Entity: `system` release identity.
- Payload: build/validation IDs, validated artifact manifest, hashes, target,
  requester identity, request reason, and required approval policy.
- Consequence: enters the existing publication-approval boundary. It is not an
  approval and cannot bypass publisher gates.

### `PUBLICATION_COMPLETED`

- Entity: `system` release identity.
- Payload: request/build/validation IDs, publisher run ID, published manifest,
  artifact hashes, commit/release identity, start/end times, and result. Failed
  publication attempts remain persisted task-attempt failures and do not emit
  `PUBLICATION_COMPLETED`. A distinct failure event requires a later schema
  version and approval.
- Consequence: update release audit/state only.

## 5. Provider version invariants

1. Accepted provider versions never disappear and are never rewritten.
2. A correction creates `PROVIDER_PANEL_CORRECTED` with a new version identity
   and an explicit link to the corrected version.
3. Rejected candidates remain in history through
   `PROVIDER_PANEL_REJECTED`; they never replace the last accepted version.
4. Accepted-no-change checks may remain source-owner audit records; they do not
   require a canonical changed event or projection rebuild.
5. Provider version identity is separate from projection model identity,
   forecast version identity, and authority identity.
6. One accepted version may affect spread, total, or both, but the authority
   owner determines and emits each domain transition independently.

## 6. Authority transition recording

The locked authority thresholds are:

| Domain | Updated sources | Authority |
|---|---:|---|
| Spread | 0–1 of 5 | `SHADOW` |
| Spread | 2–3 of 4 | `HYBRID` |
| Spread | 4 of 4 | `OFFICIAL` |
| Total | 0–1 of 3 | `SHADOW` |
| Total | 2 of 3 | `HYBRID` |
| Total | 3 of 3 | `OFFICIAL` |

`AUTHORITY_CHANGED` records a decision already made by the existing authority
owner. The lifecycle controller does not calculate why it changed. Spread and
total transitions are independent events and may occur at different times.

Authority state and value state are also independent. `CURRENT`, `STALE`,
`CARRY_FORWARD`, and `UNAVAILABLE` must remain explicit. Carry-forward is
permitted only for the same model/forecast identity under the locked lifecycle
policy; another model or authority must never be silently substituted.

## 7. Persisted and derived state

### Persisted facts

- immutable canonical events;
- raw and accepted provider versions and rejected candidates;
- forecast versions, inputs, model identities, signs, and information cutoffs;
- task requests, attempts, failures, retries, and completions;
- market first/history/close evidence under their domain contracts; and
- build, validation, and publication attempts/results.

### Derived and rebuildable projections

- current game, preparation-cycle, provider, projection, market, execution,
  and publication lifecycle state;
- current displayed authority and selected forecast reference;
- War Room maturity labels;
- freshness, stale, and carry-forward labels; and
- task queues reconstructed from events and completion evidence.

Derived state may be replaced atomically after replay. Persisted events and
accepted source/forecast versions may not be rewritten to repair derived state.

## 8. Idempotency, replay, ordering, and recovery

### Duplicate handling

- `event_id` duplicates are ignored after byte/semantic equality validation.
- Reuse of an `event_id` with different content is corruption and must fail.
- Different event IDs with the same `idempotency_key` reduce once. The later
  duplicate remains auditable but cannot duplicate tasks or state transitions.

### Deterministic replay

- The same validated event set, schema versions, reducer version, and task
  registry must produce the same state and task identities.
- Reducers start from an empty derived state. Hidden mutable state is forbidden.
- State snapshots are accelerators only and must be verifiable against the
  event range and reducer hash.

### Out-of-order events

- Arrival order does not determine lifecycle order.
- Events reduce by the timestamp rule in this document, with domain dependency
  validation.
- A late prerequisite may complete a pending transition. It must not rewrite
  previously persisted facts.
- Impossible causal order is quarantined for review rather than silently
  reordered into a successful state.

### Retry and correction

- Every task attempt has a stable task identity and unique attempt identity.
- Retry records link to the failed attempt, carry retryability/reason evidence,
  and invoke only the same reviewed task owner.
- Equivalent duplicate triggers cannot start duplicate concurrent attempts.
- Provider correction uses a new provider version event, not a retry or mutation.
- Publication retry never bypasses validation, allowlist, lock, parity, or
  approval gates.
- Provider-task retry never bypasses `PROVIDER_BUDGET_DECIDED`; a deferred or
  rejected request causes no provider call.

## 9. Relationship to the isolated rehearsal

The offline framework under
`scripts/war_room/lifecycle_simulation/` validates the same envelope concepts:
event identity/type, timestamp, cycle/entity identity, payload, source,
idempotency, deterministic replay, task requests, retries, provider versions,
independent authority transitions, and stale/carry-forward value states.

The current simulation uses compact prototype field names (`timestamp` and
`source`) and several prototype event names. Canonical compatibility mapping is:

| Simulation prototype | Canonical event |
|---|---|
| `RATING_SOURCE_UPDATED` | `PROVIDER_PANEL_CHANGED` |
| correction-shaped `PROVIDER_PANEL_CHANGED` | `PROVIDER_PANEL_CORRECTED` |
| `RATING_SOURCE_REJECTED` | `PROVIDER_PANEL_REJECTED` |
| `MARKET_QUOTE_ACCEPTED` | `MARKET_UPDATED` |
| `TASK_FAILED` / `TASK_RETRY` / `TASK_COMPLETED` | attempt evidence associated with the requested domain task |
| `VALIDATION_PASSED` | `VALIDATION_COMPLETED` with `verdict = PASSED` |

Before production integration, an isolated schema adapter/test update must move
the prototype envelope to `event_version`, `created_at`, `observed_at`,
`source_system`, `entity_type`, `correlation_id`, and `idempotency_key`. That is
not a production behavior change and is not implemented by this document.

Numeric projections in the rehearsal remain explicit fixtures supplied by a
projection-owner fixture. The reducer does not calculate projections,
authority, markets, or edges. No simulation event authorizes production build,
publication, scheduler, workflow, or API behavior.

## 10. Remaining architecture questions

The event language is locked. The following implementation details remain for
a later, separately authorized schema phase:

1. physical ledger/storage technology, retention, partitioning, and backup;
2. canonical event-ID and correlation-ID generation format;
3. the registry and migration policy for `event_version` evolution;
4. exact idempotency-key recipes for each concrete source adapter;
5. causal-dependency quarantine and late-event remediation mechanics;
6. whether publication failure receives a distinct `PUBLICATION_FAILED` event
   in schema version 2 or remains task-attempt evidence only;
7. task-attempt sub-schema and retry backoff limits; and
8. formal machine-readable JSON Schema generation and validation tooling.

None of these questions reopens formulas, provider authority, projection
authority thresholds, market calculations, UI ownership, or publication
approval boundaries.
