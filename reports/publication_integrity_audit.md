# Publication Integrity Audit

Date: 2026-08-20  
Repository: `NCAAF_MAIN_REPO`

## Executive finding

The public build was authoritative in practice, but the GitHub Pages root HTML
files were not promoted from that final build as one set. Before this repair,
only Home was guaranteed to have root/build parity and Odds had an early,
page-specific copy. The other root pages could therefore remain older than
`build/public_site`, and even Odds could diverge after the later shared-shell
pass.

The deterministic ownership boundary is now:

`source/template -> canonical builder/build_public_site -> final shared shell -> build/public_site -> exact root-page promotion -> parity audit`

The root HTML files are publication artifacts. GitHub Pages must receive those
exact bytes, not rebuild or select an older page source during publication.

## A. Active page ownership

| Public page | Canonical source | Canonical builder(s), in order | Build artifact | Final published artifact | Duplicate-writer note |
|---|---|---|---|---|---|
| `index.html` | Embedded locked `PAGE` template in `scripts/site/build_war_room_home.py` | `build_war_room_home.py`, then `apply_shared_war_room_shell.py` | `build/public_site/index.html` | root `index.html` | The home builder intentionally writes root and build; the shell also writes both. Both outputs are parity-checked. |
| `ratings.html` | `ratings_v2.html` | `build_public_site.py` transform, then shared shell | `build/public_site/ratings.html` | root `ratings.html` | Legacy/manual patch scripts exist, but are not canonical daily owners. |
| `odds.html` | `odds_v2.html` | `build_public_site.py` transform, then shared shell | `build/public_site/odds.html` | root `odds.html` | The former early Odds-only root copy was a second promotion point and was removed. |
| `openers.html` | root `openers.html` source plus shared `matchup_workspace.js` | `build_public_site.py` normalization, compatibility sync, then shared shell | `build/public_site/openers.html` | root `openers.html` | Several one-time Openers patch utilities can write the root source; none is part of canonical publication. |
| `matchups.html` | root `matchups.html` | `build_public_site.py` transform, then shared shell | `build/public_site/matchups.html` | root `matchups.html` | Historical matchup builders/patchers remain available but are not publication owners. |
| `futures.html` | `futures_v2.html` | `build_public_site.py` transform, then shared shell | `build/public_site/futures.html` | root `futures.html` | Root is now promoted only after the final shell pass. |
| `betting.html` | `betting_v2.html` | `build_public_site.py` transform, then shared shell | `build/public_site/betting.html` | root `betting.html` | Historical betting injectors can modify source pages manually; they are outside the canonical build. |
| `schedule.html` | root `schedule.html` compatibility source | `build_public_site.py` transform/compatibility pass, then shared shell | `build/public_site/schedule.html` | root `schedule.html` | `build_schedule_persistent.py` is not an active builder in `build_public_site.py`. |
| `conferences.html` | current conference workspace/matchup data and the page template in `build_conference_logo_schedule.py` | `build_conference_logo_schedule.py`, then shared shell | `build/public_site/conferences.html` | root `conferences.html` | The conference builder writes root and build; final promotion makes the shell-complete build authoritative. |
| `war-room.html` | Embedded `HTML` template in `build_war_room_page.py` | `build_war_room_page.py`, build copy/cache bust, then shared shell | `build/public_site/war-room.html` | root `war-room.html` | `build_war_room_home.py` does **not** own this page; it owns Home. The separate fast bundle is a bounded publication snapshot, not another template owner. |

## B. Writers and duplicate ownership

### Active production writers

- `scripts/site/build_public_site.py`: orchestration, page transforms, final
  root promotion.
- `scripts/site/build_war_room_home.py`: canonical locked Home builder; writes
  root and public-build Home.
- `scripts/site/build_war_room_page.py`: canonical standalone Command Center
  builder; writes root `war-room.html` before it is copied into the public
  build.
- `scripts/site/build_conference_logo_schedule.py`: builds Conferences and
  writes both root and public-build copies.
- `scripts/site/apply_shared_war_room_shell.py`: final shared-shell writer for
  public pages and root Home.
- `scripts/publish/publish_site.sh`: copies allowlisted files from the validated
  runtime public build into MAIN for commit/push; it is a synchronizer, not a
  page renderer.

### Other code capable of writing these HTML files

Repository search also finds older/manual utilities such as the Openers
cleanup/layout scripts under `scripts/site/`, historical market-presentation
injectors, root `build_matchup_page.py`, older `site/` injectors, preview
builders, and the legacy top-level `publish/publish_site.sh`. These remain
potential manual writers, but they are not invoked by the canonical
`site_build` path. They should not be run as publication owners. Backups,
previews, acceptance snapshots, and files below `archive/`, `research/`, and
`data/control/acceptance_dry_runs/` are evidence only.

The daily configuration currently invokes the Home, Command Center, and shared
shell builders around `build_public_site.py` as well as indirectly inside it.
That is redundant execution, but the canonical build invocation itself now
finishes with exact root promotion and the parity audit detects any later
divergence. Removing redundant stage commands is a separate controller change
and was intentionally not included in this bounded repair.

## C. Pre-repair root/build comparison

Observed before the synchronization change:

| Page | Result |
|---|---|
| `index.html` | MATCH |
| `ratings.html` | DIFF |
| `odds.html` | DIFF |
| `openers.html` | DIFF |
| `matchups.html` | DIFF |
| `futures.html` | DIFF |
| `betting.html` | DIFF |
| `schedule.html` | DIFF |
| `conferences.html` | DIFF |
| `war-room.html` | DIFF |

The mismatches were not evidence that the newer public build was wrong. They
showed that the final build was not promoted to the root GitHub Pages artifacts
as one atomic logical set.

## D. Command Center versus fast publication bundle

`war-room.html` and `build/war_room_public/war-room.html` served different
stages:

- root `war-room.html` is the canonical repository publication artifact;
- `build/public_site/war-room.html` is the full-build artifact;
- `build/war_room_public/war-room.html` is a temporary three-file fast-market
  publication bundle produced for targeted Command Center refreshes.

The fast bundle may legitimately differ because it captures a prior build
version/cache-busting state. It must be rebuilt and validated by the fast
publication wrapper before use. It is not an alternate source template and
must not overwrite full-build ownership outside the bounded fast publisher.

The repository architecture documents consistently identify
`build_war_room_page.py` as the owner of standalone `war-room.html` and
`build_war_room_home.py` as the owner of Home `index.html`. Therefore the call
to `build_war_room_page.py` inside `build_public_site.py` is required canonical
generation, not the duplicate to remove.

## Repair and regression control

- Removed the early Odds-only root synchronization.
- Added one final root promotion step after all page builders, compatibility
  passes, Home generation, and shared-shell application.
- The final promotion covers all ten audited root/public pages.
- Added `scripts/audit/audit_publication_parity.py`; missing or byte-different
  pages fail with a non-zero exit status and include short SHA-256 identifiers.
- No page design, model, provider, market, or data-contract behavior changed.

