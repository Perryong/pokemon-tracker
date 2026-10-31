# Market rate recovery Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Browse card prices without manually retrying every rate-limited tile, while protecting selected-card lookups.
**Architecture:** Preserve the 30/minute upstream cap and existing cache. Background tile requests use a header and stop at 25 upstream calls, leaving five for searches/direct lookups. Backend returns retry time and distinguishes local/provider throttling. UI shares one cooldown across three workers, displays a countdown and retries each tile at most twice. Selection cancels the background batch; changed search/unmount cancel retries.
**Tech Stack:** Existing React, TypeScript, Vite middleware, Vitest; no dependencies.
**Spec:** User-approved recommendation in this conversation; this short plan also records the design.

## Constraints and approaches
Automatic pause/resume plus selection priority is the selected next step. Persistent cache and cap tuning are deferred. Continue native execution on codex/market-live-view under the established issue #26 local exception; no push/merge/deployment. Reuse existing cache and request cancellation. Provider cooldown applies globally, including direct lookups; cached values remain available. Missing/malformed Retry-After defaults to 60 seconds, valid HTTP dates and seconds are supported. Delays over one hour stop automatic UI retry with a clear message, never retry early.

## Review focus
Shared cooldown races; cancellation while sleeping; long/malformed provider retry headers; preserving direct capacity/cache hits; bounded retries and selected card focus.

## Task 1 — Backend retry contract and reserved capacity
Files: server/market.ts; src/lib/__tests__/market-server.test.ts.
- [ ] Add tests: 25 background lookups then 429 with retry time while five direct lookups succeed; cached hits remain available; upstream 429 preserves distinct code and cooldown, missing/date headers handled.
- [ ] Run focused tests RED, implement minimal backend contract, run GREEN.

## Task 2 — Cancellable background pause/resume
Files: src/components/MarketSearch.tsx; src/components/MarketView.tsx; their tests.
- [ ] Fake-clock tests: 429 then success after exact wait, no early calls, shared cooldown, maximum two retries, cancellation on search change/unmount and selection.
- [ ] Implement background header, one shared cooldown per batch, countdown and abortable waits. Selection pauses unfinished tile work and preserves loaded results. Direct provider/local error messages include retry seconds.
- [ ] Run tests RED/GREEN; full suite, build, focused lint, browser proof with deterministic temporary local harness if live exhaustion is unnecessary.
- [ ] Independent review, fix important findings with regression tests, record evidence, commit locally.
