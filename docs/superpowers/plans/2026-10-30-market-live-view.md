# Mac-hosted Market View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Show real TCGdex reference prices through a Mac-hosted API and phone-friendly Market view, with private access.
**Architecture:** Existing Vite middleware hosts GET-only market endpoints beside the built React UI. Shared Zod response validation keeps provider data and frontend state bounded and truthful. Tailscale Serve exposes only the loopback preview service.
**Tech Stack:** Existing TypeScript, React, Vite, Zod, Vitest, Node fetch, Tailscale; no new dependencies.
**Spec:** `docs/superpowers/specs/2026-10-30-market-live-view-design.md`

## Authorization and execution

On 30 October the operator answered “Approve the code and proceed next step” to the explicit design/local-build/test/private-Tailscale exception request. This authorizes implementation and private access configuration for issue #26, not merge or publication. Preserve Native execution already selected in this conversation; the latest approval is direction to build, not another planning checkpoint. Work in the existing dedicated `codex/market-live-view` checkout, preserving the Mac server and user-selected project location. Project/claim remains unavailable and is not asserted.

## Global Constraints

- Read-only reference prices; no real inventory, sale evidence, mandates, model calls or Sales UI.
- Fixed TCGdex HTTPS origin; no credentials or private data in API/build/Git.
- Same-origin API; loopback preview; no public Funnel, unrelated network changes or new dependencies.
- Keep existing collection, Card Detail fallback, and Python Market harness unchanged.
- Surface stale/unknown timestamps, retained prices after failed refresh and backend absence honestly.

## Review Focus

1. Encoded path/query and redirect tricks must not broaden the fixed upstream capability (Task 1).
2. Cached results crossing the 48-hour freshness boundary must not retain a current label (Task 1).
3. Late responses after card changes/unmount must not replace current selection (Task 2).
4. A reachable backend with unavailable upstream must not be shown as fully healthy (Task 2).
5. Private HTTPS and public/static builds must not expose credentials or claim a simulated harness is live (Task 3).

### Task 1: Validated live-price API

**Files:** Create `src/lib/market.ts`, `server/market.ts`, `src/lib/__tests__/market-server.test.ts`; modify `vite.config.ts`.
**Interfaces:** `MarketCardSchema` and inferred `MarketCard`, `MarketHealthSchema`, `marketMiddleware(): (req,res,next)=>Promise<void>`. Response: schemaVersion 1, mode reference, source TCGdex, card id/name, fetchedAt, quotes with provider/currency/variant/updatedAt/freshness/prices. Fixed EUR Cardmarket and USD TCGplayer. Known price metrics only, no null/negative/nonfinite amounts. Timestamp validation supports timezone-bearing ISO values; invalid/future timestamp => unknown. Current <=48h, stale >48h.

- [x] Write tests: health capability without upstream call; successful same-ID response and metadata; no secret/unknown fields; invalid path/query/method without upstream; mismatched ID and malformed data =>502; missing card=>404; no prices=>200 empty; timeout=>504; sanitized unexpected failures; redirect rejection. Invalid/future dates =>unknown. Cache/inflight =>one request, TTL 1h; recompute freshness on cache hit; capacity256; upstream limit30/minute with cache hits still available.
- [x] Run `NODE_OPTIONS=--no-experimental-webstorage npx vitest run src/lib/__tests__/market-server.test.ts`; expect missing module/function failure.
- [x] Implement narrow schema and fixed-origin middleware. Use existing `normalizeTCGCard` only if it preserves bounds and accurate variant labels; otherwise reuse known field conventions without importing the full card adapter. Network timeout8s, redirects error, response bounded to1MiB, no-store browser cache, server cache retains original fetchedAt. Errors are static safe codes. Unrelated paths call next. Register in dev and preview.
- [x] Run focused and full frontend suite; expect all tests passing. Commit Task 1 files.

### Task 2: Accessible mobile Market view

**Files:** Create `src/components/MarketView.tsx`, `src/components/__tests__/MarketView.test.tsx`; modify `src/App.tsx`, `src/components/Navbar.tsx`, `src/index.css`, existing App regression test.
**Interfaces:** Component consumes Task1 schemas and same-origin endpoints. Health checked on mount; card requested only via user submit/refresh. Explicit ID validation; safe messages for error codes. Abort prior requests and use generation identity to ignore late responses. 12s frontend deadline. No auto polling.

- [x] Write tests: rendered success/currency/source/date; no-price result; invalid ID no fetch; unavailable HTML response; upstream failure distinct from backend reachability; previous results retained and marked failed refresh; stale response ignored after new ID/unmount; simulated harness label; App navigation and collection persistence intact.
- [x] Run focused component tests; expect missing view failure and absent Market nav failure.
- [x] Implement Market view and nav. Use existing house Button, page/filter/control/table classes with focused responsive additions. Validated API response only; no provider HTML or dynamic URLs. Show reference-only qualification limit and dates in user-readable form. Health reachability and price-fetch errors remain distinct.
- [x] Run full frontend suite and `npm run build`; expect pass. Run focused lint for changed files, report root pre-existing lint separately. Commit Task2 files.

### Task 3: Built runtime, private access and handoff

**Files:** Add `docs/market-live-view.md`, verification record and README link; update plan/spec status.
**Interfaces:** `npm run build`; `npm run preview -- --host 127.0.0.1 --port 5184 --strictPort`; `tailscale serve --bg http://127.0.0.1:5184` only after inspecting installed help/config. Do not commit private hostname/config.

- [x] Test build and API from actual loopback preview; two-card live smoke test validates IDs, currency, timestamps and mode. No account charges or subscriptions.
- [x] Browser verify Market on phone-width viewport, navigation, failure handling and screenshot. Capture real data with timestamps; check static build for credentials/private URLs.
- [x] Inspect Tailscale state/config; enable existing connection without resetting preferences, then Serve only this service. Preserve unrelated configs. Verify private HTTPS locally if possible; never claim phone verification without a phone response. If enrolment, sign-in or HTTPS enablement needs the user, provide the precise action/link and finish independent work.
- [x] Document exact start/stop/access limits and results, run whitespace/full suite/build/focused lint as required. One independent review of the whole change, fix Important findings with red-green tests, record rulings and deferred minors. Commit intended files locally; no new push/merge.

## Self-review

All spec sections map to Tasks1–3. Shared schemas join Task1→Task2; actual preview middleware connects Task1→Task3. Every review focus has a named behavioral check. Phone enrolment is an external acceptance condition, not something a passing local test proves.

## Execution status

Local implementation and verification complete; private HTTPS enablement and an actual phone round trip remain operator-dependent. See `docs/market-live-view-verification.md`. Final independent review is recorded there.
