# Technology Stack — Quantity Tracking Addition

**Project:** Pokemon TCG Collection Tracker v1.1
**Milestone:** Quantity/Duplicate Tracking
**Researched:** 2024-12-19
**Confidence:** HIGH

## Executive Summary

**No new libraries required.** Quantity tracking leverages existing React+TypeScript+Vite+shadcn/ui+localStorage stack with schema migration pattern already proven in v1.0 (`pokemon-collection-v2` storage key migration).

**Why no additions needed:**
- UI: Existing shadcn/ui components (Input, Button, Popover) handle quantity controls
- State: React hooks pattern from `useCollection` extends cleanly to quantity data
- Persistence: Existing localStorage utilities support versioned schema migration
- Validation: Existing Zod v3.23.8 handles quantity constraints
- Testing: Existing Vitest 4.1.0 + Testing Library setup covers new behaviors

**Integration strategy:** Extend `CollectionState` interface from boolean flags to `{ owned: boolean, quantity: number }` shape with backward-compatible migration from v2 → v3 schema.

---

## Current Stack (No Changes)

### Core Framework
| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| React | 18.3.1 | UI framework | ✅ Keep |
| TypeScript | 5.5.3 | Type safety | ✅ Keep |
| Vite | 5.4.8 | Build tooling | ✅ Keep |

### UI Components
| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| shadcn/ui | Latest | Component library | ✅ Keep |
| Radix UI | 1.x (various) | Primitive components | ✅ Keep |
| Lucide React | 0.446.0 | Icons | ✅ Keep |
| Tailwind CSS | 3.4.13 | Styling | ✅ Keep |

### Data & State
| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| @tcgdex/sdk | 2.7.1 | Pokemon card data | ✅ Keep |
| Zod | 3.23.8 | Runtime validation | ✅ Keep |
| localStorage | Native | Persistence | ✅ Keep |

### Testing
| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| Vitest | 4.1.0 | Test runner | ✅ Keep |
| @testing-library/react | 16.3.2 | React testing | ✅ Keep |
| @testing-library/user-event | 14.6.1 | User interaction | ✅ Keep |
| happy-dom | 20.8.4 | DOM environment | ✅ Keep |

---

## Quantity Feature Stack Decisions

### 1. UI Controls for Quantity Input

**Decision:** Use existing shadcn/ui `Input` component with `type="number"` + custom increment/decrement buttons

**Why:**
- shadcn/ui Button + Input already in package.json
- No need for complex number spinners (simple +/- buttons are clearer for card counting)
- Lucide icons (`Plus`, `Minus`) provide visual affordance
- Existing form validation hooks (`react-hook-form` 7.53.0 + `@hookform/resolvers` 3.9.0) available if complex validation needed

**Alternative considered:** Radix Slider component
- **Rejected:** Sliders poor UX for precise counts (1 vs 10 vs 100 cards)
- Numeric input + buttons allows both quick increment and direct entry

**Integration:**
```typescript
// Leverage existing Button + Input from shadcn
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// Quantity control pattern
<div className="flex items-center gap-2">
  <Button size="icon" onClick={() => decrement(cardId)}>
    <Minus className="h-4 w-4" />
  </Button>
  <Input 
    type="number" 
    min="0" 
    value={quantity} 
    onChange={(e) => setQuantity(cardId, parseInt(e.target.value))}
    className="w-16 text-center"
  />
  <Button size="icon" onClick={() => increment(cardId)}>
    <Plus className="h-4 w-4" />
  </Button>
</div>
```

---

### 2. Data Validation

**Decision:** Use existing Zod 3.23.8 for quantity constraints

**Why:**
- Already in dependencies (3.23.8)
- Validates quantity bounds (0 ≤ quantity ≤ 999)
- Ensures integer values (no decimals)
- Integrates with react-hook-form for form-based inputs

**Validation schema:**
```typescript
import { z } from 'zod';

export const quantitySchema = z.object({
  quantity: z.number().int().min(0).max(999)
});

export const collectionCardSchema = z.object({
  owned: z.boolean(),
  quantity: z.number().int().min(0).max(999).default(0)
});
```

**Alternative considered:** Manual validation
- **Rejected:** Zod already present, provides better error messages, composable

