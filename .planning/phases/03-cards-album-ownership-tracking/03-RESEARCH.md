# Phase 3: Cards Album & Ownership Tracking - Research

**Researched:** 2026-03-21
**Domain:** React card grid UI, client-side filtering, real-time stats, virtual scrolling
**Confidence:** HIGH

## Summary

Phase 3 implements the core collection tracking experience: a responsive card album grid with ownership toggles, filters (size, ownership state, name search), and real-time statistics. The existing `CardGrid` component provides a solid foundation with TCGdex integration, shadcn/ui components, and localStorage-backed ownership persistence already functional from Phase 1-2.

**Critical findings:**
1. **Virtual scrolling NOT needed yet** - current pagination (20 cards/page) plus lazy loading handles typical sets (100-200 cards) well; defer until performance evidence warrants it
2. **Client-side filtering must preserve pagination UX** - existing code hides pagination during filtering (correct pattern); stats must compute from filtered dataset
3. **Real-time stats via useMemo** - standard React optimization pattern for derived calculations prevents unnecessary re-renders

**Primary recommendation:** Build album enhancements incrementally on existing CardGrid foundation. Add card size toggle, ownership filter, name search, and fixed stats footer as UI-layer additions without major architectural changes. Test with largest TCGdex sets (Scarlet & Violet base: 198 cards) to validate performance assumptions.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Card Interaction Model**: Keep the existing card-grid interaction pattern where users can act directly on a card from the album surface. Preserve immediate ownership feedback on toggle actions. Keep owned-state signaling visually explicit on card tiles.
- **Album Controls**: Add a card size toggle with exactly two modes: small and medium. Add ownership-state filter with exactly three modes: all, owned, missing. Add in-set live name search that filters cards as the user types.
- **Stats Footer Behavior**: Implement a fixed bottom stats footer in album view. Footer must display owned count, missing count, and completion percentage. Footer values update in real time as ownership changes.
- **Data and Scope Guardrails**: Continue using existing TCGdex-backed card data and local ownership persistence from earlier phases. Do not introduce cloud/auth/account or valuation features in this phase. Keep advanced quantity/condition/wishlist features deferred (v2 scope).

### Claude's Discretion
- Exact placement/density of album controls while preserving responsive behavior.
- Search/filter control styling details and iconography.
- Internal memoization/derived-state helpers for filter + stats calculations.

### Deferred Ideas (OUT OF SCOPE)
- Quantity/condition/notes as core collection attributes in album cards (v2 scope).
- Price/market analytics or valuation overlays.
- Deep-link routing, saved filter presets, and cross-set global search.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ALBM-01 | User can open a selected set in a responsive card album grid | Existing CardGrid component + responsive grid CSS already functional |
| ALBM-02 | User sees real card images for all cards in the selected set | TCGdex SDK card.images.small/large + lazy loading already implemented |
| ALBM-03 | User can click a card to toggle ownership status | useCollection hook + CardGrid add/remove handlers already functional |
| ALBM-04 | User sees a clear owned-state indicator (green checkmark) on owned cards | Ring styling + Check icon pattern already implemented |
| ALBM-05 | User can switch album card display between small and medium sizes | CSS grid-template-columns + dynamic className switching (standard pattern) |
| ALBM-06 | User can filter album cards by all, owned, or missing states | Client-side array filtering + useMemo optimization (existing filter pattern) |
| ALBM-07 | User can search cards by name within the selected set | Client-side string matching + toLowerCase normalization (existing search pattern) |
| STAT-01 | User sees a fixed bottom footer with real-time owned count, missing count, and completion percentage | useSetCompletion hook from collection.ts + fixed CSS positioning + derived stats from filtered dataset |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 18.3.1 | UI framework | Already in project, stable hooks API for state/memoization |
| @tcgdex/sdk | 2.7.1 | Card data | Already integrated in Phase 1, provides card images + metadata |
| localStorage API | Native | Ownership persistence | Already in useCollection hook, zero dependencies |
| CSS Grid + Flexbox | Native | Responsive layouts | Already used in CardGrid, no library needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 0.446.0 | Icons (Search, Filter, Check, X) | Already in project for UI icons |
| shadcn/ui Select | 1.1.0 | Size toggle dropdown | Already in CardGrid for filters |
| shadcn/ui Input | Latest | Search text field | Already in project for forms |
| shadcn/ui Badge | Latest | Stats display | Already used for rarity/type badges |
| useMemo | React 18.3.1 | Filter/stats optimization | Built-in React hook for derived state |
| useState | React 18.3.1 | UI state (size, filters) | Built-in React hook for local state |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CSS Grid | react-window / @tanstack/react-virtual | Virtual scrolling adds complexity; defer until 500+ cards OR measured performance issue |
| useMemo | Manual state | No benefit - useMemo is standard for derived calculations |
| localStorage | IndexedDB / Supabase | Out of scope - v1 is local-first, no need for complex persistence |

