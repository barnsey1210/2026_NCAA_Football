# Page Health Summaries

The V2 site uses one shared, page-specific health strip below each page heading and before filters or primary content. It reports an accessible status label, the latest successful source timestamp, the health-artifact build time, three to six metrics, and expandable warnings and provenance.

The strip is operational QA. It does not call providers, repair data, or publish anything.

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
| Ratings | `scripts/site/build_ratings_view.py` | `ratings.html` | `#freshness` | `ratings_view.json`, ratings movement; snapshot/build timestamps | composite, SP+, FPI, TeamRankings, Brad Powers, movement | RED for composite below 138 or age over 120h; YELLOW for a partial component source or age over 48h. Existing freshness content is absorbed rather than duplicated. |
| Openers | Openers shell; matchup and Odds builders | `openers.html` | none | `matchups_view.json`, `odds_screen_v2.json`; opener/source timestamps | games, spread openers, total openers, history, unmatched | RED for missing views or age over 48h; YELLOW after 18h or for partial spread, total, or history coverage. |
| Matchups | `scripts/site/build_matchups_view.py` | `matchups.html` | none | `matchups_view.json`; build and market timestamps | games, model spread/total coverage, Five Factors, coaching, odds, injury state | RED when model spread coverage is absent or age exceeds 48h; YELLOW for partial advanced coverage or age over 18h. Unreleased injuries do not lower page health. |
| Odds | `scripts/site/build_odds_screen_v2.py`, `build_odds_futures_v2.py` | `odds.html` | `#oddsStatus` | `odds_screen_v2.json`, `odds_futures_v2.json`; provider/page timestamps | games, spreads, totals, moneylines, books, unavailable | RED when current quotes exceed 24h; YELLOW for partial coverage, fallback/aging data, or age over 8h. Stale current quotes can never be GREEN. |
| Schedule | `scripts/site/build_schedule_live_enrichment.py`; persistent schedule builder when installed | `schedule.html` | none | `schedule_live_enrichment.json`, `matchups_view.json`; build/kickoff timestamps | games, kickoffs, projections, odds, results/integrity, injury state | RED for missing projections, duplicates, or age over 48h; YELLOW when market coverage is unavailable/partial or age exceeds 18h. Unreleased injuries do not lower page health. |
| Futures | `scripts/site/build_futures_view.py` | `futures.html` | `#marketStatus` | `futures_view.json`; model/provider/build timestamps | teams, win totals, conference titles, playoff, national title, books | RED over 72h; YELLOW for non-passing market QA, stale sections, or age over 24h. Existing market status is mapped into the shared strip. |
| Conferences | `scripts/site/build_conference_workspace.py` | `conferences.html` | none | `conference_workspace.json`; build timestamp | conferences, assigned teams, missing, duplicates, title simulations/markets | RED unless all 10 conferences and 136 assigned FBS teams are present with no duplicates, or over 120h; YELLOW after 48h or for partial noncritical markets. |
| Playoff | Playoff shell and playoff model producer | `playoff.html` | none | `playoff_model_2026.json`; simulation/input timestamps | simulations, teams, playoff/title probabilities, excluded teams | Populated simulation or market data is evaluated regardless of date. GRAY requires an explicit inactive/not-released source with no usable data. Partial coverage is YELLOW and maximum staleness is RED. |
| Simulations | Simulations shell; playoff and conference model producers | `simulations.html` | none | `playoff_model_2026.json`, `conference_workspace.json`; run/build timestamps | simulations, teams, playoff/title coverage, exclusions, conferences | RED for missing model output or age over 168h; YELLOW for partial coverage or age over 72h. |
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

## Development and release

```bash
python3 scripts/site/build_page_health_status.py
python3 -m unittest tests.test_page_health_status
```

Generated QA JSON/CSV and the browser payload are build outputs, not deployment-manifest source files. Runtime source changes are deployed only through `bash deploy/deploy_to_auto.sh`; publication remains separate.
