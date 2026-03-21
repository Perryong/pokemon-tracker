# Phase 5: Quantity UI & Statistics - Research

**Researched:** 2025-01-21
**Domain:** React UI/UX patterns for quantity controls and statistics presentation
**Confidence:** HIGH

## Summary

Phase 5 integrates the quantity model (from Phase 4) into user-facing UI surfaces across CardGrid, SetGrid, CollectionView, and CollectionStats. The core challenge is delivering quantity controls (increment/decrement) while preserving the fast `0 ↔ 1` toggle workflow that makes v1.0 successful, and ensuring stats semantics remain consistent (unique-owned vs total-quantity distinction) across all views.

**Primary recommendation:** Extend existing components with minimal structural change. Add inline quantity controls to CardGrid tiles using existing shadcn/ui Button and Badge components. Augment fixed footer and SetGrid progress displays to show both unique-owned and total-quantity metrics. Keep the fast-toggle action as the primary interaction, with quantity controls as secondary/progressive disclosure.

**Risk mitigation:** The highest risk is breaking existing click-to-toggle UX or introducing stats divergence between views. Use feature flags or conditional rendering to allow incremental rollout, and enforce single-source-of-truth stats computation to prevent off-by-one errors.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Card-Level Quantity Control UX:** Quantity controls are inline on each album card tile, adjacent to current ownership action area. Use compact `minus / quantity badge / plus` controls. Keep existing owned visual styling and also show quantity badge at `1` (not hidden). Controls are always visible on mobile; on desktop they appear on hover/focus states.
- **Toggle and Adjustment Behavior:** Existing fast toggle remains primary via card action button (`0 ↔ 1`). `+` on quantity `0` sets quantity to `1` immediately and shows owned visuals right away. If quantity is `>1`, toggle action resets directly to `0`. At max quantity (`999`), plus button is disabled with subtle disabled styling.
- **Statistics and Progress Semantics:** Completion percentage remains unique-owned based (`uniqueOwned / totalCards`), never total quantity based. Album fixed footer shows: `Owned (unique)`, `Missing`, `Completion %`, and `Total Quantity`. SetGrid keeps existing `Owned X/Y` and adds a supplemental `Total Qty: Z` line. `CollectionView` and `CollectionStats` must be updated in this phase to use quantity-aware metrics for consistency.
- **Feedback and Error Behavior:** Success toast behavior: keep for toggle action; `plus/minus` adjustments stay silent unless an error occurs. On quantity save/update failure, user message emphasizes: "Quantity update not saved; your current session state is still active." Errors are surfaced both as user-facing toast and detailed console diagnostics.
- **Scope Guardrails:** Keyboard quantity shortcuts are deferred beyond this phase. Manual quantity input field is deferred (already tracked in future requirements). No cloud sync, trading inventory, or valuation scope in this phase.

### Claude's Discretion
- Exact micro-layout and spacing of tile controls and badge density.
- Animation/transition details for hover/focus reveal on desktop.
- Internal helper extraction for unique-vs-total stats computation reuse.

### Deferred Ideas (OUT OF SCOPE)
- Keyboard shortcuts for quantity controls.
- Manual numeric quantity input on card tiles.
- Duplicates-only advanced filter mode beyond current ownership filter.
- Trade inventory / condition / value features.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CTRL-01 | User can increment a card quantity from the album view | shadcn/ui Button component, useCollection.incrementQuantity API, inline controls pattern |
| CTRL-02 | User can decrement a card quantity and never go below zero | useCollection.decrementQuantity with 0-floor validation, disabled state styling |
| CTRL-03 | User can still use single-click card toggle for fast `0 ↔ 1` ownership changes | Preserve existing handleAddToCollection/handleRemoveFromCollection, add conditional behavior for qty>1 |
| CTRL-04 | User sees clear quantity badges/indicators for cards with duplicates | shadcn/ui Badge component, conditional rendering (qty=1 checkmark, qty>1 badge with number) |
| STATQ-01 | User sees set completion based on unique owned cards, not total duplicate count | Maintain existing unique-count logic in stats computation, explicitly document unique vs total |
| STATQ-02 | User sees separate unique-owned and total-quantity metrics where stats are shown | Extend footer/SetGrid to show both metrics with clear labels ("Owned (unique)" and "Total Qty") |
| STATQ-03 | User gets consistent stats across SetGrid, CardGrid, and collection summary views after quantity updates | Single source of truth for stats computation, reuse helper functions, shared hook for quantity-aware metrics |
</phase_requirements>

