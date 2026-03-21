# Pitfalls Research: Quantity Tracking Migration

**Domain:** TCG Collection Tracker — Boolean to Quantity Migration  
**Researched:** 2024-12-29  
**Confidence:** HIGH (based on codebase analysis + domain experience)

## Executive Summary

Adding quantity tracking to an existing boolean ownership system presents **data migration**, **UI consistency**, and **localStorage constraint** risks. The most critical pitfall is **dual-semantics confusion** — mixing boolean "owned" and numeric "quantity" mental models creates inconsistent behavior and data corruption. Secondary risks include **localStorage quota exhaustion**, **state synchronization bugs**, and **off-by-one errors** in stats calculations.

## Critical Pitfalls

### Pitfall 1: Dual-Semantics Confusion (Data Integrity)

**What goes wrong:**
Mixing boolean (`ownedCards[id]: boolean`) and quantity (`quantities[id]: number`) semantics creates inconsistent state. A card can be marked `owned: false` but have `quantity: 3`, or `owned: true` with `quantity: 0`. Stats calculations diverge from visible data. Toggles behave unpredictably.

**Why it happens:**
Incremental refactoring leaves both old boolean checks (`isOwned()`) and new quantity checks (`getQuantity()`) in the codebase. Different components use different data sources. Boolean ownership becomes "derived" from quantity (qty > 0 = owned) but the boolean field persists as a separate source of truth.

**Consequences:**
- **Silent data corruption:** User adds 3 cards via quantity UI, but `isOwned()` returns false because boolean wasn't updated
- **Stats divergence:** Set completion shows 50% but album view shows different count
- **Toggle ambiguity:** Clicking "owned" checkbox on a card with qty=3 — does it set qty=0 or qty=1?
- **Migration bugs:** Existing users have boolean-only data, new users have quantity-only data, system treats them differently

**How to avoid:**
1. **Single source of truth:** Eliminate boolean `ownedCards` field entirely. Derive ownership from `quantity > 0`
2. **Atomic migration:** Convert all boolean data to quantity in one migration (true → 1, false → 0)
3. **No dual-API period:** Remove `isOwned()`, `toggleOwnership()`, `addToCollection()` — force all code to use `getQuantity()`, `setQuantity(id, qty)` from day one
4. **Type safety:** Make `CollectionState.ownedCards` type error at compile time (remove from interface)

**Warning signs:**
- Multiple checks for same card return different results (`isOwned()` vs `getQuantity() > 0`)
- Stats calculations need conditional logic for "old data format"
- Components accessing `collection.ownedCards` directly instead of through quantity API
- Toggle buttons calling `addToCollection()` while quantity buttons call `setQuantity()`

**Phase to address:**
**Phase 1: Data Model Refactor** — Must be complete before any UI work begins. Mixing UI changes with data model changes creates integration hell.

---

### Pitfall 2: localStorage Quota Exhaustion

**What goes wrong:**
Storing per-card quantity for every card (even quantity=0) causes localStorage to hit 5-10MB quota limit. Current boolean format uses ~50 bytes per owned card. Quantity format naively implemented stores ~60-80 bytes per card *regardless of ownership*, multiplying storage by 10-50x for large collections.

**Why it happens:**
Storing quantity for non-owned cards (`quantities[id] = 0`) is redundant but easy to implement. Each card ID is ~15-20 chars (e.g., `"swsh1-1"`, `"base1-4"`), and JSON stringification adds overhead. With 10,000+ unique cards in TCGdex, storing all zeros consumes 1-2MB alone.

**Consequences:**
- **Quota exceeded errors:** `localStorage.setItem()` throws `QuotaExceededError`, collection save fails silently (caught by existing error handler but data lost)
- **User frustration:** Large collections (500+ cards) suddenly can't save new additions
- **Performance degradation:** JSON.stringify() on massive objects (10k+ keys) takes 100-500ms, blocking UI
- **Migration bloat:** Converting boolean to quantity initially works, but adding cards to already-full storage fails

