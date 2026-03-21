# Roadmap: v1.1 Quantity Tracking

**Milestone:** v1.1 Quantity Tracking  
**Goal:** Add quantity-based collection tracking for duplicates while preserving fast local-first workflows  
**Created:** 2026-03-21  
**Phases:** 3  
**Granularity:** Coarse

## Phases

- [ ] **Phase 4: Data Model & Migration** - Convert boolean ownership to quantity storage with safe migration
- [ ] **Phase 5: Quantity UI & Statistics** - Add quantity controls and quantity-aware progress tracking
- [ ] **Phase 6: Testing & Validation** - Verify quantity features and preserve v1.0 behavior

## Phase Details

### Phase 4: Data Model & Migration

**Goal:** User's existing ownership data converts safely to quantity storage with no data loss

**Depends on:** Nothing (first phase of v1.1)

**Requirements:** QTY-01, QTY-02, QTY-03, QTY-04, TESTQ-01

**Success Criteria** (what must be TRUE):
1. User's existing v1.0 boolean ownership data migrates to quantity format without any cards lost
2. User can rely on localStorage staying efficient (only cards with qty > 0 stored)
3. User sees ownership and quantity as one unified concept (quantity > 0 = owned, no divergence)
4. User has backup/rollback available if migration fails
5. Developer can verify migration succeeded with automated tests on realistic datasets (5000+ cards)

**Plans:** 2 plans

Plans:
- [x] 04-01-PLAN.md — Core migration infrastructure (types, Zod schemas, backup/rollback) ✅ 2026-03-21
- [ ] 04-02-PLAN.md — Hook integration with compatibility wrappers and tests

---

### Phase 5: Quantity UI & Statistics

**Goal:** User can track duplicates via quantity controls and see accurate progress metrics

**Depends on:** Phase 4 (requires quantity data model)

**Requirements:** CTRL-01, CTRL-02, CTRL-03, CTRL-04, STATQ-01, STATQ-02, STATQ-03

**Success Criteria** (what must be TRUE):
1. User can increment card quantity from album view with clear visual feedback
2. User can decrement quantity and never goes below zero
3. User can still use single-click toggle for fast 0 ↔ 1 ownership changes (v1.0 speed preserved)
4. User sees quantity badges/indicators on cards with duplicates
5. User sees set completion based on unique cards owned (not total duplicate count)
6. User sees both unique-owned and total-quantity stats displayed separately and clearly labeled
7. User gets consistent stats across SetGrid, CardGrid, and collection summary after quantity updates

**Plans:** 2 plans

Plans:
- [ ] 05-01-PLAN.md — Stats helper + CardGrid quantity controls and enhanced footer
- [ ] 05-02-PLAN.md — SetGrid, CollectionView, CollectionStats quantity-aware updates

---

### Phase 6: Testing & Validation

**Goal:** Quantity features are verified and v1.0 behaviors remain intact

**Depends on:** Phase 5 (requires complete quantity implementation)

**Requirements:** TESTQ-01, TESTQ-02, TESTQ-03

**Success Criteria** (what must be TRUE):
1. Migration logic is covered by automated tests for normal and edge-case scenarios
2. Quantity controls are covered by automated tests (increment, decrement, zero-floor, toggle)
3. Existing v1.0 behaviors (set browsing, filters, persistence) pass regression tests after quantity changes
4. Developer can run test suite and see 100% pass rate before shipping v1.1

**Plans:** TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 4. Data Model & Migration | 1/2 | In progress | - |
| 5. Quantity UI & Statistics | 0/0 | Not started | - |
| 6. Testing & Validation | 0/0 | Not started | - |

**Next:** Continue Phase 4 with `/gsd-execute-phase 4` (plan 04-02) to integrate migration into collection hook.

---

*Roadmap created: 2026-03-21*  
*Last updated: 2026-03-21 (Plan 04-01 complete)*
