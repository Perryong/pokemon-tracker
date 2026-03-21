# Project Research Summary

**Project:** Pokemon TCG Collection Tracker v1.1  
**Domain:** Collection Management — Quantity/Duplicate Tracking Extension  
**Researched:** 2024-12-19  
**Confidence:** HIGH

## Executive Summary

v1.1 adds quantity tracking to an existing boolean ownership system (v1.0 shipped and stable). This milestone converts collection data from `Record<cardId, boolean>` to `Record<cardId, number>`, enabling users to track duplicate cards while preserving the fast local-first workflow that makes v1.0 successful.

**The good news:** No new dependencies required. The existing React+TypeScript+Vite+shadcn/ui stack handles all quantity features. The critical success factors are (1) data migration executed safely with backward compatibility, (2) preserving the click-to-toggle UX that users love from v1.0, and (3) maintaining the semantic distinction between "unique cards owned" (progress metric) vs "total quantity" (duplicates metric).

**The key risk:** Dual-semantics confusion. The most dangerous pitfall is maintaining both boolean ownership and numeric quantity as separate sources of truth, which creates data corruption and stats divergence. The solution is to eliminate the boolean `ownedCards` field entirely and derive ownership from `quantity > 0`. The second risk is localStorage quota exhaustion if zero-quantity cards are stored — sparse storage (only storing qty > 0) prevents this. The third risk is off-by-one errors in stats calculations mixing unique counts with total quantities.

## Key Findings

### Recommended Stack

**No new dependencies required.** All quantity features leverage the existing v1.0 stack with proven patterns from the boolean ownership migration (`pokemon-collection-v2` storage key).

**Core technologies:**
- **React 18.3.1 + TypeScript 5.5.3:** Extend `useCollection` hook with quantity methods (`getQuantity`, `setQuantity`, `incrementQuantity`, `decrementQuantity`) while preserving existing boolean compatibility methods
- **shadcn/ui components:** Existing `Button`, `Input`, and `Badge` components handle all quantity UI needs (increment/decrement controls, quantity display, manual entry)
- **Zod 3.23.8:** Validates quantity constraints (0 ≤ qty ≤ 999, integers only) using existing validation infrastructure
- **localStorage:** Schema migration from v2 (boolean) → v3 (quantity) using versioned migration pattern already validated in v1.0
- **Vitest 4.1.0 + Testing Library:** Existing test infrastructure covers quantity operations, migration, and regression tests with no additions needed

**Critical integration decision:** Migrate to `CollectionState { version: 3, cardQuantities: Record<string, number> }` with sparse storage (omit qty=0 entries). Derive boolean `ownedCards` as computed property for backward compatibility during transition.

### Expected Features

**Must have (v1.1 launch blockers):**
- Per-card quantity display with visual badge (qty > 0 shows count)
- Increment/decrement controls (+/-) for quick duplicate tracking
- Zero-quantity validation (cannot go below 0)
- Single-click toggle preservation (click card = 0↔1, maintains v1.0 speed)
- Quantity-aware statistics (progress tracks unique cards owned, not total quantity)
- Data persistence via localStorage with v2→v3 migration
- Visual distinction for qty=1 vs qty>1 (checkmark vs badge)
- Boolean ownership = derived from quantity (qty > 0)

**Should have (v1.x enhancements after validation):**
- Manual quantity input field (type number directly vs clicking +1 twenty times)
- Keyboard shortcuts for quantity (arrow keys, +/- keys)
- Quantity filter: "duplicates only" (show cards with qty > 1)
- Batch quantity reset at set level (recount workflow)

**Defer to v2+:**
- Undo last quantity change (requires action history tracking, high complexity)
- Separate "for trade" quantity (inventory management scope creep)
- Condition tracking per quantity ("3 mint, 2 played" — combinatorial explosion)
- Price/value tracking (financial management feature drift)

