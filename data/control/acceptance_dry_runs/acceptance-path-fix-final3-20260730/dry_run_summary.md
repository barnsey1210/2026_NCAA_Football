# SGO accepted-data dry run

**COVERAGE: PARTIAL**
**PRODUCTION ACCEPTANCE: BLOCKED**
**DRY-RUN VALIDATION ONLY**

- Dry-run ID: `acceptance-path-fix-final3-20260730`
- External calls: 0
- Proposed changed fields: 8
- Production hashes unchanged: True
- Canonical history second-run additions: `{'data/odds/game_line_history.csv': 0, 'data/odds/game_book_line_history.csv': 2159}`
- Builder failures: 0
- Classification: **NEEDS MORE ACCEPTANCE-PATH FIXES**

The mirror proves that the additive canonical quote/display artifacts preserve prices and timestamps, validated same-book values can be applied without deleting accepted rows, and both history paths are idempotent. Real acceptance remains blocked only because the archived provider page is partial and retains a cursor.
