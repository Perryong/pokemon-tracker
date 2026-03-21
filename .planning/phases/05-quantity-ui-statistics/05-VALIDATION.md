---
phase: 05
slug: quantity-ui-statistics
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-21
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest 4.x + @testing-library/react |
| **Config file** | `vitest.config.ts` |
| **Quick run command** | `npm test -- --run src/components/__tests__/CardGrid.test.tsx src/lib/__tests__/stats.test.ts` |
| **Full suite command** | `npm test -- --run` |
| **Estimated runtime** | ~10-30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm test -- --run src/components/__tests__/CardGrid.test.tsx src/lib/__tests__/stats.test.ts`
- **After every plan wave:** Run `npm test -- --run`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | STATQ-01,STATQ-02 | unit | `npm test -- --run src/lib/__tests__/stats.test.ts` | ✅ | ⬜ pending |
| 05-01-02 | 01 | 1 | CTRL-01,CTRL-02,CTRL-03,CTRL-04,STATQ-01,STATQ-02 | component/integration | `npm test -- --run src/components/__tests__/CardGrid.test.tsx` | ✅ | ⬜ pending |
| 05-02-01 | 02 | 1 | STATQ-02,STATQ-03 | unit/type | `npm test -- --run src/lib/__tests__/stats.test.ts && npx tsc --noEmit` | ✅ | ⬜ pending |
| 05-02-02 | 02 | 1 | STATQ-02,STATQ-03 | type/smoke | `npx tsc --noEmit && npm test -- --run` | ✅ | ⬜ pending |
| 05-02-03 | 02 | 1 | STATQ-03 | type/smoke | `npx tsc --noEmit && npm test -- --run` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Existing infrastructure covers all phase requirements.
- [x] `src/components/__tests__/CardGrid.test.tsx` exists and is extendable for CTRL/STATQ assertions.
- [x] `src/lib/__tests__/stats.test.ts` will be created in 05-01 before dependent checks run.
- [x] No framework installation required (vitest + testing-library already configured).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Mobile always-visible controls + desktop hover/focus behavior | CTRL-01,CTRL-02,CTRL-04 | Responsive interaction state is visual and device-dependent | Run app in mobile and desktop widths; confirm controls visibility behavior matches phase context decisions. |
| SetGrid supplemental `Total Qty: Z` readability and alignment | STATQ-02,STATQ-03 | Typography and spacing quality is visual | Open sets with/without duplicates; verify line appears only when duplicates exist and does not break card layout. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-21