**Installation:**
```bash
# No new dependencies required
# All necessary libraries already in package.json
```

**Version verification:** All libraries verified against package.json (checked 2026-03-21).

## Architecture Patterns

### Recommended Project Structure
```
src/
├── components/
│   ├── CardGrid.tsx           # EXTEND: Add size/ownership filters, search, stats footer
│   ├── CardDetail.tsx         # No changes needed
│   └── ui/                    # shadcn/ui primitives (already present)
├── lib/
│   ├── api.ts                 # No changes needed (useCards hook handles fetching)
│   ├── collection.ts          # EXTEND: Add filtered stats helper
│   └── utils.ts               # No changes needed
└── App.tsx                    # No changes needed (routing already wired)
```

### Pattern 1: Client-Side Filtering with Stats Derivation
**What:** Filter cards array client-side, then compute stats from filtered results
**When to use:** When dataset is already loaded (pagination brings 20-200 cards) and filters are UI-only

**Example:**
```typescript
// In CardGrid.tsx
const [sizeMode, setSizeMode] = useState<'small' | 'medium'>('medium');
const [ownershipFilter, setOwnershipFilter] = useState<'all' | 'owned' | 'missing'>('all');
const [nameSearch, setNameSearch] = useState('');

const { isInCollection } = useCollection();

// Apply filters using useMemo to prevent re-computation on every render
const filteredCards = useMemo(() => {
  let filtered = cards;
  
  // Ownership filter
  if (ownershipFilter === 'owned') {
    filtered = filtered.filter(card => isInCollection(card.id));
  } else if (ownershipFilter === 'missing') {
    filtered = filtered.filter(card => !isInCollection(card.id));
  }
  
  // Name search (case-insensitive)
  if (nameSearch.trim()) {
    const searchLower = nameSearch.toLowerCase();
    filtered = filtered.filter(card => 
      card.name.toLowerCase().includes(searchLower)
    );
  }
  
  return filtered;
}, [cards, ownershipFilter, nameSearch, isInCollection]);

// Compute stats from FILTERED dataset
const stats = useMemo(() => {
  const total = filteredCards.length;
  const owned = filteredCards.filter(card => isInCollection(card.id)).length;
  const missing = total - owned;
  const percentage = total > 0 ? (owned / total) * 100 : 0;
  return { owned, missing, total, percentage };
}, [filteredCards, isInCollection]);
```

### Pattern 2: Dynamic Grid Column Sizing
**What:** CSS grid with responsive column counts that change based on size mode
**When to use:** When users need to control information density

**Example:**
```typescript
// Size mode state
const [sizeMode, setSizeMode] = useState<'small' | 'medium'>('medium');

// CSS classes mapping
const gridClasses = {
  small: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-2',
  medium: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4'
};

// Render
<div className={cn("grid", gridClasses[sizeMode])}>
  {filteredCards.map(card => <CardTile key={card.id} card={card} />)}
</div>
```

