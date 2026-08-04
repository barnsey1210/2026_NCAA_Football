# SGO accepted-data dry run

**COVERAGE: PARTIAL**
**PRODUCTION ACCEPTANCE: BLOCKED**
**DRY-RUN VALIDATION ONLY**

- Dry-run ID: `acceptance-dry-run-20260730-corrected-sgo-final`
- External calls: 0
- Proposed changed fields: 8
- Production hashes unchanged: True
- Canonical history second-run additions: `{'data/odds/game_line_history.csv': 290, 'data/odds/game_book_line_history.csv': 0}`
- Builder failures: 0
- Classification: **NEEDS ACCEPTANCE-PATH FIX**

The mirror proves that validated same-book values can be applied without deleting accepted rows. It also proves the current acceptance/history schema is not ready for safe SGO promotion: spread/total prices and quote timestamps have no accepted target fields, and the SGO per-book appender bypasses the corrected canonical-week/mapping/freshness/paired-side policy.

## History and downstream result

- `game_line_history.csv`: 16,796 -> 17,086 on pass 1 -> 17,376 on identical pass 2. The second pass incorrectly added another full 290-row snapshot, so canonical snapshot idempotence failed.
- `game_book_line_history.csv`: 10,095 -> 13,040 on pass 1 -> 13,040 on pass 2. The 2,945 additions were 1,616 The Odds API, 543 Action Network, and 786 SGO rows. The current SGO appender ingested the entire archived page rather than the eight canonical Week 0 games.
- All six downstream builders completed: movement report, Matchups view, clean matchup history, matchup-history JSON, Odds game payload, and Schedule enrichment.
- Mirror shared-workspace audit passed for all 902 games. Normal public-site validation passed for 16 pages. The older projection-totals audit was not applicable to this mirror and failed against the current root `index.html` because it expects an embedded V1 database.
- Changed mirror assets were limited to the accepted-line clone, two history files, movement report, Matchups/Odds/Schedule JSON and their generated audits, and the copied SGO raw fixture. No mirror row was removed.

## Acceptance blockers

1. The accepted season-line schema has no spread/total price or provider quote timestamp targets.
2. The generic per-book appender ignores SGO; the separate SGO appender bypasses corrected canonical mapping, week, neutral-site, availability, freshness, and paired-side rules.
3. The general snapshot appender is not idempotent for an identical second execution.
4. The archived provider page is partial (`nextCursor` is non-empty), so missing events cannot be reconciled or removed.

## Required future acceptance gates

- Complete explicitly bounded canonical-week coverage and no unconsumed cursor.
- Canonical mapping threshold met, zero ambiguous games, and neutral-site preservation.
- Same-book, paired, fresh, available quotes only; no unavailable/stale fallback.
- Idempotent canonical history and downstream schema/audit success.
- V2 structural hashes unchanged.
- `acceptance_enabled=true` plus explicit run-scoped authorization; publication remains a separate confirmed gate.

## Pagination recommendation

Preferred: **bounded pagination for the canonical week**. If SGO supports a sufficiently precise date/week filter, one filtered request is cheapest, but it must still reject any returned cursor. Otherwise follow `nextCursor` with a declared page/request-unit ceiling until all required canonical games are covered; abort as PARTIAL if the ceiling is reached. Market-specific calls multiply cost (at least three calls before pagination) and increase pairing risk. Using another provider as primary with SGO validation can reduce SGO calls, but does not establish SGO completeness.

No further provider request is needed to fix or test these acceptance-path defects: the saved raw response is sufficient for provider-free replay.
