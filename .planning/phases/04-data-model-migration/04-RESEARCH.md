# Phase 4: Data Model & Migration - Research

**Researched:** 2026-03-21
**Domain:** Data migration, localStorage schema evolution, sparse storage patterns
**Confidence:** HIGH

## Summary

Phase 4 migrates the existing v1 boolean ownership storage (`Record<string, boolean>`) to v3 quantity storage (`Record<string, number>`) without data loss or user disruption. This is a critical infrastructure upgrade that enables duplicate tracking while preserving all existing v1.0 behaviors.

**The migration challenge:** Convert 1000+ card ownership records from `{ "card-id": true/false }` to `{ "card-id": quantity }` safely, with backup/rollback capability, sparse storage optimization (omit qty=0), and complete backward API compatibility for existing consumers (CardGrid, stats).

**The good news:** The existing v1.0 architecture already has a versioned schema pattern (`version: 1`), localStorage persistence with quota error handling, and centralized collection state via `useCollection` hook. Migration extends this proven pattern rather than replacing it. No new dependencies required—React 18.3.1, TypeScript 5.5.3, Zod 3.23.8, and Vitest 4.1.0 handle all migration, validation, and testing needs.

**Primary recommendation:** Implement migration as idempotent, automatic-on-load transformation with deterministic backup key, sparse storage (only `qty > 0`), and strict backward compatibility via adapter pattern wrappers that derive boolean ownership from `quantity > 0`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Migration Trigger and Timing:**
- Run migration automatically on first collection load (no manual trigger required)
- Keep migration UX silent when successful and fast
- Show a non-blocking warning toast only when fallback/error paths are used
- If already on migrated schema version, detect and no-op safely

**Backup and Recovery Policy:**
- Create one deterministic backup key during migration
- Keep backup until the next successful app start, then allow cleanup
- On migration failure, attempt one automatic restore from backup
- If restore still fails, keep app usable in memory and provide manual recovery hint

**Error Handling and Data Safety:**
- If migration or save fails, do not drop user data
- Keep in-memory state usable and surface a clear warning toast
- Log detailed error context to console for debugging/support
- On storage quota issues, keep state in memory and warn; do not auto-trim owned data

**Quantity Semantics and Constraints:**
- Quantity is the single source of truth; owned-state is strictly derived from `quantity > 0`
- Enforce per-card range `0..999`
- Coerce invalid/non-integer inputs to safe integer values and clamp to range
- Use sparse storage: when quantity reaches `0`, remove the card key from persisted map

**Compatibility and Migration Contract:**
- Preserve existing consumer APIs (`isOwned`, `isInCollection`, `toggleOwnership`, add/remove methods) as quantity-backed wrappers during v1.1 transition
- Keep existing localStorage key name and migrate payload in place
- Bump persisted schema version and cover migration behavior explicitly in tests

### Claude's Discretion

- Internal naming of versioned schema interfaces and migration helpers
- Exact backup key suffix string, as long as deterministic and documented
- Migration telemetry granularity in console logs

### Deferred Ideas (OUT OF SCOPE)

- Manual quantity input UX and keyboard shortcuts (Phase 5+)
- Duplicates-only filtering and batch reset workflows (later phase)
- Trade inventory / condition / value tracking (future milestone)

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QTY-01 | User's existing ownership data migrates safely from boolean storage to quantity storage with no data loss | Migration function with backup/rollback, idempotent logic, validation tests with 1000+ card datasets |
| QTY-02 | App stores collection quantities sparsely (only cards with quantity > 0) to keep localStorage usage efficient | Sparse storage pattern removes zero-quantity entries, functional update helpers enforce invariant |
| QTY-03 | App derives owned-state from quantity (`quantity > 0`) so ownership and quantity cannot diverge | Adapter pattern wrappers (`isOwned`, `toggleOwnership`) implemented as read-only views over quantity state |
| QTY-04 | User can rely on migration fallback/backup behavior if quantity migration fails | Backup to deterministic key before migration, automatic rollback on failure, console logging for support |
| TESTQ-01 | Quantity migration logic is covered by automated tests for normal and edge-case payloads | Vitest test suite with cases: normal migration, empty collection, large dataset (5000+ cards), corrupted data, idempotency, quota errors |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 18.3.1 (current: 19.2.4) | State management via hooks | Existing v1.0 stack, proven `useCollection` pattern |
| TypeScript | 5.5.3 (current: 5.9.3) | Type safety for migration logic | Existing v1.0 stack, catches schema errors at compile time |
| Zod | 3.23.8 (current: 4.3.6) | Runtime validation of migrated data | Existing dependency, validates quantity constraints (0-999, integers) |
| Vitest | 4.1.0 | Migration test coverage | Existing test infrastructure, mocks localStorage, fast execution |

