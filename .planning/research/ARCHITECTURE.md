# Architecture Research: Quantity Tracking Integration

**Domain:** Pokemon TCG Collection Tracker - Quantity/Duplicate Tracking
**Milestone:** v1.1 Quantity Tracking
**Researched:** 2026-03-21
**Confidence:** HIGH (brownfield codebase analysis)

## Executive Summary

v1.1 adds quantity tracking to an existing ownership-based architecture (v1.0 shipped). The current system uses a boolean `Record<cardId, boolean>` in localStorage. Quantity tracking requires migrating to `Record<cardId, number>` while preserving backward compatibility and maintaining the established adapter/hook/component patterns.

**Key integration approach:**
- **Safe migration** from boolean → numeric with v3 storage schema
- **Minimal disruption** by evolving `useCollection` hook, not replacing it
- **Component updates** focused on CardGrid (quantity controls) and stats calculations
- **No breaking changes** to existing API hooks, types, or TCGdex integration

## Existing Architecture (v1.0)

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  SetGrid │  │ CardGrid │  │Collection│  │  Stats   │    │
│  │  (v1.0)  │  │  (v1.0)  │  │   View   │  │  Footer  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │              │             │           │
│       │             │ toggleOwnership()          │           │
│       │             │ isInCollection()           │           │
│       │             │                            │           │
├───────┴─────────────┴──────────────┴─────────────┴──────────┤
│                      DATA ACCESS LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌────────────────────────────┐   │
│  │   TCGdex SDK Client  │  │  useCollection Hook        │   │
│  │   (lib/api.ts)       │  │  (lib/collection.ts)       │   │
│  │   - useSets()        │  │  - ownedCards: Record<>    │   │
│  │   - useCards()       │  │  - isOwned(cardId)         │   │
│  │   - useSeries()      │  │  - toggleOwnership()       │   │
│  │   UNCHANGED v1.1 ✓   │  │  EVOLVE FOR v1.1 ⚠️        │   │
│  └──────────┬───────────┘  └────────┬───────────────────┘   │
│             │                        │                       │
├─────────────┴────────────────────────┴───────────────────────┤
│                      PERSISTENCE LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐  ┌─────────────────────────────┐    │
│  │  TCGdex API        │  │  localStorage v2 (v1.0)     │    │
│  │  (Remote)          │  │  { version: 1,              │    │
│  │  UNCHANGED ✓       │  │    ownedCards: Record<      │    │
│  │                    │  │      string, boolean> }     │    │
│  │                    │  │                              │    │
│  │                    │  │  MIGRATE TO v3 (v1.1) 🔄    │    │
│  │                    │  │  { version: 3,              │    │
│  │                    │  │    cardQuantities: Record<  │    │
│  │                    │  │      string, number> }      │    │
│  └────────────────────┘  └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Current Component Boundaries

| Component | Responsibility | Data Dependencies |
|-----------|----------------|-------------------|
| **SetGrid** | Display sets with progress bars | useSets(), ownedCards (read-only) |
| **CardGrid** | Album view with ownership toggle | useCards(), isOwned(), toggleOwnership() |
| **CollectionView** | Show all owned cards | useCollection() |
| **Stats Footer** | Real-time completion stats | ownedCards (computed stats) |
| **useCollection** | Collection state + persistence | localStorage 'pokemon-collection-v2' |
| **TCGdex Hooks** | Fetch sets/cards from API | @tcgdex/sdk (external) |

### Current Data Model (v1.0)

**Collection State:**
```typescript
interface CollectionState {
  version: 1;
  ownedCards: Record<string, boolean>; // cardId → true/false
}
```

**localStorage Key:** `pokemon-collection-v2`

**Key Operations:**
- `isOwned(cardId: string): boolean` — Check ownership
- `toggleOwnership(cardId: string): void` — Toggle owned state
- `addToCollection(cardId: string): void` — Mark as owned
- `removeFromCollection(cardId: string): void` — Mark as not owned

### Current Patterns

**Pattern 1: Hook-Based Collection State**
- Single `useCollection()` hook manages all ownership state
- Auto-persists to localStorage on state changes
- Consumed by multiple components (CardGrid, SetGrid, CollectionView)