### Pattern 3: Fixed Footer with Real-Time Stats
**What:** CSS fixed position footer that stays visible during scroll, with stats derived from visible dataset
**When to use:** When users need persistent visibility of progress metrics

**Example:**
```typescript
// Stats computation (see Pattern 1)
const stats = useMemo(() => { /* ... */ }, [filteredCards, isInCollection]);

// Render fixed footer
<div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t z-40">
  <div className="container mx-auto px-4 py-3 flex items-center justify-between max-w-7xl">
    <div className="flex gap-6 text-sm">
      <div>
        <span className="text-muted-foreground">Owned:</span>
        <Badge className="ml-2 bg-green-500">{stats.owned}</Badge>
      </div>
      <div>
        <span className="text-muted-foreground">Missing:</span>
        <Badge className="ml-2 bg-slate-500">{stats.missing}</Badge>
      </div>
      <div>
        <span className="text-muted-foreground">Completion:</span>
        <Badge className="ml-2 bg-blue-500">{stats.percentage.toFixed(1)}%</Badge>
      </div>
    </div>
  </div>
</div>
```

### Pattern 4: Search Input with Debouncing (Optional Optimization)
**What:** Delay filter execution until user stops typing to reduce re-renders
**When to use:** ONLY if performance issues observed with large filtered datasets

**Example:**
```typescript
// Without debouncing (RECOMMENDED for v1 - simpler, sufficient performance)
const [nameSearch, setNameSearch] = useState('');
<Input 
  value={nameSearch}
  onChange={(e) => setNameSearch(e.target.value)}
  placeholder="Search cards..."
/>

// With debouncing (DEFER unless needed)
// Would require: npm install use-debounce
// import { useDebounce } from 'use-debounce';
// const [debouncedSearch] = useDebounce(nameSearch, 300);
```

### Anti-Patterns to Avoid
- **Filtering on server side when data is already client-side:** TCGdex sets are fully loaded; don't make extra API calls for filtering
- **Computing stats from unfiltered dataset:** Users expect stats to reflect what they see on screen (filtered view)
- **Showing pagination during client-side filtering:** Confusing UX - existing CardGrid correctly hides pagination when filters active
- **Using complex state management (Redux/Zustand) for UI-only filters:** useState + useMemo sufficient for this scope
- **Re-implementing ownership toggle logic:** Reuse existing useCollection hook + CardGrid patterns

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Virtual scrolling | Custom intersection observer + windowing logic | @tanstack/react-virtual 3.13.23 (IF needed) | Handles viewport math, dynamic heights, resize events; 1000+ edge cases |
| Search input debouncing | Custom setTimeout wrapper | use-debounce 10.0.3 (IF needed) | Race conditions, cleanup on unmount, React 18+ concurrent mode |
| Fixed positioning + scroll handling | Custom scroll listeners | CSS `position: fixed` + `z-index` | Native browser optimization, no JS overhead |
| Responsive grid breakpoints | Custom resize observers | Tailwind responsive classes | Tested across devices, SSR-safe, predictable |
| Accessibility for filters/search | Custom keyboard navigation | shadcn/ui primitives (Select, Input) | ARIA compliance, focus management, screen reader support |

**Key insight:** Phase 3 requirements fit entirely within React's built-in capabilities + existing shadcn/ui components. Virtual scrolling is premature optimization until evidence of performance issues with 200+ card sets.

## Common Pitfalls

### Pitfall 1: Stats Computed from Wrong Dataset
**What goes wrong:** Footer shows stats for ALL cards in set, but user is viewing FILTERED cards (e.g., "missing only") - stats don't match visible content
**Why it happens:** Computing stats from original `cards` array instead of `filteredCards` array
**How to avoid:** Always derive stats from the SAME array being rendered on screen
**Warning signs:** User filters to "owned only" but footer still shows "missing: 50" when no missing cards visible

