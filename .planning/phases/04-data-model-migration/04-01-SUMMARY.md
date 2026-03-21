---
phase: 04-data-model-migration
plan: 01
subsystem: data-layer
tags: [migration, storage, types, backup, safety]
requires: []
provides: [collection-types, migration-logic, backup-system]
affects: [collection-state, persistence-layer]
tech_stack:
  added: []
  patterns: [sparse-storage, idempotent-migration, backup-rollback]
key_files:
  created:
    - src/lib/collection-types.ts
    - src/lib/migration.ts
    - src/lib/__tests__/collection-types.test.ts
    - src/lib/__tests__/migration.test.ts
  modified: []
decisions:
  - title: "Use version 3 for quantity schema"
    rationale: "Skip v2 to avoid confusion with existing storage key name 'pokemon-collection-v2'"
  - title: "Sparse storage pattern"
    rationale: "Omit zero-quantity entries to optimize localStorage usage and align with existing boolean pattern"
  - title: "In-place migration"
    rationale: "Reuse existing STORAGE_KEY for seamless upgrade, backup to separate key for safety"
metrics:
  duration_minutes: 5
  tasks_completed: 2
  files_created: 4
  lines_added: 665
  tests_added: 34
  test_coverage: "100% of migration paths"
  completed_date: "2026-03-21"
---

# Phase 04 Plan 01: Migration Infrastructure Summary

**Built:** Type-safe migration infrastructure for v1→v3 quantity schema with comprehensive backup/rollback safety.

## What Was Delivered

Created the foundational migration system that converts boolean ownership storage to quantity-based storage without data loss. This infrastructure provides:

1. **Schema Type Definitions** (`collection-types.ts`)
   - V1 interface: `{ version: 1, ownedCards: Record<string, boolean> }`
   - V3 interface: `{ version: 3, cardQuantities: Record<string, number> }`
   - Zod validator enforcing quantity constraints (0-999, integers only)
   - Storage key constants for main data and backup

2. **Migration Logic** (`migration.ts`)
   - Idempotent `migrateV1ToV3` function: true→1, false→omit (sparse)
   - Automatic backup before transformation
   - Rollback on validation failure
   - `getInitialState` with auto-detection and migration
   - Handles large datasets (tested with 5000+ cards)

3. **Comprehensive Test Coverage**
   - 34 tests across type validation and migration behavior
   - Normal cases: empty, single, multiple, mixed ownership
   - Edge cases: large datasets, corrupted data, quota errors, unknown versions
   - Error handling: backup failures, restore fallbacks
   - 100% coverage of migration code paths

## Requirements Satisfied

| Requirement | Status | Evidence |
|-------------|--------|----------|
| QTY-01: Safe migration with no data loss | ✅ Complete | Migration with backup/rollback, tested with 5000 cards |
| QTY-02: Sparse storage (only qty > 0) | ✅ Complete | False entries omitted, validated in tests |
| QTY-04: Backup/fallback behavior | ✅ Complete | createBackup, restoreFromBackup, clearBackup functions |
| TESTQ-01: Automated test coverage | ✅ Complete | 34 tests covering normal and edge cases |

## Deviations from Plan

None - plan executed exactly as written.

## Technical Decisions

### 1. Zod Schema Validation
**Decision:** Use `CollectionV3Schema.parse()` in migration, not just TypeScript types.

**Rationale:** Runtime validation catches edge cases (non-integer quantities, out-of-range values) that TypeScript can't prevent. Essential for migration safety when dealing with potentially corrupted localStorage data.

### 2. Sparse Storage Enforcement
**Decision:** Only persist cards with `quantity > 0`, omit zero-quantity entries.

**Rationale:** 
- Mirrors existing v1 behavior (false values omitted)
- Optimizes localStorage usage (typical collection has 100-500 owned cards out of 10,000+ total)
- Simplifies migration logic (true→1, false→omit)

