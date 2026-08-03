#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
DEPLOY="$ROOT/deploy/deploy_to_auto.sh"
STATUS="$ROOT/deploy/deploy_status.py"
BOOTSTRAP="$ROOT/data/audit/canonical_runtime_bootstrap_manifest.csv"
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

cat > "$TMP/expected-manifest.txt" <<'EOF'
daily_market_update.sh
CURRENT_PRIORITIES.md
scripts/markets/pull_sgo_ncaaf_game_odds.py
scripts/markets/build_sgo_canonical_artifacts.py
scripts/markets/build_sgo_daily_canonical.py
scripts/control/sgo_preview_adapter.py
scripts/audit/test_daily_betting_email_regression.py
scripts/injuries/build_injury_alerts.py
config/page_health_registry.json
scripts/site/build_page_health_status.py
scripts/site/build_public_site.py
scripts/publish/publish_site.sh
scripts/publish/check_public_site.py
page_health.js
page_health.css
config/daily_stages.json
scripts/control/daily_run_status.py
agents/append_daily_game_line_edges.py
agents/build_daily_betting_angles.py
agents/prepend_game_line_moves_to_daily_betting_angles.py
agents/prepend_injury_alerts_to_daily_betting_angles.py
email/send_daily_betting_angles_email.py
injuries/build_game_injury_scores.py
injuries/pull_cfbdepth_article_bodies.py
injuries/pull_cfbdepth_injuries.py
odds/build_actionnetwork_season_lines_2026.py
odds/build_game_line_movement_report.py
odds/merge_visible_dk_win_totals.py
odds/pull_actionnetwork_ncaaf_game_lines_2026.py
odds/pull_actionnetwork_visible_dk_win_totals.py
odds/quarantine_bad_draftkings_win_total_rows.py
pulls/pull_actionnetwork_conference_futures_api.py
ratings/append_ratings_history.py
ratings/build_ratings_movement.py
ratings/parse_massey_visible_ratings.py
ratings/pull_donchess_ratings.py
ratings/pull_sagarin_ratings.py
scripts/projections/build_game_projection_blend_2026.py
scripts/projections/build_game_projection_sources_2026.py
betting_v2.html
scripts/model_tracking/__init__.py
scripts/model_tracking/model_tracking.py
scripts/model_tracking/capture_model_tracking.py
scripts/model_tracking/settle_model_tracking.py
scripts/model_tracking/build_model_performance_view.py
scripts/control/run_data_refresh.py
data/model_tracking/config.json
data/model_tracking/schema.json
tests/test_model_tracking_phase1.py
tests/test_betting_model_performance_integration.py
EOF
cmp -s "$TMP/expected-manifest.txt" "$ROOT/deploy/source_manifest.txt" \
  || fail "source manifest differs from the approved runtime files"
printf 'PASS: manifest is exactly the approved runtime files\n'
python3 - "$ROOT" "$BOOTSTRAP" "$ROOT/deploy/source_manifest.txt" "$ROOT/config/daily_stages.json" <<'PY'
import csv
import json
import pathlib
import subprocess
import sys

root, bootstrap_path, manifest_path, registry_path = map(pathlib.Path, sys.argv[1:])
rows = list(csv.DictReader(bootstrap_path.open(encoding="utf-8")))
assert len(rows) == 22
bootstrap = [row["canonical_path"] for row in rows]
assert len(set(bootstrap)) == 22
manifest = manifest_path.read_text(encoding="utf-8").splitlines()
assert set(bootstrap).issubset(manifest)
registry = json.loads(registry_path.read_text(encoding="utf-8"))
registered = {path for stage in registry["stages"] for path in stage["scripts"]}
assert set(bootstrap).issubset(registered)
for row in rows:
    path = row["canonical_path"]
    source = root / path
    assert source.is_file() and not source.is_symlink()
    assert row["byte_identical"] == "True"
    assert row["source_repository_sha256"] == row["equivalent_runtime_sha256"]
    assert not any(char in path for char in "*?[]")
    assert not path.endswith("/")
    assert source.suffix in {".py", ".sh"}
    subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", path], check=True, capture_output=True)
