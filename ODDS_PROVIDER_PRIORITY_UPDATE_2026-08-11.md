# 2026 NCAAF Odds Provider Architecture Update

Date: 2026-08-11

## Production current odds source priority

The production current-market odds pipeline now uses:

1.  The Odds API --- primary current sportsbook odds source
2.  SportsGameOdds --- secondary/backup current odds source
3.  Action Network --- fallback source where available
4.  Unavailable

Source selection remains quote-level:

`canonical_game_id × sportsbook × market_type × side`

The system must not select a provider for an entire game if another
provider has better coverage for a specific sportsbook, market, or side.

## Provider roles

### The Odds API

Primary source for: - current spreads - current totals - current
moneylines - sportsbook quote freshness

### SportsGameOdds

Secondary source for: - backup coverage - validation - research - future
provider comparison

### Action Network

Fallback source when primary sources do not provide the required quote.

## Documentation updates required

Update references that currently state:

"SportsGameOdds is primary"

to:

"The Odds API is primary. SportsGameOdds remains a secondary approved
provider."

Do not remove historical SGO references. SGO research datasets, audits,
and historical analysis remain valid.

## Implementation status

Current canonical market contract priority:

The Odds API → SportsGameOdds → Action Network → Missing

Public pages should continue consuming the canonical current-market
contract rather than selecting providers independently.
