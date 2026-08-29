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
NCAAF_PROFILE_PLAN=0

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
    --plan)
      NCAAF_PROFILE_PLAN=1
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

CANONICAL_STAGE_ORDER=(
  futures_market_acquisition
  game_market_acquisition
  game_line_history
  injuries_and_signals
  email_build
  email_regression
  ratings_refresh
  ratings_normalization
  schedule_refresh
  projections
  postgame_refresh
  conference_simulations
  playoff_simulations
  matchup_core
  betting_ledger
  line_history_assets
  shadow_models
  playoff_futures
  odds_payloads
  email_send
  site_build
  site_validation
  publication
)

stage_enabled() {
  local stage="$1"

  # Full is intentionally automatic: every canonical stage runs. This means
  # adding a future stage does not require separately updating the full profile.
  if [ "$NCAAF_PROFILE" = "full" ]; then
    return 0
  fi

  case "$NCAAF_PROFILE:$stage" in

    # Fast Openers refresh:
    # current game markets + ratings + schedule/projections + downstream
    # matchup/Shadow/Odds/site publication. No sims, futures, email or PBP.
    openers:game_market_acquisition|\
    openers:game_line_history|\
    openers:ratings_refresh|\
    openers:ratings_normalization|\
    openers:schedule_refresh|\
    openers:projections|\
    openers:matchup_core|\
    openers:line_history_assets|\
    openers:shadow_models|\
    openers:odds_payloads|\
    openers:site_build|\
    openers:site_validation|\
    openers:publication)
      return 0
      ;;

    # Fast Postgame refresh:
    # authoritative schedule/results + rich postgame features + Shadow and
    # downstream site publication. No market/rating refresh or simulations.
    postgame:schedule_refresh|\
    postgame:postgame_refresh|\
    postgame:matchup_core|\
    postgame:shadow_models|\
    postgame:site_build|\
    postgame:site_validation|\
    postgame:publication)
      return 0
      ;;

    # Fast Market refresh:
    # same canonical live game-market acquisition/fallback/history path plus
    # downstream Odds/Matchups/site publication. No ratings or simulations.
    market:game_market_acquisition|\
    market:game_line_history|\
    market:matchup_core|\
    market:line_history_assets|\
    market:shadow_models|\
    market:odds_payloads|\
    market:site_build|\
    market:site_validation|\
    market:publication)
      return 0
      ;;
  esac

  return 1
}

print_profile_plan() {
  local stage

  echo "NCAAF execution profile: $NCAAF_PROFILE"
  echo
  echo "RUN:"

  for stage in "${CANONICAL_STAGE_ORDER[@]}"; do
    if stage_enabled "$stage"; then
      echo "  $stage"
    fi
  done

  echo
  echo "SKIP:"

  for stage in "${CANONICAL_STAGE_ORDER[@]}"; do
    if ! stage_enabled "$stage"; then
      echo "  $stage"
    fi
  done
}

if [ "$NCAAF_PROFILE_PLAN" -eq 1 ]; then
  print_profile_plan
  exit 0
fi


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
EMAIL_REGRESSION_PASSED=1


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

