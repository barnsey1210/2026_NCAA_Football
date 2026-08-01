#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_REMOTE="https://github.com/barnsey1210/2026_NCAA_Football.git"
DEFAULT_TARGET="/Users/jameslindesmith/NCAAF_AUTO"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
EXPECTED_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
MANIFEST="$SCRIPT_DIR/source_manifest.txt"
TARGET="$DEFAULT_TARGET"
ALLOW_DIRTY=0

usage() {
  cat <<'EOF'
Usage: deploy/deploy_to_auto.sh [--target ABSOLUTE_PATH] [--manifest FILE] [--allow-dirty]

Copies only regular files explicitly listed in the manifest from the authoritative
Git repository to an operational runtime workspace. The working tree must be clean
unless --allow-dirty is supplied deliberately.
EOF
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

while (($#)); do
  case "$1" in
    --target) (($# >= 2)) || die "--target requires a value"; TARGET="$2"; shift 2 ;;
    --manifest) (($# >= 2)) || die "--manifest requires a value"; MANIFEST="$2"; shift 2 ;;
    --allow-dirty) ALLOW_DIRTY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

command -v git >/dev/null || die "git is required"
command -v python3 >/dev/null || die "python3 is required"

SOURCE_ROOT="$(git -C "$EXPECTED_ROOT" rev-parse --show-toplevel 2>/dev/null)" \
  || die "deployment script is not inside a Git repository"
SOURCE_ROOT="$(cd -- "$SOURCE_ROOT" && pwd -P)"
[[ "$SOURCE_ROOT" == "$EXPECTED_ROOT" ]] \
  || die "detected source repository root is not the expected script repository: $SOURCE_ROOT"

origin="$(git -C "$SOURCE_ROOT" remote get-url origin 2>/dev/null || true)"
case "$origin" in
  "$EXPECTED_REMOTE"|"${EXPECTED_REMOTE%.git}"|git@github.com:barnsey1210/2026_NCAA_Football.git)
    ;;
  *) die "unexpected origin remote for authoritative repository: ${origin:-missing}" ;;
esac

SOURCE_COMMIT="$(git -C "$SOURCE_ROOT" rev-parse HEAD)"
if (( ! ALLOW_DIRTY )) && [[ -n "$(git -C "$SOURCE_ROOT" status --porcelain --untracked-files=normal)" ]]; then
  die "source working tree is not clean; commit/review changes first or use --allow-dirty explicitly"
fi

[[ "$TARGET" = /* ]] || die "target must be an absolute path"
mkdir -p -- "$TARGET"
TARGET="$(cd -- "$TARGET" && pwd -P)"
[[ "$TARGET" != "/" ]] || die "refusing filesystem-root target"
[[ "$TARGET" != "$SOURCE_ROOT" && "$TARGET" != "$SOURCE_ROOT"/* ]] \
  || die "target must be outside the authoritative source repository"
[[ -f "$MANIFEST" ]] || die "manifest not found: $MANIFEST"

declare -a PATHS=()
line_no=0
while IFS= read -r raw || [[ -n "$raw" ]]; do
  line_no=$((line_no + 1))
  path="${raw%$'\r'}"
  [[ -n "$path" ]] || die "empty manifest path at line $line_no"
  [[ "$path" != /* ]] || die "absolute manifest path rejected at line $line_no: $path"
  [[ "$path" != "." && "$path" != ".." && "$path" != ../* && "$path" != */../* && "$path" != */.. ]] \
    || die "path traversal rejected at line $line_no: $path"
  [[ "$path" != */ ]] || die "directory-style manifest path rejected at line $line_no: $path"
  for existing in "${PATHS[@]:-}"; do
    [[ "$existing" != "$path" ]] || die "duplicate manifest path at line $line_no: $path"
  done

  source_path="$SOURCE_ROOT/$path"
  [[ -e "$source_path" ]] || die "missing source file at line $line_no: $path"
  [[ -f "$source_path" && ! -L "$source_path" ]] || die "manifest entry is not a regular non-symlink file: $path"
  resolved="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$source_path")"
  [[ "$resolved" == "$SOURCE_ROOT"/* ]] || die "source path escapes repository root: $path"
  PATHS+=("$path")
done < "$MANIFEST"
(( ${#PATHS[@]} > 0 )) || die "manifest contains no files"

printf 'Source repository: %s\n' "$SOURCE_ROOT"
printf 'Source commit: %s\n' "$SOURCE_COMMIT"
printf 'Target runtime: %s\n' "$TARGET"
printf 'Manifest: %s (%d files)\n' "$MANIFEST" "${#PATHS[@]}"

# Validate source syntax before changing any runtime file.
for path in "${PATHS[@]}"; do
  case "$path" in
    *.sh) bash -n "$SOURCE_ROOT/$path" ;;
    *.py) PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/ncaaf-deploy-pycache" python3 -m py_compile "$SOURCE_ROOT/$path" ;;
  esac
done

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT="$TARGET/.deploy_rollback/${timestamp}-${SOURCE_COMMIT:0:12}"
mkdir -p -- "$BACKUP_ROOT"
declare -a COPIED=()
declare -a BACKED_UP=()

deployment_failed() {
  rc=$?
  trap - ERR
  printf '\nDEPLOYMENT FAILED after runtime copying began (exit %d).\n' "$rc" >&2
  printf 'Backup location: %s\n' "$BACKUP_ROOT" >&2
  printf 'Rollback: copy files from %s back to %s preserving relative paths.\n' "$BACKUP_ROOT" "$TARGET" >&2
  exit "$rc"
}
trap deployment_failed ERR

for path in "${PATHS[@]}"; do
  src="$SOURCE_ROOT/$path"
  dest="$TARGET/$path"
  dest_dir="$(dirname -- "$dest")"
  mkdir -p -- "$dest_dir"
  resolved_dest_dir="$(cd -- "$dest_dir" && pwd -P)"
  [[ "$resolved_dest_dir" == "$TARGET" || "$resolved_dest_dir" == "$TARGET"/* ]] \
    || die "runtime destination parent escapes target through a symlink: $path"

  if [[ -e "$dest" || -L "$dest" ]]; then
    [[ -f "$dest" && ! -L "$dest" ]] || die "runtime destination is not a regular non-symlink file: $dest"
    backup="$BACKUP_ROOT/$path"
    mkdir -p -- "$(dirname -- "$backup")"
    cp -p -- "$dest" "$backup"
    BACKED_UP+=("$path")
  fi

  tmp="$(mktemp "$dest_dir/.deploy.$(basename -- "$dest").XXXXXX")"
  trap 'rm -f -- "${tmp:-}"' EXIT
  cp -p -- "$src" "$tmp"
  mv -f -- "$tmp" "$dest"
  tmp=""
  trap - EXIT
  COPIED+=("$path")
done

for path in "${PATHS[@]}"; do
  case "$path" in
    *.sh) bash -n "$TARGET/$path" ;;
    *.py) PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/ncaaf-deploy-pycache" python3 -m py_compile "$TARGET/$path" ;;
  esac
done

EMAIL_TEST="scripts/audit/test_daily_betting_email_regression.py"
EMAIL_CSV="$TARGET/data/agents/daily_betting_angles.csv"
EMAIL_HTML="$TARGET/data/agents/daily_betting_angles.html"
if [[ -f "$TARGET/$EMAIL_TEST" && -f "$EMAIL_CSV" && -f "$EMAIL_HTML" ]]; then
  (cd "$TARGET" && python3 "$EMAIL_TEST")
  EMAIL_RESULT="PASSED"
else
  EMAIL_RESULT="SKIPPED (required runtime CSV/HTML fixtures are absent)"
  printf 'SKIP: daily betting email regression; required artifacts absent in target\n'
fi

printf '\nDEPLOYMENT PASSED\n'
printf 'Source commit: %s\n' "$SOURCE_COMMIT"
printf 'Copied files (%d):\n' "${#COPIED[@]}"
printf '  %s\n' "${COPIED[@]}"
printf 'Backup location: %s\n' "$BACKUP_ROOT"
printf 'Backed-up files: %d\n' "${#BACKED_UP[@]}"
printf 'Shell/Python syntax validation: PASSED\n'
printf 'Email regression: %s\n' "$EMAIL_RESULT"
printf 'Rollback: copy files from %s back to %s preserving relative paths.\n' "$BACKUP_ROOT" "$TARGET"
trap - ERR
