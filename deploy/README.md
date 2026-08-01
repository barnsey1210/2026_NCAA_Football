# Manifest-based runtime deployment

`NCAAF_MAIN_REPO` is the authoritative Git source. `NCAAF_AUTO` is an operational runtime workspace and is intentionally not a Git checkout. Runtime-affecting source work is not operationally complete until it is reviewed, merged, and manually deployed.

Documentation-only changes usually do not require runtime deployment. Add a documentation file to the manifest only when the runtime genuinely consumes it.

## Standard workflow

1. Make and test source changes in `/Users/jameslindesmith/NCAAF_MAIN_REPO`.
2. Commit and review them.
3. Add only approved runtime files to `deploy/source_manifest.txt`.
4. Merge the approved changes into `main`.
5. From a clean authoritative checkout, run one manual command:

   ```bash
   cd /Users/jameslindesmith/NCAAF_MAIN_REPO
   bash deploy/deploy_to_auto.sh
   ```

6. The deployer backs up existing runtime files, copies only the manifest allowlist, and validates shell, Python, and daily-email regression behavior.
7. After every successful deployment it atomically writes `/Users/jameslindesmith/NCAAF_AUTO/data/control/deployed_source_version.json`.
8. Confirm the recorded version and runtime contents:

   ```bash
   python3 deploy/deploy_status.py
   ```

9. The normal 8 AM runtime job continues using the stable files already present in `NCAAF_AUTO`.
10. Publication remains a separate operation through the existing validated publication workflow.

Deployment is deliberately not part of `daily_market_update.sh`, the LaunchAgent, a schedule, or the publication workflow.

## Manifest boundary

`deploy/source_manifest.txt` is the authoritative deployment allowlist. The deployer rejects empty, absolute, parent-traversal, duplicate, missing, directory, symlink, and repository-escaping entries. It never broadly synchronizes `scripts/`, invokes `rsync`, or deletes target files.

The initial manifest remains restricted to the eight source files approved by stabilization commit `9318203`.

## Test targets and exceptional dirty-tree use

For an isolated test target:

```bash
bash deploy/deploy_to_auto.sh --target /absolute/path/to/test-runtime --allow-dirty
python3 deploy/deploy_status.py --target /absolute/path/to/test-runtime
```

`--allow-dirty` is intentionally explicit. It is for controlled local tests only; a real runtime deployment should originate from a clean reviewed commit.

## Deployment record and status

The success record contains the source repository, commit, branch, UTC deployment time, target, exact file list, backup location, validation outcomes, and overall result. It is written only after all validation succeeds. A failed deployment does not claim a new successful version.

The read-only status command returns:

- `CURRENT` — recorded commit equals repository HEAD and every manifest file matches that commit;
- `BEHIND` — runtime still matches its recorded commit and that commit is an ancestor of a newer repository HEAD;
- `UNKNOWN` — the record is missing/invalid, its commit cannot be checked, the manifest changed, or runtime contents differ.

Status does not modify files, deploy, call providers, send email, or publish.

## Rollback

The deployment summary prints the timestamped backup directory. Restore a backed-up file using its preserved relative path, for example:

```bash
cp -p /path/to/runtime/.deploy_rollback/TIMESTAMP-COMMIT/daily_market_update.sh \
  /path/to/runtime/daily_market_update.sh
```

Only files that existed before deployment have backup copies. Files newly introduced by a deployment must be reviewed and removed manually if rollback requires their absence. Inspect the relative file list before restoring; never copy an entire backup tree blindly.

The deployer itself never invokes the daily pipeline, provider APIs, email sending, or publication.
