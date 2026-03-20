# Phase 1: Data Foundation & Persistence - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the data and persistence foundation for the tracker: migrate set/card/series data loading to `@tcgdex/sdk`, persist ownership reliably in localStorage, and provide accurate collection-derived completion metrics that downstream views can consume.

</domain>

<decisions>
## Implementation Decisions

### TCGdex Data Integration
- Fully replace the existing PokemonTCG.io fetch layer with `@tcgdex/sdk` in this phase.
- Use SDK calls as canonical sources: `tcgdex.fetch('sets')`, `tcgdex.fetch('series')`, and `tcgdex.fetch('sets', setId)`.
- Normalize returned SDK data into app-facing models used by existing components to reduce downstream churn.

### Ownership Persistence Model
- MVP ownership is boolean only (`owned/unowned`) in this phase.
- Persist minimal localStorage metadata keyed by `cardId` (no full card payload snapshots).
- Exclude quantity/condition/value fields from the phase-1 persisted schema.

### Completion and Derived Stats
- Compute set completion from persisted owned card IDs against set card totals.
- Keep completion math deterministic and recomputable after reload from localStorage + fetched set data.
- Treat derived stats as computed values, not separately persisted aggregates.

### Data Loading and Filtering Behavior
- Use client-side instant filtering on the loaded in-memory dataset as default behavior.
- Keep Phase 1 responsible for reusable data/filter primitives that later set/album views can use directly.
- Preserve explicit loading and error states from hooks so later phases can render UX feedback consistently.

### Claude's Discretion
- Exact adapter/helper naming and file boundaries for SDK wrapper utilities.
- Cache policy details (short-lived in-memory cache vs simple re-fetch semantics) as long as success criteria remain met.
- Internal typing granularity for SDK response normalization.

</decisions>

<specifics>
## Specific Ideas

- This inserted workstream should produce an end-to-end MVP backbone (sets + album + local persistence) by establishing a clean data contract now.
- Keep phase 1 intentionally simple in ownership semantics to avoid schema churn before core flow is validated.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and success criteria
- `.planning/ROADMAP.md` §"Phase 1: Data Foundation & Persistence" — fixed boundary, dependencies, and success criteria.
- `.planning/ROADMAP.md` §"Phase 02.1 (INSERTED)" — urgent insertion context that motivated this foundation clarification.

### Product constraints and intent
- `.planning/PROJECT.md` §"Core Value" — local-progress-first user value.
- `.planning/PROJECT.md` §"Constraints" — mandatory `@tcgdex/sdk` data source and localStorage persistence.

### Requirement contract
- `.planning/REQUIREMENTS.md` §"Data Integration" (`DATA-01..DATA-04`) — required SDK fetch capabilities.
- `.planning/REQUIREMENTS.md` §"Collection Stats and Persistence" (`PERS-01..PERS-03`) — persistence and consistency requirements.

### Existing implementation baseline
- `src/lib/api.ts` — current PokemonTCG.io API client and hook contracts to be migrated.
- `src/lib/collection.ts` — current localStorage collection model to be simplified to minimal ownership metadata.
- `src/App.tsx` — top-level view orchestration consuming set/card flows.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/lib/api.ts`: existing `useSets`, `useCards`, `useCard` hook interface patterns can be preserved while swapping data source internals.
- `src/lib/collection.ts`: existing ownership helper API (`isInCollection`, add/remove, getters) is a usable surface if backing storage is refactored.
- `src/components/ui/*`: existing shadcn/ui primitives already cover loading/error/empty rendering needs for downstream phases.

### Established Patterns
- Hook-based async loading with explicit `loading` and `error` states is already used across set/card screens.
- localStorage hydration on mount + write-on-change effect pattern is established in collection handling.
- Type-first interfaces in `src/lib/api.ts` are the current contract boundary between data and UI.

### Integration Points
- `src/components/SetGrid.tsx` and `src/components/CardGrid.tsx` depend directly on `useSets`/`useCards` response shape.
- `src/components/CardGrid.tsx`, `src/components/CardDetail.tsx`, and `src/components/CollectionView.tsx` depend on collection hook semantics.
- `src/components/Navbar.tsx` and set cards rely on collection counts/progress-ready computed outputs.

</code_context>

<deferred>
## Deferred Ideas

- Quantity and card condition tracking (v2 requirement `ADV-01`) — intentionally deferred.
- Price/value analytics and rich collection economics — deferred outside Phase 1 boundary.
- Cloud sync/account-linked persistence — out of scope for v1 and this phase.

</deferred>

---

*Phase: 01-data-foundation-persistence*
*Context gathered: 2026-03-20*
