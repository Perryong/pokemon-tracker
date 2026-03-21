---
phase: 03
slug: cards-album-ownership-tracking
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | none — manual verification baseline |
| **Config file** | none |
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
| 03-xx-01 | TBD | 1 | ALBM-01 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 03-xx-02 | TBD | 1 | ALBM-02 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 03-xx-03 | TBD | 1 | ALBM-03 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 03-xx-04 | TBD | 1 | ALBM-04 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 03-xx-05 | TBD | 1 | ALBM-05 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 03-xx-06 | TBD | 1 | ALBM-06 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 03-xx-07 | TBD | 1 | ALBM-07 | typecheck+build | `npm run build` | ✅ | ⬜ pending |
| 03-xx-08 | TBD | 1 | STAT-01 | typecheck+build | `npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/components/CardGrid.test.tsx` — optional test stubs for ALBM-01..ALBM-07 + STAT-01 if framework is introduced
- [ ] `vitest.config.ts` — optional test config
- [ ] `npm install -D vitest @testing-library/react @testing-library/user-event jsdom` — only if adding test tooling in this phase

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Card size toggle (small/medium) updates grid density | ALBM-05 | No UI test framework baseline | Switch size modes and verify card dimensions/layout change while remaining responsive |
| Ownership filter all/owned/missing works correctly | ALBM-06 | No UI test framework baseline | Toggle ownership on several cards, then apply each filter and confirm visible set |
| In-set search filters by card name live | ALBM-07 | No UI test framework baseline | Type partial card names and verify immediate filtering |
| Fixed bottom stats footer updates in real time | STAT-01 | Visual + interaction behavior | Toggle ownership and verify owned/missing/percentage values update instantly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
