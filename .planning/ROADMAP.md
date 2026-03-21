# Roadmap: Pokemon TCG Collection Tracker

**Project**: Pokemon TCG Collection Tracker  
**Core Value**: Let me reliably track my Pokemon TCG collection progress by set, with fast card-level updates that persist between sessions.  
**Version**: v1  
**Granularity**: Coarse  
**Created**: 2026-03-20  
**Last Updated**: 2026-03-21

## Phases

- [x] **Phase 1: Data Foundation & Persistence** - Integrate TCGdex SDK and build reliable localStorage-backed collection storage
- [x] **Phase 2: Sets View & Navigation** - Build sets browsing interface with filtering, search, and progress tracking
- [x] **Phase 3: Cards Album & Ownership Tracking** - Implement card-level ownership tracking with filters and real-time stats
- [x] **Phase 02.1: Release Hardening** - Validate production readiness with automated tests and comprehensive smoke testing

## Phase Details

### Phase 1: Data Foundation & Persistence
**Goal**: App can load TCG data from TCGdex SDK and persist collection state reliably between sessions

**Depends on**: Nothing (foundation phase)

**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, PERS-01, PERS-02, PERS-03

**Success Criteria** (what must be TRUE):
  1. User's browser successfully fetches all Pokemon TCG sets, series metadata, and set details with cards from TCGdex SDK
  2. User can toggle card ownership and see the change persist after closing and reopening the browser
  3. User can reload the app at any time without losing collection progress or statistics
  4. App stores only card IDs (not full objects) in localStorage to prevent quota issues with large collections
  5. User sees accurate set-level completion percentages that reflect actual owned cards in their collection

**Plans**: 4 plans (3 waves)

Plans:
- [x] 01-01-PLAN.md — TCGdex SDK adapter layer with type normalization
- [x] 01-02-PLAN.md — Collection persistence refactor with completion stats
- [x] 01-03-PLAN.md — Hook migration and component integration
- [x] 01-04-PLAN.md — Surface persisted set completion percentages in SetGrid

---

### Phase 2: Sets View & Navigation
**Goal**: User can browse, filter, and track progress across all Pokemon TCG sets

**Depends on**: Phase 1 (needs TCGdex data and collection calculations)

**Requirements**: SETS-01, SETS-02, SETS-03, SETS-04, SETS-05

**Success Criteria** (what must be TRUE):
  1. User can view all available Pokemon TCG sets with official set logos displayed
  2. User can filter the sets list by series (e.g., Sword & Shield, Scarlet & Violet) using a dropdown
  3. User can search sets by name and see results update live as they type
  4. User sees accurate progress bars for each set showing owned cards versus total cards
  5. User can identify completed sets at a glance with a distinct 100% completion indicator
  6. User can click a set to navigate to the Cards Album View

**Plans**: 1 plan (1 wave)

Plans:
- [x] 02-01-PLAN.md — Series filter, live search, and completion badge enhancements

---

### Phase 02.1: Release Hardening (INSERTED)

**Goal:** Harden existing v1 functionality by validating critical user flows, establishing automated regression tests, and ensuring production build readiness

**Depends on:** Phase 2

**Requirements**: HARD-01, HARD-02, HARD-03, HARD-04, HARD-05, HARD-06

**Success Criteria** (what must be TRUE):
  1. Vitest test infrastructure operational with `npm test` command
  2. Collection persistence tests verify ownership survives reload
  3. Stats calculation tests verify owned/missing/percentage accuracy
  4. Production build (`npm run build`) completes without errors
  5. All 27 smoke checklist items pass against production build
  6. Any non-critical issues documented in deferred backlog

**Plans:** 2 plans (2 waves)

Plans:
- [x] 02.1-01-PLAN.md — Test infrastructure + critical regression tests (HARD-01, HARD-02, HARD-03)
- [ ] 02.1-02-PLAN.md — Production build + smoke checklist + release gate (HARD-04, HARD-05, HARD-06)

### Phase 3: Cards Album & Ownership Tracking
**Goal**: User can view and track ownership of individual cards within selected sets with real-time feedback

**Depends on**: Phase 1 (persistence), Phase 2 (navigation from Sets View)

**Requirements**: ALBM-01, ALBM-02, ALBM-03, ALBM-04, ALBM-05, ALBM-06, ALBM-07, STAT-01

**Success Criteria** (what must be TRUE):
  1. User can open any set and see all cards displayed in a responsive grid with real card images
  2. User can click any card to toggle ownership status with immediate visual feedback
  3. User sees a clear owned-state indicator (green checkmark) on all owned cards
  4. User can switch card display size between small and medium views to suit their preference
  5. User can filter cards by "all", "owned", or "missing" states and see only matching cards
  6. User can search for specific cards by name within the current set
  7. User sees a fixed bottom stats footer that updates in real time showing owned count, missing count, and completion percentage

