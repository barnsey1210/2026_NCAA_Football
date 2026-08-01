# 2026 NCAAF Project Map

_Updated 2026-08-01_

## Authoritative repository

`/Users/jameslindesmith/NCAAF_MAIN_REPO`

| Path | Purpose |
|---|---|
| `daily_market_update.sh` | Canonical daily runtime orchestration |
| `scripts/markets/` | Provider acquisition and canonical market builders |
| `scripts/ratings/` | Ratings acquisition, normalization, and history builders |
| `scripts/results/` | Scores, results, and postgame inputs |
| `scripts/injuries/` | Injury normalization and alert construction |
| `scripts/signals/` | Betting-signal builders |
| `scripts/site/` | V2 payload and page builders |
| `scripts/publish/` | Validated publication tooling |
| `scripts/audit/` | Regression, consistency, and pre-publish checks |
| `scripts/control/` | Application-side controller adapters; not the private workflow repository |
| `scripts/history/`, `scripts/snapshots/` | Historical and snapshot transforms |
| `deploy/source_manifest.txt` | Explicit runtime-deployment allowlist |
| `deploy/deploy_to_auto.sh` | Safe deployment command |
| `deploy/deploy_status.py` | Read-only CURRENT / BEHIND / UNKNOWN runtime audit |
| `deploy/README.md` | Deployment and rollback runbook |
| `tests/test_deploy_to_auto.sh` | Isolated deployment behavior tests |

## Operational runtime

`/Users/jameslindesmith/NCAAF_AUTO`

The runtime uses the same relative source paths as the main repository, plus mutable operational content. Important runtime classes include:

| Runtime area | Contents | Source-control policy |
|---|---|---|
| `data/` | Canonical data, histories, QA, site JSON, research, databases | Runtime/generated unless explicitly curated |
| `logs/` and reports | Execution logs and current summaries | Runtime only |
| raw/provider archives | Private responses and request evidence | Runtime only; may contain licensed or sensitive data |
| caches and temporary staging | Rebuild acceleration and run-scoped files | Runtime only |
| generated HTML and `build/` | Local/publication candidates | Generated; deployer must not overwrite implicitly |
| private environment files | API keys and credentials | Never Git |

Source changes originate in `NCAAF_MAIN_REPO`; the runtime receives only manifest-approved files.

## Control and publication repositories

### `/Users/jameslindesmith/NCAAF_CONTROL`

Private, repository-scoped manual/control tooling only. It may contain safe GitHub Actions workflows, controller configuration templates, and operating documentation. It must not contain production data, secrets, application-source mirrors, or public assets.

### `/Users/jameslindesmith/Sites/NCAAF_SITE`

Public static publication repository. It is updated only by the normal validated publication process from accepted runtime outputs.

## Stabilization deployment manifest

The initial manifest is deliberately limited to:

```text
daily_market_update.sh
CURRENT_PRIORITIES.md
scripts/markets/pull_sgo_ncaaf_game_odds.py
scripts/markets/build_sgo_canonical_artifacts.py
scripts/markets/build_sgo_daily_canonical.py
scripts/control/sgo_preview_adapter.py
scripts/audit/test_daily_betting_email_regression.py
scripts/injuries/build_injury_alerts.py
```

Adding a file requires an explicit source-ownership review, manifest edit, isolated deployment test, and focused commit.

## Canonical interfaces

- **Daily orchestration:** `daily_market_update.sh`
- **Deployment:** `deploy/deploy_to_auto.sh`
- **Deployment status:** `deploy/deploy_status.py`
- **Deployment allowlist:** `deploy/source_manifest.txt`
- **Public-site checks:** existing audit and publish check commands invoked by the runtime publisher
- **Publication:** existing runtime publication scripts; never performed by the deployer
