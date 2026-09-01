# War Room State Model Reconciliation

_Audit date: 2026-08-24_
_Scope: architecture only; no controller, workflow, model, authority, UI, or publication changes_

## Reconciliation answer

**Yes, the current repository contains enough state primitives to define and initially drive a system lifecycle.** It already records canonical finals, postgame readiness audits, source timestamps and content changes, projection completeness and identity, Shadow readiness, current/history market states, run/stage status, quota/cooldown/lock outcomes, validation, and publication results.

**No, those primitives alone are not enough for unattended weekend operation.** The missing layer is primarily:

1. an append-only event and forecast-version contract;
2. idempotent orchestration and scoped dispatch;
3. retry/recovery policy;
4. provider/final/market transition monitoring;
5. historical replay parameterization; and
6. first real 2026 final-game acceptance.

This is more precise than saying “only orchestration is missing.” Calculations largely exist, but some critical transition evidence—especially exact final detection, immutable live first-seen/close, and forecast versions—must be persisted for orchestration to be reliable and auditable.

The governing lifecycle and event definitions are in `docs/WAR_ROOM_SYSTEM_LIFECYCLE.md`.
Canonical projection-authority policy is in
`docs/WAR_ROOM_PROJECTION_AUTHORITY.md`.
The final operational lifecycle model is
`docs/WAR_ROOM_LIFECYCLE_OPERATIONAL_MODEL.md`.

## 1. Intended architecture

The intended War Room architecture is an operational view over canonical owners:

```text
provider/source acquisition
  -> canonical domain contracts
  -> strict projection and authority owners
  -> page adapters
  -> validation
  -> allowlisted publication
```

The lifecycle layer belongs between canonical observations and scoped task dispatch. It records and reduces events; it does not become a new data or calculation authority.

The desired weekend loop is:

```text
game/market/provider observations
  -> immutable lifecycle events
  -> derived domain states
  -> scoped calls to existing builders
  -> existing authority selection
  -> affected public rebuild
  -> existing validation/publication gates
```

## 2. Current implementation

### Existing state systems

| Domain | Existing concepts | Current owner/artifact | Persistence quality |
|---|---|---|---|
| Game | scheduled, completed flag, final scores, matched/unmatched/ambiguous | CFBD schedule; `game_results_2026.{json,csv}` and audit | Latest canonical results persist; transition event/time absent |
| Postgame | no completed games, cache ready/missing, feature ready, eligible/rejected Shadow rows | postgame pull/feature/Shadow audits | Durable latest audits and week caches; no unified event sequence |
| Ratings | unavailable, rejected, initialized, baseline established, no change, updated, manual source | accepted candidates, `live_rating_change_status.json`, source status/history/movement | Strong source history; event semantics are distributed |
| Projection | `AVAILABLE`, `MISSING_COMPONENT`, `NOT_YET_ACTIVATED`, separate `DEGRADED`, resolver `UNAVAILABLE`, authorities | canonical projection contract and resolver | Versioned latest contract; no append-only per-build forecast history for all states |
| Shadow | waiting, partial, ready, missing reasons; SP+/Sagarin/O-D model identities | component predictions, projection contract, Saturday lines, audits | Historical research is strong; live current-state persistence is mostly latest-only |
| Market | `LIVE`, `BACKUP_SOURCE`, `STALE`, `MISSING`; fast venue health; first/history/movement/close fields | current market, fast matrix, line history | Quote history exists; live first/close event ownership needs locking |
| War Room maturity | `STALE`, `SHADOW_PARTIAL`, `SHADOW`, `HYBRID`, `UPDATED` | `build_war_room_market_matrix.py` | Re-derived on every build, not a controller ledger |
| Execution | pending/running/passed/failed/skipped, warnings, lock, quota/cooldown/config blocks | daily and guarded refresh status | Strong run audit, but command-centric rather than domain-event-centric |
| Publication | build, validation, parity, push success/failure | public builder, validators, `publish_site.sh`, run status | Strong fail-closed gates; no general lifecycle event vocabulary |

### Existing orchestration

There are two orchestration families:

1. `daily_market_update.sh` with `config/daily_stages.json` and profiles `full`, `openers`, `postgame`, and `market`. Runtime stage status is atomically recorded by `scripts/control/daily_run_status.py`.
2. `scripts/control/run_data_refresh.py`, which offers guarded `status`, `odds`, `ratings`, `postgame`, `pregame`, `full`, and `publish-existing` modes, plus exclusive locks, quota/cooldown gates, dry runs, validation, and explicit publication confirmation.

