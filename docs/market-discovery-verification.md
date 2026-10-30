# SGD, charts and discovery verification — 30 October 2026

Scope: operator-requested continuation of issue #26 on `codex/market-live-view`, base `bb034ce`. The operator explicitly selected existing-data SGD prices, average-price charts and relevant matches with price sorting. Local execution exception continues; no signed claim, publication or merge is asserted. Project `read:project` remains unavailable. Both repositories were searched for overlap; no private details are reproduced here. Ruflo was unavailable.

## Verified

- 171 frontend tests across22 files passed with `NODE_OPTIONS=--no-experimental-webstorage npx vitest run`. New FX/chart tests first failed, then passed; search/UI tests first failed, then passed. The provider-order regression was also observed RED→GREEN.
- EUR and USD use independent validated SGD rates; invalid, future, older-than-seven-days, nonfinite and unsupported currency cases are covered. Missing conversion never displays native amounts as SGD; zero is retained. Card Detail and Market use the shared conversion.
- Charts show actual available 30/7/1-day averages and distinguish holo. Missing/nonfinite windows are omitted, zero remains, and TCGplayer-only market prices cannot create a fictitious average chart.
- Search validates fixed upstream/query/image boundaries, malformed responses, result caps, shared rate limits/cache, partial matching and multi-part set IDs. UI covers 12-result batches, three-request concurrency, price sort, empty/error responses, stale searches, exact selection and keyboard focus. The previously deferred initial-health cancellation issue is resolved and covered.
- `npm run build` passed. Changed-file ESLint passed with no findings; full lint retains nine pre-existing errors and five warnings. Whitespace check passed. No new dependencies.
- Real Mac backend search `pika` returned243 matching cards, not truncated. The first12 were priced on demand in the browser; sorting high-to-low put valid SGD references first, unavailable prices last.
- Live ECB/Frankfurter rates dated2026-10-29: EUR→SGD1.4265 and USD→SGD1.2817. Browser Pikachu `cel25-5` displayed reference trend SGD5.61 and average comparison SGD5.78 (30-day), SGD5.58 (7-day), SGD6.76 (1-day). Provider update remained2026-10-29; backend fetch around2026-10-30T04:15:06Z. These are observed estimates, not guaranteed resale prices.
- Built preview verified at390px using a temporary iframe. Search, sort, images/unavailable images, selection and the chart rendered without horizontal clipping. Screenshots: `/tmp/pokemon-market-sgd-search.png`, `/tmp/pokemon-market-sgd-chart.png`. Temporary QA HTML removed before handoff. Only this app's loopback preview was restarted.
- Python agent and collection storage are unchanged. Existing Python tests were not rerun. Private HTTPS/actual phone access remains pending the previously requested Tailscale sign-in; no networking changes were made here.

## Rulings

- Ruling: Apply the user's explicit build choice to the recorded matching design and continue the established native execution — avoids repeating approvals for the selected scope — implementation must not introduce another provider, popularity claims or daily history.
- Ruling: Preserve provider order for equally relevant names — live ID sorting put an entire unpriced set first — ordering remains provider-dependent and is not a popularity measure.

## Independent review

Independent fresh-context review of `bb034ce..ab7df04` found no Critical findings, one Important FX expiry defect and one Minor accessibility limitation.

Fixed: mounted views could keep expired FX rates indefinitely. Two fake-clock tests first failed, then passed after renewal/invalidation was added. Open hooks renew at six-hour expiry (or the seven-day observation limit); failed renewal removes the rate, marks it unavailable and retries later. Every amount and chart also checks the record's expiry/date before use, so retained expired values cannot reach tables, sorting or charts. Recovery after a failed renewal is tested. Full suite171/171, build and focused lint passed after the fix. No second review was used.

Deferred minor: chart `role=img` names identify the series/currency but do not enumerate window values; the adjacent accessible table supplies those values. A future accessibility pass should include values in the chart name or use grouped text semantics.

Reviewer exclusions resolved:

- Ruling: Leave actual phone/Tailscale verification outside this follow-up — it remains the established external sign-in step — phone access is still unverified.
- Ruling: Keep popularity ranking and daily history excluded — the operator explicitly chose existing reference data — results cannot answer measured popularity or daily movements.
- Ruling: Keep provider freshness as a manually refreshed snapshot — source timestamps remain visible and this is separate from FX renewal — an idle view can retain its original freshness label until another lookup.