**Plans**: 2 plans (2 waves)

Plans:
- [x] 03-01-PLAN.md — Album controls: size toggle, ownership filter, name search (ALBM-05, ALBM-06, ALBM-07)
- [x] 03-02-PLAN.md — Fixed stats footer with real-time updates + verification (ALBM-01..04, STAT-01)

---

### Phase 02.1: Release Hardening
**Goal**: Validate production readiness with comprehensive testing and quality assurance

**Depends on**: Phases 1, 2, 3 (validates all delivered functionality)

**Requirements**: HARD-01, HARD-02, HARD-03, HARD-04, HARD-05, HARD-06

**Success Criteria** (what must be TRUE):
  1. Automated test suite covers core persistence and stats calculation logic
  2. Production build completes without errors or warnings
  3. All critical user flows validated via smoke testing
  4. Zero release-blocking defects remain
  5. Non-critical issues documented for follow-up

**Plans**: 2 plans (2 waves)

Plans:
- [x] 02.1-01-PLAN.md — Vitest test infrastructure with persistence and stats regression tests
- [x] 02.1-02-PLAN.md — Production build validation and comprehensive smoke testing

---

## Progress Tracking

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation & Persistence | 4/4 | Complete | 2026-03-21 |
| 2. Sets View & Navigation | 1/1 | Complete | 2026-03-21 |
| 3. Cards Album & Ownership Tracking | 2/2 | Complete | 2026-03-21 |
| 02.1. Release Hardening | 2/2 | Complete | 2026-03-21 |

**Overall Progress**: 9/9 plans complete (100%) ✅

---

## Requirement Coverage

All v1 requirements mapped to phases:

| Requirement | Phase | Category |
|-------------|-------|----------|
| DATA-01 | Phase 1 | Data Integration |
| DATA-02 | Phase 1 | Data Integration |
| DATA-03 | Phase 1 | Data Integration |
| DATA-04 | Phase 1 | Data Integration |
| PERS-01 | Phase 1 | Persistence |
| PERS-02 | Phase 1 | Persistence |
| PERS-03 | Phase 1 | Persistence |
| SETS-01 | Phase 2 | Sets View |
| SETS-02 | Phase 2 | Sets View |
| SETS-03 | Phase 2 | Sets View |
| SETS-04 | Phase 2 | Sets View |
| SETS-05 | Phase 2 | Sets View |
| ALBM-01 | Phase 3 | Cards Album |
| ALBM-02 | Phase 3 | Cards Album |
| ALBM-03 | Phase 3 | Cards Album |
| ALBM-04 | Phase 3 | Cards Album |
| ALBM-05 | Phase 3 | Cards Album |
| ALBM-06 | Phase 3 | Cards Album |
| ALBM-07 | Phase 3 | Cards Album |
| STAT-01 | Phase 3 | Stats |
| HARD-01 | Phase 02.1 | Testing |
| HARD-02 | Phase 02.1 | Testing |
| HARD-03 | Phase 02.1 | Testing |
| HARD-04 | Phase 02.1 | Build |
| HARD-05 | Phase 02.1 | Quality |
| HARD-06 | Phase 02.1 | Documentation |

**Coverage**: 26/26 requirements mapped (100%) ✅
- 20 v1 feature requirements ✅
- 6 hardening requirements ✅

---

## Critical Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Combined Data + Persistence in Phase 1 | Can't validate persistence patterns without real data layer; localStorage strategy depends on TCGdex data structure | Foundation must be correct before UI work begins |
| Stats footer in Phase 3 (not Phase 1) | Real-time stats only make sense in context of album view where user is actively tracking | Defers implementation until user workflow is established |
| 3 phases (not 4-5 from research) | Coarse granularity + brownfield codebase (foundation exists); research suggested 4-5 for greenfield | Compressed structure reflects existing React/shadcn foundation |
| No separate Polish phase | Core features include polish requirements (responsive grid, lazy loading exists, performance acceptable for v1 scale) | Polish is built-in, not bolted-on |

---

## Research Flags

**Critical pitfalls addressed in phase planning:**

- **Phase 1**: Card identity (use card.id as primary key), localStorage size explosion (store IDs only), data loss prevention (export functionality)
- **Phase 2**: Set completion false positives (handle base vs master set), API caching strategy with TTL
- **Phase 3**: Image loading performance (lazy loading + consider virtual scrolling), stale data handling, API rate limiting

**Phases needing deeper research during planning:**
- **Phase 3**: Virtual scrolling implementation for sets with 200+ cards (research flag from SUMMARY.md)

---

*Roadmap created: 2026-03-20*  
*Last updated: 2026-03-21*  
*Status: All phases complete - v1 requirements fulfilled (20/20) ✅*
