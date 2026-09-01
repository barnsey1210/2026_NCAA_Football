#!/usr/bin/env bash
set -euo pipefail

RUNTIME_ROOT="/Users/jameslindesmith/NCAAF_AUTO"
DAILY_ENV="/Users/jameslindesmith/.config/ncaaf/daily.env"
CONTROL_ENV="/Users/jameslindesmith/.config/ncaaf/war_room_control.env"

[[ -d "$RUNTIME_ROOT" ]] || { echo "missing runtime: $RUNTIME_ROOT" >&2; exit 1; }

set -a
[[ -f "$DAILY_ENV" ]] && source "$DAILY_ENV"
[[ -f "$CONTROL_ENV" ]] && source "$CONTROL_ENV"
set +a

# Reuse the protected CFBD credential used by the daily workflow.
# Never persist the secret in Git or the LaunchAgent plist.
if [[ -z "${CFBD_API_KEY:-}" ]]; then
  CFBD_API_KEY="$(
    security find-generic-password \
      -a "$USER" \
      -s CFBD_API_KEY \
      -w 2>/dev/null || true
  )"
  export CFBD_API_KEY
fi

export WAR_ROOM_PUBLIC_ORIGIN="${WAR_ROOM_PUBLIC_ORIGIN:-https://barnsey1210.github.io}"
export WAR_ROOM_PUBLIC_ORIGINS="${WAR_ROOM_PUBLIC_ORIGINS:-https://barnsey1210.github.io,https://barnseywr.com}"
export WAR_ROOM_PAGES_ORIGIN="${WAR_ROOM_PAGES_ORIGIN:-}"
cd "$RUNTIME_ROOT"
exec /usr/bin/python3 -m uvicorn \
  scripts.war_room.war_room_operator_api:app \
  --host 127.0.0.1 \
  --port 8787 \
  --no-proxy-headers
