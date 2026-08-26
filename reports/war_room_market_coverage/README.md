# War Room selected-week market coverage audit

## Evidence boundary

- Runtime root: `/Users/jameslindesmith/NCAAF_AUTO`
- Latest fast provider snapshot audited: `theodds_20260826T163246Z`
- Provider response: 111 events, 2,362 normalized rows
- War Room matrix before repair: built `2026-08-26T16:40:18.835817+00:00`
- Preserved fast raw snapshots searched: 33
- Canonical matching audit: 0 unmatched rows, 0 invalid rows, 0 invalid pairs
- Provider calls made for this audit: 0

The row-level lineage is preserved in:

- `selected_week_market_coverage_before.csv`
- `selected_week_market_coverage_after.csv`

Each file contains one row per selected-week game and provider, including the
provider event ID, latest raw-provider pair state, normalized pair state,
canonical current-market pair state, War Room pair state, preserved-archive
observation counts/last-seen evidence, and rejection classification.

## Root cause

The War Room matrix read only the latest normalized fast CSV. It did not use a
fresh, complete pair already accepted by `current_market_contract.json` when a
book/game/market was absent from the latest fast response. That caused real,
still-current book-specific quotes to disappear from the Command Center when a
subsequent The Odds API response omitted that book/game.

The repair keeps the latest fast pair authoritative and fills only an exact
missing or invalid pair when all of the following are true:

1. the game is already on the latest matched fast board;
2. the book participated in the latest fast pull;
3. the canonical current-market pair is complete and internally valid; and
4. every quote still passes the existing canonical maximum-age rule at the
   fast-pull timestamp.

No denominator changes, cross-book quote copying, or fabricated markets are
used. The output records `CURRENT_MARKET_CONTRACT_FALLBACK` provenance.

## Before and after

| Provider | W0 games | W0 spread | W0 total | W1 games | W1 spread | W1 total |
|---|---:|---:|---:|---:|---:|---:|
| DraftKings before | 8/8 | 100.0% | 100.0% | 31/43 | 72.1% | 72.1% |
| DraftKings after | 8/8 | 100.0% | 100.0% | 42/43 | 90.7% | 97.7% |
| FanDuel before | 8/8 | 100.0% | 100.0% | 42/43 | 97.7% | 97.7% |
| FanDuel after | 8/8 | 100.0% | 100.0% | 43/43 | 100.0% | 100.0% |
| BetMGM before | 5/8 | 62.5% | 62.5% | 43/43 | 95.3% | 100.0% |
| BetMGM after | 8/8 | 100.0% | 100.0% | 43/43 | 100.0% | 100.0% |
| Caesars before | 8/8 | 100.0% | 100.0% | 42/43 | 97.7% | 97.7% |
| Caesars after | 8/8 | 100.0% | 100.0% | 43/43 | 100.0% | 100.0% |
| Pinnacle before | 8/8 | 100.0% | 100.0% | 37/43 | 86.0% | 86.0% |
| Pinnacle after | 8/8 | 100.0% | 100.0% | 37/43 | 86.0% | 86.0% |
| Novig before | 8/8 | 100.0% | 100.0% | 43/43 | 97.7% | 100.0% |
| Novig after | 8/8 | 100.0% | 100.0% | 43/43 | 97.7% | 100.0% |
| ProphetX before | 8/8 | 100.0% | 100.0% | 0/43 | 0.0% | 0.0% |
| ProphetX after | 8/8 | 100.0% | 100.0% | 0/43 | 0.0% | 0.0% |
| Kalshi before | 0/8 | 0.0% | 0.0% | 0/43 | 0.0% | 0.0% |
| Kalshi after | 0/8 | 0.0% | 0.0% | 0/43 | 0.0% | 0.0% |

## Legitimate remaining source gaps

These pairs do not exist in the latest provider response, the canonical
current-market contract, or any of the 33 preserved fast provider snapshots:

- DraftKings spread: `g57` Western Michigan at Michigan; `g39` Florida
  Atlantic at Florida; `g95` Washington State at Washington.
- DraftKings spread and total: `g60` UL-Monroe at Mississippi State.
- Pinnacle spread and total: `g19` San Jose State at Eastern Michigan; `g90`
  Fresno State at USC; `g22` Miami-FL at Stanford; `g56` Arkansas State at
  Memphis; `g42` UNLV at Hawaii; `g99` SMU at Florida State.
- Novig spread: `g60` UL-Monroe at Mississippi State. Novig supplied the total
  in all 33 preserved snapshots but never supplied a spread.
- ProphetX: no spread or total pair for any of the 43 Week 1 FBS-vs-FBS games.
- Kalshi: no spread or total pair for any Week 0 or Week 1 game.

Because the underlying sources do not contain these markets, the repair leaves
them unavailable rather than manufacturing 100% coverage.
