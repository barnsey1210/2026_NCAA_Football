# Manifest-based runtime deployment

`NCAAF_MAIN_REPO` is authoritative source. `NCAAF_AUTO` is an operational
runtime workspace and is intentionally not managed as a Git checkout.

## Normal use

From a clean authoritative checkout:

```bash
cd /Users/jameslindesmith/NCAAF_MAIN_REPO
bash deploy/deploy_to_auto.sh
```

The default target is `/Users/jameslindesmith/NCAAF_AUTO`. Only regular files
listed in `deploy/source_manifest.txt` are eligible. The command prints the
deployed Git commit, validates syntax before and after copying, creates a
timestamped rollback tree under the target's `.deploy_rollback/`, and runs the
daily-email regression only when its generated CSV/HTML fixtures exist.

For an isolated test target:

```bash
bash deploy/deploy_to_auto.sh --target /absolute/path/to/test-runtime --allow-dirty
```

`--allow-dirty` is intentionally explicit. Use it only for reviewed local
testing; normal runtime deployment should come from a clean committed tree.

## Rollback

The deployment summary prints the backup directory. Restore a backed-up file
using its preserved relative path, for example:

```bash
cp -p /path/to/runtime/.deploy_rollback/TIMESTAMP-COMMIT/daily_market_update.sh \
  /path/to/runtime/daily_market_update.sh
```

Only files that existed before deployment have backup copies. Files newly
introduced by a deployment must be reviewed and removed manually if rollback
requires their absence. Never copy the entire backup directory over the
runtime without inspecting its manifest-relative contents.

The deployer never invokes the daily pipeline, providers, email sending,
publication, `rsync`, or delete synchronization.
