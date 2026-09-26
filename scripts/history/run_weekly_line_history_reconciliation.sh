#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/../.."
python3 scripts/history/build_matchup_line_history_clean.py --full-reconcile
python3 scripts/site/inject_matchup_line_history.py --asset-only
