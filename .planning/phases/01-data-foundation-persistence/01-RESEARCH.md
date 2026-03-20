# Phase 1: Data Foundation & Persistence - Research

**Researched:** 2026-03-20
**Domain:** TCGdex SDK integration, localStorage persistence, React hooks data layer
**Confidence:** HIGH

## Summary

Phase 1 requires migrating from PokemonTCG.io API to TCGdex SDK for data fetching and establishing minimal localStorage persistence for card ownership. The project is a React + TypeScript + Vite brownfield codebase with existing hook-based patterns (`useSets`, `useCards`, `useCard`) and localStorage collection logic that need adaptation.

**TCGdex SDK (v2.7.1)** is a TypeScript-first library with fully typed endpoints and built-in caching. The SDK uses a unified `fetch()` method with type-safe overloads for different endpoints (`'sets'`, `'series'`, `'cards'`). Response structures differ significantly from PokemonTCG.io API — sets use `cardCount.total` vs `total`, series are distinct top-level entities, and card images are single URLs not objects.

**localStorage persistence** currently stores full `CollectionCard` objects with quantity/condition/price fields that Phase 1 explicitly defers. The schema must be simplified to minimal ownership metadata (card ID + owned boolean) to prevent localStorage quota issues and align with Phase 1 MVP scope.

**Primary recommendation:** Create a thin adapter layer that wraps TCGdex SDK calls, normalizes responses to existing app types, and preserves hook interfaces to minimize downstream component churn. Replace collection storage with minimal `Record<cardId, boolean>` schema and compute derived stats on-the-fly.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
**TCGdex Data Integration**
- Fully replace the existing PokemonTCG.io fetch layer with `@tcgdex/sdk` in this phase.
- Use SDK calls as canonical sources: `tcgdex.fetch('sets')`, `tcgdex.fetch('series')`, and `tcgdex.fetch('sets', setId)`.
- Normalize returned SDK data into app-facing models used by existing components to reduce downstream churn.

**Ownership Persistence Model**
- MVP ownership is boolean only (`owned/unowned`) in this phase.
- Persist minimal localStorage metadata keyed by `cardId` (no full card payload snapshots).
- Exclude quantity/condition/value fields from the phase-1 persisted schema.

**Completion and Derived Stats**
- Compute set completion from persisted owned card IDs against set card totals.
- Keep completion math deterministic and recomputable after reload from localStorage + fetched set data.
- Treat derived stats as computed values, not separately persisted aggregates.

**Data Loading and Filtering Behavior**
- Use client-side instant filtering on the loaded in-memory dataset as default behavior.
- Keep Phase 1 responsible for reusable data/filter primitives that later set/album views can use directly.
- Preserve explicit loading and error states from hooks so later phases can render UX feedback consistently.

### Claude's Discretion
- Exact adapter/helper naming and file boundaries for SDK wrapper utilities.
- Cache policy details (short-lived in-memory cache vs simple re-fetch semantics) as long as success criteria remain met.
- Internal typing granularity for SDK response normalization.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | App fetches all Pokemon TCG sets using TCGdex SDK `tcgdex.fetch('sets')` | SDK provides `fetch('sets')` endpoint returning `SetList` (array of `SetResume` objects with `id`, `name`, `logo`, `cardCount.total`, `cardCount.official`) |
| DATA-02 | App fetches series metadata using TCGdex SDK `tcgdex.fetch('series')` | SDK provides `fetch('series')` endpoint returning `SerieList` (array of `SerieResume` objects with `id`, `name`, `logo`) |
| DATA-03 | App fetches selected set details and cards using TCGdex SDK `tcgdex.fetch('sets', setId)` | SDK provides `fetch('sets', setId)` endpoint returning `Set` object with embedded `cards: CardList` array of card details |
| DATA-04 | App uses TCGdex card `image` data for card rendering in album view | TCGdex cards have `image?: string` field (single URL) vs PokemonTCG.io's `images: {small, large}` object structure |
| PERS-01 | Card ownership changes are automatically persisted to localStorage | Existing `useCollection` hook has localStorage write-on-change pattern; needs schema simplification to `Record<cardId, boolean>` |
| PERS-02 | Persisted collection data reloads correctly on future browser sessions | Current implementation hydrates on mount; pattern is sound but schema must be validated for minimal payload |
| PERS-03 | Set-level and album-level statistics remain consistent after reload | Completion % must be computed from: `(ownedCardIds.filter(id => setCardIds.includes(id)).length / set.cardCount.total) * 100` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tcgdex/sdk | 2.7.1 | Pokemon TCG data fetching | Project requirement; official open-source TCGdex API client with TypeScript types |
| React | 18.3.1 | UI framework | Already established in brownfield codebase |
| TypeScript | 5.5.3 | Type safety | Already established with strict mode enabled |
| localStorage API | Browser native | Client-side persistence | Project constraint for local-first v1 scope (no backend) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @cachex/core | (bundled with SDK) | TCGdex built-in caching | Automatic; SDK manages cache TTL internally |
| react hooks (useState, useEffect, useMemo) | 18.3.1 | State and lifecycle management | Existing pattern for data fetching hooks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @tcgdex/sdk | Continue with PokemonTCG.io | Violates project requirement; user explicitly chose TCGdex |
| localStorage | IndexedDB | More complex API; localStorage sufficient for ~5MB card ID collection |
| Custom hooks | React Query / SWR | Adds dependency; existing pattern works; Phase 1 scope is data foundation not advanced caching |

