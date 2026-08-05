# Canonical Data Flow Consolidation

## Objective

Eliminate page-local source selection and silent stale-data fallback across the
War Room public site.

## Phase 1 — Current Market Contract

Status: implementation package prepared.

### Canonical contract

`data/site/current_market_contract.json`

Source priority is applied independently per:

`game_id × sportsbook × market × side`

1. Fresh SportsGameOdds accepted quote
2. Fresh Action Network quote
3. Missing

Historical snapshots are never used as current-market fallback.

### Consumers in Phase 1

- Odds Screen current quote inventory
- Openers Best Market through `matchups_view.json`
- Matchups current/reference/best-side market
- War Room Home market summaries through `matchups_view.json`

### Required assertions

- `stale_current_quotes_displayed = 0`
- Missing current data is displayed as missing, not cached.
- Best-side values match the canonical contract.
- Current market and historical market are audited separately.
- Runtime/public/main publication parity remains a separate audit.

## Remaining phases

1. Add The Odds API as the second approved backup provider.
2. Remove legacy Action-only quote selection from the Odds Screen builder.
3. Migrate Betting/Viewer's Guide and daily email.
4. Formalize ratings date semantics.
5. Expand domain contracts to futures, injuries, coaching, schedule, weather,
   simulations, conferences, and playoff.
6. Retire obsolete paths only after dual-run parity checks.
