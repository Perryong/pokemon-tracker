# Market discovery implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Goal:** SGD price displays, truthful average charts and partial-name card discovery.
**Architecture:** Extend existing Market middleware and React view; share FX conversion with Card Detail. Bounded search results are priced in batches using the existing card endpoint. No new dependencies.
**Tech Stack:** TypeScript, React, Zod, Vite, Vitest; responsive SVG/HTML.
**Spec:** docs/superpowers/specs/2026-10-30-market-discovery-design.md

## Global Constraints

Existing data only; reference prices, no popularity or daily-history claims. Preserve original API currencies, render estimated SGD. Local branch only; no push, merge, subscription or network change.

## Review Focus

1. Mixed USD/EUR data never uses the wrong conversion rate, including failed/stale rates.
2. Search filters and images cannot redirect to arbitrary upstream hosts; large results stay bounded.
3. Superseded searches/selection/FX requests cannot replace a newer result or label old prices current.
4. Price sorting includes only loaded valid comparable references and labels its limited coverage.
5. Charts omit missing/nonfinite windows, keep valid zeroes and distinguish averages from daily history.

### Task 1: Shared SGD display and average charts

**Files:** src/lib/exchange-rate.ts, src/components/CardDetail.tsx, src/components/MarketView.tsx, new src/components/PriceChart.tsx, related tests and styles.
**Interfaces:** useSgdExchangeRates(enabled) returns rates keyed EUR/USD and per-currency errors; toSgd(value,currency,rates) returns finite number|null. PriceChart consumes quote prices and validated SGD rate; separate ordinary/holo average groups.
- [x] Write failing tests for both currencies, invalid/future/old dates, nonfinite multiplication, zero, FX failure hiding raw price amounts, and missing/zero chart windows.
- [x] Run focused tests; observe RED.
- [x] Implement shared conversion/cache, accessible bar chart, both display callers; preserve provenance and timestamps.
- [x] Full suite/build/focused lint pass; commit.

### Task 2: Bounded name search and result pricing

**Files:** server/market.ts, src/lib/market.ts, new src/components/MarketSearch.tsx, MarketView.tsx, styles, server/UI tests.
**Interfaces:** GET /api/market/search?q=<2–60 chars> returns schemaVersion1, query, cards[{id,name,image?}], truncated; max500. MarketSearch onSelect(id); prices use original endpoint, shared FX rates. MarketView load(id) supports selected ID and explicit input; health stays independent until a card response supersedes it.
- [x] Write failing tests for partial-name search, ranking, bounded inputs/results/images, cache/rate reuse, multi-hyphen IDs, empty/malformed responses; UI 12-item paging, limited concurrency, sorting/error states and stale-response suppression.
- [x] Observe RED, implement exact endpoint and search component without arbitrary query forwarding; keep all existing request/body/cache constraints.
- [x] Verify full tests/build/focused lint, commit.

### Task 3: Runtime verification and review

**Files:** docs/market-live-view.md, docs/market-discovery-verification.md, README.md as needed.
- [x] Restart only this app's preview, verify real pika results and SGD values, chart and card selection at390px; capture screenshot.
- [x] Verify all tests/build/affected lint and whitespace; report existing lint separately.
- [x] Independent whole-change review; one RED→GREEN fix pass for Important/Critical findings. Record decisions/deferred minors and keep local branch, leave private phone sign-in pending.
