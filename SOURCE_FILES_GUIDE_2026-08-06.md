# ChatGPT Project Source Files Guide

_Last updated: 2026-08-06_

## Upload these as the authoritative project Source bundle

1. `PROJECT_ARCHITECTURE_2026-08-06.md`
   - Defines repository roles and the three-layer CFBDepth architecture.

2. `PROJECT_MAP_updated_2026-08-06.md`
   - Concise operating map and current implementation order.

3. `README_updated_2026-08-06.md`
   - Entry point, rebuild commands, and current checkpoint.

4. `CURRENT_PRIORITIES_2026_NCAAF_UPDATED_2026-08-06.md`
   - Authoritative working roadmap and milestone history.

5. `CFBDEPTH_DATA_ARCHITECTURE_2026-08-06.md`
   - Dedicated cross-page data-flow and integration decisions.

## Important repository files referenced by the Source bundle

These should remain in GitHub but do not all need to be uploaded as ChatGPT Project Sources:

### Import and mapping
- `scripts/research/import_cfbdepth_exports.py`
- `config/cfbdepth_player_school_crosswalk.csv`

### Research Matchups prototype
- `scripts/research/build_cfbdepth_matchups_enrichment.py`
- `data/research/cfbdepth_matchups/preview_ohio_state_at_texas.json`
- `data/audits/cfbdepth_matchups_enrichment_audit.json`

### Shared site layer
- `scripts/site/build_cfbdepth_team_asset.py`
- `data/site/cfbdepth_teams_2026.json`
- `data/audits/cfbdepth_team_asset_audit.json`

### Import audits
- `data/audits/cfbdepth_import_audit.json`
- `data/audits/cfbdepth_team_crosswalk_audit.csv`

The primary future implementation asset is `data/site/cfbdepth_teams_2026.json`.

## Optional supporting Sources

- `BETTING_SYSTEMS_NOTES.md`
- `ROOT_FILE_INVENTORY.txt`
- `WAR_ROOM_DATA_ARCHITECTURE.md`

## Do not use Project Sources as a backup

Do not upload every raw export, generated canonical CSV, large JSON asset, log, cache, virtual environment, HTML backup, or full runtime folder merely for preservation. GitHub is the code/data-artifact history. Project Sources should remain a small, current documentation set for continuity.

## Replace Source documents when these change

- repository roles or local paths,
- canonical build/publish workflow,
- major data-source architecture,
- public page ownership,
- current priorities,
- required validation gates,
- page integration decisions.
