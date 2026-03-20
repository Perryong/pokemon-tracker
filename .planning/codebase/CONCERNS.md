# Codebase Concerns

**Analysis Date:** 2026-03-20

## Tech Debt

**Client-side API layer and data hooks are tightly coupled:**
- Issue: API contracts, fetch/retry behavior, and React hooks are implemented in one file, making changes risky and encouraging broad edits.
- Files: `src/lib/api.ts`
- Impact: Small API changes can break multiple views (`SetGrid`, `CardGrid`, `CollectionView`) at once; onboarding and debugging cost increases.
- Fix approach: Split `src/lib/api.ts` into typed API client functions (transport), query builders, and separate hooks per domain (`sets`, `cards`, `card`).

**Duplicate and likely redundant database migration history:**
- Issue: Two migration files define near-identical full schema setup and policies.
- Files: `supabase/migrations/20250518150840_sunny_scene.sql`, `supabase/migrations/20250518150930_empty_silence.sql`
- Impact: Drift risk and confusion about source-of-truth schema when future migrations are added.
- Fix approach: Consolidate to a single canonical baseline migration and add incremental migrations only for deltas.

**Unused backend infrastructure in active frontend flow:**
- Issue: Supabase migration files exist, but application runtime uses browser `localStorage` collection storage and no Supabase client usage is detected in `src`.
- Files: `supabase/migrations/20250518150840_sunny_scene.sql`, `supabase/migrations/20250518150930_empty_silence.sql`, `src/lib/collection.ts`
- Impact: Maintenance overhead with unclear architecture direction (local-first vs hosted persistence).
- Fix approach: Either wire Supabase into runtime data paths or remove/stage backend artifacts outside primary app repository.

## Known Bugs

**Collection state desynchronizes across components in same tab:**
- Symptoms: Collection count/value and “owned” indicators can become stale between views/components until remount or manual refresh.
- Files: `src/lib/collection.ts`, `src/components/Navbar.tsx`, `src/components/CardGrid.tsx`, `src/components/CollectionStats.tsx`, `src/components/CardDetail.tsx`, `src/components/CollectionView.tsx`
- Trigger: Each component calls `useCollection()` and receives isolated `useState` state; updates in one hook instance are not broadcast to others.
- Workaround: Full page refresh or navigation patterns that force remount.

**Card detail form state can carry over between selected cards:**
- Symptoms: Quantity/condition/notes/purchase price may not reflect the newly selected card if modal state persists.
- Files: `src/components/CardDetail.tsx`
- Trigger: Local state is initialized from `collectionCard` once (`useState(...)`) and is not synchronized on `card` change.
- Workaround: Close/reopen modal or manually edit fields each time.

**Linting fails in current branch (blocking quality gate):**
- Symptoms: `npm run lint` exits with errors.
- Files: `src/components/CardGrid.tsx`, `src/components/ui/calendar.tsx`, `src/components/ui/chart.tsx`, `src/components/ui/command.tsx`, `src/components/ui/input.tsx`, `src/components/ui/textarea.tsx`, `src/hooks/use-toast.ts`, `src/lib/api.ts`, `src/lib/collection.ts`
- Trigger: Unused vars, empty object type patterns, `any` usage, and hook dependency warnings.
- Workaround: None reliable; must address lint violations.

## Security Considerations

**Hardcoded API key exposed in client bundle:**
- Risk: Key extraction from shipped frontend enables unauthorized third-party usage and quota exhaustion.
- Files: `src/lib/api.ts`
- Current mitigation: None in code. `.env` exists at repo root (`.env`) and is gitignored (`.gitignore`), but runtime code does not read env for the key.
- Recommendations: Move key to `import.meta.env`, rotate existing key, and proxy external API calls through a server endpoint if key secrecy matters.

**Unvalidated localStorage deserialization:**
- Risk: Corrupted or maliciously injected localStorage data can crash collection initialization.
- Files: `src/lib/collection.ts`
- Current mitigation: None; `JSON.parse` is called without try/catch or schema validation.
- Recommendations: Wrap parse in guarded try/catch and validate parsed shape before use (e.g., zod schema).

