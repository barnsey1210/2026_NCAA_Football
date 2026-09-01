# 2026 NCAAF — Current Priorities

_Synchronized as of 2026-09-01_

## Repository roles

- `/Users/jameslindesmith/NCAAF_MAIN_REPO` is the authoritative Git source for reviewed code, configuration, tests, and documentation.
- `/Users/jameslindesmith/NCAAF_AUTO` is the operational runtime workspace. It holds mutable data, caches, databases, logs, generated pages, and provider responses and is not a Git repository.
- `/Users/jameslindesmith/NCAAF_CONTROL` is limited to private manual/control tooling and safe workflow dispatch. It is not a source-code mirror, data repository, or publication repository.
- `/Users/jameslindesmith/NCAAF_MAIN_REPO` is also the canonical GitHub Pages
  publication repository. `/Users/jameslindesmith/Sites/NCAAF_SITE` is legacy
  and is not part of the canonical workflow.

The V2 site is canonical. Legacy V1 generation and promotion must remain disabled.

## Completed stabilization work

The stabilization checkpoint at commit `9318203` completed:

- SportsGameOdds all-upcoming canonical-game acceptance, with selected week retained as display-only state.
- Daily betting email regression coverage and fail-fast integration.
- Injury ingestion empty-input handling with clean zero-row outputs and explicit unavailable status.
- Legacy V1 daily-build and publication cleanup from the canonical daily workflow.

These are closed stabilization items. Regressions should be fixed without restoring legacy paths or duplicating the canonical implementations.

## Completed — manifest deployment and daily automation consolidation

The first controlled manifest deployment completed successfully. Daily automation consolidation now preserves the single production workflow while adding an ordered stage registry, structured runtime status, explicit email/publication gating, and static/isolated regression coverage. Deployment remains manual and separate from daily execution.

Required operating rules:

1. Deploy only paths explicitly listed in `deploy/source_manifest.txt`.
2. Require a clean authoritative source tree unless the documented override is intentionally used.
3. Create timestamped rollback backups before replacement.
4. Validate deployed shell and Python source and run the runtime email regression when its fixtures exist.
5. Never broadly synchronize `scripts/`, never use deletion synchronization, and never overwrite runtime data or generated outputs implicitly.
6. Review the deployment summary before running any live daily workflow.
7. Confirm `python3 deploy/deploy_status.py` reports `CURRENT` after deployment.

Deployment stays manual and separate from `daily_market_update.sh`, the LaunchAgent, the 8 AM job, and publication. Successful runtime deployments record their exact source commit in `data/control/deployed_source_version.json`.

## Immediate next priorities

1. Improve Command Center logo/value spacing and expired operator-session UX
   without changing the approved matrix width/layout.
2. Migrate the current GitHub Pages public site to Cloudflare Pages at
   `barnseywr.com`, redirect `www` to the apex, and preserve the authenticated
   `control.barnseywr.com` origin after pre-cutover CORS/Access validation.
3. Resume historical timing analysis separately; deferred SUN12 and
   retrospective anomalies are not validated production betting conclusions.

Active Standard Spread is `standard_spread_4src_equal_v1` (SP+, FPI,
TeamRankings, DRatings at 25% each). Active Standard Total is
`standard_total_sp_massey_dratings_v1` (SP+ Total 40%, Massey Dual 40%,
DRatings Total 20%). Sagarin remains Shadow/research/legacy only for game
projections. Spread is Official at 4/4 and Hybrid at 2-3/4 accepted updates;
Total is Official at 3/3 and Hybrid at 2/3.

## Non-negotiable safeguards

- Do not edit authoritative source directly in `NCAAF_AUTO` and then treat it as canonical.
- Do not copy runtime secrets, raw responses, databases, logs, caches, spreadsheets, or generated HTML into source control.
- Do not use `NCAAF_CONTROL` for production application code or data.
- Do not publish merely because a build or deployment succeeds; publication remains a separate validated operation.
- Do not restore legacy V1 shells or builders.
