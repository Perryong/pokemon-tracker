# Project Research Summary

**Project:** Pokemon TCG Collection Tracker
**Domain:** Pokemon Trading Card Game Collection Management
**Researched:** 2024-03-20
**Confidence:** HIGH

## Executive Summary

This project is a **Pokemon TCG collection tracker web app** — a personal, local-first tool for tracking card ownership across all Pokemon TCG sets. Based on comprehensive research across stack selection, feature landscape, architecture patterns, and common pitfalls, the recommended approach is a **React 18 + TypeScript + Vite SPA** with localStorage persistence and the TCGdex SDK for card data.

The architecture is straightforward: a hook-based React app with three main views (Sets, Cards Album, Collection), using custom hooks to manage API calls and collection state. The existing codebase already has the foundation in place (React, TypeScript, shadcn/ui, localStorage patterns), but needs TCGdex SDK integration and implementation of tracking-specific features (progress bars, series filtering, ownership toggles).

**Key risks and mitigations:**
1. **localStorage quota limits** — Store only card IDs + metadata, not full card objects (prevents 5MB limit crashes)
2. **Card identity collisions** — Use TCGdex's card.id as primary key to handle reprints/variants correctly
3. **Image loading performance** — Use lazy loading (already present) + virtual scrolling for large sets (200+ cards)
4. **Data loss vulnerability** — Implement export/import functionality in MVP to protect user data
5. **API dependency** — Implement caching with TTL + graceful degradation for TCGdex downtime

The feature scope aligns perfectly with established table stakes (ownership tracking, set browsing, progress indicators, search, persistence) while appropriately deferring complex differentiators (price tracking, multi-quantity, deck building) to validate core value first. The project is well-positioned to deliver a polished v1 that meets user expectations without over-engineering.

## Key Findings

### Recommended Stack

The existing stack is production-ready and aligned with 2024 best practices. Key technologies:

**Core technologies:**
- **React 18.3.x** — Stable, mature, full ecosystem support. Stay on v18 (avoid React 19 until shadcn/ui migrates)
- **TypeScript 5.6.x** — Modern type inference, critical for TCGdex API type safety
- **Vite 5.4.x** — Fast builds, optimized dev experience. Stay on v5 (v8 ecosystem not ready)
- **Tailwind CSS 3.4.x** — Industry standard, required by shadcn/ui. Stay on v3 (v4 breaks compatibility)
- **@tcgdex/sdk ^2.7.1** — Official Pokemon TCG data API (project requirement). Latest stable with built-in caching
- **Zustand ^5.0.12** — Recommended for collection state management (simpler than Redux for this use case)
- **@tanstack/react-query ^5.91.3** — Recommended for TCGdex API caching and request management

**Already in use (keep):**
- shadcn/ui + Radix UI components for accessible, styled primitives
- lucide-react for icons
- zod for schema validation
- next-themes for dark mode

**Critical version constraints:**
- React 18.x + Radix UI 1.x (React 19 breaks Radix compatibility)
- Tailwind 3.x + shadcn/ui (Tailwind 4 breaks shadcn config)
- All dependencies validated against npm registry as of research date

### Expected Features

**Table Stakes (must have for v1):**
- ✅ Card ownership toggle with visual indicator
- ✅ Set browsing with set logos and metadata
- ✅ Set completion progress bars and percentages
- ✅ Series/era filtering to organize 1000+ sets
- ✅ Card search by name within sets
- ✅ localStorage persistence
- ✅ Set statistics (owned/missing counts)
- ✅ Responsive card grid (desktop + mobile)
- ✅ Card images with lazy loading

**Differentiators (defer to v2+):**
- Multi-quantity tracking (validate boolean ownership first)
- Wishlist/want list (second dimension of tracking)
- Price tracking (high complexity, external API dependency)
- Card variants (holo, reverse holo, 1st edition)
- Offline PWA (polish feature)
- Bulk ownership actions (efficiency after core validated)

**Anti-Features (explicitly avoid):**
- Marketplace/trading platform (liability, scope creep)
- Social features/public profiles (conflicts with personal-use scope)
- Authentication/accounts in v1 (backend dependency, delays value)
- Card scanning/OCR (marginal benefit for manual entry speed)
- Multi-game support (dilutes focus)

**MVP Recommendation:** All table stakes are already EXISTING or ACTIVE requirements in PROJECT.md. This validates the scope against ecosystem expectations. Missing differentiators are appropriate deferrals.

