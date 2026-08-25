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

export WAR_ROOM_PUBLIC_ORIGIN="${WAR_ROOM_PUBLIC_ORIGIN:-https://barnsey1210.github.io}"
cd "$RUNTIME_ROOT"
exec /usr/bin/python3 -m uvicorn \
  scripts.war_room.war_room_operator_api:app \
  --host 127.0.0.1 \
  --port 8787 \
  --no-proxy-headers
