# Phase 2: Sets View & Navigation - Research

**Researched:** 2026-03-21
**Domain:** React UI filtering, series dropdown, live search, progress visualization, navigation patterns
**Confidence:** HIGH

## Summary

Phase 2 builds on the Phase 1 TCGdex adapter and collection persistence layer to deliver a fully functional sets browsing experience. The existing `SetGrid` component already implements most requirements but needs series filtering, live search, and refinements to progress/completion UI.

**Core technical challenges:**
1. **Series filtering** — TCGdex provides series metadata via `useSeries` hook; need series dropdown integrated with existing filter architecture
2. **Live search** — Client-side name filtering with controlled input state and memoized filtering for performance
3. **Progress indicators** — Existing completion calculation from Phase 1 already powers progress bars and badges; UI refinement needed
4. **Navigation contract** — App-level view state (`sets` → `cards`) already established; clicking a set card must trigger `onSetSelect` callback

The SetGrid component already has legality and date filters working, pagination, skeleton loading states, and error handling. Phase 2 adds series dropdown, search input, and polishes completion badges to meet all SETS-01 through SETS-05 requirements.

**Primary recommendation:** Extend existing `SetGrid` filter controls with series dropdown and search input using shadcn Select and Input components. Use controlled state for search with useMemo-based filtering. Enhance completion badge visibility for 100% sets.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Sets Surface Layout**
- Use the existing card-grid style in `SetGrid` as the primary layout (no table/list redesign in this phase).
- Keep set logos/symbols as the visual anchor, with set metadata and completion details underneath.
- Preserve responsive grid behavior across mobile and desktop breakpoints already used by the current component.

**Filtering and Search Behavior**
- Keep a series dropdown as a first-class filter for this phase.
- Keep live set-name search with immediate client-side filtering while typing.
- Retain existing legality and release-date filters where they do not conflict with series/search behavior.

**Progress and Completion Signals**
- Continue rendering owned/total values with a progress bar per set card.
- Keep a distinct completion badge/indicator when a set reaches 100% ownership.
- Use current collection-derived percentage math from phase 1 as the single source of truth.

**Navigation Flow**
- Clicking a set card should navigate directly to the album/cards view for that selected set.
- Preserve current app-level navigation contract (`sets` → `cards`) rather than introducing a new route system in this phase.
- Keep interaction latency low by relying on the existing hooks/data pipeline.

### Claude's Discretion
- Exact filter control placement and spacing refinements within existing layout constraints.
- Empty/loading copy details and minor badge/label wording.
- Internal helper extraction for filter composition/search normalization.

### Deferred Ideas (OUT OF SCOPE)
- Advanced set sorting/grouping strategies beyond current requirements (can be future UX enhancement).
- URL-based routing/deep-linking for sets (out of scope for this phase).
- Collection analytics expansion beyond per-set completion bars.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SETS-01 | User can view all available Pokemon TCG sets with official logos | SetGrid already renders sets with logos via `set.images.logo` from TCGdex; validated working in Phase 1 |
| SETS-02 | User can filter sets by series using a dropdown | TCGdex provides `useSeries` hook; need to add series Select control and series filter to existing filter composition logic |
| SETS-03 | User can search sets by name with live filtering as they type | Add controlled Input component with client-side name filtering; use memoization for performance with 100+ sets |
| SETS-04 | User sees per-set collection progress bars based on owned cards versus set total | Existing `completionBySet` useMemo calculation already computes `owned/total/percentage`; Progress component already renders |
| SETS-05 | User sees a distinct completion indicator when a set reaches 100% ownership | Current code renders "Complete" badge when `percentage === 100`; need to enhance visibility/styling for discoverability |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 18.3.1 | UI framework | Established in brownfield codebase |
| TypeScript | 5.5.3 | Type safety | Established with strict mode |
| shadcn/ui | Latest (Radix 1.x) | Component library | Project standard for all UI components |
| @tcgdex/sdk | 2.7.1 | TCG data source | Phase 1 established; provides series metadata via `fetch('series')` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 0.446.0 | Icons | Already installed; use for search icon in input field |
| date-fns | 3.6.0 | Date formatting | Already used in SetGrid for releaseDate display |
| class-variance-authority | 0.7.0 | Conditional styling | Already used with shadcn components |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Client-side search | Server-side search endpoint | TCGdex returns all sets (~100); client-side filtering faster and simpler |
| Controlled input state | Uncontrolled input with refs | Controlled state standard React pattern; easier to test and compose with filters |
| useMemo filtering | Re-filter on every render | Performance degrades with 100+ sets; memoization is React best practice |

