# 2026 NCAAF Project — Master Handoff

Last Updated:
2026-08-19

Purpose:
Primary context document for future ChatGPT/Codex sessions.

---

# Project Mission

The 2026 NCAAF project is a production college football intelligence platform combining:

- team ratings
- game projections
- betting markets
- historical market research
- simulations
- matchup analysis
- automated daily refresh pipelines

The goal is not simply displaying data. The goal is building a research-driven betting decision system.

---

# Current Repository Architecture

## Canonical Repository

NCAAF_MAIN_REPO

Purpose:
Authoritative production source.

Contains:
- production code
- site builders
- data contracts
- documentation
- publishing workflow

---

## Operational Repository

NCAAF_AUTO

Purpose:
Runtime automation workspace.

Responsible for:
- scheduled refreshes
- data pulls
- operational execution

---

## Control Repository

NCAAF_CONTROL

Purpose:
Guarded refresh workflows and acceptance tooling.

---

# Current Production Site Architecture

## Home

Route:

index.html

Role:

Primary homepage.

IMPORTANT:

Home is independent.

The Command Center does NOT replace Home.

Do not inject the Command Center into Home unless explicitly requested.

Home ownership:

scripts/site/build_war_room_home.py

---

# War Room Command Center V1

Route:

war-room.html

Product name:

War Room Command Center

Role:

Standalone operational dashboard.

Purpose:

Provide a market/projection command interface.

Ownership:

Page:
scripts/site/build_war_room_page.py

Health artifact:
scripts/war_room/build_war_room_health.py

Market matrix:
scripts/war_room/build_war_room_market_matrix.py

Data:

data/site/war_room_health.json

data/site/war_room_market_matrix.json

Status:

Implemented.

Production publication wiring exists.

Remaining:
- navigation exposure
- live season acceptance
- operational monitoring

---

# Navigation Rule

Current decision:

Keep URL:

war-room.html

Navigation label:

Command Center

Do not rename route.

Do not replace Home.

---

# Projection Architecture

## Ratings Page Composite

Production rating page:

SP+
25%

FPI
25%

TeamRankings
25%

Sagarin
25%

This is separate from game prediction models.

---

## Standard Spread Model

Weights:

SP+ 20%
FPI 20%
TeamRankings 20%
Sagarin Rating 20%
DRatings 20%

---

## Standard Total Model

SP+
40%

Massey Dual
40%

Sagarin Total
20%

---

## Shadow Spread Model

SP+ Shadow
50%

Sagarin Shadow
50%

---

# Market Architecture

Historical and production market source:

The Odds API

Previous SGO architecture has been retired.

Do not reintroduce SGO assumptions.

---

# Refresh Architecture

Current workflow profiles:

status
market
openers
postgame
full

Manual refreshes publish automatically.

Daily pipeline remains the batch backbone.

Fast refresh architecture:
Fast refresh is an operational acceleration layer.
It does not replace the daily batch pipeline.
Purpose:
rapid market updates for operator workflows.

Current Command Center dependency:

fast market snapshot artifacts.

---

# Completed Major Milestones

## Completed

- Ratings architecture
- Projection pipeline foundation
- Matchup architecture
- Odds migration to The Odds API
- War Room shell
- Standalone Command Center V1
- Projection documentation reconciliation
- Public page data contract registration

# Current Release State

Command Center V1 release preparation is complete.

Current state:

- Architecture documented
- Public data contract registered
- Standalone page exists
- Production builders identified
- Validation path exists

Pending:

- Commit production release files
- Publish war-room.html
- Add Command Center navigation entry
- Validate live deployment
- Complete Codex architecture audit

# Release Workflow

Production changes should follow:

1. Make targeted changes
2. Validate locally
3. Commit bounded release group
4. Push canonical repository
5. Run publish workflow
6. Verify production artifacts

Avoid mixing:
- research archives
- prototypes
- generated artifacts
- production releases

---

# Current Immediate Priorities

1. Complete Command Center production release

Tasks:

- commit production files
- publish route
- add navigation link
- validate live deployment

---

2. Verify automation

Confirm:

- daily refresh builds Command Center
- fast market artifacts handled correctly
- no stale provider references remain

---

3. Codex architecture audit

After release:

Review:

- docs vs code
- builders
- contracts
- automation
- stale references
- unused prototypes

---

# Known Risks

## Generated snapshots

War Room JSON files are generated artifacts.

They are not proof of live freshness.

Before major publication:

- rebuild artifacts
- validate timestamps
- publish

---

## Legacy files

Many prototypes/backups exist.

Do not delete aggressively.

Classify first.

---

# Rules For Future Work

1. Do not modify Home when working on Command Center.
2. Do not merge rating composites with prediction models.
3. Do not restore SGO assumptions.
4. Do not use git add .
5. Use targeted commits.
6. Preserve historical research formulas exactly.
7. Treat documentation as architecture contracts.

---

# Next Chat Instructions

When continuing this project:

First read:

docs/CHATGPT_MASTER_HANDOFF_2026_NCAAF.md

Then read only the specific supporting docs needed.