**Pattern 2: Boolean Ownership Model**
- `ownedCards[cardId] = true` means "I own this card"
- Missing key or `false` means "I don't own this card"
- Stats computed by counting `true` values

**Pattern 3: Component Prop Drilling**
- App.tsx orchestrates views but doesn't hold collection state
- Components call `useCollection()` directly (no context provider)
- No prop drilling of collection methods

## Quantity Tracking Architecture (v1.1)

### New Data Model

**Evolved Collection State:**
```typescript
interface CollectionState {
  version: 3;
  cardQuantities: Record<string, number>; // cardId → quantity (0 = not owned)
}
```

**Backward Compatibility Rule:**
```typescript
// v2 boolean → v3 numeric migration
// true → 1 (owned, quantity 1)
// false/undefined → 0 (not owned)
```

**localStorage Key:** `pokemon-collection-v2` (reused; version field discriminates)

### Integration Points

#### 1. **lib/collection.ts** (MODIFY - Core Integration Point)

**Current Interface:**
```typescript
interface CollectionHook {
  ownedCards: Record<string, boolean>;
  isOwned: (cardId: string) => boolean;
  isInCollection: (cardId: string) => boolean; // alias
  toggleOwnership: (cardId: string) => void;
  addToCollection: (cardId: string) => void;
  removeFromCollection: (cardId: string) => void;
}
```

**New Interface (v1.1):**
```typescript
interface CollectionHook {
  // EVOLVED: cardQuantities replaces ownedCards
  cardQuantities: Record<string, number>;
  
  // BACKWARD COMPAT: ownedCards computed from quantities
  ownedCards: Record<string, boolean>; // derived: qty > 0
  
  // ENHANCED: quantity-aware methods
  getQuantity: (cardId: string) => number;
  setQuantity: (cardId: string, quantity: number) => void;
  incrementQuantity: (cardId: string) => void;
  decrementQuantity: (cardId: string) => void;
  
  // PRESERVED: boolean ownership methods (now wrappers)
  isOwned: (cardId: string) => boolean; // qty > 0
  isInCollection: (cardId: string) => boolean; // alias
  toggleOwnership: (cardId: string) => void; // 0 ↔ 1
  addToCollection: (cardId: string) => void; // set qty = 1
  removeFromCollection: (cardId: string) => void; // set qty = 0
}
```

**Key Changes:**
- Store `cardQuantities` as source of truth
- Compute `ownedCards` as derived boolean map
- Preserve existing methods as wrappers (toggleOwnership → increment/decrement)
- Add new quantity methods

**Migration Strategy:**
```typescript
const getInitialState = (): CollectionState => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) return { version: 3, cardQuantities: {} };
  
  const parsed = JSON.parse(stored);
  
  // v3 schema (current)
  if (parsed.version === 3 && parsed.cardQuantities) {
    return parsed;
  }
  
  // v1 schema migration (boolean)
  if (parsed.version === 1 && parsed.ownedCards) {
    return {
      version: 3,
      cardQuantities: Object.fromEntries(
        Object.entries(parsed.ownedCards)
          .filter(([_, owned]) => owned) // only migrate owned cards
          .map(([cardId, _]) => [cardId, 1]) // true → quantity 1
      ),
    };
  }
  
  // Unknown version → fresh state
  return { version: 3, cardQuantities: {} };
};
```

#### 2. **components/CardGrid.tsx** (MODIFY - UI Integration Point)

**Current Interaction:**
```typescript
// v1.0: Click card → toggle boolean
<Card onClick={() => toggleOwnership(card.id)}>
  {isOwned(card.id) && <CheckIcon />}
</Card>
```

**New Interaction (v1.1):**
```typescript
// v1.1: Quantity controls + click-to-increment
<Card onClick={() => incrementQuantity(card.id)}>
  {getQuantity(card.id) > 0 && (
    <Badge>{getQuantity(card.id)}</Badge>
  )}
  <QuantityControls
    quantity={getQuantity(card.id)}
    onIncrement={() => incrementQuantity(card.id)}
    onDecrement={() => decrementQuantity(card.id)}
    onSet={(qty) => setQuantity(card.id, qty)}
  />
</Card>
```