**Installation:**
All required packages already installed. No new dependencies needed.

**Version verification:** Verified against package.json on 2026-03-21. React 18.3.1, shadcn/ui components using Radix UI 1.x primitives.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── components/
│   ├── SetGrid.tsx           # MODIFY: Add series filter, search input, enhance completion badge
│   └── ui/                   # Existing shadcn components (Select, Input, Badge, Progress)
├── lib/
│   ├── api.ts                # EXISTING: useSets, useSeries hooks already implemented in Phase 1
│   ├── collection.ts         # EXISTING: useCollection with ownedCards map
│   └── types.ts              # EXISTING: PokemonSet, Series types
```

### Pattern 1: Composed Filter State
**What:** Manage multiple independent filter controls (series, search, legality, dates) as separate state variables combined into filters object
**When to use:** Multi-faceted filtering UI where each filter is independent
**Example:**
```typescript
// SetGrid.tsx
const [seriesFilter, setSeriesFilter] = useState<string | null>(null);
const [searchQuery, setSearchQuery] = useState<string>('');
const [legalityFilter, setLegalityFilter] = useState<string | null>(null);

// Compose filters object
const filters: Record<string, string> = {};
if (legalityFilter === 'standard') {
  filters['legalities.standard'] = 'legal';
}
// Note: Series and search filters applied client-side, not in filters object
```

### Pattern 2: Controlled Search Input with Memoized Filtering
**What:** Search input with controlled state, client-side filtering with useMemo for performance
**When to use:** Live search filtering on lists with 50-500 items
**Example:**
```typescript
// SetGrid.tsx
const [searchQuery, setSearchQuery] = useState('');

// Filter sets by search query (memoized to prevent re-filtering on every render)
const filteredBySearch = useMemo(() => {
  if (!searchQuery.trim()) return sets;
  
  const query = searchQuery.toLowerCase().trim();
  return sets.filter(set => 
    set.name.toLowerCase().includes(query)
  );
}, [sets, searchQuery]);

// Render
<Input
  type="text"
  placeholder="Search sets..."
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
  className="w-[240px]"
/>
```

**Why no debouncing:** With client-side filtering on ~100 sets, filtering is instant (<5ms). Debouncing adds complexity without benefit. Only debounce if filtering becomes slow (500+ items or async).

### Pattern 3: Series Dropdown Filter
**What:** Series dropdown using shadcn Select component integrated with existing filter state
**When to use:** Categorical filtering with 5-20 distinct values
**Example:**
```typescript
// SetGrid.tsx
const { series, loading: seriesLoading } = useSeries(); // Hook from Phase 1
const [seriesFilter, setSeriesFilter] = useState<string | null>(null);

// Filter sets by series (applied after useSets returns, before search filtering)
const filteredBySeries = useMemo(() => {
  if (!seriesFilter) return sets;
  return sets.filter(set => set.series === seriesFilter);
}, [sets, seriesFilter]);

// Render
<Select 
  value={seriesFilter || "all"} 
  onValueChange={(value) => setSeriesFilter(value === "all" ? null : value)}
>
  <SelectTrigger className="w-[200px]">
    <SelectValue placeholder="All Series" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">All Series</SelectItem>
    {series.map(s => (
      <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>
    ))}
  </SelectContent>
