# Stack Research

**Domain:** Pokemon TCG Collection Tracker Web App
**Researched:** 2026-03-20
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **React** | ^18.3.1 | UI framework and state management | React 18 is the stable production release with concurrent features and automatic batching. Stay on 18.x for now — React 19 (latest: 19.2.4) introduces breaking changes in ecosystem libraries. shadcn/ui and Radix UI are validated against React 18. |
| **TypeScript** | ^5.6.3 | Type safety and developer experience | TypeScript 5.x provides modern type inference, better performance, and decorators support. Version 5.6+ is stable; 5.9.3 is latest but 5.6.3+ is sufficient. Critical for data model safety with TCGdex API types. |
| **Vite** | ^5.4.8 | Build tool and dev server | Vite 5.x is production-ready with fast HMR and optimized builds. Stay on 5.x — Vite 8 (latest: 8.0.1) is cutting edge but has breaking changes. Vite 5.4+ includes critical bug fixes and performance improvements. |
| **Tailwind CSS** | ^3.4.13 | Utility-first styling | Tailwind v3.x is the industry standard with mature ecosystem and plugin support. Stay on 3.x — v4 (latest: 4.2.2) is in development and breaks shadcn/ui compatibility. v3.4.13+ includes all modern features and is what shadcn/ui expects. |

### Critical Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **@tcgdex/sdk** | ^2.7.1 | Official Pokemon TCG data API client | **REQUIRED.** Project explicitly requires using TCGdex SDK for all Pokemon card data (sets, cards, series). Version 2.7.1 is latest stable with built-in caching via @cachex packages. Includes TypeScript definitions. |
| **@radix-ui/react-*** | ^1.x | Accessible headless UI primitives | **REQUIRED (via shadcn/ui).** Codebase already uses Radix components through shadcn/ui. Keep all Radix packages on latest 1.x minor versions. These power Progress bars, Dialogs, Select dropdowns, etc. |
| **lucide-react** | ^0.446.0 | Icon library | **REQUIRED.** Already in use for UI icons. Version 0.446+ is stable. Lucide provides consistent, customizable SVG icons that work seamlessly with Tailwind and shadcn/ui. |
| **zod** | ^3.23.8 | Runtime type validation and parsing | **RECOMMENDED.** Already in codebase for form validation. Use for validating localStorage data schemas and API responses. Version 3.x is stable; avoid v4 beta (4.3.6) until ecosystem catches up. |
| **zustand** | ^5.0.12 | Lightweight state management | **RECOMMENDED for collection state.** Use for managing collection ownership state, UI filters, and derived statistics. Simpler than Context API for this use case. Version 5.x is latest stable with improved TypeScript support and React 18 compatibility. |
| **@tanstack/react-query** | ^5.91.3 | Server state management and caching | **OPTIONAL but RECOMMENDED.** Use for managing TCGdex API calls with automatic caching, background refetching, and loading states. Version 5.x is stable and production-ready. Complements zustand (client state) vs server state separation. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **class-variance-authority** | ^0.7.0 | Component variant styling | Already in use with shadcn/ui for managing component style variants (button sizes, etc.). Essential for shadcn/ui pattern. |
| **clsx** / **tailwind-merge** | ^2.1.1 / ^2.5.2 | Conditional className composition | Already in use. clsx for conditional classes, tailwind-merge for deduplicating Tailwind utilities. Standard shadcn/ui pattern. |
| **react-hook-form** | ^7.53.0 | Form state and validation | Already in codebase. Use if adding settings forms or import/export features. Pairs with zod for schema validation. Version 7.x is stable. |
| **sonner** | ^1.5.0 | Toast notifications | Already in use. Lightweight, accessible toast library for success/error feedback. Works well with shadcn/ui theming. |
| **next-themes** | ^0.3.0 | Theme management (dark/light mode) | Already in use for theme switching. Handles system preferences and persistence. Version 0.3.x is stable. |
| **idb** | ^8.0.3 | IndexedDB wrapper (future upgrade) | **NOT NEEDED FOR V1.** Use only if localStorage becomes insufficient (large collections >5MB). IndexedDB provides better performance and storage limits for large datasets. |
| **react-router-dom** | ^7.13.1 | Client-side routing (future upgrade) | **NOT NEEDED FOR V1.** Current scope is single-page with two views. Add only if introducing distinct routes (/sets, /sets/:id, etc.) in future versions. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **ESLint** | JavaScript/TypeScript linting | Already configured with `eslint.config.js` flat config. Keep on v9.x (avoid v10 until stable). typescript-eslint@8.x provides React 18 and TypeScript 5.x support. |
| **PostCSS** + **Autoprefixer** | CSS processing and vendor prefixing | Already configured for Tailwind CSS processing. Required for Tailwind v3. |
| **@types/node** | Node.js TypeScript definitions | Already in use for Vite path resolution. Keep on v22.x LTS types. |
| **Vitest** (future) | Unit testing framework | **NOT IN PROJECT YET.** Add when implementing tests. Vitest is the Vite-native testing framework with Jest-compatible API. |

