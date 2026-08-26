#!/usr/bin/env bash
set -euo pipefail

RUNTIME_ROOT="/Users/jameslindesmith/NCAAF_AUTO"
DAILY_ENV="/Users/jameslindesmith/.config/ncaaf/daily.env"

[[ -d "$RUNTIME_ROOT" ]] || { echo "missing runtime: $RUNTIME_ROOT" >&2; exit 1; }

set -a
[[ -f "$DAILY_ENV" ]] && source "$DAILY_ENV"
set +a

# Reuse the protected CFBD credential convention without placing it in the
# LaunchAgent definition or logs. The watcher still fails closed when absent.
if [[ -z "${CFBD_API_KEY:-}" ]]; then
  CFBD_API_KEY="$(
    security find-generic-password \
      -a "$USER" \
      -s CFBD_API_KEY \
      -w 2>/dev/null || true
  )"
  export CFBD_API_KEY
fi

cd "$RUNTIME_ROOT"
exec /usr/bin/python3 scripts/war_room/run_cfbd_final_watcher.py \
  --trigger launchagent
