#!/bin/bash
set -e

WORK="$HOME/NCAAF_AUTO"
ICLOUD="/Users/jameslindesmith/Library/Mobile Documents/com~apple~CloudDocs/NCAAF"
LOG="$HOME/Scripts/NCAAF/daily_market_update.log"

# Gmail email step uses environment variables from your shell/launchd plist/keychain.
# Required when sending is enabled: NCAAF_GMAIL_USER, NCAAF_GMAIL_APP_PASSWORD, NCAAF_EMAIL_TO.
# Email env vars are checked only at send time so market/site builds can still run without email.

cd "$WORK"

wait_for_network() {
  local host="${1:-api.actionnetwork.com}"
  local tries="${2:-12}"
  local sleep_sec="${3:-10}"
  local i=1

  while [ "$i" -le "$tries" ]; do
    if /usr/bin/python3 - <<PYNET
import socket, sys
host = "$host"
try:
    socket.getaddrinfo(host, 443)
    sys.exit(0)
except Exception:
    sys.exit(1)
PYNET
    then
      echo "Network/DNS check passed for $host"
      return 0
    fi

    echo "WARNING: DNS/network not ready for $host, attempt $i/$tries. Waiting ${sleep_sec}s..."
    sleep "$sleep_sec"
    i=$((i+1))
  done

  echo "WARNING: DNS/network still unavailable for $host. Continuing with cached data where possible."
  return 0
}


run_py() {
  local primary="$1"
  local fallback="$2"
  if [ -f "$primary" ]; then
    python3 "$primary"
  elif [ -n "$fallback" ] && [ -f "$fallback" ]; then
    python3 "$fallback"
  else
    echo "WARNING: missing script: $primary${fallback:+ or $fallback}"
    return 1
  fi
}

STAGE_REGISTRY="config/daily_stages.json"
STATUS_WRITER="scripts/control/daily_run_status.py"
STATUS_FILE="data/control/daily_run_status.json"
SOURCE_RECORD="data/control/deployed_source_version.json"
RUN_ID="daily-$(date -u +%Y%m%dT%H%M%SZ)-$$"
STARTED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
CURRENT_STAGE=""
RUN_FINALIZED=0

status_stage() {
  local stage_id="$1"
  local status="$2"
  local detail="${3:-}"
  local args=(stage --output "$STATUS_FILE" --stage-id "$stage_id" --status "$status")
  if [ -n "$detail" ]; then
    args+=(--detail "$detail")
  fi
  python3 "$STATUS_WRITER" "${args[@]}"
}

stage_start() {
  CURRENT_STAGE="$1"
  status_stage "$CURRENT_STAGE" RUNNING
}

stage_pass() {
  status_stage "$1" PASSED "${2:-}"
  CURRENT_STAGE=""
}

stage_skip() {
  status_stage "$1" SKIPPED "$2"
  CURRENT_STAGE=""
}

stage_fail() {
  status_stage "$1" FAILED "$2"
  CURRENT_STAGE=""
}

warn() {
  local message="$1"
  echo "WARNING: $message"
  python3 "$STATUS_WRITER" warning --output "$STATUS_FILE" \
    --stage-id "$CURRENT_STAGE" --message "$message"
}

finalize_run_status() {
  local exit_code="$1"
  if [ "$RUN_FINALIZED" -eq 1 ]; then
    return
  fi
  RUN_FINALIZED=1
  if [ "$exit_code" -ne 0 ] && [ -n "$CURRENT_STAGE" ]; then
    status_stage "$CURRENT_STAGE" FAILED "workflow exited during this stage" || true
  fi
  python3 "$STATUS_WRITER" finish --output "$STATUS_FILE" \
    --finished-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --exit-code "$exit_code" || true
}

on_exit() {
  local exit_code=$?
  finalize_run_status "$exit_code"
  exit "$exit_code"
}

python3 "$STATUS_WRITER" init --output "$STATUS_FILE" \
  --registry "$STAGE_REGISTRY" --source-record "$SOURCE_RECORD" \
  --run-id "$RUN_ID" --started-at "$STARTED_AT_UTC"
trap on_exit EXIT

