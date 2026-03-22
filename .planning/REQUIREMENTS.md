# Requirements: Pokemon TCG Collection Tracker

**Defined:** 2026-03-21
**Core Value:** Let me reliably track my Pokemon TCG collection progress by set, with fast card-level updates that persist between sessions.

## v1.1 Requirements

Requirements for this milestone (quantity tracking). Each maps to roadmap phases.

### Data Model & Migration

- [x] **QTY-01**: User's existing ownership data migrates safely from boolean storage to quantity storage with no data loss. ✅ 04-01
- [x] **QTY-02**: App stores collection quantities sparsely (only cards with quantity > 0) to keep localStorage usage efficient. ✅ 04-01
- [x] **QTY-03**: App derives owned-state from quantity (`quantity > 0`) so ownership and quantity cannot diverge.
- [x] **QTY-04**: User can rely on migration fallback/backup behavior if quantity migration fails. ✅ 04-01

### Quantity Controls

- [x] **CTRL-01**: User can increment a card quantity from the album view. ✅ 05-01
- [x] **CTRL-02**: User can decrement a card quantity and never go below zero. ✅ 05-01
- [x] **CTRL-03**: User can still use single-click card toggle for fast `0 ↔ 1` ownership changes. ✅ 05-01
- [x] **CTRL-04**: User sees clear quantity badges/indicators for cards with duplicates. ✅ 05-01

### Statistics & Progress Semantics

- [x] **STATQ-01**: User sees set completion based on unique owned cards, not total duplicate count. ✅ 05-01
- [x] **STATQ-02**: User sees separate unique-owned and total-quantity metrics where stats are shown. ✅ 05-02
- [x] **STATQ-03**: User gets consistent stats across SetGrid, CardGrid, and collection summary views after quantity updates. ✅ 05-02

### Validation & Regression

- [x] **TESTQ-01**: Quantity migration logic is covered by automated tests for normal and edge-case payloads. ✅ 04-01
- [x] **TESTQ-02**: Quantity controls are covered by automated tests (increment, decrement, 0-floor, fast toggle behavior).
- [x] **TESTQ-03**: Existing v1.0 core behaviors (set browsing, filters, persistence) remain verified after quantity changes.

## Future Requirements (Deferred)

### Enhanced Quantity UX

- **QUX-01**: User can type quantity directly via manual numeric input.
- **QUX-02**: User can use keyboard shortcuts for quantity adjustments.
- **QUX-03**: User can filter album cards by duplicates-only (`quantity > 1`).
- **QUX-04**: User can run set-level batch quantity reset/recount flows.

### Advanced Collection Scope

- **ADVQ-01**: User can track trade inventory separately from owned quantity.
- **ADVQ-02**: User can track card condition distribution per quantity.
- **ADVQ-03**: User can track price/value by quantity holdings.

## Out of Scope

Explicitly excluded for v1.1 milestone to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Cloud sync or multi-device quantity sync | Maintains local-first architecture and avoids backend expansion in v1.1 |
| Marketplace/trading workflows | Not required to deliver duplicate tracking core value |
| OCR/scanner-driven quantity auto-increment | High complexity and outside current milestone focus |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| QTY-01 | Phase 4 | ✅ Complete (04-01) |
| QTY-02 | Phase 4 | ✅ Complete (04-01) |
| QTY-03 | Phase 4 | In progress (04-02) |
| QTY-04 | Phase 4 | ✅ Complete (04-01) |
| CTRL-01 | Phase 5 | Pending |
| CTRL-02 | Phase 5 | Pending |
| CTRL-03 | Phase 5 | Pending |
| CTRL-04 | Phase 5 | Pending |
| STATQ-01 | Phase 5 | Pending |
| STATQ-02 | Phase 5 | Pending |
| STATQ-03 | Phase 5 | Pending |
| TESTQ-01 | Phase 4/6 | ✅ Complete (04-01) |
| TESTQ-02 | Phase 6 | Complete |
| TESTQ-03 | Phase 6 | Complete |

**Coverage:**
- v1.1 requirements: 14 total
- Mapped to phases: 14 ✓
- Complete: 4 (QTY-01, QTY-02, QTY-04, TESTQ-01)
- In progress: 1 (QTY-03)
- Pending: 9

---
*Requirements defined: 2026-03-21*
*Last updated: 2026-03-21 (Plan 04-01 complete)*
