# 2026 NCAAF Repository and Data Architecture

_Last synchronized: 2026-09-01_

## Authoritative locations

| Role | Path | Responsibility |
|---|---|---|
| Main source repository | `/Users/jameslindesmith/NCAAF_MAIN_REPO` | Approved source, documentation, canonical artifacts, tests, Git history |
| Runtime workspace | `/Users/jameslindesmith/NCAAF_AUTO` | Scheduled execution, live pulls, runtime state, logs, caches, generated output |
| Manual control repository | `/Users/jameslindesmith/NCAAF_CONTROL` | Guarded refresh, acceptance, rollback, audit-ledger tooling |
| Canonical publishing repository | `/Users/jameslindesmith/NCAAF_MAIN_REPO` | Receives allowlisted validated artifacts and publishes GitHub Pages from `main` |
| Legacy site checkout | `/Users/jameslindesmith/Sites/NCAAF_SITE` | Legacy only; not part of the canonical workflow |

Canonical V2 owns public site output. Runtime generates and validates; MAIN
preserves approved source and performs explicit publication. The current public
host is GitHub Pages. Planned migration is `barnseywr.com` on Cloudflare Pages,
with `www.barnseywr.com` redirecting to the apex and
`control.barnseywr.com` preserved for the authenticated controller/API. The
migration is not complete and must preserve/test CORS, origin, and Access
behavior before DNS cutover.

## Required workflow

1. Edit approved source files in `NCAAF_MAIN_REPO`.
2. Test and commit them there.
3. Deploy only reviewed manifest-listed files to `NCAAF_AUTO`.
4. Validate from the runtime workspace.
5. Generate runtime data and public artifacts.
6. Synchronize validated public assets into the canonical repository.
7. Publish explicitly.

Never run an unrestricted source-tree sync and never use `--delete`.

## CFBDepth three-layer architecture

### Layer 1 — raw archive

`data/raw/cfbdepth/2026-08-05/` stores the 15 official exports unchanged. Raw files are evidence and replay inputs; public pages must not read them directly.

### Layer 2 — canonical domain data

`scripts/research/import_cfbdepth_exports.py` builds deterministic canonical outputs:

- `data/canonical/cfbdepth_air_ratings_2026.csv`
- `data/canonical/cfbdepth_coaching_impacts_2026.csv`
- `data/canonical/cfbdepth_depth_grades_2026.csv`
- `data/canonical/cfbdepth_rotation_talent_2026.csv`
- `data/canonical/cfbdepth_team_injury_impact_2026.csv`
- `data/canonical/cfbdepth_offense_profile_2026.csv`
- `data/canonical/cfbdepth_defense_profile_2026.csv`
- `data/canonical/cfbdepth_players_2026.csv`
- `data/canonical/cfbdepth_position_groups_2026.csv`
- `data/canonical/cfbdepth_team_top_players_2026.json`

Mapping and audit artifacts:

- `config/cfbdepth_player_school_crosswalk.csv`
- `data/audits/cfbdepth_import_audit.json`
- `data/audits/cfbdepth_team_crosswalk_audit.csv`

Validated result: 12,381 mapped player rows, 140 player teams, 1,110 team-position groups, zero warnings.

### Layer 3 — shared site asset and page adapters

`scripts/site/build_cfbdepth_team_asset.py` builds:

- `data/site/cfbdepth_teams_2026.json`
- `data/audits/cfbdepth_team_asset_audit.json`

The shared asset stores each team once and is the reusable input for:

- the standalone Matchups page,
- individual team pages,
- a future curated team-level subset in the existing Openers matchup drawer,
- future betting-signal calculations.

Full team/player snapshots must not be copied into every one of the 902 game records. Page-specific builders should reference team names and include only calculated or curated fields needed by that page.

## Research matchup prototype

`scripts/research/build_cfbdepth_matchups_enrichment.py` creates a 140-team research payload and an Ohio State–Texas preview. It is research-only and does not render public HTML.

The preview contains full away/home snapshots and two 15-row unit-comparison arrays. These are raw CFBDepth rating differentials, not calibrated betting signals.

## Injury boundary

CFBDepth team-level Injury Impact is available as team context. It does not establish individual player injuries or prove that a team has no injuries.

The old June-era public-page injury/depth pipeline is isolated. Player-level injury reporting remains unavailable until a validated source and canonical injury contract are configured.

## Current UI integration rule

The existing matchup drawer remains untouched during initial Matchups UI planning. Integration order is:

1. standalone Matchups page,
2. individual team pages,
3. curated team-level drawer subset.
