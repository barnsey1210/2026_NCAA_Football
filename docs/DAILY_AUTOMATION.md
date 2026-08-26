# Daily automation architecture and runbook

> The canonical repository/runtime boundary and the relationship between this
> full daily backbone and bounded fast paths are defined in
> `docs/NCAAF_RUNTIME_UPDATE_ARCHITECTURE.md`.

_Audited 2026-08-01_

## Canonical execution path

The production path has two layers and only one business-logic entry point:

1. `$HOME/Scripts/NCAAF/daily_market_update.sh` is a thin machine-local launcher. It sources `$HOME/.config/ncaaf/daily.env`, then replaces itself with `/bin/bash /Users/jameslindesmith/NCAAF_AUTO/daily_market_update.sh`. It contains no provider, ratings, email, site-build, or publication logic.
2. `daily_market_update.sh`, owned by this repository and deployed to `NCAAF_AUTO`, is the only production orchestration implementation.

The LaunchAgent schedules the thin launcher. Neither layer pulls source from Git or deploys code. Source deployment remains the separate manual `deploy/deploy_to_auto.sh` boundary.

## Fast Ratings monitor

`com.jim.ncaaf.fast-ratings` wakes every 1,800 seconds. Its deployed wrapper
evaluates `America/New_York` locally and dispatches the existing bounded Ratings
service only from Sunday 00:00 through Monday 12:00, inclusive. All other wakes
record `OUTSIDE_RATINGS_WINDOW` and make zero provider contacts. The monitor is
additive: it does not change the 8 AM backbone, and manual Command Center
Refresh Ratings remains available at any time.

Automatic and manual Ratings requests both enter
`scripts/control/run_war_room_service.py ratings`. Provider acceptance,
version-change detection, projection rebuilding, and Hybrid/Official authority
remain with their existing owners. The shared canonical-writer lock protects
Ratings from Postgame and other writers; an active daily run produces
`DEFERRED_BY_DAILY_BACKBONE` for retry at the next scheduler wake.

## Stage registry and run status

`config/daily_stages.json` is the machine-readable stage registry. It records order, required/optional policy, network usage, and email/publication dependencies without duplicating the business commands from `daily_market_update.sh`.

Every run atomically updates runtime-only `data/control/daily_run_status.json` through `scripts/control/daily_run_status.py`. The report includes the run ID, timestamps, deployed source commit, stage outcomes, warnings, email build/send state, validation, publication, and overall result. It never includes environment-variable values.

## Current stage inventory

| Order | Stage | Principal commands | Policy | Network | Email | Publication | Inputs and outputs / fallback |
|---:|---|---|---|:---:|:---:|:---:|---|
| 10 | Futures market acquisition | Action Network win totals; visible DK pull/merge; FanDuel totals; BettingPros Caesars totals; Action Network conference futures; history, movement, arbitrage | Required group; explicitly marked provider substeps may warn | Yes | Yes | Yes | Provider responses and cached market files -> futures histories/reports. Optional provider failures preserve cached data. |
| 20 | Game market acquisition | CFBD lines; Action Network lines/build; season-line build; The Odds API pull/build | Optional | Yes | Yes | Yes | Provider lines -> normalized season lines. Individual failures warn. |
| 30 | SGO pull | `scripts/markets/pull_sgo_ncaaf_game_odds.py` | Optional | Yes | Yes | Yes | SGO API -> private raw response; failure preserves prior SGO/fallback data. |
| 40 | SGO normalization | canonical daily builder; compatibility export; SGO book history | Optional | No | Yes | Yes | Raw SGO response -> accepted/preview compatibility artifacts and history. Explicitly skipped if raw response is absent. |
| 50 | Game-line history | append normalized history; movement report | Optional | No | Yes | Yes | Current normalized lines -> daily history and movement. Failures warn. |
| 60 | Injuries and signals | CFBDepth injuries/articles; injury alerts; daily angles; game-line edges | Required group | Yes | Yes | Yes | Injury/provider and market inputs -> alerts and `daily_betting_angles.csv`. Optional injury pulls warn; core angle build remains fail-fast. |
| 70 | Email build | prepend moves/injuries; clean moves; build HTML | Required | No | Yes | No | Daily angles -> canonical HTML email. Supplemental failures warn; HTML build is fail-fast. |
| 80 | Email regression | `scripts/audit/test_daily_betting_email_regression.py` | Required | No | Yes | No | CSV + HTML -> regression verdict. Must pass before sending. |
| 90 | Injury scores | game injury-score builder | Optional | No | No | Yes | Alerts -> game injury scores; failure warns. |
| 100 | Ratings refresh | Sagarin, Massey, Donchess acquisition/parsing | Optional | Yes | No | Yes | Provider/source inputs -> refreshed source ratings. Failures warn. SP+, FPI, and TeamRankings acquisition remains provenance-gated. |
| 110 | Ratings normalization | latest ratings, history append, movement | Optional | No | No | Yes | Rating source files -> canonical current/history/movement files. Failures warn. |
| 120 | Projections | source projections and blended projections | Optional | No | No | Yes | Canonical ratings/schedule -> projection sources and blend. Runs after ratings. |
| 130 | Matchup core | canonical matchup view builder | Required | No | No | Yes | Schedule, projections, markets -> V2 matchup payload. |
| 140 | Line-history assets | clean history builder; asset-only injection | Required | No | No | Yes | Canonical market history -> shared Odds/matchup history JSON. No V1 shell injection. |
| 150 | Shadow models | market ratings; ratings view; frozen Shadow features/components/lines; schedule enrichment; audits | Required | No | No | Yes | Completed-game and canonical market/rating inputs -> Openers/Schedule Shadow data and audits. No refit. |
| 160 | Playoff futures | Action Network playoff pull; Futures V2 build | Optional | Yes | No | Yes | Provider/cached futures -> Futures V2 payload. Network/pull failures preserve cached data and warn. |
| 170 | Odds payloads | Odds games and futures V2 builders | Optional | No | No | Yes | Canonical game/futures markets -> Odds V2 JSON. Failed builders retain last valid artifacts. |
| 180 | Email send | Gmail sender | Optional | Yes | Yes | No | Built and regression-tested email -> SMTP delivery. `NCAAF_SEND_EMAIL=0` skips sending only. Missing credentials or send failure is explicit and does not corrupt completed outputs. |
| 190 | Site build | canonical V2 public-site builder | Required | No | No | Yes | Canonical V2 inputs -> `build/public_site`. Runs even when publication is disabled. |
| 200 | Site validation | V2 index audits and public-site check | Required | No | No | Yes | Built bundle -> validation verdict. Must pass before publication. |
| 210 | Publication | staged publisher with `--push` | Required when enabled; otherwise explicit skip | Yes | No | Yes | Validated bundle -> `NCAAF_SITE`. `NCAAF_AUTO_PUBLISH=0` skips only publication. Publisher failure stops the workflow; invalid assets are never promoted. |

