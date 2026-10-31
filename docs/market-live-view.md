# Market view with hosted pricing

The **Market** navigation item reads real TCGdex reference prices through the public [pokemon-price-api](https://pokemon-price-api-omega.vercel.app) on Vercel. Search by a name or partial word such as **Pikachu** or **pika**, or enter a TCGdex ID directly. Results load in batches of 12 with at most three simultaneous price lookups. **Load more cards** adds the next batch. Sorting by SGD price covers loaded cards only; this is not a popularity ranking. Click a card to open its full prices and average charts. Refresh is manual. All displayed amounts are estimated SGD; the API preserves the original EUR/USD amounts and provider update time separately from backend fetch time.

These are reference prices, not completed-sale evidence or an autonomous buy decision. The Python Market Agent remains simulated. Browser collections still belong to each browser/origin; opening the private URL on a phone does not copy the Mac's collection.

## SGD and charts

Market and Card Detail convert both Cardmarket EUR and TCGplayer USD with dated ECB reference rates via Frankfurter, retrieved from the hosted `/api/market/rates` endpoint. One in-flight rates request is shared across currencies and views. Native v1 quotes are converted exactly once in the frontend; this client does not request the API’s already-converted v2 quotes. Rates are validated, cached until the server expiry (at most six hours) and rejected if expired, future-dated or seven days old. Open views renew rates at expiry; failed renewal removes converted amounts and retries after six hours (reopening the view retries sooner). Price lookups remain manual. The source and date remain visible. If conversion fails, price amounts are unavailable; original foreign values are never relabelled SGD. Refresh the view to retry. The rates are estimates, not executable FX quotes.

Charts compare available **30-day, 7-day and 1-day averages**, with separate holo references when supplied. These are overlapping averaging windows, not a daily price history. Missing windows are omitted; zero values are preserved. TCGplayer-only quotes do not supply these windows. Chart values and table values use the same conversion rate.

Search uses case-insensitive substring matching, 2–60 characters, with at most 500 results per query. Exact names rank first, then prefixes and other matches; equal names retain the provider's order. Narrow the query if it reaches the cap. A tile shows a Cardmarket trend/average reference or an available TCGplayer market reference; this does not establish an exact condition/printing match. Missing/unconverted references sort last. Rate-limit errors stay visible and card selection permits a later retry.

## Hosted API and local preview

From the repository, with its existing dependencies installed:

```sh
npm run build
npm run preview -- --host 127.0.0.1 --port 5184 --strictPort
```

Open `http://127.0.0.1:5184/` on the Mac, then **Market**. Keep this process running. Stop it with Ctrl-C in that terminal. Port conflicts fail explicitly; choose an unused port and update the Serve target together. Rebuild and restart after code changes. Vite preview is a personal verification service, not production hosting.

The Market API needs no API key. Its origin is defined in `src/lib/market.ts`; health, search, card prices and rates all use that origin in development and production. No Vite proxy or Vercel rewrite is needed because the API allows public cross-origin GET requests. Static builds work without the legacy `server/market.ts` middleware. The separately configured keyed Card Detail provider is unchanged; it is not used by Market. Never expose the Vite development server, project directory or credentials through Serve.

## Private phone access

1. Connect Tailscale on the Mac and phone to the same permitted tailnet. `tailscale up` with no flags preserves existing preferences; do not use `--reset` to resolve configuration errors.
2. Inspect `tailscale serve status` before changing routes. Preserve any other service. Enable Serve/HTTPS through the sign-in link printed by the CLI if required.
3. With this built preview running and no conflicting Serve route:

   ```sh
   tailscale serve --bg http://127.0.0.1:5184
   tailscale serve status
   ```

4. Open the private HTTPS URL printed by Serve on the connected phone and select **Market**. A successful local request does not prove the phone is enrolled or authorized.
5. To remove just this default HTTPS listener, first confirm it still belongs to this app, then use `tailscale serve --https=443 off`. Do not reset all Serve configuration or disable Tailscale if other work uses it.

No public Funnel, router forwarding, daemon, power-setting changes or automatic restart is configured. For this private frontend URL, the Mac must stay awake, online, connected to Tailscale and running the preview process. The Vercel price API continues operating independently when the Mac is off. Deploy the frontend to static hosting for an app URL that also remains available. Tailnet policy controls access; the view has no additional application login.

## Status and limits

- **Backend reachable** confirms the hosted API, not upstream availability. Provider failures appear separately. Static-only frontend hosts use the same hosted API; no sample values or viewer-localhost fallback is supplied.
- Missing card, empty prices, provider errors, rate limits and connection failures have distinct messages. Retained values after a failed/new lookup are marked **Previous result**.
- Provider timestamps older than 48 hours are stale. Missing, malformed or future timestamps have unknown freshness. Freshness is recalculated on each backend request; a screen left open is a snapshot until refreshed.
- Hosted API cache: up to 1 hour for cards/searches with bounded per-instance storage and shared duplicate requests; CDN caching is bounded by data expiry. The old Mac middleware’s 30-request-per-minute cap is not on this request path. Real upstream rate limits still apply and are respected by the existing retry UI.
- Upstream timeout: 8 seconds; frontend deadline: 12 seconds; response body limit: 1 MiB. Fixed TCGdex HTTPS origin, no redirects, strict IDs, read-only methods, public read-only CORS on the hosted API.
- Metrics retain provider field names. Aggregate Cardmarket references do not establish an exact printing/condition match. Invalid price amounts are omitted; no conversion or qualification is inferred.

## Verification

The hosted connection is tracked in [issue #43](https://github.com/Perryong/pokemon-tracker/issues/43), branch `codex/connect-price-api`, under the operator’s explicit 2026-10-31 exception allowing implementation, testing and a draft PR while Project/claim access is unavailable. No accepted claim, merge or production frontend deployment is asserted.

Verified on 2026-10-31:

- Baseline: 190 tests passed. Updated suite: 194 tests passed across 22 files; production build passed.
- Test-first check: the hosted-route/FX tests failed against the old implementation, then passed after connection. Tests cover request sharing, expiry bounds, malformed/missing rates, failure recovery, cancellation, retry limits and SGD conversion.
- Full ESLint output is identical to baseline: 9 errors and 5 warnings in existing UI primitives, `use-toast`, migration and its tests. No new lint findings.
- Served `dist/` with Python's static HTTP server, without Vite middleware. Local `/api/market/health` returned 404 while hosted health, rates and card lookup returned 200 and the UI showed prices/charts.
- Live Charizard search loaded 12 cards; 11 had priced references, one had no reference price. SGD descending sorting and selection worked. Browser resource entries showed all 17 Market API requests going to Vercel.
- Cross-checked Charizard `ecard1-6`: native EUR trend 554.68 × dated EUR/SGD rate 1.4282 = displayed SGD 792.19. This verifies one conversion. Prices are a snapshot, not fixed expected future values.
- A 390 × 844 browser viewport had no horizontal overflow. This is mobile browser emulation, not a physical phone test.
- Independent code review found no substantive issues in this integration diff.

Historical Mac-backend evidence remains in [discovery/SGD/chart verification](market-discovery-verification.md) and [original live-view evidence](market-live-view-verification.md), associated with [issue #26](https://github.com/Perryong/pokemon-tracker/issues/26). Those reports describe the earlier local-backend implementation.

The branch inherits unmerged Market work from commit `5720d20`, also represented in PR #42. Reconcile that baseline before merging either PR; the new integration is a separate commit. The hosted API remains an external dependency. The optional authenticated Card Detail provider and production frontend deployment were not changed or verified by this task.