## Standard Stack

### Core (No New Dependencies)
All Phase 5 features leverage the existing v1.0 stack. No new packages required.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React 18.3.1 | 18.3.1 | Component framework | Existing project foundation, hooks-based state management |
| @radix-ui/react-tooltip | 1.1.2 (current: 1.2.8) | Hover tooltips for controls | Already in dependencies, accessibility built-in, composable with Button |
| shadcn/ui Button | - | Increment/decrement controls | Already used throughout project, variant system supports disabled states |
| shadcn/ui Badge | - | Quantity display | Already used for rarity/types, compact size perfect for quantity indicator |
| lucide-react | 0.446.0 | Icons (Plus, Minus, Check) | Already in dependencies, consistent icon system |
| Vitest 4.1.0 + Testing Library | 4.1.0 / 16.3.2 | Test framework | Existing test infrastructure validated in Phase 4 |

**Installation:** None required. All components and APIs already present.

**Version verification (performed 2025-01-21):**
- @radix-ui/react-tooltip: project has 1.1.2, latest is 1.2.8 (minor update available but not required)
- All other dependencies current and verified in package.json

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx / cn utility | 2.1.1 | Conditional classNames | Apply disabled/hover states to quantity controls |
| useToast hook | - | Error feedback | Show quantity update errors per user constraint (silent on success, toast on error) |
| useMemo | React 18.3.1 | Stats computation | Derive unique/total metrics efficiently without re-renders |
| useCallback | React 18.3.1 | Stable operation handlers | Prevent re-renders when passing increment/decrement to child components |

### Alternatives Considered
None. Phase 5 is brownfield integration using proven stack from Phase 4 and v1.0.

## Architecture Patterns

### Recommended Component Structure
Extend existing components, don't replace them. Phase 5 touches 5 files:

```
src/
├── components/
│   ├── CardGrid.tsx         # ADD: quantity controls inline, UPDATE: footer stats
│   ├── SetGrid.tsx          # ADD: total quantity supplement to progress display
│   ├── CollectionView.tsx   # UPDATE: quantity-aware stats
│   ├── CollectionStats.tsx  # UPDATE: quantity-aware stats with unique/total breakdown
│   └── ui/
│       └── (no changes)     # Reuse existing Button, Badge, Tooltip
├── lib/
│   ├── collection.ts        # ALREADY HAS: incrementQuantity, decrementQuantity APIs (from Phase 4)
│   └── stats.ts             # CREATE: shared stats computation helpers (optional, Claude's discretion)
```

### Pattern 1: Inline Quantity Controls with Conditional Visibility
**What:** Add increment/decrement controls to CardGrid tiles, shown on desktop hover/focus, always visible on mobile.
**When to use:** Card album view where users interact with individual cards.
**Example:**
```tsx
// Source: Derived from CardGrid.tsx existing hover overlay pattern
const QuantityControls: React.FC<{ card: PokemonCard }> = ({ card }) => {
  const { getQuantity, incrementQuantity, decrementQuantity } = useCollection();
  const quantity = getQuantity(card.id);
  
  return (
    <div className="flex items-center gap-1">
      <Button
        size="sm"
        variant="outline"
        onClick={(e) => {
          e.stopPropagation();
          decrementQuantity(card.id);
        }}
        disabled={quantity === 0}
        className="h-7 w-7 p-0"
      >
        <Minus className="h-3 w-3" />
      </Button>
      
      <Badge variant="secondary" className="min-w-[2rem] justify-center">
        {quantity}
      </Badge>
      
      <Button
        size="sm"
        variant="outline"
        onClick={(e) => {
          e.stopPropagation();
          incrementQuantity(card.id);
        }}
        disabled={quantity >= 999}
        className="h-7 w-7 p-0"
      >
        <Plus className="h-3 w-3" />
      </Button>
    </div>
  );
};
```

**Integration point:** Add to CardGrid's existing hover overlay (line 371 in current code) alongside the Add/Remove button. Use CSS classes for desktop-only hover visibility, mobile always-visible.

