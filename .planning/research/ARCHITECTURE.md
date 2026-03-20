# Architecture Research

**Domain:** Pokemon TCG Collection Tracker
**Researched:** 2026-03-20
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Sets    │  │  Cards   │  │Collection│  │  Stats   │    │
│  │  View    │  │  Album   │  │  View    │  │  Footer  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │              │             │           │
├───────┴─────────────┴──────────────┴─────────────┴──────────┤
│                      DATA ACCESS LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌────────────────────────────┐   │
│  │   TCGdex SDK Client  │  │  Collection Storage Hook   │   │
│  │   (Sets, Cards)      │  │  (useCollection)           │   │
│  └──────────┬───────────┘  └────────┬───────────────────┘   │
│             │                        │                       │
├─────────────┴────────────────────────┴───────────────────────┤
│                      PERSISTENCE LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐  ┌─────────────────────────────┐    │
│  │  TCGdex API        │  │  Browser localStorage       │    │
│  │  (Remote)          │  │  (Local)                    │    │
│  └────────────────────┘  └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Sets View** | Display all Pokemon TCG sets with filtering, search, and progress | Grid/list with set logos, completion bars, series filters |
| **Cards Album** | Show all cards in a set with ownership toggle | Responsive grid of card images with click-to-mark |
| **Collection View** | Display user's owned cards across all sets | Filterable list/grid aggregating owned cards |
| **Stats Footer** | Real-time collection metrics | Fixed footer showing owned/missing/completion % |
| **TCGdex SDK Client** | Fetch set and card data from Pokemon TCG API | Async hooks wrapping SDK methods |
| **Collection Store** | Manage ownership state and persistence | React hook with localStorage sync |
| **Search/Filter System** | Enable discovery by name, series, type, rarity | Client-side filtering on fetched data |

## Recommended Project Structure

```
src/
├── components/
│   ├── SetGrid.tsx            # Sets view with series filter
│   ├── CardGrid.tsx           # Cards album for selected set
│   ├── CardDetail.tsx         # Card detail modal
│   ├── CollectionView.tsx     # User's owned cards view
│   ├── CollectionStats.tsx    # Stats/progress display
│   ├── Navbar.tsx             # View navigation
│   └── ui/                    # shadcn/Radix primitives
│       ├── button.tsx
│       ├── dialog.tsx
│       ├── select.tsx
│       ├── input.tsx
│       └── progress.tsx
├── lib/
│   ├── api.ts                 # TCGdex SDK wrapper + types
│   ├── collection.ts          # Collection store hook
│   └── utils.ts               # Helper functions (cn, etc)
├── hooks/
│   └── use-toast.ts           # Toast notification system
├── App.tsx                    # Top-level view orchestration
└── main.tsx                   # React root mount
```

### Structure Rationale

- **components/:** Feature-level UI components that compose views. Each component maps to a user-facing screen or major feature (Sets, Cards, Collection).
- **components/ui/:** Pure presentational primitives from shadcn/ui. No business logic, just styled Radix components.
- **lib/:** Core business logic separated from UI. `api.ts` owns all external data fetching, `collection.ts` owns all ownership state.
- **hooks/:** Reusable React hooks for cross-cutting concerns (toasts, etc).
- **Flat component structure:** No deep nesting because this is a view-centric app with ~6 main screens. Deep folders add navigation overhead without value.

## Architectural Patterns

### Pattern 1: Hook-Based Data Fetching

**What:** Encapsulate API calls in custom React hooks that return `{ data, loading, error }` tuples.

**When to use:** Any time a component needs external data (sets, cards, series list).

**Trade-offs:**
- ✅ Declarative: Component just calls `useSets()` and renders loading/error/data states
- ✅ Reusable: Multiple components can share the same hook
- ✅ Testable: Can mock hooks independently of components
- ❌ Can cause unnecessary re-fetches if not memoized properly
- ❌ Complex data dependencies require careful effect dependencies

