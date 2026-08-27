# War Room Activity Contract

## Purpose and ownership

The War Room activity system is an operational projection of changes already
accepted by canonical market, ratings, projection, results, postgame, and
selected-week health owners. It does not acquire data, calculate models, select
quotes, or redefine provider health.

`scripts/war_room/build_war_room_activity.py` compares the previous accepted
snapshot with the current resolved artifacts. Runtime owns the append-only
ledger at `data/war_room/history/war_room_events.jsonl` and its rebuildable
detector state at `data/war_room/history/war_room_activity_state.json`. The
bounded browser contract is `data/site/war_room_activity.json` with schema
`war-room-activity-v1`.

The rebuildable runtime lookup
`data/war_room/history/war_room_game_activity_index.json` has schema
`war-room-game-activity-index-v1`. It is derived from the durable ledger and
canonical matchup line history; it is not a second event authority.

## Event record

Each JSONL record contains:

- `event_id`: deterministic content identity (`wre_...`)
- `event_type`, `event_version`, `event_timestamp`
- `observed_at`, `detected_at`, `created_at`
- `refresh_id`, `correlation_id`, `idempotency_key`, `cycle_id`
- `source_system`, `entity_type`, `entity_id`
- nullable `season`, `week`, `game_id`, `away_team`, `home_team`
- nullable `book`, `market`, `side`, `old_line`, `new_line`
- nullable `old_price`, `new_price`, `source`
- `significance`, `metadata`, and `payload`

Canonical timestamps remain UTC. The page converts them to America/New_York
for display. Rerunning the same transition produces the same event ID and does
not append a duplicate.

## Phase 1 event vocabulary

Market events are `MARKET_OPENED`, `BOOK_MARKET_ADDED`,
`BOOK_MARKET_REMOVED`, `SPREAD_MOVED`, and `TOTAL_MOVED`. A move requires a
resolved accepted line change; a price-only change is not a line move. The
first successful baseline does not synthesize historical openers.

Provider/model events are `RATING_UPDATED`, `MODEL_STATE_CHANGED`,
`SHADOW_SPREAD_READY`, `SHADOW_TOTAL_READY`, `PROVIDER_DEGRADED`,
`PROVIDER_RECOVERED`, and `PROVIDER_UNAVAILABLE`. Result events are
`FINAL_POSTED` and `POSTGAME_REFRESHED`.

These activity names are presentation/change-detection events and do not
replace the lifecycle-controller vocabulary in `docs/WAR_ROOM_EVENT_SCHEMA.md`.

## Durable versus public history

The durable ledger retains per-book accepted transitions for every configured
book and exchange. The public projection is a separate deterministic view; it
is not a dump of that ledger.

Routine visible market moves are limited to DraftKings, FanDuel, BetMGM,
Caesars, and Pinnacle and require an absolute accepted line change of at least
0.5 points. Price-only changes, sub-0.5 moves, and routine Novig, ProphetX, or
Kalshi repricing are absent from the public tape.

Directionally equivalent moves for one game and market are grouped over a
90-second window. A Pinnacle-leading cluster becomes a `PINNACLE_MOVE` plus a
retail `MARKET_FOLLOW`; other qualifying clusters become `MARKET_MOVE`.
Individual evidence remains in the ledger. Accepted rating events sharing a
refresh ID become one `RATINGS_UPDATED` public event. Technical
`POSTGAME_REFRESHED` events remain durable but are hidden unless a meaningful
final, Shadow, model-state, or ratings consequence is separately detected.

## Bootstrap and opener permanence

The cursor snapshot is
`data/war_room/history/war_room_activity_state.json`. Its
`opened_market_keys` permanently records each observed
`game_id|book|market`. The durable first `MARKET_OPENED` event is the permanent
activity-era per-book opener. The public projector selects the earliest such
event for `game_id|market`; Pinnacle receives a separate `PINNACLE_OPENED`
milestone only when it was not first and appeared more than 90 seconds later.

This identity does not replace canonical historical opener ownership. Existing
market-history contracts remain authoritative for opening observations before
activity-system activation.

If the ledger and cursor do not exist, the first run silently writes the
current resolved matrix as its baseline and appends zero historical events.
It cannot flood the tape with synthetic openers. Later runs compare against
the cursor while the append-only ledger preserves accepted history across
temporary disappearance and restarts.

