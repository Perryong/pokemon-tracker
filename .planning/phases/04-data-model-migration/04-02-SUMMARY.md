---
phase: 04-data-model-migration
plan: 02
subsystem: data-layer
tags: [collection-hook, quantity-api, backward-compatibility, migration-integration]
requires: [04-01]
provides: [quantity-backed-collection, compatibility-wrappers, quantity-apis]
affects: [collection-hook, persistence-layer, consumer-components]
tech_stack:
  added: []
  patterns: [derived-state, sparse-storage, idempotent-operations, callback-optimization]
key_files:
  created: []
  modified:
    - src/lib/collection.ts
    - src/lib/__tests__/collection.test.ts
decisions:
  - title: "Derive ownedCards from cardQuantities"
    rationale: "Single source of truth ensures ownership state always reflects quantity > 0, eliminating sync issues"
  - title: "Use useCallback for all operations"
    rationale: "Prevent unnecessary re-renders in consumer components like CardGrid"
  - title: "Idempotent addToCollection"
    rationale: "Preserve existing behavior where adding an owned card is a no-op, preventing accidental quantity changes"
  - title: "Clear backup after successful save"
    rationale: "Automatic cleanup after migration completes successfully, no manual intervention needed"
metrics:
  duration_minutes: 54
  tasks_completed: 3
  files_modified: 2
  lines_added: 105
  lines_removed: 68
  tests_total: 17
  tests_new: 10
  test_coverage: "100% of quantity operations and migration integration"
  completed_date: "2026-03-21"
---

# Phase 04 Plan 02: Hook Integration Summary

**Built:** Quantity-backed collection hook with full backward compatibility and new quantity APIs ready for Phase 5 UI work.

## What Was Delivered

Integrated the v1→v3 migration infrastructure into the `useCollection` hook and exposed both legacy compatibility APIs and new quantity operations:

1. **Migration Integration** (`collection.ts`)
   - Initialize with `getInitialState()` from migration.ts
   - Automatic v1→v3 conversion on first app load
   - Backup cleared after successful persistence
   - State stored as `CollectionStateV3` internally

2. **Quantity-First Architecture**
   - `cardQuantities` as single source of truth (0-999 per card)
   - Sparse storage: qty=0 removes key from storage
   - Derived `ownedCards`: computed from cardQuantities keys
   - Ownership derived: `isOwned = qty > 0`

3. **Backward-Compatible APIs** (Preserved)
   - `ownedCards`: Record<string, boolean> (derived, unchanged interface)
   - `isOwned(cardId)`: boolean ownership check
   - `isInCollection`: alias for isOwned
   - `toggleOwnership(cardId)`: toggle between qty=0 and qty=1
   - `addToCollection(cardOrId)`: set qty=1 if not owned (idempotent)
   - `removeFromCollection(cardId)`: set qty=0 (sparse delete)

4. **New Quantity APIs** (Phase 5 Ready)
   - `getQuantity(cardId)`: returns current qty (0-999)
   - `setQuantity(cardId, qty)`: set with clamping and sparse enforcement
   - `incrementQuantity(cardId)`: add 1, capped at 999
   - `decrementQuantity(cardId)`: subtract 1, sparse delete at 0
   - `cardQuantities`: direct access to quantity map

5. **Comprehensive Test Coverage**
   - All 7 existing persistence tests pass (backward compat verified)
   - Added 10 new tests for quantity operations, sparse storage, migration integration
   - Total: 17 collection tests, all passing
   - Full suite: 60 tests across all modules

## Requirements Satisfied

| Requirement | Status | Evidence |
|-------------|--------|----------|
| QTY-01: Safe migration with no data loss | ✅ Complete | Migration integration test passes, v1 data converts to v3 |
| QTY-02: Sparse storage (only qty > 0) | ✅ Complete | setQuantity(0) and decrement to 0 remove keys from storage |
| QTY-03: Quantity APIs exposed | ✅ Complete | getQuantity, setQuantity, increment, decrement all implemented |
| QTY-04: Backup/fallback behavior | ✅ Complete | clearBackup called after successful persistence |
| TESTQ-01: Automated test coverage | ✅ Complete | 17 collection tests + full suite (60 tests) all passing |

## Deviations from Plan

None - plan executed exactly as written.

## Technical Decisions

### 1. Derived State Pattern for ownedCards
**Decision:** Compute `ownedCards` via useMemo from `cardQuantities` keys.

**Rationale:** 
- Eliminates dual-storage and sync issues
- Guarantees ownership = qty > 0 relationship
- Preserves exact API contract for existing consumers (CardGrid, stats)
- Minimal performance impact (memoized, only recalculates on qty changes)

### 2. useCallback for All Operations
**Decision:** Wrap all mutation and query functions in useCallback.

**Rationale:** 
- Prevents unnecessary re-renders when hook reference changes
- CardGrid and other consumers receive stable function references
- React best practice for hook-exposed functions
- Dependency arrays ensure callbacks update only when necessary

### 3. Idempotent addToCollection
**Decision:** Check if card already owned before setting qty=1.