### 3. Backup Key Strategy
**Decision:** Use `pokemon-collection-v2-backup` as deterministic backup key.

**Rationale:** Predictable key name enables debugging, recovery tools, and manual intervention. Separate from main key prevents conflicts during migration.

### 4. In-Memory Fallback
**Decision:** `convertToV3InMemory` helper for rollback scenarios.

**Rationale:** If backup restore fails, still provide valid v3 state to keep app usable. Last resort is empty collection with console warnings for debugging.

## Testing Highlights

**Large Dataset Test:** Successfully migrates 5000 cards in <100ms, validating performance for realistic collections.

**Edge Case Coverage:**
- Corrupted JSON → returns empty collection
- Unknown version → returns empty collection  
- Quota exceeded → keeps state in memory
- Backup failure → logs error but continues
- Mixed truthy/falsy → only migrates `true` values

**Mock Strategy:** Used `vi.spyOn(localStorage, 'setItem')` for error injection testing, ensuring backup failure paths are validated.

## File Manifest

### Created Files

**`src/lib/collection-types.ts` (742 bytes)**
- Exports: `CollectionStateV1`, `CollectionStateV3`, `CollectionState`, `CollectionV3Schema`, `STORAGE_KEY`, `BACKUP_KEY`
- Purpose: Type definitions and validation schemas
- Zero logic - types and constants only

**`src/lib/migration.ts` (4803 bytes)**
- Exports: `migrateV1ToV3`, `getInitialState`, `createBackup`, `restoreFromBackup`, `clearBackup`
- Purpose: Migration functions with backup/rollback
- Dependencies: `collection-types`, `zod`

**`src/lib/__tests__/collection-types.test.ts` (3827 bytes)**
- 14 tests for type validation and Zod schema
- Covers: constant values, interface usage, validation rules (range, integer, version)

**`src/lib/__tests__/migration.test.ts` (9314 bytes)**
- 20 tests for migration behavior
- Covers: normal cases, edge cases, error handling, large datasets

### Integration Points

**Ready for Plan 02:**
- `getInitialState()` can replace existing `getInitialState` in `collection.ts`
- `CollectionStateV3` provides target schema for hook refactor
- Migration is automatic and transparent to consumers

## Known Limitations

1. **Migration is one-way:** No v3→v1 downgrade path (intentional, matches project requirements)
2. **Backup lifecycle:** Manual cleanup required after successful migration (Plan 02 will handle)
3. **No progress indication:** Silent migration suitable for fast cases (<100ms), Plan 02 may add UX for slow cases

## Next Steps (Plan 02)

1. Integrate `getInitialState()` into `useCollection` hook
2. Update collection methods to use `cardQuantities` instead of `ownedCards`
3. Preserve compatibility APIs (`isOwned`, `toggleOwnership`) as quantity wrappers
4. Add migration cleanup logic (remove backup after successful app start)
5. Extend existing collection tests for v3 behavior and idempotency

## Self-Check: PASSED

**Files created:**
- ✅ `src/lib/collection-types.ts` exists
- ✅ `src/lib/migration.ts` exists
- ✅ `src/lib/__tests__/collection-types.test.ts` exists
- ✅ `src/lib/__tests__/migration.test.ts` exists

**Commits verified:**
- ✅ `cce8d94` - Task 1: collection schema types
- ✅ `d344011` - Task 2: migration with backup/rollback

**Tests passing:**
- ✅ All 34 tests pass (14 type tests + 20 migration tests)
- ✅ TypeScript compilation clean (`npx tsc --noEmit`)
- ✅ Large dataset test (5000 cards) completes in <100ms

**Requirements validated:**
- ✅ QTY-01: Migration safety verified by backup/restore tests
- ✅ QTY-02: Sparse storage verified by "omits false entries" test
- ✅ QTY-04: Backup behavior verified by backup function tests
- ✅ TESTQ-01: 34 tests provide comprehensive coverage