### Pattern 2: Preserve Fast Toggle with Quantity-Aware Behavior
**What:** Existing toggle button (`handleAddToCollection`/`handleRemoveFromCollection`) adapts based on current quantity.
**When to use:** Maintain v1.0 fast workflow while supporting quantity model.
**Example:**
```tsx
// Source: Modified from CardGrid.tsx handleAddToCollection (line 117)
const handleToggleOwnership = async (card: PokemonCard, e: React.MouseEvent) => {
  e.stopPropagation();
  const quantity = getQuantity(card.id);
  
  try {
    if (quantity === 0) {
      // Fast add: 0 → 1
      await addToCollection(card.id);
      toast({ title: "Card Added", description: `${card.name} added.`, duration: 2000 });
    } else {
      // Any quantity > 0: reset to 0
      await setQuantity(card.id, 0);
      toast({ title: "Card Removed", description: `${card.name} removed.`, duration: 2000 });
    }
  } catch (error) {
    toast({
      title: "Error",
      description: "Quantity update not saved; your current session state is still active.",
      variant: "destructive",
    });
    console.error('Toggle ownership failed:', error);
  }
};
```

**Key insight:** Toggle behavior changes based on quantity state, but UX remains single-click. User constraint specifies: "If quantity is `>1`, toggle action resets directly to `0`."

### Pattern 3: Single-Source Stats Computation
**What:** Derive unique-owned and total-quantity metrics from `cardQuantities` in one place, reuse everywhere.
**When to use:** CardGrid footer, SetGrid progress, CollectionView, CollectionStats.
**Example:**
```tsx
// Source: New helper (Claude's discretion for extraction)
// lib/stats.ts or inline in useCollection
export interface QuantityStats {
  uniqueOwned: number;    // Count of cardIds with qty > 0
  totalQuantity: number;  // Sum of all quantities
  missing: number;        // total - uniqueOwned
  completionPercent: number; // (uniqueOwned / total) * 100
}

export function computeSetStats(
  setCardIds: string[],
  cardQuantities: Record<string, number>
): QuantityStats {
  const totalCards = setCardIds.length;
  
  const uniqueOwned = setCardIds.filter(id => (cardQuantities[id] ?? 0) > 0).length;
  const totalQuantity = setCardIds.reduce((sum, id) => sum + (cardQuantities[id] ?? 0), 0);
  const missing = totalCards - uniqueOwned;
  const completionPercent = totalCards > 0 ? (uniqueOwned / totalCards) * 100 : 0;
  
  return { uniqueOwned, totalQuantity, missing, completionPercent };
}
```

**Usage in CardGrid footer:**
```tsx
const stats = useMemo(() => {
  const setCardIds = filteredCards.map(c => c.id);
  return computeSetStats(setCardIds, cardQuantities);
}, [filteredCards, cardQuantities]);

// Footer display (line 502 in current CardGrid.tsx)
<Badge>Owned: {stats.uniqueOwned}</Badge>
<Badge>Missing: {stats.missing}</Badge>
<Badge>Completion: {stats.completionPercent.toFixed(1)}%</Badge>
<Badge>Total Qty: {stats.totalQuantity}</Badge>
```

### Pattern 4: Progressive Enhancement for SetGrid
**What:** Add total quantity supplement to existing progress display without breaking layout.
**When to use:** SetGrid set cards (line 318-330 in current SetGrid.tsx).
**Example:**
```tsx
// Source: Extended from SetGrid.tsx completion display (line 318)
<div className="space-y-2 mb-4">
  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 text-sm">
    <span className="font-medium">
      Owned {completion.owned} / {completion.total}
    </span>
    <span className="text-xs uppercase tracking-wide text-muted-foreground">
      {completion.percentage.toFixed(0)}%
    </span>
  </div>
  {/* NEW: Total quantity supplement */}
  <div className="text-xs text-muted-foreground">
    Total Qty: {completion.totalQuantity}
  </div>
  <Progress
    value={completion.percentage}
    aria-label={`Owned ${completion.owned} of ${completion.total} cards in ${set.name}`}
  />
</div>
```

**Integration:** Modify `completionBySet` computation in SetGrid.tsx (line 76-103) to include `totalQuantity` field.

### Anti-Patterns to Avoid