**Installation:**
```bash
npm install @tcgdex/sdk
```

**Version verification:** Verified against npm registry on 2026-03-20. TCGdex SDK 2.7.1 published 2025-08-25.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── lib/
│   ├── tcgdex.ts           # TCGdex SDK singleton instance + adapter utilities
│   ├── api.ts              # Hook layer (useSets, useCards, useCard) - refactored to use tcgdex adapter
│   ├── collection.ts       # Collection persistence (useCollection) - simplified schema
│   └── types.ts            # (new) Normalized app types bridging TCGdex types and UI contracts
├── components/             # Existing UI components (no changes needed if types preserved)
└── hooks/                  # Existing custom hooks directory
```

### Pattern 1: TCGdex Adapter Layer
**What:** Thin wrapper around TCGdex SDK that normalizes response types to match existing app contracts
**When to use:** When migrating data sources without breaking downstream consumers
**Example:**
```typescript
// src/lib/tcgdex.ts
import TCGdex, { Set as TCGSet, Card as TCGCard, SetResume as TCGSetResume } from '@tcgdex/sdk'
import { PokemonSet, PokemonCard } from './types'

// Singleton SDK instance
export const tcgdex = new TCGdex('en')

// Adapter: TCGdex Set → App PokemonSet
export function normalizeTCGSet(tcgSet: TCGSetResume | TCGSet): PokemonSet {
  return {
    id: tcgSet.id,
    name: tcgSet.name,
    series: 'serie' in tcgSet ? tcgSet.serie.name : 'Unknown', // Full Set has serie, Resume doesn't
    printedTotal: tcgSet.cardCount.official,
    total: tcgSet.cardCount.total,
    releaseDate: 'releaseDate' in tcgSet ? tcgSet.releaseDate : '',
    images: {
      symbol: tcgSet.symbol || '',
      logo: tcgSet.logo || '',
    },
    // ... map other fields as needed
  }
}

// Adapter: TCGdex Card → App PokemonCard
export function normalizeTCGCard(tcgCard: TCGCard): PokemonCard {
  return {
    id: tcgCard.id,
    name: tcgCard.name,
    images: {
      small: tcgCard.image || '',
      large: tcgCard.image || '', // TCGdex has single image URL
    },
    set: normalizeTCGSet(tcgCard.set),
    number: tcgCard.localId,
    rarity: tcgCard.rarity,
    // ... map other fields
  }
}
```

### Pattern 2: Minimal Ownership Schema
**What:** Store only card IDs with boolean ownership status in localStorage
**When to use:** Phase 1 MVP persistence before adding quantity/condition tracking
**Example:**
```typescript
// src/lib/collection.ts
const COLLECTION_KEY = 'pokemon-tcg-collection-v2' // New key for schema migration

interface CollectionData {
  version: 1
  ownedCards: Record<string, boolean> // cardId → owned
}

function getStoredCollection(): CollectionData {
  const stored = localStorage.getItem(COLLECTION_KEY)
  if (!stored) return { version: 1, ownedCards: {} }
  
  try {
    const parsed = JSON.parse(stored)
    // Validate schema
    if (parsed.version === 1 && typeof parsed.ownedCards === 'object') {
      return parsed
    }
    return { version: 1, ownedCards: {} }
  } catch {
    return { version: 1, ownedCards: {} }
  }
}