**How to avoid:**
1. **Sparse storage:** Only store `{ cardId: quantity }` for qty > 0. Omit zero quantities entirely (default to 0 on read)
2. **Compressed IDs:** Consider mapping card IDs to short numeric indices if storage becomes critical
3. **Quota monitoring:** Add storage size tracking, warn at 80% capacity
4. **Lazy cleanup:** Periodically remove `quantity: 0` entries from storage (e.g., on load or background task)
5. **Data validation:** Test migration with large mock dataset (5000+ cards) before shipping

**Warning signs:**
- Storage size growing linearly with *total cards in database*, not *owned cards*
- `localStorage.setItem()` failing in browser console during testing
- JSON stringification showing large objects (>1MB) in performance profiler
- User reports "my collection isn't saving"

**Phase to address:**
**Phase 1: Data Model Refactor** — Storage format must be optimized from the start. Fixing this post-migration requires a second migration.

---

### Pitfall 3: Off-By-One Errors in Stats (Owned vs Quantity)

**What goes wrong:**
Stats calculations confuse "cards owned" (unique cards with qty > 0) vs "total quantity" (sum of all quantities). Set completion shows 80/100 cards but user actually owns 250 cards (many duplicates). Or vice versa: completion percentage calculated from total quantity instead of unique owned cards.

**Why it happens:**
Existing code calculates `owned = setCardIds.filter(id => ownedCards[id]).length` (unique count). New code might accidentally calculate `owned = Object.values(quantities).reduce((sum, qty) => sum + qty, 0)` (total quantity). Mixed terminology — "owned", "collected", "have", "missing" — becomes ambiguous with quantities.

**Consequences:**
- **Misleading completion:** "You've collected 150/100 cards" (summing quantities instead of unique)
- **Progress confusion:** User adds duplicate, completion percentage doesn't change (expected) but "Cards Owned" count increases (unexpected)
- **Filter bugs:** "Missing cards" filter shows cards where qty=0, but existing owned cards (qty≥1) are missing from "owned" filter
- **Sorting issues:** Sorting by "# owned" sorts by quantity (3 copies) instead of binary owned/missing

**How to avoid:**
1. **Explicit metrics:** Distinguish "Unique Cards Owned" (count of IDs with qty>0) vs "Total Cards" (sum of quantities)
2. **Completion consistency:** Set completion *always* uses unique cards, never quantities
3. **UI clarity:** Label stats as "X unique cards" or "Y total cards (including duplicates)"
4. **Test coverage:** Unit tests for stats with edge cases (qty=0, qty=1, qty=10+)
5. **Type aliases:** `type UniqueCount = number` vs `type TotalQuantity = number` for clarity

**Warning signs:**
- Stats don't match between different views (set grid vs album vs stats page)
- Completion percentage goes backward when adding duplicate
- "Missing cards" count is negative or > total cards
- Progress bar shows >100% completion

**Phase to address:**
**Phase 2: Stats Integration** — Stats must be explicitly redesigned for quantity semantics. Don't assume boolean stats "just work" with quantities.

---

### Pitfall 4: Race Conditions in Quantity Updates

**What goes wrong:**
Multiple rapid quantity updates (e.g., user spamming increment button) result in lost updates. Final quantity is wrong. User clicks "+1" five times, card shows quantity=2 instead of 5. Or worse: concurrent updates from different components (modal + grid) overwrite each other.

**Why it happens:**
React state updates are asynchronous. Calling `setCollection({ ...prev, quantities: { ...prev.quantities, [id]: qty + 1 }})` multiple times in quick succession reads stale `prev` values. Each update increments from the same base, not the latest value. No locking mechanism in localStorage or React state.

**Consequences:**
- **Lost increments:** User clicks +1 three times, quantity only goes up by 1
- **Quantity drift:** Actual quantity diverges from displayed quantity, requires page refresh to see correct value
- **Corruption during migration:** Migration running while user adds cards simultaneously leads to hybrid state
- **Undo/redo issues:** If implementing undo, concurrent updates break history stack