</Select>
```

**Key insight:** TCGdex `Set` objects have `series: string` field (series name). Filter by name, not series ID, to match set structure.

### Pattern 4: Enhanced Completion Badge
**What:** Make 100% completion badge more visually distinct than current implementation
**When to use:** Drawing attention to completed sets for user satisfaction
**Example:**
```typescript
// SetGrid.tsx (within set card mapping)
{completion.percentage === 100 && (
  <Badge 
    className="border-emerald-500 bg-emerald-100 text-emerald-700 font-semibold" 
    variant="outline"
  >
    ✓ Complete
  </Badge>
)}
```

**Alternative approach:** Add subtle animation or glow effect using tailwindcss-animate (already installed).

### Pattern 5: Filter Composition Chain
**What:** Apply multiple filters sequentially using memoized intermediate results
**When to use:** Multiple independent filters that can be short-circuited
**Example:**
```typescript
// 1. useSets applies API-level filters (legality, date range)
const { sets, loading, error } = useSets(currentPage, pageSize, apiFilters);

// 2. Apply series filter (client-side)
const filteredBySeries = useMemo(() => {
  if (!seriesFilter) return sets;
  return sets.filter(set => set.series === seriesFilter);
}, [sets, seriesFilter]);

// 3. Apply search filter (client-side)
const filteredBySearch = useMemo(() => {
  if (!searchQuery.trim()) return filteredBySeries;
  const query = searchQuery.toLowerCase().trim();
  return filteredBySeries.filter(set => 
    set.name.toLowerCase().includes(query)
  );
}, [filteredBySeries, searchQuery]);

// 4. Render final filtered list
{filteredBySearch.map(set => ...)}
```

**Performance:** With ~100 sets, filtering chain runs in <10ms total. useMemo prevents re-filtering when unrelated state changes (e.g., page navigation).

### Anti-Patterns to Avoid
- **Debouncing search with short delay (<300ms):** Adds perceived lag without performance benefit for client-side filtering
- **Filtering in render loop:** Always use useMemo for filter operations to prevent unnecessary recalculation
- **Storing filtered results in state:** Derived data should be computed in render, not stored; creates sync bugs
- **Series filter by ID when sets store name:** TCGdex sets have `series: string` (name), not `seriesId`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Search input UI | Custom input with icon positioning | shadcn Input + lucide-react icon | shadcn Input has consistent styling; custom positioning fragile |
| Dropdown filter | Custom select with keyboard navigation | shadcn Select (Radix Primitive) | Radix handles accessibility, keyboard nav, focus management — 100+ edge cases |
| Progress bars | Custom div with width percentage | shadcn Progress component | Consistent styling, ARIA labels, theme integration |
| Badge variants | Custom badge classes | shadcn Badge with variant prop | Supports theme switching, consistent with existing UI |
| String normalization for search | Custom regex/trim logic | `toLowerCase().trim().includes()` | Simple, fast, handles 99% of use cases |

**Key insight:** shadcn/ui components are already installed and battle-tested. Building custom filter controls would duplicate ~500 lines of accessibility and styling code.

## Common Pitfalls

### Pitfall 1: Series Filter Mismatch (ID vs Name)
**What goes wrong:** Series dropdown uses series ID but set.series field contains series name string
**Why it happens:** TCGdex `Set` objects from `fetch('sets')` endpoint contain `series: string` (name), not `seriesId`. Only full `Set` from `fetch('sets', setId)` has `serie: SerieResume` object.
**How to avoid:** 
- Filter sets by `set.series === seriesName` not `set.seriesId === seriesId`
- Series dropdown should map series names, not IDs
- Verify with console log: `sets[0].series` returns `"Sword & Shield"` not `"swsh"`
**Warning signs:**
- Series filter returns zero results
- Filter works for some series but not others
- `set.seriesId` is undefined in SetGrid

### Pitfall 2: Search Input Uncontrolled → Controlled Warning
**What goes wrong:** React warning "component is changing an uncontrolled input to be controlled"
**Why it happens:** Input `value` prop starts as `undefined` then becomes controlled string
**How to avoid:**
- Initialize search state with empty string: `useState('')` not `useState()`
- Always provide `value={searchQuery || ''}` to Input component
- Never conditionally render Input based on search state
**Warning signs:**
- Console warning about controlled/uncontrolled
- Input cursor jumps to end while typing
- Input value resets unexpectedly

### Pitfall 3: useMemo Dependency Array Missing Filters
**What goes wrong:** Filtered results don't update when filter state changes
**Why it happens:** useMemo dependency array missing filter state variables
**How to avoid:**
- Include ALL filter variables in dependency array: `[sets, seriesFilter, searchQuery]`
- Use ESLint react-hooks/exhaustive-deps rule (already configured in project)
- Test: change filter and verify filtered results update
**Warning signs:**
- Filter controls change but displayed sets don't update
- Need to change page or refresh to see filter results
- ESLint warning about missing dependencies

### Pitfall 4: Case-Sensitive Search
**What goes wrong:** Searching "sword" doesn't match "Sword & Shield" sets
**Why it happens:** String comparison without normalization
**How to avoid:**
- Always normalize both search query AND set name: `query.toLowerCase()` and `set.name.toLowerCase()`
- Trim whitespace from query before filtering: `query.trim()`
- Use `.includes()` for partial matching, not `===`
**Warning signs:**
- User reports "search doesn't work"
- Search requires exact capitalization
- Search fails with leading/trailing spaces

### Pitfall 5: Filter Composition Order
**What goes wrong:** Search filter runs before series filter, causing performance issues or incorrect results
**Why it happens:** Filter chain order matters; applying expensive filters first wastes computation
**How to avoid:**
- Apply most restrictive filters first (series narrows ~100 sets → ~15)
- Apply search filter last (operates on smaller result set)
- Chain useMemo calls in dependency order: series depends on sets, search depends on series-filtered
**Warning signs:**
- Filtering feels slow when typing
- Results incorrect when multiple filters active
- Filter A clears results from Filter B

## Code Examples

Verified patterns from existing codebase and React best practices:

### Series Filter Integration
```typescript
// SetGrid.tsx - Add to existing filter controls section
import { useSeries } from '@/lib/api';

