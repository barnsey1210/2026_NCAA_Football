# Page Health Summaries

The V2 site uses one shared, page-specific health strip below each page heading and before filters or primary content. It reports an accessible status label, the latest successful source timestamp, the health-artifact build time, three to six metrics, and expandable warnings and provenance.

The strip measures **business readiness**, not merely whether a script exited successfully. A technically successful build can still be YELLOW or RED when the page is missing a dataset required for its intended decision-making use. It does not call providers, repair data, or publish anything.

Metrics are classified in the registry as:

- **Core metrics:** required for GREEN. Missing core data is RED when the page cannot perform its primary job; partial core coverage is normally YELLOW when the page remains usable.
- **Optional metrics:** useful context that normally does not reduce a page below GREEN unless its registry rule explicitly makes it health-affecting.
- **Future metrics:** planned checks documented for later implementation. They never affect current status.

This classification is metadata on the existing page registry and does not introduce another evaluator or orchestration path.

## Shared architecture

- Registry and thresholds: `config/page_health_registry.json`
- Evaluator: `scripts/site/build_page_health_status.py`
- QA artifacts: `data/qa/page_health_status.json` and `data/qa/page_health_status_details.csv`
- Browser payload: `data/site/page_health_status.json`
- Renderer and styles: `page_health.js` and `page_health.css`
- Public assembly: `scripts/site/build_public_site.py`
- Publication validation: `scripts/publish/check_public_site.py`

The evaluator runs synchronously at the start of `scripts/site/build_public_site.py`; its checked subprocess must succeed before any public page is assembled. In the normal daily path, page-specific source stages finish through Odds payloads at stage 170, followed by site build at stage 190, validation at stage 200, and publication at stage 210. The publisher also rebuilds page-specific inputs before calling this same public builder and validating its output. There is no second page-health orchestration path, and a failed health build cannot silently reuse an older artifact.

## Status semantics

| Status | Meaning |
|---|---|
| GREEN / Healthy | Critical artifacts exist, parse, meet required coverage, are within the fresh threshold, and pass critical checks. |
| YELLOW / Usable with warnings | The page remains usable, but data is aging, coverage is partial, a fallback is active, or a noncritical section is unavailable. |
| RED / Action required | A critical artifact is missing or malformed, maximum staleness is exceeded, critical coverage fails, or invalid current data would be displayed. |
| GRAY / Inactive or unavailable | The source explicitly reports that the feature or market is not released/open, or the domain is intentionally inactive. Available data is always evaluated normally; a calendar date alone cannot make a page GRAY or conceal a failure. |

Fresh and maximum-stale ages are configured per page. A missing critical artifact is always RED. Stale current odds are always RED. Missing conference membership is always RED. Malformed betting prices or visible `nan` output are always RED.

## Page inventory and rules

All public pages are assembled by `scripts/site/build_public_site.py`; the builder/payload column identifies the page-specific upstream producer where one exists. Public URLs are unchanged.