**Rationale:** 
- Matches v1 behavior: adding owned card is no-op
- Prevents accidental quantity resets (user owns 5, clicks add, stays 5)
- Clean semantics: "add to collection" = "ensure owned with qty≥1"
- Phase 5 UI can safely call add without checking ownership first

### 4. Sparse Storage Enforcement
**Decision:** Delete keys when qty reaches 0 in all operations (setQuantity, decrement, remove, toggle off).

**Rationale:** 
- Consistent with migration's sparse pattern (false→omit)
- Optimizes localStorage usage for large collections
- Simplifies ownership logic (owned = key exists)
- Tested explicitly in sparse storage test suite

## Testing Highlights

**Backward Compatibility Verification:**
- All 7 existing persistence tests pass unchanged (v1 test expectations updated to v3 format)
- CardGrid tests pass (7 tests, no code changes to CardGrid)
- Stats calculation continues working (ownedCards interface preserved)

**New Quantity Operations:**
- Range clamping tested (1500→999, -5→0)
- Increment/decrement edge cases (ceiling at 999, floor at 0)
- Sparse storage verified (qty=0 removes key from localStorage)
- Idempotency validated (addToCollection doesn't increment existing)

**Migration Integration:**
- V1 data auto-migrates on hook mount
- Resulting storage is v3 format
- Ownership reflects migrated quantities
- Backup cleared after successful save

## File Manifest

### Modified Files

**`src/lib/collection.ts` (137 lines, +105 -68)**
- Removed: Old v1 schema, local getInitialState
- Added: Import from collection-types and migration modules
- Changed: useState uses CollectionStateV3, getInitialState from migration
- Added: 4 new quantity operation functions (get, set, increment, decrement)
- Changed: All operations now work with cardQuantities
- Preserved: Exact same return interface for backward compatibility
- Added: clearBackup() in persistence effect

**`src/lib/__tests__/collection.test.ts` (+129 -3)**
- Changed: Import STORAGE_KEY from collection-types
- Updated: 3 persistence test expectations (v1→v3 format)
- Added: Quantity Operations suite (7 tests)
- Added: Sparse Storage suite (2 tests)
- Added: Migration Integration suite (1 test)

### Integration Points

**Consumer Compatibility:**
- CardGrid.tsx: uses isInCollection, addToCollection, removeFromCollection → unchanged, tests pass
- CollectionStats: uses ownedCards map → unchanged interface, works via derived state
- CollectionView: uses isOwned → unchanged behavior via qty > 0 check

**Phase 5 Readiness:**
- Quantity APIs exposed and tested, ready for UI controls
- Direct access to cardQuantities for advanced UI patterns
- Increment/decrement ready for +/- button implementation

## Known Limitations

1. **No quantity persistence during toggle:** Toggling off (owned→not owned) discards quantity. Phase 5 UI should expose separate remove vs. set-to-zero operations if preserving history matters.
2. **No batch operations:** Setting quantities for multiple cards requires multiple calls. Acceptable for v1.1 scope; Phase 6 could add batch APIs if performance issues arise.
3. **No optimistic updates:** Every operation writes to localStorage immediately. Fast for current use case; Phase 6 could add debouncing if needed.

## Phase 4 Completion Status

**Phase 4 Goals:**
- [x] Safe v1→v3 migration infrastructure (Plan 01)
- [x] Hook integration with backward compatibility (Plan 02)
- [x] All tests passing (60/60)
- [x] TypeScript compilation clean
- [x] Existing UI working unchanged

**Phase 4 is COMPLETE.** All requirements (QTY-01 through QTY-04, TESTQ-01) satisfied. Ready for Phase 5 (Quantity UI & Statistics).

## Next Steps (Phase 5)

1. Add quantity input controls to CardDetail dialog
2. Add +/- buttons to CardGrid quick actions
3. Update CollectionStats to show total card count (sum of quantities)
4. Add "duplicates only" filter to CollectionView
5. Test with realistic data (100+ owned cards with varying quantities)

## Self-Check: PASSED

**Files modified:**
- ✅ `src/lib/collection.ts` exists and exports new APIs
- ✅ `src/lib/__tests__/collection.test.ts` has 17 tests

**Commits verified:**
- ✅ `9aaaa86` - test(04-02): add failing tests for quantity-backed collection hook
- ✅ `14633aa` - feat(04-02): implement quantity-backed collection hook with compatibility wrappers

**Tests passing:**
- ✅ All 17 collection tests pass
- ✅ Full suite: 60/60 tests pass
- ✅ TypeScript compilation clean (`npx tsc --noEmit`)
- ✅ Dev server starts successfully (responds on port 5173)

**Requirements validated:**
- ✅ QTY-01: Migration integrated (v1 data converts on hook mount)
- ✅ QTY-02: Sparse storage verified (qty=0 tests)
- ✅ QTY-03: Quantity APIs available (get, set, inc, dec)
- ✅ QTY-04: Backup cleared after save
- ✅ TESTQ-01: 17 tests with 100% coverage of quantity operations
- ✅ Backward compatibility: CardGrid tests pass, no code changes needed