- **Mixing boolean ownedCards with quantity logic:** Phase 4 established `cardQuantities` as single source of truth. NEVER check both `ownedCards[id]` and `cardQuantities[id]` — always derive owned from quantity.
- **Hidden quantity badge at qty=1:** User constraint specifies badge shown at `1`, not hidden. Prevents confusion about whether card is owned.
- **Toasting on successful increment/decrement:** User constraint: silent on success, toast only on error. Reduces notification fatigue.
- **Total quantity in completion percentage:** STATQ-01 explicitly: completion is unique-owned based. Never `(totalQuantity / totalCards) * 100`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Button disabled states | Custom CSS for opacity/cursor | shadcn/ui Button `disabled` prop | Built-in accessibility (aria-disabled), keyboard handling, focus management |
| Hover tooltips for controls | Custom position-tracking tooltip | @radix-ui/react-tooltip (already in deps) | Portal rendering, collision detection, ARIA labeling automatic |
| Stats computation caching | Manual dirty-checking or ref-based cache | React `useMemo` with deps array | React handles invalidation, prevents stale closures, debuggable with DevTools |
| Quantity increment/decrement | Direct state mutation or separate handlers | useCollection APIs (incrementQuantity, decrementQuantity) | Atomic updates, 0-999 clamping built-in, sparse storage automatic |

**Key insight:** All quantity UI primitives already exist (Button, Badge, Tooltip) and quantity operations already implemented (Phase 4). Phase 5 is pure composition, not new primitives.

## Common Pitfalls

### Pitfall 1: Stats Divergence Between Views
**What goes wrong:** CardGrid shows different completion percentage than SetGrid for the same set because computation logic is duplicated and inconsistent.
**Why it happens:** Copy-paste stats logic with slight variations (e.g., one uses `ownedCards`, another uses `cardQuantities`). Filtering differences (filtered vs full set). Timing issues (one view uses stale data).
**How to avoid:** Single source of truth for stats computation. Extract `computeSetStats` helper and reuse in CardGrid, SetGrid, CollectionView, CollectionStats. Always pass `cardQuantities` from `useCollection`, never derive locally.
**Warning signs:** "Why do my stats not match between views?" user reports. Automated tests for same dataset returning different stats. Console logs showing different owned counts for same set.

### Pitfall 2: Breaking Fast Toggle UX
**What goes wrong:** Adding quantity controls makes the fast `0 ↔ 1` toggle slower or requires multiple clicks. Users complain new version is "clunky" compared to v1.0.
**Why it happens:** Replacing single-click toggle with multi-step workflow (click to open, adjust quantity, confirm). Adding confirmation dialogs. Moving toggle action inside a popover/modal.
**How to avoid:** Preserve existing toggle button location and behavior (line 380 in CardGrid.tsx). Keep it as primary action. Quantity controls are secondary/progressive disclosure. Test with stopwatch: `0 → 1` must remain < 1 second.
**Warning signs:** Users stop using the app after update. Click-through rates drop. Support requests about "how to add cards now."

### Pitfall 3: Off-By-One in Unique vs Total
**What goes wrong:** Completion percentage calculation uses total quantity instead of unique owned count. Adding a duplicate changes completion from 50% to 51% (incorrect).
**Why it happens:** Mixing `sum(quantities)` with `count(unique IDs)` in formula. Using wrong field from stats object. Copy-paste error in formula.
**How to avoid:** Explicit naming: `uniqueOwned` vs `totalQuantity`. Unit tests for edge case: add duplicate, assert completion unchanged. Code review checklist: "Does this formula use unique count?"
**Warning signs:** Completion percentage changes when adding duplicates. Percentage exceeds 100%. Negative missing count.

### Pitfall 4: Quantity Controls Not Stopping Propagation
**What goes wrong:** Clicking increment/decrement also triggers card detail modal open. User can't adjust quantity without opening detail view.
**Why it happens:** Event propagation from Button click to Card onClick. Missing `e.stopPropagation()` in handlers.
**How to avoid:** Always `e.stopPropagation()` in inline control handlers (see Pattern 1 example). Test: click increment, assert modal did NOT open.
**Warning signs:** Modal opens when adjusting quantity. Users can't increment without extra clicks.