### Pitfall 2: Over-Rendering on Every Keystroke
**What goes wrong:** Typing in search box causes entire grid to re-render 60 times (once per character)
**Why it happens:** Not wrapping filter/stats logic in useMemo, causing new array/object references on every render
**How to avoid:** Use useMemo for `filteredCards` and `stats` with proper dependency arrays
**Warning signs:** Laggy typing in search input, console.log shows 10+ renders per keystroke

### Pitfall 3: Fixed Footer Covering Content
**What goes wrong:** Last row of cards hidden behind footer, inaccessible even with scroll
**Why it happens:** Not adding bottom padding/margin to main content area to account for footer height
**How to avoid:** Add `pb-20` (or footer height + gap) to grid container so content scrolls above footer
**Warning signs:** User can't see or click last row of cards, scrollbar reaches bottom but cards cut off

### Pitfall 4: Pagination State Inconsistent with Filters
**What goes wrong:** User filters to "owned only" (15 results), but pagination shows "Page 1 of 5" from unfiltered 100-card set
**Why it happens:** Pagination logic uses original `totalCards` instead of filtered count
**How to avoid:** Hide pagination entirely when any filter is active (existing CardGrid pattern), OR compute totalPages from filteredCards.length
**Warning signs:** Page 2+ buttons show but clicking them displays empty results

### Pitfall 5: Search Case-Sensitivity
**What goes wrong:** User searches "pikachu" but card is named "Pikachu" (capitalized) - no match found
**Why it happens:** Using strict string comparison (card.name.includes(search)) instead of case-insensitive match
**How to avoid:** Always normalize: `card.name.toLowerCase().includes(search.toLowerCase())`
**Warning signs:** User complains "search doesn't work" but card exists with different casing

### Pitfall 6: Ownership State Stale After Toggle
**What goes wrong:** User toggles card ownership, but stats footer doesn't update OR shows wrong count
**Why it happens:** Stats useMemo doesn't include `isInCollection` or `ownedCards` in dependency array
**How to avoid:** Include ALL values that affect computation in useMemo dependencies: `[filteredCards, isInCollection, ownedCards]`
**Warning signs:** Toggle works (ring appears) but footer stats stay frozen at old values

### Pitfall 7: Performance Testing Only Small Sets
**What goes wrong:** App feels fast during development with 50-card test set, but user experiences lag with 200-card sets
**Why it happens:** Not testing with largest TCGdex sets (Scarlet & Violet base: 198 cards, Sun & Moon base: 163 cards)
**How to avoid:** Test with real large sets BEFORE declaring performance acceptable; measure with Chrome DevTools Performance tab
**Warning signs:** User reports "app is slow" but dev testing was only with 20-card sets

## Code Examples

Verified patterns from existing codebase:

### Ownership Toggle (Already Functional)
```typescript
// Source: src/components/CardGrid.tsx lines 77-126
const handleAddToCollection = async (card: PokemonCard, e: React.MouseEvent) => {
  e.stopPropagation(); // Prevent card click when clicking button
  setProcessingCards(prev => new Set(prev).add(card.id));
  
  try {
    await addToCollection(card.id);
    toast({
      title: "Card Added",
      description: `${card.name} has been added to your collection.`,
      duration: 2000,
    });
  } catch (error) {
    toast({
      title: "Error",
      description: "Failed to add card to collection.",
      variant: "destructive",
    });
  } finally {
    setProcessingCards(prev => {
      const next = new Set(prev);
      next.delete(card.id);
      return next;
    });
  }
};

// Usage in card render:
const isOwned = isInCollection(card.id);
const isProcessing = processingCards.has(card.id);

<Card className={cn(
  "group overflow-hidden transition-all duration-300",
  isOwned && "ring-2 ring-green-500 ring-offset-2"
)}>
  {/* Card content */}
</Card>
```