{
  echo "========================================"
  echo "Daily market update started: $(date)"

  # STAGE: futures_market_acquisition
  stage_start "futures_market_acquisition"
  run_py "pull_actionnetwork_win_totals_api.py"
  run_py "odds/pull_actionnetwork_visible_dk_win_totals.py" "pull_actionnetwork_visible_dk_win_totals.py" || warn "visible DK win totals pull failed"
  run_py "odds/merge_visible_dk_win_totals.py" "merge_visible_dk_win_totals.py" || warn "visible DK win totals merge failed"
  run_py "pull_fanduel_win_totals.py"
  run_py "pull_bettingpros_caesars_win_totals.py" || warn "Caesars/BettingPros pull failed; preserving cached data"
  run_py "pulls/pull_actionnetwork_conference_futures_api.py"
  run_py "odds/quarantine_bad_draftkings_win_total_rows.py" "quarantine_bad_draftkings_win_total_rows.py" || warn "bad DraftKings win total quarantine failed"
  run_py "append_market_history.py"
  run_py "build_daily_market_movement_report.py"
  run_py "build_market_arbitrage_report.py"
  stage_pass "futures_market_acquisition"

  # STAGE: game_market_acquisition
  stage_start "game_market_acquisition"
  # Season game lines from CFBD. Used for early spread/total display while SGO is capped.
  run_py "pull_cfbd_lines_2026.py" || warn "CFBD season lines pull failed"
  run_py "odds/pull_actionnetwork_ncaaf_game_lines_2026.py" "pull_actionnetwork_ncaaf_game_lines_2026.py" || warn "Action Network game lines pull failed"
  run_py "odds/build_actionnetwork_season_lines_2026.py" "build_actionnetwork_season_lines_2026.py" || warn "Action Network season game lines build failed"
  run_py "build_season_game_lines_2026.py" || warn "season game lines build failed"
  run_py "pull_theodds_ncaaf_lines_2026.py" || warn "The Odds API line pull failed"
  run_py "build_theodds_season_lines_2026.py" || warn "The Odds API line normalization failed"
  stage_pass "game_market_acquisition"

  # SportsGameOdds is the preferred live source for game lines.
  # STAGE: sgo_pull
  stage_start "sgo_pull"
  run_py "scripts/markets/pull_sgo_ncaaf_game_odds.py" \
    || warn "live SGO pull failed; preserving prior SGO and fallback data"
  stage_pass "sgo_pull"

  # If an SGO response is present, normalize it through the same canonical
  # controller mapping/pairing/coverage path. Partial coverage remains
  # preview-only and cannot change accepted state or history.
  # STAGE: sgo_normalization
  stage_start "sgo_normalization"
  if [ -f "data/markets/sgo/sgo_ncaaf_events_raw.json" ]; then
    run_py "scripts/markets/build_sgo_daily_canonical.py" || warn "canonical SGO preview build failed"
    run_py "scripts/markets/parse_sgo_ncaaf_game_odds.py" || warn "SGO coverage blocked accepted compatibility export"
    run_py "scripts/odds/append_sgo_game_book_line_history.py" || warn "SGO coverage blocked canonical history append"
    stage_pass "sgo_normalization"
  else
    stage_skip "sgo_normalization" "no SGO raw response available; cached accepted data preserved"
  fi


  # Append today's normalized game lines before site/email rendering.
  # STAGE: game_line_history
  stage_start "game_line_history"
  run_py "scripts/odds/append_game_line_history.py" "append_game_line_history.py" || warn "game line history append failed"
  run_py "odds/build_game_line_movement_report.py" "build_game_line_movement_report.py" || warn "game line movement report build failed"
  stage_pass "game_line_history"

  echo "Skipping legacy V1 market-site build; canonical V2 owns all public site output."

  # STAGE: injuries_and_signals
  stage_start "injuries_and_signals"
  run_py "injuries/pull_cfbdepth_injuries.py" "pull_cfbdepth_injuries.py" || warn "CFBDepth injury pull failed"
  run_py "injuries/pull_cfbdepth_article_bodies.py" "pull_cfbdepth_article_bodies.py" || warn "CFBDepth injury article pull failed"
  run_py "scripts/injuries/build_injury_alerts.py" "build_injury_alerts.py" || warn "injury alert build failed"
  run_py "agents/build_daily_betting_angles.py" "build_daily_betting_angles.py"
  run_py "agents/append_daily_game_line_edges.py" "append_daily_game_line_edges.py" || warn "game line email edges append failed"
  stage_pass "injuries_and_signals"

  echo "Checking daily betting angle categories before HTML email build..."
  python3 - <<'PY2'
import pandas as pd
from pathlib import Path

p = Path("data/agents/daily_betting_angles.csv")
if not p.exists():
    print("WARNING: daily_betting_angles.csv missing before email HTML build")
else:
    df = pd.read_csv(p)
    if "category" in df.columns:
        print(df["category"].value_counts(dropna=False).to_string())
        game_rows = int((df["category"] == "Game line edge").sum())
        print(f"Game line edge rows before HTML build: {game_rows}")
        if game_rows == 0:
            print("WARNING: zero game line edge rows before email HTML build")
PY2


  # Add supplemental rows, remove juice-only game moves, then render HTML.
  # STAGE: email_build
  stage_start "email_build"
  run_py "agents/prepend_game_line_moves_to_daily_betting_angles.py" "prepend_game_line_moves_to_daily_betting_angles.py" || warn "prepend game line moves to email failed"
  run_py "agents/prepend_injury_alerts_to_daily_betting_angles.py" "prepend_injury_alerts_to_daily_betting_angles.py" || warn "prepend injury alerts failed"
  run_py "scripts/agents/clean_daily_game_line_moves.py" "clean_daily_game_line_moves.py" || warn "daily game-line move cleaning failed"
  run_py "scripts/agents/build_daily_betting_angles_html.py" "build_daily_betting_angles_html.py"
  stage_pass "email_build"

  # STAGE: email_regression
  stage_start "email_regression"
  python3 scripts/audit/test_daily_betting_email_regression.py
  stage_pass "email_regression"

  # These legacy HTML injectors target index.html directly and therefore must
  # not run in the V2 daily path. Their production data is supplied by the
  # canonical V2 JSON/view builders below. The legacy intermediate remains an
  # optional diagnostic artifact and is never a publication source.
  echo "Skipping legacy index injectors; V2 builders own the canonical site shell."
  # STAGE: injury_scores
  stage_start "injury_scores"
  run_py "injuries/build_game_injury_scores.py" "build_game_injury_scores.py" || warn "game injury score build failed"
  stage_pass "injury_scores"

  # Ratings/projection maintenance. Pull/parse refreshes are optional because some sources may be inactive.
  # STAGE: ratings_refresh
  stage_start "ratings_refresh"
  run_py "ratings/pull_sagarin_ratings.py" "pull_sagarin_ratings.py" || warn "Sagarin ratings refresh failed"
  run_py "ratings/parse_massey_visible_ratings.py" "parse_massey_visible_ratings.py" || warn "Massey ratings refresh failed"
  run_py "ratings/pull_donchess_ratings.py" "pull_donchess_ratings.py" || warn "Donchess ratings refresh failed"
  stage_pass "ratings_refresh"

  # STAGE: ratings_normalization
  stage_start "ratings_normalization"
  run_py "scripts/ratings/build_all_ratings_latest.py" "build_all_ratings_latest.py" || warn "ratings latest build failed"
  run_py "ratings/append_ratings_history.py" "append_ratings_history.py" || warn "ratings history append failed"
  run_py "ratings/build_ratings_movement.py" "build_ratings_movement.py" || warn "ratings movement build failed"
  stage_pass "ratings_normalization"

  # STAGE: projections
  stage_start "projections"
  run_py "scripts/projections/build_game_projection_sources_2026.py" "build_game_projection_sources_2026.py" || warn "game projection source build failed"
  run_py "scripts/projections/build_game_projection_blend_2026.py" "build_game_projection_blend_2026.py" || warn "game projection blend build failed"
  stage_pass "projections"

  # Shadow production bridge. Current selected market lines must already be in
  # matchups_view; completed-game results/PBP/game-control builders run through
  # the existing site build and postgame paths. These steps do no acquisition
  # and never refit the frozen movement models.
  # STAGE: matchup_core
  stage_start "matchup_core"
  run_py "scripts/site/build_matchups_view.py" "build_matchups_view.py"
  stage_pass "matchup_core"

  # Bridge the newly appended daily market snapshot into the normalized V2
  # history assets consumed by both Odds and the shared matchup workspace.
  # Asset-only mode deliberately leaves every canonical V2 HTML file untouched.
  # STAGE: line_history_assets
  stage_start "line_history_assets"
  run_py "scripts/history/build_matchup_line_history_clean.py" "build_matchup_line_history_clean.py"
  python3 scripts/site/inject_matchup_line_history.py --asset-only
  stage_pass "line_history_assets"

  # STAGE: shadow_models
  stage_start "shadow_models"
  python3 scripts/research/build_market_implied_power_ratings.py --production-2026
  run_py "scripts/site/build_ratings_view.py" "build_ratings_view.py"
  python3 scripts/site/build_shadow_team_game_features.py --mode all
  python3 scripts/site/build_saturday_shadow_component_predictions.py
  python3 scripts/site/build_saturday_shadow_lines.py
  python3 scripts/site/build_schedule_live_enrichment.py
  python3 scripts/audit/audit_market_shadow_production_layer.py
  python3 scripts/audit/audit_saturday_shadow_production_integration.py
  stage_pass "shadow_models"

  # Refresh V2 Futures data after the canonical projection outputs are final.
  # A failed or stale playoff-market pull does not block the rest of the site; the
  # Futures QA banner will surface the issue while cached data remains available.
  # STAGE: playoff_futures
  stage_start "playoff_futures"
  wait_for_network "api.actionnetwork.com"
  run_py "scripts/markets/pull_actionnetwork_playoff_futures.py" "pull_actionnetwork_playoff_futures.py" || warn "Action Network playoff futures pull failed; using cached data where available"
  run_py "scripts/site/build_futures_view.py" "build_futures_view.py" || warn "Futures V2 data build failed"
  stage_pass "playoff_futures"

  # Refresh the production Odds page payloads after the current game and
  # futures sources are complete. Builders write atomically scoped Odds
  # artifacts; on failure the previous valid files remain available.
  # STAGE: odds_payloads
  stage_start "odds_payloads"
  run_py "scripts/site/build_odds_screen_v2.py" "build_odds_screen_v2.py" || warn "Odds game payload build failed; retaining last valid artifact"
  run_py "scripts/site/build_odds_futures_v2.py" "build_odds_futures_v2.py" || warn "Odds futures payload build failed; retaining last valid artifact"
  stage_pass "odds_payloads"

  # Optional email send. Do not let missing Gmail env vars stop the market/site/rating build.
  # STAGE: email_send
  stage_start "email_send"
  if [ "${NCAAF_SEND_EMAIL:-1}" = "0" ]; then
    echo "NCAAF_SEND_EMAIL=0: daily email build completed; sending skipped"
    stage_skip "email_send" "disabled by NCAAF_SEND_EMAIL=0"
  elif [ -n "${NCAAF_GMAIL_USER:-}" ] && [ -n "${NCAAF_GMAIL_APP_PASSWORD:-}" ] && [ -n "${NCAAF_EMAIL_TO:-}" ]; then
    if run_py "email/send_daily_betting_angles_email.py" "send_daily_betting_angles_email.py"; then
      stage_pass "email_send"
    else
      warn "daily betting angles email send failed"
      stage_fail "email_send" "email sender returned non-zero"
    fi
  else
    warn "Skipping email send because required Gmail environment variables are missing"
    stage_skip "email_send" "credentials unavailable"
  fi

  # Build and validate the canonical V2 public bundle. Publication is delegated
  # to the normal staged publisher so a legacy artifact can never be copied to
  # the public repository by this script.
  # STAGE: site_build
  stage_start "site_build"
  python3 scripts/site/build_public_site.py
  stage_pass "site_build"

  # STAGE: site_validation
  stage_start "site_validation"
  python3 scripts/audit/audit_canonical_v2_index.py index.html
  python3 scripts/audit/audit_canonical_v2_index.py build/public_site/index.html
  python3 scripts/publish/check_public_site.py
  stage_pass "site_validation"

  # STAGE: publication
  stage_start "publication"
  if [ "${NCAAF_AUTO_PUBLISH:-1}" = "0" ]; then
    echo "NCAAF_AUTO_PUBLISH=0: validated V2 build; publication skipped"
    stage_skip "publication" "disabled by NCAAF_AUTO_PUBLISH=0"
  else
    bash scripts/publish/publish_site.sh --push
    stage_pass "publication"
  fi

# cp market_win_totals_history.csv "$ICLOUD/"
  # cp market_conference_futures_history.csv "$ICLOUD/"
  # cp market_win_totals_movement.csv "$ICLOUD/"
  # cp market_conference_futures_movement.csv "$ICLOUD/"
  # cp market_movement_export.xlsx "$ICLOUD/"
  # cp market_futures_export.xlsx "$ICLOUD/"
  # cp index_auto_market.html "$ICLOUD/"

  echo "Daily market update finished: $(date)"
  finalize_run_status 0
} >> "$LOG" 2>&1

# The install_* scripts below this point were one-time source migrations. They
# also write directly into the publication repository, so they are deliberately
# excluded from recurring automation. Their approved results live in the V2
# source files and are copied only by the staged publisher above.