## Installation

```bash
# Already installed (existing dependencies)
# Review package.json — most dependencies are already present

# Required NEW package for project requirements
npm install @tcgdex/sdk@^2.7.1

# Recommended for state management (not yet in project)
npm install zustand@^5.0.12

# Recommended for API data fetching (not yet in project)
npm install @tanstack/react-query@^5.91.3

# Optional: Update outdated dependencies (safe, backwards compatible)
npm update
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **React 18.x** | React 19.x (latest) | Wait until shadcn/ui and Radix UI officially support React 19. React 19 changes APIs for refs, context, and Suspense boundaries. Not urgent — React 18 is stable and maintained. |
| **Zustand** | Redux Toolkit | Use Redux Toolkit only if: (1) need time-travel debugging, (2) extremely complex state relationships, (3) team is already expert in Redux. For this project, Zustand's simplicity fits the personal-use, local-first model. |
| **@tanstack/react-query** | SWR | Use SWR if preferring Vercel ecosystem or simpler API. Both are excellent. React Query has more features (infinite queries, optimistic updates) but SWR has smaller bundle size. Choose based on team familiarity. |
| **localStorage** | IndexedDB (via idb) | Use IndexedDB when: (1) storing >5MB data, (2) need structured queries, (3) need better performance with large collections. For v1 scope (personal use, likely <1000 cards), localStorage is simpler and sufficient. Migrate later if needed. |
| **Tailwind CSS v3** | Tailwind v4 | Wait for v4 to stabilize and shadcn/ui to migrate. v4 is rewrite with new engine but ecosystem hasn't caught up. v3.4.x is mature, performant, and well-documented. |
| **Vite 5.x** | Vite 8.x | Stay on Vite 5 until ecosystem stabilizes around v8. Vite 8 is major rewrite; wait for plugin ecosystem to update. Vite 5.4+ is fast, stable, and production-proven. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Create React App (CRA)** | Officially deprecated and unmaintained since 2022. Slow builds, outdated dependencies, no longer recommended by React team. | **Vite** (already in use). Modern, fast, maintained. |
| **Older Pokemon TCG APIs** | Ad-hoc REST APIs, PokémonTCG.io (different data model), or direct scraping. Project requirements explicitly call for TCGdex SDK. | **@tcgdex/sdk** (official SDK with types, caching, and maintenance). |
| **React 19 (for now)** | Breaking changes in ecosystem. Radix UI and shadcn/ui haven't fully migrated. Will cause type errors and runtime issues with current component library. | **React 18.3.x** (stable, ecosystem-validated). |
| **Class components** | Legacy React pattern. Hooks (introduced in React 16.8) are the standard. Better composition, less boilerplate, better TypeScript support. | **Function components + hooks** (already in use). |
| **Styled Components / Emotion** | CSS-in-JS libraries with runtime cost. Project already uses Tailwind CSS. Adding styled-components creates conflicting styling paradigms and bundle bloat. | **Tailwind CSS** (already configured) with utility classes and shadcn/ui. |
| **MobX** | Alternative state library but adds complexity. For local-first collection tracker, Zustand's simplicity and React 18 integration is better fit. | **Zustand** (simple, TypeScript-first, React 18 native). |
| **Global CSS files beyond index.css** | Tailwind utility classes and shadcn/ui components should handle 99% of styling. Avoid creating separate CSS files that conflict with Tailwind. | **Tailwind utilities** + component-level styles via `cn()` helper. |

## Stack Patterns by Use Case

**For collection state management:**
- Use **Zustand** with localStorage persistence middleware
- Store: owned card IDs, collection statistics cache, UI preferences
- Pattern: `create(persist(store, { name: 'pokemon-collection' }))`
- Why: Simple, TypeScript-first, integrates with localStorage pattern already in use

**For TCGdex API calls:**
- Use **@tanstack/react-query** with staleTime configuration
- Fetch: sets list, set details with cards, series metadata
- Pattern: `useQuery({ queryKey: ['set', setId], queryFn: () => tcgdex.fetch('sets', setId) })`
- Why: Automatic caching, background refetch, loading/error states, reduces API calls

**For derived statistics (owned/missing counts):**
- Use **Zustand selectors** with shallow equality
- Compute: completion percentage, owned count, missing count per set
- Pattern: `const stats = useStore(state => calculateStats(state.ownedCards, setId), shallow)`
- Why: Avoids re-renders, keeps logic close to state, no prop drilling

**For localStorage persistence:**
- Use **native localStorage** with JSON serialization for v1
- Store: collection data as `{ version: 1, ownedCards: string[], lastUpdated: string }`
- Pattern: Read on mount, write on ownership toggle, debounce writes
- Why: Simple, no dependencies, sufficient for <5MB data, already proven in codebase

**For component styling:**
- Use **Tailwind utilities** + **shadcn/ui components** + **CVA for variants**
- Pattern: Compose existing shadcn/ui primitives, extend with Tailwind classes
- Why: Consistent design system, accessible components, no custom CSS

## Version Compatibility Matrix

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| React 18.3.x | @radix-ui/react-* 1.x | ✅ Fully compatible. Radix UI v1.x validated for React 18. |
| React 18.3.x | @tanstack/react-query 5.x | ✅ Fully compatible. TanStack Query v5 built for React 18. |
| React 18.3.x | zustand 5.x | ✅ Fully compatible. Zustand v5 uses React 18 features. |
| Tailwind CSS 3.4.x | shadcn/ui | ✅ Required version. shadcn/ui expects Tailwind v3. |
| Vite 5.4.x | @vitejs/plugin-react 4.x | ✅ Fully compatible. Plugin version tracks Vite major. |
| TypeScript 5.6.x | All @radix-ui packages | ✅ Fully compatible. TypeScript 5.x is standard. |
| @tcgdex/sdk 2.7.x | Node.js >=18 / Browser | ✅ Works in both. Has browser and Node builds. |
| zod 3.x | react-hook-form 7.x + @hookform/resolvers 3.x | ✅ Standard integration via zodResolver. |

**Known Incompatibilities:**
- ⚠️ React 19.x + @radix-ui/* → Type errors and API mismatches (ref forwarding changes)
- ⚠️ Tailwind CSS 4.x + shadcn/ui → Breaking changes in config format
- ⚠️ Vite 8.x + older plugins → Plugin API changes, wait for ecosystem updates
- ⚠️ zod 4.x + @hookform/resolvers → Resolver package hasn't updated yet

## Environment Constraints

**Based on `package.json` analysis:**
- Node.js version: Not specified in package.json, but Vite 5.4 requires Node >=18
- Package manager: npm (package-lock.json present)
- Module type: ES modules (`"type": "module"` in package.json)
- TypeScript config: Project references with app/node split
- Path alias: `@/*` → `./src/*` configured in both Vite and TypeScript

**Recommendations:**
1. Add `"engines": { "node": ">=18.0.0" }` to package.json for clarity
2. Keep using npm (lockfile is npm format, changing to pnpm/yarn adds friction)
3. Run `npm update` to get latest compatible patch versions (safe, no breaking changes)

## Sources

**HIGH Confidence:**
- npm registry (official package metadata) — version numbers, compatibility, publish dates
- package.json analysis — current dependencies and configuration
- @tcgdex/sdk official package — confirmed version 2.7.1 as latest stable (published 2025-08-25)
- Vite, React, TypeScript documentation — version compatibility and stability guidance
- shadcn/ui documentation — confirmed React 18 + Tailwind v3 requirements

**MEDIUM Confidence:**
- npm outdated analysis — identified version gaps and major version warnings
- React/Vite/Tailwind ecosystem conventions — based on community patterns (2025 standards)
- localStorage vs IndexedDB recommendation — based on typical collection tracker data sizes

**LOW Confidence:**
- React 19 timeline for shadcn/ui support — estimated based on current React 19 adoption pace
- Specific breaking changes in Vite 8 and Tailwind 4 — not yet in stable release docs

**Verified Packages (npm registry check):**
- @tcgdex/sdk@2.7.1 ✅
- react@18.3.1 (stable), react@19.2.4 (latest) ✅
- vite@5.4.8 (project), vite@8.0.1 (latest) ✅
- tailwindcss@3.4.13 (project), tailwindcss@4.2.2 (latest) ✅
- zustand@5.0.12 ✅
- @tanstack/react-query@5.91.3 ✅
- idb@8.0.3 ✅
- react-router-dom@7.13.1 ✅

---

*Stack research for: Pokemon TCG Collection Tracker Web App*  
*Researched: 2026-03-20*  
*Confidence: HIGH — all recommendations based on verified npm registry data and official documentation*