---

### 3. State Management

**Decision:** Extend existing `useCollection` hook pattern with quantity support

**Why:**
- Current `useCollection` hook works well (no reported issues in v1.0)
- Minimal changes: `Record<string, boolean>` → `Record<string, { owned: boolean, quantity: number }>`
- Preserves local-first state management approach
- No need for Redux/Zustand (single collection context sufficient)

**Migration strategy:**
```typescript
// Extend CollectionState interface
interface CollectionState {
  version: 3; // Bump from v2 → v3
  cards: Record<string, CardCollection>; // Renamed from ownedCards
}

interface CardCollection {
  owned: boolean;
  quantity: number;
}

// Backward-compatible migration
const getInitialState = (): CollectionState => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    const parsed = JSON.parse(stored);
    
    // Migrate v2 → v3
    if (parsed.version === 2 && parsed.ownedCards) {
      return {
        version: 3,
        cards: Object.entries(parsed.ownedCards).reduce((acc, [id, owned]) => {
          acc[id] = { owned: !!owned, quantity: owned ? 1 : 0 };
          return acc;
        }, {} as Record<string, CardCollection>)
      };
    }
    
    if (parsed.version === 3) return parsed;
  }
  
  return { version: 3, cards: {} };
};
```

**Alternative considered:** Separate quantity store
- **Rejected:** Would require syncing two stores, complicates ownership logic

---

### 4. LocalStorage Persistence

**Decision:** Continue using native localStorage with schema versioning

**Why:**
- Current approach proven reliable in v1.0
- Schema versioning pattern (`version: 3`) supports backward-compatible migrations
- No quota issues reported (card data minimal, ~KB per set)
- Personal-use scope doesn't require cloud sync

**Schema migration pattern:**
```typescript
const STORAGE_KEY = 'pokemon-collection-v3'; // New key for v1.1

// Or reuse existing key with version bump
const STORAGE_KEY = 'pokemon-collection'; // Unified key, version in data
```

**Recommendation:** Reuse existing `pokemon-collection-v2` key, bump version field to `3`
- **Why:** Single storage key simplifies cleanup, version field handles migration
- **Migration:** v2 → v3 happens on first load, v2 data preserved until overwrite

**Alternative considered:** IndexedDB
- **Rejected:** Overkill for simple key-value storage, adds complexity
- **When to revisit:** If storing >5MB data (e.g., card images, deck snapshots)

**Quota management:**
```typescript
// Existing quota error handling in useCollection - no changes needed
catch (e) {
  if (e instanceof DOMException && e.name === 'QuotaExceededError') {
    console.error('localStorage quota exceeded');
    // Future: Implement cleanup (e.g., remove zero-quantity entries)
  }
}
```

---

### 5. Testing Utilities

**Decision:** Use existing Vitest + Testing Library setup, no additions

**Why:**
- Vitest 4.1.0 supports React hooks testing
- `@testing-library/user-event` 14.6.1 simulates increment/decrement clicks
- happy-dom 20.8.4 provides localStorage mock automatically
- Existing test pattern in `CardGrid.test.tsx` extends to quantity tests

**Test coverage areas:**
1. **Quantity controls:** Increment, decrement, direct input
2. **Bounds validation:** 0 ≤ quantity ≤ 999
3. **Stats computation:** Owned count, total quantity, set completion
4. **Persistence:** Save/load quantity data, schema migration v2 → v3
5. **Regression:** Boolean ownership behavior preserved

**Example test pattern:**
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CardGrid } from '@/components/CardGrid';

test('increments card quantity', async () => {
  const user = userEvent.setup();
  render(<CardGrid cards={mockCards} />);
  
  const incrementBtn = screen.getByLabelText('Increment quantity');
  await user.click(incrementBtn);
  
  expect(screen.getByDisplayValue('1')).toBeInTheDocument();
});