**Key insight from research:** Most collection trackers *lose* the fast click-to-toggle when adding quantity controls. This is our differentiator — preserve the v1.0 single-click workflow for 0→1 transitions, add quantity controls as *augmentation* not replacement.

### Architecture Approach

**Brownfield integration strategy:** Evolve existing architecture, don't replace it. The v1.0 system uses hook-based collection state (`useCollection`) with localStorage persistence. Quantity tracking extends this pattern without disrupting the established component boundaries.

**Major components and changes:**

1. **lib/collection.ts (CORE MODIFICATION)** — Data model and state management
   - **Change:** `CollectionState` from `{ version: 1, ownedCards: Record<string, boolean> }` to `{ version: 3, cardQuantities: Record<string, number> }`
   - **Migration:** v1 boolean → v3 numeric with `true → 1`, `false/undefined → omit from storage` (sparse representation)
   - **New methods:** `getQuantity()`, `setQuantity()`, `incrementQuantity()`, `decrementQuantity()`
   - **Compatibility:** Preserve `isOwned()`, `toggleOwnership()` as wrappers over quantity operations
   - **Derived state:** Compute `ownedCards: Record<string, boolean>` from quantities on-demand (qty > 0 = owned)

2. **components/CardGrid.tsx (UI INTEGRATION)** — Quantity controls and display
   - **Add:** Quantity badge overlay (top-right corner, shows count if > 0)
   - **Add:** Increment/decrement buttons (+ / -) on hover or always visible
   - **Add:** Manual input (click badge → enter number)
   - **Preserve:** Existing ownership filter (owned = qty > 0)

3. **lib/stats.ts (STATS COMPUTATION)** — Quantity-aware metrics
   - **Maintain:** Set completion uses unique card count (qty > 0), *never* total quantity sum
   - **Add:** Optional `totalQuantity` and `duplicates` metrics for enhanced stats footer
   - **Critical:** Explicitly distinguish `uniqueOwned` (count of IDs with qty>0) vs `totalQuantity` (sum of quantities)

4. **TCGdex API hooks (NO CHANGE)** — Card data fetching unchanged
   - **Impact:** None. API provides card definitions, collection state is independent

**Data flow pattern:**
```
User clicks +1 → incrementQuantity(cardId)
  → setCollection(prev => functional update with (prev.qty || 0) + 1)
  → useEffect → localStorage.setItem('pokemon-collection-v2', stringify(v3 state))
  → CardGrid badge re-renders, SetGrid progress updates if 0→1 transition
```

**Anti-patterns to avoid:**
- Separate quantity store (creates dual-source-of-truth sync bugs)
- Breaking change to `ownedCards` type (forces simultaneous migration of all consumers)
- Adding `quantity` field to `PokemonCard` API model (mixes read-only data with user state)
- No migration fallback (data loss risk if migration fails)

### Critical Pitfalls

**Pitfall 1: Dual-Semantics Confusion (CRITICAL — Data Integrity)**
- **What:** Mixing boolean `ownedCards[id]` and numeric `quantities[id]` as separate sources causes inconsistent state (owned=false but qty=3, or owned=true but qty=0)
- **Prevention:** Eliminate boolean field entirely. Store only `cardQuantities: Record<string, number>`. Derive `isOwned(id)` as `qty > 0`. Atomic migration v1→v3 converts all boolean data to quantity in one pass. No dual-API period.
- **Detection:** Multiple checks for same card return different results. Stats conditional on "old format". Components accessing `ownedCards` directly instead of quantity API.
- **Phase:** Must be resolved in Phase 1 (Data Model Refactor) before any UI work

**Pitfall 2: localStorage Quota Exhaustion (CRITICAL — Reliability)**
- **What:** Storing quantity for all cards (including qty=0) multiplies storage 10-50x, hitting 5-10MB browser limit
- **Prevention:** Sparse storage — only store `{ cardId: quantity }` for qty > 0. Omit zero quantities (default to 0 on read). Test with 5000+ card mock dataset.
- **Detection:** Storage size growing with *total cards in database*, not *owned cards*. `QuotaExceededError` in console.
- **Phase:** Must be part of Phase 1 (Data Model Refactor) — storage format baked into migration

