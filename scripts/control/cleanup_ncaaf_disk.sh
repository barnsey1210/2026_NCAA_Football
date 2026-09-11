#!/bin/bash
set -u

MAIN="/Users/jameslindesmith/NCAAF_MAIN_REPO"
AUTO="/Users/jameslindesmith/NCAAF_AUTO"

ROLLBACK_DIR="$AUTO/.deploy_rollback"
ACCEPTANCE_DIR="$AUTO/data/control/acceptance_dry_runs"

KEEP_ROLLBACKS=5
ACCEPTANCE_MAX_AGE_DAYS=7

MODE="dry-run"

if [ "${1:-}" = "--apply" ]; then
  MODE="apply"
elif [ "${1:-}" = "--dry-run" ] || [ -z "${1:-}" ]; then
  MODE="dry-run"
else
  echo "Usage: $0 [--dry-run|--apply]"
  exit 2
fi

echo "============================================"
echo " NCAAF operational disk cleanup"
echo " Mode: $MODE"
echo "============================================"
echo

show_size() {
  if [ -e "$1" ]; then
    du -sh "$1" 2>/dev/null | awk '{print $1}'
  else
    echo "0B"
  fi
}

remove_path() {
  target="$1"
  reason="$2"

  [ -e "$target" ] || return 0

  size="$(show_size "$target")"
  echo "[$MODE] $reason"
  echo "  $target  ($size)"

  if [ "$MODE" = "apply" ]; then
    rm -rf "$target"
  fi
}

echo "Disk before:"
df -h / | tail -1
echo

# ---------------------------------------------------------
# 1. Deployment rollback retention
# Keep newest KEEP_ROLLBACKS snapshots only.
# ---------------------------------------------------------

echo "== Deployment rollback retention =="

if [ -d "$ROLLBACK_DIR" ]; then
  count="$(find "$ROLLBACK_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
  echo "Found $count rollback snapshots; keeping newest $KEEP_ROLLBACKS."

  ls -1dt "$ROLLBACK_DIR"/*/ 2>/dev/null \
    | tail -n +"$((KEEP_ROLLBACKS + 1))" \
    | while IFS= read -r path; do
        [ -n "$path" ] || continue
        remove_path "${path%/}" "Old deployment rollback"
      done
else
  echo "No rollback directory found."
fi

echo

# ---------------------------------------------------------
# 2. Old acceptance dry runs
# Only this explicitly disposable test-workspace directory.
# ---------------------------------------------------------

echo "== Acceptance dry-run retention =="

if [ -d "$ACCEPTANCE_DIR" ]; then
  find "$ACCEPTANCE_DIR" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -mtime +"$ACCEPTANCE_MAX_AGE_DAYS" \
    -print 2>/dev/null \
    | while IFS= read -r path; do
        remove_path "$path" "Acceptance dry run older than ${ACCEPTANCE_MAX_AGE_DAYS} days"
      done
else
  echo "No acceptance_dry_runs directory found."
fi

echo

# ---------------------------------------------------------
# 3. Regenerable public/build artifacts
# ---------------------------------------------------------

echo "== Regenerable build artifacts =="

remove_path "$MAIN/build/cloudflare_pages" \
  "Regenerable Cloudflare Pages bundle"

remove_path "$MAIN/build/public_site" \
  "Regenerable MAIN public-site bundle"

remove_path "$AUTO/build/public_site" \
  "Regenerable AUTO public-site bundle"

remove_path "$MAIN/build/war_room_home_release_backups" \
  "Old generated War Room release backups"

echo

# ---------------------------------------------------------
# 4. Python / pytest caches
# ---------------------------------------------------------

echo "== Python/test caches =="

for root in "$MAIN" "$AUTO"; do
  find "$root" \
    -type d \
    \( -name '__pycache__' -o -name '.pytest_cache' \) \
    -prune \
    -print 2>/dev/null \
    | while IFS= read -r path; do
        remove_path "$path" "Regenerable Python/test cache"
      done
done

echo

# ---------------------------------------------------------
# 5. Registered temporary NCAAF Git worktrees
#
# Only removes worktrees:
#   - registered with MAIN's Git repository
#   - physically under /private/tmp/
#   - whose basename starts with ncaaf
#
# It will never remove MAIN itself or an arbitrary temp dir.
# ---------------------------------------------------------

echo "== Temporary Git worktrees =="

if git -C "$MAIN" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$MAIN" worktree list --porcelain \
    | sed -n 's/^worktree //p' \
    | while IFS= read -r wt; do

        case "$wt" in
          /private/tmp/ncaaf*|/private/tmp/ncaaf_*)
            size="$(show_size "$wt")"
            echo "[$MODE] Registered temporary NCAAF worktree"
            echo "  $wt  ($size)"

            if [ "$MODE" = "apply" ]; then
              git -C "$MAIN" worktree remove --force "$wt" || {
                echo "WARNING: could not remove worktree: $wt"
              }
            fi
            ;;
        esac
      done

  if [ "$MODE" = "apply" ]; then
    git -C "$MAIN" worktree prune
  else
    echo "[dry-run] Would run: git worktree prune"
  fi
else
  echo "MAIN is not available as a Git repository; skipping worktree cleanup."
fi

echo

# ---------------------------------------------------------
# FINAL STATUS
# ---------------------------------------------------------

echo "============================================"

if [ "$MODE" = "dry-run" ]; then
  echo "DRY RUN COMPLETE — nothing was deleted."
  echo
  echo "Review the list above, then run:"
  echo "  $0 --apply"
else
  echo "CLEANUP COMPLETE"
  echo
  echo "Remaining rollback storage:"
  du -sh "$ROLLBACK_DIR" 2>/dev/null || true

  echo
  echo "Registered Git worktrees:"
  git -C "$MAIN" worktree list 2>/dev/null || true

  echo
  echo "Disk after:"
  df -h / | tail -1
fi

echo "============================================"
