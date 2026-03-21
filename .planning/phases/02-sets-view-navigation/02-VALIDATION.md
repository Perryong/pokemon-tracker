---
phase: 02
slug: sets-view-navigation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | none — Wave 0 installs Vitest + React Testing Library |
| **Config file** | none — Wave 0 creates `vitest.config.ts` |
| **Quick run command** | `npm run build` |
| **Full suite command** | `npm run build` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm run build`
- **After every plan wave:** Run `npm run build`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | SETS-01 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 02-01-02 | 01 | 0 | SETS-02 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 02-01-03 | 01 | 0 | SETS-03 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 02-01-04 | 01 | 0 | SETS-04 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 02-01-05 | 01 | 0 | SETS-05 | typecheck+build | `npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/components/SetGrid.test.tsx` — stubs for SETS-01..SETS-05 (optional; only if tests are introduced in this phase)
- [ ] `vitest.config.ts` — shared test config (optional)
- [ ] `npm install -D vitest @testing-library/react @testing-library/user-event jsdom` — only if test tooling is added

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Series dropdown filters sets | SETS-02 | No existing UI test framework in repo baseline | Open Sets view, select a series, confirm only matching sets remain |
| Live set-name search | SETS-03 | No existing UI test framework in repo baseline | Type partial set name, verify list updates per keystroke |
| Completion badge visibility | SETS-05 | Visual semantics check | Ensure 100% sets show distinct completion indicator |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
