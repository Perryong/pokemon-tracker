---
phase: 01
slug: data-foundation-persistence
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| **Config file** | none — Wave 0 installs/configures |
| **Quick run command** | `npm run test -- --run --reporter=verbose` |
| **Full suite command** | `npm run test -- --run --coverage` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm run test -- --run --reporter=verbose`
- **After every plan wave:** Run `npm run test -- --run --coverage`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DATA-01 | integration | `npm test -- src/lib/tcgdex.test.ts -t "fetch sets"` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DATA-02 | integration | `npm test -- src/lib/tcgdex.test.ts -t "fetch series"` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | DATA-03 | integration | `npm test -- src/lib/tcgdex.test.ts -t "fetch set details"` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | DATA-04 | unit | `npm test -- src/lib/tcgdex.test.ts -t "normalize card image"` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | PERS-01 | unit | `npm test -- src/lib/collection.test.ts -t "persist ownership"` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | PERS-02 | unit | `npm test -- src/lib/collection.test.ts -t "reload collection"` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | PERS-03 | unit | `npm test -- src/lib/collection.test.ts -t "completion stats"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `vitest.config.ts` — Vitest runtime/test environment config
- [ ] `src/lib/tcgdex.test.ts` — SDK adapter and normalization tests
- [ ] `src/lib/collection.test.ts` — localStorage persistence and completion math tests
- [ ] `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom` — framework install if missing

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| App persists owned toggles across browser restart | PERS-01, PERS-02 | Browser session lifecycle | Mark a card owned, reload page, close/reopen browser tab, verify owned state remains |
| Set-level completion stays accurate after reload | PERS-03 | Depends on combined API + persisted local state | Own/unown cards in one set, reload, verify completion percent and counts match expected values |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
