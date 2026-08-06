# 2026 NCAAF Project Map

_Last updated: 2026-08-06_

## Current operating rule

The authoritative source-code repository is:

- Local: `/Users/jameslindesmith/NCAAF_MAIN_REPO`
- GitHub: `barnsey1210/2026_NCAA_Football`

The operational runtime workspace is `/Users/jameslindesmith/NCAAF_AUTO`. The manual control repository is `/Users/jameslindesmith/NCAAF_CONTROL`. The validated public deployment repository is `/Users/jameslindesmith/Sites/NCAAF_SITE`.

Canonical V2 owns public output. Runtime generates and validates; the main repository preserves approved source and publishes explicitly. Do not restore recurring legacy V1 ownership.

## Repository responsibilities

### `NCAAF_MAIN_REPO`
- Approved source code, tests, documentation, canonical data artifacts, and Git history.

### `NCAAF_AUTO`
- Scheduled execution, live pulls, runtime data, logs, caches, generated reports, and publication preparation.

### `NCAAF_CONTROL`
- Guarded/manual refresh, acceptance, audit-ledger, rollback, and controller-specific tooling.

### `NCAAF_SITE`
- Validated public-site files and GitHub Pages publication.

## CFBDepth data architecture

Official CFBDepth CSV exports now follow this path:

```text
official CFBDepth CSV exports
  → data/raw/cfbdepth/2026-08-05/
  → scripts/research/import_cfbdepth_exports.py
  → data/canonical/cfbdepth_*
  → scripts/site/build_cfbdepth_team_asset.py
  → data/site/cfbdepth_teams_2026.json
  → standalone Matchups / team pages / curated drawer subset
```

Research-only matchup work uses:

```text
scripts/research/build_cfbdepth_matchups_enrichment.py
  → data/research/cfbdepth_matchups/cfbdepth_matchups_team_enrichment_2026.json
  → data/research/cfbdepth_matchups/preview_ohio_state_at_texas.json
```

Validated coverage:

- 15 official exports
- 7 team datasets
- 12,381 mapped player rows
- 140 player teams
- all 138 site teams covered
- 1,110 team-position groups
- zero warnings

Data-use rules:

- Page builders read canonical or site assets, never raw exports.
- Each team is stored once in the shared site asset.
- Do not duplicate full player/team objects into all 902 games.
- The existing Openers matchup drawer remains unchanged for now.
- The standalone Matchups UI is designed first, then team-page integration, then a curated team-level drawer enhancement.
- Player-level injury reporting remains unavailable until a validated source is configured. Team-level CFBDepth Injury Impact is not a substitute for individual injury reports.

## Current daily automation

- LaunchAgent: `com.jim.ncaaf.marketupdate`
- Scheduled time: 8:00 AM local
- Thin launcher: `$HOME/Scripts/NCAAF/daily_market_update.sh`
- Runtime script: `/Users/jameslindesmith/NCAAF_AUTO/daily_market_update.sh`
- Email switch: `NCAAF_SEND_EMAIL=0`
- Publication switch: `NCAAF_AUTO_PUBLISH=0`

Deploy only approved manifest-listed source files. Never broadly sync the complete `scripts/` tree or use `--delete`.

## Current implementation order

1. Plan the standalone Matchups UI around the shared CFBDepth asset.
2. Connect the approved Matchups UI without changing the existing drawer.
3. Add CFBDepth team/player sections to individual team pages.
4. Select a small team-level subset for the existing matchup drawer.
5. Continue the canonical player-level injury-source project separately.

Use `CURRENT_PRIORITIES_2026_NCAAF_UPDATED_2026-08-06.md` as the authoritative roadmap.
