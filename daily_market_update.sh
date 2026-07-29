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

{
  echo "========================================"
  echo "Daily market update started: $(date)"

  run_py "pull_actionnetwork_win_totals_api.py"
  run_py "scripts/odds/pull_actionnetwork_visible_dk_win_totals.py" "pull_actionnetwork_visible_dk_win_totals.py" || echo "WARNING: visible DK win totals pull failed"
  run_py "scripts/odds/merge_visible_dk_win_totals.py" "merge_visible_dk_win_totals.py" || echo "WARNING: visible DK win totals merge failed"
  run_py "pull_fanduel_win_totals.py"
  run_py "pull_bettingpros_caesars_win_totals.py"
  run_py "pull_actionnetwork_conference_futures_api.py"
  run_py "scripts/odds/quarantine_bad_draftkings_win_total_rows.py" "quarantine_bad_draftkings_win_total_rows.py" || echo "WARNING: bad DraftKings win total quarantine failed"
  run_py "append_market_history.py"
  run_py "build_daily_market_movement_report.py"
  run_py "build_market_arbitrage_report.py"
  # Season game lines from CFBD. Used for early spread/total display while SGO is capped.
  run_py "pull_cfbd_lines_2026.py" || echo "WARNING: CFBD season lines pull failed"
  run_py "scripts/odds/pull_actionnetwork_ncaaf_game_lines_2026.py" "pull_actionnetwork_ncaaf_game_lines_2026.py" || echo "WARNING: Action Network game lines pull failed"
  run_py "scripts/odds/build_actionnetwork_season_lines_2026.py" "build_actionnetwork_season_lines_2026.py" || echo "WARNING: Action Network season game lines build failed"
  run_py "build_season_game_lines_2026.py" || echo "WARNING: season game lines build failed"
    run_py "pull_theodds_ncaaf_lines_2026.py" || echo "WARNING: The Odds API line pull failed"
    run_py "build_theodds_season_lines_2026.py" || echo "WARNING: The Odds API line normalization failed"


  # Append today's normalized game lines before site/email rendering.
  run_py "scripts/odds/append_game_line_history.py" "append_game_line_history.py" || echo "WARNING: game line history append failed"
  run_py "scripts/odds/build_game_line_movement_report.py" "build_game_line_movement_report.py" || echo "WARNING: game line movement report build failed"

  echo "Using ~/NCAAF_AUTO/v1.html as the isolated legacy automation template."

  python3 build_market_futures_safe.py \
    --win-totals-csv "market_win_totals_import.csv" \
    --conference-futures-csv "market_conference_futures_import.csv" \
    --output-xlsx "market_futures_export.xlsx"

  python3 build_site_from_workbook_safe_with_movement.py \
    --workbook "2026_NCAA _Season.xlsm" \
    --template "v1.html" \
    --output "index_auto_market.html" \
    --cfbd-xlsx "cfbd_2026_export.xlsx" \
    --market-xlsx "market_futures_export.xlsx" \
    --movement-xlsx "market_movement_export.xlsx" \
      --season-lines-csv "data/odds/season_game_lines_2026.csv" \
      --theodds-lines-csv "data/odds/theodds_season_game_lines_2026.csv" \
      --action-lines-csv "data/odds/actionnetwork_season_game_lines_2026.csv"


  run_py "inject_daily_market_moves.py"
  run_py "inject_market_arbs.py"
  run_py "scripts/injuries/pull_cfbdepth_injuries.py" "pull_cfbdepth_injuries.py" || echo "WARNING: CFBDepth injury pull failed"
  run_py "scripts/injuries/pull_cfbdepth_article_bodies.py" "pull_cfbdepth_article_bodies.py" || echo "WARNING: CFBDepth injury article pull failed"
  run_py "scripts/injuries/build_injury_alerts.py" "build_injury_alerts.py" || echo "WARNING: injury alert build failed"
  run_py "scripts/agents/build_daily_betting_angles.py" "build_daily_betting_angles.py"
  run_py "scripts/agents/append_daily_game_line_edges.py" "append_daily_game_line_edges.py" || echo "WARNING: game line email edges append failed"

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
  run_py "scripts/agents/prepend_game_line_moves_to_daily_betting_angles.py" "prepend_game_line_moves_to_daily_betting_angles.py" || echo "WARNING: prepend game line moves to email failed"
  run_py "scripts/agents/prepend_injury_alerts_to_daily_betting_angles.py" "prepend_injury_alerts_to_daily_betting_angles.py" || echo "WARNING: prepend injury alerts failed"
  run_py "scripts/agents/clean_daily_game_line_moves.py" "clean_daily_game_line_moves.py" || echo "WARNING: daily game-line move cleaning failed"
  run_py "scripts/agents/build_daily_betting_angles_html.py" "build_daily_betting_angles_html.py"

  mkdir -p backups/html
  cp v1.html "backups/html/v1_before_daily_refresh_$(date +%Y%m%d_%H%M%S).html"
  cp index_auto_market.html v1.html
  echo "Legacy market artifact refreshed at index_auto_market.html and v1.html; canonical V2 index is unchanged."

  # These legacy HTML injectors target index.html directly and therefore must
  # not run in the V2 daily path. Their production data is supplied by the
  # canonical V2 JSON/view builders below. The legacy intermediate remains an
  # optional diagnostic artifact and is never a publication source.
  echo "Skipping legacy index injectors; V2 builders own the canonical site shell."
  run_py "scripts/injuries/build_game_injury_scores.py" "build_game_injury_scores.py" || echo "WARNING: game injury score build failed"

  # Ratings/projection maintenance. Pull/parse refreshes are optional because some sources may be inactive.
  run_py "scripts/ratings/pull_sagarin_ratings.py" "pull_sagarin_ratings.py" || echo "WARNING: Sagarin ratings refresh failed"
  run_py "scripts/ratings/parse_massey_visible_ratings.py" "parse_massey_visible_ratings.py" || echo "WARNING: Massey ratings refresh failed"
  run_py "scripts/ratings/pull_donchess_ratings.py" "pull_donchess_ratings.py" || echo "WARNING: Donchess ratings refresh failed"

  run_py "scripts/ratings/build_all_ratings_latest.py" "build_all_ratings_latest.py" || echo "WARNING: ratings latest build failed"
  run_py "scripts/ratings/append_ratings_history.py" "append_ratings_history.py" || echo "WARNING: ratings history append failed"
  run_py "scripts/ratings/build_ratings_movement.py" "build_ratings_movement.py" || echo "WARNING: ratings movement build failed"
  run_py "scripts/projections/build_game_projection_sources_2026.py" "build_game_projection_sources_2026.py" || echo "WARNING: game projection source build failed"
  run_py "scripts/projections/build_game_projection_blend_2026.py" "build_game_projection_blend_2026.py" || echo "WARNING: game projection blend build failed"

  # Shadow production bridge. Current selected market lines must already be in
  # matchups_view; completed-game results/PBP/game-control builders run through
  # the existing site build and postgame paths. These steps do no acquisition
  # and never refit the frozen movement models.
  run_py "scripts/site/build_matchups_view.py" "build_matchups_view.py"
  run_py "scripts/site/build_odds_screen_v1.py" "build_odds_screen_v1.py" || echo "WARNING: odds screen build failed"
  python3 scripts/research/build_market_implied_power_ratings.py --production-2026
  run_py "scripts/site/build_ratings_view.py" "build_ratings_view.py"
  python3 scripts/site/build_shadow_team_game_features.py --mode all
  python3 scripts/site/build_saturday_shadow_component_predictions.py
  python3 scripts/site/build_saturday_shadow_lines.py
  python3 scripts/site/build_schedule_live_enrichment.py
  python3 scripts/audit/audit_market_shadow_production_layer.py
  python3 scripts/audit/audit_saturday_shadow_production_integration.py

  # Refresh V2 Futures data after the canonical V1 site and projection outputs are final.
  # A failed or stale playoff-market pull does not block the rest of the site; the
  # Futures QA banner will surface the issue while cached data remains available.
  wait_for_network "api.actionnetwork.com"
  run_py "scripts/markets/pull_actionnetwork_playoff_futures.py" "pull_actionnetwork_playoff_futures.py" || echo "WARNING: Action Network playoff futures pull failed; using cached data where available"
  run_py "scripts/site/build_futures_view.py" "build_futures_view.py" || echo "WARNING: Futures V2 data build failed"

  # Refresh the production Odds page payloads after the current game and
  # futures sources are complete. Builders write atomically scoped Odds
  # artifacts; on failure the previous valid files remain available.
  run_py "scripts/site/build_odds_screen_v2.py" "build_odds_screen_v2.py" || echo "WARNING: Odds game payload build failed; retaining last valid artifact"
  run_py "scripts/site/build_odds_futures_v2.py" "build_odds_futures_v2.py" || echo "WARNING: Odds futures payload build failed; retaining last valid artifact"

  # Optional email send. Do not let missing Gmail env vars stop the market/site/rating build.
  if [ -n "${NCAAF_GMAIL_USER:-}" ] && [ -n "${NCAAF_GMAIL_APP_PASSWORD:-}" ] && [ -n "${NCAAF_EMAIL_TO:-}" ]; then
    run_py "scripts/email/send_daily_betting_angles_email.py" "send_daily_betting_angles_email.py" || echo "WARNING: daily betting angles email send failed"
  else
    echo "WARNING: Skipping email send because NCAAF_GMAIL_USER, NCAAF_GMAIL_APP_PASSWORD, or NCAAF_EMAIL_TO is missing"
  fi

  # Build and validate the canonical V2 public bundle. Publication is delegated
  # to the normal staged publisher so a legacy artifact can never be copied to
  # the public repository by this script.
  python3 scripts/site/build_public_site.py
  python3 scripts/audit/audit_canonical_v2_index.py index.html
  python3 scripts/audit/audit_canonical_v2_index.py build/public_site/index.html
  python3 scripts/publish/check_public_site.py
  if [ "${NCAAF_AUTO_PUBLISH:-1}" = "0" ]; then
    echo "NCAAF_AUTO_PUBLISH=0: validated V2 build; publication skipped"
  else
    bash scripts/publish/publish_site.sh --push
  fi

# cp market_win_totals_history.csv "$ICLOUD/"
  # cp market_conference_futures_history.csv "$ICLOUD/"
  # cp market_win_totals_movement.csv "$ICLOUD/"
  # cp market_conference_futures_movement.csv "$ICLOUD/"
  # cp market_movement_export.xlsx "$ICLOUD/"
  # cp market_futures_export.xlsx "$ICLOUD/"
  # cp index_auto_market.html "$ICLOUD/"

  echo "Daily market update finished: $(date)"
} >> "$LOG" 2>&1

# The install_* scripts below this point were one-time source migrations. They
# also write directly into the publication repository, so they are deliberately
# excluded from recurring automation. Their approved results live in the V2
# source files and are copied only by the staged publisher above.
