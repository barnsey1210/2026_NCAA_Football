# 2026 Futures pre-Week-1 checkpoint recovery

## Authority

The first weekly baseline is the exact generated `data/site/futures_view.json`
stored in Git commit `cad503f9754f4ee057ef2040e5c297e8fdae08e7`.
It was built at `2026-08-31T12:07:08.958970+00:00`, strictly before the first
scheduled Week 1 FBS kickoff at `2026-09-03T22:00:00+00:00`.

This is an authentic unified artifact, not a post-hoc reconstruction. Its Git
blob is `c42eb8a869f1e53cfc9702504e36dda07c84727d`; its SHA-256 is
`10b7f64d5e342c1c666adfbeb14181f223b5241ccd15fec12ce3cdc06cd79236`.

The same commit contains the corresponding season simulation (Git blob
`0afc7936ee446217df0d5c1f0a171fb89cf1ead9`, built at
`2026-08-31T12:02:23.196619+00:00`) and playoff simulation (Git blob
`1b11e2455361e3c6f89fbe2d04dcf77e5669ddc3`, built at
`2026-08-31T12:05:11.378254+00:00`).

## Coverage

- 138 team rows and 138 projected-win values
- 107 market win totals
- 138 conference-title model probabilities and 109 market probabilities
- 138 CFP model and market probabilities
- 138 national-title model and market probabilities

Unavailable source fields remain null. Historical per-book quote arrays were
not present and are not claimed.

## Recovery contract

Run `scripts/markets/recover_preweek1_futures_checkpoint.py`. The importer
reads the Git object directly, verifies the expected Git blobs and SHA-256,
requires the source timestamp to be strictly pre-kickoff, and imports it under
checkpoint ID `2026-preweek1-git-c42eb8a869f1e`. Repeated runs verify the exact
existing record and do not duplicate or mutate it. A conflicting record fails
closed.

The weekly selector accepts only populated successful checkpoints strictly
before the first FBS kickoff of the latest completed week. It selects the
latest qualifying checkpoint and leaves a missing baseline explicit.