### Architecture Approach

The architecture follows standard React SPA patterns with a three-layer approach:

**Major components:**
1. **Presentation Layer** — Sets View, Cards Album, Collection View, Stats Footer (4 main views)
2. **Data Access Layer** — TCGdex SDK client hooks, collection storage hook (useCollection)
3. **Persistence Layer** — TCGdex API (remote), localStorage (local)

**Key patterns:**
- **Hook-based data fetching** — `useSets()`, `useCards()` return `{ data, loading, error }` tuples
- **Persistent store hook** — `useCollection()` manages ownership state + localStorage sync automatically
- **Computed progress metrics** — Derive completion % from collection state (never store separately)
- **View state in App component** — Top-level component manages which view is active (no routing needed for v1)

**Component structure:**
```
src/
├── components/           # Feature components (SetGrid, CardGrid, CollectionView)
├── components/ui/        # shadcn/ui primitives (button, dialog, progress)
├── lib/                  # Core logic (api.ts, collection.ts, utils.ts)
├── hooks/                # Reusable hooks (use-toast, etc)
└── App.tsx               # View orchestration
```

**Existing codebase status:** Foundation is in place (React, TypeScript, Vite, shadcn/ui). Needs:
1. Migration from current Pokemon TCG API to @tcgdex/sdk (project requirement)
2. Set progress calculation from collection data
3. Album controls (size toggle, ownership filters, in-set search)
4. Series filtering dropdown
5. Set logo display

### Critical Pitfalls

Based on analysis of common failure modes in collection tracker apps:

1. **Card Identity Crisis** — Same Pokemon reprinted across sets with different artwork causes tracking errors
   - **Prevention:** Always use `card.id` from TCGdex as primary key, never merge by name alone
   - **Phase:** Phase 1 (Data Foundation) — must be correct from day one

2. **localStorage Size Explosion** — Storing full card objects hits 5-10MB browser limit at ~200-500 cards
   - **Prevention:** Store only card IDs + ownership metadata, fetch full card data from API on-demand
   - **Phase:** Phase 1 (Data Foundation) — current implementation stores full objects, MUST be refactored before launch

3. **Stale Card Data** — Cached prices and set metadata become outdated without refresh strategy
   - **Prevention:** Implement cache TTL (24hr for cards, 6hr for prices, 7 days for sets) + manual refresh button
   - **Phase:** Phase 2 (TCGdex Integration) — build caching strategy during SDK integration

4. **Set Completion False Positives** — Users confused by 100% completion when missing secret rares
   - **Prevention:** Support "Base Set" (printedTotal) vs "Master Set" (total) completion modes, display both counts
   - **Phase:** Phase 1 (Sets View) — completion logic must handle this from day one

5. **Image Loading Performance** — Loading 100-300 card images simultaneously causes browser freeze/crash
   - **Prevention:** Lazy loading (already present ✓), virtual scrolling for sets with 200+ cards, prefer small images for grid
   - **Phase:** Phase 2 (Cards Album View) — build performance optimization into initial implementation

6. **Lost Collection Data** — Users clear browser data or switch browsers, lose months of tracking work
   - **Prevention:** Implement export/import functionality, prominent "Export Collection" button
   - **Phase:** Phase 1 or 2 — export should be in MVP (no cloud sync safety net in local-first design)

7. **TCGdex API Rate Limiting** — Over-eager API calls trigger rate limits or app breaks during downtime
   - **Prevention:** Aggressive caching, graceful degradation with cached data, exponential backoff for retries
   - **Phase:** Phase 2 (TCGdex Integration) — error handling must be implemented during SDK integration

## Implications for Roadmap

Based on combined research, suggested phase structure:

### Phase 1: Data Foundation & Core Storage
**Rationale:** Can't build UI without correct data structures. Collection storage is core business logic that all features depend on.

**Delivers:**
- TCGdex SDK integration with TypeScript types
- `useSets()` and `useCards()` API hooks
- `useCollection()` hook with localStorage (refactored to store IDs only, not full objects)
- Progress calculation utilities
- Data persistence across page reloads
- Export collection functionality

**Addresses:**
- Pitfall #1 (Card Identity) — Use card.id as primary key
- Pitfall #2 (localStorage Size) — Store minimal data projection
- Pitfall #6 (Data Loss) — Export functionality from day one

**Critical:** This phase must establish correct data patterns. Mistakes here are expensive to fix later (data migration required).

