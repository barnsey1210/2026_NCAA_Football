# Source Files Guide

_Authoritative as of 2026-08-01_

## Source-of-truth rule

Reviewed code, configuration, tests, and documentation are authored in `/Users/jameslindesmith/NCAAF_MAIN_REPO`. A similarly named file in `/Users/jameslindesmith/NCAAF_AUTO` is an operational copy, not an independent source of truth.

Use [`docs/CODEX_TASK_TEMPLATE.md`](docs/CODEX_TASK_TEMPLATE.md) as the standard branch, test, review, deployment, and reporting checklist for future source work.

## What belongs in the main repository

- Pipeline and builder source under `scripts/`.
- The canonical orchestration shell script.
- Tests and audits that define expected behavior.
- Safe configuration templates and schemas.
- Architecture, runbooks, source guides, and current priorities.
- Explicitly reviewed static inputs whose licensing and ownership permit versioning.

## What remains runtime-only

- API keys, cookies, tokens, and private environment files.
- Raw provider responses and licensed feeds.
- Market, ratings, results, betting, and research databases.
- Logs, caches, temporary staging, current-run ledgers, and status files.
- Generated site JSON, HTML, publication builds, and backups.
- Machine-specific LaunchAgent state and runner files.

Runtime material is not copied back to source control merely because a script generated it.

## Deployment eligibility

A source file reaches `NCAAF_AUTO` only when its relative path appears in `deploy/source_manifest.txt`. Manifest entries must be regular files inside the repository and may not be absolute, empty, missing, directories, symlinks, or contain parent traversal.

To add a deployable source file:

1. Confirm it is authoritative source rather than generated runtime output.
2. Add the exact repository-relative path to the manifest.
3. Add or update an isolated deployment test when behavior changes.
4. Run `bash tests/test_deploy_to_auto.sh`.
5. Review the target path, backup behavior, and syntax validation.
6. Commit the source and manifest change together.
7. After review and merge, deploy once with `bash deploy/deploy_to_auto.sh` and confirm `python3 deploy/deploy_status.py` reports `CURRENT`.

Do not solve deployment by syncing an entire directory.
Documentation-only source changes normally do not require runtime deployment. Runtime-affecting work is not operationally complete until the reviewed commit has been deployed.

## Approved manifest evolution

The initial list was limited to the eight files from stabilization commit `9318203`. Daily automation consolidation adds only the stage registry and run-status writer required by the changed orchestration. `deploy/source_manifest.txt` is always the exact current allowlist; no directory is implicitly deployable.

## Review checklist

Before approving a source change, confirm:

- the file is in the authoritative repository;
- no secrets or machine-specific values are present;
- no raw/runtime/generated artifact is being introduced accidentally;
- relevant unit, regression, or audit checks pass;
- a deployable file is explicitly allowlisted;
- deployment does not imply acceptance, provider calls, email, or publication;
- rollback instructions are available for runtime replacement.

## Conflict resolution

If source and runtime copies differ, first determine whether the runtime difference is mutable state or an emergency source edit. Preserve evidence, port any legitimate source fix into `NCAAF_MAIN_REPO`, review and commit it, then redeploy through the manifest. Do not overwrite either side blindly.
