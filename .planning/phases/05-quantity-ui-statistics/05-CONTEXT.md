# Phase 5: Quantity UI & Statistics - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver quantity-based album interaction and stats semantics on top of the migrated quantity model: users can adjust duplicates directly in the card album, keep fast toggle behavior, and see consistent unique-vs-total metrics across album, set cards, and collection summary views.

</domain>

<decisions>
## Implementation Decisions

### Card-Level Quantity Control UX
- Quantity controls are inline on each album card tile, adjacent to current ownership action area.
- Use compact `minus / quantity badge / plus` controls.
- Keep existing owned visual styling and also show quantity badge at `1` (not hidden).
- Controls are always visible on mobile; on desktop they appear on hover/focus states.

### Toggle and Adjustment Behavior
- Existing fast toggle remains primary via card action button (`0 ↔ 1`).
- `+` on quantity `0` sets quantity to `1` immediately and shows owned visuals right away.
- If quantity is `>1`, toggle action resets directly to `0`.
- At max quantity (`999`), plus button is disabled with subtle disabled styling.

### Statistics and Progress Semantics
- Completion percentage remains unique-owned based (`uniqueOwned / totalCards`), never total quantity based.
- Album fixed footer shows: `Owned (unique)`, `Missing`, `Completion %`, and `Total Quantity`.
- SetGrid keeps existing `Owned X/Y` and adds a supplemental `Total Qty: Z` line.
- `CollectionView` and `CollectionStats` must be updated in this phase to use quantity-aware metrics for consistency.

### Feedback and Error Behavior
- Success toast behavior: keep for toggle action; `plus/minus` adjustments stay silent unless an error occurs.
- On quantity save/update failure, user message emphasizes: "Quantity update not saved; your current session state is still active."
- Errors are surfaced both as user-facing toast and detailed console diagnostics.

### Scope Guardrails
- Keyboard quantity shortcuts are deferred beyond this phase.
- Manual quantity input field is deferred (already tracked in future requirements).
- No cloud sync, trading inventory, or valuation scope in this phase.

### Claude's Discretion
- Exact micro-layout and spacing of tile controls and badge density.
- Animation/transition details for hover/focus reveal on desktop.
- Internal helper extraction for unique-vs-total stats computation reuse.

</decisions>

<specifics>
## Specific Ideas

- Preserve the v1 "fast scan and quick toggle" feel while adding duplicate control as an augmentation, not a replacement.
- Keep stats understandable at a glance by clearly separating ownership progress (unique) from collection volume (total quantity).

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` §"Phase 5: Quantity UI & Statistics" — fixed scope and success criteria.
- `.planning/REQUIREMENTS.md` §"Quantity Controls" (`CTRL-01..CTRL-04`) — UI behavior requirements.
- `.planning/REQUIREMENTS.md` §"Statistics & Progress Semantics" (`STATQ-01..STATQ-03`) — metric contracts.

### Upstream quantity model and migration behavior
- `.planning/phases/04-data-model-migration/04-CONTEXT.md` — migration and quantity semantics decisions.
- `.planning/phases/04-data-model-migration/04-RESEARCH.md` — implementation constraints and validation architecture.
- `.planning/phases/04-data-model-migration/04-VALIDATION.md` — test sampling expectations to preserve.

### Existing code surfaces
- `src/components/CardGrid.tsx` — album interaction surface, ownership filters, footer stats.
- `src/components/SetGrid.tsx` — per-set progress card rendering where `Total Qty` supplement is added.
- `src/components/CardDetail.tsx` — secondary ownership surface that must remain behavior-consistent.
- `src/components/CollectionView.tsx` — summary metric surface to update for quantity-aware values.
- `src/components/CollectionStats.tsx` — stats summary surface to update for quantity-aware values.
- `src/lib/collection.ts` — quantity APIs (`getQuantity`, `setQuantity`, `incrementQuantity`, `decrementQuantity`) and compatibility wrappers.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useCollection` already exposes quantity and compatibility APIs, enabling Phase 5 UI work without schema changes.
- `CardGrid` already has an ownership action region, filter controls, and fixed footer that can be extended instead of redesigned.
- Existing `Badge`, `Button`, `Input`, and hover/focus utility patterns in shadcn/ui cover required control styling.

### Established Patterns
- Ownership filtering in album uses `isInCollection` and must remain derived from quantity semantics.
- Stats in CardGrid are computed from filtered dataset; this should continue while expanding displayed metrics.
- Set and collection summary components currently derive owned totals from `ownedCards`, giving a direct baseline for quantity-aware extension.

### Integration Points
- Card tile controls in `CardGrid` must coordinate with existing `handleAddToCollection` / `handleRemoveFromCollection` flows.
- SetGrid progress (`Owned X/Y`) and album footer stats must stay mathematically consistent after quantity updates.
- Collection summary views (`CollectionView`, `CollectionStats`) must align with the same unique-vs-total metric definitions used in album/set surfaces.

</code_context>

<deferred>
## Deferred Ideas

- Keyboard shortcuts for quantity controls.
- Manual numeric quantity input on card tiles.
- Duplicates-only advanced filter mode beyond current ownership filter.
- Trade inventory / condition / value features.

</deferred>

---

*Phase: 05-quantity-ui-statistics*
*Context gathered: 2026-03-21*
