#!/bin/bash
set -e

# Canonical execution profile.
#
# The production stage implementations live only in this file. Profiles select
# subsets of those same stages; they must never reimplement provider, ratings,
# projection, or publication logic elsewhere.
#
# Default/no argument preserves the existing full 8 AM workflow.
NCAAF_PROFILE="${NCAAF_PROFILE:-full}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --profile requires a value" >&2
        exit 2
      fi
      NCAAF_PROFILE="$2"
      shift 2
      ;;
    --profile=*)
      NCAAF_PROFILE="${1#*=}"
      shift
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$NCAAF_PROFILE" in
  full|openers|postgame|market)
    ;;
  *)
    echo "ERROR: unknown NCAAF profile: $NCAAF_PROFILE" >&2
    exit 2
    ;;
esac

export NCAAF_PROFILE


# Load CFBD API key from macOS Keychain when it is not already present.
if [ -z "${CFBD_API_KEY:-}" ]; then
  CFBD_API_KEY="$(security find-generic-password     -a "$USER"     -s CFBD_API_KEY     -w 2>/dev/null || true)"
  export CFBD_API_KEY
fi

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

# SportsGameOdds is an optional secondary market source.
# Email eligibility is not tied to SGO health; the canonical current-market
# contract owns provider priority and fallback selection.
SGO_PULL_OK=0
SGO_NORMALIZATION_OK=0

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