**Example:**
```typescript
// lib/api.ts
export const useSets = (filters?: { series?: string }) => {
  const [data, setData] = useState<PokemonSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchSets = async () => {
      try {
        setLoading(true);
        const tcgdex = new TCGdex('en');
        const sets = await tcgdex.fetchSets();
        const filtered = filters?.series 
          ? sets.filter(s => s.series === filters.series)
          : sets;
        setData(filtered);
      } catch (e) {
        setError(e as Error);
      } finally {
        setLoading(false);
      }
    };
    fetchSets();
  }, [filters?.series]);

  return { data, loading, error };
};

// components/SetGrid.tsx
const SetGrid = () => {
  const { data: sets, loading, error } = useSets();
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return <div>{sets.map(set => <SetCard key={set.id} set={set} />)}</div>;
};
```

### Pattern 2: Persistent Store Hook

**What:** Single custom hook that manages collection state and automatically syncs to localStorage.

**When to use:** When you need state that survives page refreshes and is accessed by multiple components.

**Trade-offs:**
- ✅ Single source of truth for collection data
- ✅ Automatic persistence without manual save calls
- ✅ Simple API: `addToCollection()`, `removeFromCollection()`, `isInCollection()`
- ❌ localStorage has size limits (~5-10MB depending on browser)
- ❌ All collection data loads into memory (fine for <10k cards)
- ❌ No undo/redo without additional state management

**Example:**
```typescript
// lib/collection.ts
const STORAGE_KEY = 'pokemon-tcg-collection';

export const useCollection = () => {
  const [collection, setCollection] = useState<Record<string, CollectionCard>>({});
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) setCollection(JSON.parse(stored));
    setIsLoaded(true);
  }, []);

  // Persist on every change
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collection));
    }
  }, [collection, isLoaded]);

  const addToCollection = (card: PokemonCard) => {
    setCollection(prev => ({ ...prev, [card.id]: { ...card, owned: true } }));
  };

  const isInCollection = (cardId: string) => !!collection[cardId];

  return { collection, addToCollection, isInCollection };
};
```

### Pattern 3: Computed Progress Metrics

**What:** Derive completion percentages and counts from collection state rather than storing them separately.

**When to use:** When displaying progress bars, stats footers, or set completion indicators.

