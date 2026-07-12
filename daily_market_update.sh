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


  echo "Using ~/NCAAF_AUTO/index.html as automation baseline template. No iCloud copy is performed."

  python3 build_market_futures_safe.py \
    --win-totals-csv "market_win_totals_import.csv" \
    --conference-futures-csv "market_conference_futures_import.csv" \
    --output-xlsx "market_futures_export.xlsx"

  
# Active 2026 ratings/projection refresh must happen before HTML site build.
run_py "build_all_ratings_latest.py" "build_all_ratings_latest.py" || echo "WARNING: ratings latest build failed"
run_py "scripts/ratings/build_active_2026_ratings_master.py" "build_active_2026_ratings_master.py" || echo "WARNING: active 2026 ratings master build failed"
run_py "append_ratings_history.py" "append_ratings_history.py" || echo "WARNING: ratings history append failed"
run_py "build_ratings_movement.py" "build_ratings_movement.py" || echo "WARNING: ratings movement build failed"
run_py "build_game_projection_sources_2026.py" "build_game_projection_sources_2026.py" || echo "WARNING: game projection source build failed"
run_py "build_game_projection_blend_2026.py" "build_game_projection_blend_2026.py" || echo "WARNING: game projection blend build failed"

python3 build_site_from_workbook_safe_with_movement.py \
    --workbook "2026_NCAA _Season.xlsm" \
    --template "index.html" \
    --output "index_auto_market.html" \
    --cfbd-xlsx "cfbd_2026_export.xlsx" \
    --market-xlsx "market_futures_export.xlsx" \
    --movement-xlsx "market_movement_export.xlsx" \
      --season-lines-csv "data/odds/season_game_lines_2026.csv" \
      --theodds-lines-csv "data/odds/theodds_season_game_lines_2026.csv" \
      --action-lines-csv "data/odds/actionnetwork_season_game_lines_2026.csv"

  run_py "scripts/odds/append_game_line_history.py" "append_game_line_history.py" || echo "WARNING: game line history append failed"
  run_py "scripts/odds/build_game_line_movement_report.py" "build_game_line_movement_report.py" || echo "WARNING: game line movement report build failed"

  run_py "inject_daily_market_moves.py"
  run_py "inject_market_arbs.py"
run_py "scripts/injuries/pull_cfbdepth_injuries.py" "pull_cfbdepth_injuries.py" || echo "WARNING: CFBDepth injury pull failed"
run_py "scripts/injuries/pull_cfbdepth_article_bodies.py" "pull_cfbdepth_article_bodies.py" || echo "WARNING: CFBDepth injury article pull failed"
run_py "scripts/injuries/build_injury_alerts.py" "build_injury_alerts.py" || echo "WARNING: injury alert build failed"
run_py "scripts/agents/build_daily_betting_angles.py" "build_daily_betting_angles.py"
run_py "scripts/agents/postprocess_daily_betting_angles_display.py" "postprocess_daily_betting_angles_display.py" || echo "WARNING: betting angles display postprocess failed"
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

  run_py "scripts/agents/build_daily_betting_angles_html.py" "build_daily_betting_angles_html.py"
  run_py "scripts/agents/prepend_game_line_moves_to_daily_betting_angles.py" "prepend_game_line_moves_to_daily_betting_angles.py" || echo "WARNING: prepend game line moves to email failed"
run_py "scripts/agents/prepend_injury_alerts_to_daily_betting_angles.py" "prepend_injury_alerts_to_daily_betting_angles.py" || echo "WARNING: prepend injury alerts failed"

  mkdir -p backups/html
  cp index.html "backups/html/index_before_daily_promote_$(date +%Y%m%d_%H%M%S).html"
  cp index_auto_market.html index.html
  cp index_auto_market.html index_publish.html
  echo "Promoted fresh build to index.html and index_publish.html"

  run_py "scripts/odds/clear_stale_fallback_game_lines_from_site.py" "clear_stale_fallback_game_lines_from_site.py" || echo "WARNING: stale fallback game-line cleanup failed"
  run_py "scripts/site/fix_projection_spread_mismatches.py" "fix_projection_spread_mismatches.py" || echo "WARNING: projection spread mismatch fix failed"
  run_py "scripts/site/fix_projection_rating_mismatches.py" "fix_projection_rating_mismatches.py" || echo "WARNING: projection rating mismatch fix failed"
  run_py "scripts/odds/restore_action_market_metadata_to_site.py" "restore_action_market_metadata_to_site.py" || echo "WARNING: restore Action market metadata failed"
  run_py "scripts/market/build_intraday_win_total_moves.py" "build_intraday_win_total_moves.py" || echo "WARNING: intraday win total moves failed"