### Existing Filter Pattern (Client-Side)
```typescript
// Source: src/lib/api.ts lines 120-139
const applyCardFilters = (cards: PokemonCard[], filters: Record<string, string>): PokemonCard[] => {
  return cards.filter(card => {
    // Handle type filter
    if (filters['types'] && (!card.types || !card.types.includes(filters['types']))) {
      return false;
    }
    
    // Handle subtype filter
    if (filters['subtypes'] && (!card.subtypes || !card.subtypes.includes(filters['subtypes']))) {
      return false;
    }
    
    // Handle rarity filter
    if (filters['rarity'] && card.rarity !== filters['rarity']) {
      return false;
    }
    
    return true;
  });
};
```

### Lazy Loading with Fallback
```typescript
// Source: src/components/CardGrid.tsx lines 317-329
const fallbackCardImage =
  'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="260" height="360" viewBox="0 0 260 360"><rect width="260" height="360" rx="16" fill="%23f4f4f5"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%23a1a1aa" font-family="Inter,Arial" font-size="16">Image Unavailable</text></svg>';

<img
  src={card.images.small || fallbackCardImage}
  alt={card.name}
  className="w-full aspect-[2.5/3.5] object-contain"
  loading="lazy"
  onError={(e) => {
    if (e.currentTarget.src !== fallbackCardImage) {
      e.currentTarget.src = fallbackCardImage;
    }
  }}
/>
```

### Completion Stats Hook (Existing)
```typescript
// Source: src/lib/collection.ts lines 99-124
export function useSetCompletion(
  setCardIds: string[],
  ownedCards: Record<string, boolean>
): CompletionStats {
  return useMemo(() => {
    const total = setCardIds.length;
    if (total === 0) {
      return { owned: 0, missing: 0, total: 0, percentage: 0 };
    }
    
    const owned = setCardIds.filter(id => ownedCards[id]).length;
    const missing = total - owned;
    const percentage = (owned / total) * 100;
    
    return { owned, missing, total, percentage };
  }, [setCardIds, ownedCards]);
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual scroll listeners for fixed headers | CSS `position: sticky` / `fixed` + `backdrop-blur` | CSS3 (2015+) | Browser-optimized, no JS overhead, predictable behavior |
| jQuery for DOM filtering | React useMemo + array methods | React 16.8+ (2019) | Declarative, testable, concurrent-mode compatible |
| Server-side pagination for ALL filters | Hybrid: server pagination, client filtering | Modern SPA era (2020+) | Reduces API calls, instant UX for filters on loaded data |
| Redux for all app state | useState + useMemo for UI-only state | React Hooks era (2019+) | Less boilerplate, co-located state, simpler debugging |
| Class components + lifecycle methods | Functional components + hooks | React 16.8+ (2019) | Less code, easier composition, better tree-shaking |

**Deprecated/outdated:**
- `componentDidMount` / `componentDidUpdate` for filter logic → Use `useEffect` + `useMemo`
- `this.setState` callback chains → Use `useEffect` with dependencies
- Manual shouldComponentUpdate → React.memo + useMemo handle optimization
- Inline arrow functions in render → Extract handlers OR accept minor performance cost (React 18 optimizes well)

## Validation Architecture

> Note: Validation enabled per `.planning/config.json` workflow.nyquist_validation: true

### Test Framework
| Property | Value |
|----------|-------|
| Framework | No test framework detected |
| Config file | None — see Wave 0 gaps |
| Quick run command | N/A — no tests exist |
| Full suite command | N/A — no tests exist |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ALBM-01 | Album grid renders responsive layout for selected set | unit | `npm run test src/components/CardGrid.test.tsx -- -t "renders responsive grid"` | ❌ Wave 0 |
| ALBM-02 | Card images load with lazy loading and fallback | unit | `npm run test src/components/CardGrid.test.tsx -- -t "lazy loads images"` | ❌ Wave 0 |
| ALBM-03 | Ownership toggle updates localStorage and UI state | unit | `npm run test src/lib/collection.test.ts -- -t "toggleOwnership"` | ❌ Wave 0 |
| ALBM-04 | Owned cards display green ring indicator | unit | `npm run test src/components/CardGrid.test.tsx -- -t "owned card styling"` | ❌ Wave 0 |
| ALBM-05 | Card size toggle switches between small/medium grid | unit | `npm run test src/components/CardGrid.test.tsx -- -t "size mode toggle"` | ❌ Wave 0 |
| ALBM-06 | Ownership filter shows correct subset of cards | unit | `npm run test src/components/CardGrid.test.tsx -- -t "ownership filter"` | ❌ Wave 0 |
| ALBM-07 | Name search filters cards case-insensitively | unit | `npm run test src/components/CardGrid.test.tsx -- -t "name search"` | ❌ Wave 0 |
| STAT-01 | Footer stats update in real-time with ownership changes | unit | `npm run test src/components/CardGrid.test.tsx -- -t "stats footer updates"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** Manual browser testing (no automated tests available)
- **Per wave merge:** Manual browser testing with all requirements checklist
- **Phase gate:** Manual verification of all 8 requirements before `/gsd-verify-work`

