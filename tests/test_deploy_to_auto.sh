#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
DEPLOY="$ROOT/deploy/deploy_to_auto.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/ncaaf-deploy-test.XXXXXX")"
DIRTY_MARKER="$ROOT/.deploy_test_dirty_marker"
BAD_SHELL="$ROOT/tests/.deploy_bad_syntax.sh"
BAD_PYTHON="$ROOT/tests/.deploy_bad_syntax.py"
trap 'rm -rf -- "$TMP"; rm -f -- "$DIRTY_MARKER" "$BAD_SHELL" "$BAD_PYTHON"' EXIT

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
expect_fail() {
  local label="$1"; shift
  if "$@" >"$TMP/$label.out" 2>&1; then
    fail "$label unexpectedly succeeded"
  fi
  printf 'PASS: rejected %s\n' "$label"
}

runtime="$TMP/runtime"
mkdir -p "$runtime/scripts/markets"
printf 'leave me alone\n' > "$runtime/unlisted.txt"
printf 'old runtime content\n' > "$runtime/daily_market_update.sh"

printf 'temporary dirty-tree fixture\n' > "$DIRTY_MARKER"
expect_fail dirty-tree bash "$DEPLOY" --target "$TMP/dirty-runtime"
grep -q 'source working tree is not clean' "$TMP/dirty-tree.out" || fail "dirty-tree rejection was not explicit"
rm -f -- "$DIRTY_MARKER"

output="$TMP/deploy.out"
bash "$DEPLOY" --target "$runtime" --allow-dirty >"$output"
cmp -s "$ROOT/daily_market_update.sh" "$runtime/daily_market_update.sh" || fail "listed file not copied"
[[ "$(cat "$runtime/unlisted.txt")" == "leave me alone" ]] || fail "unlisted file changed"
backup="$(find "$runtime/.deploy_rollback" -type f -path '*/daily_market_update.sh' -print -quit)"
[[ -n "$backup" && "$(cat "$backup")" == "old runtime content" ]] || fail "rollback backup missing or incorrect"
for path in $(cat "$ROOT/deploy/source_manifest.txt"); do
  [[ -f "$runtime/$path" ]] || fail "manifest file missing from target: $path"
done
grep -q 'SKIP: daily betting email regression' "$output" || fail "isolated fixture SKIP not reported"
printf 'PASS: manifest-only copy, unlisted preservation, backup, and explicit fixture SKIP\n'

fixture_runtime="$TMP/fixture-runtime"
mkdir -p "$fixture_runtime/data/agents"
cat > "$fixture_runtime/data/agents/daily_betting_angles.csv" <<'CSV'
category,description
Game line edge,Example edge
CSV
cat > "$fixture_runtime/data/agents/daily_betting_angles.html" <<'HTML'
<html><body><h2>Game Line Moves</h2><h2>Game Line Edges</h2></body></html>
HTML
bash "$DEPLOY" --target "$fixture_runtime" --allow-dirty >"$TMP/fixture-deploy.out"
grep -q 'Email regression: PASSED' "$TMP/fixture-deploy.out" || fail "email regression did not run with fixtures present"
printf 'PASS: daily betting email regression runs when fixtures exist\n'

bad_fixture_runtime="$TMP/bad-fixture-runtime"
mkdir -p "$bad_fixture_runtime/data/agents"
printf 'category,description\nOther,No required edge\n' > "$bad_fixture_runtime/data/agents/daily_betting_angles.csv"
printf '<html><body>Incomplete</body></html>\n' > "$bad_fixture_runtime/data/agents/daily_betting_angles.html"
expect_fail post-copy-validation bash "$DEPLOY" --target "$bad_fixture_runtime" --allow-dirty
grep -q 'DEPLOYMENT FAILED after runtime copying began' "$TMP/post-copy-validation.out" || fail "post-copy failure summary missing"
grep -q 'Rollback: copy files from' "$TMP/post-copy-validation.out" || fail "post-copy rollback instructions missing"
printf 'PASS: post-copy validation failure reports rollback instructions\n'

printf '../escape\n' > "$TMP/traversal.txt"
expect_fail traversal bash "$DEPLOY" --target "$TMP/traversal-runtime" --manifest "$TMP/traversal.txt" --allow-dirty

printf 'does/not/exist.py\n' > "$TMP/missing.txt"
expect_fail missing bash "$DEPLOY" --target "$TMP/missing-runtime" --manifest "$TMP/missing.txt" --allow-dirty

mkdir -p "$TMP/escape-destination" "$TMP/symlink-runtime"
ln -s "$TMP/escape-destination" "$TMP/symlink-runtime/scripts"
printf 'scripts/markets/pull_sgo_ncaaf_game_odds.py\n' > "$TMP/symlink-target.txt"
expect_fail symlink-target bash "$DEPLOY" --target "$TMP/symlink-runtime" --manifest "$TMP/symlink-target.txt" --allow-dirty
[[ ! -e "$TMP/escape-destination/markets/pull_sgo_ncaaf_game_odds.py" ]] || fail "symlinked target escaped runtime root"

bad_shell_rel="tests/.deploy_bad_syntax.sh"
bad_python_rel="tests/.deploy_bad_syntax.py"
printf 'if then\n' > "$BAD_SHELL"
printf 'def broken(:\n' > "$BAD_PYTHON"
printf '%s\n' "$bad_shell_rel" > "$TMP/bad-shell.txt"
printf '%s\n' "$bad_python_rel" > "$TMP/bad-python.txt"
expect_fail shell-syntax bash "$DEPLOY" --target "$TMP/bad-shell-runtime" --manifest "$TMP/bad-shell.txt" --allow-dirty
expect_fail python-syntax bash "$DEPLOY" --target "$TMP/bad-python-runtime" --manifest "$TMP/bad-python.txt" --allow-dirty
[[ ! -e "$TMP/bad-shell-runtime/$bad_shell_rel" ]] || fail "bad shell was copied before validation"
[[ ! -e "$TMP/bad-python-runtime/$bad_python_rel" ]] || fail "bad Python was copied before validation"
rm -f -- "$ROOT/$bad_shell_rel" "$ROOT/$bad_python_rel"

if rg -n -- '--delete|rsync' "$DEPLOY"; then
  fail "deployment script contains prohibited sync/delete behavior"
fi
printf 'PASS: no rsync or --delete behavior\n'

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "$DEPLOY" "$ROOT/tests/test_deploy_to_auto.sh"
  printf 'PASS: shellcheck\n'
else
  printf 'SKIP: shellcheck is not installed\n'
fi

printf 'ALL DEPLOYMENT TESTS PASSED\n'
