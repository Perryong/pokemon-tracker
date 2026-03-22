---
phase: 06
slug: testing-validation
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest 4.x + @testing-library/react |
| **Config file** | `vitest.config.ts` |
| **Quick run command** | `npm run test -- src/components/__tests__/CardGrid.test.tsx --run` |
| **Full suite command** | `npm run test --run` |
| **Build gate command** | `npm run build` |
| **Estimated runtime** | ~15-60 seconds |

---

## Sampling Rate

- **After every task commit:** run the task-level `<automated>` command from the plan.
- **After each plan completion:** run `npm run test --run`.
- **Before phase sign-off:** run strict gate `npm run test --run && npm run build`.
- **Max feedback latency:** 120 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | TESTQ-02 | config/component | `npm run test -- src/components/__tests__/CardGrid.test.tsx --run` | ✅ | ⬜ pending |
| 06-01-02 | 01 | 1 | TESTQ-02 | component/unit | `npm run test -- src/components/__tests__/CardGrid.test.tsx --run && npm run test -- src/lib/__tests__/collection.test.ts --run` | ✅ | ⬜ pending |
| 06-01-03 | 01 | 1 | TESTQ-01 | unit | `npm run test -- src/lib/__tests__/migration.test.ts --run` | ✅ | ⬜ pending |
| 06-02-01 | 02 | 2 | TESTQ-03 | component/integration | `npm run test -- src/components/__tests__/SetGrid.regression.test.tsx --run && npm run test -- src/components/__tests__/App.persistence-regression.test.tsx --run` | ✅ | ⬜ pending |
| 06-02-02 | 02 | 2 | TESTQ-03 | component/integration | `npm run test -- src/components/__tests__/CrossViewStats.test.tsx --run && npm run test -- src/components/__tests__/CardGrid.test.tsx --run` | ✅ | ⬜ pending |
| 06-02-03 | 02 | 2 | TESTQ-03 | suite/build | `npm run test --run && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Existing Vitest + Testing Library infrastructure is in place.
- [x] Target test files referenced by plans exist or are explicitly created by tasks.
- [x] No new test framework installation required for this phase.
- [x] Strict release gate command is defined and executable.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None required for phase sign-off | TESTQ-01, TESTQ-02, TESTQ-03 | Phase 6 decision locks sign-off to automated evidence only | Optional manual checks may be run, but do not affect pass/fail. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verification commands.
- [x] Sampling continuity enforced across both plans.
- [x] Final strict gate includes both test suite and build.
- [x] No watch-mode commands in verification path.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** ready for execution planning gate (2026-03-22)