### Wave 0 Gaps
No test infrastructure exists. Recommended additions:

- [ ] **Install Vitest + Testing Library:**
  ```bash
  npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
  ```
- [ ] **Create `vitest.config.ts`:**
  ```typescript
  import { defineConfig } from 'vitest/config'
  import react from '@vitejs/plugin-react'
  import path from 'path'
  
  export default defineConfig({
    plugins: [react()],
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  })
  ```
- [ ] **Create `src/test/setup.ts`:**
  ```typescript
  import '@testing-library/jest-dom'
  
  // Mock localStorage
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  }
  global.localStorage = localStorageMock as any
  ```
- [ ] **Add test scripts to package.json:**
  ```json
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
  ```
- [ ] **Create `src/lib/collection.test.ts`** — unit tests for ownership persistence hooks
- [ ] **Create `src/components/CardGrid.test.tsx`** — component tests for filters, size toggle, stats footer

**Alternative:** Manual testing sufficient for v1 scope given yolo mode + coarse granularity. Defer test infrastructure to post-v1 if time-constrained.

## Virtual Scrolling Decision Framework

**When to add virtual scrolling:** Follow this evidence-based decision tree.

### Decision Criteria
```
IF (ANY of these are TRUE):
  1. Measured performance issue with 200+ card sets:
     - Chrome DevTools shows >100ms main thread blocking during render
     - Lighthouse performance score <90 on target hardware
     - User reports visible lag when scrolling
  
  2. Target set size exceeds 500 cards:
     - No current TCGdex set exceeds 300 cards
     - Future expansions could hit this threshold
  
  3. Mobile performance unacceptable:
     - Tested on low-end Android device (<4GB RAM)
     - Scroll jank visible OR crash from memory pressure

THEN:
  Add @tanstack/react-virtual (recommended over react-window)
  
ELSE:
  Keep current pagination + lazy loading approach
  Re-evaluate after user feedback
```

### If Virtual Scrolling Needed: Implementation Notes

**Library choice: @tanstack/react-virtual 3.13.23**
- Modern API with React 18 support
- Dynamic height cards (pokemon cards vary slightly)
- Better TypeScript types than react-window
- Active maintenance (updated Jan 2025)

**Installation:**
```bash
npm install @tanstack/react-virtual@3.13.23
```