**Trade-offs:**
- ✅ Always accurate (can't get out of sync)
- ✅ No duplicate state to maintain
- ✅ Simple to test (pure function)
- ❌ Recomputes on every render unless memoized
- ❌ Requires card count per set from API

**Example:**
```typescript
// lib/collection.ts
export const calculateSetProgress = (
  setId: string,
  totalCards: number,
  collection: Record<string, CollectionCard>
) => {
  const ownedCount = Object.values(collection)
    .filter(card => card.set.id === setId)
    .length;
  
  return {
    owned: ownedCount,
    missing: totalCards - ownedCount,
    percentage: Math.round((ownedCount / totalCards) * 100)
  };
};

// components/SetCard.tsx
const SetCard = ({ set }: { set: PokemonSet }) => {
  const { collection } = useCollection();
  const progress = useMemo(
    () => calculateSetProgress(set.id, set.printedTotal, collection),
    [set.id, set.printedTotal, collection]
  );

  return (
    <div>
      <h3>{set.name}</h3>
      <Progress value={progress.percentage} />
      <span>{progress.owned}/{set.printedTotal} cards</span>
    </div>
  );
};
```

### Pattern 4: View State Management in App Component

**What:** Top-level component manages which view is active and what's selected (set, card, modal state).

**When to use:** Single-page apps with multiple views and shared navigation state.

**Trade-offs:**
- ✅ Simple: No routing library needed for personal app
- ✅ Fast: No URL parsing or route matching overhead
- ✅ Centralized: All view state in one place
- ❌ No browser back/forward support
- ❌ No deep linking to specific sets or cards
- ❌ Can't share URLs with friends

**Example:**
```typescript
// App.tsx
const App = () => {
  const [view, setView] = useState<'sets' | 'cards' | 'collection'>('sets');
  const [selectedSet, setSelectedSet] = useState<PokemonSet | null>(null);
  const [selectedCard, setSelectedCard] = useState<PokemonCard | null>(null);

  return (
    <div>
      <Navbar view={view} onSetView={setView} />
      
      {view === 'sets' && <SetGrid onSetSelect={(set) => {
        setSelectedSet(set);
        setView('cards');
      }} />}
      
      {view === 'cards' && selectedSet && (
        <CardGrid set={selectedSet} onCardSelect={setSelectedCard} />
      )}
      
      {view === 'collection' && <CollectionView />}
      
      <CardDetail card={selectedCard} />
    </div>
  );
};
```

## Data Flow

### Primary Flow: Browse Sets → View Cards → Mark Ownership

```
User clicks set
    ↓
SetGrid → onSetSelect() → App.tsx (setSelectedSet, setView('cards'))
    ↓
CardGrid mounts → useCards(setId) → TCGdex SDK → fetch cards
    ↓
User clicks card image → toggles ownership
    ↓
CardGrid → useCollection() → addToCollection() / removeFromCollection()
    ↓
Collection hook → updates state → syncs to localStorage
    ↓
All components using useCollection re-render (stats, progress bars)
```

### Secondary Flow: View Collection

```
User clicks "Collection" in nav
    ↓
Navbar → onSetView('collection') → App.tsx (setView)
    ↓
CollectionView mounts → useCollection() → reads from state
    ↓
Applies client-side filters (rarity, set, name)
    ↓
Renders owned cards in grid
```

### State Update Pattern

```
User Action (click card)
    ↓
Event Handler (handleCardClick)
    ↓
Collection Hook (addToCollection)
    ↓
State Update (setCollection)
    ↓
├─ Re-render consumers (CardGrid, Stats, SetGrid progress bars)
└─ Persist to localStorage (via useEffect)
```

### Key Data Flows

1. **Set Loading:** App mounts → SetGrid calls useSets() → TCGdex fetches all sets → displays with computed progress from collection
2. **Card Loading:** User selects set → CardGrid calls useCards(setId) → TCGdex fetches set cards → displays with ownership indicators from collection
3. **Ownership Toggle:** User clicks card → checks if in collection → calls add/remove → collection updates → progress bars re-render
4. **Stats Display:** Stats component reads collection hook → computes totals → renders in footer (updates reactively when collection changes)
5. **Search/Filter:** User types in search → filters applied client-side to already-fetched data → no API calls

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k cards | **Current architecture is optimal.** localStorage handles this easily, client-side filtering is instant. |
| 1k-10k cards | **Fine with current approach.** localStorage limit is ~5-10MB; 10k cards as JSON is ~2-3MB. Consider pagination in collection view for perceived performance. |
| 10k-100k cards | **IndexedDB recommended.** localStorage becomes slow to parse. IndexedDB allows querying without loading entire collection into memory. Virtual scrolling required for card grids. |
| Multiple users | **Backend + auth required.** Move collection storage to database with user accounts. Add sync layer to handle offline changes. |

### Scaling Priorities

1. **First bottleneck: Client-side filtering with large collections**
   - **When:** Collection view shows 1000+ owned cards, filtering lags
   - **Fix:** Add virtual scrolling (react-window) to render only visible cards. Move filtering to worker thread if needed.

2. **Second bottleneck: localStorage size limits**
   - **When:** Collection reaches ~8k cards (approaching 5MB JSON)
   - **Fix:** Migrate to IndexedDB with Dexie.js wrapper. Store only card IDs + metadata, fetch full card data on-demand.

3. **Third bottleneck: API rate limits**
   - **When:** Fetching many sets/cards hits TCGdex rate limits
   - **Fix:** Implement request batching and caching layer. Store fetched sets/cards in IndexedDB to avoid refetching on revisit.

## Anti-Patterns

### Anti-Pattern 1: Storing Full Card Objects in Collection

**What people do:** Store entire `PokemonCard` object (with images, attacks, etc) in collection state and localStorage.

**Why it's wrong:**
- Bloats localStorage with duplicate data (card details are fetched from API anyway)
- Makes serialization slow (deep object cloning on every update)
- Collection can exceed localStorage size limits faster

**Do this instead:**
```typescript
// ❌ BAD: Storing full card
const collection: Record<string, PokemonCard> = {
  "xy1-1": { id: "xy1-1", name: "...", images: {...}, attacks: [...], ... }
};

// ✅ GOOD: Store only IDs + user metadata
const collection: Record<string, CollectionMetadata> = {
  "xy1-1": { 
    cardId: "xy1-1", 
    owned: true, 
    quantity: 2, 
    condition: "Near Mint",
    acquiredDate: "2026-03-20"
  }
};

// Fetch full card data from API when needed (or use a join pattern)
```

### Anti-Pattern 2: Separate Progress State

**What people do:** Store completion percentages and counts in separate state variables or localStorage keys.

**Why it's wrong:**
- Creates duplicate source of truth that can desync
- Requires manual updates in multiple places
- Makes bugs hard to trace (which state is correct?)

**Do this instead:**
```typescript
// ❌ BAD: Separate progress state
const [collection, setCollection] = useState({});
const [progress, setProgress] = useState({ owned: 0, total: 0 });

// When adding card, must update both:
addCard(card);
setProgress(prev => ({ ...prev, owned: prev.owned + 1 }));

// ✅ GOOD: Derive from collection
const progress = useMemo(() => {
  const owned = Object.keys(collection).length;
  const total = currentSet.printedTotal;
  return { owned, total, percentage: (owned / total) * 100 };
}, [collection, currentSet]);
```

### Anti-Pattern 3: Fetching Cards One-by-One

**What people do:** When showing a set's cards, loop through card IDs and fetch each individually.

**Why it's wrong:**
- Makes N+1 API requests (one per card)
- Slow to load (serial network requests)
- Hits API rate limits quickly

**Do this instead:**
```typescript
// ❌ BAD: Individual fetches
for (const cardId of set.cardIds) {
  const card = await tcgdex.fetch('cards', cardId); // N requests!
}

// ✅ GOOD: Batch fetch via set endpoint
const setWithCards = await tcgdex.fetch('sets', setId); // 1 request
const cards = setWithCards.cards; // All cards included
```

### Anti-Pattern 4: Using Global State for Everything

**What people do:** Put all state (view, selected set, collection, API data) in a global store like Redux.

**Why it's wrong:**
- Massive overkill for a personal collection tracker
- Adds boilerplate and complexity
- Harder to reason about data flow
- Makes components harder to test in isolation

**Do this instead:**
```typescript
// ❌ BAD: Everything in Redux
const dispatch = useDispatch();
const sets = useSelector(state => state.sets.data);
const loading = useSelector(state => state.sets.loading);
dispatch(fetchSets()); // in useEffect

// ✅ GOOD: Local state + custom hooks
const { data: sets, loading } = useSets(); // Simple, clear
const { collection, addToCollection } = useCollection(); // Encapsulated
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **TCGdex API** | REST API via `@tcgdex/sdk` package | SDK wraps endpoints for sets, cards, series. Returns typed data. No auth required. |
| **Browser localStorage** | Native Web Storage API | Used for collection persistence. 5-10MB limit. Synchronous read/write. |
| **Radix UI primitives** | React component imports | Headless UI components. Style with Tailwind via shadcn/ui wrappers. |
| **Lucide React icons** | Direct imports from `lucide-react` | Tree-shakeable icon set. Import only needed icons. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Component ↔ API layer** | Custom hooks (useSets, useCards) | Components call hooks, hooks return data/loading/error. Unidirectional data flow. |
| **Component ↔ Collection store** | useCollection hook | Components call methods (add/remove), hook manages state + localStorage sync. |
| **View ↔ View (navigation)** | Callback props through App.tsx | Child passes event up (onSetSelect), parent updates state (setView), triggers re-render. |
| **UI primitive ↔ Feature component** | Props interface | Feature components import primitives, pass styling/behavior via props. No direct state coupling. |

## Build Order Recommendations

### Phase 1: Data Foundation
**Why first:** Can't build UI without knowing what data looks like
- Set up TCGdex SDK integration
- Define TypeScript interfaces for Set, Card, Collection
- Build `useSets()` and `useCards()` hooks
- Verify API responses match types

### Phase 2: Collection Storage
**Why second:** Core business logic that UI depends on
- Implement `useCollection()` hook with localStorage
- Add CRUD methods (add/remove/update)
- Build progress calculation utilities
- Test persistence across page reloads

### Phase 3: Sets View
**Why third:** Entry point for user workflow
- Build SetGrid component with set cards
- Add series filter dropdown
- Add name search input
- Wire progress bars (uses Phase 2)

### Phase 4: Cards Album
**Why fourth:** Main interaction surface
- Build CardGrid with card images
- Add click-to-toggle ownership (uses Phase 2)
- Implement size toggle (small/medium cards)
- Add ownership filters (all/owned/missing)

### Phase 5: Stats & Polish
**Why last:** Enhancement layer over core functionality
- Build stats footer with live counts
- Add CollectionView for cross-set owned cards
- Implement card detail modal
- Polish transitions and loading states

**Dependency rationale:**
- Can't build Sets View without API hooks (Phase 1)
- Can't show progress without collection store (Phase 2)
- Cards Album requires Sets View for navigation (Phase 3)
- Stats require both collection store (Phase 2) and rendered views to display in (Phases 3-4)

**Parallel work opportunities:**
- Phase 1 and Phase 2 can be built in parallel (no dependencies)
- Within Phase 3, filter UI can be built while progress bars are in progress
- Phase 5 stats footer and CollectionView can be built simultaneously

## Existing Architecture (Brownfield Notes)

**Current state:** The project already has:
- React + TypeScript + Vite foundation
- shadcn/ui component system fully integrated
- Existing `api.ts` with PokemonSet/PokemonCard types
- Existing `collection.ts` with useCollection hook
- Existing view components (SetGrid, CardGrid, CollectionView, etc)
- Working localStorage persistence pattern

**What needs adjustment for tracker requirements:**
1. **API integration:** Current `api.ts` uses direct fetch to Pokemon TCG API. Needs migration to `@tcgdex/sdk` per project requirements.
2. **Set progress calculation:** Collection data exists but progress bars/completion indicators need to be computed from it.
3. **Album controls:** CardGrid exists but missing size toggle, ownership filters, and in-set search.
4. **Stats footer:** CollectionStats exists but may need real-time updates and fixed positioning.
5. **Set logos:** SetGrid needs to display official set logos (from `set.images.logo` field).
6. **Series filtering:** Sets view needs series dropdown (data from TCGdex series endpoint).

## Sources

**Architecture Analysis:**
- Project codebase analysis (`.planning/codebase/ARCHITECTURE.md`) — HIGH confidence
- Existing code review (`src/App.tsx`, `src/lib/api.ts`, `src/lib/collection.ts`) — HIGH confidence
- PROJECT.md requirements (TCGdex SDK integration, localStorage persistence) — HIGH confidence

**Domain Patterns:**
- React SPA architecture patterns (2026 best practices) — HIGH confidence from training data
- localStorage persistence patterns — HIGH confidence from training data
- Collection tracking UX patterns — MEDIUM confidence from training data + inference

**Pokemon TCG Specific:**
- TCGdex SDK usage patterns — MEDIUM confidence from package documentation patterns
- Set/card data structures — HIGH confidence from existing codebase types

---
*Architecture research for: Pokemon TCG Collection Tracker*
*Researched: 2026-03-20*
