# AGENTS.md — 2026 NCAAF Project Instructions

## Read first

Before changing code, data contracts, builders, or public pages, read:

1. `docs/WAR_ROOM_DATA_ARCHITECTURE.md`
2. `config/public_page_data_contracts.json`
3. the current priorities/roadmap document in the repository
4. the repository architecture and project map documents

## Authoritative operating model

- `/Users/jameslindesmith/NCAAF_MAIN_REPO` is the authoritative source repository and the canonical GitHub Pages publishing repository.
- `/Users/jameslindesmith/NCAAF_AUTO` is the operational runtime workspace. It performs scheduled pulls, runtime builds, validation, email generation, and public artifact staging.
- `/Users/jameslindesmith/NCAAF_CONTROL` is reserved for guarded/manual refresh and acceptance tooling.
- `/Users/jameslindesmith/Sites/NCAAF_SITE` is legacy and is not part of the canonical daily publishing workflow.

## Data architecture rules

- Public pages may format canonical data differently, but must not independently select a provider or invent a page-local data pipeline.
- Reuse an existing canonical domain contract or extend it centrally.
- Add or update propagation-audit coverage whenever a new field, artifact, or page consumer is introduced.
- Do not display stale market data as current.
- When current live market data is unavailable, show an explicit unavailable or stale state rather than silently substituting cached data.
- Historical line data must remain labeled as historical and must not overwrite the canonical current market.
- Preserve the locked War Room homepage unless the task explicitly changes it.

## Publishing rules

- Runtime builds validated public artifacts in `NCAAF_AUTO/build/public_site`.
- The canonical publisher copies only allowlisted public artifacts into `NCAAF_MAIN_REPO`.
- Publication commits and pushes from `NCAAF_MAIN_REPO` to GitHub `main`.
- Never recursively publish the entire runtime data tree.
- Never use unrestricted source-tree synchronization or `--delete`.
- Respect the explicit public publish manifest and file-size guards.

## Safety

- Make targeted changes.
- Preserve backups before replacing important generated or production files.
- Do not delete legacy builders until dual-run parity and propagation audits prove they are no longer needed.
- Run syntax checks, required regression gates, public-site validation, and propagation audits before publishing.