The fast market path adds `run_fast_market_refresh.py`, bounded fast publication, a schedule contract, credential isolation, quota reserve, freshness checks, and a targeted three-file publisher.

These are capable command runners. They do not watch domain events or reduce an immutable event stream. Some command lists duplicate the daily profile's sequencing, which is a future convergence risk; the lifecycle design should dispatch canonical stage/task owners rather than add a third command list.

### Current Shadow integration

Shadow is correctly a phase within the larger system:

- final results and closing market establish the completed-game evidence;
- postgame caches/features produce eligible team-game observations;
- entering SP+/Sagarin snapshots establish no-lookahead baselines;
- frozen model inference produces Shadow components;
- the canonical projection contract establishes named availability;
- the authority owner decides whether Standard, Shadow, or another currently permitted state is selected;
- market contracts provide opener/current comparison;
- public builders display the result.

The 2025 rehearsal in `docs/SHADOW_MODEL_LIFECYCLE_AUDIT.md` proves the artifact-level sequence but not event-driven production replay.

## 3. Documentation drift

| Drift | Evidence | Reconciliation |
|---|---|---|
| Duplicate War Room specs | Root and `docs/` specifications differ in operational detail | Root spec is richer/current for fast-market policy; consolidate later without changing runtime |
| Repository-role conflict | `PROJECT_ARCHITECTURE_2026-08-11.md` and older automation docs name `NCAAF_SITE` as publication repo | Repository rules/current publisher establish MAIN as canonical publisher and `NCAAF_SITE` as legacy |
| Daily stage inventory is stale | `docs/DAILY_AUTOMATION.md` still lists retired SGO stages and old publication language | `daily_market_update.sh` and `config/daily_stages.json` are executable evidence |
| Ratings source comments are stale | Some shell/priority text still describes five-source or Brad Powers/DRatings composite | Current ratings builder/status establish SP+ / FPI / TeamRankings / Sagarin at 25% each |
| Strict projection docs versus old audits | Older audit text describes `AVAILABLE_DEGRADED` under official IDs | Current resolver accepts `AVAILABLE` only for official IDs and separate `DEGRADED` IDs for operational estimates |
| Shadow formula metadata conflict | `config/market_shadow_production.json` retains older experimental formulas | Frozen validated artifact and canonical projection contract are current formula authority; no change made here |
| `HYBRID` ambiguity | Older docs did not distinguish strict Official formulas from a renormalized updated-source authority tier | Resolved by `docs/WAR_ROOM_PROJECTION_AUTHORITY.md`: spread 2-3 of 4 and total 2 of 3 use updated canonical weights renormalized under separate Hybrid authority |
| Authority update counter | Current matrix compares source dates with per-game completed-game watermarks | Canonical policy now requires provider-level accepted version changes; per-game freshness remains diagnostic. Production alignment is a future audited change. |
| “State machine” wording | Specs imply lifecycle; implementation derives a display label | Reserve “system lifecycle” for orthogonal persisted domains; keep matrix maturity as a derived view |
| Schedule versus installation | Fast windows exist in JSON/runbook | Machine-local scheduler installation and observed execution remain separate proof obligations |

## 4. Missing lifecycle pieces

### Required before automatic operation

- Canonical append-only event log and deterministic reducer.
- Immutable forecast versions keyed by game, model, model version, source cutoffs, and build/run ID.
- Final-game watcher/poller that emits one idempotent `GAME_FINAL`.
- Bounded late-PBP retry and failure escalation.
- Provider candidate fingerprint monitoring connected to affected games.
- Immutable live `MARKET_FIRST_SEEN` and explicit `MARKET_CLOSE` semantics.
- Scoped dependency dispatch rather than whole-profile reruns for every event.
- Crash/restart recovery from the event log.
- Parameterized replay to an isolated output root.
- First real 2026 final-game acceptance.

### Useful but not controller prerequisites

- Additional browser/end-to-end latency telemetry.
- Cadence tuning from passive fast-market history.
- Operator dashboards for event inspection.
- Longer-term lifecycle archival/compaction policy.

## 5. Recommended future controller design

### Shape

A thin controller should have four responsibilities:

1. **Ingest event facts** emitted by canonical owners.
2. **Reduce facts into domain states** deterministically and replayably.
3. **Dispatch idempotent scoped tasks** based on unmet dependencies.
4. **Record outcomes/retries** and request existing build/validation/publication paths.

