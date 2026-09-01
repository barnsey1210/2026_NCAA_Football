# 2026 NCAAF Current Production Handoff

_Status synchronized: 2026-09-01_

## Production models

- Standard Spread `standard_spread_4src_equal_v1`: SP+, FPI,
  TeamRankings, and DRatings at 25% each.
- Standard Total `standard_total_sp_massey_dratings_v1`: SP+ Total 40%,
  Massey Dual 40%, and DRatings Total 20%.
- Total challenger/research `total_sp50_massey50_v1`: SP+ Total 50% and
  Massey Dual 50%; not active Standard authority.
- Legacy-only registrations: `standard_spread_5src_legacy_v1` and
  `standard_total_40_40_20_sagarin_legacy_v1`.
- Shadow Spread `shadow_spread_sp_sagarin_v1`: Shadow SP+ 50% and Shadow
  Sagarin 50%.
- Shadow Total `shadow_total_enhanced_spplus_od_v1`:
  `0.5*(home offense + away defense) + 0.5*(away offense + home defense)`
  using frozen SP+ offense/defense inputs.

Sagarin is not part of active Standard Spread, Standard Total, or their health
counts. It remains relevant to Shadow, research, diagnostics, and legacy model
identities.

## Authority and health

Spread and Total are evaluated independently from accepted provider-version
updates.

- Spread sources: SP+, FPI, TeamRankings, DRatings. Official = 4/4; Hybrid =
  2-3/4.
- Total sources: SP+ Total, Massey Dual, DRatings Total. Official = 3/3;
  Hybrid = 2/3.

Availability, freshness, selection mode, and lifecycle state remain separate
from authority. Display an available projection value and label degraded,
partial, stale, or carry-forward state rather than suppressing the value.

## Repository and deployment roles

- `NCAAF_MAIN_REPO`: authoritative source, code, config, tests, docs, and
  canonical GitHub publication repository.
- `NCAAF_AUTO`: operational runtime, mutable data, provider responses, builds,
  logs, and publication staging; never authoritative source.
- `NCAAF_CONTROL`: guarded/manual control workflows.
- `NCAAF_SITE`: legacy checkout only.

Production source moves MAIN -> AUTO through the reviewed manifest-controlled
deployment. Do not broadly synchronize trees, use `--delete`, edit AUTO source
directly, or publish unvalidated artifacts.

## Public and control topology

The public site currently runs on GitHub Pages. The planned migration is:

- `https://barnseywr.com`: primary public site on Cloudflare Pages;
- `https://www.barnseywr.com`: redirect to the apex;
- `https://control.barnseywr.com`: retained authenticated controller/API.

Test exact-origin CORS, Cloudflare Access, authentication, live-data reads, and
operator actions before DNS cutover. Manual operator actions use the protected
popup/API. An expired Cloudflare Access session in an already-open popup can
fail before FastAPI receives the POST; reconnecting the operator session fixes
the channel. This is not a Market or quota defect.

## Next three tasks

1. Fix Command Center logo/value spacing and expired-operator-session UX while
   preserving the approved matrix width/layout.
2. Move the public site to `barnseywr.com` through tested Cloudflare Pages
   migration and DNS cutover.
3. Resume historical timing audit later as a separate research workstream.

Historical SUN12 and retrospective timing anomalies remain deferred. They must
not be treated as validated production betting conclusions.
