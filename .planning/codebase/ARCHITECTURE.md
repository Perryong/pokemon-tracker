# Architecture

**Analysis Date:** 2026-03-20

## Pattern Overview

**Overall:** Component-driven React SPA with hook-based data access and client-side persistence.

**Key Characteristics:**
- Top-level view orchestration is centralized in `src/App.tsx`, with child feature screens rendered conditionally.
- Data access is encapsulated in custom hooks in `src/lib/api.ts` and `src/lib/collection.ts`, then consumed in UI components.
- Persistence is browser-local (`localStorage`) through `useCollection` in `src/lib/collection.ts`; no active runtime backend client is wired into `src/`.

## Layers

**Application Composition Layer:**
- Purpose: Coordinate global view state and screen transitions.
- Location: `src/App.tsx`, bootstrapped by `src/main.tsx`.
- Contains: Route-like view state (`sets | cards | collection`), selected set/card state, modal open state.
- Depends on: Feature components (`src/components/*.tsx`), theme and toast providers (`next-themes`, `src/components/ui/toaster.tsx`).
- Used by: Browser entrypoint in `src/main.tsx`.

**Feature UI Layer:**
- Purpose: Render user-facing flows for set browsing, card browsing, card detail, and collection management.
- Location: `src/components/SetGrid.tsx`, `src/components/CardGrid.tsx`, `src/components/CardDetail.tsx`, `src/components/CollectionView.tsx`, `src/components/CollectionStats.tsx`, `src/components/Navbar.tsx`.
- Contains: Screen components, filtering/sorting UI, pagination controls, modal/detail rendering.
- Depends on: Data hooks in `src/lib/api.ts`, collection store hook in `src/lib/collection.ts`, primitives in `src/components/ui/*`.
- Used by: `src/App.tsx`.

**Data Access Layer (Remote API):**
- Purpose: Define domain models and fetch Pokémon data from external API.
- Location: `src/lib/api.ts`.
- Contains: Interfaces (`PokemonSet`, `PokemonCard`, `CollectionCard`), fetch wrapper with retry/error logic, hooks (`useSets`, `useCards`, `useCard`).
- Depends on: Browser `fetch`, React hooks.
- Used by: `src/components/SetGrid.tsx`, `src/components/CardGrid.tsx`, `src/components/CollectionView.tsx`, `src/App.tsx` (types).

**Client Persistence Layer (Collection Store):**
- Purpose: Manage owned-card state and persist it between sessions.
- Location: `src/lib/collection.ts`.
- Contains: `useCollection` hook, CRUD helpers (`addToCollection`, `updateCollectionCard`, `removeFromCollection`), value computation (`calculateCollectionValue`), local storage serialization.
- Depends on: React state/effects and browser `localStorage`.
- Used by: `src/components/CardGrid.tsx`, `src/components/CardDetail.tsx`, `src/components/CollectionView.tsx`, `src/components/CollectionStats.tsx`, `src/components/Navbar.tsx`.

**Design System / Utility Layer:**
- Purpose: Provide reusable visual primitives and helper utilities.
- Location: `src/components/ui/*.tsx`, `src/hooks/use-toast.ts`, `src/lib/utils.ts`.
- Contains: shadcn/Radix-based UI primitives, toast state reducer/store, className composition helper (`cn`).
- Depends on: Radix UI, Tailwind utility classes, React.
- Used by: All feature components in `src/components/*.tsx`.

## Data Flow

**Browse Sets → Browse Cards → Manage Collection:**

1. App mounts from `src/main.tsx` into `src/App.tsx`, initializing view state and rendering `Navbar` plus the active feature panel.
2. `src/components/SetGrid.tsx` calls `useSets` from `src/lib/api.ts`; filter controls build API query params and render paginated sets.
3. Selecting a set triggers `onSetSelect` to `src/App.tsx`, which stores `selectedSet` and switches view to cards.
4. `src/components/CardGrid.tsx` calls `useCards` from `src/lib/api.ts`, applies extra client-side price filtering, and renders card tiles.
5. Add/remove actions call `useCollection` from `src/lib/collection.ts`, mutating in-memory collection and syncing to `localStorage`.
6. Selecting a card opens `src/components/CardDetail.tsx`, which reads and updates owned metadata through `useCollection`.
7. `src/components/CollectionView.tsx` and `src/components/CollectionStats.tsx` read the same collection hook for filtered lists and computed analytics.

**State Management:**
- Screen/navigation state is local component state in `src/App.tsx`.
- Data-fetch state (`loading`, `error`, result data) is per-hook state in `src/lib/api.ts`.
- Collection state is local hook state persisted to `localStorage` in `src/lib/collection.ts`.
- Toast UI state is managed by a module-level reducer store in `src/hooks/use-toast.ts`, rendered by `src/components/ui/toaster.tsx`.

## Key Abstractions

**Hook-based Data Clients:**
- Purpose: Encapsulate asynchronous fetch lifecycles and return typed results to components.
- Examples: `useSets`, `useCards`, `useCard` in `src/lib/api.ts`.
- Pattern: `useEffect` triggers async fetch on dependency change, updates local `loading/error/data` state tuple.

**Collection Store Hook:**
- Purpose: Single source for collection CRUD and valuation logic.
- Examples: `useCollection` in `src/lib/collection.ts`, consumed by `src/components/CardGrid.tsx` and `src/components/CardDetail.tsx`.
- Pattern: Read-modify-write on object map keyed by card id, mirrored to `localStorage`.

**Composable UI Primitive Wrappers:**
- Purpose: Keep feature components declarative while centralizing primitive behavior/styling.
- Examples: `src/components/ui/select.tsx`, `src/components/ui/dialog.tsx`, `src/components/ui/pagination.tsx`.
- Pattern: Feature modules import prebuilt UI primitives via alias paths (`@/components/ui/...`).

## Entry Points

**Browser Bootstrap:**
- Location: `src/main.tsx`
- Triggers: Vite frontend startup from `index.html`.
- Responsibilities: Mount `<App />` under `StrictMode`, load global styles from `src/index.css`.

**Application Shell:**
- Location: `src/App.tsx`
- Triggers: Initial render from `src/main.tsx`.
- Responsibilities: Theme provider wrapping, top-level navigation state, feature panel switching, card detail modal control, toast container mounting.

**Database Migration Track (separate from runtime app flow):**
- Location: `supabase/migrations/20250518150840_sunny_scene.sql`, `supabase/migrations/20250518150930_empty_silence.sql`
- Triggers: Supabase migration tooling.
- Responsibilities: Define relational schema, indexes, RLS policies, triggers for backend data model.

## Error Handling

**Strategy:** Fail fast with explicit API error classification, expose component-level fallback UI, and keep hook state consistent.

**Patterns:**
- HTTP and network handling in `src/lib/api.ts` classifies 401/404/429 statuses and retries transient failures with backoff.
- Feature components (`src/components/SetGrid.tsx`, `src/components/CardGrid.tsx`) branch on `error` and render retry panels.
- Collection actions in `src/components/CardGrid.tsx` catch action failures and emit destructive toast notifications via `src/hooks/use-toast.ts`.

## Cross-Cutting Concerns

**Logging:** Console-based diagnostics are emitted in `src/lib/api.ts` for failed requests and retry attempts.  
**Validation:** Type-level validation is enforced via TypeScript interfaces in `src/lib/api.ts`; runtime input validation is minimal and mostly UI-constrained.  
**Authentication:** Not implemented in active `src/` runtime flow; Supabase auth policies exist only in migration SQL (`supabase/migrations/*.sql`).

---

*Architecture analysis: 2026-03-20*
