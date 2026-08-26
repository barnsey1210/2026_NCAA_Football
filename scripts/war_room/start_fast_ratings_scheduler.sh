#!/usr/bin/env bash
set -euo pipefail

RUNTIME_ROOT="/Users/jameslindesmith/NCAAF_AUTO"
DAILY_ENV="/Users/jameslindesmith/.config/ncaaf/daily.env"

[[ -d "$RUNTIME_ROOT" ]] || { echo "missing runtime: $RUNTIME_ROOT" >&2; exit 1; }

set -a
[[ -f "$DAILY_ENV" ]] && source "$DAILY_ENV"
set +a

cd "$RUNTIME_ROOT"
exec /usr/bin/python3 scripts/war_room/run_fast_ratings_scheduler.py \
  --trigger ratings-scheduler
