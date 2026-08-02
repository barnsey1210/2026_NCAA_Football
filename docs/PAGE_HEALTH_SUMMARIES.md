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

The evaluator runs during public-site assembly. Page JavaScript only renders the precomputed record; page-specific scripts do not own freshness or coverage thresholds.

## Status semantics

| Status | Meaning |
|---|---|
| GREEN / Healthy | Critical artifacts exist, parse, meet required coverage, are within the fresh threshold, and pass critical checks. |
| YELLOW / Usable with warnings | The page remains usable, but data is aging, coverage is partial, a fallback is active, or a noncritical section is unavailable. |
| RED / Action required | A critical artifact is missing or malformed, maximum staleness is exceeded, critical coverage fails, or invalid current data would be displayed. |
| GRAY / Inactive or unavailable | The feature is legitimately inactive or not yet in season. GRAY is applied only after critical checks and cannot mask a failure. |

Fresh and maximum-stale ages are configured per page. A missing critical artifact is always RED. Stale current odds are always RED. Missing conference membership is always RED. Malformed betting prices or visible `nan` output are always RED.

## Page inventory and rules

All public pages are assembled by `scripts/site/build_public_site.py`; the builder/payload column identifies the page-specific upstream producer where one exists. Public URLs are unchanged.

| Page | Builder / payload producer | Public output | Prior status UI | Primary artifacts / timestamps | Main metrics | First-pass rules and missing behavior |
|---|---|---|---|---|---|---|
| Dashboard | Dashboard shell; matchups and betting activity builders | `index.html` | none | `matchups_view.json`, `betting_activity_view.json`; optional daily-run status, market history, betting angles, injuries | slate games, signals, market history, injury alerts, open wagers | RED for absent/malformed critical views or age over 48h; YELLOW after 18h or when daily-run status is absent. |
| Ratings | `scripts/site/build_ratings_view.py` | `ratings.html` | `#freshness` | `ratings_view.json`, ratings movement; snapshot/build timestamps | composite, SP+, FPI, TeamRankings, Brad Powers, movement | RED for composite below 138 or age over 120h; YELLOW for a partial component source or age over 48h. Existing freshness content is absorbed rather than duplicated. |
| Openers | Openers shell; matchup and Odds builders | `openers.html` | none | `matchups_view.json`, `odds_screen_v2.json`; opener/source timestamps | games, spread openers, total openers, history, unmatched | RED for missing views or age over 48h; YELLOW after 18h or for partial spread, total, or history coverage. |
| Matchups | `scripts/site/build_matchups_view.py` | `matchups.html` | none | `matchups_view.json`; build and market timestamps | games, model spreads/totals, Five Factors, coaching, odds | RED when model spread coverage is absent or age exceeds 48h; YELLOW for partial advanced coverage or age over 18h. |
| Odds | `scripts/site/build_odds_screen_v2.py`, `build_odds_futures_v2.py` | `odds.html` | `#oddsStatus` | `odds_screen_v2.json`, `odds_futures_v2.json`; provider/page timestamps | games, spreads, totals, moneylines, books, unavailable | RED when current quotes exceed 24h; YELLOW for partial coverage, fallback/aging data, or age over 8h. Stale current quotes can never be GREEN. |
| Schedule | `scripts/site/build_schedule_live_enrichment.py`; persistent schedule builder when installed | `schedule.html` | none | `schedule_live_enrichment.json`, `matchups_view.json`; build/kickoff timestamps | games, kickoffs, projections, odds, results, duplicates | RED for missing projections, duplicates, or age over 48h; YELLOW when market coverage is unavailable/partial or age exceeds 18h. |
| Futures | `scripts/site/build_futures_view.py` | `futures.html` | `#marketStatus` | `futures_view.json`; model/provider/build timestamps | teams, win totals, conference titles, playoff, national title, books | RED over 72h; YELLOW for non-passing market QA, stale sections, or age over 24h. Existing market status is mapped into the shared strip. |
| Conferences | `scripts/site/build_conference_workspace.py` | `conferences.html` | none | `conference_workspace.json`; build timestamp | conferences, assigned teams, missing, duplicates, title simulations/markets | RED unless all 10 conferences and 136 assigned FBS teams are present with no duplicates, or over 120h; YELLOW after 48h or for partial noncritical markets. |
| Playoff | Playoff shell and playoff model producer | `playoff.html` | none | `playoff_model_2026.json`; simulation/input timestamps | simulations, teams, playoff/title probabilities, excluded teams | Critical failures remain RED. Before configured in-season activation, otherwise valid data is GRAY. After activation partial coverage is YELLOW and maximum staleness is RED. |
| Simulations | Simulations shell; playoff and conference model producers | `simulations.html` | none | `playoff_model_2026.json`, `conference_workspace.json`; run/build timestamps | simulations, teams, playoff/title coverage, exclusions, conferences | RED for missing model output or age over 168h; YELLOW for partial coverage or age over 72h. |
| Betting | betting activity, matchup, signal, and history producers | `betting.html` | none | `betting_activity_view.json`, `matchups_view.json`; build timestamps | games, active signals, line moves, open wagers, duplicates, malformed | RED for malformed prices, visible `nan`, duplicate bet IDs, or age over 48h; YELLOW after 18h or for noncritical evidence gaps. |

## Provenance and unavailable data

Every page record lists its critical `source_artifacts`; expanded details show those paths and all warnings, failures, and legitimate unavailable reasons. File modification time is used only when an artifact has no recognized timestamp. The builder never invents timestamps, counts, or provider results.

Existing status blocks on Ratings, Futures, and Odds are hidden only after the shared record loads successfully. If the shared payload cannot load, the page retains its original status UI where present and inserts an explicit unavailable message.

## Development and release

```bash
python3 scripts/site/build_page_health_status.py
python3 -m unittest tests.test_page_health_status
```

Generated QA JSON/CSV and the browser payload are build outputs, not deployment-manifest source files. Runtime source changes are deployed only through `bash deploy/deploy_to_auto.sh`; publication remains separate.