test('migrates v2 boolean data to v3 quantity', () => {
  localStorage.setItem('pokemon-collection-v2', JSON.stringify({
    version: 2,
    ownedCards: { 'card-1': true, 'card-2': false }
  }));
  
  const { result } = renderHook(() => useCollection());
  
  expect(result.current.getQuantity('card-1')).toBe(1);
  expect(result.current.getQuantity('card-2')).toBe(0);
});
```

**Alternative considered:** Playwright for E2E
- **Rejected:** Unit tests sufficient for localStorage + state logic
- **When to revisit:** Multi-page workflows, complex user journeys

---

### 6. Component Library (shadcn/ui)

**Decision:** No new shadcn components required

**Components sufficient for quantity UI:**
- ✅ `Button` — Increment/decrement actions
- ✅ `Input` — Direct quantity entry (type="number")
- ✅ `Popover` — Quantity editor in card hover/modal (if needed)
- ✅ `Tooltip` — Explain quantity controls
- ✅ `Badge` — Display quantity count on card thumbnail

**Existing Radix primitives cover all interaction needs:**
- `@radix-ui/react-popover` — Inline quantity editor
- `@radix-ui/react-tooltip` — Help text
- `@radix-ui/react-label` — Accessible labels

**Alternative considered:** Add `NumberInput` or `Stepper` component
- **Rejected:** Custom Button + Input composition simpler, more flexible
- No need for third-party spinners (e.g., `react-number-format`)

---

## What NOT to Add

| Library | Why NOT | What to Use Instead |
|---------|---------|-------------------|
| Immer | Overkill for flat state shape | Native spread operators |
| Redux Toolkit | Single collection context sufficient | Existing `useCollection` hook |
| React Query | No server data fetching (localStorage only) | React `useState` + `useEffect` |
| Formik | Simple increment/decrement, not forms | Direct event handlers |
| lodash | Native JS sufficient for quantity math | `Array.reduce`, `Object.entries` |
| date-fns extras | Already have 3.6.0, no new date logic | Existing date-fns install |
| react-number-format | Overcomplicated for integer input | Native `<Input type="number">` |
| zustand | useState + context sufficient | Existing hooks pattern |

---

## Migration & Integration Points

### 1. Schema Migration (v2 → v3)

**Current schema (v1.0):**
```typescript
interface CollectionState {
  version: 2;
  ownedCards: Record<string, boolean>;
}
```

**New schema (v1.1):**
```typescript
interface CollectionState {
  version: 3;
  cards: Record<string, CardCollection>;
}

interface CardCollection {
  owned: boolean;
  quantity: number;
}
```

**Migration logic:**
```typescript
// On first load with v2 data
if (parsed.version === 2) {
  return {
    version: 3,
    cards: Object.entries(parsed.ownedCards).reduce((acc, [id, owned]) => {
      acc[id] = { owned: !!owned, quantity: owned ? 1 : 0 };
      return acc;
    }, {})
  };
}
```

**Backward compatibility:**
- ✅ v2 data automatically migrates to v3 on first load
- ✅ v1.0 boolean ownership behavior preserved (owned = true → quantity = 1)
- ✅ No data loss (old `ownedCards` consumed into new `cards` structure)

---

### 2. Collection Hook API Extension

**Current API:**
```typescript
const { isOwned, toggleOwnership } = useCollection();
```

**Extended API:**
```typescript
const {
  isOwned,              // Existing: boolean check
  toggleOwnership,      // Existing: flip owned state
  getQuantity,          // New: get current quantity
  setQuantity,          // New: set absolute quantity
  incrementQuantity,    // New: quantity++
  decrementQuantity,    // New: quantity--
} = useCollection();
```

**Implementation:**
```typescript
const getQuantity = (cardId: string): number => {
  return collection.cards[cardId]?.quantity || 0;
};

const setQuantity = (cardId: string, quantity: number): void => {
  const validQuantity = Math.max(0, Math.min(999, quantity));
  setCollection(prev => ({
    ...prev,
    cards: {
      ...prev.cards,
      [cardId]: {
        owned: validQuantity > 0,
        quantity: validQuantity
      }
    }
  }));
};

const incrementQuantity = (cardId: string): void => {
  const current = getQuantity(cardId);
  setQuantity(cardId, current + 1);
};

