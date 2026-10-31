# Live reference research by default

The operator selected “Live card prices and research first” after authorizing the switch from a fixture-focused demonstration. Use the existing TCGdex/Cardmarket/TCGplayer reference feed and dated ECB/Frankfurter SGD conversion. No new provider, account or collector is needed.

## Approach and scope

Use the existing Market view as the default read-only research surface: automatically request the current default card `base1-1` when Market opens, retain name search/card selection/manual refresh, and explain that these are real provider references with up to one hour backend caching. Keep source time and fetch time distinct. Retain the original currencies in the API and estimated SGD in the UI. Provider failure must show an error or clearly previous result, never fixture prices.

The alternatives were real card-price research (operator selected) and actual marketplace listing intake (requires a configured source, deferred). This change consumes real reference data; it does not feed reference quotes into completed-sale valuation or activate fixture schedules. Private fixture controls remain opt-in and explicitly synthetic. No production/live authority, stock mutation, seller contact, model calls or real Sales integration is added.

## Implementation and acceptance

Reuse MarketView's bounded lookup/abort/generation handling for both initial load and subsequent user actions. Initial work must cancel on unmount or a changed card, and a late response cannot replace a newer selection. Health and provider errors remain independently truthful. Keep the current default card rather than inventing a watchlist. Add no dependency or backend service.

Tests demonstrate initial provider-backed display without submitting the lookup form, no private API calls until the panel is opened, manual-refresh failure retaining only marked previous data, missing/malformed data without fallback, cancellation and stale selection behavior. Run the full frontend suite/build/focused lint and real-provider Playwright checks at desktop and phone width. Update #34/#40 and PR #42; no merge.