The detector reads the resolved War Room matrix. A raw-provider omission that
canonical current-market fallback preserves therefore creates no removal,
reopen, false move, or provider-health event.

## Dedupe identity

Durable IDs hash event type, entity, and transition evidence: accepted pair
fingerprint for open/add; old pair plus refresh for removal; old/new pair
fingerprints for moves; old/new accepted timestamps for ratings; old/new model
snapshots for model state; model/value for Shadow readiness; final scores for a
final; accepted build timestamp for postgame; and prior/new status plus refresh
for provider health. Public aggregate IDs hash their type and ordered
underlying durable event IDs. A repeated no-op build appends nothing and
reproduces the same projection.

## Public projection

The public artifact contains `built_at`, `latest_refresh_id`, durable/public
event counts, a visible-only `since_last_refresh` summary, and the newest
bounded list (default 200). Public items include `display_priority` and
`underlying_event_ids`; priority supports filtering without falsifying
chronology. The static artifact and authenticated
Cloudflare live route `/war-room/live/activity` expose the same schema.

The browser filters this bounded list by the selected matrix week without a
provider request. Clicking a game event may switch to that available week,
scroll to its existing matrix row, and flash it. The ledger—not local storage
or browser state—remains authoritative.

The live route reads AUTO's activity artifact directly, returns
`Cache-Control: no-store`, uses the same exact-origin policy as the existing
live endpoints, needs no GitHub Pages update for routine changes, and makes no
provider request.

## Game-focused meaningful history

Selecting a matrix row keeps the operator on the Command Center and requests
only that canonical game through
`/war-room/live/activity?game_id=<canonical_game_id>`. The response schema is
`war-room-game-activity-v1`; it contains game identity, authoritative opener
summaries, a bounded number of curated public events, and the immediately prior
canonical game context for each selected team. The API never returns the full
JSONL ledger. The browser caches a response only for the current Activity
artifact version and invalidates that cache when the version changes.

The game tape is **meaningful War Room market history**, not complete raw line
history. It preserves the selected-week tape's public suppression and
90-second aggregation rules. Global `RATINGS_UPDATED` events are absent because
they do not have a game identity; game-level model-state, Shadow, final, and
postgame consequences remain eligible.

Opening spread and total use the earliest authoritative accepted observation
from `data/site/matchup_line_history.json`. Pinnacle uses its own earliest
accepted observation from canonical `data/odds/game_book_line_history.csv`
when available. Each opener retains line, available price, sportsbook,
timestamp, source, provenance, and whether it was an explicit provider opener
or first tracked accepted observation. The current matrix is never used as an
opener fallback. Missing authority renders `NOT TRACKED`. These observations
appear as chronological `MARKET_OPENED` and `PINNACLE_OPENED` entries in the
selected game's MARKET tape; there is no separate pinned opening-market block.

Prior-game identity is resolved only from canonical game IDs, team identity,
and kickoff ordering. For each selected team, the newest canonical kickoff
strictly before the selected game is eligible. The response includes meaningful
`FINAL_POSTED`, `MODEL_STATE_CHANGED`, `SHADOW_SPREAD_READY`, and
`SHADOW_TOTAL_READY` events plus an explicit status such as `SHADOW_READY`,
`POSTGAME_PROCESSED`, `FINAL_POSTED`, `NOT_YET_FINAL`, or `NO_PRIOR_GAME`.
Technical refresh events are not promoted into this context. If both selected
teams share the same prior game, its underlying events are rendered once.

Selected-game filters have distinct presentation contracts. `ALL` is only the
chronological curated event stream for the selected game and contains no
synthetic opener or prior-game status rows. `MARKET` adds a two-row persistent
snapshot from canonical opener summaries and the resolved current best market;
`MODEL` adds the current Standard model values and their existing component
metadata; `POSTGAME` adds current/prior canonical game status and lifecycle
context. The corresponding filtered event stream remains independently
scrollable beneath each compact snapshot. With no selected game, the existing
selected-week Activity summary and filtering behavior remains unchanged.

The static Activity payload carries only opener summaries plus its already
bounded public tape as a graceful fallback. Routine game selection uses the
AUTO live route and does not depend on MAIN or GitHub Pages publication.

## Deferred edge transitions

Phase 1 does not emit edge-threshold events. Although the matrix contains edge
values, there is not yet a separate stable canonical threshold-state contract
for transition comparison. Phase 2 should consume the existing War Room
actionability owner rather than duplicate numeric thresholds in this detector.