for path in manifest:
    assert path and not any(char in path for char in "*?[]") and not path.endswith("/")
print("PASS: exact 22-file canonical bootstrap is registered, tracked, regular, and manifest-approved")
PY
make_recorded_runtime() {
  local target="$1" commit="$2"
  mkdir -p "$target/data/control"
  while IFS= read -r path; do
    mkdir -p "$target/$(dirname -- "$path")"
    git -C "$ROOT" show "$commit:$path" > "$target/$path"
  done < "$ROOT/deploy/source_manifest.txt"
  python3 - "$target" "$ROOT" "$commit" "$ROOT/deploy/source_manifest.txt" <<'PY'
import json
import pathlib
import sys

target, root, commit, manifest_path = sys.argv[1:]
files = pathlib.Path(manifest_path).read_text(encoding="utf-8").splitlines()
record = {
    "source_repository": root,
    "source_commit": commit,
    "source_branch": "main",
    "deployed_at_utc": "2026-08-01T00:00:00Z",
    "target_runtime": target,
    "deployed_files": files,
    "backup_location": f"{target}/.deploy_rollback/test",
    "shell_validation_status": "PASSED",
    "python_validation_status": "PASSED",
    "email_regression_status": "SKIPPED (test fixture)",
    "overall_status": "PASSED",
}
path = pathlib.Path(target) / "data/control/deployed_source_version.json"
path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
PY
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
record="$runtime/data/control/deployed_source_version.json"
[[ -f "$record" ]] || fail "successful deployment did not create version record"
python3 - "$record" "$ROOT" "$(git -C "$ROOT" rev-parse HEAD)" "$ROOT/deploy/source_manifest.txt" <<'PY'
import json
import pathlib
import sys

record_path, root, expected_commit, manifest_path = sys.argv[1:]
record = json.loads(pathlib.Path(record_path).read_text(encoding="utf-8"))
expected_files = pathlib.Path(manifest_path).read_text(encoding="utf-8").splitlines()
assert record["source_repository"] == root
assert record["source_commit"] == expected_commit
assert record["deployed_files"] == expected_files
assert record["shell_validation_status"] == "PASSED"
assert record["python_validation_status"] == "PASSED"
assert record["overall_status"] == "PASSED"
PY
current_runtime="$TMP/current-runtime"
make_recorded_runtime "$current_runtime" "$(git -C "$ROOT" rev-parse HEAD)"
python3 "$STATUS" --target "$current_runtime" >"$TMP/current-status.out"
grep -q '^Deployment state: CURRENT$' "$TMP/current-status.out" || fail "matching deployment did not report CURRENT"
before_status_hashes="$TMP/status-before.sha"
after_status_hashes="$TMP/status-after.sha"
find "$current_runtime" -type f -exec shasum {} \; | sort >"$before_status_hashes"
python3 "$STATUS" --target "$current_runtime" >"$TMP/repeated-status.out"
find "$current_runtime" -type f -exec shasum {} \; | sort >"$after_status_hashes"
cmp -s "$before_status_hashes" "$after_status_hashes" || fail "status mode modified runtime files"
printf 'PASS: manifest-only copy, deployment record, CURRENT status, read-only status, backup, and explicit fixture SKIP\n'

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
mkdir -p "$bad_fixture_runtime/data/agents" "$bad_fixture_runtime/data/control"
printf 'category,description\nOther,No required edge\n' > "$bad_fixture_runtime/data/agents/daily_betting_angles.csv"
printf '<html><body>Incomplete</body></html>\n' > "$bad_fixture_runtime/data/agents/daily_betting_angles.html"
printf '{"overall_status":"PREVIOUS"}\n' > "$bad_fixture_runtime/data/control/deployed_source_version.json"
prior_record_hash="$(shasum "$bad_fixture_runtime/data/control/deployed_source_version.json")"
expect_fail post-copy-validation bash "$DEPLOY" --target "$bad_fixture_runtime" --allow-dirty
grep -q 'DEPLOYMENT FAILED after runtime copying began' "$TMP/post-copy-validation.out" || fail "post-copy failure summary missing"
grep -q 'Rollback: copy files from' "$TMP/post-copy-validation.out" || fail "post-copy rollback instructions missing"
[[ "$(shasum "$bad_fixture_runtime/data/control/deployed_source_version.json")" == "$prior_record_hash" ]] \
  || fail "failed validation replaced the prior deployment record"
printf 'PASS: post-copy validation failure reports rollback instructions\n'

behind_source="$TMP/behind-source"
behind_runtime="$TMP/behind-runtime"
mkdir -p "$behind_source/deploy" "$behind_runtime/data/control"
cp "$STATUS" "$behind_source/deploy/deploy_status.py"
printf 'app.py\n' > "$behind_source/deploy/source_manifest.txt"
printf 'print("stable")\n' > "$behind_source/app.py"
git -C "$behind_source" init -q
git -C "$behind_source" config user.name "Deployment Test"
git -C "$behind_source" config user.email "deployment-test@example.invalid"
git -C "$behind_source" remote add origin https://github.com/barnsey1210/2026_NCAA_Football.git
git -C "$behind_source" add .
git -C "$behind_source" commit -qm "runtime version"
behind_commit="$(git -C "$behind_source" rev-parse HEAD)"
mkdir -p "$behind_runtime"
cp "$behind_source/app.py" "$behind_runtime/app.py"
python3 - "$behind_runtime" "$behind_source" "$behind_commit" <<'PY'
import json
import pathlib
import sys

target, source, commit = sys.argv[1:]
target = str(pathlib.Path(target).resolve())
source = str(pathlib.Path(source).resolve())
record = {
    "source_repository": source,
    "source_commit": commit,
    "source_branch": "main",
    "deployed_at_utc": "2026-08-01T00:00:00Z",
    "target_runtime": target,
    "deployed_files": ["app.py"],
    "backup_location": f"{target}/.deploy_rollback/test",
    "shell_validation_status": "PASSED",
    "python_validation_status": "PASSED",
    "email_regression_status": "SKIPPED (test fixture)",
    "overall_status": "PASSED",
}
path = pathlib.Path(target) / "data/control/deployed_source_version.json"
path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
PY
printf 'newer docs\n' > "$behind_source/README.md"
git -C "$behind_source" add README.md
git -C "$behind_source" commit -qm "newer source commit"
python3 "$behind_source/deploy/deploy_status.py" --target "$behind_runtime" >"$TMP/behind-status.out"
grep -q '^Deployment state: BEHIND$' "$TMP/behind-status.out" || fail "older recorded deployment did not report BEHIND"
grep -q '^Main repository has newer commits: YES$' "$TMP/behind-status.out" || fail "BEHIND status did not report newer commits"
printf 'PASS: status reports BEHIND for an older intact deployed commit\n'

printf '../escape\n' > "$TMP/traversal.txt"
expect_fail traversal bash "$DEPLOY" --target "$TMP/traversal-runtime" --manifest "$TMP/traversal.txt" --allow-dirty

printf '/absolute/path\n' > "$TMP/absolute.txt"
expect_fail absolute bash "$DEPLOY" --target "$TMP/absolute-runtime" --manifest "$TMP/absolute.txt" --allow-dirty

printf '\n' > "$TMP/empty.txt"
expect_fail empty bash "$DEPLOY" --target "$TMP/empty-runtime" --manifest "$TMP/empty.txt" --allow-dirty

printf 'scripts/markets/\n' > "$TMP/directory.txt"
expect_fail directory bash "$DEPLOY" --target "$TMP/directory-runtime" --manifest "$TMP/directory.txt" --allow-dirty

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

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/ncaaf-deploy-pycache" python3 -m py_compile "$STATUS"
printf 'PASS: deployment status Python syntax\n'

printf 'ALL DEPLOYMENT TESTS PASSED\n'
