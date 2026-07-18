#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PUBLISH_REPO="${NCAAF_PUBLISH_REPO:-/Users/jameslindesmith/Sites/NCAAF_SITE}"
MODE="${1:---check}"

cd "$ROOT"
python3 scripts/publish/check_index_before_publish.py
python3 scripts/audit/audit_game_projection_spreads.py
python3 scripts/audit/audit_page_payload_size.py
python3 scripts/site/build_postgame_shadow_updates.py
python3 scripts/site/build_ratings_view.py
python3 scripts/betting/build_betting_activity_view.py
python3 scripts/site/build_matchups_view.py
python3 scripts/site/build_futures_view.py
python3 scripts/site/build_conference_workspace.py
python3 scripts/site/build_public_site.py
python3 scripts/publish/check_public_site.py

if [ ! -d "$PUBLISH_REPO/.git" ]; then
  echo "FAIL: publication repository not found: $PUBLISH_REPO" >&2
  exit 1
fi

if [ -n "$(git -C "$PUBLISH_REPO" status --porcelain)" ]; then
  echo "FAIL: publication repository has uncommitted changes" >&2
  git -C "$PUBLISH_REPO" status --short
  exit 1
fi

if [ "$MODE" = "--check" ]; then
  echo "PASS: local site validated; publication repository is clean"
  exit 0
fi

if [ "$MODE" != "--publish" ] && [ "$MODE" != "--push" ]; then
  echo "Usage: $0 [--check|--publish|--push]" >&2
  exit 2
fi

stage_dir="$(mktemp -d "$PUBLISH_REPO/.site-stage.XXXXXX")"
trap 'rm -rf "$stage_dir"' EXIT
cp build/public_site/*.html "$stage_dir/"
mkdir -p "$stage_dir/data/bets" "$stage_dir/data/site" "$stage_dir/data/agents" "$PUBLISH_REPO/data/bets" "$PUBLISH_REPO/data/site" "$PUBLISH_REPO/data/agents"
for file in bets_enriched.csv betting_dashboard.json market_clv_match_audit.csv betting_performance_history.csv bet_closing_clv.csv bet_closing_clv_audit.csv; do
  [ -f "data/bets/$file" ] && cp "data/bets/$file" "$stage_dir/data/bets/$file"
done
for file in matchup_line_history.json matchups_view.json betting_activity_view.json futures_view.json conference_workspace.json postgame_shadow_updates.json ratings_view.json; do
  [ -f "data/site/$file" ] && cp "data/site/$file" "$stage_dir/data/site/$file"
done
[ -f data/agents/home_top_bets.json ] && cp data/agents/home_top_bets.json "$stage_dir/data/agents/home_top_bets.json"
for staged in "$stage_dir"/*.html; do mv "$staged" "$PUBLISH_REPO/$(basename "$staged")"; done
for staged in "$stage_dir"/data/bets/*; do
  [ -f "$staged" ] && mv "$staged" "$PUBLISH_REPO/data/bets/$(basename "$staged")"
done
for staged in "$stage_dir"/data/site/*; do
  [ -f "$staged" ] && mv "$staged" "$PUBLISH_REPO/data/site/$(basename "$staged")"
done
for staged in "$stage_dir"/data/agents/*; do
  [ -f "$staged" ] && mv "$staged" "$PUBLISH_REPO/data/agents/$(basename "$staged")"
done

git -C "$PUBLISH_REPO" add index.html dashboard.html openers.html matchups.html futures.html conferences.html betting.html team.html ratings.html simulations.html legacy.html v1.html matchup.html data/bets data/site data/agents
if git -C "$PUBLISH_REPO" diff --cached --quiet; then
  echo "No website changes to publish"
  exit 0
fi

git -C "$PUBLISH_REPO" diff --cached --check
git -C "$PUBLISH_REPO" commit -m "Daily NCAAF site update $(date +%Y-%m-%d)"

if [ "$MODE" = "--push" ]; then
  git -C "$PUBLISH_REPO" push
else
  echo "Committed locally; run $0 --push after review to publish"
fi
