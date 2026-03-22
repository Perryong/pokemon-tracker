# Milestones

## v1.1 Quantity Tracking (Shipped: 2026-03-22)

**Phases completed:** 3 phases, 6 plans, 6 tasks

**Key accomplishments:**

- Migrated collection persistence from boolean ownership to quantity schema with backup/rollback safety and deterministic large-payload coverage.
- Added quantity controls and badges in album cards while preserving fast toggle behavior (`0 ↔ 1`) and enforcing `0..999` boundaries.
- Unified stats semantics across SetGrid, CardGrid, CollectionView, and CollectionStats (unique-owned vs total-quantity clarity).
- Stabilized Vitest matcher/runtime setup with `@testing-library/jest-dom` and expanded quantity regression coverage.
- Closed strict release evidence gate with green `npm run test` and `npm run build`.

### Known Gaps Accepted as Tech Debt

- Milestone was shipped without a formal `.planning/v1.1-MILESTONE-AUDIT.md` artifact (user-approved proceed-anyway).

---

## v1.0 Pokemon TCG Collection Tracker v1.0 (Shipped: 2026-03-21)

**Phases completed:** 4 phases, 9 plans, 8 tasks

**Key accomplishments:**

- (none recorded)

---