## Performance Bottlenecks

**Large UI components with repeated heavy computations on render:**
- Problem: Sorting/filtering/reduction logic executes repeatedly without memoization.
- Files: `src/components/CardGrid.tsx`, `src/components/CollectionView.tsx`, `src/components/CollectionStats.tsx`
- Cause: Inline `filter`, `sort`, and multi-pass price scans run every render; several files exceed 300 lines (`CardGrid.tsx` 445, `CardDetail.tsx` 365, `CollectionStats.tsx` 344).
- Improvement path: Add `useMemo` for derived collections, extract price utilities, and split large components into smaller memoized subcomponents.

**Unnecessary network fetch for card detail in collection view:**
- Problem: Selecting a card in collection triggers `useCard` API fetch although card data is already locally available.
- Files: `src/components/CollectionView.tsx`, `src/lib/api.ts`
- Cause: `selectedCardId` is used with `useCard(...)` instead of using selected card object directly.
- Improvement path: Use local selected card object for modal by default; fetch only when missing/refresh requested.

## Fragile Areas

**Theme handling has dual control paths:**
- Files: `src/App.tsx`, `src/components/Navbar.tsx`
- Why fragile: App uses `ThemeProvider` from `next-themes`, while navbar also directly toggles `document.documentElement.classList` and localStorage.
- Safe modification: Standardize on `next-themes` API (`useTheme`) and remove direct DOM class toggles.
- Test coverage: No project tests detected in `src` for theme behavior regression.

**Reload-based recovery in error UI:**
- Files: `src/components/SetGrid.tsx`, `src/components/CardGrid.tsx`
- Why fragile: `window.location.reload()` masks root causes, loses in-memory UI state, and creates poor offline/slow-network behavior.
- Safe modification: Replace with query retry actions (re-run hook fetch) and scoped fallback UI.
- Test coverage: No automated tests detected for error state and retry behavior.

## Scaling Limits

**Collection persistence tied to browser localStorage capacity:**
- Current capacity: Browser localStorage limits (typically a few MB per origin).
- Limit: Large collections with full card payloads and notes eventually exceed quota; writes fail and user data may not persist.
- Scaling path: Move persisted collection to backend storage (e.g., Supabase tables already defined in `supabase/migrations/*.sql`) with pagination and partial caching.

## Dependencies at Risk

**TypeScript version mismatch with lint parser support:**
- Risk: Tooling instability and false positives/negatives in linting.
- Impact: Slower CI/CD and uncertain static analysis reliability.
- Migration plan: Align TypeScript to supported `@typescript-eslint` range or upgrade `@typescript-eslint` packages to versions supporting installed TS (`npm run lint` currently warns about TS 5.6.3 support).

## Missing Critical Features

**No automated test suite in application source:**
- Problem: No first-party `*.test.*` or `*.spec.*` files detected in `src`.
- Blocks: Safe refactoring of core hooks/components (`src/lib/api.ts`, `src/lib/collection.ts`, `src/components/*`) and confidence in regression prevention.

## Test Coverage Gaps

**Core data and persistence logic untested:**
- What's not tested: Retry logic, error mapping, and query building in API hooks; localStorage persistence behavior and corruption handling.
- Files: `src/lib/api.ts`, `src/lib/collection.ts`
- Risk: Silent failures in production during network issues or malformed storage.
- Priority: High

**User-critical UI workflows untested:**
- What's not tested: Add/remove card flow, filter interactions, pagination boundaries, and collection stats correctness.
- Files: `src/components/CardGrid.tsx`, `src/components/CardDetail.tsx`, `src/components/CollectionView.tsx`, `src/components/CollectionStats.tsx`, `src/components/SetGrid.tsx`
- Risk: Regressions in core collection workflows without detection.
- Priority: High

---

*Concerns audit: 2026-03-20*