## Failure behavior

- A required command exits the workflow and the active stage is recorded as `FAILED`.
- An explicitly optional provider or derived-artifact step emits and records a warning while preserving known-valid cached output where stated.
- Email generation and regression are required even when sending is disabled. Email delivery failure is recorded, but does not rewrite earlier outputs.
- Site build and validation are required even when publication is disabled. Publication cannot run before both pass.
- The status writer records `PASSED`, `PASSED_WITH_WARNINGS`, or `FAILED`; skipped email/publication gates remain explicit.

## Environment variables

The orchestration directly evaluates:

- `HOME` — runtime and log locations.
- `NCAAF_SEND_EMAIL` — `0` disables send only; default preserves current enabled behavior.
- `NCAAF_GMAIL_USER`, `NCAAF_GMAIL_APP_PASSWORD`, `NCAAF_EMAIL_TO` — required only at send time.
- `NCAAF_AUTO_PUBLISH` — `0` disables publication only; default preserves current enabled behavior.

Provider scripts consume their own protected API environment variables from the launcher-loaded private environment, including configured credentials for SportsGameOdds, BettingPros, CFBD, The Odds API, and other active providers. Values must never enter logs or `daily_run_status.json`.

### Approved CFBD production role

Canonical service ownership and budget policy are defined in
`docs/WAR_ROOM_PROVIDER_SERVICES_AND_API_BUDGETS.md`.

CFBD Tier 2 is approved for production. It owns acquisition of schedule/status
and `GAME_FINAL` evidence, plus postgame plays, drives, havoc, and advanced game
statistics. Raw and accepted historical responses should be preserved for
replay and future research. CFBD does not own projection authority, ratings
authority, market authority, or betting-edge calculations.

The Tier 2 key will be wired later through the existing protected
secret/environment pattern. No key belongs in this document, the stage
registry, logs, generated data, or public artifacts. Current scripts already
cover schedule, lines, plays, drives, and havoc; advanced-game-statistics
acquisition remains a later wiring task and is not claimed as implemented here.

### The Odds API budget

The locked monthly budget is 20,000 credits with a 2,000-credit emergency
reserve. The reconciled balance above the reserve is available for normal
operations, subject to the existing quota, cooldown, overlap, and validation
gates.

## Duplicates, legacy references, and known risks

- Several `run_py` calls retain a canonical `scripts/...` path plus a root-level fallback for runtime compatibility. These are intentional transition fallbacks, but are a duplicate-source risk and should be retired only after runtime provenance review.
- Runtime-source reconciliation now accounts for all 61 registered primary script paths in the authoritative source repository. Twenty-three active sources were recovered without changing their behavior, and 20 byte-identical duplicate references were redirected to already tracked canonical paths. The reviewed deployment bootstrap installs those 20 canonical paths plus two structured projection paths through the explicit manifest. Old equivalent runtime files are retained; any later compatibility-copy removal requires separate review.
- Multiple providers may cover the same market. This is intentional acquisition redundancy; canonical normalization and sportsbook-selection rules remain downstream authority.
- `wait_for_network` warns and continues rather than failing, allowing cached futures data.
- The orchestration contains comments naming old V1 targets and explicitly logs that they are skipped. No recurring executable V1 builder, legacy index injector, `index_auto_market.html -> v1.html` promotion, or direct legacy publication is active.
- Publication and email remain enabled by default to preserve production behavior. Development must use static audits and isolated tests rather than executing this pipeline.

## Validation commands

```bash
bash -n daily_market_update.sh
python3 -m py_compile scripts/control/daily_run_status.py scripts/audit/audit_daily_automation.py
python3 scripts/audit/audit_daily_automation.py
python3 -m unittest tests.test_daily_automation
```

These checks do not call providers, send email, build the site, or publish.