### Pitfall 5: Mobile Hover State Issues
**What goes wrong:** Quantity controls hidden on mobile because desktop-only hover styles. Users can't adjust quantities on phone/tablet.
**Why it happens:** CSS classes like `group-hover:opacity-100` require hover support. Mobile touch doesn't trigger hover.
**How to avoid:** User constraint: controls always visible on mobile, hover-reveal on desktop. Use `@media (hover: hover)` query for desktop-only hover styles. Test on actual mobile device.
**Warning signs:** "Can't see quantity controls on phone" reports. Mobile usage drops after update.

## Code Examples

Verified patterns from existing codebase:

### CardGrid Hover Overlay Pattern (Existing)
```tsx
// Source: src/components/CardGrid.tsx line 371-396
<div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center z-10">
  <Button
    variant={isOwned ? "destructive" : "default"}
    size="sm"
    className="transform translate-y-4 opacity-0 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300"
    onClick={(e) => isOwned ? handleRemoveFromCollection(card, e) : handleAddToCollection(card, e)}
  >
    {isOwned ? <><Check className="h-4 w-4 mr-2" />Remove</> : <><Plus className="h-4 w-4 mr-2" />Add</>}
  </Button>
</div>
```
**Usage:** Extend this overlay to also include quantity controls (minus/badge/plus) positioned adjacent to toggle button.

### useCollection Quantity APIs (Phase 4)
```tsx
// Source: src/lib/collection.ts line 92-116
const incrementQuantity = useCallback((cardId: string): void => {
  setCollection(prev => {
    const current = prev.cardQuantities[cardId] || 0;
    if (current >= 999) return prev; // Max quantity
    return {
      ...prev,
      cardQuantities: { ...prev.cardQuantities, [cardId]: current + 1 }
    };
  });
}, []);

const decrementQuantity = useCallback((cardId: string): void => {
  setCollection(prev => {
    const current = prev.cardQuantities[cardId] || 0;
    if (current <= 0) return prev; // Floor at 0
    const newQty = current - 1;
    const newQuantities = { ...prev.cardQuantities };
    if (newQty === 0) {
      delete newQuantities[cardId]; // Sparse storage
    } else {
      newQuantities[cardId] = newQty;
    }
    return { ...prev, cardQuantities: newQuantities };
  });
}, []);
```
**Usage:** Already available from `useCollection()` hook. No changes needed, just consume in UI.

### Stats Computation Pattern (Existing)
```tsx
// Source: src/components/CardGrid.tsx line 93-99
const stats = useMemo(() => {
  const total = filteredCards.length;
  const owned = filteredCards.filter(card => isInCollection(card.id)).length;
  const missing = total - owned;
  const percentage = total > 0 ? (owned / total) * 100 : 0;
  return { owned, missing, total, percentage };
}, [filteredCards, isInCollection]);
```
**Modification:** Extend to also compute `totalQuantity` using `cardQuantities`:
```tsx
const totalQuantity = filteredCards.reduce((sum, card) => sum + (cardQuantities[card.id] ?? 0), 0);
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| Config file | `vitest.config.ts` (existing) |
| Quick run command | `npm test` |
| Full suite command | `npm test -- --run` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CTRL-01 | Increment quantity from album view | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "incrementQuantity"` | ✅ Existing (Phase 4) |
| CTRL-02 | Decrement with 0-floor validation | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "decrementQuantity"` | ✅ Existing (Phase 4) |
| CTRL-03 | Fast toggle `0 ↔ 1` preserved | integration | `npm test -- src/components/__tests__/CardGrid.test.tsx -t "toggle"` | ✅ Existing |
| CTRL-04 | Quantity badge display logic | unit | `npm test -- src/components/__tests__/QuantityBadge.test.tsx -t "badge"` | ❌ Wave 0 |
| STATQ-01 | Completion uses unique count, not total | unit | `npm test -- src/lib/__tests__/stats.test.ts -t "completion unique"` | ❌ Wave 0 |
| STATQ-02 | Separate unique/total metrics shown | integration | `npm test -- src/components/__tests__/CardGrid.test.tsx -t "footer stats"` | ❌ Wave 0 |
| STATQ-03 | Stats consistency across views | integration | `npm test -- src/components/__tests__/stats-consistency.test.tsx -t "cross-view"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `npm test -- src/lib/__tests__/collection.test.ts src/components/__tests__/CardGrid.test.tsx --run`
- **Per wave merge:** `npm test -- --run`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `src/components/__tests__/QuantityBadge.test.tsx` — covers CTRL-04 (badge display at qty=0, 1, >1)
- [ ] `src/lib/__tests__/stats.test.ts` — covers STATQ-01 (unique vs total computation)
- [ ] `src/components/__tests__/stats-consistency.test.tsx` — covers STATQ-03 (same data → same stats in all views)
- [ ] Extend `src/components/__tests__/CardGrid.test.tsx` — add STATQ-02 (footer shows both metrics)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Boolean ownership only (`ownedCards: Record<string, boolean>`) | Quantity-based with derived ownership (`cardQuantities: Record<string, number>`, owned = qty > 0) | Phase 4 (2025-01-21) | Stats must distinguish unique vs total; UI shows both metrics |
| Single "Add to Collection" button | Toggle + quantity controls hybrid | Phase 5 (this phase) | Fast toggle preserved, quantity controls progressive disclosure |
| Stats show only owned/total | Stats show owned (unique) + total quantity | Phase 5 (this phase) | Users understand collection volume vs completion progress |