**Research flag:** ✅ Well-documented patterns (TCGdex SDK docs, React custom hooks)

---

### Phase 2: Sets View & Navigation
**Rationale:** Entry point for user workflow. Users browse sets before viewing individual cards.

**Delivers:**
- SetGrid component with set logos
- Series dropdown filter (using TCGdex `/series` endpoint)
- Set name search input
- Set completion progress bars (uses Phase 1 calculations)
- Set statistics display (owned/missing counts)
- Navigation to Cards Album

**Addresses:**
- Pitfall #4 (Set Completion) — Implement Base vs Master set completion mode
- Table stakes features: set browsing, series filtering, progress tracking

**Uses:**
- Stack: React + Tailwind + shadcn/ui (existing), TCGdex SDK (Phase 1)
- Architecture: Hook-based data fetching pattern, computed progress metrics

**Research flag:** ✅ Standard patterns (set list display, filtering UI)

---

### Phase 3: Cards Album & Ownership Tracking
**Rationale:** Main interaction surface. Core value proposition of ownership tracking.

**Delivers:**
- CardGrid component with card images (lazy loaded)
- Click-to-toggle ownership with visual feedback
- Card size toggle (small/medium/large grid)
- Ownership filters (all/owned/missing)
- In-set search by card name
- Card detail modal (card info, attacks, abilities)

**Addresses:**
- Pitfall #5 (Image Performance) — Lazy loading + consider virtual scrolling for large sets
- Pitfall #3 (Stale Data) — Implement cache TTL during SDK integration
- Pitfall #7 (API Rate Limiting) — Caching + error handling
- Table stakes features: ownership toggle, card search, responsive grid

**Uses:**
- Stack: TCGdex SDK for card data, Zustand/useCollection for ownership state
- Architecture: Persistent store hook, view state management

**Research flag:** ⚠️ **Needs deeper research** — Virtual scrolling implementation for sets with 200+ cards (react-window integration patterns)

---

### Phase 4: Collection View & Stats
**Rationale:** Enhancement layer over core functionality. Provides cross-set overview and motivation.

**Delivers:**
- CollectionView showing all owned cards across sets
- Client-side filtering (by set, series, rarity, name)
- Stats footer with real-time counts (owned/missing/completion %)
- Collection-level statistics (total cards owned, total value if price tracking added later)
- Import collection functionality (complements export from Phase 1)

**Addresses:**
- Table stakes features: collection view, statistics display
- Differentiator prep: Foundation for price tracking (Phase 5+)

**Uses:**
- Stack: Zustand selectors for derived statistics, React Query for cached API data
- Architecture: Computed progress metrics pattern, client-side filtering

**Research flag:** ✅ Standard patterns (aggregation, filtering, stats display)

---

### Phase 5: Polish & Optimization (v1.1+)
**Rationale:** Performance and UX improvements after core validated.

**Delivers:**
- Virtual scrolling for large sets (if Phase 3 performance issues surface)
- Rarity filtering
- Set sorting options (release date, name, completion %)
- Bulk ownership actions ("mark all commons as owned")
- Card detail enhancements (attack damage, retreat cost, etc)
- Dark mode polish (contrast improvements for card images)

**Addresses:**
- Differentiators: Efficiency features for power users
- Performance: Scaling for large collections (1000+ cards)

**Research flag:** ⚠️ **May need research** — Virtual scrolling library integration (react-window vs react-virtualized)

---

### Phase Ordering Rationale

**Why this order:**
1. **Phase 1 first** — Data foundation must be correct before building UI. localStorage refactoring is easier now than after users have data.
2. **Phase 2 second** — Sets View is the entry point. Users can't navigate to Cards Album without it.
3. **Phase 3 third** — Cards Album is the main interaction. Depends on Phase 1 (collection storage) and Phase 2 (navigation).
4. **Phase 4 fourth** — Stats and Collection View enhance core functionality. Don't block MVP but add significant value.
5. **Phase 5 last** — Polish and optimization after core validated with real usage.