**How to avoid:**
1. **Functional updates:** Always use `setCollection(prev => ({ ...prev, quantities: { ...prev.quantities, [id]: (prev.quantities[id] || 0) + 1 }}))` — reads latest state
2. **Optimistic UI with rollback:** Display increment immediately, but roll back if save fails
3. **Debounce saves:** Batch multiple rapid increments into single localStorage write
4. **Atomic operations:** Create `incrementQuantity(id, delta)` and `setQuantity(id, newQty)` helpers that handle state updates correctly
5. **Lock during migration:** Disable collection updates while migration is in progress

**Warning signs:**
- Quantity increments "lag" behind button clicks
- Clicking +1 multiple times rapidly results in quantity not matching click count
- Console warnings about React state updates from unmounted components
- Quantity changes revert after page refresh

**Phase to address:**
**Phase 1: Data Model Refactor** — Atomic update operations must be built into the core collection hook. UI layer should never directly mutate quantities.

---

### Pitfall 5: Incomplete Migration Error Handling

**What goes wrong:**
Migration from boolean to quantity fails silently for subset of users. Some users see broken state: all quantities=0 despite previously owning cards, or migration runs twice creating duplicate data, or old data preserved alongside new data causing dual-semantics bugs (Pitfall 1).

**Why it happens:**
Migration code assumes localStorage is always present and parseable. Users with corrupted data, browser extensions blocking localStorage, private/incognito mode, or third-party storage cleaners break migration. No rollback mechanism. No migration success flag. No validation that migrated data is correct.

**Consequences:**
- **Data loss:** User's collection disappears after update, all cards show quantity=0
- **Stuck in migration loop:** Migration runs on every page load because success flag wasn't set
- **Partial migration:** Only first 100 cards migrated before quota error, rest lost
- **Customer support nightmare:** No way to diagnose or recover for users reporting "my collection is gone"

**How to avoid:**
1. **Migration versioning:** Use schema version field (v1 = boolean, v2 = quantity), check before migration
2. **Dry-run validation:** Test migration logic on copy of data before modifying actual collection
3. **Backup old format:** Store `pokemon-collection-v1-backup` before migrating to v2
4. **Success flag:** Set `migrationCompleted: true` only after successful save
5. **Error recovery:** If migration fails, restore from backup, log error, show user message
6. **Idempotent migration:** Running migration twice should be safe (no-op if already migrated)
7. **Manual recovery UI:** Provide "restore backup" button in settings for 30 days post-migration

