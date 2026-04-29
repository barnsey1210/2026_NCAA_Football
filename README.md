# 2026 NCAAF Dashboard

## Main files
- site/index.html = current website file to upload to GitHub
- workbook/2026_NCAA _Season.xlsm = main source workbook
- data/import/ = current CSV imports used by build scripts
- data/history/ = daily odds/history/movement logs
- data/exports/ = generated Excel exports
- scripts/pulls/ = scripts that pull odds/data
- scripts/build/ = scripts that merge/build dashboard files
- logs/ = automation logs

## Daily automation
Daily pull currently runs from ~/Scripts/NCAAF or ~/NCAAF_AUTO.
Keep this folder as the organized project copy. Update automation paths later only after everything is stable.

## Publishing workflow
1. Pull/update market data
2. Append history
3. Build market export
4. Build test HTML
5. Open site/index_test.html
6. If correct, copy to site/index.html and upload to GitHub

## Current caution
Root-level files are still the active working files. Do not move or delete them until script paths are updated and tested.