profile_skip_stage() {
  local stage="$1"
  stage_skip "$stage" "excluded by NCAAF_PROFILE=$NCAAF_PROFILE"
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
  --run-id "$RUN_ID" --profile "$NCAAF_PROFILE" \
  --started-at "$STARTED_AT_UTC"
trap on_exit EXIT

{
  echo "========================================"
  echo "Daily market update started: $(date)"
  echo "Execution profile: $NCAAF_PROFILE"

  # STAGE: futures_market_acquisition
  if stage_enabled "futures_market_acquisition"; then
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

  else
    profile_skip_stage "futures_market_acquisition"
  fi

  # STAGE: game_market_acquisition
  if stage_enabled "game_market_acquisition"; then
  stage_start "game_market_acquisition"
  # Season game lines from CFBD. Used for early spread/total display before The Odds API market normalization.
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
  run_py "scripts/markets/build_current_market_contract.py" "build_current_market_contract.py" || warn "Canonical current market contract build failed; retaining last valid artifact"
  stage_pass "game_market_acquisition"

  # strategy is evaluated. Failure must not block downstream site/email work.
  else
    profile_skip_stage "game_market_acquisition"
  fi


  # STAGE: game_line_history
  if stage_enabled "game_line_history"; then
  stage_start "game_line_history"
  run_py "scripts/odds/append_game_line_history.py" "append_game_line_history.py" || warn "game line history append failed"
  run_py "scripts/odds/append_current_market_book_history.py" "append_current_market_book_history.py" || warn "canonical per-book market history append failed"
  run_py "odds/build_game_line_movement_report.py" "build_game_line_movement_report.py" || warn "game line movement report build failed"
  stage_pass "game_line_history"

  echo "Skipping legacy V1 market-site build; canonical V2 owns all public site output."

  else
    profile_skip_stage "game_line_history"
  fi

  # STAGE: injuries_and_signals
  if stage_enabled "injuries_and_signals"; then
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
  else
    profile_skip_stage "injuries_and_signals"
  fi

  # STAGE: email_build
  if stage_enabled "email_build"; then
  stage_start "email_build"
  run_py "agents/prepend_game_line_moves_to_daily_betting_angles.py" "prepend_game_line_moves_to_daily_betting_angles.py" || warn "prepend game line moves to email failed"
  echo "Skipping legacy injury email rows; canonical injury source not configured."
  run_py "scripts/agents/clean_daily_game_line_moves.py" "clean_daily_game_line_moves.py" || warn "daily game-line move cleaning failed"
  run_py "scripts/agents/build_daily_betting_angles_html.py" "build_daily_betting_angles_html.py"
  stage_pass "email_build"

  else
    profile_skip_stage "email_build"
  fi

  # STAGE: email_regression
  if stage_enabled "email_regression"; then
  stage_start "email_regression"
  if python3 scripts/audit/test_daily_betting_email_regression.py; then
    stage_pass "email_regression"
  else
    EMAIL_REGRESSION_PASSED=0
    stage_fail "email_regression" "email artifacts failed regression; email send blocked while independent publication stages continue"
    echo "WARNING: email regression failed; skipping email delivery and continuing independent production stages"
  fi

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
  else
    profile_skip_stage "email_regression"
  fi

  # STAGE: ratings_refresh
  if stage_enabled "ratings_refresh"; then
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
  else
    profile_skip_stage "ratings_refresh"
  fi

  # STAGE: ratings_normalization
  if stage_enabled "ratings_normalization"; then
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

  else
    profile_skip_stage "ratings_normalization"
  fi

  # STAGE: schedule_refresh
  if stage_enabled "schedule_refresh"; then
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

  else
    profile_skip_stage "schedule_refresh"
  fi

  # STAGE: projections
  if stage_enabled "projections"; then
  stage_start "projections"
  run_py "scripts/projections/refresh_massey_game_projections_2026.py" "refresh_massey_game_projections_2026.py" || warn "Massey rolling 14-day game projections refresh failed; retaining last-known-good data"
  run_py "scripts/projections/pull_dratings_ncaaf_predictions.py" "pull_dratings_ncaaf_predictions.py" || warn "DRatings NCAAF predictions refresh failed"
  run_py "scripts/projections/build_game_projection_sources_2026.py" "build_game_projection_sources_2026.py" || warn "game projection source build failed"
  run_py "scripts/projections/build_current_game_projection_contract.py" "build_current_game_projection_contract.py" || warn "canonical game projection contract build failed"
  run_py "scripts/audit/audit_projection_fbs_production_coverage.py" "audit_projection_fbs_production_coverage.py" || warn "FBS production projection coverage audit failed"
  run_py "scripts/projections/build_game_projection_blend_2026.py" "build_game_projection_blend_2026.py" || warn "game projection blend build failed"
  run_py "scripts/projections/apply_game_projection_blend_to_preseason_db.py" "apply_game_projection_blend_to_preseason_db.py" || warn "game projection site overlay failed"
  stage_pass "projections"

  # Canonical completed-game/Postgame refresh. The CFBD schedule was already
  # refreshed above, so do not spend another /games call here. Build final
  # results from that schedule, acquire rich PBP/drive/havoc data only when
  # completed games exist, then build season-to-date postgame features.
  else
    profile_skip_stage "projections"
  fi

  # STAGE: postgame_refresh
  if stage_enabled "postgame_refresh"; then
  stage_start "postgame_refresh"
  run_py "scripts/results/build_game_results_2026.py" "build_game_results_2026.py"
  run_py "scripts/postgame/pull_cfbd_postgame_2026.py" "pull_cfbd_postgame_2026.py"
  run_py "scripts/postgame/build_postgame_features_2026.py" "build_postgame_features_2026.py"
  stage_pass "postgame_refresh"

# Current season/conference Monte Carlo simulations. This stage consumes the
# canonical projection consensus already applied to preseason_db.json.
  else
    profile_skip_stage "postgame_refresh"
  fi

# STAGE: conference_simulations
if stage_enabled "conference_simulations"; then

stage_start "conference_simulations"
run_py "scripts/simulations/build_season_simulations_2026.py" "build_season_simulations_2026.py"
stage_pass "conference_simulations"

# Current CFP selection and playoff Monte Carlo simulation. This consumes the
# canonical preseason DB after current projections and probability aliases have
# been applied. CFP selection retains the validated resume model; game winners
# use the canonical logistic margin-to-win-probability conversion.
else
  profile_skip_stage "conference_simulations"
fi

# STAGE: playoff_simulations
if stage_enabled "playoff_simulations"; then

stage_start "playoff_simulations"
run_py "scripts/simulations/run_playoff_model_2026.py" "run_playoff_model_2026.py"
run_py "scripts/audit/audit_playoff_model_2026.py" "audit_playoff_model_2026.py"
stage_pass "playoff_simulations"


  # Shadow production bridge. Canonical completed-game results and postgame
  # PBP/drive/game-control features were built earlier in postgame_refresh.
  # This stage builds no-lookahead 2026 Shadow features and applies the frozen
  # movement models; it never refits those models on 2026 outcomes.
else
  profile_skip_stage "playoff_simulations"
fi

  # STAGE: matchup_core
  if stage_enabled "matchup_core"; then
  stage_start "matchup_core"
  run_py "scripts/site/augment_team_advanced_profiles_drives.py" "augment_team_advanced_profiles_drives.py"
  run_py "scripts/site/build_matchups_view.py" "build_matchups_view.py"
  stage_pass "matchup_core"

  # Bridge the newly appended daily market snapshot into the normalized V2
  # history assets consumed by both Odds and the shared matchup workspace.
  # Asset-only mode deliberately leaves every canonical V2 HTML file untouched.
  else
    profile_skip_stage "matchup_core"
  fi

  # STAGE: betting_ledger
  # The published Google Sheet is the authoritative tracked-wager source.
  # Existing betting owners retain normalization, grading, CLV, and EV logic.
  if stage_enabled "betting_ledger"; then
  stage_start "betting_ledger"
  run_py "betting/pull_google_sheet_bets.py" "pull_google_sheet_bets.py"
  run_py "betting/build_betting_dashboard.py" "build_betting_dashboard.py"
  run_py "betting/enrich_betting_current_clv.py" "enrich_betting_current_clv.py"
  run_py "betting/freeze_betting_closing_clv.py" "freeze_betting_closing_clv.py"
  run_py "betting/build_betting_activity_view.py" "build_betting_activity_view.py"
  stage_pass "betting_ledger"
  else
    profile_skip_stage "betting_ledger"
  fi

  # STAGE: line_history_assets
  if stage_enabled "line_history_assets"; then
  stage_start "line_history_assets"
  run_py "scripts/history/build_matchup_line_history_clean.py" "build_matchup_line_history_clean.py"
  python3 scripts/site/inject_matchup_line_history.py --asset-only
  stage_pass "line_history_assets"

  else
    profile_skip_stage "line_history_assets"
  fi

  # STAGE: shadow_models
  if stage_enabled "shadow_models"; then
  stage_start "shadow_models"
  python3 scripts/research/build_market_implied_power_ratings.py --production-2026
  run_py "scripts/site/build_ratings_view.py" "build_ratings_view.py"
  run_py "scripts/site/build_projection_source_status_view.py" "build_projection_source_status_view.py" || warn "projection source status view build failed"
  python3 scripts/postgame/build_shadow_team_game_features_2026.py
  python3 scripts/site/build_saturday_shadow_component_predictions.py
  python3 scripts/projections/build_current_game_projection_contract.py
  python3 scripts/site/build_matchups_view.py
  python3 scripts/site/build_saturday_shadow_lines.py
  python3 scripts/audit/validate_projection_resolver.py
  python3 scripts/site/build_schedule_live_enrichment.py
  python3 scripts/audit/audit_market_shadow_production_layer.py
  python3 scripts/audit/audit_saturday_shadow_production_integration.py
  stage_pass "shadow_models"

  # Refresh V2 Futures data after the canonical projection outputs are final.
  # A failed or stale playoff-market pull does not block the rest of the site; the
  # Futures QA banner will surface the issue while cached data remains available.
  else
    profile_skip_stage "shadow_models"
  fi

  # STAGE: playoff_futures
  if stage_enabled "playoff_futures"; then
  stage_start "playoff_futures"
  wait_for_network "api.actionnetwork.com"
  run_py "scripts/markets/pull_actionnetwork_playoff_futures.py" "pull_actionnetwork_playoff_futures.py" || warn "Action Network playoff futures pull failed; using cached data where available"
  run_py "scripts/site/build_futures_view.py" "build_futures_view.py" || warn "Futures V2 data build failed"
run_py "scripts/site/build_conference_workspace.py" "build_conference_workspace.py"
  stage_pass "playoff_futures"

  # Refresh the production Odds page payloads after the current game and
  # futures sources are complete. Builders write atomically scoped Odds
  # artifacts; on failure the previous valid files remain available.
  else
    profile_skip_stage "playoff_futures"
  fi

  # STAGE: odds_payloads
  if stage_enabled "odds_payloads"; then
  stage_start "odds_payloads"
  # Canonical current market was built immediately after acquisition.
  run_py "scripts/site/build_odds_screen_v2.py" "build_odds_screen_v2.py" || warn "Odds game payload build failed; retaining last valid artifact"
  run_py "scripts/site/build_odds_futures_v2.py" "build_odds_futures_v2.py" || warn "Odds futures payload build failed; retaining last valid artifact"
  stage_pass "odds_payloads"

  # Optional email send. Do not let missing Gmail env vars stop the market/site/rating build.
  else
    profile_skip_stage "odds_payloads"
  fi

  # STAGE: email_send
  if stage_enabled "email_send"; then
  stage_start "email_send"
  if [ "$EMAIL_REGRESSION_PASSED" -ne 1 ]; then
    echo "Email delivery skipped because the email regression gate failed"
    stage_skip "email_send" "email regression failed"
  elif [ "${NCAAF_SEND_EMAIL:-1}" = "0" ]; then
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
  else
    profile_skip_stage "email_send"
  fi

  # STAGE: site_build
  if stage_enabled "site_build"; then
  stage_start "site_build"
  python3 scripts/ratings/refresh_ratings_source_status.py
  # Odds, Openers, Matchups, and Home consume the canonical current-market contract directly.
  python3 scripts/site/compact_matchups_payload.py
  python3 scripts/audit/audit_current_market_propagation.py
  python3 scripts/war_room/build_war_room_health.py
  python3 scripts/war_room/build_war_room_market_matrix.py
  python3 scripts/site/build_public_site.py
  python3 scripts/site/inject_market_presentation_fixes.py
  python3 scripts/audit/audit_war_room_home_market_propagation.py
  stage_pass "site_build"

  else
    profile_skip_stage "site_build"
  fi

  # STAGE: site_validation
  if stage_enabled "site_validation"; then
  stage_start "site_validation"
  python3 scripts/audit/audit_canonical_v2_index.py index.html
  python3 scripts/audit/audit_canonical_v2_index.py build/public_site/index.html
  python3 scripts/audit/audit_canonical_openers_drawer.py
  python3 scripts/audit/audit_war_room_home_market_propagation.py
  python3 scripts/publish/check_public_site.py
  stage_pass "site_validation"

  else
    profile_skip_stage "site_validation"
  fi

  # STAGE: publication
  if stage_enabled "publication"; then
  stage_start "publication"
  if [ "${NCAAF_AUTO_PUBLISH:-1}" = "0" ]; then
    echo "NCAAF_AUTO_PUBLISH=0: validated V2 build; publication skipped"
    stage_skip "publication" "disabled by NCAAF_AUTO_PUBLISH=0"
  else
    bash scripts/publish/publish_site.sh --push
    stage_pass "publication"
  fi

  else
    profile_skip_stage "publication"
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