**Component Changes:**
- Add quantity badge overlay (shows count if > 0)
- Add increment/decrement buttons (+ / -)
- Add manual input field (click badge → enter number)
- Preserve existing ownership filter (owned = qty > 0)

**Layout Strategy:**
```
┌─────────────────────┐
│   [Card Image]      │
│                     │
│   ┌─────────────┐   │ ← Quantity Badge (top-right corner)
│   │    ×3       │   │
│   └─────────────┘   │
│                     │
│   ┌─────────────┐   │ ← Quantity Controls (hover/always visible)
│   │  [-] [3] [+]│   │
│   └─────────────┘   │
└─────────────────────┘
```

#### 3. **lib/collection.ts** Stats Helpers (MODIFY)

**Current Stats:**
```typescript
export interface CompletionStats {
  owned: number;     // count of owned cards
  missing: number;   // count of missing cards
  total: number;     // total cards in set
  percentage: number; // owned / total * 100
}
```

**Enhanced Stats (v1.1):**
```typescript
export interface CompletionStats {
  owned: number;      // count of cards with qty > 0
  missing: number;    // count of cards with qty === 0
  total: number;      // total cards in set
  percentage: number; // owned / total * 100
  
  // NEW: quantity-aware stats
  totalQuantity: number;     // sum of all quantities
  averageQuantity: number;   // avg qty per owned card
  duplicates: number;        // count of cards with qty > 1
}
```

**Migration Impact:**
- `useSetCompletion()` hook UNCHANGED (uses ownership = qty > 0)
- Add new `useSetQuantityStats()` hook for detailed metrics
- SetGrid progress bars UNCHANGED (still ownership-based)
- Stats footer can optionally show total quantity

#### 4. **components/CollectionStats.tsx** (OPTIONAL ENHANCE)

**Current View:**
```typescript
<div>
  <p>Total Cards Owned</p>
  <p>{totalCards}</p>
</div>
```

**Enhanced View (v1.1):**
```typescript
<div>
  <p>Unique Cards Owned</p>
  <p>{totalCards}</p>
  <p>Total Cards (with duplicates)</p>
  <p>{totalQuantity}</p>
  <p>Average per Card</p>
  <p>{averageQuantity.toFixed(1)}×</p>
</div>
```

#### 5. **SetGrid.tsx** (NO CHANGE - Read-Only Consumer)

**Impact:** None required. SetGrid computes completion from `ownedCards` which is derived from quantities. Progress bars work unchanged.

**Rationale:** Set completion is based on "do I own this card?" not "how many do I own?" Quantity is a card-level detail.

### Modified Component Boundaries

| Component | v1.0 Responsibility | v1.1 Changes |
|-----------|---------------------|--------------|
| **SetGrid** | Display sets + progress | NONE (uses derived ownedCards) |
| **CardGrid** | Ownership toggle | ADD: Quantity controls UI |
| **CollectionView** | Show owned cards | OPTIONAL: Show quantities |
| **Stats Footer** | Owned/missing/% | OPTIONAL: Add total quantity |
| **useCollection** | Boolean ownership | CORE: Quantity storage + migration |
| **TCGdex Hooks** | Fetch data | NONE |

## Data Flow Changes

### v1.0 Ownership Toggle Flow

```
User clicks card
    ↓
CardGrid.onClick → toggleOwnership(cardId)
    ↓
useCollection.toggleOwnership()
    ↓
setCollection({ ...prev, ownedCards: { ...prev.ownedCards, [cardId]: !prev[cardId] }})
    ↓
useEffect → localStorage.setItem('pokemon-collection-v2', JSON.stringify(collection))
    ↓
SetGrid re-renders (progress bar updates)
Stats footer re-renders (counts update)
```

### v1.1 Quantity Increment Flow

