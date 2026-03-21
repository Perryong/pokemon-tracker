---
phase: 04
slug: data-model-migration
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-21
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest 4.x |
| **Config file** | `vitest.config.ts` |
| **Quick run command** | `npm test -- --run src/lib/__tests__/collection.test.ts` |
| **Full suite command** | `npm test -- --run` |
| **Estimated runtime** | ~5-15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm test -- --run src/lib/__tests__/collection.test.ts`
- **After every plan wave:** Run `npm test -- --run`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | QTY-01,QTY-02 | unit/type | `npx tsc --noEmit src/lib/collection-types.ts` | ✅ | ⬜ pending |
| 04-01-02 | 01 | 1 | QTY-01,QTY-04,TESTQ-01 | unit | `npm test -- --run src/lib/__tests__/migration.test.ts` | ✅ | ⬜ pending |
| 04-02-01 | 02 | 2 | QTY-01,QTY-02,QTY-03,QTY-04 | unit/type | `npx tsc --noEmit && npm test -- --run src/lib/__tests__/collection.test.ts` | ✅ | ⬜ pending |
| 04-02-02 | 02 | 2 | TESTQ-01 | unit | `npm test -- --run src/lib/__tests__/collection.test.ts` | ✅ | ⬜ pending |
| 04-02-03 | 02 | 2 | TESTQ-01 | suite/type | `npm test -- --run && npx tsc --noEmit` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Existing infrastructure covers all phase requirements.
- [x] `src/lib/__tests__/collection.test.ts` exists and will be extended for migration/idempotency/sparse-storage coverage.
- [x] `src/lib/__tests__/migration.test.ts` planned in 04-01 to isolate migration-specific edge cases.
- [x] Vitest, testing-library, and localStorage mock environment already configured.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Migration UX remains silent on success and non-blocking on fallback | QTY-04 | Toast presentation semantics are UX-level | Start app with v1 payload in localStorage; verify no blocking modal; simulate failure path and verify warning toast appears. |
| Backup lifecycle (kept until next successful start) | QTY-04 | Lifecycle spans app restarts | Migrate once, reload app twice, verify deterministic backup key lifecycle matches policy. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s for quick checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-21
