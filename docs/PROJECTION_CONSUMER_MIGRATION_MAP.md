# Projection Consumer Migration Map

Date: 2026-08-19  
Status: canonical resolver and standalone Command Center consumer active;
broader consumer migration remains in controlled rollout

Target source for scheduled-game projections:
`data/site/current_game_projection_contract.json`

| File | Current source | Current formula/use | Target contract | Migration required | Risk |
| --- | --- | --- | --- | --- | --- |
| `scripts/projections/build_game_projection_blend_2026.py` | `game_projection_sources_2026.csv`, preseason DB, mutable blend config | Equal-available spread and total blend | Becomes legacy comparison during dual-run; canonical engine owns named formulas | Do not delete; compare row-level outputs, then remove it as a public projection owner | High: silent renormalization and nonhistorical source sets |
| `scripts/projections/apply_game_projection_blend_to_preseason_db.py` | Blend CSV | Overlays blended spread/total into preseason DB | Read named Standard projections from canonical contract only after parity approval | Stop treating preseason DB as projection authority | High: broad downstream fan-out |
| `scripts/site/build_matchups_view.py` | Preseason DB / embedded site data | Adapts `projected_margin_home` and `projected_total` | Named projections from canonical contract | Add adapter lookup by `game_id`; no page-local blend | High: Openers, Matchups, Home, Betting, Team fan-out |
| `index.html` and `scripts/site/build_war_room_home.py` | `matchups_view.json` | Displays standard model values | Continue through migrated matchup adapter | No direct contract calculation | Medium |
| `openers.html` | `matchups_view.json`, `saturday_shadow_lines.json` | Standard values plus current Market/SP+ Shadow mode | Standard and historical Shadow model IDs from canonical contract | Retain current UI until dual-run parity and availability review | High: current Shadow label is not historical model |
| `matchups.html` | `matchups_view.json` | Displays model spread/total and computes market edge | Canonical named Standard model fields through adapter | Preserve sign conversion and edge tests | High: sign inversion |
| `matchup.html`, `matchup_workspace.js` | `matchups_view.json` | Individual matchup model context | Canonical projection adapter | No local formula | Medium |
| `schedule.html`, `scripts/site/build_schedule_live_enrichment.py` | `matchups_view.json`, `saturday_shadow_lines.json` | Standard and next Shadow values | Canonical model IDs and explicit availability | Replace ambiguous projection keys after parity | Medium |
| `betting.html` | `matchups_view.json`, historical performance contracts | Live context and frozen performance evidence | Live values from canonical projection adapter; historical evidence unchanged | Keep performance artifacts separate from live inference | Medium |
| `team.html`, `team_coach_card.js` | `matchups_view.json` | Model spread, total, win probability, edge | Canonical Standard projection through adapter | Preserve team-relative sign conversion | High: home vs team orientation |
| `scripts/signals/build_game_betting_angles_2026.py` | `game_projection_blend_2026.csv` | Betting-angle inputs | Canonical model ID selected centrally | Move only after historical formula parity | High: changes signal population |
| `scripts/signals/build_travel_1h_signals_2026.py` | `matchups_view.json` | Projection context | Canonical adapter | No independent fallback | Medium |
| `scripts/model_tracking/capture_model_tracking.py` | `matchups_view.json` | Captures active projection | Canonical model ID, version, state and component provenance | Extend ledger schema before switch | High: historical comparability |
| `scripts/model_tracking/settle_model_tracking.py` | Captured matchup projections | Settles model results | Versioned captured model identity | Never relabel legacy predictions | High |
| `scripts/history/append_game_line_model_history.py` | `matchups_view.json` | Stores spread/total beside market | Canonical value plus model ID/version | Add explicit sign and state fields | High |
| `scripts/history/build_matchup_line_history_clean.py` | Matchups and history | Fills projection history | Canonical snapshots only; no backfill from current value | Preserve observation-time meaning | High |
| `scripts/agents/build_home_command_center.py` | `matchups_view.json` | Current dashboard calculations | Future adapter consumes canonical contract | Do not become a formula owner | Medium |
| `scripts/simulations/run_playoff_model_2026.py` | Preseason DB projected margin fallback | Scheduled-game expected margins | Team Rating Engine for simulations; canonical Game Projection Engine only where explicitly intended | Decide simulation boundary before migration | High: game engine and team rating engine must remain separate |
| `scripts/war_room/build_war_room_market_matrix.py`, `scripts/war_room/build_war_room_health.py`, `scripts/site/build_war_room_page.py`, `war-room.html` | Canonical projection, market, rating, schedule, betting, and health/status owners | Adapts named values and evidence into standalone operational contracts | Canonical projection contract plus existing domain contracts | Implemented V1; retain unavailable states and prohibit page-local blends | High: freshness and propagation must remain explicit |

## Team Rating Engine boundary

The Team Rating Engine remains separate. Its production composite is equal-weight SP+, FPI, TeamRankings, and Sagarin. DRatings is excluded. Massey and Powers remain research sources. Simulations and hypothetical matchups may use the Team Rating Engine when scheduled-game projections are unavailable; they must not call that result a canonical Standard Spread game projection.

## Migration sequence

1. Dual-run the new contract without consumer changes.
2. Refresh the existing normalized provider-source artifact through its existing pipeline; do not add source selection to the canonical builder.
3. Pass historical formula, sign, missingness, and 2025 Sagarin fixture tests.
4. Migrate `build_matchups_view.py` as the first adapter and compare every game.
5. Migrate Openers and Matchups through that adapter without redesign.
6. Extend line history and model tracking with model ID/version/state before switching signals.
7. Migrate signal builders and remaining page adapters.
8. Retire legacy projection ownership only after dual-run parity and propagation audits pass.
9. Command Center V1 data projections and standalone UI are implemented from
   canonical contracts. Remaining work is live-season acceptance and separately
   authorized navigation exposure, not a Home replacement.