run_py "scripts/coach/build_coach_fav_dog_splits_all_periods.py" "build_coach_fav_dog_splits_all_periods.py" || echo "WARNING: coach favorite/dog splits failed"
run_py "scripts/coach/build_coach_full_game_fav_dog_cfbd.py" "build_coach_full_game_fav_dog_cfbd.py" || echo "WARNING: coach full-game CFBD fav/dog splits failed"
run_py "scripts/coach/build_coach_fav_dog_splits_hybrid.py" "build_coach_fav_dog_splits_hybrid.py" || echo "WARNING: coach hybrid fav/dog splits failed"
run_py "scripts/coach/build_game_coach_fav_dog_context.py" "build_game_coach_fav_dog_context.py" || echo "WARNING: game coach favorite/dog context failed"
run_py "scripts/site/inject_coach_fav_dog_context.py" "inject_coach_fav_dog_context.py" || echo "WARNING: coach favorite/dog context injection failed"
run_py "scripts/site/inject_matchup_coach_fav_dog_context.py" "inject_matchup_coach_fav_dog_context.py" || echo "WARNING: matchup coach favorite/dog context injection failed"
run_py "scripts/site/inject_coach_fav_dog_trends_page.py" "inject_coach_fav_dog_trends_page.py" || echo "WARNING: coach fav/dog trends page injection failed"
run_py "scripts/site/inject_rp_support_badges.py" "inject_rp_support_badges.py" || echo "WARNING: RP support badge injection failed"
run_py "scripts/markets/pull_sgo_ncaaf_game_odds.py" "pull_sgo_ncaaf_game_odds.py" || echo "WARNING: SGO NCAAF game odds pull failed"
run_py "scripts/markets/parse_sgo_ncaaf_game_odds.py" "parse_sgo_ncaaf_game_odds.py" || echo "WARNING: SGO NCAAF game odds parse failed"
run_py "scripts/site/inject_sgo_game_odds.py" "inject_sgo_game_odds.py" || echo "WARNING: SGO NCAAF game odds injection failed"
run_py "scripts/site/inject_opening_possession_main_badges.py" "inject_opening_possession_main_badges.py" || echo "WARNING: opening possession main badge injection failed"
run_py "scripts/site/inject_opening_possession_matchup.py" "inject_opening_possession_matchup.py" || echo "WARNING: opening possession matchup injection failed"
run_py "scripts/signals/build_travel_1h_signals_2026.py" "build_travel_1h_signals_2026.py" || echo "WARNING: travel 1H signal build failed"
run_py "scripts/site/inject_travel_1h_badges.py" "inject_travel_1h_badges.py" || echo "WARNING: travel 1H badge injection failed"
run_py "scripts/site/inject_home_dashboard_data.py" "inject_home_dashboard_data.py"
run_py "scripts/site/patch_dashboard_all_market_moves.py" "patch_dashboard_all_market_moves.py" || echo "WARNING: all market moves dashboard patch failed"
  run_py "scripts/injuries/build_game_injury_scores.py" "build_game_injury_scores.py" || echo "WARNING: game injury score build failed"
  run_py "scripts/site/inject_game_injury_overlay.py" "inject_game_injury_overlay.py" || echo "WARNING: game injury overlay injection failed"
  run_py "scripts/ratings/pull_sagarin_ratings.py" "pull_sagarin_ratings.py" || echo "WARNING: Sagarin ratings refresh failed"
  run_py "scripts/ratings/parse_massey_visible_ratings.py" "parse_massey_visible_ratings.py" || echo "WARNING: Massey ratings refresh failed"
  run_py "scripts/ratings/pull_donchess_ratings.py" "pull_donchess_ratings.py" || echo "WARNING: Donchess ratings refresh failed"
  run_py "scripts/ratings/test_rating_sources.py" "test_rating_sources.py" || echo "WARNING: ratings source pull/test failed"
  run_py "scripts/ratings/parse_rating_source_tables.py" "parse_rating_source_tables.py" || echo "WARNING: ratings source table parse failed"
  run_py "scripts/ratings/parse_kford_text.py" "parse_kford_text.py" || run_py "scripts/ratings/parse_kford_manual.py" "parse_kford_manual.py" || echo "WARNING: KFord parse failed"
  run_py "scripts/ratings/parse_bradpowers_pdf.py" "parse_bradpowers_pdf.py" || echo "WARNING: Brad Powers PDF parse failed"
  # DISABLED: moved before site build / root script is canonical
