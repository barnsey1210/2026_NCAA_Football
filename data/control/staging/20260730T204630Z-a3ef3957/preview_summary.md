# Corrected SGO provider-free replay

- REPLAY_SOURCE_RUN_ID: n/a
- NETWORK_CALLS: 2
- COVERAGE: COMPLETE (2 archived page(s); nextCursor=False)
- ACCEPTANCE: SKIPPED
- PUBLICATION: SKIPPED
- Raw events: 111
- Canonical week: 0 (2026-08-29 to 2026-08-29)
- Mapped / unmatched / ambiguous / excluded: 110 / 1 / 0 / 0
- Staged FBS-FBS / FCS-FBS / FCS-FCS / neutral: 8 / 0 / 0 / 2
- Quote observations: 220 (unavailable 19, suspended 0, stale 6)
- Corrected changes: games 0, spreads 0, totals 0, moneylines 0
- Original changes: games 39, spreads 29, totals 14, moneylines 7

The material count reduction is intentional: the original preview merged SGO provider Weeks 0/1 into 91 rows, matched only exact lowercase team pairs, and selected the freshest quote across books before comparing it to a DraftKings/Bovada-priority accepted row. The corrected replay stages only canonical Week 0, preserves all supported quote rows, and counts movement only when a complete paired quote exists for the accepted row's same display sportsbook. Missing accepted values are not counted as movements.

The response is sufficient to correct and test normalization for the events retained on its first page. It is not sufficient to establish complete upcoming coverage because nextCursor was non-empty. A future production design should use bounded pagination with a declared maximum page/request budget, preflight cost, abort on budget exhaustion, a PARTIAL warning, and no acceptance when required coverage is incomplete. The existing one-request preview guarantee remains unchanged pending approval.