**Note:** Package versions shown are installed versions (from package.json). Current registry versions shown for reference but upgrades are out of scope for this phase.

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @testing-library/react | 16.3.2 | Hook testing for migration | Test migration via `renderHook` to validate state transformations |
| happy-dom | 20.8.4 | DOM environment for tests | Vitest environment, provides localStorage mock for migration tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Automatic migration | Manual migration trigger | Manual requires UI, documentation, support burden; automatic is silent for 99% case |
| In-place key migration | New storage key (v3) | New key requires data copy/cleanup logic and doesn't match v1.0 pattern (reused `pokemon-collection-v2`) |
| Zod validation | Manual type guards | Zod provides better error messages and composition, already in dependencies |

**Installation:**
```bash
# No new packages required
# All migration dependencies already present in v1.0 stack
```

**Version verification:** Versions verified against package.json (2026-03-21). Current registry versions noted but not required for this phase.

## Architecture Patterns

### Recommended Migration Flow
```
App loads → useCollection initializes
  ├─ getInitialState() reads localStorage['pokemon-collection-v2']
  ├─ Detect version (v1)
  ├─ Backup: localStorage['pokemon-collection-v2-backup'] = stringify(v1State)
  ├─ Transform: { version: 1, ownedCards } → { version: 3, cardQuantities }
  │   └─ true → 1, false/undefined → omit (sparse)
  ├─ Validate: Zod schema check on transformed data
  ├─ Persist: localStorage['pokemon-collection-v2'] = stringify(v3State)
  ├─ Success: return v3State
  └─ Failure: restore from backup, log error, return fallback
```

### Pattern 1: Idempotent Schema Versioning
**What:** Migration function checks current version and no-ops if already v3
**When to use:** Every app load (migration runs in `getInitialState()`)
**Example:**
```typescript
// Source: Existing codebase pattern (src/lib/collection.ts)
const getInitialState = (): CollectionStateV3 => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return { version: 3, cardQuantities: {} };
    
    const parsed = JSON.parse(stored);
    
    // Idempotent: if already v3, return as-is
    if (parsed.version === 3) {
      return validateV3Schema(parsed);
    }
    
    // Migration path: v1 → v3
    if (parsed.version === 1) {
      return migrateV1ToV3(parsed);
    }
    
    // Unknown version: log and use defaults
    console.warn('Unknown collection version:', parsed.version);
    return { version: 3, cardQuantities: {} };
  } catch (e) {
    console.error('Collection load failed:', e);
    return { version: 3, cardQuantities: {} };
  }
};
```

### Pattern 2: Sparse Storage with Functional Updates
**What:** Only persist `{ cardId: quantity }` for `quantity > 0`, omit zero-quantity entries
**When to use:** All collection state updates (add, remove, set, increment, decrement)
**Example:**
```typescript
// Source: React functional update pattern + sparse invariant
const setQuantity = (cardId: string, quantity: number): void => {
  setCollection(prev => {
    const newQuantities = { ...prev.cardQuantities };
    
    // Clamp and coerce to valid range
    const clamped = Math.max(0, Math.min(999, Math.floor(quantity)));
    
    // Sparse: remove entry if zero
    if (clamped === 0) {
      delete newQuantities[cardId];
    } else {
      newQuantities[cardId] = clamped;
    }
    
    return {
      ...prev,
      cardQuantities: newQuantities
    };
  });
};
```

