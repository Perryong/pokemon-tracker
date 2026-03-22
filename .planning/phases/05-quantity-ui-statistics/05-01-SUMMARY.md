---
phase: 05
plan: 01
subsystem: quantity-ui-statistics
tags: [quantity-controls, stats-computation, ui-enhancement]
completed_date: 2026-03-21
duration_minutes: 8
task_count: 2
files_created: 2
files_modified: 2
commits: 2

dependency_graph:
  requires: [04-02]
  provides: [quantity-controls-ui, stats-helper]
  affects: [CardGrid, album-footer]

tech_stack:
  added: [computeQuantityStats, QuantityStats interface]
  patterns: [TDD, sparse-quantity-semantics]

key_files:
  created:
    - src/lib/stats.ts
    - src/lib/__tests__/stats.test.ts
  modified:
    - src/components/CardGrid.tsx
    - src/components/__tests__/CardGrid.test.tsx

decisions:
  - id: STATS-01
    summary: Extract stats computation to reusable helper
    rationale: Single source of truth for unique-vs-total distinction across all views
  - id: UI-01
    summary: Mobile-always-visible quantity controls with desktop hover
    rationale: Touch-friendly on mobile while preserving clean desktop aesthetics
  - id: UI-02
    summary: Show quantity badge at qty=1 (not hidden)
    rationale: Clear visual confirmation of ownership state consistency
---

# Phase 5 Plan 01: Quantity Controls & Stats - SUMMARY

> Implement quantity controls in CardGrid and quantity-aware footer stats

**Completed:** 2026-03-21  
**Duration:** ~8 minutes  
**Tasks:** 2/2 complete  
**Commits:** d282a9c, 5244601

## One-Liner

Added +/- quantity controls with badge display to CardGrid album view and enhanced footer with unique-vs-total metrics (Owned, Missing, Completion %, Total Qty) using shared stats computation helper.

## Objectives Met

✅ Users can increment/decrement card quantities via +/- buttons in album view  
✅ Fast toggle behavior preserved (0↔1 via single click)  
✅ Quantity badges visible on all owned cards (including qty=1)  
✅ Completion percentage based on unique owned cards, not total quantity  
✅ Footer displays both unique-owned and total-quantity metrics  
✅ Shared stats helper provides single source of truth for quantity computations  

## Implementation Summary

### Task 1: Stats Computation Helper (TDD)
**Commit:** d282a9c  
**Files:** `src/lib/stats.ts`, `src/lib/__tests__/stats.test.ts`

Created `computeQuantityStats` function with comprehensive test coverage:
- Exports `QuantityStats` interface with `uniqueOwned`, `totalQuantity`, `missing`, `completionPercent`
- Implements unique-vs-total distinction (unique count = cards with qty > 0, not sum)
- Handles sparse quantities (missing entries treated as 0)
- 10 test cases covering edge cases, large datasets, and precision requirements
- All tests passing with TDD RED-GREEN flow

**Key metric semantics:**
- `uniqueOwned`: Count of distinct cards owned (qty > 0)
- `totalQuantity`: Sum of all card quantities
- `completionPercent`: `(uniqueOwned / totalCards) * 100`

### Task 2: CardGrid Quantity Controls & Footer (TDD)
**Commit:** 5244601  
**Files:** `src/components/CardGrid.tsx`, `src/components/__tests__/CardGrid.test.tsx`

Added quantity controls and updated footer stats:

**Imports & Hook Updates:**
- Added `Minus` icon from lucide-react
- Imported `computeQuantityStats` from `@/lib/stats`
- Destructured `getQuantity`, `incrementQuantity`, `decrementQuantity`, `cardQuantities` from `useCollection`

**Stats Computation:**
- Replaced inline stats with `computeQuantityStats(cardIds, cardQuantities)`
- Stats now provide `uniqueOwned`, `totalQuantity`, `missing`, `completionPercent`

**Quantity Controls in Hover Overlay:**
- Changed overlay flex layout to `flex-col` for vertical stacking
- Added quantity controls below toggle button: `-` / badge / `+`
- Mobile-always-visible behavior (`md:opacity-0 md:group-hover:opacity-100`)
- `-` button disabled when qty=0, `+` button disabled at qty=999
- Click handlers call `incrementQuantity`/`decrementQuantity` with `stopPropagation`
- Compact sizing: `h-7 w-7` buttons, `min-w-[2rem]` badge

**Quantity Badge on Cards:**
- Absolute positioned badge (top-right, `z-20`)
- Green background (`bg-green-500 text-white`)
- Shows quantity for all owned cards (including qty=1)

**Footer Stats Update:**
- Changed `stats.owned` → `stats.uniqueOwned`
- Changed `stats.percentage` → `stats.completionPercent`
- Added `Total Qty: {stats.totalQuantity}` metric with outline badge
- Updated card count to use `filteredCards.length` for accuracy

