# 2026 NCAAF Project Architecture

_Authoritative as of 2026-08-01_

## System boundaries

| Location | Role | Authoritative for | Must not become |
|---|---|---|---|
| `/Users/jameslindesmith/NCAAF_MAIN_REPO` | Main Git repository | Reviewed source, configuration, tests, and documentation | Runtime working directory or secret store |
| `/Users/jameslindesmith/NCAAF_AUTO` | Operational runtime | Mutable provider data, histories, databases, caches, logs, generated assets, and execution state | Independent source repository |
| `/Users/jameslindesmith/NCAAF_CONTROL` | Private control repository | Manual dispatch workflows, status-only controls, and controller templates | Application-source mirror, production-data store, or publisher |
| `/Users/jameslindesmith/Sites/NCAAF_SITE` | Public publication repository | Validated static publication output | Development or runtime workspace |

`NCAAF_MAIN_REPO` is the single source of truth for versioned application source. `NCAAF_AUTO` is intentionally mutable and receives reviewed files through an allowlisted deployment.

## Controlled flow

```text
NCAAF_MAIN_REPO
  reviewed commit + deploy/source_manifest.txt
                  |
                  v
       deploy/deploy_to_auto.sh
       backup + atomic copy + validation
                  |
                  v
             NCAAF_AUTO
 provider pulls -> canonical data -> V2 builders -> publish validation
                  |
                  v
              NCAAF_SITE
```

`NCAAF_CONTROL` may request an approved operation, but it does not replace any pipeline implementation. Full refresh delegates to the canonical runtime workflow. Provider calls, acceptance, and publication remain independently gated.

## Canonical runtime layers

1. **Acquisition** — provider-specific scripts pull ratings, odds, results, injuries, and other inputs into private runtime storage.
2. **Normalization** — canonical builders map teams and games, retain provenance, and produce normalized artifacts.
3. **Model and signal generation** — approved calculations consume canonical data; they do not pull providers independently.
4. **V2 site generation** — site builders create the current V2 payloads and static pages.
5. **Validation and publication** — audits must pass before the normal publisher updates `NCAAF_SITE`.

The daily entry point is `daily_market_update.sh`. Legacy V1 generation and direct legacy page promotion are excluded from that workflow.

## Deployment architecture

The deployment boundary is file-manifest based:

- `deploy/source_manifest.txt` is the complete allowlist.
- `deploy/deploy_to_auto.sh` validates repository identity, source cleanliness, manifest safety, and target safety.
- Existing target files receive timestamped rollback backups preserving relative paths.
- Files are installed atomically where practical.
- Deployed `.sh` and `.py` files are syntax checked.
- The email regression runs from the runtime when its required artifacts exist; isolated targets report an explicit skip.

The deployer does not run the daily pipeline, call providers, send email, or publish.

## Data ownership and secrets

Runtime-only material includes API environment files, raw provider responses, databases, logs, caches, current-run ledgers, generated HTML, and publication staging. These remain outside the source manifest unless a specific reviewed decision explicitly changes ownership.

Secrets are loaded from private environment files and must never appear in Git, command output, generated JSON, audit reports, or workflow summaries.

## Completed stabilization checkpoint

Commit `9318203` is the approved source baseline for:

- SGO all-upcoming canonical-game acceptance;
- daily betting email regression protection;
- injury empty-input handling; and
- removal of legacy V1 work from the daily path.

The first deployment manifest intentionally contains only the eight files approved in that checkpoint.