**Minimal implementation pattern:**
```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

const CardGrid = ({ cards }) => {
  const parentRef = useRef<HTMLDivElement>(null)
  
  const rowVirtualizer = useVirtualizer({
    count: Math.ceil(cards.length / COLUMNS),
    getScrollElement: () => parentRef.current,
    estimateSize: () => 400, // estimate card height + gap
    overscan: 2, // render 2 extra rows off-screen
  })
  
  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: rowVirtualizer.getTotalSize() }}>
        {rowVirtualizer.getVirtualItems().map(virtualRow => {
          const startIdx = virtualRow.index * COLUMNS
          const rowCards = cards.slice(startIdx, startIdx + COLUMNS)
          return (
            <div key={virtualRow.index} className="grid grid-cols-5 gap-4">
              {rowCards.map(card => <CardTile key={card.id} card={card} />)}
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

**Complexity trade-offs:**
- ✅ Handles 1000+ cards smoothly
- ❌ Adds bundle size (~8KB gzipped)
- ❌ Complicates keyboard navigation
- ❌ Breaks native browser scroll restoration
- ❌ Requires careful height estimation for accurate scrollbar

**Recommendation for Phase 3:** DO NOT implement virtual scrolling unless performance testing reveals issues. Current pagination + lazy loading sufficient for known TCGdex set sizes (largest: 198 cards).

## Open Questions

### 1. **Performance threshold for largest sets**
   - **What we know:** Largest TCGdex set is Scarlet & Violet base (198 cards); existing CardGrid paginates at 20 cards/page
   - **What's unclear:** With filters removing pagination, does rendering 198 cards simultaneously cause performance issues?
   - **Recommendation:** Test in Wave 0 with SV base set, all filters set to "all", measuring render time + scroll jank. If <100ms render + smooth 60fps scroll, no optimization needed. If >100ms OR jank detected, add virtual scrolling in Wave 1.

### 2. **Stats computation frequency**
   - **What we know:** useMemo optimizes stats derivation; dependencies are [filteredCards, isInCollection, ownedCards]
   - **What's unclear:** Does ownership toggle trigger excessive re-computation when many cards visible?
   - **Recommendation:** Profile with React DevTools Profiler during typical usage (toggle 5-10 cards in quick succession). If stats component re-renders >1x per toggle, investigate useCallback for isInCollection OR extract stats to separate memoized component.

### 3. **Mobile touch interaction for ownership toggle**
   - **What we know:** Existing CardGrid uses hover overlay with Add/Remove button
   - **What's unclear:** On mobile (no hover), does long-press OR direct button tap work intuitively?
   - **Recommendation:** Manual testing on iOS/Android during Wave 1. Consider adding always-visible toggle icon for touch devices: `@media (hover: none) { /* show button without hover */ }`

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/components/CardGrid.tsx`, `src/lib/collection.ts`, `src/lib/api.ts` — patterns verified functional in Phase 1-2
- Package.json dependencies (verified 2026-03-21) — React 18.3.1, @tcgdex/sdk 2.7.1, shadcn/ui components
- npm registry: @tanstack/react-virtual@3.13.23 (published 2025-01), react-window@1.8.10 (last update 2023)

### Secondary (MEDIUM confidence)
- React documentation (react.dev) — useMemo, useState patterns current as of React 18
- MDN Web Docs — CSS Grid, position: fixed, lazy loading attributes
- shadcn/ui documentation (ui.shadcn.com) — Select, Input, Badge component APIs

### Tertiary (LOW confidence)
- Virtual scrolling library comparison based on npm trends + GitHub activity (no direct benchmark available)
- Performance thresholds (100ms, 60fps) based on general web performance best practices, not TCG-app-specific testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in project, versions verified
- Architecture: HIGH - patterns extracted from functional Phase 1-2 codebase
- Pitfalls: HIGH - identified from CardGrid.tsx existing issues + standard React anti-patterns
- Virtual scrolling: MEDIUM - recommendation based on set size analysis, pending actual performance testing
- Testing infrastructure: HIGH - gap assessment clear, no existing framework detected

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (30 days - stable React/TCGdex ecosystem)