| Page | Builder / payload producer | Public output | Prior status UI | Primary artifacts / timestamps | Main metrics | First-pass rules and missing behavior |
|---|---|---|---|---|---|---|
| Dashboard | Dashboard shell; matchups and betting activity builders | `index.html` | none | `matchups_view.json`, `betting_activity_view.json`; optional last-completed daily-run status, market history, betting angles, injuries | slate games, signals, market history, injury state, open wagers, last completed run | RED for absent/malformed critical views or age over 48h; YELLOW after 18h or when last-completed-run status is absent. Unreleased injuries do not lower page health. |
| Ratings | `scripts/site/build_ratings_view.py` | `ratings.html` | `#freshness` | `ratings_view.json`, `matchups_view.json`, ratings movement; snapshot/build timestamps | composite; SP+, FPI, TeamRankings, Brad Powers; Market-Derived Ratings; offense/defense; movement; variance | GREEN requires all named datasets. Market-Derived Ratings remain a separate required dataset and are never included in the composite. Missing core datasets are RED; partial source/team coverage is YELLOW. Existing freshness content is preserved. |
| Openers | Openers shell; matchup and Odds builders | `openers.html` | none | `matchups_view.json`, `odds_screen_v2.json`; opener/source timestamps | opener coverage, retained history, exact game mapping, current market freshness | Uses the existing Shadow QA rather than duplicating projection health. RED for missing/malformed views or maximum staleness; YELLOW for partial opener/history coverage or mapping gaps. |
| Matchups | `scripts/site/build_matchups_view.py` | `matchups.html` | none | `matchups_view.json`; build and market timestamps | games, model spread/total coverage, Five Factors, coaching, odds, injury state | RED when model spread coverage is absent or age exceeds 48h; YELLOW for partial advanced coverage or age over 18h. Unreleased injuries do not lower page health. |
| Odds | `scripts/site/build_odds_screen_v2.py`, `build_odds_futures_v2.py` | `odds.html` | `#oddsStatus` | `odds_screen_v2.json`, `odds_futures_v2.json`; provider/page timestamps | games, spreads, totals, moneylines, books, unavailable | GREEN below 24h; YELLOW from 24h through 48h; RED beyond 48h. Malformed odds, mapping failures, missing critical artifacts, and stale data presented as current are RED. |
| Schedule | `scripts/site/build_schedule_live_enrichment.py`; persistent schedule builder when installed | `schedule.html` | none | `schedule_live_enrichment.json`, `matchups_view.json`; build/kickoff timestamps | games, kickoffs, projections, odds, results/integrity, injury state | RED for missing projections, duplicates, or age over 48h; YELLOW when market coverage is unavailable/partial or age exceeds 18h. Unreleased injuries do not lower page health. |
| Futures | `scripts/site/build_futures_view.py` | `futures.html` | `#marketStatus` | `futures_view.json`; model/provider/build timestamps | team coverage, win totals, conference titles, playoff, national title, books | GREEN requires all four market categories, no missing team-market coverage, and sportsbook data below 24h. YELLOW covers labeled stale data, missing teams, or partial sportsbook coverage. RED covers critical failure, widespread missing markets, malformed prices, or stale prices presented as current. |
| Conferences | `scripts/site/build_conference_workspace.py` | `conferences.html` | none | `conference_workspace.json`, `futures_view.json`; build/provider timestamps | memberships, eligibility/integrity, current overall and conference records, title simulations and markets | GREEN requires 10 conferences, 136 unique assigned teams, complete current records, current simulations, and current conference markets. Missing/duplicate memberships remain RED; partial or stale simulation/market coverage is YELLOW. |
| Playoff | Playoff shell and playoff model producer | `playoff.html` | none | `playoff_model_2026.json`, `ratings_view.json`, `futures_view.json`; simulation/input/provider timestamps | eligible teams, simulations, playoff prices, dependency freshness | GREEN requires eligible-team coverage, current simulation output, and playoff prices below 24h. Newer ratings than the simulation produces YELLOW even if elapsed age alone looks acceptable. GRAY still requires explicit inactive/not-released state with no usable data. |
| Simulations | Simulations shell; playoff and conference model producers | `simulations.html` | none | `playoff_model_2026.json`, `conference_workspace.json`, latest completed daily-run status | run completion, teams, playoff/title coverage, conferences | GREEN means simulation output completed during the latest successful daily run. YELLOW means usable output exists but was not produced during that run, or the completed-run record is unavailable. RED means the simulation stage failed or required output is missing. |
| Betting | betting activity, matchup, signal, and history producers | `betting.html` | none | `betting_activity_view.json`, `matchups_view.json`; build timestamps | games, active signals, line moves, open wagers, duplicates, malformed | RED for malformed prices, visible `nan`, duplicate bet IDs, or age over 48h; YELLOW after 18h or for noncritical evidence gaps. |

## Provenance and unavailable data

Every page record lists its critical `source_artifacts`; expanded details show those paths and all warnings, failures, and legitimate unavailable reasons. File modification time is used only when an artifact has no recognized timestamp. The builder never invents timestamps, counts, or provider results.

Injury availability is classified separately:

- **No reports released:** no raw or normalized CFBDepth report data exists. This is GRAY/inactive for the injury subsection and does not make Dashboard, Matchups, or Schedule YELLOW.
- **No injuries found:** the source produced current data but no actionable injury rows. This is a healthy empty result.
- **Source failed:** an error row exists, or raw report data exists without its required normalized output. This is RED on pages that present injury context.
- **Active reports stale:** active alerts exceed the maximum injury age. This is RED; aging but not maximally stale active output is YELLOW.

`data/control/daily_run_status.json` is interpreted by its recorded state. A final record is labeled **Last completed run** and uses `finished_at_utc`; it is never described as the current in-progress run. If the file actually contains `overall_result: RUNNING`, the metric instead says **Current run at build** and uses `started_at_utc`. This distinction matters because the health payload is a timestamped snapshot created before publication finishes.

Existing status blocks on Ratings, Futures, and Odds are hidden only after the shared record loads successfully. If the shared payload cannot load, the page retains its original status UI where present and inserts an explicit unavailable message.

## Future planned page health

The Team Page is intentionally outside the current 11-page registry. A Team Page health summary will be added after the Team Dashboard redesign is complete, when its core business-readiness contract is stable. Until then, its absence is planned scope rather than an inactive or failed health record.

## Development and release

```bash
python3 scripts/site/build_page_health_status.py
python3 -m unittest tests.test_page_health_status
```

Generated QA JSON/CSV and the browser payload are build outputs, not deployment-manifest source files. Runtime source changes are deployed only through `bash deploy/deploy_to_auto.sh`; publication remains separate.