# run_py "scripts/ratings/build_all_ratings_latest.py" "build_all_ratings_latest.py" || echo "WARNING: ratings latest build failed"
  run_py "scripts/ratings/append_ratings_history.py" "append_ratings_history.py" || echo "WARNING: ratings history append failed"
  run_py "scripts/ratings/build_ratings_movement.py" "build_ratings_movement.py" || echo "WARNING: ratings movement build failed"
  run_py "scripts/audit/audit_ratings_source_freshness.py" "audit_ratings_source_freshness.py" || echo "WARNING: ratings source freshness audit failed"

  # DISABLED 2026-07-11: can overwrite blended projections back to rating-only lines
# python3 scripts/audit/fix_game_projection_spreads_from_current_ratings.py --apply || echo "WARNING: projection spread fix failed"
run_py "scripts/weather/pull_open_meteo_game_weather.py" "pull_open_meteo_game_weather.py" || echo "WARNING: weather pull failed"
run_py "scripts/history/append_game_line_model_history.py" "append_game_line_model_history.py" || echo "WARNING: game line/model history append failed"
run_py "scripts/betting/pull_google_sheet_bets.py" "pull_google_sheet_bets.py" || echo "WARNING: betting sheet pull failed"
run_py "scripts/betting/build_betting_dashboard.py" "build_betting_dashboard.py" || echo "WARNING: betting dashboard build failed"
run_py "scripts/betting/enrich_betting_current_clv.py" "enrich_betting_current_clv.py" || echo "WARNING: betting current CLV enrichment failed"
run_py "scripts/betting/freeze_betting_closing_clv.py" "freeze_betting_closing_clv.py" || echo "WARNING: betting closing CLV freeze failed"
# DISABLED temporarily: betting dashboard inject broke site navigation
run_py "scripts/site/inject_betting_dashboard.py" "inject_betting_dashboard.py" || echo "WARNING: betting dashboard inject failed"
run_py "scripts/site/build_matchup_page.py" "build_matchup_page.py" || echo "WARNING: matchup page build failed"
run_py "scripts/site/patch_game_line_move_display_clean.py" "patch_game_line_move_display_clean.py" || echo "WARNING: game line move display patch failed"
run_py "scripts/site/patch_market_moves_arbs_display_clean.py" "patch_market_moves_arbs_display_clean.py" || echo "WARNING: market moves/arbs display patch failed"
run_py "scripts/audit/audit_game_projection_spreads.py" "audit_game_projection_spreads.py" || echo "WARNING: projection spread audit failed"
run_py "scripts/audit/audit_game_projection_totals_v2.py" "audit_game_projection_totals_v2.py" || echo "WARNING: projection total audit failed"
run_py "scripts/site/build_daily_run_health.py" "build_daily_run_health.py" || echo "WARNING: daily run health build failed"
  run_py "scripts/site/inject_coach_halves_from_csv.py" "inject_coach_halves_from_csv.py" || echo "WARNING: coach halves CSV inject failed"
  run_py "scripts/site/clean_site_chrome.py" "clean_site_chrome.py" || echo "WARNING: site chrome cleanup failed"

  # Ratings/projection maintenance. Pull/parse refreshes are optional because some sources may be inactive.

  # DISABLED: moved before site build
# run_py "scripts/projections/build_game_projection_sources_2026.py" "build_game_projection_sources_2026.py" || echo "WARNING: game projection source build failed"
  # DISABLED: moved before site build
