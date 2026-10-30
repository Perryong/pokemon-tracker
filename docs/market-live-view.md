# Mac-hosted Market view

The **Market** navigation item reads real TCGdex reference prices through this Mac's backend. Search by a name or partial word such as **Pikachu** or **pika**, or enter a TCGdex ID directly. Results load in batches of 12 with at most three simultaneous price lookups. **Load more cards** adds the next batch. Sorting by SGD price covers loaded cards only; this is not a popularity ranking. Click a card to open its full prices and average charts. Refresh is manual. All displayed amounts are estimated SGD; the API preserves the original EUR/USD amounts and provider update time separately from backend fetch time.

These are reference prices, not completed-sale evidence or an autonomous buy decision. The Python Market Agent remains simulated. Browser collections still belong to each browser/origin; opening the private URL on a phone does not copy the Mac's collection.

## SGD and charts

Market and Card Detail convert both Cardmarket EUR and TCGplayer USD with dated ECB reference rates via Frankfurter. Rates are validated, cached for up to six hours and rejected if future-dated or older than seven days. Open views renew rates at expiry; failed renewal removes converted amounts and retries after six hours (reopening the view retries sooner). Price lookups remain manual. The source and date remain visible. If conversion fails, price amounts are unavailable; original foreign values are never relabelled SGD. Refresh the view to retry. The rates are estimates, not executable FX quotes.

Charts compare available **30-day, 7-day and 1-day averages**, with separate holo references when supplied. These are overlapping averaging windows, not a daily price history. Missing windows are omitted; zero values are preserved. TCGplayer-only quotes do not supply these windows. Chart values and table values use the same conversion rate.

Search uses case-insensitive substring matching, 2–60 characters, with at most 500 results per query. Exact names rank first, then prefixes and other matches; equal names retain the provider's order. Narrow the query if it reaches the cap. A tile shows a Cardmarket trend/average reference or an available TCGplayer market reference; this does not establish an exact condition/printing match. Missing/unconverted references sort last. Rate-limit errors stay visible and card selection permits a later retry.

## Start and stop

From the repository, with its existing dependencies installed:

```sh
npm run build
npm run preview -- --host 127.0.0.1 --port 5184 --strictPort
```

Open `http://127.0.0.1:5184/` on the Mac, then **Market**. Keep this process running. Stop it with Ctrl-C in that terminal. Port conflicts fail explicitly; choose an unused port and update the Serve target together. Rebuild and restart after code changes. Vite preview is a personal verification service, not production hosting.

The new endpoint needs no API key. The separately configured keyed Card Detail provider is unchanged; it is not used by Market. Never expose the Vite development server, project directory or credentials through Serve.

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

No public Funnel, router forwarding, daemon, power-setting changes or automatic restart is configured. The Mac must stay awake, online, connected to Tailscale and running the preview process. Tailnet policy controls access; the view has no additional application login.

## Status and limits

- **Backend reachable** confirms the Mac API, not upstream availability. Provider failures appear separately. Static-only hosts report backend unavailable; no sample values or viewer-localhost fallback is supplied.
- Missing card, empty prices, provider errors, rate limits and connection failures have distinct messages. Retained values after a failed/new lookup are marked **Previous result**.
- Provider timestamps older than 48 hours are stale. Missing, malformed or future timestamps have unknown freshness. Freshness is recalculated on each backend request; a screen left open is a snapshot until refreshed.
- Cache: 1 hour, 256 cached cards/searches, shared duplicate requests. Maximum 30 uncached card/search upstream calls per minute per process; cached reads remain available. Restarting the process resets these limits.
- Upstream timeout: 8 seconds; frontend deadline: 12 seconds; response body limit: 1 MiB. Fixed TCGdex HTTPS origin, no redirects, strict IDs, read-only methods, no browser cache/CORS expansion.
- Metrics retain provider field names. Aggregate Cardmarket references do not establish an exact printing/condition match. Invalid price amounts are omitted; no conversion or qualification is inferred.

## Verification

See [discovery/SGD/chart verification](market-discovery-verification.md) and [original live-view evidence](market-live-view-verification.md), including the outstanding private-access step. Implementation belongs to [issue #26](https://github.com/Perryong/pokemon-tracker/issues/26); local code is on `codex/market-live-view`, under the operator's explicit local-work exception. No accepted workflow claim, new PR publication or merge is asserted.
