# Phase 3: Cards Album & Ownership Tracking - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the cards album experience for a selected set: responsive card grid with real images, click-to-toggle ownership, owned-state indicators, size controls, ownership/search filters, and a fixed real-time stats footer.

</domain>

<decisions>
## Implementation Decisions

### Card Interaction Model
- Keep the existing card-grid interaction pattern where users can act directly on a card from the album surface.
- Preserve immediate ownership feedback on toggle actions.
- Keep owned-state signaling visually explicit on card tiles.

### Album Controls
- Add a card size toggle with exactly two modes: small and medium.
- Add ownership-state filter with exactly three modes: all, owned, missing.
- Add in-set live name search that filters cards as the user types.

### Stats Footer Behavior
- Implement a fixed bottom stats footer in album view.
- Footer must display owned count, missing count, and completion percentage.
- Footer values update in real time as ownership changes.

### Data and Scope Guardrails
- Continue using existing TCGdex-backed card data and local ownership persistence from earlier phases.
- Do not introduce cloud/auth/account or valuation features in this phase.
- Keep advanced quantity/condition/wishlist features deferred (v2 scope).

### Claude's Discretion
- Exact placement/density of album controls while preserving responsive behavior.
- Search/filter control styling details and iconography.
- Internal memoization/derived-state helpers for filter + stats calculations.

</decisions>

<specifics>
## Specific Ideas

- Preserve the current fast “browse and toggle” feel from the existing card grid while adding clearer control affordances.
- Prioritize scanability: users should quickly see owned status, narrow to missing cards, and track progress without leaving album view.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirement contract
- `.planning/ROADMAP.md` §"Phase 3: Cards Album & Ownership Tracking" — goal, dependencies, and success criteria.
- `.planning/REQUIREMENTS.md` §"Cards Album View" (`ALBM-01..ALBM-07`) and §"Collection Stats and Persistence" (`STAT-01`) — mandatory phase outputs.

### Upstream decisions and constraints
- `.planning/PROJECT.md` §"Constraints" — local-first/personal-use scope and required stack constraints.
- `.planning/phases/01-data-foundation-persistence/01-CONTEXT.md` — persistence/data decisions that album behavior depends on.
- `.planning/phases/02-sets-view-navigation/02-CONTEXT.md` and `02-UI-SPEC.md` — UI patterns and navigation continuity from sets view.

### Existing implementation baseline
- `src/components/CardGrid.tsx` — current album grid, filters, pagination, and add/remove interactions.
- `src/components/CardDetail.tsx` — detail modal + ownership actions and owned-state display.
- `src/lib/collection.ts` — ownership persistence and collection helper APIs.
- `src/App.tsx` — set→cards navigation and card-detail wiring.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CardGrid` already provides responsive card rendering, image fallback handling, and ownership action buttons.
- `useCollection` exposes `isInCollection`, `addToCollection`, and `removeFromCollection` for immediate toggle behavior.
- Existing shadcn primitives (`Select`, `Badge`, `Button`, `Input`, `Pagination`, `Skeleton`) cover required album controls and UI states.

### Established Patterns
- Hook-based loading/error states in list views (`useCards` + guard renders).
- Client-side derived collections via `useMemo`/array transforms for filtering and stats.
- Visual status cues via badge/ring styling and toast feedback on ownership updates.

### Integration Points
- `SetGrid` selection feeds `CardGrid` via `selectedSet` in `App.tsx`.
- Ownership toggles in album must stay consistent with set-level completion calculations.
- Stats footer should consume the same filtered/ownership-aware card dataset shown on screen.

</code_context>

<deferred>
## Deferred Ideas

- Quantity/condition/notes as core collection attributes in album cards (v2 scope).
- Price/market analytics or valuation overlays.
- Deep-link routing, saved filter presets, and cross-set global search.

</deferred>

---

*Phase: 03-cards-album-ownership-tracking*
*Context gathered: 2026-03-21*
