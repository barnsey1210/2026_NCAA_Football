#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PUBLISH_REPO="${NCAAF_PUBLISH_REPO:-/Users/jameslindesmith/Sites/NCAAF_SITE}"
MODE="${1:---check}"

cd "$ROOT"
# The canonical publication shell is V2. The former checker validates the
# embedded database in the legacy monolith and is intentionally not used here.
python3 scripts/audit/audit_canonical_v2_index.py index.html
python3 scripts/audit/audit_game_projection_spreads.py
python3 scripts/audit/audit_page_payload_size.py
python3 scripts/site/build_postgame_shadow_updates.py
python3 scripts/betting/build_betting_activity_view.py
python3 scripts/site/build_matchups_view.py
python3 scripts/history/build_matchup_line_history_clean.py
python3 scripts/site/inject_matchup_line_history.py --asset-only
python3 scripts/research/build_market_implied_power_ratings.py --production-2026
python3 scripts/site/build_ratings_view.py
python3 scripts/site/build_shadow_team_game_features.py --mode all
python3 scripts/site/build_saturday_shadow_component_predictions.py
python3 scripts/site/build_saturday_shadow_lines.py
python3 scripts/site/build_schedule_live_enrichment.py
python3 scripts/audit/audit_market_shadow_production_layer.py
python3 scripts/audit/audit_saturday_shadow_production_integration.py
python3 scripts/audit/audit_coach_betting_consistency.py || echo "WARNING: coach betting consistency audit could not complete (report-only)"
python3 scripts/site/build_futures_view.py
python3 scripts/site/build_conference_workspace.py
echo "Building production Odds payloads..."
python3 scripts/site/build_odds_screen_v2.py
python3 scripts/site/build_odds_futures_v2.py
# MATCHUP_PREPUBLISH_AUDITS_START
echo "Running matchup pre-publish audits..."
python3 scripts/audit/audit_matchup_workspace.py
python3 scripts/audit/audit_matchup_card_data.py
python3 scripts/audit/audit_v2_dark_logo_badges.py
echo "Matchup pre-publish audits passed."
# MATCHUP_PREPUBLISH_AUDITS_END

python3 scripts/site/build_public_site.py
python3 scripts/audit/audit_canonical_v2_index.py build/public_site/index.html
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
cp build/public_site/*.js "$stage_dir/"
mkdir -p "$stage_dir/data/bets" "$stage_dir/data/site" "$stage_dir/data/agents" "$PUBLISH_REPO/data/bets" "$PUBLISH_REPO/data/site" "$PUBLISH_REPO/data/agents"
for file in bets_enriched.csv betting_dashboard.json market_clv_match_audit.csv betting_performance_history.csv bet_closing_clv.csv bet_closing_clv_audit.csv; do
  [ -f "data/bets/$file" ] && cp "data/bets/$file" "$stage_dir/data/bets/$file"
done
for file in matchup_line_history.json matchups_view.json betting_activity_view.json futures_view.json conference_workspace.json postgame_shadow_updates.json ratings_view.json game_control_team_games_2026.json playoff_model_2026.json schedule_live_enrichment.json odds_screen_v2.json odds_futures_v2.json; do
  [ -f "data/site/$file" ] && cp "data/site/$file" "$stage_dir/data/site/$file"
done
[ -f data/agents/home_top_bets.json ] && cp data/agents/home_top_bets.json "$stage_dir/data/agents/home_top_bets.json"

SCHEDULE_ENRICHMENT_STAGE="$stage_dir/data/site/schedule_live_enrichment.json"

if [[ ! -f "$SCHEDULE_ENRICHMENT_STAGE" ]]; then
  echo "ERROR: missing staged Schedule enrichment: $SCHEDULE_ENRICHMENT_STAGE" >&2
  exit 1
fi

python3 - "$SCHEDULE_ENRICHMENT_STAGE" <<'PYVALIDATE'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text())
games = data.get("games", [])
confirmed = sum(1 for row in games if row.get("kickoff_status") == "confirmed")
fbs_tagged = sum(1 for row in games if "fbs_matchup" in row)

if not games:
    raise SystemExit(f"ERROR: no games in {path}")
if confirmed == 0:
    raise SystemExit(f"ERROR: no confirmed kickoff times in {path}")
if fbs_tagged == 0:
    raise SystemExit(f"ERROR: no FBS/FCS classifications in {path}")

print(
    "validated staged artifact: data/site/schedule_live_enrichment.json "
    f"(games={len(games)}, confirmed_kickoffs={confirmed}, "
    f"fbs_tagged={fbs_tagged})"
)
PYVALIDATE
for staged in "$stage_dir"/*.html; do mv "$staged" "$PUBLISH_REPO/$(basename "$staged")"; done
for staged in "$stage_dir"/*.js; do mv "$staged" "$PUBLISH_REPO/$(basename "$staged")"; done
for staged in "$stage_dir"/data/bets/*; do
  [ -f "$staged" ] && mv "$staged" "$PUBLISH_REPO/data/bets/$(basename "$staged")"
done
for staged in "$stage_dir"/data/site/*; do
  [ -f "$staged" ] && mv "$staged" "$PUBLISH_REPO/data/site/$(basename "$staged")"
done
for staged in "$stage_dir"/data/agents/*; do
  [ -f "$staged" ] && mv "$staged" "$PUBLISH_REPO/data/agents/$(basename "$staged")"
done

git -C "$PUBLISH_REPO" add index.html dashboard.html openers.html matchups.html odds.html schedule.html futures.html conferences.html playoff.html betting.html team.html ratings.html simulations.html legacy.html v1.html matchup.html playoff_futures_tab.js dashboard_playoff_edges.js coach_cards.js team_coach_card.js matchup_workspace.js data/bets data/site data/agents
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
