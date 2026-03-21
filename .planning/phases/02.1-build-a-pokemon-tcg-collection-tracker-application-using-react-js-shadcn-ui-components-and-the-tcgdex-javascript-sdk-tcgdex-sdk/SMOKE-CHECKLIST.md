# Phase 02.1 Smoke Test Checklist

**Executed:** 2026-03-21  
**Build:** Production (`npm run build` → `npm run preview`)  
**URL:** http://localhost:4173  
**Purpose:** Validate release readiness of all 20/20 v1 requirements

---

## Critical Path 1: Browse → Select → Own → Persist
*Tests: DATA-01, DATA-03, PERS-01, PERS-02, SETS-01, ALBM-01, ALBM-03*

- [ ] 1.1 Open production build at http://localhost:4173
- [ ] 1.2 Verify SetGrid loads with set logos and release dates
- [ ] 1.3 Verify series filter dropdown populated (DATA-02)
- [ ] 1.4 Select series "Scarlet & Violet", verify filtered results
- [ ] 1.5 Search for "151", verify live filtering (SETS-03)
- [ ] 1.6 Verify progress bars show completion percentages (SETS-04)
- [ ] 1.7 Click a set to open CardGrid (ALBM-01)
- [ ] 1.8 Verify card images load (ALBM-02, DATA-04)
- [ ] 1.9 Toggle ownership on 3 different cards
- [ ] 1.10 Verify green ring indicator on owned cards (ALBM-04)
- [ ] 1.11 Reload browser (F5)
- [ ] 1.12 Verify owned cards still show green ring (PERS-02)
- [ ] 1.13 Verify stats footer matches owned count (PERS-03)

---

## Critical Path 2: Album Filtering & Stats
*Tests: ALBM-05, ALBM-06, ALBM-07, STAT-01*

- [ ] 2.1 In CardGrid, use ownership filter → select "Owned"
- [ ] 2.2 Verify only owned cards visible (ALBM-06)
- [ ] 2.3 Verify stats footer reflects filtered view (STAT-01)
- [ ] 2.4 Search for card name "Pikachu" (ALBM-07)
- [ ] 2.5 Verify search works with ownership filter
- [ ] 2.6 Switch size mode to "Small" (ALBM-05)
- [ ] 2.7 Verify grid adapts to 8-column layout
- [ ] 2.8 Switch back to "Medium" size mode
- [ ] 2.9 Use "Back to Sets" button
- [ ] 2.10 Verify SetGrid shows updated completion percentage (SETS-05)
- [ ] 2.11 Verify completion badge shows on 100% complete sets

---

## Critical Path 3: Edge Cases & Error States
*Tests: Stability, error handling, filter interactions*

- [ ] 3.1 Toggle same card multiple times rapidly (5+ clicks)
- [ ] 3.2 Verify no duplicate state or UI glitches
- [ ] 3.3 Clear all filters (series + search)
- [ ] 3.4 Open browser console (F12)
- [ ] 3.5 Verify no errors in console log
- [ ] 3.6 Check for network errors or failed requests

---

## Execution Notes

**How this checklist was executed:**
This checklist requires human verification in a browser. The production build has been created and the preview server is running at http://localhost:4173. Each item should be manually validated by the user.

**Pass Criteria:**
- All checklist items must be verified as working
- Any BLOCKER issues must be fixed before proceeding
- CRITICAL/HIGH issues documented in DEFERRED.md for follow-up

**Automated Setup Complete:**
- ✅ Production build created (`npm run build`)
- ✅ Preview server started at http://localhost:4173
- ✅ Smoke checklist created (27 items)

**Result:** Awaiting human verification at checkpoint

---

*Generated: 2026-03-21*  
*Source: .planning/phases/02.1-.../02.1-RESEARCH.md*
