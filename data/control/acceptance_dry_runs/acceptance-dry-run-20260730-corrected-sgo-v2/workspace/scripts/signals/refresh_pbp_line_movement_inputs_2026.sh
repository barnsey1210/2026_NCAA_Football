#!/bin/bash
set -e

if [ -z "${1:-}" ]; then
  echo "Usage: $0 COMPLETED_WEEK"
  exit 2
fi

WEEK="$1"
cd "$(dirname "$0")/../.."

python3 scripts/research/pull_cfbd_pbp_history.py \
  --seasons 2026 \
  --through-week "$WEEK" \
  --refresh-week "$WEEK" \
  --refresh-season-aggregates \
  --max-calls 6

python3 scripts/research/build_pbp_tendency_history.py \
  --seasons 2026 \
  --output-dir data/research/pbp_history_2026

python3 scripts/research/build_drive_context_history.py \
  --seasons 2026 \
  --base data/research/pbp_history_2026/team_game_tendencies.csv \
  --output-dir data/research/drive_context_2026

python3 scripts/signals/build_pbp_line_movement_signals_2026.py
python3 scripts/signals/build_game_betting_angles_2026.py

echo "Refreshed 2026 PBP movement inputs through completed week $WEEK"