refresh_live_rating_source() {
  local source="$1"

  echo "Refreshing live rating source: $source"

  if ! python3 scripts/ratings/test_rating_sources.py --sources "$source"; then
    warn "$source ratings pull failed; retaining last-known-good accepted ratings"
    return 0
  fi

  if ! python3 scripts/ratings/parse_rating_source_tables.py --sources "$source"; then
    warn "$source ratings parse failed; retaining last-known-good accepted ratings"
    return 0
  fi

  if ! python3 scripts/ratings/accept_live_rating_candidates_with_status.py --sources "$source"; then
    warn "$source ratings acceptance failed; retaining last-known-good accepted ratings"
    return 0
  fi
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
  echo "Execution profile: $NCAAF_PROFILE"

  # STAGE: futures_market_acquisition
  stage_start "futures_market_acquisition"
  run_py "pull_actionnetwork_win_totals_api.py" || warn "Action Network win totals API pull unavailable; preserving cached data"
  run_py "odds/pull_actionnetwork_visible_dk_win_totals.py" "pull_actionnetwork_visible_dk_win_totals.py" || warn "visible DK win totals pull failed"
  run_py "odds/merge_visible_dk_win_totals.py" "merge_visible_dk_win_totals.py" || warn "visible DK win totals merge failed"
  run_py "pull_fanduel_win_totals.py" || warn "FanDuel win totals pull unavailable; preserving cached data"
  run_py "pull_bettingpros_caesars_win_totals.py" || warn "Caesars/BettingPros pull failed; preserving cached data"
  run_py "pulls/pull_actionnetwork_conference_futures_api.py" || warn "Action Network conference futures pull failed; preserving cached data"
  run_py "odds/quarantine_bad_draftkings_win_total_rows.py" "quarantine_bad_draftkings_win_total_rows.py" || warn "bad DraftKings win total quarantine failed"
  run_py "append_market_history.py" || warn "market history append failed; preserving prior history"
  run_py "build_daily_market_movement_report.py" || warn "daily market movement report build failed; preserving prior report"
  run_py "build_market_arbitrage_report.py" || warn "market arbitrage report build failed; preserving prior report"
  stage_pass "futures_market_acquisition"

  # STAGE: game_market_acquisition
  stage_start "game_market_acquisition"
  # Season game lines from CFBD. Used for early spread/total display while SGO is capped.
  run_py "pull_cfbd_lines_2026.py" || warn "CFBD season lines pull failed"
  run_py "odds/pull_actionnetwork_ncaaf_game_lines_2026.py" "pull_actionnetwork_ncaaf_game_lines_2026.py" || warn "Action Network game lines pull failed"
  run_py "odds/build_actionnetwork_season_lines_2026.py" "build_actionnetwork_season_lines_2026.py" || warn "Action Network season game lines build failed"
  run_py "build_season_game_lines_2026.py" || warn "season game lines build failed"
  # The Odds API is the preferred live source for current game lines.
  if run_py "pull_theodds_ncaaf_lines_2026.py"; then
    run_py "build_theodds_season_lines_2026.py" || warn "The Odds API line normalization failed"
  else
    warn "The Odds API primary live line pull failed; preserving cached/fallback data"
  fi
  stage_pass "game_market_acquisition"

  # SportsGameOdds is an optional secondary source while quota/subscription
  # strategy is evaluated. Failure must not block downstream site/email work.
  # STAGE: sgo_pull
  stage_start "sgo_pull"
  if run_py "scripts/markets/pull_sgo_ncaaf_game_odds.py"; then
    SGO_PULL_OK=1
    stage_pass "sgo_pull"
  else
    warn "live SGO pull failed; preserving prior SGO and fallback data"
    stage_skip "sgo_pull" "optional secondary SportsGameOdds source unavailable; cached/fallback data preserved"
  fi

  # Normalize only a raw response produced by a successful current run.
  # SGO is optional; failure does not block canonical market/site/email work.
  # STAGE: sgo_normalization
  stage_start "sgo_normalization"
  if [ "$SGO_PULL_OK" -eq 1 ] && [ -f "data/markets/sgo/sgo_ncaaf_events_raw.json" ]; then
    if run_py "scripts/markets/build_sgo_daily_canonical.py"; then
      if run_py "scripts/markets/parse_sgo_ncaaf_game_odds.py"; then
        SGO_NORMALIZATION_OK=1
        run_py "scripts/odds/append_sgo_game_book_line_history.py" \
          || warn "SGO canonical history append failed"
        stage_pass "sgo_normalization"
      else
        warn "SGO compatibility export failed; preserving fallback data"
        stage_fail "sgo_normalization" "SGO compatibility export failed"
      fi
    else
      warn "canonical SGO normalization failed; preserving fallback data"
      stage_fail "sgo_normalization" "canonical SGO normalization failed"
    fi
  elif [ "$SGO_PULL_OK" -eq 1 ]; then
    warn "successful SGO pull produced no raw response"
    stage_fail "sgo_normalization" "successful SGO pull produced no raw response"
  else
    stage_skip "sgo_normalization" "SGO pull unavailable; cached accepted/fallback data preserved"
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
  echo "Skipping legacy CFBDepth injury pull; redesigned source not configured."
  echo "Skipping legacy CFBDepth article pull; redesigned source not configured."
  echo "Skipping legacy injury alert build; canonical injury source not configured."
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
  echo "Skipping legacy injury email rows; canonical injury source not configured."
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
  # Legacy injury scoring is retired until the canonical injury contract exists.
  echo "Skipping legacy game injury scores; canonical injury source not configured."

  # Ratings/projection maintenance. Every automated production source is
  # refreshed independently. A failed source preserves its last-known-good
  # accepted value rather than preventing successful sources from updating.
  # STAGE: ratings_refresh
  stage_start "ratings_refresh"

  refresh_live_rating_source "spplus"
  refresh_live_rating_source "fpi"
  refresh_live_rating_source "teamrankings"

  run_py "ratings/pull_donchess_ratings.py" "pull_donchess_ratings.py" \
    || warn "Donchess/DRatings ratings refresh failed; retaining last-known-good data"

  run_py "ratings/pull_sagarin_ratings.py" "pull_sagarin_ratings.py" \
    || warn "Sagarin ratings refresh failed; retaining last-known-good data"

  # Massey remains a non-production reference source.
  run_py "ratings/parse_massey_visible_ratings.py" "parse_massey_visible_ratings.py" \
    || warn "Massey ratings refresh failed; retaining last-known-good reference data"

  stage_pass "ratings_refresh"

  # Build the same canonical five-source production ratings model used by the
  # site: SP+, FPI, TeamRankings, Donchess/DRatings, and Sagarin.
  # STAGE: ratings_normalization
  stage_start "ratings_normalization"
  run_py "scripts/ratings/build_all_ratings_latest.py" "build_all_ratings_latest.py" \
    || warn "ratings latest build failed"
  run_py "scripts/ratings/build_active_2026_ratings_master.py" "build_active_2026_ratings_master.py" \
    || warn "active five-source ratings master build failed"
  run_py "scripts/ratings/merge_live_rating_change_status.py" "merge_live_rating_change_status.py" \
    || warn "live rating change-status merge failed"
  run_py "ratings/append_ratings_history.py" "append_ratings_history.py" \
    || warn "ratings history append failed"
  run_py "ratings/build_ratings_movement.py" "build_ratings_movement.py" \
    || warn "ratings movement build failed"
  stage_pass "ratings_normalization"

  # STAGE: schedule_refresh
  stage_start "schedule_refresh"
  run_py "scripts/schedule/pull_cfbd_schedule_2026.py" "pull_cfbd_schedule_2026.py" \
    || warn "CFBD canonical schedule refresh failed"
  if [ -f "data/canonical/cfbd_schedule_2026.json" ]; then
    python3 scripts/schedule/apply_cfbd_schedule_overlay_2026.py --apply \
      || warn "CFBD schedule overlay failed"
  else
    warn "CFBD canonical schedule unavailable; preserving prior canonical schedule"
  fi
  stage_pass "schedule_refresh"

  # STAGE: projections
  stage_start "projections"
  run_py "scripts/projections/pull_dratings_ncaaf_predictions.py" "pull_dratings_ncaaf_predictions.py" || warn "DRatings NCAAF predictions refresh failed"
  run_py "scripts/projections/build_game_projection_sources_2026.py" "build_game_projection_sources_2026.py" || warn "game projection source build failed"
  run_py "scripts/projections/build_game_projection_blend_2026.py" "build_game_projection_blend_2026.py" || warn "game projection blend build failed"
  run_py "scripts/projections/apply_game_projection_blend_to_preseason_db.py" "apply_game_projection_blend_to_preseason_db.py" || warn "game projection site overlay failed"
  stage_pass "projections"

  # Canonical completed-game/Postgame refresh. The CFBD schedule was already
  # refreshed above, so do not spend another /games call here. Build final
  # results from that schedule, acquire rich PBP/drive/havoc data only when
  # completed games exist, then build season-to-date postgame features.
  # STAGE: postgame_refresh
  stage_start "postgame_refresh"
  run_py "scripts/results/build_game_results_2026.py" "build_game_results_2026.py"
  run_py "scripts/postgame/pull_cfbd_postgame_2026.py" "pull_cfbd_postgame_2026.py"
  run_py "scripts/postgame/build_postgame_features_2026.py" "build_postgame_features_2026.py"
  stage_pass "postgame_refresh"

# Current season/conference Monte Carlo simulations. This stage consumes the
# canonical projection consensus already applied to preseason_db.json.
# STAGE: conference_simulations

stage_start "conference_simulations"
run_py "scripts/simulations/build_season_simulations_2026.py" "build_season_simulations_2026.py"
stage_pass "conference_simulations"

# Current CFP selection and playoff Monte Carlo simulation. This consumes the
# canonical preseason DB after current projections and probability aliases have
# been applied. CFP selection retains the validated resume model; game winners
# use the canonical logistic margin-to-win-probability conversion.
# STAGE: playoff_simulations

stage_start "playoff_simulations"
run_py "scripts/simulations/run_playoff_model_2026.py" "run_playoff_model_2026.py"
run_py "scripts/audit/audit_playoff_model_2026.py" "audit_playoff_model_2026.py"
stage_pass "playoff_simulations"


  # Shadow production bridge. Canonical completed-game results and postgame
  # PBP/drive/game-control features were built earlier in postgame_refresh.
  # This stage builds no-lookahead 2026 Shadow features and applies the frozen
  # movement models; it never refits those models on 2026 outcomes.
  # STAGE: matchup_core
  stage_start "matchup_core"
  run_py "scripts/site/augment_team_advanced_profiles_drives.py" "augment_team_advanced_profiles_drives.py"
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
  python3 scripts/postgame/build_shadow_team_game_features_2026.py
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
run_py "scripts/site/build_conference_workspace.py" "build_conference_workspace.py"
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
  python3 scripts/ratings/refresh_ratings_source_status.py
  python3 scripts/markets/build_current_market_contract.py
  python3 scripts/site/build_odds_screen_v2.py
  python3 scripts/markets/apply_current_market_to_odds_screen.py
  python3 scripts/markets/apply_current_market_to_matchups.py
  python3 scripts/site/compact_matchups_payload.py
  python3 scripts/audit/audit_current_market_propagation.py
  python3 scripts/site/build_public_site.py
  python3 scripts/site/build_war_room_home.py
  python3 scripts/site/inject_market_presentation_fixes.py
  python3 scripts/site/apply_shared_war_room_shell.py
  cp matchup_workspace.js build/public_site/matchup_workspace.js
  python3 scripts/audit/audit_war_room_home_market_propagation.py
  stage_pass "site_build"

  # STAGE: site_validation
  stage_start "site_validation"
  python3 scripts/audit/audit_canonical_v2_index.py index.html
  python3 scripts/audit/audit_canonical_v2_index.py build/public_site/index.html
  python3 scripts/audit/audit_canonical_openers_drawer.py
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