**Warning signs:**
- User reports "lost all my cards after update"
- Migration code runs on every app startup (check dev console logs)
- localStorage shows both `v1` and `v2` keys simultaneously
- Error logs show `QuotaExceededError` during migration
- Different users reporting different migration outcomes (some work, some don't)

**Phase to address:**
**Phase 1: Data Model Refactor** — Migration must be bulletproof before any user touches it. This is a one-time operation with high risk.

---

### Pitfall 6: UI State Synchronization (Multiple Sources of Truth)

**What goes wrong:**
Quantity displayed in modal differs from quantity in card grid. User changes quantity in album view, but set grid stats don't update. Changing quantity doesn't trigger completion percentage recalculation. Opening card detail shows stale quantity value.

**Why it happens:**
Multiple components maintain local state copies of quantities. Modal reads from `collection.quantities[id]` once on mount, doesn't re-fetch on updates. Stats components compute from snapshot of ownedCards, don't recompute when quantities prop changes. React memoization caches stale values.

**Consequences:**
- **User confusion:** "I just set this to 5, why does it show 3?"
- **Mismatched stats:** Card grid shows "80/100 owned", set list shows "75/100"
- **Stale UI:** Changing quantity doesn't update progress bar until page refresh
- **Debugging difficulty:** Hard to trace which component has correct value

**How to avoid:**
1. **Single source hook:** All components use `useCollection()` hook, no local state duplication
2. **Reactive stats:** Use `useMemo` to recompute stats whenever `quantities` object reference changes
3. **Context API (optional):** If prop drilling becomes complex, use context for collection state
4. **Controlled components:** Quantity inputs controlled by parent state, not local state
5. **Key-based remounting:** Use `key={cardId}` on modals to force remount with fresh data

**Warning signs:**
- Different numbers in different parts of UI for same card/set
- Stats don't update until page refresh
- Closing and reopening modal shows different quantity than card grid
- Console shows multiple renders with different quantity values for same card

**Phase to address:**
**Phase 2: Stats Integration** AND **Phase 3: UI Components** — Both phases must coordinate on single data source pattern.

---

### Pitfall 7: Ambiguous Zero-Quantity Semantics

**What goes wrong:**
Unclear whether `quantity: 0` means "explicitly set to zero" vs "not in collection" vs "remove from storage". User removes last copy of card (qty 1→0), card disappears from "owned" filter (expected) but also disappears from storage, so undo/history is impossible. Or card stays in storage with qty=0, wasting space.

**Why it happens:**
Boolean ownership was clear: `true` = owned, `false`/missing = not owned. Quantity introduces ambiguity: Is `quantities[id] = 0` equivalent to `delete quantities[id]`? Does setting qty=0 remove card from collection or just mark it as "owned but zero copies"?

**Consequences:**
- **Storage bloat:** Every card ever owned remains in storage with qty=0, never removed
- **Incomplete removal:** Setting qty=0 doesn't fully remove card, breaks "clear collection" feature
- **Undo complexity:** If qty=0 cards are deleted, undo must re-insert them; if kept, undo must distinguish 0→1 from missing→1
- **Filter confusion:** "Missing cards" filter must check both `qty === 0` and `qty === undefined`

**How to avoid:**
1. **Explicit rule:** `quantity: 0` is equivalent to "not in collection" — always delete from storage when qty reaches 0
2. **Cleanup on write:** `setQuantity(id, 0)` automatically does `delete quantities[id]`
3. **History tracking (optional):** If undo is required, separate history log from active collection state
4. **Read default:** `getQuantity(id)` returns 0 if ID not in storage (sparse representation)
5. **Migration consistency:** Boolean `false` → missing from storage (not qty=0 entry)

**Warning signs:**
- Storage contains hundreds of `"cardId": 0` entries
- "Missing" filter needs complex logic (`qty === 0 || !quantities[id]`)
- "Clear collection" feature doesn't actually remove cards from storage
- Undo/redo logic has special cases for qty=0

**Phase to address:**
**Phase 1: Data Model Refactor** — Semantics must be defined before implementing any quantity operations.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep boolean `ownedCards` alongside `quantities` for "compatibility" | No code changes to existing components | Dual-semantics bugs (Pitfall 1), permanent tech debt | Never — forces full refactor later |
| Store all quantities including zeros | Simple implementation, no special read logic | Storage bloat, quota errors (Pitfall 2) | Only for MVP if collection < 100 cards |
| Skip migration backup | Faster migration, less complexity | No recovery if migration fails, user data loss | Never — backup is essential |
| Use string quantity inputs without validation | User can type any value | Invalid quantities (negative, decimals, huge numbers), data corruption | Never — always validate input |
| Calculate stats on every render without memoization | Simple code, no React optimization | UI lag with large collections (500+ cards) | Acceptable for Phase 1, fix in Phase 2 optimization |
| Manual quantity input only (no increment/decrement buttons) | Less UI complexity | Poor UX for high-quantity cards (typing "23" is slower than clicking +1 twenty-three times... wait, actually typing is faster) | Acceptable for MVP, add buttons later |
| No migration version tracking | Less code, no schema versioning | Can't detect if migration already ran, risk of double-migration | Never — version field is 1 line of code |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `useCollection` hook | Returning `ownedCards` object (boolean) alongside `quantities` object | Remove `ownedCards` entirely, derive `isOwned(id)` from `quantities[id] > 0` |
| localStorage writes | Writing full collection state on every quantity change | Debounce writes, batch multiple changes, use functional updates |
| Stats calculations | Mixing `filter(isOwned).length` (unique) with `reduce(sum quantities)` (total) | Explicitly name metrics: `uniqueOwned` vs `totalQuantity`, document which is used where |
| React re-renders | Components re-render on every collection change (all cards) | Memoize components by card ID, only re-render affected cards |
| TCGdex API | Fetching card data to determine if owned | Cache card ownership locally, don't hit API for ownership checks |
| Migration timing | Running migration in `useEffect` (happens on every render during development) | Run migration once on app load, outside React lifecycle, set success flag |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| JSON.stringify() on every quantity change | UI freezes for 100-500ms on increment | Debounce writes to 500ms, batch changes | Collections > 500 cards |
| Recomputing stats for entire collection on single card update | Progress bar lags behind button click | Memoize stats per set, only recompute affected set | Collections > 1000 cards |
| No memoization in card grid renders | Scrolling feels janky, all cards re-render on any change | Wrap cards in `React.memo`, compare by card ID | >50 cards per page |
| Loading entire TCGdex database into memory for stats | 100+ MB memory usage, slow page load | Compute stats from localStorage quantities only, no need for full card data | Any large set (200+ cards) |
| Sparse storage read misses | Checking `quantities[id]` for every card in every render | Cache "isOwned" checks in useMemo, use Set for O(1) lookup | >1000 cards rendered |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback on quantity change | User clicks +1, nothing happens (debounced), clicks again, eventually sees +2 | Optimistic UI update immediately, debounce only localStorage write |
| Quantity input accepts invalid values | User types "-5" or "999999", breaks stats | Validate input, clamp to 0-999, show error message on invalid input |
| No visual distinction between qty=1 and qty=5+ | All owned cards look the same, user forgets which have duplicates | Badge showing quantity on card thumbnail, different color for duplicates |
| Removing last card (qty 1→0) requires two actions | User decrements to 0, then must click "remove" button | Decrementing to 0 automatically removes card from collection |
| No bulk quantity operations | User wants to add 5 copies of 20 cards after opening booster box, must click +1 one hundred times | "Add multiple" modal with quantity input, or "quick add" flow |
| Quantity controls hidden in modal/detail | User must click card, open modal, find quantity input, change, close — slow | Inline quantity controls on card thumbnail (hover or always visible) |
| No undo for accidental quantity changes | User accidentally clicks "set to 0" instead of +1, loses data | Undo toast notification for 5 seconds after change |

## "Looks Done But Isn't" Checklist

- [ ] **Migration:** Tested with realistic large dataset (1000+ cards), not just 5 sample cards — verify doesn't hit quota limit
- [ ] **Migration:** Backup created before migration, success flag set after, idempotent (safe to run twice) — verify in browser DevTools localStorage
- [ ] **Quantity operations:** All use functional state updates (`prev => ...`), not direct reads — verify by rapidly clicking +1 ten times
- [ ] **Stats calculations:** Explicitly tested with qty=0, qty=1, qty=10+, and missing IDs — verify owned count vs total quantity distinction
- [ ] **UI synchronization:** Multiple components (grid, modal, stats) show same quantity immediately after change — verify by opening modal while grid visible
- [ ] **Storage efficiency:** Only non-zero quantities stored, verified by checking localStorage size and contents — verify qty=0 cards are deleted
- [ ] **Input validation:** Quantity inputs reject negative, decimal, huge numbers — verify by typing "-1", "3.14", "9999999"
- [ ] **Error handling:** Migration failure shows user-friendly message and preserves old data — verify by simulating quota error
- [ ] **localStorage errors:** QuotaExceededError caught and handled gracefully, user notified — verify by filling localStorage to limit

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Dual-semantics confusion (boolean + quantity both active) | HIGH — requires careful refactor | 1. Create temporary derived boolean field from quantities, 2. Update all consumers to use derived field, 3. Remove original boolean field |
| localStorage quota exceeded | MEDIUM — requires data cleanup | 1. Implement sparse storage (remove qty=0), 2. Force re-save collection to compact, 3. Add quota monitoring |
| Lost migration (user's collection gone) | LOW — if backup exists | 1. Restore from `pokemon-collection-v1-backup`, 2. Re-run migration with fix, 3. Delete backup after success |
| Race conditions (lost increments) | LOW — no data corruption, just UX issue | 1. Replace direct state updates with functional updates, 2. Add debouncing, 3. Test rapid clicks |
| Stats divergence (different numbers in different views) | MEDIUM — requires state audit | 1. Identify all stat calculation sites, 2. Standardize on single source (useCollection hook), 3. Add integration test |
| Incomplete migration (subset of cards migrated) | MEDIUM — if backup exists | 1. Restore backup, 2. Fix migration to handle quota errors mid-migration, 3. Re-run with error handling |
| Zero-quantity ambiguity (storage bloat) | LOW — cleanup is straightforward | 1. Write cleanup script to remove qty=0 entries, 2. Run on user's localStorage, 3. Add deletion to setQuantity(0) |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Dual-semantics confusion | Phase 1: Data Model Refactor | No references to `ownedCards` boolean in codebase, all ownership derived from quantity |
| localStorage quota exhaustion | Phase 1: Data Model Refactor | localStorage size < 500KB for 1000-card collection, no qty=0 entries stored |
| Off-by-one stats errors | Phase 2: Stats Integration | Unit tests pass for "unique owned" vs "total quantity" edge cases |
| Race conditions | Phase 1: Data Model Refactor | Rapid clicking +1 button 10 times results in qty=10, no lost updates |
| Incomplete migration | Phase 1: Data Model Refactor | Migration creates backup, sets success flag, tested with quota error simulation |
| UI state synchronization | Phase 2: Stats Integration + Phase 3: UI Components | Changing quantity in modal updates grid and stats immediately, no refresh needed |
| Zero-quantity semantics | Phase 1: Data Model Refactor | Setting qty=0 removes card from storage, getQuantity(id) returns 0 for missing IDs |

## Domain-Specific Considerations

### TCG Collection Tracking Context

**Why quantity matters differently here:**
- **Duplicates are common:** Opening booster packs creates duplicates by design, unlike other collection types (books, movies)
- **Trade economy:** TCG collectors often track extras for trading, so qty>1 is not just "backup," it's actionable data
- **Set completion mindset:** Completion percentage is about *unique cards*, not total quantity, but users also care about total card count
- **Bulk additions:** Opening a booster box (36 packs) can add 360 cards at once, not one-at-a-time
- **Rarity differences:** Users may want 1 copy of common cards but 4 copies of competitive playable cards (deck limit)

**Implications for quantity semantics:**
- Set completion stats MUST use unique count, not total quantity
- Bulk operations (add set, add multiple) are high priority, not nice-to-have
- Quantity UI must be fast enough for rapid entry (keyboard shortcuts, +1/-1 buttons)
- "Missing" filter is about unique cards not owned, ignoring quantity
- Future feature: "Tradeable extras" (qty > 1) is a natural extension

## Sources

- **Codebase analysis:** `.planning/PROJECT.md`, `src/lib/collection.ts`, `src/components/CardGrid.tsx`, `src/components/CollectionStats.tsx`
- **Domain knowledge:** TCG collection tracking patterns, localStorage best practices
- **React patterns:** State management, memoization, functional updates (React documentation)
- **localStorage limits:** 5-10MB quota across browsers (MDN Web Docs)
- **Migration patterns:** Schema versioning, backward compatibility (established patterns)
- **Training data:** Common pitfalls in boolean-to-quantity data migrations

---

*Pitfalls research for: Pokemon TCG Collection Tracker v1.1 Quantity Tracking*  
*Researched: 2024-12-29*  
*Next: Feed into roadmap phase structure and success criteria*
