#!/usr/bin/env bash
set -euo pipefail

RUNTIME_ROOT="/Users/jameslindesmith/NCAAF_AUTO"
DAILY_ENV="/Users/jameslindesmith/.config/ncaaf/daily.env"

set -a
[[ -f "$DAILY_ENV" ]] && source "$DAILY_ENV"
set +a

cd "$RUNTIME_ROOT"
exec /usr/bin/python3 scripts/war_room/run_massey_window_scheduler.py \
  --trigger launchagent
