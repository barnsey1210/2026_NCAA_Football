# Cloudflare Pages Migration Runbook

Status: Phase 1 repository preparation only. GitHub Pages remains the production public host until the preview and cutover gates below pass.

## Boundaries

- `NCAAF_MAIN_REPO` remains the authoritative source and publication repository.
- `NCAAF_AUTO` remains the operational runtime.
- `control.barnseywr.com`, its Cloudflare Tunnel, Cloudflare Access policy, loopback FastAPI service, fixed action routes, and provider credentials are unchanged.
- The site remains a multipage static site. Do not configure an SPA fallback.
- Do not attach either custom domain until the `pages.dev` preview passes.

## Local build and validation

From the repository root, run:

```bash
python3 scripts/publish/build_cloudflare_pages_bundle.py
python3 scripts/publish/check_cloudflare_pages_bundle.py
find build/cloudflare_pages -type l -print
```

The last command must print nothing. The bundle is materialized at `build/cloudflare_pages`; it contains only manifest-allowlisted files and never preserves repository symlinks.

## Cloudflare Pages project settings

- Production branch: `main`
- Build command: `python3 scripts/publish/build_cloudflare_pages_bundle.py && python3 scripts/publish/check_cloudflare_pages_bundle.py`
- Build output directory: `build/cloudflare_pages`
- Root directory: repository root
- Framework preset: None
- Runtime secrets: none for the static build
- Required Python: Python 3 standard library only. Runtime/publication pipelines remain responsible for updating the canonical root artifacts before they are committed.

Do not add `wrangler.toml` for this static Pages deployment. The committed `_headers` file is copied into the bundle. No `_redirects` or SPA fallback is used.

## Preview acceptance

1. Create the Pages project without a custom domain and allow it to produce its exact stable `https://<project>.pages.dev` origin.
2. Add that exact origin to the protected operator environment as `WAR_ROOM_PAGES_ORIGIN`. Never use `*.pages.dev`.
3. Redeploy/restart the operator only through the established MAIN-to-AUTO procedure after the exact-origin configuration is reviewed.
4. Validate every root page, JS/CSS asset, logo, and required JSON contract on the preview hostname.
5. Confirm the preview has no mixed-content, missing-asset, CORS, or console errors on desktop and mobile.
6. Compare hashes/content of the GitHub Pages build candidate and Cloudflare Pages bundle for every shared canonical root artifact.

## War Room live-read and operator acceptance

Using the exact preview origin:

1. Confirm browser GETs to `/war-room/live/version`, `/war-room/live/health`, `/war-room/live/market-matrix`, `/war-room/live/activity`, and `/war-room/live/schedule` succeed through `control.barnseywr.com` with exact-origin CORS.
2. Confirm a foreign origin, a suffix attack, and an arbitrary `pages.dev` origin are rejected.
3. Confirm Connect opens the existing protected bootstrap and completes the nonce-bound `postMessage` handshake.
4. Let the Access session expire and confirm the public page returns to reconnect-required behavior.
5. In a separately approved bounded acceptance test, confirm an operator action POST originates from `https://control.barnseywr.com`, is Access-authenticated, and reaches only an allowlisted fixed route.
6. Confirm no credential or Access token is present in public JavaScript.

## Apex cutover

1. Keep GitHub Pages live while the preview tests run.
2. Attach `barnseywr.com` to Cloudflare Pages only after all preview and operator gates pass.
3. Validate the apex site again before changing user-facing links or documentation.
4. Configure a Cloudflare zone redirect from `https://www.barnseywr.com/*` to `https://barnseywr.com/$1`. Do not add `www` to the operator CORS allowlist merely for the redirect.
5. Leave `control.barnseywr.com` DNS, Tunnel, Access application, and origin service untouched.
6. After the apex is stable, update the current-production architecture/handoff documentation in a separate post-cutover change.

## Rollback

1. Remove or disable only the apex Pages custom-domain attachment/redirect change.
2. Restore the prior public DNS/GitHub Pages custom-domain arrangement if it was changed.
3. Keep the GitHub Pages deployment and repository publication path intact throughout the migration so it remains the immediate fallback.
4. Leave `control.barnseywr.com` unchanged; remove only the no-longer-needed exact `pages.dev` origin from the operator environment after rollback.