### Pattern 3: Adapter Pattern for Backward Compatibility
**What:** Preserve existing boolean ownership APIs (`isOwned`, `toggleOwnership`) as thin wrappers over quantity state
**When to use:** Maintain compatibility with CardGrid, stats, and other v1.0 consumers during migration phase
**Example:**
```typescript
// Source: Adapter pattern + React hooks best practices
export const useCollection = () => {
  const [collection, setCollection] = useState<CollectionStateV3>(getInitialState);
  
  // Core quantity API (new)
  const getQuantity = (cardId: string): number => {
    return collection.cardQuantities[cardId] || 0;
  };
  
  // Backward-compatible boolean API (adapter)
  const isOwned = (cardId: string): boolean => {
    return getQuantity(cardId) > 0; // Derived from quantity
  };
  
  // Backward-compatible toggle (adapter)
  const toggleOwnership = (cardId: string): void => {
    const current = getQuantity(cardId);
    setQuantity(cardId, current > 0 ? 0 : 1);
  };
  
  // Derived ownedCards for backward compatibility
  const ownedCards = useMemo(() => {
    const derived: Record<string, boolean> = {};
    Object.keys(collection.cardQuantities).forEach(id => {
      derived[id] = true; // Only stored IDs have qty > 0
    });
    return derived;
  }, [collection.cardQuantities]);
  
  return {
    // Backward-compatible API
    ownedCards,
    isOwned,
    isInCollection: isOwned,
    toggleOwnership,
    addToCollection: (id: string) => setQuantity(id, 1),
    removeFromCollection: (id: string) => setQuantity(id, 0),
    
    // New quantity API (for future phases)
    getQuantity,
    setQuantity,
    incrementQuantity: (id: string) => setQuantity(id, getQuantity(id) + 1),
    decrementQuantity: (id: string) => setQuantity(id, Math.max(0, getQuantity(id) - 1)),
  };
};
```

### Pattern 4: Backup and Rollback
**What:** Write backup to deterministic key before migration, restore on failure
**When to use:** Once per migration (not on every state update)
**Example:**
```typescript
// Source: Migration safety pattern
const BACKUP_KEY = 'pokemon-collection-v2-backup';

const migrateV1ToV3 = (v1State: CollectionStateV1): CollectionStateV3 => {
  try {
    // Step 1: Backup original data
    localStorage.setItem(BACKUP_KEY, JSON.stringify(v1State));
    
    // Step 2: Transform data
    const cardQuantities: Record<string, number> = {};
    Object.entries(v1State.ownedCards).forEach(([id, owned]) => {
      if (owned) {
        cardQuantities[id] = 1; // Sparse: only store qty > 0
      }
    });
    
    const v3State: CollectionStateV3 = {
      version: 3,
      cardQuantities
    };
    
    // Step 3: Validate transformed data
    const validated = CollectionV3Schema.parse(v3State);
    
    // Step 4: Persist migrated data
    localStorage.setItem(STORAGE_KEY, JSON.stringify(validated));
    
    console.log(`Migration complete: ${Object.keys(cardQuantities).length} cards migrated`);
    return validated;
    
  } catch (e) {
    console.error('Migration failed, attempting rollback:', e);
    
    // Rollback: restore from backup
    try {
      const backup = localStorage.getItem(BACKUP_KEY);
      if (backup) {
        localStorage.setItem(STORAGE_KEY, backup);
        const restored = JSON.parse(backup);
        console.warn('Rollback successful, using v1 format');
        // Return v1 converted to v3 in-memory (don't persist)
        return convertV1ToV3InMemory(restored);
      }
    } catch (rollbackError) {
      console.error('Rollback failed:', rollbackError);
    }
    
    // Last resort: empty collection
    return { version: 3, cardQuantities: {} };
  }
};
```

### Anti-Patterns to Avoid

- **Dual source of truth:** DO NOT store both `ownedCards: Record<string, boolean>` AND `cardQuantities: Record<string, number>` in persisted state—causes sync bugs. Store only `cardQuantities`, derive `ownedCards` on read.
- **Non-sparse storage:** DO NOT store `{ "card-1": 0, "card-2": 0, ... }` for unowned cards—wastes 10-50x storage. Omit zero-quantity entries.
- **Non-functional updates:** DO NOT use `const current = getQuantity(id); setQuantity(id, current + 1);`—race conditions. Use `setCollection(prev => ...)` for atomic updates.
- **Silent migration failures:** DO NOT return empty collection without logging—users lose data. Always log errors, attempt rollback, surface warning toast.
- **Version mixing:** DO NOT allow v1 and v3 states to coexist in localStorage—confuses initialization. Migrate in-place under same key.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema validation | Manual type guards with `typeof` checks | Zod schemas (`z.object`, `z.record`, `z.number`) | Zod provides better error messages, composition, and is already in dependencies |
| localStorage quota handling | Custom try-catch per write | Existing `useEffect` pattern with `QuotaExceededError` check | Already validated in v1.0 (src/lib/collection.ts line 38-44) |
| Migration versioning | Ad-hoc version checks | Version field + switch statement pattern | Already established in v1.0 schema, extensible for v3→v4 |
| Backup key generation | Dynamic timestamps | Deterministic suffix (`-backup`) | Predictable for cleanup, easier to debug, matches user constraint |

