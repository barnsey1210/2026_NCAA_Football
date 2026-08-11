# 2026 NCAA Football Project

_Last updated: 2026-08-11_

## Start here

| Role | Path |
|---|---|
| Main source repository | `/Users/jameslindesmith/NCAAF_MAIN_REPO` |
| Runtime workspace | `/Users/jameslindesmith/NCAAF_AUTO` |
| Manual control repository | `/Users/jameslindesmith/NCAAF_CONTROL` |
| Public deployment repository | `/Users/jameslindesmith/Sites/NCAAF_SITE` |

GitHub: `barnsey1210/2026_NCAA_Football`

Canonical V2 owns public output. Commit normal source changes to `NCAAF_MAIN_REPO`, deploy only reviewed manifest-listed files to the runtime workspace, validate generated output, and publish explicitly.

## Current CFBDepth checkpoint

The official CFBDepth export pipeline is established.

- 15 official CSV exports archived
- 7 team datasets imported
- 12,381 player rows mapped
- 140 teams with player data
- all 138 site teams covered
- 1,110 team-position groups
- zero warnings

Primary shared site asset:

`data/site/cfbdepth_teams_2026.json`

This asset is intended to feed the standalone Matchups page, individual team pages, and later a small curated team-level enhancement to the existing matchup drawer. The drawer is currently unchanged.

## Rebuild commands

Import canonical CFBDepth data:

```bash
python3 scripts/research/import_cfbdepth_exports.py \
  --raw-dir data/raw/cfbdepth/2026-08-05 \
  --repo-root . \
  --as-of 2026-08-05
```

Build the research matchup preview:

```bash
python3 scripts/research/build_cfbdepth_matchups_enrichment.py \
  --repo-root . \
  --as-of 2026-08-05 \
  --away "Ohio State" \
  --home "Texas"
```

Build the shared team asset:

```bash
python3 scripts/site/build_cfbdepth_team_asset.py \
  --repo-root . \
  --as-of 2026-08-05
```

## Important boundaries

- Public pages read canonical/site assets, not raw CFBDepth exports.
- Full player/team data is not duplicated across all 902 games.
- Team-level Injury Impact is not individual injury reporting.
- The legacy public-page injury/depth pipeline remains isolated.
- The standalone Matchups UI should be designed before visible integration.

## Current implementation order

1. Plan standalone Matchups UI.
2. Connect Matchups to the shared CFBDepth asset.
3. Add CFBDepth data to individual team pages.
4. Select a lightweight team-level subset for the existing matchup drawer.

## Documentation hierarchy

1. `PROJECT_ARCHITECTURE_2026-08-06.md`
2. `CURRENT_PRIORITIES_2026_NCAAF_UPDATED_2026-08-06.md`
3. `CFBDEPTH_DATA_ARCHITECTURE_2026-08-06.md`
4. `PROJECT_MAP_updated_2026-08-06.md`
5. `README_updated_2026-08-06.md`
