# CFBDepth Data Architecture — 2026 NCAAF

_Last updated: 2026-08-06_

## Decision

Canonical CFBDepth data is stored once, then exposed through a shared team-indexed site asset. Page builders pull only the fields needed for their interface.

The architecture must support three consumers:

1. standalone Matchups page,
2. individual team pages,
3. a future curated team-level subset in the existing matchup drawer.

Full player/team objects are not duplicated into all 902 game records.

## Data flow

```text
15 official CFBDepth CSV exports
  ↓
data/raw/cfbdepth/2026-08-05/
  ↓
scripts/research/import_cfbdepth_exports.py
  ↓
data/canonical/cfbdepth_*
  ↓
scripts/site/build_cfbdepth_team_asset.py
  ↓
data/site/cfbdepth_teams_2026.json
  ↓
Matchups page / team pages / curated drawer subset
```

Research-only matchup prototyping follows:

```text
canonical CFBDepth files
  ↓
scripts/research/build_cfbdepth_matchups_enrichment.py
  ↓
140-team enrichment payload
  + Ohio State–Texas v2 preview
```

## Validated coverage

- 15 official exports
- 7 team-level datasets
- 12,381 mapped player rows
- 140 teams with player data
- 138 of 138 site teams covered
- Idaho and UTRGV retained as non-site teams
- 1,110 team-position groups
- zero unmapped school codes
- zero warnings

## Canonical outputs

Team-level:

- AIR ratings
- coaching impacts
- depth grades
- rotation talent
- team Injury Impact
- offense profile
- defense profile

Player-level:

- unified player ratings
- position-group aggregates
- top-player summaries

## Shared asset contract

`data/site/cfbdepth_teams_2026.json` is the primary page-facing asset. Each team entry includes summary and detailed sections for team profiles, position groups, and top players.

Rules:

- store each team once,
- keep source/as-of metadata,
- preserve non-site teams but flag them,
- validate all 138 site-team mappings,
- produce deterministic output,
- do not render pages directly from raw exports.

## Page integration plan

### Standalone Matchups

Use the shared team asset for away/home context and a compact page-specific comparison payload for calculated unit matchups. Design the UI before connecting production rendering.

Likely sections:

- personnel overview,
- selected position-matchup edges,
- top impact players,
- expandable offense/defense and position-group detail.

### Team pages

Use the same shared team entry to add team profile, position-unit, and player sections without creating a second CFBDepth pipeline.

### Existing matchup drawer

Keep unchanged during initial Matchups work. Later consider only a small team-level subset such as AIR, depth, rotation, Injury Impact, and strongest/weakest units. Avoid full player tables.

## Injury limitation

CFBDepth team Injury Impact is aggregate team context. It is not a verified individual injury list and must not be interpreted as proof of zero injuries.

The legacy June-era public-page injury/depth pipeline is isolated. Player-level injury reporting remains unavailable until a validated source and canonical injury contract are configured.

## Key commits

- `ff79d95` — deterministic CFBDepth import audit
- `1835c27` — research CFBDepth matchup enrichment
- `e4110a8` — expanded matchup preview schema
- `b53bd3f` — shared CFBDepth team asset
