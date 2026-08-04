#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---check}"
RUNTIME_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PUBLIC_DIR="$RUNTIME_ROOT/build/public_site"
MAIN_REPO="${NCAAF_MAIN_REPO:-/Users/jameslindesmith/NCAAF_MAIN_REPO}"
MAX_ODDS_AGE_HOURS="${NCAAF_MAX_ODDS_AGE_HOURS:-18}"

log(){ printf '[canonical-publish] %s\n' "$*"; }
die(){ printf '[canonical-publish] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$MODE" == "--check" || "$MODE" == "--push" ]] || die "usage: $0 --check|--push"
[[ -d "$RUNTIME_ROOT/.git" ]] || log "runtime is not the publishing Git repository; using generated public artifacts only"
[[ -d "$PUBLIC_DIR" ]] || die "missing public build: $PUBLIC_DIR"
[[ -s "$PUBLIC_DIR/odds.html" ]] || die "missing public Odds page"
[[ -s "$PUBLIC_DIR/matchups.html" ]] || die "missing public Matchups page"
[[ -s "$PUBLIC_DIR/data/site/odds_screen_v2.json" ]] || die "missing public odds payload"
[[ -s "$PUBLIC_DIR/data/site/matchups_view.json" ]] || die "missing public matchup payload"

# Use the project's established public-site validator when available.
if [[ -f "$RUNTIME_ROOT/scripts/publish/check_public_site.py" ]]; then
  (
    cd "$RUNTIME_ROOT"
    python3 scripts/publish/check_public_site.py
  )
fi

python3 - "$PUBLIC_DIR/data/site/odds_screen_v2.json" "$MAX_ODDS_AGE_HOURS" <<'PY'
from datetime import datetime, timezone
from pathlib import Path
import sys

path = Path(sys.argv[1])
limit = float(sys.argv[2])
age_hours = (datetime.now(timezone.utc).timestamp() - path.stat().st_mtime) / 3600
print(f"[canonical-publish] odds payload age: {age_hours:.2f} hours")
if age_hours > limit:
    raise SystemExit(
        f"odds payload is {age_hours:.1f}h old; refusing to publish "
        f"(limit {limit:.1f}h, override with NCAAF_MAX_ODDS_AGE_HOURS)"
    )
PY

log "public build validation passed"
[[ "$MODE" == "--push" ]] || exit 0

[[ -d "$MAIN_REPO/.git" ]] || die "canonical repository not found: $MAIN_REPO"
[[ -f "$MAIN_REPO/scripts/site/build_war_room_home.py" ]] || \
  die "locked War Room homepage builder missing from canonical repository"

# Tracked changes are unsafe because this process is about to update generated
# production assets. Untracked design previews are intentionally ignored.
TRACKED_DIRTY="$(git -C "$MAIN_REPO" status --porcelain --untracked-files=no)"
[[ -z "$TRACKED_DIRTY" ]] || {
  printf '%s\n' "$TRACKED_DIRTY" >&2
  die "canonical repository has tracked local changes; review them before the daily publish"
}

log "synchronizing canonical repository with origin/main"
git -C "$MAIN_REPO" fetch origin main
git -C "$MAIN_REPO" checkout main
git -C "$MAIN_REPO" pull --ff-only origin main

TMP_MANIFEST="$(mktemp)"
PUBLISH_COMMITTED=0
cleanup(){
  rc=$?
  rm -f "$TMP_MANIFEST"
  if [[ $rc -ne 0 && "$PUBLISH_COMMITTED" = "0" ]]; then
    log "publish failed before commit; restoring tracked canonical worktree"
    git -C "$MAIN_REPO" reset --hard origin/main >/dev/null 2>&1 || true
  fi
  exit $rc
}
trap cleanup EXIT

# Copy generated public files to the canonical repo, but never replace the
# locked War Room homepage or the temporary Coaches landing page.
python3 - "$PUBLIC_DIR" "$MAIN_REPO" "$TMP_MANIFEST" <<'PY'
from pathlib import Path
import hashlib
import shutil
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
manifest = Path(sys.argv[3])

excluded = {
    Path("index.html"),      # locked War Room homepage
    Path("coaches.html"),    # reserved Coaches landing page
}
changed = []

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

for src in sorted(source.rglob("*")):
    if not src.is_file():
        continue
    rel = src.relative_to(source)
    if rel in excluded:
        continue
    dst = target / rel
    if dst.exists() and digest(src) == digest(dst):
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    changed.append(rel.as_posix())

manifest.write_text("\n".join(changed) + ("\n" if changed else ""), encoding="utf-8")
print(f"[canonical-publish] synchronized {len(changed)} changed public files")
for rel in changed[:30]:
    print(f"[canonical-publish]   {rel}")
if len(changed) > 30:
    print(f"[canonical-publish]   ... and {len(changed)-30} more")
PY

# Rebuild the locked homepage after data synchronization. This preserves its
# design and navigation while allowing it to read the newly published JSON.
(
  cd "$MAIN_REPO"
  PYTHONPATH="$MAIN_REPO" python3 scripts/site/build_war_room_home.py
)

grep -q 'data-war-room-home-release=' "$MAIN_REPO/index.html" || \
  die "locked War Room homepage marker disappeared"
grep -q 'data/site/matchups_view.json' "$MAIN_REPO/index.html" || \
  die "War Room homepage no longer references the matchup market payload"
grep -q 'data/site/matchup_line_history.json' "$MAIN_REPO/index.html" || \
  die "War Room homepage no longer references line history"

# Stage only files synchronized by this publisher plus the regenerated homepage.
if [[ -s "$TMP_MANIFEST" ]]; then
  git -C "$MAIN_REPO" add --pathspec-from-file="$TMP_MANIFEST"
fi
git -C "$MAIN_REPO" add index.html

if git -C "$MAIN_REPO" diff --cached --quiet; then
  log "no public data changes to commit"
  exit 0
fi

STAMP="$(date +%Y-%m-%d)"
git -C "$MAIN_REPO" commit -m "Daily NCAAF data update $STAMP"
PUBLISH_COMMITTED=1

# A site-design commit may land while the refresh is running. Rebase the data
# commit once rather than failing on a non-fast-forward push.
if ! git -C "$MAIN_REPO" push origin main; then
  log "remote main moved during publish; rebasing once"
  git -C "$MAIN_REPO" pull --rebase origin main
  git -C "$MAIN_REPO" push origin main
fi

log "published canonical main at $(git -C "$MAIN_REPO" rev-parse --short HEAD)"
