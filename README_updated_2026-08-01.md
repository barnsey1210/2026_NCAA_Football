# 2026 NCAA Football Data and Betting Platform

This repository is the authoritative source repository for the 2026 NCAAF application. Operational execution occurs in a separate runtime workspace so mutable data and generated outputs do not become source authority.

## Repository model

- **Source:** `/Users/jameslindesmith/NCAAF_MAIN_REPO`
- **Runtime:** `/Users/jameslindesmith/NCAAF_AUTO`
- **Manual control tooling:** `/Users/jameslindesmith/NCAAF_CONTROL`
- **Public site:** `/Users/jameslindesmith/Sites/NCAAF_SITE`

See [PROJECT_ARCHITECTURE_2026-08-01.md](PROJECT_ARCHITECTURE_2026-08-01.md) for boundaries and [PROJECT_MAP_updated_2026-08-01.md](PROJECT_MAP_updated_2026-08-01.md) for the directory map.

Future repository tasks should follow the reusable [Codex task workflow](docs/CODEX_TASK_TEMPLATE.md), including its conflict rule, review boundary, and runtime completion criteria.

The daily production path and its stage/failure inventory are documented in [docs/DAILY_AUTOMATION.md](docs/DAILY_AUTOMATION.md). The machine launcher remains thin; all business logic stays in the one deployed `daily_market_update.sh` entry point.

## Safe source workflow

1. Make and review source changes in this repository.
2. Run focused tests and repository validation.
3. Commit the reviewed source.
4. Add runtime files to `deploy/source_manifest.txt` only after ownership review.
5. Test deployment against an isolated target.
6. Deploy the reviewed commit to `NCAAF_AUTO`.
7. Run operational workflows and publication separately.

Do not edit a runtime copy and treat it as authoritative source.
For runtime-affecting features, merge plus successful source tests are not the final operational step: run the single deployment command and verify deployment status. Documentation-only changes generally do not require deployment.

V2 page health is standardized through the central registry and shared renderer described in [docs/PAGE_HEALTH_SUMMARIES.md](docs/PAGE_HEALTH_SUMMARIES.md). Page URLs and page-specific data remain unchanged; the shared strip summarizes existing artifacts and provenance.

## Manifest deployment

Preview the allowlist:

```bash
sed -n '1,200p' deploy/source_manifest.txt
```

Test the deployer:

```bash
bash tests/test_deploy_to_auto.sh
```

Deploy the current clean source commit to the default runtime:

```bash
bash deploy/deploy_to_auto.sh
```

Test against an isolated runtime:

```bash
bash deploy/deploy_to_auto.sh --target /absolute/path/to/test-runtime
```

Audit the default runtime without changing it:

```bash
python3 deploy/deploy_status.py
```

The deployer creates a timestamped rollback backup, prints exact restore instructions, and writes `data/control/deployed_source_version.json` only after successful validation. A dirty source tree is rejected by default; the exceptional override is documented in `deploy/README.md` and should not be used for routine releases.

The deployer never broadly syncs `scripts/`, never uses deletion synchronization, and never runs providers, email, the daily pipeline, or publication.

## Validation

At minimum, deployment-related changes should run:

```bash
bash tests/test_deploy_to_auto.sh
git diff --check
```

Deployed shell scripts are checked with `bash -n`; Python source is checked with `python3 -m py_compile`. The daily betting email regression runs from a real runtime when its artifacts exist and explicitly reports `SKIP` in isolated targets without those fixtures.

## Current status

The August 1 stabilization baseline completed SGO all-upcoming acceptance, email regression protection, injury empty-input handling, and legacy V1 daily-path cleanup. The immediate priority is review and controlled adoption of manifest-based runtime deployment. See [CURRENT_PRIORITIES.md](CURRENT_PRIORITIES.md).

## Safety

- Never commit API keys or private environment files.
- Keep raw provider responses, databases, logs, caches, current-run status, and generated publication artifacts in the runtime.
- Keep `NCAAF_CONTROL` limited to manual/control tooling.
- Keep acceptance and publication separately gated.
- V2 is canonical; do not restore legacy V1 publication paths.