const SetGrid: React.FC<SetGridProps> = ({ onSetSelect }) => {
  // Existing state
  const [currentPage, setCurrentPage] = useState(1);
  const [legalityFilter, setLegalityFilter] = useState<string | null>(null);
  
  // NEW: Series filter state
  const [seriesFilter, setSeriesFilter] = useState<string | null>(null);
  const { series, loading: seriesLoading } = useSeries();
  
  // Build API-level filters (legality, dates)
  const filters: Record<string, string> = {};
  if (legalityFilter) {
    if (legalityFilter === 'standard') {
      filters['legalities.standard'] = 'legal';
    } else if (legalityFilter === 'expanded') {
      filters['legalities.expanded'] = 'legal';
    }
  }
  
  const { sets, totalSets, loading, error } = useSets(currentPage, pageSize, filters);
  
  // NEW: Apply series filter client-side
  const filteredSets = useMemo(() => {
    if (!seriesFilter) return sets;
    return sets.filter(set => set.series === seriesFilter);
  }, [sets, seriesFilter]);
  
  // Render series dropdown
  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">Pokémon TCG Sets</h1>
        
        <div className="flex flex-wrap gap-2">
          {/* NEW: Series dropdown */}
          <Select 
            value={seriesFilter || "all"} 
            onValueChange={(value) => setSeriesFilter(value === "all" ? null : value)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Series" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Series</SelectItem>
              {series.map(s => (
                <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {/* Existing filters... */}
        </div>
      </div>
      
      {/* Render filteredSets instead of sets */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {filteredSets.map(set => (
          <Card key={set.id} onClick={() => onSetSelect(set)}>
            {/* ... */}
          </Card>
        ))}
      </div>
    </div>
  );
};
```

### Live Search Input
```typescript
// SetGrid.tsx - Add to filter controls
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';

const SetGrid: React.FC<SetGridProps> = ({ onSetSelect }) => {
  // NEW: Search state
  const [searchQuery, setSearchQuery] = useState('');
  
  // Apply filters in chain: series → search
  const filteredBySeries = useMemo(() => {
    if (!seriesFilter) return sets;
    return sets.filter(set => set.series === seriesFilter);
  }, [sets, seriesFilter]);
  
  const filteredBySearch = useMemo(() => {
    if (!searchQuery.trim()) return filteredBySeries;
    const query = searchQuery.toLowerCase().trim();
    return filteredBySeries.filter(set => 
      set.name.toLowerCase().includes(query)
    );
  }, [filteredBySeries, searchQuery]);
  
  // Render
  return (
    <div className="flex flex-wrap gap-2">
      {/* Series dropdown */}
      <Select>...</Select>
      
      {/* NEW: Search input */}
      <div className="relative">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search sets..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-8 w-[240px]"
        />
      </div>
      
      {/* Clear filters button */}
      {(seriesFilter || searchQuery || legalityFilter) && (
        <Button variant="ghost" onClick={() => {
          setSeriesFilter(null);
          setSearchQuery('');
          setLegalityFilter(null);
        }}>
          Clear Filters
        </Button>
      )}
    </div>
  );
};
```

### Enhanced Completion Badge
```typescript
// SetGrid.tsx - Within set card rendering
const completion = getCompletion(set.id, set.total);

return (
  <Card key={set.id}>
    <CardContent className="p-4">
      {/* Progress section */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">
            Owned {completion.owned} / {completion.total}
          </span>
          <span className="text-xs uppercase tracking-wide text-muted-foreground">
            {completion.percentage.toFixed(0)}%
          </span>
        </div>
        <Progress
          value={completion.percentage}
          aria-label={`Owned ${completion.owned} of ${completion.total} cards in ${set.name}`}
        />
      </div>
      
      {/* Badges section */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1">
          {set.legalities?.standard === 'legal' && (
            <Badge variant="default" className="bg-green-600">Standard</Badge>
          )}
          {set.legalities?.expanded === 'legal' && (
            <Badge variant="secondary">Expanded</Badge>
          )}
        </div>
        
        {/* ENHANCED: More prominent 100% badge */}
        {completion.percentage === 100 && (
          <Badge 
            className="border-emerald-500 bg-emerald-100 text-emerald-700 font-semibold shadow-sm" 
            variant="outline"
          >
            ✓ Complete
          </Badge>
        )}
      </div>
    </CardContent>
  </Card>
);
```

### Empty State with Active Filters
```typescript
// SetGrid.tsx - Empty state handling
{!loading && filteredBySearch.length === 0 && sets.length > 0 && (
  <div className="text-center p-8 bg-muted rounded-lg">
    <h2 className="text-2xl font-semibold mb-2">No Sets Found</h2>
    <p className="mb-4">
      No sets match your current filters
      {searchQuery && ` for "${searchQuery}"`}
      {seriesFilter && ` in ${seriesFilter}`}.
    </p>
    <Button onClick={() => {
      setSearchQuery('');
      setSeriesFilter(null);
      setLegalityFilter(null);
    }}>
      Clear Filters
    </Button>
  </div>
)}

{!loading && sets.length === 0 && (
  <div className="text-center p-8 bg-muted rounded-lg">
    <h2 className="text-2xl font-semibold mb-2">No Sets Available</h2>
    <p className="mb-4">Unable to load Pokémon TCG sets.</p>
  </div>
)}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Debounced search inputs | Immediate filtering with useMemo | React 18 (2022) | Concurrent rendering makes synchronous filtering feel instant |
| Uncontrolled inputs with refs | Controlled inputs with state | React 16.8+ hooks (2019) | Easier to compose with other state, better for forms |
| Custom select components | Radix Primitives (shadcn/ui) | 2023-2024 | Accessibility built-in, keyboard navigation, screen reader support |
| Filter state in Redux/context | Local component state | React hooks era (2019+) | Simpler for component-scoped filters; lift only when needed |

**Deprecated/outdated:**
- **Class components for filters:** Function components with hooks are standard since 2019
- **Lodash debounce for search:** Native setTimeout or no debouncing for client-side filtering
- **Custom accessibility attributes:** Radix/shadcn handle ARIA automatically

## Open Questions

1. **Should series dropdown show set counts per series?**
   - What we know: useSeries returns series metadata, useSets returns all sets
   - What's unclear: Whether to compute and display count like "Sword & Shield (23)"
   - Recommendation: Defer to Phase 2 planning; adds complexity but improves UX

2. **Should search match set IDs in addition to names?**
   - What we know: Power users might search "swsh1" instead of "Sword & Shield"
   - What's unclear: Whether user expectation includes ID search
   - Recommendation: Start with name-only search; add ID matching if user feedback requests

3. **Should filters persist in localStorage?**
   - What we know: User might want to return to same filter state after refresh
   - What's unclear: Whether this adds value or just creates stale filter confusion
   - Recommendation: Defer to Phase 3+; MVP doesn't require persistence

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None detected — recommend Vitest + React Testing Library |
| Config file | None — Wave 0 task required |
| Quick run command | `npm run test` (after setup) |
| Full suite command | `npm run test -- --run` (after setup) |

**Recommendation for Wave 0:** Install and configure Vitest for fast unit tests:
```bash
npm install -D vitest @testing-library/react @testing-library/user-event jsdom
```

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SETS-01 | Renders all sets with logos | unit | `npm run test SetGrid.test.tsx -t "renders sets with logos"` | ❌ Wave 0 |
| SETS-02 | Series dropdown filters sets | unit | `npm run test SetGrid.test.tsx -t "filters by series"` | ❌ Wave 0 |
| SETS-03 | Search input filters by name | unit | `npm run test SetGrid.test.tsx -t "filters by search query"` | ❌ Wave 0 |
| SETS-04 | Shows progress bars per set | unit | `npm run test SetGrid.test.tsx -t "displays progress bars"` | ❌ Wave 0 |
| SETS-05 | Shows completion badge at 100% | unit | `npm run test SetGrid.test.tsx -t "displays completion badge"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** Quick smoke test — `npm run dev` and manually verify SetGrid renders
- **Per wave merge:** Run full unit test suite (after Wave 0 test setup)
- **Phase gate:** All SETS-01 through SETS-05 tests green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `src/components/SetGrid.test.tsx` — covers SETS-01 through SETS-05
- [ ] `vitest.config.ts` — Vitest configuration with React Testing Library
- [ ] Framework install: `npm install -D vitest @testing-library/react @testing-library/user-event jsdom`
- [ ] `package.json` scripts: Add `"test": "vitest"` and `"test:ui": "vitest --ui"`

## Sources

### Primary (HIGH confidence)
- React 18.3.1 official docs (https://react.dev) — hooks, useMemo, controlled components
- Radix UI documentation (https://radix-ui.com) — Select, Input primitives
- Project codebase analysis — SetGrid.tsx, api.ts, collection.ts, types.ts

### Secondary (MEDIUM confidence)
- shadcn/ui component patterns (https://ui.shadcn.com) — Select and Input examples
- TCGdex SDK Phase 1 research — series structure and hook patterns
- Phase 1 context and implementation — established filter and state patterns

### Tertiary (LOW confidence)
- None — all findings verified against codebase or official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All packages already installed and in use
- Architecture: HIGH - Patterns derived from existing SetGrid implementation
- Pitfalls: HIGH - Verified against common React filtering bugs and codebase structure
- Validation: MEDIUM - No test framework detected; recommendation based on React ecosystem standard

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (30 days; stable React patterns unlikely to change)

---

*Phase: 02-sets-view-navigation*
*Research completed: 2026-03-21*