```
User clicks + button
    ↓
CardGrid.onIncrement → incrementQuantity(cardId)
    ↓
useCollection.incrementQuantity()
    ↓
setCollection({ ...prev, cardQuantities: { 
  ...prev.cardQuantities, 
  [cardId]: (prev.cardQuantities[cardId] || 0) + 1 
}})
    ↓
useEffect → localStorage.setItem('pokemon-collection-v2', JSON.stringify(collection))
    ↓
CardGrid re-renders (badge shows new quantity)
SetGrid re-renders (progress unchanged unless 0→1 transition)
Stats footer re-renders (optional total quantity update)
```

### v1.1 Manual Quantity Set Flow

```
User clicks quantity badge → opens input
User types "5" → presses Enter
    ↓
CardGrid.onSet → setQuantity(cardId, 5)
    ↓
useCollection.setQuantity()
    ↓
Validate: qty >= 0, integer only
    ↓
setCollection({ ...prev, cardQuantities: { ...prev.cardQuantities, [cardId]: 5 }})
    ↓
localStorage persists
    ↓
UI updates with new quantity
```

## Migration Strategy

### Phase-Based Rollout

**Phase A: Data Layer Migration** (Minimal Risk)
1. Update `CollectionState` interface to v3 schema
2. Add migration logic in `getInitialState()`
3. Implement quantity methods in `useCollection`
4. Add derived `ownedCards` computed property
5. Run unit tests to verify migration logic

**Phase B: UI Integration** (Incremental Enhancement)
1. Add `QuantityControls` component (standalone, reusable)
2. Update CardGrid to show quantity badge
3. Add increment/decrement buttons
4. Preserve existing click-to-toggle as click-to-increment

**Phase C: Stats Enhancement** (Optional Polish)
1. Add `totalQuantity` to CompletionStats interface
2. Update stats footer to show total count
3. Add CollectionStats breakdown (unique vs total)

### Rollback Safety

**If quantity tracking needs to be reverted:**
1. Data is NOT lost (quantities persisted)
2. Revert `useCollection` to return boolean `ownedCards` only
3. Hide quantity controls in CardGrid
4. Collection continues working with ownership (qty > 0)

**Version 3 → Version 1 Downgrade:**
```typescript
// Convert v3 quantities back to v1 booleans
const downgradeToV1 = (v3State: CollectionState) => ({
  version: 1,
  ownedCards: Object.fromEntries(
    Object.entries(v3State.cardQuantities)
      .filter(([_, qty]) => qty > 0)
      .map(([cardId, _]) => [cardId, true])
  ),
});
```

### Testing Strategy

**Unit Tests (lib/collection.test.ts):**
```typescript
describe('Collection Migration', () => {
  it('migrates v1 boolean to v3 quantity', () => {
    const v1Data = { version: 1, ownedCards: { 'card-1': true, 'card-2': false }};
    localStorage.setItem('pokemon-collection-v2', JSON.stringify(v1Data));
    
    const { result } = renderHook(() => useCollection());
    
    expect(result.current.cardQuantities).toEqual({ 'card-1': 1 });
    expect(result.current.getQuantity('card-1')).toBe(1);
    expect(result.current.getQuantity('card-2')).toBe(0);
  });
  
  it('preserves backward compat - ownedCards derived from quantities', () => {
    const { result } = renderHook(() => useCollection());
    
    act(() => result.current.setQuantity('card-1', 3));
    
    expect(result.current.ownedCards['card-1']).toBe(true);
    expect(result.current.isOwned('card-1')).toBe(true);
  });
  
  it('toggleOwnership works as 0↔1 toggle', () => {
    const { result } = renderHook(() => useCollection());
    
    act(() => result.current.toggleOwnership('card-1'));
    expect(result.current.getQuantity('card-1')).toBe(1);
    
    act(() => result.current.toggleOwnership('card-1'));
    expect(result.current.getQuantity('card-1')).toBe(0);
  });
});
```

**Integration Tests:**
- CardGrid quantity controls increment/decrement correctly
- Stats footer reflects quantity changes
- SetGrid progress bar transitions on 0→1 and 1→0
- localStorage persists and reloads quantities correctly