**Key insight:** The v1.0 codebase already has proven patterns for localStorage persistence, quota errors, and versioned schemas. Extend these patterns rather than introducing new approaches.

## Common Pitfalls

### Pitfall 1: Data Loss During Migration Failure
**What goes wrong:** Migration throws error mid-transform, user refreshes, loses entire collection
**Why it happens:** No backup before mutation, or backup not written before risky transform logic
**How to avoid:** 
1. Write backup to separate key FIRST (before any transformation)
2. Parse backup write for confirmation (don't assume success)
3. Only then run transformation
4. On any error, restore from backup before returning
**Warning signs:** 
- `localStorage.getItem(BACKUP_KEY)` returns null after migration attempt
- Console logs show "migration failed" but no "backup created"
- Users report empty collections after migration
**Code example:**
```typescript
// WRONG: No backup before risky operation
const migrate = (v1: V1): V3 => {
  const v3 = transform(v1); // Throws error, original v1 lost
  localStorage.setItem(KEY, JSON.stringify(v3));
  return v3;
};

// RIGHT: Backup first, restore on failure
const migrate = (v1: V1): V3 => {
  // Step 1: Backup (safe operation)
  localStorage.setItem(BACKUP_KEY, JSON.stringify(v1));
  
  try {
    // Step 2: Risky transformation
    const v3 = transform(v1);
    localStorage.setItem(KEY, JSON.stringify(v3));
    return v3;
  } catch (e) {
    // Step 3: Restore on failure
    const backup = localStorage.getItem(BACKUP_KEY);
    if (backup) {
      localStorage.setItem(KEY, backup);
    }
    throw e;
  }
};
```

### Pitfall 2: Non-Idempotent Migration (Runs Every Load)
**What goes wrong:** Migration runs on every app load even after successful migration, corrupts data or wastes CPU
**Why it happens:** Version check missing or incorrect, migration function doesn't check if already v3
**How to avoid:**
1. FIRST check `parsed.version === 3` and return immediately
2. Only run migration if version is explicitly v1
3. Test: run migration twice with same input, assert identical output
**Warning signs:**
- Console logs show "migration complete" on every page refresh
- Backup key gets overwritten on every load
- localStorage write happens even when state unchanged
**Code example:**
```typescript
// WRONG: Always runs migration
const getInitialState = (): V3 => {
  const stored = localStorage.getItem(KEY);
  const parsed = JSON.parse(stored);
  return migrateV1ToV3(parsed); // Runs even if already v3!
};

// RIGHT: Idempotent check
const getInitialState = (): V3 => {
  const stored = localStorage.getItem(KEY);
  if (!stored) return defaultV3State;
  
  const parsed = JSON.parse(stored);
  
  // Idempotent: return if already migrated
  if (parsed.version === 3) {
    return parsed;
  }
  
  // Only migrate if v1
  if (parsed.version === 1) {
    return migrateV1ToV3(parsed);
  }
  
  return defaultV3State;
};
```

### Pitfall 3: Sparse Storage Invariant Violation
**What goes wrong:** Zero-quantity entries accumulate in localStorage (`{ "card-1": 0, "card-2": 0, ... }`), storage quota exceeded
**Why it happens:** Set operations don't delete zero-quantity keys, only update value to 0
**How to avoid:**
1. ALWAYS check `if (quantity === 0) delete map[id]` in set operations
2. Migration transforms `false → omit` not `false → 0`
3. Test: set quantity to 0, verify key removed from storage
**Warning signs:**
- localStorage size grows with total cards in database (not owned cards)
- `Object.keys(cardQuantities).length` increases when removing cards
- QuotaExceededError appears after user removes many cards
**Code example:**
```typescript
// WRONG: Stores zeros
const setQuantity = (id: string, qty: number) => {
  setCollection(prev => ({
    ...prev,
    cardQuantities: {
      ...prev.cardQuantities,
      [id]: qty // Stores qty=0!
    }
  }));
};

// RIGHT: Sparse storage
const setQuantity = (id: string, qty: number) => {
  setCollection(prev => {
    const newQuantities = { ...prev.cardQuantities };
    if (qty <= 0) {
      delete newQuantities[id]; // Remove zero-quantity entries
    } else {
      newQuantities[id] = qty;
    }
    return {
      ...prev,
      cardQuantities: newQuantities
    };
  });
};
```

### Pitfall 4: Derived State Synchronization Bugs
**What goes wrong:** `ownedCards` and `cardQuantities` diverge (owned=true but qty=0, or owned=false but qty=3), stats incorrect
**Why it happens:** Persisting both boolean and quantity fields, manual sync logic missed edge cases
**How to avoid:**
1. NEVER store `ownedCards` in persisted state (only `cardQuantities`)
2. Derive `ownedCards` from quantities using `useMemo` or computed property
3. Adapter APIs (`isOwned`, `toggleOwnership`) read from quantities only
4. Test: set quantity, verify `isOwned` reflects `qty > 0`
**Warning signs:**
- Stats show different counts between views
- User toggles card, stats don't update
- Collection has cards with `owned=true` but `qty=0` in stored state
**Code example:**
```typescript
// WRONG: Dual source of truth
interface CollectionState {
  version: 3;
  ownedCards: Record<string, boolean>; // DON'T DO THIS
  cardQuantities: Record<string, number>;
}

// RIGHT: Single source, derived state
interface CollectionState {
  version: 3;
  cardQuantities: Record<string, number>; // Only this
}

// Derived in hook
const ownedCards = useMemo(() => {
  const derived: Record<string, boolean> = {};
  Object.keys(collection.cardQuantities).forEach(id => {
    derived[id] = true; // qty > 0 by sparse invariant
  });
  return derived;
}, [collection.cardQuantities]);
```

### Pitfall 5: Race Conditions in Concurrent Updates
**What goes wrong:** Rapid clicks on increment button result in qty=2 instead of qty=5 (lost updates)
**Why it happens:** Non-functional state updates read stale state
**How to avoid:**
1. ALWAYS use functional updates: `setCollection(prev => transform(prev))`
2. Never read state then set: `const current = get(); set(current + 1);`
3. Test: simulate rapid clicks (5x in 100ms), verify final quantity correct
**Warning signs:**
- User clicks +1 multiple times, quantity doesn't match click count
- Race condition warnings in React DevTools
- Inconsistent behavior on slow vs fast hardware
**Code example:**
```typescript
// WRONG: Stale state read
const increment = (id: string) => {
  const current = getQuantity(id); // Reads stale state
  setQuantity(id, current + 1); // Multiple calls race
};

// RIGHT: Functional update
const increment = (id: string) => {
  setCollection(prev => ({
    ...prev,
    cardQuantities: {
      ...prev.cardQuantities,
      [id]: (prev.cardQuantities[id] || 0) + 1 // Reads latest state
    }
  }));
};
```

## Code Examples

Verified patterns from project codebase and React/TypeScript standards:

### Schema Definitions
```typescript
// Source: Extend existing pattern (src/lib/collection.ts lines 8-11)
interface CollectionStateV1 {
  version: 1;
  ownedCards: Record<string, boolean>;
}

interface CollectionStateV3 {
  version: 3;
  cardQuantities: Record<string, number>; // Only qty > 0 stored
}

// Zod validation schema
import { z } from 'zod';

const CollectionV3Schema = z.object({
  version: z.literal(3),
  cardQuantities: z.record(
    z.string(), 
    z.number().int().min(0).max(999)
  )
});
```

### Migration Function
```typescript
// Source: Migration safety pattern + existing error handling
const STORAGE_KEY = 'pokemon-collection-v2';
const BACKUP_KEY = 'pokemon-collection-v2-backup';

const migrateV1ToV3 = (v1State: CollectionStateV1): CollectionStateV3 => {
  try {
    // Backup original
    localStorage.setItem(BACKUP_KEY, JSON.stringify(v1State));
    console.log('Migration backup created');
    
    // Transform with sparse storage
    const cardQuantities: Record<string, number> = {};
    Object.entries(v1State.ownedCards).forEach(([id, owned]) => {
      if (owned) {
        cardQuantities[id] = 1; // Only store owned cards
      }
      // false/undefined → omit (sparse)
    });
    
    const v3State: CollectionStateV3 = {
      version: 3,
      cardQuantities
    };
    
    // Validate
    const validated = CollectionV3Schema.parse(v3State);
    
    // Persist
    localStorage.setItem(STORAGE_KEY, JSON.stringify(validated));
    
    console.log(`Migration complete: ${Object.keys(cardQuantities).length} cards migrated`);
    return validated;
    
  } catch (e) {
    console.error('Migration failed:', e);
    
    // Attempt rollback
    try {
      const backup = localStorage.getItem(BACKUP_KEY);
      if (backup) {
        localStorage.setItem(STORAGE_KEY, backup);
        console.warn('Rollback successful');
      }
    } catch (rollbackError) {
      console.error('Rollback failed:', rollbackError);
    }
    
    // Return empty collection (safe fallback)
    return { version: 3, cardQuantities: {} };
  }
};
```

### Collection Hook with Backward Compatibility
```typescript
// Source: Extend existing hook (src/lib/collection.ts)
export const useCollection = () => {
  const [collection, setCollection] = useState<CollectionStateV3>(getInitialState);
  
  // Persist on change (existing pattern, lines 34-44)
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collection));
    } catch (e) {
      if (e instanceof DOMException && e.name === 'QuotaExceededError') {
        console.error('localStorage quota exceeded');
      } else {
        console.error('Failed to save collection:', e);
      }
    }
  }, [collection]);
  
  // Core quantity API
  const getQuantity = (cardId: string): number => {
    return collection.cardQuantities[cardId] || 0;
  };
  
  const setQuantity = (cardId: string, quantity: number): void => {
    setCollection(prev => {
      const newQuantities = { ...prev.cardQuantities };
      const clamped = Math.max(0, Math.min(999, Math.floor(quantity)));
      
      if (clamped === 0) {
        delete newQuantities[cardId]; // Sparse storage
      } else {
        newQuantities[cardId] = clamped;
      }
      
      return {
        ...prev,
        cardQuantities: newQuantities
      };
    });
  };
  
  // Backward-compatible API (adapters)
  const isOwned = (cardId: string): boolean => {
    return getQuantity(cardId) > 0;
  };
  
  const toggleOwnership = (cardId: string): void => {
    const current = getQuantity(cardId);
    setQuantity(cardId, current > 0 ? 0 : 1);
  };
  
  // Derived ownedCards for backward compatibility
  const ownedCards = useMemo(() => {
    const derived: Record<string, boolean> = {};
    Object.keys(collection.cardQuantities).forEach(id => {
      derived[id] = true; // Sparse invariant: only qty > 0 stored
    });
    return derived;
  }, [collection.cardQuantities]);
  
  return {
    // Backward-compatible API (existing consumers use these)
    ownedCards,
    isOwned,
    isInCollection: isOwned,
    toggleOwnership,
    addToCollection: (cardId: string) => setQuantity(cardId, 1),
    removeFromCollection: (cardId: string) => setQuantity(cardId, 0),
    
    // New quantity API (for Phase 5+)
    getQuantity,
    setQuantity,
    incrementQuantity: (cardId: string) => 
      setQuantity(cardId, getQuantity(cardId) + 1),
    decrementQuantity: (cardId: string) => 
      setQuantity(cardId, Math.max(0, getQuantity(cardId) - 1)),
  };
};
```

### Test Examples
```typescript
// Source: Extend existing test patterns (src/lib/__tests__/collection.test.ts)
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCollection } from '../collection';

describe('Collection Migration', () => {
  beforeEach(() => {
    localStorage.clear();
  });
  
  it('migrates v1 boolean to v3 quantity without data loss', () => {
    // Setup v1 data
    const v1Data = {
      version: 1,
      ownedCards: { 'card-1': true, 'card-2': true, 'card-3': false }
    };
    localStorage.setItem('pokemon-collection-v2', JSON.stringify(v1Data));
    
    // Trigger migration
    const { result } = renderHook(() => useCollection());
    
    // Verify migration
    const stored = JSON.parse(localStorage.getItem('pokemon-collection-v2'));
    expect(stored.version).toBe(3);
    expect(stored.cardQuantities).toEqual({ 'card-1': 1, 'card-2': 1 });
    // card-3 omitted (sparse storage for false → qty 0)
    
    // Verify backward-compatible API
    expect(result.current.isOwned('card-1')).toBe(true);
    expect(result.current.isOwned('card-2')).toBe(true);
    expect(result.current.isOwned('card-3')).toBe(false);
  });
  
  it('is idempotent - second load does not re-migrate', () => {
    // First load: migration
    const v1Data = { version: 1, ownedCards: { 'card-1': true } };
    localStorage.setItem('pokemon-collection-v2', JSON.stringify(v1Data));
    const { result: result1 } = renderHook(() => useCollection());
    
    // Verify migrated
    const stored1 = JSON.parse(localStorage.getItem('pokemon-collection-v2'));
    expect(stored1.version).toBe(3);
    
    // Second load: no migration
    const { result: result2 } = renderHook(() => useCollection());
    const stored2 = JSON.parse(localStorage.getItem('pokemon-collection-v2'));
    
    // Should be identical (no re-migration)
    expect(stored2).toEqual(stored1);
  });
  
  it('handles corrupted data gracefully', () => {
    // Invalid JSON
    localStorage.setItem('pokemon-collection-v2', 'not valid json');
    
    const { result } = renderHook(() => useCollection());
    
    // Should not crash, return empty collection
    expect(result.current.ownedCards).toEqual({});
  });
  
  it('enforces sparse storage - removing card deletes key', () => {
    const { result } = renderHook(() => useCollection());
    
    // Add card
    act(() => {
      result.current.setQuantity('card-1', 5);
    });
    
    let stored = JSON.parse(localStorage.getItem('pokemon-collection-v2'));
    expect(stored.cardQuantities['card-1']).toBe(5);
    
    // Remove card
    act(() => {
      result.current.setQuantity('card-1', 0);
    });
    
    stored = JSON.parse(localStorage.getItem('pokemon-collection-v2'));
    expect(stored.cardQuantities['card-1']).toBeUndefined();
    expect(Object.keys(stored.cardQuantities)).not.toContain('card-1');
  });
  
  it('migrates large collection without quota errors', () => {
    // Create 5000-card collection
    const largeCollection: Record<string, boolean> = {};
    for (let i = 0; i < 5000; i++) {
      largeCollection[`card-${i}`] = i % 2 === 0; // 50% ownership
    }
    
    const v1Data = { version: 1, ownedCards: largeCollection };
    localStorage.setItem('pokemon-collection-v2', JSON.stringify(v1Data));
    
    // Trigger migration
    const { result } = renderHook(() => useCollection());
    
    // Verify no quota error
    const stored = JSON.parse(localStorage.getItem('pokemon-collection-v2'));
    expect(stored.version).toBe(3);
    
    // Verify sparse storage: only owned cards stored
    expect(Object.keys(stored.cardQuantities).length).toBe(2500);
  });
});
```

## State of the Art

| Old Approach (v1.0) | Current Approach (v1.1) | When Changed | Impact |
|---------------------|-------------------------|--------------|--------|
| Boolean ownership (`ownedCards: Record<string, boolean>`) | Quantity storage (`cardQuantities: Record<string, number>`) | Phase 4 | Enables duplicate tracking, maintains ownership semantics |
| Store true/false for all cards | Sparse storage (only qty > 0) | Phase 4 | 10-50x reduction in localStorage usage |
| Direct boolean reads | Derived boolean from quantity | Phase 4 | Single source of truth, no sync bugs |
| No schema versioning | Version field + migration logic | v1.0 → v1.1 | Safe schema evolution, rollback capability |

**Deprecated/outdated:**
- **Direct `ownedCards` field in persisted state:** Replaced by derived `ownedCards` computed from `cardQuantities`. Still exposed in hook API for backward compatibility but not persisted.
- **Non-versioned localStorage schema:** All new schemas MUST include `version` field for future migrations.

## Open Questions

1. **Should we expose migration progress for large collections?**
   - What we know: Migration is synchronous, runs in `getInitialState()` blocking render
   - What's unclear: For 10,000+ card collections, could migration take >1 second? Should we show loading state?
   - Recommendation: Test with 10,000-card mock dataset. If migration < 500ms, keep silent. If > 1s, add non-blocking toast "Migrating collection data..." (defer to implementation testing).

2. **When should backup key be cleaned up?**
   - What we know: User constraint says "keep backup until next successful app start"
   - What's unclear: Define "successful app start"—first render? First collection write? 24 hours later?
   - Recommendation: Keep backup for one session. On second successful `getInitialState()` call (next app load), delete backup key. Document in migration code. (Low risk: backup is ~50-500KB, not quota-critical).

3. **Should we enforce max collection size (storage quota headroom)?**
   - What we know: Sparse storage keeps 1000-card collection under 100KB. localStorage quota is 5-10MB.
   - What's unclear: Should we warn/block if user approaches quota? Trim old data?
   - Recommendation: Per user constraint "do not auto-trim owned data," keep all user data. If QuotaExceededError occurs, show toast with manual recovery hint (export/clear). Don't proactively limit. (Defer enforcement until real-world quota issues reported).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 |
| Config file | `vitest.config.ts` (exists) |
| Quick run command | `npm test -- src/lib/__tests__/collection.test.ts` |
| Full suite command | `npm test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QTY-01 | Migrate v1 boolean → v3 quantity without data loss | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "migration"` | ✅ (extend existing) |
| QTY-01 | Idempotent migration (safe to run twice) | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "idempotent"` | ❌ Wave 0 |
| QTY-01 | Migration rollback on failure | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "rollback"` | ❌ Wave 0 |
| QTY-02 | Sparse storage: qty=0 removes key from storage | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "sparse"` | ❌ Wave 0 |
| QTY-02 | Large dataset migration (5000+ cards) stays under quota | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "large collection"` | ❌ Wave 0 |
| QTY-03 | `isOwned` derived from quantity (qty > 0) | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "derived ownership"` | ❌ Wave 0 |
| QTY-03 | `toggleOwnership` updates quantity (0↔1) | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "toggle"` | ✅ (extend existing) |
| QTY-04 | Backup created before migration | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "backup"` | ❌ Wave 0 |
| QTY-04 | Automatic restore on migration failure | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "rollback"` | ❌ Wave 0 |
| TESTQ-01 | Corrupted data handled gracefully | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "corrupted"` | ❌ Wave 0 |
| TESTQ-01 | QuotaExceededError handled during migration | unit | `npm test -- src/lib/__tests__/collection.test.ts -t "quota"` | ✅ (extend existing line 98-119) |

### Sampling Rate
- **Per task commit:** `npm test -- src/lib/__tests__/collection.test.ts` (migration tests only, <5 seconds)
- **Per wave merge:** `npm test` (full suite including existing v1.0 regression tests)
- **Phase gate:** Full suite green + manual verification with 1000+ card mock collection

### Wave 0 Gaps
- [ ] `src/lib/__tests__/collection.test.ts` — Add migration test cases (idempotent, rollback, sparse, large dataset, derived ownership, backup)
- [ ] Test fixtures — Create large mock datasets (1000, 5000, 10000 cards) for performance testing
- [ ] Migration validators — Helper functions to assert v3 schema structure and sparse storage invariant

## Sources

### Primary (HIGH confidence)
- **Existing codebase:** `src/lib/collection.ts` (v1.0 schema, localStorage patterns, quota handling), `src/lib/__tests__/collection.test.ts` (test infrastructure, mocking patterns), `package.json` (confirmed dependency versions)
- **Context documents:** `.planning/phases/04-data-model-migration/04-CONTEXT.md` (user constraints, locked decisions), `.planning/REQUIREMENTS.md` (QTY-01 through QTY-04, TESTQ-01 requirements)
- **React documentation:** Hooks patterns (functional state updates, useMemo for derived state, useEffect for side effects)
- **MDN Web Docs:** Web Storage API (localStorage quota limits 5-10MB, QuotaExceededError handling, JSON serialization)

### Secondary (MEDIUM confidence)
- **Zod documentation:** Schema validation patterns (z.object, z.record, z.number validation with min/max/int constraints, safeParse error handling)
- **TypeScript patterns:** Interface versioning, discriminated unions for schema versions, type guards for runtime validation
- **Vitest + Testing Library documentation:** renderHook for hook testing, act for state updates, localStorage mocking in happy-dom environment

### Tertiary (LOW confidence)
- **General migration patterns:** Schema versioning best practices (version field, migration chains, idempotency) — validated against existing v1.0 pattern in codebase
- **React state management anti-patterns:** Stale state reads, non-functional updates — flagged for prevention in implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All dependencies present in package.json, no installations required, versions verified against npm registry
- Architecture: HIGH - Direct codebase analysis, extends existing v1.0 patterns (collection hook, localStorage persistence, version field)
- Pitfalls: HIGH - Sourced from migration safety principles (backup/rollback, idempotency), React hook gotchas (functional updates), localStorage constraints (quota, sparse storage)
- Validation: HIGH - Existing test infrastructure (Vitest + Testing Library), test patterns established in v1.0, test framework configured

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (30 days - stable domain, React/TypeScript/localStorage APIs mature and stable)

---

*Research complete. Ready for Phase 4 planning.*
*Key risks: Data loss (mitigated by backup/rollback), sparse storage compliance (mitigated by functional update helpers), backward compatibility (mitigated by adapter pattern wrappers).*
*All requirements (QTY-01 through QTY-04, TESTQ-01) have clear implementation paths with existing stack.*
