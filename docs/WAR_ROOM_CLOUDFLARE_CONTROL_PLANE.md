# War Room Cloudflare Control Plane

## Locked request path

```text
public GitHub Pages Command Center
  -> Cloudflare Access-protected HTTPS hostname
  -> Cloudflare Tunnel
  -> 127.0.0.1:8787 in NCAAF_AUTO
  -> allowlisted War Room service dispatcher
  -> existing domain owners, validators and publisher
```

No Worker is required for the minimum implementation. Access owns operator
authentication, Tunnel owns private transport, and the loopback FastAPI origin
owns fixed action dispatch. Provider credentials remain exclusively in AUTO's
protected process environment.

The origin accepts only Market, Ratings and Postgame actions. It accepts no
command text, script path, provider choice, formula, publication override, or
credential from the browser.

## Activation boundary

`config/war_room_control_plane.json` deliberately leaves `control_base_url`
null until the operator selects a Cloudflare-managed hostname and protects it
with an Access application/policy. Public controls remain unavailable until a
reviewed HTTPS hostname is configured and deployed.

The Access application must:

- cover `/war-room/*` on the selected hostname;
- allow only the approved operator identity;
- deny unauthenticated requests;
- retain the Access JWT and authenticated-email headers to the origin; and
- permit the public GitHub Pages origin through the origin's exact CORS policy.

The three already-public live-data routes are a narrow exception to operator
authentication. Configure a more-specific Access application for
`control.barnseywr.com/war-room/live/*` with a Bypass policy. Cloudflare's
most-specific application-path rule takes precedence. The FastAPI origin still
accepts browser reads only from the exact GitHub Pages origin and exposes no
operator identity, task control, credentials, or filesystem parameter. All
other `/war-room/*` routes remain under the approved-operator Access policy.

The tunnel ingress must use the final catch-all `http_status:404` rule from
`deploy/cloudflare/war-room-tunnel.example.yml`. The origin remains bound to
`127.0.0.1:8787`; no router port-forward is permitted.