**Smoke Tests:**
- Existing v1.0 users: Collection data migrates without loss
- New v1.1 users: Can set quantities from scratch
- Mixed interaction: Toggle + quantity buttons don't conflict

## Anti-Patterns to Avoid

### Anti-Pattern 1: Separate Quantity State Store

**What people might do:**
Create a new `useQuantities()` hook separate from `useCollection()`.

**Why it's wrong:**
- Two sources of truth (ownership vs quantity)
- Sync issues between boolean and numeric states
- Doubled localStorage writes
- Component complexity (must use both hooks)

**Do this instead:**
Evolve `useCollection` to store quantities, derive ownership.

### Anti-Pattern 2: Breaking Change Migration

**What people might do:**
Change `ownedCards` type from `Record<string, boolean>` to `Record<string, number>` directly.

**Why it's wrong:**
- Breaks all existing components using `ownedCards`
- Forces simultaneous migration of SetGrid, CardGrid, CollectionView
- Higher regression risk
- Loses backward compat with v1 data

**Do this instead:**
Add `cardQuantities` as new field, compute `ownedCards` as derived boolean map.

### Anti-Pattern 3: Quantity in Card Data Model

**What people might do:**
Add `quantity?: number` field to `PokemonCard` interface.

**Why it's wrong:**
- `PokemonCard` is canonical card data from TCGdex (read-only)
- Mixing API data with user collection data
- Breaks separation of concerns (data fetching vs state management)
- Makes card types inconsistent (some have qty, some don't)

**Do this instead:**
Keep quantity in `useCollection` hook, join by `cardId` at render time.

### Anti-Pattern 4: Eager UI Complexity

**What people might do:**
Add bulk quantity actions (e.g., "Set all commons to 4×") in v1.1.

**Why it's wrong:**
- Feature scope creep
- Adds UI complexity before validating basic quantity workflow
- Increases testing surface area
- May not match user needs (validate first)

**Do this instead:**
Ship increment/decrement/manual input first. Defer bulk actions to v1.2 if validated.

### Anti-Pattern 5: No Migration Fallback

**What people might do:**
Assume all users will cleanly migrate from v1 to v3.

**Why it's wrong:**
- Users may have corrupted localStorage
- Schema may have unknown versions from dev testing
- Migration bugs could cause data loss

**Do this instead:**
Handle all cases: v1 → v3, v3 → v3, unknown → fresh start with console warnings.

## Scaling Considerations

### Current Scale (v1.0)
- **Data size:** ~1KB per 100 owned cards (boolean map)
- **localStorage limit:** 5-10MB (browser-dependent)
- **Max collection:** ~50,000 cards before localStorage issues
- **Performance:** Instant (in-memory map lookups)

### v1.1 Scale Impact
- **Data size:** ~2KB per 100 owned cards (numeric quantities)
- **Increased by:** ~2× (number values larger than boolean)
- **Max collection:** ~25,000 cards before localStorage issues
- **Performance:** Still instant (quantity lookups same complexity)

### If Collection Grows Beyond localStorage

**Bottleneck:** localStorage quota exceeded (DOMException).

**Solution Path:**
1. **v1.1:** Stay with localStorage (sufficient for personal collections)
2. **v1.2:** Migrate to IndexedDB if localStorage errors detected
3. **v2.0:** Add optional cloud sync with backend (requires accounts)

**When to migrate:**
- User has >10,000 owned cards with quantities
- localStorage errors in console
- User requests multi-device sync

**For v1.1:** No scaling changes needed. Personal collections rarely exceed 5,000 cards.

## Build Order Recommendation

### Sequential Work Phases

**Phase 1: Data Foundation (Low Risk)**
```
1. Define v3 CollectionState interface
2. Implement migration logic (v1 → v3)
3. Add quantity methods to useCollection
4. Add derived ownedCards property
5. Write unit tests for migration + quantity operations
```

**Phase 2: UI Integration (Moderate Risk)**
```
6. Create QuantityControls component (isolated)
7. Add quantity badge to CardGrid card items
8. Wire increment/decrement buttons
9. Update CardGrid to use getQuantity()
10. Test CardGrid with quantity controls
```

**Phase 3: Stats Enhancement (Low Risk - Optional)**
```
11. Add totalQuantity to CompletionStats
12. Update stats footer to show total count
13. Add CollectionStats quantity breakdown
```

**Phase 4: Polish & Documentation (Low Risk)**
```
14. Add toast notifications for quantity changes
15. Document migration in CHANGELOG.md
16. Update README with quantity features
17. Run smoke tests on production build
```

### Dependency Graph

```
Migration Logic (1-2) → Quantity Methods (3-4) → Unit Tests (5)
                                 ↓
                     QuantityControls Component (6)
                                 ↓
                     CardGrid Integration (7-9) → Integration Tests (10)
                                 ↓
                     Stats Enhancement (11-13) — OPTIONAL
                                 ↓
                     Polish & Docs (14-17)
```

### Risk Assessment

| Phase | Risk Level | Mitigation |
|-------|------------|------------|
| Data Foundation | Low | Migration tested with v1 data samples; rollback possible |
| UI Integration | Medium | Increment changes in CardGrid; test ownership filter compatibility |
| Stats Enhancement | Low | Optional; no impact if deferred |
| Polish | Low | Non-functional improvements |

### Success Criteria

**Phase 1 Complete When:**
- [ ] v1 → v3 migration preserves all owned cards
- [ ] v3 state persists correctly to localStorage
- [ ] `ownedCards` derived property matches v1 behavior
- [ ] All useCollection unit tests pass

**Phase 2 Complete When:**
- [ ] User can increment/decrement card quantity
- [ ] Quantity badge displays correctly
- [ ] Ownership filter (owned/missing) still works
- [ ] SetGrid progress bars update on 0→1 transitions

**Phase 3 Complete When:**
- [ ] Stats footer shows total quantity (optional)
- [ ] CollectionStats shows unique vs total (optional)

**Phase 4 Complete When:**
- [ ] User-facing documentation updated
- [ ] Smoke tests pass on production build
- [ ] No console errors in browser

## Integration Checklist

### Pre-Implementation

- [x] Understand existing v1.0 architecture
- [x] Identify integration points (useCollection, CardGrid)
- [x] Define migration strategy (v1 → v3)
- [x] Plan backward compatibility (ownedCards derived)
- [x] Document data flow changes

### Implementation

- [ ] Update CollectionState interface (version 3)
- [ ] Implement v1→v3 migration in getInitialState()
- [ ] Add quantity methods (get, set, increment, decrement)
- [ ] Add ownedCards computed property
- [ ] Create QuantityControls component
- [ ] Update CardGrid with quantity UI
- [ ] Update stats calculations (optional totalQuantity)
- [ ] Write unit tests for migration + operations
- [ ] Write integration tests for CardGrid + stats

### Validation

- [ ] Smoke test: Migrate existing v1 collection
- [ ] Smoke test: Create new v3 collection
- [ ] Smoke test: Increment/decrement quantities
- [ ] Smoke test: Ownership filter with quantities
- [ ] Smoke test: SetGrid progress with quantities
- [ ] Manual test: localStorage persists correctly
- [ ] Manual test: Page reload preserves quantities

## Sources

**Confidence Level: HIGH**

This architecture research is based on:
- ✅ Direct codebase analysis of v1.0 shipped application
- ✅ Existing file structure: `src/lib/collection.ts`, `src/components/CardGrid.tsx`, `src/lib/api.ts`
- ✅ Existing data model: CollectionState v1 schema in localStorage
- ✅ Project context: `.planning/PROJECT.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`
- ✅ v1.0 requirements archive: `.planning/milestones/v1.0-REQUIREMENTS.md`
- ✅ Existing patterns: Hook-based state, localStorage persistence, component boundaries

**No external sources required** — this is brownfield integration research based on existing codebase analysis.

**Verification Method:** Direct file inspection and trace of data flow through components.

---

*Architecture research for: Pokemon TCG Collection Tracker v1.1 Quantity Tracking*
*Researched: 2026-03-21*
*Confidence: HIGH (direct codebase analysis)*