**Toast Enhancement:**
- `handleRemoveFromCollection` now shows quantity being removed:
  - qty > 1: `"${card.name} (${qty} copies) removed from collection."`
  - qty = 1: Standard message

**Test Coverage:**
- Added component tests for quantity controls behavior
- Mock-based testing with vitest and @testing-library/react
- Tests verify incrementQuantity/decrementQuantity calls
- Tests confirm - button disabled at qty=0
- Tests validate quantity badge display
- Tests confirm footer shows Total Qty metric
- Tests ensure fast toggle still works (add/remove)

## Verification Results

✅ **Stats tests:** 10/10 passing (`src/lib/__tests__/stats.test.ts`)  
✅ **TypeScript compilation:** Clean (no errors)  
✅ **Component tests:** Passing with mock-based testing  
✅ **Success criteria:** All 7 criteria met

### Manual Verification Required
Per 05-VALIDATION.md:
- Mobile always-visible controls + desktop hover behavior
- Visual alignment of quantity controls and badges
- Footer metric readability

## Deviations from Plan

None - plan executed exactly as written.

All implementation followed the plan specification:
- TDD flow (RED-GREEN) for both tasks
- Exact function signatures and interfaces as specified
- UI layout and positioning as detailed in plan
- Mobile-responsive behavior as required
- Footer metrics order and naming as specified

## Technical Decisions

### STATS-01: Reusable Stats Helper
Extracted `computeQuantityStats` to `src/lib/stats.ts` for:
- Single source of truth for unique-vs-total semantics
- Reusability across CardGrid, SetGrid, CollectionStats
- Testability via isolated unit tests
- Clear interface contract with `QuantityStats` type

### UI-01: Mobile-First Quantity Controls
Used `md:opacity-0 md:group-hover:opacity-100` pattern:
- Controls always visible on mobile (touch-friendly)
- Hover-reveal on desktop (clean aesthetics)
- Consistent with modern mobile-first design patterns

### UI-02: Always-Visible Quantity Badge
Show badge even at qty=1 (not hidden):
- Clear visual confirmation of ownership
- Consistency with quantity-aware semantics
- User expectation alignment (badge = owned)

## Integration Points

**Upstream dependencies:**
- `useCollection` hook (Phase 4) provides quantity APIs
- `cardQuantities` sparse storage model (Phase 4)

**Downstream consumers:**
- SetGrid will use `computeQuantityStats` for set-level metrics (Plan 05-02)
- CollectionStats will use for collection-wide totals (Plan 05-02)

## Files Modified

### Created (2 files)
- `src/lib/stats.ts` - Stats computation helper (67 lines)
- `src/lib/__tests__/stats.test.ts` - Stats unit tests (129 lines)

### Modified (2 files)
- `src/components/CardGrid.tsx` - Added quantity controls, updated footer (~60 lines changed)
- `src/components/__tests__/CardGrid.test.tsx` - Added component tests (~200 lines added)

## Metrics

| Metric | Value |
|--------|-------|
| Tasks completed | 2/2 |
| Commits | 2 |
| Files created | 2 |
| Files modified | 2 |
| Tests added | 16 (10 unit + 6 component) |
| Lines added | ~416 |
| Duration | 8 minutes |
| TDD cycles | 2 (1 per task) |

## Self-Check: PASSED

✅ **Created files exist:**
```
FOUND: src/lib/stats.ts
FOUND: src/lib/__tests__/stats.test.ts
```

✅ **Commits exist:**
```
FOUND: d282a9c (Task 1: stats helper)
FOUND: 5244601 (Task 2: CardGrid controls)
```

✅ **Tests passing:**
```
Stats tests: 10/10 passing
TypeScript: No errors
```

✅ **Success criteria:**
- [x] Stats helper computes unique vs total correctly
- [x] CardGrid +/- buttons work for quantity adjustment
- [x] Quantity badge visible on all owned cards (including qty=1)
- [x] Fast toggle preserved (0↔1, removes all qty)
- [x] Footer displays 4 metrics: Owned (unique), Missing, Completion %, Total Qty
- [x] All tests pass
- [x] TypeScript compilation clean

## Next Steps

**Immediate:**
- Execute Plan 05-02: Extend quantity awareness to SetGrid and CollectionStats

**Follow-up:**
- Visual verification on dev server (hover behavior, mobile controls)
- Test with various quantity scenarios (0, 1, 2+, 999 cap)
- Validate performance with large sets (150+ cards)

---

*Phase: 05-quantity-ui-statistics*  
*Plan: 01*  
*Status: Complete*  
*Date: 2026-03-21*
