# 2026 NCAAF Project Map

## Current rule
Root-level files are still the active working files unless noted otherwise. Do not move or delete them until paths are updated and tested.

## Website files
- index.html — active website file currently uploaded to GitHub.
- index_test.html — local test build before publishing.
- index_auto_market.html — auto-generated market version / backup output.
- site/index.html — organized copy of current website file.
- site/index_test.html — organized copy of current test file.
- site/backups/ — backup HTML versions.

## Main workbook
- 2026_NCAA _Season.xlsm — active source workbook.
- workbook/2026_NCAA _Season.xlsm — organized copy.

## Market data files
- market_win_totals_import.csv — current win total import file.
- market_conference_futures_import.csv — current conference futures import file.
- market_win_totals_history.csv — daily win total history log.
- market_conference_futures_history.csv — daily conference futures history log.
- market_win_totals_movement.csv — derived win total movement file.
- market_conference_futures_movement.csv — derived conference futures movement file.
- market_futures_export.xlsx — generated market workbook used by site build.
- market_movement_export.xlsx — generated movement workbook.

## Returning production
- returning_production_2026_raw.txt — pasted ESPN returning production table.
- returning_production_2026_import.csv — cleaned returning production import.
- index.html currently embeds returning production in team dashboard Ratings card.

## Main scripts
- build_site_from_workbook_safe_with_movement.py — builds dashboard HTML from workbook/market/movement data.
- build_market_futures_safe.py — builds market futures export workbook.
- append_market_history.py — appends daily market snapshots and creates movement files.
- pull_actionnetwork_win_totals_api.py — pulls Action Network win totals.
- pull_actionnetwork_conference_futures_api.py — pulls Action Network conference futures.
- pull_fanduel_win_totals.py — pulls FanDuel win totals.
- pull_bettingpros_caesars_win_totals.py — pulls Caesars win totals from BettingPros API.
- pull_cfbd_2026_data.py — pulls CFBD enrichment data.

## Automation
- ~/Library/LaunchAgents/com.jim.ncaaf.marketupdate.plist — launchd schedule.
- ~/Scripts/NCAAF/daily_market_update.sh — daily automation shell script.
- ~/Scripts/NCAAF/daily_market_update.log — daily automation log.

## Organized copies
- data/import/ — copied current import CSVs.
- data/history/ — copied history/movement CSVs.
- data/exports/ — copied generated Excel exports.
- scripts/pulls/ — copied pull scripts.
- scripts/build/ — copied build scripts.
- logs/ — copied automation logs.

## Do not touch yet
- Root-level active CSVs.
- Root-level active Python scripts.
- Root-level index.html.
- Daily automation paths.

## Website pages currently active
- Home
- Season Schedule
- Results Center
- Rankings
- Futures Market
- Simulations
- Conferences
- Coach Trends
- Betting
- Team dashboards