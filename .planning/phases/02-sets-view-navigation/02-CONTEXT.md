# Phase 2: Sets View & Navigation - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the Sets View so users can browse all Pokemon TCG sets, filter/search them quickly, see per-set completion progress, identify completed sets, and open a set into the cards album flow.

</domain>

<decisions>
## Implementation Decisions

### Sets Surface Layout
- Use the existing card-grid style in `SetGrid` as the primary layout (no table/list redesign in this phase).
- Keep set logos/symbols as the visual anchor, with set metadata and completion details underneath.
- Preserve responsive grid behavior across mobile and desktop breakpoints already used by the current component.

### Filtering and Search Behavior
- Keep a series dropdown as a first-class filter for this phase.
- Keep live set-name search with immediate client-side filtering while typing.
- Retain existing legality and release-date filters where they do not conflict with series/search behavior.

### Progress and Completion Signals
- Continue rendering owned/total values with a progress bar per set card.
- Keep a distinct completion badge/indicator when a set reaches 100% ownership.
- Use current collection-derived percentage math from phase 1 as the single source of truth.

### Navigation Flow
- Clicking a set card should navigate directly to the album/cards view for that selected set.
- Preserve current app-level navigation contract (`sets` -> `cards`) rather than introducing a new route system in this phase.
- Keep interaction latency low by relying on the existing hooks/data pipeline.

### Claude's Discretion
- Exact filter control placement and spacing refinements within existing layout constraints.
- Empty/loading copy details and minor badge/label wording.
- Internal helper extraction for filter composition/search normalization.

</decisions>

<specifics>
## Specific Ideas

- Maintain continuity with the existing polished card-based UI rather than introducing a net-new visual paradigm.
- Emphasize "quick scan + quick open" behavior: users should identify set status at a glance and open the target set in one click.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and success criteria
- `.planning/ROADMAP.md` §"Phase 2: Sets View & Navigation" — definitive goal and success criteria for sets browsing and navigation.
- `.planning/REQUIREMENTS.md` §"Sets View" (`SETS-01..SETS-05`) — required capability checklist for this phase.

### Upstream constraints and persistence contract
- `.planning/PROJECT.md` §"Constraints" — requires `@tcgdex/sdk` and local-first persistence model.
- `.planning/phases/01-data-foundation-persistence/01-CONTEXT.md` — decisions that lock data/persistence behavior consumed by sets view.

### Existing implementation baseline
- `src/components/SetGrid.tsx` — current sets grid, filters, progress, and click-through surface.
- `src/lib/api.ts` (`useSets`, `useSeries`) — data loading/filtering hooks used by sets view.
- `src/lib/collection.ts` — ownership source for completion calculations.
- `src/App.tsx` and `src/components/Navbar.tsx` — view switching/navigation integration points.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SetGrid` already contains responsive set cards, progress bars, completion badges, and pagination scaffolding.
- `useSets` + `useSeries` in `src/lib/api.ts` provide set and series data with loading/error states.
- Shared shadcn controls (`Select`, `Input`, `Badge`, `Progress`, `Skeleton`, `Pagination`) are already integrated and reusable.

### Established Patterns
- Hook-driven async data fetching with explicit loading/error handling.
- Client-side filtering composed via a `filters` object and memoized completion calculations.
- App-wide view state managed in `App.tsx` with typed view unions and callback props.

### Integration Points
- `SetGrid.onSetSelect` drives transition into album/cards view in `App.tsx`.
- Collection ownership map from `useCollection` powers completion indicators in set cards.
- `Navbar` controls switching between sets and collection views and should remain behaviorally aligned.

</code_context>

<deferred>
## Deferred Ideas

- Advanced set sorting/grouping strategies beyond current requirements (can be future UX enhancement).
- URL-based routing/deep-linking for sets (out of scope for this phase).
- Collection analytics expansion beyond per-set completion bars.

</deferred>

---

*Phase: 02-sets-view-navigation*
*Context gathered: 2026-03-21*
