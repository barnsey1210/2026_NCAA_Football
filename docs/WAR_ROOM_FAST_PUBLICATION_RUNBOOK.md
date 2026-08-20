# War Room Fast Publication Runbook

## Data flow

1. `run_fast_market_refresh.py` acquires and normalizes the fast The Odds API
   spread/total feed, then rebuilds health and market matrix.
2. `run_fast_market_publication.py` rebuilds `war-room.html` and creates
   `build/war_room_public` containing exactly three public files.
3. `audit_war_room_fast_publication.py` requires matching refresh IDs and pull
   timestamps, V1 schemas, nonempty matched coverage, and a pull no older than
   15 minutes.
4. `publish_site.sh --war-room-push` synchronizes and commits only those three
   files to canonical `main`, which triggers the existing GitHub Pages publish.

The full public build is not used because it can contain older copies of other
page payloads. Home is not rebuilt.

## Page-consumer boundary

- Command Center consumes the fast health and matrix artifacts.
- Openers consumes `matchups_view.json`, `current_market_contract.json`, Shadow,
  and schedule enrichment.
- Odds consumes `odds_screen_v2.json` and `odds_futures_v2.json`.
- Matchups and individual matchup pages consume `matchups_view.json`.
- Futures consumes `futures_view.json`.

Those pages do not consume the fast War Room artifacts. They remain current
through the canonical `market`, `openers`, or `full` pipeline profiles. Fast
quotes must not overwrite their canonical inputs without a separate parity-
tested normalization decision.

## Operating windows

The repository schedule contract is `config/war_room_fast_schedule.json`:

- Saturday 11:00 PM ET
- Sunday 9:00 AM ET
- Sunday 2:00 PM ET
- Sunday 9:00 PM ET

Install these as machine-local, non-overlapping scheduler entries in a separate
deployment step. Each entry must load only `THE_ODDS_API_KEY_FAST`, change to
`/Users/jameslindesmith/NCAAF_AUTO`, and execute:

```bash
python3 scripts/war_room/run_fast_market_publication.py --push
```

The existing daily 8 AM LaunchAgent remains unchanged.

## GitHub workflow change required

The manual refresh workflow is owned by `NCAAF_CONTROL`, not MAIN_REPO. Add a
separately reviewed `war-room-fast` dispatch option there. Its self-hosted step
must delegate to the same runtime command above; it must not duplicate provider,
builder, validator, or publisher commands in workflow YAML. Require an explicit
push input, keep concurrency non-cancelling, and retain the controller audit.

## Failure policy

- Missing fast credential: stop before acquisition.
- Quota at/below reserve or unavailable: stop before acquisition.
- Provider, builder, or validator failure: do not publish.
- Mismatched refresh IDs/timestamps or artifact age over 15 minutes: do not
  publish.
- Dirty tracked MAIN_REPO worktree: do not publish.
- Git synchronization or push failure: exit nonzero; do not broaden the staged
  pathspec and never use `git add .`.