**Deprecated/outdated:**
- `ownedCards` as primary data source: Now derived from `cardQuantities` (Phase 4). Do NOT modify `ownedCards` directly.
- `addToCollection` / `removeFromCollection` for quantity adjustment: Use `incrementQuantity` / `decrementQuantity` for duplicates. Use add/remove only for backward compatibility (they set qty=1 or qty=0).

## Open Questions

1. **Should quantity controls use tooltip labels for accessibility?**
   - What we know: Tooltips available via @radix-ui/react-tooltip (already in deps). Screen readers need ARIA labels.
   - What's unclear: Whether icon-only buttons (Minus/Plus) provide sufficient context without tooltip.
   - Recommendation: Add tooltips ("Decrease quantity" / "Increase quantity") for accessibility. Low implementation cost, high UX value.

2. **How should mobile always-visible controls affect layout density?**
   - What we know: User constraint specifies always-visible on mobile. Current CardGrid uses compact grid on mobile.
   - What's unclear: Whether inline controls reduce cards-per-row or require taller tiles.
   - Recommendation: Test with actual mobile viewport. Likely need to reduce grid density (`grid-cols-2` → `grid-cols-1` on small screens) or stack controls vertically.

3. **Should quantity badge have visual distinction at qty=1 vs qty>1?**
   - What we know: User constraint shows badge at qty=1 (not hidden). Research suggests users may want checkmark vs number distinction.
   - What's unclear: Whether qty=1 should show "1" badge or checkmark icon (like existing owned indicator).
   - Recommendation: Use checkmark at qty=1, number badge at qty>1. Matches existing owned visual (ring + checkmark), feels more natural.

## Sources

### Primary (HIGH confidence)
- **Existing codebase** — `src/components/CardGrid.tsx`, `src/components/SetGrid.tsx`, `src/lib/collection.ts` (Phase 4 APIs verified)
- **package.json** — shadcn/ui components, @radix-ui versions verified (2025-01-21)
- **Phase 4 CONTEXT.md and RESEARCH.md** — Quantity model semantics, sparse storage, API contracts
- **REQUIREMENTS.md** — CTRL-01 through STATQ-03 requirements verified
- **05-CONTEXT.md** — User constraints for UI behavior, toggle semantics, stats labels

### Secondary (MEDIUM confidence)
- **shadcn/ui documentation** — Button disabled prop, Badge variants, Tooltip composition patterns
- **React documentation** — useMemo for stats computation, useCallback for stable handlers, event.stopPropagation pattern
- **Radix UI documentation** — Tooltip ARIA labeling, Portal rendering for mobile compatibility

### Tertiary (LOW confidence)
- None. All findings backed by codebase analysis or official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All dependencies present, versions verified, no installation required
- Architecture: HIGH — Existing components analyzed, extension points identified, patterns established in v1.0
- Pitfalls: HIGH — Stats divergence and toggle UX risks validated against existing codebase structure and user constraints

**Research date:** 2025-01-21
**Valid until:** 2025-02-21 (30 days, stable stack and requirements)
