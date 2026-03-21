# Requirements: Pokemon TCG Collection Tracker

**Defined:** 2026-03-20
**Core Value:** Let me reliably track my Pokemon TCG collection progress by set, with fast card-level updates that persist between sessions.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Integration

- [x] **DATA-01**: App fetches all Pokemon TCG sets using TCGdex SDK `tcgdex.fetch('sets')`.
- [x] **DATA-02**: App fetches series metadata using TCGdex SDK `tcgdex.fetch('series')`.
- [x] **DATA-03**: App fetches selected set details and cards using TCGdex SDK `tcgdex.fetch('sets', setId)`.
- [x] **DATA-04**: App uses TCGdex card `image` data for card rendering in album view.

### Sets View

- [x] **SETS-01**: User can view all available Pokemon TCG sets with official logos.
- [x] **SETS-02**: User can filter sets by series using a dropdown (for example Sword & Shield, Scarlet & Violet).
- [x] **SETS-03**: User can search sets by name with live filtering as they type.
- [x] **SETS-04**: User sees per-set collection progress bars based on owned cards versus set total.
- [x] **SETS-05**: User sees a distinct completion indicator when a set reaches 100% ownership.

### Cards Album View

- [x] **ALBM-01**: User can open a selected set in a responsive card album grid.
- [x] **ALBM-02**: User sees real card images for all cards in the selected set.
- [x] **ALBM-03**: User can click a card to toggle ownership status.
- [x] **ALBM-04**: User sees a clear owned-state indicator (green checkmark) on owned cards.
- [x] **ALBM-05**: User can switch album card display between small and medium sizes.
- [x] **ALBM-06**: User can filter album cards by all, owned, or missing states.
- [x] **ALBM-07**: User can search cards by name within the selected set.

### Collection Stats and Persistence

- [x] **STAT-01**: User sees a fixed bottom footer with real-time owned count, missing count, and completion percentage.
- [x] **PERS-01**: Card ownership changes are automatically persisted to localStorage.
- [x] **PERS-02**: Persisted collection data reloads correctly on future browser sessions.
- [x] **PERS-03**: Set-level and album-level statistics remain consistent after reload.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Collection Features

- **ADV-01**: User can track card quantity (duplicates) rather than only boolean ownership.
- **ADV-02**: User can mark wishlist cards separately from owned cards.
- **ADV-03**: User can apply rarity-based filtering and sorting in set and album views.

### Data Portability and Insights

- **PORT-01**: User can export and import collection data through app UI.
- **PORT-02**: User can see expanded collection analytics beyond basic completion metrics.

## Release Hardening Requirements (Phase 02.1)

Post-feature stabilization requirements for release confidence. These validate and harden existing v1 behavior without adding new capabilities.

- [x] **HARD-01**: Vitest test infrastructure is operational and `npm test` executes successfully.
- [x] **HARD-02**: Collection persistence tests verify ownership survives reload/hydration flows.
- [x] **HARD-03**: Stats calculation tests verify owned/missing/completion percentage accuracy.
- [ ] **HARD-04**: Production build (`npm run build`) completes without errors.
- [ ] **HARD-05**: Release smoke checklist passes for critical v1 user journeys on production build.
- [ ] **HARD-06**: Non-critical findings are documented in a deferred backlog with severity/rationale.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| User authentication and cloud sync | v1 is personal-use and local-first |
| Social sharing, trading, marketplace flows | Not part of core collection tracking value |
| OCR/card scanning workflows | Adds significant complexity beyond v1 needs |
| Public profiles and multi-user collaboration | Personal app scope for first release |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| PERS-01 | Phase 1 | Complete |
| PERS-02 | Phase 1 | Complete |
| PERS-03 | Phase 1 | Complete |
| SETS-01 | Phase 2 | Complete |
| SETS-02 | Phase 2 | Complete |
| SETS-03 | Phase 2 | Complete |
| SETS-04 | Phase 2 | Complete |
| SETS-05 | Phase 2 | Complete |
| ALBM-01 | Phase 3 | Complete |
| ALBM-02 | Phase 3 | Complete |
| ALBM-03 | Phase 3 | Complete |
| ALBM-04 | Phase 3 | Complete |
| ALBM-05 | Phase 3 | Complete |
| ALBM-06 | Phase 3 | Complete |
| ALBM-07 | Phase 3 | Complete |
| STAT-01 | Phase 3 | Complete |
| HARD-01 | Phase 02.1 | Complete |
| HARD-02 | Phase 02.1 | Complete |
| HARD-03 | Phase 02.1 | Complete |
| HARD-04 | Phase 02.1 | Pending |
| HARD-05 | Phase 02.1 | Pending |
| HARD-06 | Phase 02.1 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓
- Completed: 23/26 (88%) (20 v1 + 3 hardening complete)

---
*Requirements defined: 2026-03-20*
*Last updated: 2026-03-21 - Phase 02.1 Plan 01 complete (test infrastructure)*
