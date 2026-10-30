# Mac-hosted live market view

Date: 30 October 2026 (Asia/Singapore)
Status: proposed for operator approval; no implementation claim or new exception established. Independent builder check: nothing important left.
Issue: https://github.com/Perryong/pokemon-tracker/issues/26
Branch: `codex/market-live-view`, based on the completed simulated Market slice at `f940a64`.

## Intent and evidence

Let the operator see current provider card-price data in a mobile-friendly Market view served by their MacBook. The browser should call the Mac backend, which fetches and validates upstream prices. This is the next data/display step toward the Market Agent, not a claim that live negotiation, inventory or autonomous valuation exists.

The existing keyed provider rejected the live checks. TCGdex, already used by the tracker, returned HTTP 200 for `base1-1` and `sv03-199`, including provider timestamps dated 29 October. The current card detail view rendered these fallback prices and its existing estimated SGD conversion. Today that fallback is fetched directly by the browser. The new Market view routes its requests through the local backend instead.

The operator requested use of their MacBook backend and authorized checking the existing provider before considering another. The working TCGdex feed removes the need for another subscription or price collector. Tailscale is installed but stopped and has no Serve configuration; phone access has not been demonstrated.

## Approach

Recommended builder choice: reuse React and the existing Vite server/preview middleware on the Mac, add a small read-only TCGdex endpoint, and serve the built dashboard and API together through private Tailscale Serve. Keep the current Python simulation package unchanged. There is no need for FastAPI, a database, a second runtime, new accounts, or another model call to display reference prices.

Alternatives considered:

- Hosted frontend plus a separately authenticated tunnel to the Mac: keeps the public URL but adds authentication, cross-origin configuration and tunnel management. Unnecessary for a personal first dashboard.
- A new Python price service: can later support the Python agent directly, but duplicates the existing HTTP hosting and normalization work for this display-only step.

The Tailscale deployment choice is a recommendation for approval, not a claim that the operator has already enabled it. No public Funnel or router port-forward is proposed.

## User-facing behavior

Add a **Market** navigation item beside Sets and My Collection. The existing collection and card views keep their behavior.

The Market view contains a labelled card-ID field (with `base1-1` as an example), Load prices/Refresh controls, card identity/name, backend connection status, provider/source, original currency, provider update time and backend fetch time. Cards are loaded on demand; there is no autonomous polling or expensive bulk scan. Layout is usable at phone widths, and status/error updates are accessible to assistive technology.

The view identifies these as **live reference prices**. Original EUR/USD values remain visible; existing currency-conversion behavior outside this view is unchanged. No invented SGD evidence, profit, stock, completed sales, inventory totals, agent runs or mandate statistics appear. The Market Agent status explains that its execution harness remains simulated and that approved policy/exact sale evidence are still needed for live qualification. A market price or low asking price never becomes permission to negotiate or buy.

Show explicit loading, invalid ID, no card, no pricing, stale/unknown freshness, provider failure and backend-unavailable states. A failed refresh must not relabel retained old prices as fresh. On a hosted/static frontend without the Mac endpoint, show backend unavailable; never silently substitute fixtures or the viewer's localhost.

## Backend contract and boundaries

- `GET /api/market/health`: returns a bounded capability response identifying the live-price backend and read-only reference mode. Reachability does not assert upstream health.
- `GET /api/market/cards/{cardId}`: validates a bounded supported card ID, fetches only the fixed HTTPS TCGdex English-card endpoint, verifies returned ID, normalizes known price fields, and returns card identity, source, currency, provider timestamps, fetch time and reference-only classification.
- No arbitrary URL, upstream path, shell command, user-supplied headers or credential input is accepted. Mutating methods are rejected. Encoded separators and malformed IDs cannot cause upstream fetches.
- Reuse the existing card normalization where it remains truthful. Do not infer precise printing/condition from aggregate pricing; label unresolved variant matching. Missing/null prices stay missing; finite nonnegative values only.
- A bounded in-process cache, shared in-flight requests, timeout and bounded upstream request rate prevent duplicate traffic and runaway requests. Implementation chooses simple explicit limits and covers them with tests. No persistent cache or scheduler is necessary.
- Provider timestamps remain distinct from fetched/cached-at time. Report age/unknown timestamps without promising real-time transaction prices. Future or malformed timestamps must not make evidence appear current.
- Only public provider card data is returned. No API keys, local paths, machine identity, internal configuration, collections, inventory or conversation data is exposed. No broad CORS headers are needed because frontend and backend share one origin.

## Local operation and phone access

Use a production frontend build with the existing preview middleware, bound only to `127.0.0.1`. The current test server is on port 5184; implementation will avoid occupied ports and will stop only its own process when replacing it.

After approval, connect the existing Tailscale installation and configure Serve for this loopback service only. Inspect any existing configuration first; do not overwrite another application's routing, change ACLs or enable Funnel. Keep published configuration and device addresses out of Git. If sign-in/HTTPS enablement or phone enrolment needs the operator, provide that exact remaining step rather than claim phone access works.

Access requires the phone to be connected to the same permitted tailnet. The Mac must be awake, online and running the service. No launch-on-login daemon, power-setting change or production hosting migration is included. Document start/stop/reconnect commands and test reachability locally; a real phone round trip needs operator confirmation.

## Scope and ownership

Implementation reaches new backend middleware, its narrow response types, the new Market component/client, App/Navbar navigation, necessary styles, Vite configuration, tests and operator documentation. It does not change the Python Market package, implement Sales issue #18, merge PR #25, change browser collection storage, subscribe to the expired provider or expose private operator actions.

Issue #24 and PR #25 provide context. This read-only price view has no Python/Sales runtime dependency. New work needs its own issue and claim or an explicit operator exception. Project read currently fails for missing `read:project`; the protected coordination environment remains absent. The earlier exception covered the simulated slice and its draft PR only, not this new dashboard/network scope.

Ruflo tools are unavailable in this session; use the repository workflow and Superpowers verification.

## Acceptance and verification

1. Browser Market requests go to the same-origin Mac endpoint; the backend returns real TCGdex reference prices with matching card ID and truthful provenance.
2. Invalid paths, unsupported methods, upstream errors, no prices, invalid price values, stale/unknown timestamps, timeout, caching and concurrent duplicate requests are covered by focused tests.
3. UI tests cover success, empty/error/disconnected states, stale responses after a selection change, navigation and keyboard labels; the existing collection regression suite still passes.
4. Build and affected checks run. Report the known pre-existing lint failures separately. Run the existing Python suite if any shared package boundary changes; otherwise preserve its previously recorded evidence.
5. Run a bounded live smoke check for two known cards and verify the rendered view at phone width. Show timestamps, currencies and reference-only status; do not assert financial accuracy from reachability.
6. Test the built frontend with the Mac API. Verify loopback binding and private Serve configuration if authorized; distinguish a successful local HTTPS request from an actual phone test.
7. Independent review and evidence precede handoff. Local execution approval does not authorize merge or production deployment; publishing any new draft PR requires approval or explicit inclusion in the exception.

## Sources

- Repository `server/cardmarket.ts`, `src/lib/types.ts`, `src/lib/api.ts`, `vite.config.ts`, and the completed Market README/verification.
- https://tcgdex.dev/faq — no-key API and documented price/variant mapping limitations.
- https://tailscale.com/docs/features/tailscale-serve — private access to a local service over the tailnet.
- https://github.com/Perryong/pokemon-tracker/issues/18 — Sales UI ownership boundary, not a dependency or claim for this view.
