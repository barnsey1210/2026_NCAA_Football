# SGO accepted-data dry run

**COVERAGE: PARTIAL**
**PRODUCTION ACCEPTANCE: BLOCKED**
**DRY-RUN VALIDATION ONLY**

- Dry-run ID: `acceptance-path-fix-retest-20260730`
- External calls: 0
- Proposed changed fields: 8
- Production hashes unchanged: True
- Canonical history second-run additions: `{'data/odds/game_line_history.csv': 0, 'data/odds/game_book_line_history.csv': 0}`
- Builder failures: 0
- Classification: **NEEDS ACCEPTANCE-PATH FIX**

The mirror proves that validated same-book values can be applied without deleting accepted rows. It also proves the current acceptance/history schema is not ready for safe SGO promotion: spread/total prices and quote timestamps have no accepted target fields, and the SGO per-book appender bypasses the corrected canonical-week/mapping/freshness/paired-side policy.