# run_py "scripts/projections/build_game_projection_blend_2026.py" "build_game_projection_blend_2026.py" || echo "WARNING: game projection blend build failed"

  # Optional email send. Do not let missing Gmail env vars stop the market/site/rating build.
  if [ -n "${NCAAF_GMAIL_USER:-}" ] && [ -n "${NCAAF_GMAIL_APP_PASSWORD:-}" ] && [ -n "${NCAAF_EMAIL_TO:-}" ]; then
    run_py "scripts/email/send_daily_betting_angles_email.py" "send_daily_betting_angles_email.py" || echo "WARNING: daily betting angles email send failed"
  else
    echo "WARNING: Skipping email send because NCAAF_GMAIL_USER, NCAAF_GMAIL_APP_PASSWORD, or NCAAF_EMAIL_TO is missing"
  fi



  # AUTO_GITHUB_PUBLISH_START
  # Publish the freshly built site to the GitHub Pages repo after sanity checks.
  PUBLISH_REPO="$HOME/Sites/NCAAF_SITE"

  if [ -d "$PUBLISH_REPO/.git" ]; then
    echo "Running GitHub publish sanity check..."
    if python3 scripts/publish/check_index_before_publish.py; then
      echo "Copying fresh site files to GitHub Pages repo..."
      cp index.html "$PUBLISH_REPO/index.html"
      [ -f matchup.html ] && cp matchup.html "$PUBLISH_REPO/matchup.html"

      mkdir -p "$PUBLISH_REPO/data/bets"
      [ -f data/bets/bets_enriched.csv ] && cp data/bets/bets_enriched.csv "$PUBLISH_REPO/data/bets/bets_enriched.csv"
      [ -f data/bets/betting_dashboard.json ] && cp data/bets/betting_dashboard.json "$PUBLISH_REPO/data/bets/betting_dashboard.json"
      [ -f data/bets/market_clv_match_audit.csv ] && cp data/bets/market_clv_match_audit.csv "$PUBLISH_REPO/data/bets/market_clv_match_audit.csv"
      [ -f data/bets/betting_performance_history.csv ] && cp data/bets/betting_performance_history.csv "$PUBLISH_REPO/data/bets/betting_performance_history.csv"
      [ -f data/bets/bet_closing_clv.csv ] && cp data/bets/bet_closing_clv.csv "$PUBLISH_REPO/data/bets/bet_closing_clv.csv"
      [ -f data/bets/bet_closing_clv_audit.csv ] && cp data/bets/bet_closing_clv_audit.csv "$PUBLISH_REPO/data/bets/bet_closing_clv_audit.csv"

      echo "Publishing to GitHub Pages repo..."
      cd "$PUBLISH_REPO"
      git status --short
      git add index.html matchup.html data/bets
      git commit -m "Daily NCAAF market update $(date +%Y-%m-%d)" || echo "No changes to commit"
      git push || echo "WARNING: GitHub push failed"
      cd "$HOME/NCAAF_AUTO"
    else
      echo "WARNING: publish sanity check failed; skipping GitHub publish"
    fi
  else
    echo "WARNING: GitHub publish repo not found at $PUBLISH_REPO"
  fi
  # AUTO_GITHUB_PUBLISH_END

  # cp market_win_totals_history.csv "$ICLOUD/"
  # cp market_conference_futures_history.csv "$ICLOUD/"
  # cp market_win_totals_movement.csv "$ICLOUD/"
  # cp market_conference_futures_movement.csv "$ICLOUD/"
  # cp market_movement_export.xlsx "$ICLOUD/"
  # cp market_futures_export.xlsx "$ICLOUD/"
  # cp index_auto_market.html "$ICLOUD/"

  echo "Daily market update finished: $(date)"
} >> "$LOG" 2>&1
run_py "scripts/site/cleanup_literal_newline_rows.py" "cleanup_literal_newline_rows.py" || echo "WARNING: literal newline cleanup failed"
run_py "scripts/site/cleanup_stale_projection_audit_notes.py" "cleanup_stale_projection_audit_notes.py" || echo "WARNING: stale projection audit cleanup failed"
run_py "scripts/site/inject_active_ratings_rankings_ui.py" "inject_active_ratings_rankings_ui.py" || echo "WARNING: active ratings rankings UI injection failed"
