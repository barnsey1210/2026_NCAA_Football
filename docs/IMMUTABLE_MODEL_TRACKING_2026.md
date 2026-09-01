# Immutable 2026 model tracking v2

Status: prospective capture is integrated into the reviewed MAIN pipeline;
MAIN has not been deployed to AUTO and no public artifact has been published.

This design records the exact model and market states visible at an observation time, then settles them later without rewriting history. Stable content IDs make repeated capture idempotent. Corrections append replacements and explicit supersession pointers.

The registry includes individual component models, the legacy Standard models,
the active MAIN Standard identities, the 50/50 Total challenger, and both
existing Shadow models. Registration remains descriptive and separate from
authority selection. MAIN authority is switched, while runtime activation and
prospective capture remain pending deployment to AUTO.

## Capture boundary

`capture_current_contracts.py` reads only the accepted canonical projection and
current-market contracts. It defaults to preview; the canonical daily stage
uses explicit `--accept` after both acceptance boundaries. Content-derived IDs
mean identical reruns do not append rows, while changed projections,
availability, lifecycle, lines, or prices create new observations. Observation
time, provider/source time, formula version, per-component timestamps, source
artifacts, line, price, book, and kickoff are separate fields.

## Settlement and scorecards

`settle_accepted_observations.py` accepts only verified finals from
`data/canonical/game_results_2026.json`, appends settlement and score rows, and
never rewrites predictions. Scorecards are rebuildable views, never primary
evidence. CLV remains null until a canonical close exists.

## Backfill audit

The existing ledgers contain no accepted prospective rows. Current contracts
are snapshots, not a trustworthy history of what was visible at earlier
timestamps. Therefore no historical 2026 observations were silently backfilled.
Capture begins only after deployment and a new eligible accepted pregame state.

## Files requiring separate approval to deploy

1. Deploy the reviewed manifest entries from MAIN into `NCAAF_AUTO`.
2. Validate an AUTO preview, then an accepted prospective capture.
3. Confirm the deployed resolver reports the MAIN-selected active identities.
4. Publish the validated site bundle only after user approval.

No Shadow model, Shadow lifecycle rule, or frozen historical evidence was
changed by the MAIN authority activation.