const decrementQuantity = (cardId: string): void => {
  const current = getQuantity(cardId);
  setQuantity(cardId, Math.max(0, current - 1));
};
```

**Backward compatibility:**
- `toggleOwnership` preserved: sets `owned: true, quantity: 1` or `owned: false, quantity: 0`
- `isOwned` preserved: returns `cards[cardId]?.owned || false`

---

### 3. Stats Computation Updates

**Current stats (v1.0):**
```typescript
interface CompletionStats {
  owned: number;        // Count of owned cards
  missing: number;      // Count of missing cards
  total: number;        // Total cards in set
  percentage: number;   // Completion percentage
}
```

**Extended stats (v1.1):**
```typescript
interface CompletionStats {
  owned: number;        // Count of unique owned cards
  missing: number;      // Count of missing cards
  total: number;        // Total unique cards in set
  percentage: number;   // Completion percentage
  totalQuantity: number; // NEW: Sum of all card quantities
  duplicates: number;    // NEW: totalQuantity - owned
}
```

**Implementation:**
```typescript
export function useSetCompletion(
  setCardIds: string[],
  cards: Record<string, CardCollection>
): CompletionStats {
  return useMemo(() => {
    const total = setCardIds.length;
    const owned = setCardIds.filter(id => cards[id]?.owned).length;
    const missing = total - owned;
    const percentage = total > 0 ? (owned / total) * 100 : 0;
    
    // NEW: Calculate total quantity and duplicates
    const totalQuantity = setCardIds.reduce((sum, id) => {
      return sum + (cards[id]?.quantity || 0);
    }, 0);
    const duplicates = totalQuantity - owned;
    
    return { owned, missing, total, percentage, totalQuantity, duplicates };
  }, [setCardIds, cards]);
}
```

---

### 4. Component Integration Points

**CardGrid.tsx updates:**
- Add quantity badge overlay on card thumbnails
- Add increment/decrement buttons on hover or in card detail modal
- Update click behavior: checkbox for ownership, +/- for quantity

**CollectionStats.tsx updates:**
- Add "Total Cards: X" row (sum of quantities)
- Add "Duplicates: X" row (totalQuantity - owned)
- Preserve existing "Owned: X / Y" and completion % display

**CardDetail.tsx updates:**
- Add quantity input field in card detail view
- Show quantity history (optional, future enhancement)

---

## Testing Strategy

### Unit Tests (Vitest + Testing Library)

**Priority 1: State management**
- ✅ `useCollection` hook quantity methods
- ✅ Schema migration v2 → v3
- ✅ LocalStorage persistence roundtrip
- ✅ Validation bounds (0 ≤ quantity ≤ 999)

**Priority 2: Component behavior**
- ✅ Increment/decrement buttons
- ✅ Direct quantity input
- ✅ Stats recalculation
- ✅ Quantity badge rendering

**Priority 3: Regression**
- ✅ Boolean ownership preserved
- ✅ Existing tests pass with new schema
- ✅ v1.0 data migrates without loss

**Test utilities:**
```typescript
// Mock localStorage for testing
beforeEach(() => {
  localStorage.clear();
});

// Helper to setup v2 data for migration tests
const setupV2Data = (data: Record<string, boolean>) => {
  localStorage.setItem('pokemon-collection-v2', JSON.stringify({
    version: 2,
    ownedCards: data
  }));
};
```

### Integration Tests

**Manual smoke tests (checklist):**
- [ ] Load app with v2 data → v3 migration successful
- [ ] Increment card quantity → persists on refresh
- [ ] Set quantity to 0 → card shows as not owned
- [ ] Set quantity to 999 → max enforced
- [ ] Stats show correct owned vs total quantity
- [ ] Existing v1.0 features still work (filters, search, set browsing)

---

## Performance Considerations

### LocalStorage Efficiency

**Current data size (v1.0):**
- ~200 cards per set × ~100 sets = 20,000 cards max
- Boolean flags: `20,000 * 2 bytes = 40 KB`

**New data size (v1.1):**
- Card object: `{ owned: boolean, quantity: number }`
- JSON size: `~30 bytes per card` (with key)
- Max storage: `20,000 * 30 bytes = 600 KB`

**localStorage limit:** 5-10 MB (browser dependent)
**Headroom:** ~94% free (600 KB / 5 MB)

**Conclusion:** No performance concerns, no optimizations needed

**Future optimization (if needed):**
- Compress zero-quantity entries (don't store if quantity = 0)
- Use IndexedDB for >1M cards (not likely in Pokemon TCG)

---

## Installation & Setup

**No new dependencies required.**

All quantity features use existing stack:

```bash
# Verify current dependencies (already installed)
npm list react typescript vite zod vitest