**Pitfall 3: Off-By-One Stats Errors (HIGH — User Confusion)**
- **What:** Mixing "cards owned" (unique count) vs "total quantity" (sum) breaks completion percentage (shows "150/100 cards" or progress doesn't change when adding duplicates)
- **Prevention:** Set completion *always* uses unique card count (qty > 0), never quantities. Label stats explicitly: "Unique Cards Owned" vs "Total Cards (with duplicates)". Unit tests for edge cases (qty=0, qty=1, qty=10+).
- **Detection:** Stats don't match between views. Completion goes backward when adding duplicate. "Missing cards" count negative.
- **Phase:** Must be addressed in Phase 2 (Stats Integration)

**Pitfall 4: Race Conditions in Quantity Updates (MODERATE — UX)**
- **What:** Multiple rapid clicks lost due to stale state reads (click +1 five times, get qty=2 instead of 5)
- **Prevention:** Functional state updates (`setCollection(prev => ...)` reads latest state). Optimistic UI with rollback. Atomic operation helpers.
- **Detection:** Quantity lags behind clicks. Rapid clicking doesn't match final quantity.
- **Phase:** Phase 1 (Data Model) — atomic updates built into collection hook

**Pitfall 5: Incomplete Migration Error Handling (HIGH — Data Loss Risk)**
- **What:** Migration fails silently for users with corrupted data, localStorage blocked, or quota errors mid-migration
- **Prevention:** Migration versioning with schema version field. Dry-run validation on copy. Backup old format (`pokemon-collection-v1-backup`). Success flag only after save. Idempotent (safe to run twice). Manual recovery UI.
- **Detection:** "Lost all my cards" reports. Migration runs on every startup. Both v1 and v3 keys in localStorage.
- **Phase:** Phase 1 (Data Model) — migration must be bulletproof before user touches it

## Implications for Roadmap

Based on research, recommended phase structure prioritizes data integrity before UI, validates with MVP, then enhances based on feedback.

### Phase 1: Data Model & Migration Foundation
**Rationale:** Data migration is one-time, high-risk operation. Must be bulletproof before any UI work. Mixing data changes with UI changes creates integration hell.

**Delivers:**
- v3 schema definition (`cardQuantities: Record<string, number>`)
- v1→v3 migration logic with backup, validation, success flag
- Sparse storage (qty=0 omitted)
- Quantity methods in `useCollection` (get/set/increment/decrement)
- Derived `ownedCards` for backward compatibility
- Unit tests for migration with 1000+ card dataset
- Error handling for quota exceeded, corrupted data

**Addresses from FEATURES.md:**
- Data model migration (table stakes)
- Quantity persistence (table stakes)
- Zero quantity = not owned semantic (table stakes)

**Avoids from PITFALLS.md:**
- Dual-semantics confusion (eliminate boolean, use derived)
- localStorage quota exhaustion (sparse storage)
- Race conditions (functional updates)
- Incomplete migration handling (backup + validation)
- Zero-quantity ambiguity (defined semantics)

**Success criteria:**
- Migration tested with 5000+ card mock data
- Rollback to v1 possible (backup preserved)
- All existing v1.0 collections migrate without loss
- localStorage size < 500KB for 1000-card collection

---

### Phase 2: Quantity Controls UI (MVP)
**Rationale:** Deliver minimum viable quantity tracking. Users need to see and modify quantities. Preserve fast v1.0 click workflow as differentiator.

**Delivers:**
- Quantity badge on cards (top-right corner)
- Increment/decrement buttons (+ / -)
- Click-to-increment preserves fast workflow
- Quantity input validation (0-999, integers)
- Visual distinction: qty=1 (checkmark) vs qty>1 (badge)

**Addresses from FEATURES.md:**
- Per-card quantity display (table stakes)
- Increment/decrement controls (table stakes)
- Validation cannot go below zero (table stakes)
- Single-click toggle preservation (differentiator)
- Visual distinction for quantity > 1 (table stakes)

**Avoids from PITFALLS.md:**
- UI state synchronization (all components use `useCollection` hook)
- No feedback on quantity change (optimistic UI updates)

**Success criteria:**
- User can click card to go 0→1 (fast workflow preserved)
- User can click +1/-1 to adjust quantity
- Quantity badge displays correctly
- No negative quantities possible
- Ownership filter still works (owned = qty > 0)

---

### Phase 3: Stats Integration
**Rationale:** Progress tracking must explicitly distinguish unique cards vs total quantity. Critical for user understanding of completion percentage.

**Delivers:**
- Quantity-aware set completion (unique count)
- Footer stats: "X unique cards" and "Y total cards" separate
- Set progress bars based on unique ownership (qty > 0)
- Regression: existing v1.0 stats behavior preserved

**Addresses from FEATURES.md:**
- Quantity-aware set statistics (table stakes)
- Quantity-aware completion percentage (table stakes)

**Avoids from PITFALLS.md:**
- Off-by-one stats errors (explicit unique vs total)
- Stats divergence between views (single source)

**Success criteria:**
- Set completion shows unique cards owned, not total quantity
- Footer shows both unique and total (labeled clearly)
- Adding duplicate doesn't change completion percentage
- Stats match between SetGrid, CardGrid, CollectionView

---

### Phase 4: Manual Input & Polish (Post-MVP)
**Rationale:** Defer until usage validates need. Manual input is quality-of-life for bulk entry but not required for MVP. Add based on user feedback (analytics showing >10 increments per change, or user requests).

**Delivers:**
- Manual quantity input field (click badge → type number)
- Keyboard shortcuts (arrow keys, +/-)
- Quantity filter: "duplicates only"
- Batch reset at set level

**Addresses from FEATURES.md:**
- Manual quantity input (differentiator, deferred)
- Keyboard shortcuts (differentiator, deferred)
- Quantity filter duplicates (differentiator, deferred)
- Batch reset (differentiator, deferred)

**Success criteria:**
- User feedback validates need (tracked via analytics)
- Implementation doesn't break MVP workflows

---

### Phase Ordering Rationale

**Why this order:**
1. **Data first, UI second:** Migration failure = data loss. UI bugs = annoying but fixable. Data layer must be rock-solid before UI touches it.
2. **MVP validates assumptions:** Ship increment/decrement first. *Then* measure if users need manual input (analytics: clicking +1 twenty times vs typing "20").
3. **Stats after controls:** Users need to *see* and *change* quantities before caring about advanced stats. Basic "unique owned" metric in Phase 2, enhanced breakdown in Phase 3.
4. **Polish after validation:** Keyboard shortcuts and filters are power-user features. Validate demand before building.

**Dependency chain:**
```
Phase 1 (Data) → BLOCKS → Phases 2, 3, 4
Phase 2 (UI) → ENABLES → Phase 4 (enhanced controls)
Phase 3 (Stats) → INDEPENDENT → can run parallel to Phase 2
```

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 1 (Data Migration):** Schema migration with large datasets (>5000 cards) needs localStorage quota testing in multiple browsers. Backup/recovery flow needs user testing for error scenarios.
- **Phase 4 (Manual Input):** Keyboard shortcut patterns need accessibility audit (conflicts with browser shortcuts, screen reader support).

**Phases with standard patterns (skip research-phase):**
- **Phase 2 (UI Controls):** Increment/decrement buttons are established pattern. shadcn/ui Button+Badge components are well-documented. No novel interaction design.
- **Phase 3 (Stats):** Stats calculation is pure data transformation. React `useMemo` pattern is standard. Testing framework validated in v1.0.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | All tools present in existing dependencies. No new installs required. React hooks, shadcn/ui, Zod, localStorage patterns validated in v1.0. |
| Features | **HIGH** | Table stakes features consistent across 5+ major collection trackers (TCGPlayer, Pokellector, Cardmarket, Delver Lens). Click-to-toggle preservation is validated differentiation. |
| Architecture | **HIGH** | Direct codebase analysis. Brownfield integration extends proven v1.0 patterns. Hook evolution simpler than replacement. Component boundaries well-defined. |
| Pitfalls | **HIGH** | Critical pitfalls sourced from boolean-to-quantity migration patterns, React state management gotchas, and localStorage constraints (MDN Web Docs). TCG domain specifics (duplicates common, progress = variety) inform semantic decisions. |

**Overall confidence:** HIGH

### Gaps to Address

**Minor gaps (handle during implementation):**
- **localStorage quota in practice:** Test with realistic dataset sizes across browsers (Chrome, Firefox, Safari) to validate 600KB estimate and 5MB headroom
- **Migration rollback UX:** Define user-facing message if migration fails (currently console.error, needs toast notification)
- **Quantity max value:** 999 is reasonable upper bound, but validate with competitive players who maintain 4-copy playsets across multiple decks
- **Keyboard shortcut conflicts:** If implementing arrow keys for quantity, audit against browser/screen reader defaults

**No blockers identified.** All gaps are refinements during implementation, not unknowns blocking planning.

## Sources

### Primary (HIGH confidence)
- **Existing codebase** — `src/lib/collection.ts`, `src/components/CardGrid.tsx`, `package.json`, `.planning/PROJECT.md`, `.planning/STATE.md` (v1.0 shipped, stable patterns)
- **TCGPlayer Collection Tracker** — Industry standard TCG collection management (increment/decrement, quantity badges, unique stats)
- **Pokellector** — Pokemon-specific tracker (fast toggle, quantity overlays, set completion focus)
- **shadcn/ui component catalog** — Verified Button, Input, Badge, Popover components available
- **MDN Web Docs** — localStorage quota limits (5-10MB browser-dependent), DOMException handling

### Secondary (MEDIUM confidence)
- **Cardmarket Collection** — European TCG marketplace tracker (manual input patterns, unique vs total counts)
- **Delver Lens** — Mobile scanner app (quantity entry workflows, visual indicators)
- **React documentation** — Functional state updates, useMemo patterns, hook composition
- **Zod documentation** — Number schema validation (min, max, int constraints)

### Tertiary (LOW confidence)
- **Pokemon TCG community patterns** — Booster pack duplicate rates, competitive playset requirements (informs feature prioritization but not implementation)

---

## Ready for Roadmap

**SUMMARY.md complete.** Research synthesis provides:
- ✅ Clear phase structure (4 phases, dependencies mapped)
- ✅ Feature prioritization (table stakes vs differentiators vs deferred)
- ✅ Pitfall prevention strategies (mapped to phases)
- ✅ Technology stack decisions (no new dependencies)
- ✅ Architecture integration points (brownfield extension, not replacement)
- ✅ Confidence assessment (HIGH across all areas, minor gaps identified)

**Recommendation for roadmapper:**
- **Start with Phase 1 (Data Model) as milestone 1.1.1** — critical foundation, must be bulletproof
- **Phase 2 (UI Controls) + Phase 3 (Stats) as milestone 1.1.2** — deliver MVP quantity tracking
- **Phase 4 (Polish) as milestone 1.1.3 or defer to 1.2** — validate demand first

**Success metrics for v1.1:**
- Existing v1.0 users: Zero data loss during migration (100% success rate)
- New workflow: Click-to-toggle preserved (< 1 second for 0→1 transition)
- Storage efficiency: < 500KB for 1000-card collection (sparse storage working)
- Stats accuracy: Completion % based on unique cards (not total quantity)

---

*Research completed: 2024-12-19*  
*Ready for requirements: yes*  
*Next: Feed synthesis into roadmap phase planning for v1.1 Quantity Tracking milestone*