function saveCollection(data: CollectionData): void {
  try {
    localStorage.setItem(COLLECTION_KEY, JSON.stringify(data))
  } catch (e) {
    if (e instanceof DOMException && e.name === 'QuotaExceededError') {
      // Handle quota - should never happen with minimal schema
      console.error('localStorage quota exceeded')
    }
    throw e
  }
}
```

### Pattern 3: Computed Completion Stats
**What:** Calculate set completion on-the-fly from owned card IDs and fetched set data
**When to use:** Always in Phase 1; stats are derived not persisted
**Example:**
```typescript
// src/lib/collection.ts (continued)
export function useCollectionStats(setId?: string) {
  const { ownedCards } = useCollection()
  const { cards } = useCards(setId) // Cards from set
  
  return useMemo(() => {
    if (!cards || cards.length === 0) {
      return { owned: 0, missing: 0, total: 0, percentage: 0 }
    }
    
    const setCardIds = cards.map(c => c.id)
    const ownedInSet = setCardIds.filter(id => ownedCards[id])
    
    return {
      owned: ownedInSet.length,
      missing: setCardIds.length - ownedInSet.length,
      total: setCardIds.length,
      percentage: (ownedInSet.length / setCardIds.length) * 100,
    }
  }, [ownedCards, cards])
}
```

### Pattern 4: Hook Interface Preservation
**What:** Keep existing `useSets`, `useCards`, `useCard` hook signatures while swapping implementation
**When to use:** Minimizing downstream component churn during data source migration
**Example:**
```typescript
// src/lib/api.ts (refactored internals, same interface)
export const useSets = (page: number, pageSize: number, filters: Record<string, string> = {}) => {
  const [sets, setSets] = useState<PokemonSet[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  
  useEffect(() => {
    let cancelled = false
    
    const fetchSets = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const tcgSets = await tcgdex.fetch('sets') // TCGdex call
        if (cancelled) return
        
        // Normalize and apply filters client-side
        const normalized = (tcgSets || []).map(normalizeTCGSet)
        const filtered = applySetFilters(normalized, filters)
        
        // Client-side pagination
        const start = (page - 1) * pageSize
        const paginated = filtered.slice(start, start + pageSize)
        
        setSets(paginated)
      } catch (e) {
        if (!cancelled) setError(e as Error)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    
    fetchSets()
    return () => { cancelled = true }
  }, [page, pageSize, JSON.stringify(filters)])
  
  return { sets, totalSets: sets.length, loading, error }
}
```

### Anti-Patterns to Avoid
- **Storing full card objects in localStorage:** Bloats storage; Phase 1 requirement is minimal metadata only
- **Server-side pagination expectations:** TCGdex returns full datasets; paginate client-side
- **Mutating TCGdex SDK responses:** SDK objects may be cached; always normalize to new objects
- **Accessing card images as objects:** TCGdex uses `image` (string) not `images.small/large` (object)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TCG card data fetching | Custom fetch wrappers, retry logic, rate limiting | @tcgdex/sdk | SDK includes built-in caching (@cachex/core), error handling, and TypeScript types; hand-rolling risks API changes |
| localStorage serialization errors | Custom try-catch around every write | Schema validation + versioned key | localStorage can fail silently; TCGdex API changes require migration strategy |
| Set completion calculations | Store completion % in localStorage | Compute from owned IDs + set totals | Persisting derived stats creates sync bugs; recomputing from source of truth is deterministic |
| Client-side filtering/sorting | Imperative array manipulation | useMemo + filter/sort chains | React optimization patterns prevent re-renders; hand-rolled logic hard to maintain |

**Key insight:** TCGdex SDK has 2+ years of production use and handles edge cases (rate limits, caching, retries) that would take significant effort to replicate. The Phase 1 adapter layer should normalize types, not reimplement API client logic.

## Common Pitfalls

### Pitfall 1: localStorage Quota Exceeded
**What goes wrong:** Storing full card objects (with images, prices, descriptions) exceeds 5-10MB localStorage limit
**Why it happens:** Browser localStorage is designed for small metadata, not large datasets; full PokemonTCG.io card objects are ~2-5KB each × 1000+ cards = quota exceeded
**How to avoid:** 
- Store only minimal ownership data: `{ cardId: boolean }`
- Do NOT store card images, descriptions, attacks, or full set objects
- Use versioned localStorage key (`collection-v2`) to safely migrate existing data
**Warning signs:** 
- `QuotaExceededError` in browser console
- Collection fails to persist after adding many cards
- localStorage.getItem returns null unexpectedly

### Pitfall 2: TCGdex API Structure Mismatches
**What goes wrong:** Code expects PokemonTCG.io structure (e.g., `card.images.small`) but TCGdex returns `card.image` (string)
**Why it happens:** Different APIs have different schemas; TCGdex uses simpler structure (single image URL) vs PokemonTCG.io (multiple sizes)
**How to avoid:**
- Create adapter functions (`normalizeTCGCard`) to map TCGdex types to app types
- Use TypeScript to enforce type contracts at adapter boundaries
- Test adapter with real TCGdex API responses (not just types)
**Warning signs:**
- `undefined` errors when accessing `card.images.small`
- Missing images in UI after SDK migration
- TypeScript errors about incompatible types between API and components

### Pitfall 3: Series vs Set Confusion
**What goes wrong:** Treating series as a property of sets instead of independent entities
**Why it happens:** PokemonTCG.io has `set.series` as string; TCGdex has separate `series` endpoint with `id`/`name`/`sets` relationship
**How to avoid:**
- Fetch series list separately: `tcgdex.fetch('series')`
- Map series to sets using `serie.sets` array or `set.serie.id`
- Store series as lookup table if filtering by series is frequent
**Warning signs:**
- Series filter dropdown shows duplicate or missing entries
- Cannot fetch all sets in a series
- Series name doesn't match official Pokemon TCG series names

### Pitfall 4: Stale Data After Collection Changes
**What goes wrong:** Set completion % doesn't update after marking card as owned
**Why it happens:** React not re-rendering computed stats when collection state changes but cards are memoized separately
**How to avoid:**
- Use `useMemo` with proper dependencies: `[ownedCards, cards]`
- Ensure collection state updates trigger hook consumers to re-render
- Compute stats in custom hook that subscribes to both collection and card data
**Warning signs:**
- Progress bar doesn't move after clicking card
- Completion % correct after page refresh but not on live updates
- Set shows 100% but missing cards indicator still visible

### Pitfall 5: Card Identity Across Sources
**What goes wrong:** Same card has different IDs between localStorage and fetched data
**Why it happens:** Using `localId` (set-relative: "1", "2") instead of `id` (global: "base1-1", "base1-2") for persistence
**How to avoid:**
- ALWAYS use TCGdex card `id` (global identifier) for localStorage keys
- Never use `localId` (card number within set) as primary key
- Document in types: `id: string // Global ID like 'swsh1-1'`
**Warning signs:**
- Collection lost after fetching same set again
- Owned cards appear unowned in different views
- Duplicate entries for same card in collection

### Pitfall 6: Effect Dependency Arrays
**What goes wrong:** Infinite re-render loops or stale closures when fetching data
**Why it happens:** Using objects or arrays in `useEffect` dependencies without proper memoization; `filters` object recreated every render triggers new fetch
**How to avoid:**
- Use `JSON.stringify(filters)` as dependency or `useMemo` for filter objects
- Implement cancellation tokens to abort stale fetches
- Use `useCallback` for functions passed as dependencies
**Warning signs:**
- API called multiple times per second in network tab
- React DevTools shows rapid re-renders
- Browser freezes or becomes sluggish

## Code Examples

Verified patterns based on TCGdex SDK v2.7.1 official types and documentation:

### TCGdex Initialization
```typescript
// src/lib/tcgdex.ts
import TCGdex from '@tcgdex/sdk'

// Create singleton instance with English language
export const tcgdex = new TCGdex('en')

// Optional: Adjust cache TTL (default is 3600 seconds = 1 hour)
tcgdex.setCacheTTL(1800) // 30 minutes

// SDK automatically handles caching via built-in @cachex/core
```

### Fetching Sets
```typescript
// Source: @tcgdex/sdk type definitions
import { tcgdex } from './tcgdex'
import type { SetResume } from '@tcgdex/sdk'

async function fetchAllSets(): Promise<SetResume[]> {
  try {
    const sets = await tcgdex.fetch('sets')
    return sets || []
  } catch (error) {
    console.error('Failed to fetch sets:', error)
    throw error
  }
}

// TCGdex SetResume structure:
// {
//   id: string           // "base1", "swsh1"
//   name: string         // "Base Set", "Sword & Shield"
//   logo?: string        // URL to set logo
//   symbol?: string      // URL to set symbol
//   cardCount: {
//     total: number      // Total cards including secrets
//     official: number   // Printed count on card bottom
//   }
// }
```

### Fetching Series
```typescript
// Source: @tcgdex/sdk type definitions
import type { SerieResume } from '@tcgdex/sdk'

async function fetchAllSeries(): Promise<SerieResume[]> {
  const series = await tcgdex.fetch('series')
  return series || []
}

// SerieResume structure:
// {
//   id: string       // "base", "sword-shield"
//   name: string     // "Base", "Sword & Shield"
//   logo?: string    // URL to series logo
// }
```

### Fetching Set Details with Cards
```typescript
// Source: @tcgdex/sdk type definitions
import type { Set as TCGSet } from '@tcgdex/sdk'

async function fetchSetDetails(setId: string): Promise<TCGSet | undefined> {
  const setDetails = await tcgdex.fetch('sets', setId)
  
  // TCGSet includes:
  // - All SetResume fields
  // - serie: SerieResume (parent series info)
  // - releaseDate: string
  // - legal: { standard: boolean, expanded: boolean }
  // - cards: CardList (array of CardResume objects)
  
  return setDetails
}
```

### Minimal Collection Persistence
```typescript
// Source: React hooks + Web Storage API best practices
import { useState, useEffect } from 'react'

const STORAGE_KEY = 'pokemon-collection-v1'

interface CollectionState {
  version: 1
  ownedCards: Record<string, boolean>
}

export function useCollection() {
  const [collection, setCollection] = useState<CollectionState>(() => {
    // Initialize from localStorage
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (parsed.version === 1) return parsed
      }
    } catch (e) {
      console.warn('Failed to load collection:', e)
    }
    return { version: 1, ownedCards: {} }
  })

  // Persist on change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collection))
    } catch (e) {
      console.error('Failed to save collection:', e)
    }
  }, [collection])

  const toggleOwnership = (cardId: string) => {
    setCollection(prev => ({
      ...prev,
      ownedCards: {
        ...prev.ownedCards,
        [cardId]: !prev.ownedCards[cardId],
      },
    }))
  }

  const isOwned = (cardId: string): boolean => {
    return !!collection.ownedCards[cardId]
  }

  return { collection, toggleOwnership, isOwned }
}
```

### Computed Completion Statistics
```typescript
// Source: React useMemo optimization pattern
import { useMemo } from 'react'

interface CompletionStats {
  owned: number
  missing: number
  total: number
  percentage: number
}

export function useSetCompletion(
  setCardIds: string[],
  ownedCards: Record<string, boolean>
): CompletionStats {
  return useMemo(() => {
    const total = setCardIds.length
    if (total === 0) {
      return { owned: 0, missing: 0, total: 0, percentage: 0 }
    }

    const owned = setCardIds.filter(id => ownedCards[id]).length
    const missing = total - owned
    const percentage = (owned / total) * 100

    return { owned, missing, total, percentage }
  }, [setCardIds, ownedCards])
}
```

### Client-Side Filtering
```typescript
// Source: React functional patterns
import type { SetResume } from '@tcgdex/sdk'

interface SetFilters {
  series?: string
  search?: string
}

export function filterSets(
  sets: SetResume[],
  filters: SetFilters
): SetResume[] {
  return sets.filter(set => {
    // Series filter (requires fetching full Set details for serie.name)
    if (filters.series && filters.series !== 'all') {
      // Note: SetResume doesn't include serie; need full Set or separate series lookup
      // For Phase 1, may need to store serie mapping or fetch full sets
    }

    // Name search (case-insensitive)
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      if (!set.name.toLowerCase().includes(searchLower)) {
        return false
      }
    }

    return true
  })
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PokemonTCG.io API (`api.pokemontcg.io/v2`) | TCGdex API (`api.tcgdex.net/v2`) | User decision (Phase 1) | Different schemas: `set.total` → `set.cardCount.total`, `card.images` → `card.image` |
| Full card objects in localStorage | Minimal ownership metadata | Phase 1 decision | Prevents quota issues; defers quantity/condition to v2 |
| Server-side pagination | Client-side filtering/pagination | TCGdex architecture | SDK returns full datasets; paginate in memory |
| String series property | Series as first-class entities | TCGdex API design | Fetch via `tcgdex.fetch('series')` instead of extracting from sets |

**Deprecated/outdated:**
- **PokemonTCG.io API key usage:** TCGdex is open-source and doesn't require API keys
- **Complex pagination logic:** TCGdex returns full datasets; client-side pagination sufficient for v1
- **PokemonTCG.io type interfaces:** Remove `src/lib/api.ts` types after creating normalized types

## Open Questions

1. **How to handle series filtering without fetching full set details?**
   - What we know: `SetResume` (from `fetch('sets')`) doesn't include parent series; full `Set` (from `fetch('sets', id)`) includes `serie: SerieResume`
   - What's unclear: Whether to fetch all full set details upfront or maintain separate series→sets mapping
   - Recommendation: Fetch `series` endpoint once, build `serieId → setIds[]` lookup, filter sets by ID matching. Avoids N+1 fetches for series filter.

2. **SDK caching behavior across React re-renders**
   - What we know: TCGdex SDK has built-in @cachex/core with default 1-hour TTL
   - What's unclear: Whether multiple React components calling same endpoint triggers duplicate network requests or cache hits
   - Recommendation: Assume SDK caches effectively (it's designed for this); add loading state tests to verify. If needed, can wrap SDK in React context to share state.

3. **Migration path for existing localStorage data**
   - What we know: Current implementation stores full `CollectionCard` objects; Phase 1 needs minimal schema
   - What's unclear: Whether to auto-migrate old data or start fresh with new key
   - Recommendation: Use new localStorage key (`pokemon-collection-v1`) to avoid conflicts. Provide manual import/export feature in later phase if users need migration.

## Validation Architecture

> Nyquist validation is enabled in workflow configuration.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| Config file | none — see Wave 0 |
| Quick run command | `npm run test -- --run --reporter=verbose` |
| Full suite command | `npm run test -- --run --coverage` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Fetches all TCG sets from TCGdex SDK | integration | `npm test -- src/lib/tcgdex.test.ts -t "fetch sets"` | ❌ Wave 0 |
| DATA-02 | Fetches series metadata from TCGdex SDK | integration | `npm test -- src/lib/tcgdex.test.ts -t "fetch series"` | ❌ Wave 0 |
| DATA-03 | Fetches set details with cards from TCGdex SDK | integration | `npm test -- src/lib/tcgdex.test.ts -t "fetch set details"` | ❌ Wave 0 |
| DATA-04 | Normalizes TCGdex card image to app format | unit | `npm test -- src/lib/tcgdex.test.ts -t "normalize card image"` | ❌ Wave 0 |
| PERS-01 | Persists ownership changes to localStorage | unit | `npm test -- src/lib/collection.test.ts -t "persist ownership"` | ❌ Wave 0 |
| PERS-02 | Reloads collection from localStorage on mount | unit | `npm test -- src/lib/collection.test.ts -t "reload collection"` | ❌ Wave 0 |
| PERS-03 | Computes consistent completion stats after reload | unit | `npm test -- src/lib/collection.test.ts -t "completion stats"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `npm test -- --run --reporter=verbose` (fast unit tests only)
- **Per wave merge:** `npm test -- --run --coverage` (full suite with coverage report)
- **Phase gate:** Full suite green + coverage ≥80% for `src/lib/` before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `vitest.config.ts` — Vitest configuration with React testing setup
- [ ] `src/lib/tcgdex.test.ts` — Tests for SDK adapter and normalization functions
- [ ] `src/lib/collection.test.ts` — Tests for localStorage persistence and stat computation
- [ ] Framework install: `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom` — if not detected

## Sources

### Primary (HIGH confidence)
- @tcgdex/sdk v2.7.1 type definitions (`node_modules/@tcgdex/sdk/dist/tcgdex.d.ts`) - Complete TypeScript interface definitions for all SDK methods and return types
- @tcgdex/sdk README.md - Official usage examples and endpoint documentation
- npm registry (@tcgdex/sdk) - Version and publish date verification (2.7.1, published 2025-08-25)

### Secondary (MEDIUM confidence)
- Existing codebase (`src/lib/api.ts`, `src/lib/collection.ts`) - Current implementation patterns for hooks and localStorage
- React 18 documentation (hooks, useMemo, useEffect patterns) - Established patterns for async data fetching
- Web Storage API (localStorage) - Browser-native persistence capabilities and quota limits

### Tertiary (LOW confidence)
- None - All research findings derived from primary sources (SDK types, existing code)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All versions verified against npm registry; TCGdex SDK officially documented
- Architecture: HIGH - Patterns derived from existing codebase + SDK type contracts
- Pitfalls: MEDIUM-HIGH - Common localStorage and React hooks pitfalls are well-documented; TCGdex-specific issues inferred from API structure differences

**Research date:** 2026-03-20
**Valid until:** ~2026-05-01 (40 days) - TCGdex API is stable; React patterns unlikely to change; localStorage browser support unchanging