Suggested contracts:

- `lifecycle_events.jsonl`: immutable append-only facts.
- `lifecycle_state.json`: rebuildable current state indexed by game/source/domain.
- `forecast_versions.jsonl`: immutable canonical model/version/input-cutoff snapshots.
- `lifecycle_attempts.jsonl`: task attempt, lock, retry, and terminal outcome evidence.

These names are proposals, not implementation commitments. Schema and retention review must precede file creation.

### Reducer boundaries

The reducer may answer:

- Has this final already been processed?
- Which postgame prerequisites remain?
- Which next games are affected by a completed team-game?
- Which source panels changed since the completed-game watermark?
- Which canonical projection/authority event was most recently emitted?
- Has the market appeared or moved since that forecast version?
- Is a rebuild requested, running, failed, retryable, validated, or published?

It must not answer:

- What is the fair spread/total?
- Which provider should win source selection?
- Which model formula or weights apply?
- Whether a degraded model should be relabeled official?
- What the page should display beyond passing canonical fields/statuses.

### Idempotency and concurrency

- Stable event key: event type + canonical entity + source version/fingerprint.
- Stable task key: task type + affected entity + input event version.
- One active attempt per task key.
- Atomic state replacement after reducer completion.
- Append attempt outcome before retry.
- Preserve existing provider locks, quota reserves, cooldowns, and publisher dirty-tree/parity gates.

## 6. Automatic and manual modes

### Automatic weekend mode

```text
controlled CFBD status poll
  -> GAME_FINAL
  -> scoped postgame work
  -> POSTGAME_READY
  -> scoped Shadow work
  -> SHADOW_READY/PARTIAL

controlled ratings polls
  -> RATING_SOURCE_CHECKED/UPDATED/REJECTED
  -> affected official projections
  -> OFFICIAL_PROJECTION_READY

controlled daily/fast market pulls
  -> MARKET_FIRST_SEEN / MARKET_QUOTE_ACCEPTED / MARKET_CLOSE
  -> comparison/adapters

relevant state change
  -> public build
  -> validation/parity
  -> allowlisted publication
```

Cadence must be policy-driven by game windows, provider-release behavior, quota, cooldown, and overlap rules. The lifecycle controller requests work; existing acquisition gates retain veto authority.

### Manual operator mode

The operator should use the same event/task system to force a bounded poll, retry one failed task, replay to a temporary root, rebuild derived state, run validation-only, or explicitly publish. Manual mode must remain credential-safe and cannot bypass input, quota, authority, validation, or publication rules.

## 7. What the controller must not own

- Standard or Shadow formulas, weights, coefficients, HFA, or signs.
- Team rating composite formula.
- Official/degraded model identity or resolver policy.
- Provider source priority and accepted-quote logic.
- Market edge calculations.
- Betting signals.
- War Room layout or page labels.
- Public artifact schema transformation.
- Validation verdicts.
- Git staging scope, commit policy, or publication authority.

## Recommended implementation order

1. Define the remaining authority-cycle boundary/baseline and source correction/retraction policy; threshold and Hybrid rules are now locked.
2. Audit/align the existing authority owner with provider-level global counts,
   independent spread/total thresholds, and separate Hybrid identity.
3. Complete the first real 2026 final-game acceptance using existing scripts.
4. Define event, forecast-version, reducer-state, and attempt schemas.
5. Parameterize an isolated historical replay and prove deterministic reduction.
6. Add event emitters to owners without changing their calculations.
7. Implement the reducer in observe-only/shadow mode; compare its derived state with current artifacts.
8. Add idempotent scoped task dispatch and retry policy, initially with publication disabled.
9. Dual-run against existing full/postgame/pregame paths and reconcile every transition.
10. Connect existing validation/publication gates only after parity, then install/audit controlled weekend scheduling while preserving manual override.

## Final status

| Question | Answer |
|---|---|
| Are enough state primitives present? | **Yes**, for a first version of the lifecycle contract and reducer. |
| Is orchestration the primary missing layer? | **Yes**, together with durable event/forecast version persistence required to make orchestration auditable. |
| Is a new formula/authority owner needed? | **No.** |
| Is a persisted controller needed for the desired unattended weekend operation? | **Yes**, after lifecycle contracts and first-final acceptance. |
| Should it be implemented now? | **No.** Resolve the listed gates first. |