# No additional installs needed for quantity tracking
```

**Configuration updates:** None required

**Environment variables:** None required

---

## Rollback & Compatibility

### Version Compatibility

| App Version | Schema Version | Compatibility |
|-------------|----------------|---------------|
| v1.0 | v2 (boolean) | ✅ Reads v2, writes v2 |
| v1.1 | v3 (quantity) | ✅ Reads v2+v3, writes v3 |
| v1.1 → v1.0 | Rollback risk | ⚠️ v3 data unreadable by v1.0 |

**Rollback strategy:**
- Keep v2 schema reader in v1.1 code (migration only, never write v2)
- If rollback needed: Export collection, reinstall v1.0, re-import as boolean flags

**Data loss scenarios:**
- v1.1 → v1.0 rollback: Quantity data lost (falls back to owned = true/false)
- localStorage cleared: All data lost (expected, local-first design)

**Mitigation:**
- Export/import feature (future milestone) provides backup
- Cloud sync (out of scope) would preserve data across devices

---

## Open Questions & Future Considerations

### Resolved (No Action Needed)
- ✅ **Input component?** → Use existing shadcn Input + Button
- ✅ **State management?** → Extend existing useCollection hook
- ✅ **Validation?** → Use existing Zod
- ✅ **Testing?** → Use existing Vitest + Testing Library
- ✅ **Migration?** → v2 → v3 schema version bump

### Deferred to Future Milestones
- ⏸️ **Bulk quantity editing** (e.g., set all to 0) → v1.2+
- ⏸️ **Quantity history** (track changes over time) → v1.3+
- ⏸️ **Export/import with quantities** → v1.2+
- ⏸️ **IndexedDB migration** → Only if >5MB data

### Not Applicable
- ❌ **Cloud sync** → Out of scope (personal-use app)
- ❌ **Real-time collaboration** → Not needed
- ❌ **Optimistic updates** → localStorage is synchronous

---

## Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| UI Components | **HIGH** | Existing shadcn/ui covers all needs, no gaps found |
| State Management | **HIGH** | React hooks pattern proven in v1.0, extends cleanly |
| Persistence | **HIGH** | localStorage + versioning pattern validated in v1.0 |
| Testing | **HIGH** | Vitest + Testing Library sufficient, no new tools needed |
| Integration | **HIGH** | Minimal API surface changes, backward compatible |
| Performance | **HIGH** | 600KB < 5MB limit, no optimization needed |

**Overall confidence:** HIGH

**Validation sources:**
- ✅ Existing package.json dependencies verified
- ✅ Current v1.0 code patterns reviewed (collection.ts, types.ts)
- ✅ shadcn/ui component catalog cross-checked
- ✅ localStorage quota limits researched (MDN Web Docs)
- ✅ Vitest React hooks testing capabilities verified

**No external research required** — all decisions based on existing codebase and proven patterns from v1.0 execution.

---

## Summary

**Stack decision: No new dependencies.**

Quantity tracking is a **pure feature extension** of existing v1.0 stack:
- React hooks → Add quantity methods to `useCollection`
- TypeScript → Extend `CollectionState` interface
- Zod → Validate quantity bounds
- shadcn/ui → Compose Button + Input for controls
- localStorage → Bump schema version v2 → v3
- Vitest → Test quantity logic + migration

**Risk level:** Low (no new dependencies, no breaking changes)

**Implementation readiness:** High (all tools present, patterns validated)

**Next steps:**
1. Extend `CollectionState` type definition
2. Implement schema migration v2 → v3
3. Add quantity methods to `useCollection` hook
4. Build quantity UI controls in CardGrid/CardDetail
5. Update stats computation for totalQuantity + duplicates
6. Write unit tests for new quantity behaviors
7. Run regression tests to ensure v1.0 features preserved

---

*Research completed: 2024-12-19*  
*Researcher: Project Research Agent (Phase 6)*  
*Downstream: Roadmap creation for v1.1 Quantity Tracking milestone*
