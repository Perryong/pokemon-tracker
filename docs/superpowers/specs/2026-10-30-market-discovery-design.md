# Market discovery, SGD and charts

The operator requested all price displays in SGD, pricing charts, and partial-name search such as Pikachu/pika. They selected: “Use existing data: SGD prices, average-price charts, and relevant card matches with price sorting (recommended)”. Continue the established local build/test workflow on codex/market-live-view; no publication, merge, new subscription or networking change.

## Approach

Reuse TCGdex and the existing Frankfurter conversion pattern. A second provider for daily history and measured popularity was offered and not selected. TCGdex supplies rolling average windows, not daily observations or popularity; label charts and sorting accordingly. No fabricated popularity, stock, completed sales or daily prices.

- Share a validated EUR/USD→SGD rate hook across Market and Card Detail. Keep upstream amounts/currencies unchanged in the API; all displayed prices and charts use estimated SGD with the rate date/source. Missing FX displays unavailable, never a foreign amount labelled SGD. Cache positive validated rates for six hours; reject invalid/future/stale (>7 days) rate dates and nonfinite conversions.
- Add a bounded GET name-search endpoint to the same Mac middleware. Case-insensitive substring search, length 2–60, no arbitrary filters/URLs. Use fixed upstream, no redirects, existing timeout/body/rate/cache rules. Return at most 500 brief matches, validated IDs/names and optional trusted TCGdex images. Rank exact names, then prefix, then substring, with stable ID tie breaks. Cards with multi-part set IDs must remain selectable.
- Show responsive image result tiles, card names/IDs and estimated reference prices. Load 12 at a time, at most 3 concurrent price requests. Reuse card cache/limits; failures remain explicit per card. Show “Load more” for further matches. Relevance is default; SGD price sorting applies to loaded results, explicitly labelled. Choose Cardmarket trend then average as representative reference; fallback to a TCGplayer market price. No implication that aggregate price identifies a specific condition/printing.
- Clicking a card loads the existing full reference view. Preserve direct-ID lookup. Keep search and selection request identities separate; ignore superseded responses and abort on unmount. A cancelled initial lookup must not strand the backend status.
- Render accessible bar comparisons of 30-, 7-, 1-day averages, separate ordinary/holo groups when present. Missing windows stay missing; zero is valid. State that these are overlapping averages, not a daily price history. TCGplayer-only quotes have no average chart. Use simple responsive SVG/HTML, no new dependency.

## Acceptance

Test EUR/USD/zero/failure conversions, rate freshness and currency validation, safe search filters/paths/images, ranking and bounds, special IDs, partial-name matches, selection and search races, price ordering, missing prices, charts with actual available windows, and collection regression. Run full frontend suite, build, changed-file lint, bounded real API checks and phone-width browser verification. One independent final review. Preserve pre-existing repository lint failures and private-access blocker.

## Sources and constraints

TCGdex filtering: https://tcgdex.dev/rest/filtering-sorting-pagination
Pricing fields: https://tcgdex.dev/reference/card
Live checks confirmed EUR/SGD and USD/SGD ECB rates from Frankfurter and partial-name results. Nested price sorting was not trusted from brief-list responses; sort only actually priced results locally. No Ruflo tools available. Project read:project access is still unavailable; retain the operator-approved local exception, never claim signed ownership.
