# Standard Codex task workflow

> **Conflict rule:** If this document conflicts with an individual task prompt, stop and ask for clarification rather than making assumptions.

Use this template for repository work. Keep every task scoped, reviewable, and explicit about operational effects.

## Project roles

- `/Users/jameslindesmith/NCAAF_MAIN_REPO` is the authoritative source repository.
- `/Users/jameslindesmith/NCAAF_AUTO` is the operational runtime workspace, not a development repository.
- `/Users/jameslindesmith/NCAAF_CONTROL` is limited to guarded/manual control tooling.
- `/Users/jameslindesmith/Sites/NCAAF_SITE` is the publication repository.

## Required reading

Before runtime-affecting work, read:

- `PROJECT_ARCHITECTURE_2026-08-01.md`
- `CURRENT_PRIORITIES.md`
- `PROJECT_MAP_updated_2026-08-01.md`
- `README_updated_2026-08-01.md`
- `deploy/README.md`
- `docs/DAILY_AUTOMATION.md`
- `docs/RUNTIME_SOURCE_RECONCILIATION.md`
- `docs/CODEX_TASK_TEMPLATE.md`

## Standard workflow

1. Create a focused branch from current `main`.
2. Inspect the existing implementation and data flow before changing anything.
3. Implement only the requested scope; preserve unrelated behavior.
4. Add or update focused tests and run applicable audits.
5. Commit focused changes, push the branch, and open a PR against `main`.
6. Do not merge without explicit approval.
7. After an approved merge, deploy runtime files only with:

   ```bash
   bash deploy/deploy_to_auto.sh
   ```

8. Verify the deployed source with:

   ```bash
   python3 deploy/deploy_status.py
   ```

9. Runtime-affecting work is not complete until deployment status is `CURRENT`.

## Prohibited unless explicitly authorized

- Develop directly in `NCAAF_AUTO` or treat runtime copies as source.
- Broadly synchronize directories, use broad `rsync`, or use `rsync --delete`.
- Push directly to `main`.
- Change the LaunchAgent, API keys, credentials, or private environment files.
- Call live APIs, send email, or publish during development tests.
- Modify `NCAAF_CONTROL` or `NCAAF_SITE`.
- Delete compatibility files.
- Change unrelated pages, pipelines, or features.

## Deployment manifest policy

- Add only the exact runtime source files required by the feature.
- Never add directories, globs, generated data, logs, caches, databases, raw responses, or build outputs.
- Explain every manifest addition in the PR.
- Preserve manifest-only copying, rollback backups, atomic replacement, and validation behavior.
- Documentation-only changes usually do not require runtime deployment.

## Testing expectations

Run what applies to the change and report exact commands and results:

- `bash -n` for shell source.
- `python3 -m py_compile` for Python source.
- Focused unit and regression tests.
- `python3 scripts/audit/audit_daily_automation.py` for automation changes.
- `bash tests/test_deploy_to_auto.sh` for deployment or manifest changes.
- Daily betting email regression when its runtime fixtures are available.
- `git diff --check`.
- Two-run idempotence checks for generated artifacts.
- Fixture-based or saved-response tests instead of live provider calls.

## Required deliverables

Every completed task should report:

- concise summary and changed-file list;
- exact tests and results;
- known risks and follow-up work;
- manifest and deployment impact;
- PR URL/number and commit hashes;
- what was intentionally not run or changed; and
- the next recommended step.

## ChatGPT and Codex responsibilities

**ChatGPT:** architecture, product direction, UX/UI requirements, prioritization, review criteria, and deployment approval.

**Codex:** repository inspection, implementation, refactoring, tests, PR preparation, controlled deployment after approval, and documentation updates.

## Feature completion rule

- Runtime-affecting work: **branch -> test -> PR -> review -> merge -> deploy -> verify `CURRENT`**.
- Documentation-only work: **branch -> test/check -> PR -> review -> merge**.
