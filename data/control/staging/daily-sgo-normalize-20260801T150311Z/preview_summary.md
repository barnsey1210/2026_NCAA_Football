# Corrected SGO provider-free replay

- REPLAY_SOURCE_RUN_ID: fixture
- NETWORK_CALLS: 0
- COVERAGE: COMPLETE (1 archived page(s); nextCursor=False)
- ACCEPTANCE: SKIPPED
- PUBLICATION: SKIPPED
- Raw events: 111
- Canonical week: 0 (2026-08-29 to 2026-11-28)
- Mapped / unmatched / ambiguous / excluded: 110 / 1 / 0 / 0
- Staged FBS-FBS / FCS-FBS / FCS-FCS / neutral: 70 / 40 / 0 / 5
- Quote observations: 1757 (unavailable 101, suspended 0, stale 62)
- Corrected changes: games 30, spreads 25, totals 7, moneylines 7
- Original changes: games 39, spreads 29, totals 14, moneylines 7

The material count reduction is intentional: the original preview merged SGO provider Weeks 0/1 into 91 rows, matched only exact lowercase team pairs, and selected the freshest quote across books before comparing it to a DraftKings/Bovada-priority accepted row. The corrected replay stages only canonical Week 0, preserves all supported quote rows, and counts movement only when a complete paired quote exists for the accepted row's same display sportsbook. Missing accepted values are not counted as movements.

The response is sufficient to correct and test normalization for the events retained on its first page. It is not sufficient to establish complete upcoming coverage because nextCursor was non-empty. A future production design should use bounded pagination with a declared maximum page/request budget, preflight cost, abort on budget exhaustion, a PARTIAL warning, and no acceptance when required coverage is incomplete. The existing one-request preview guarantee remains unchanged pending approval.