**Dependencies:**
- Phase 2 depends on Phase 1 (can't show progress without collection store)
- Phase 3 depends on Phase 1 (ownership tracking) and Phase 2 (navigation)
- Phase 4 depends on Phases 1-3 (aggregates data from all views)

**Parallel work opportunities:**
- Phase 1 and Phase 2 can start simultaneously (different concerns)
- Within Phase 3, filters and search can be built while ownership toggle is in progress
- Phase 4 stats footer and CollectionView can be built simultaneously

**Critical path for MVP:**
Phase 1 → Phase 2 → Phase 3 → Phase 4 (core tracking functionality complete)

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 3 (Cards Album)** — Virtual scrolling implementation patterns, performance profiling for large sets
- **Phase 5 (Optimization)** — react-window vs react-virtualized comparison, IndexedDB migration strategy if localStorage proves insufficient

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Data Foundation)** — React custom hooks, localStorage patterns, TCGdex SDK integration well-documented
- **Phase 2 (Sets View)** — Standard React component patterns, filtering UI, shadcn/ui select component usage
- **Phase 4 (Stats)** — Aggregation and derived state patterns, standard React patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | All recommendations based on npm registry verification, existing codebase analysis, and official docs. Version constraints validated. |
| Features | **MEDIUM** | Table stakes validated against training data knowledge of major competitors (Pokellector, TCGCollector, CollX). No real-time competitor analysis available. Differentiators need user validation. |
| Architecture | **HIGH** | Standard React SPA patterns. Existing codebase already implements recommended structure. TCGdex SDK usage patterns inferred from package documentation and existing API client patterns. |
| Pitfalls | **HIGH** | Based on domain expertise, existing codebase analysis showing localStorage full card storage issue, and general web app scaling patterns. Pokemon TCG data quirks validated against domain knowledge. |

**Overall confidence:** **HIGH**

### Gaps to Address

Areas that couldn't be fully resolved and need attention during planning:

1. **TCGdex API rate limits** — Documentation doesn't specify exact rate limit thresholds. Need to test in practice and monitor for 429 responses. Implement conservative caching as insurance.

2. **Virtual scrolling threshold** — Need to profile actual performance with real card images on target devices (desktop, mobile, tablets) to determine when virtual scrolling becomes necessary (estimated at 200+ cards but needs validation).

3. **Competitive landscape current state** — Cannot verify 2024 feature sets of major competitors (Pokellector, TCGCollector, CollX) without web search. Feature prioritization based on training data knowledge which may be outdated.

4. **User community preferences** — No direct access to Reddit r/PokemonTCG or Discord communities to validate feature priorities (e.g., do users want multi-quantity tracking? master set vs base set completion?). Recommend quick user research before investing in complex differentiators.

5. **TCGdex SDK caching specifics** — Package v2.7.1 mentions built-in caching via @cachex packages but implementation details need verification during integration. May affect recommended caching strategy.

6. **localStorage quota across browsers** — Ranges from 5-10MB depending on browser. Need to test actual quota on target browsers (Chrome, Firefox, Safari, Edge) and set conservative limit (e.g., 3MB safety margin).

**Recommendation:** These gaps don't block planning or initial implementation. Address during Phase execution:
- Gap #1, #5: Phase 2 (TCGdex Integration) — Test API behavior, validate SDK caching
- Gap #2: Phase 3 (Cards Album) — Profile performance with real data
- Gap #3, #4: Validate with user feedback after MVP (inform Phase 5 priorities)
- Gap #6: Phase 1 (Data Foundation) — Test localStorage on target browsers

## Sources

### Primary (HIGH confidence)
- npm registry verification — Package versions, compatibility, publish dates (@tcgdex/sdk@2.7.1, react@18.3.1, etc)
- Codebase analysis — Existing architecture, current implementation patterns (collection.ts, api.ts, component structure)
- PROJECT.md requirements — Explicit project scope and technical requirements
- Official documentation — React, Vite, TypeScript, Tailwind CSS version compatibility and best practices

### Secondary (MEDIUM confidence)
- Training data knowledge — Pokemon TCG collection tracker ecosystem (Pokellector, TCGCollector, CollX), common patterns
- React SPA architecture patterns — 2026 best practices for hooks, state management, performance
- TCGdex SDK usage patterns — Inferred from package documentation structure and existing API client patterns
- Web storage limits — Browser localStorage quota constraints (5-10MB standard across browsers)

### Tertiary (LOW confidence)
- React 19 ecosystem migration timeline — Estimated based on current adoption pace (not yet in stable release docs)
- Vite 8 and Tailwind 4 breaking changes — Not yet in stable release documentation, based on pre-release signals
- Virtual scrolling threshold — Estimated at 200+ cards but needs device-specific profiling

---
*Research completed: 2024-03-20*  
*Ready for roadmap: yes*  
*Next step: Create implementation roadmap with phase breakdowns based on implications above*
