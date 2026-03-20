# Coding Conventions

**Analysis Date:** 2026-03-20

## Naming Patterns

**Files:**
- Use `PascalCase.tsx` for feature-level React components in `src/components/` (examples: `src/components/CardGrid.tsx`, `src/components/CollectionView.tsx`).
- Use `kebab-case.tsx` for reusable UI primitives in `src/components/ui/` (examples: `src/components/ui/alert-dialog.tsx`, `src/components/ui/navigation-menu.tsx`).
- Use `camelCase.ts` for non-UI modules/hooks in `src/lib/` and `src/hooks/` (examples: `src/lib/collection.ts`, `src/hooks/use-toast.ts`).

**Functions:**
- Use `camelCase` for functions and handlers (examples: `handleAddToCollection`, `getCardPrice`, `clearFilters` in `src/components/CardGrid.tsx`).
- Prefix React event handlers with `handle` (examples in `src/App.tsx`, `src/components/SetGrid.tsx`, `src/components/CardDetail.tsx`).
- Prefix custom hooks with `use` (examples: `useSets`, `useCards`, `useCard` in `src/lib/api.ts`; `useCollection` in `src/lib/collection.ts`).

**Variables:**
- Use `camelCase` for local state and constants scoped to modules/components (examples: `selectedSet`, `priceRange`, `processingCards` in `src/components/CardGrid.tsx`).
- Use `SCREAMING_SNAKE_CASE` for module-level constants (examples: `MAX_RETRIES` in `src/lib/api.ts`, `TOAST_LIMIT` in `src/hooks/use-toast.ts`).

**Types:**
- Use `PascalCase` for interfaces and type aliases (examples: `PokemonCard` in `src/lib/api.ts`, `FormFieldContextValue` in `src/components/ui/form.tsx`).
- Prefer explicit interface/type declarations for component props (examples: `NavbarProps` in `src/components/Navbar.tsx`, `CardGridProps` in `src/components/CardGrid.tsx`).

## Code Style

**Formatting:**
- Tool used: Not detected (`.prettierrc*` is not present).
- Follow existing file-local style; the codebase currently contains mixed quote styles:
  - Single quotes in files like `src/components/ui/button.tsx`.
  - Double quotes in files like `src/components/Navbar.tsx` and `src/components/CardDetail.tsx`.
- Use trailing commas in multiline structures where already present (examples in `src/components/CardGrid.tsx` and `src/lib/api.ts`).

**Linting:**
- Tool used: ESLint with TypeScript support in `eslint.config.js`.
- Key rules/config:
  - Extend `@eslint/js` recommended and `typescript-eslint` recommended (`eslint.config.js`).
  - Enforce React Hooks rules via `eslint-plugin-react-hooks` (`eslint.config.js`).
  - Warn on non-component exports for React Refresh (`react-refresh/only-export-components`) in `eslint.config.js`.
  - Ignore `dist` for linting (`eslint.config.js`).
- TypeScript strictness is enabled in `tsconfig.app.json` (`"strict": true`, `"noUnusedLocals": true`, `"noUnusedParameters": true`).

## Import Organization

**Order:**
1. External libraries first (example: `react`, `date-fns`, `lucide-react` in `src/components/SetGrid.tsx`).
2. Internal alias imports using `@/` next (example: UI and lib imports in `src/components/CardGrid.tsx`).
3. Local relative imports where used (example: `./App.tsx` in `src/main.tsx`).

**Path Aliases:**
- Use `@/*` alias for `src/*` configured in `tsconfig.json`, `tsconfig.app.json`, and `vite.config.ts`.
- Prefer alias imports for internal modules in app code (examples across `src/components/*.tsx` and `src/hooks/use-toast.ts`).

## Error Handling

**Patterns:**
- API/data hooks return structured state objects with `{ data, loading, error }` patterns (examples: `useSets`, `useCards`, `useCard` in `src/lib/api.ts`).
- Wrap async operations in `try/catch/finally` and always clear loading flags in `finally` (examples in `src/lib/api.ts`, `src/components/CardGrid.tsx`).
- Surface user-facing failures via in-UI fallback blocks and retry buttons (examples in `src/components/SetGrid.tsx` and `src/components/CardGrid.tsx`).
- Throw explicit `Error` objects for HTTP failure modes (examples in `fetchFromApi` in `src/lib/api.ts`).

## Logging

**Framework:** `console` (`console.error`, `console.log` in `src/lib/api.ts`).

**Patterns:**
- Log structured API failure metadata (status, headers, URL) in `src/lib/api.ts`.
- Log retry attempts for transient network failures in `src/lib/api.ts`.
- Do not introduce additional logging abstraction; continue with lightweight console logging unless a logging library is added.

## Comments

**When to Comment:**
- Add section-divider comments for large files to delineate logical regions (examples in `src/components/Navbar.tsx`, `src/components/CardDetail.tsx`, `src/components/CollectionView.tsx`).
- Add short explanatory comments above non-obvious logic, especially fallback or query-construction logic (examples in `src/lib/api.ts`, `src/lib/collection.ts`).

**JSDoc/TSDoc:**
- Not detected for functions/components in `src/`.
- Continue using TypeScript types/interfaces for API clarity; only add JSDoc when behavior is non-obvious.

## Function Design

**Size:** 
- Utility wrappers are small and focused (example: `cn` in `src/lib/utils.ts`).
- Feature components can be large and contain colocated helpers/state/handlers (examples: `src/components/CardGrid.tsx`, `src/components/CardDetail.tsx`).

**Parameters:**
- Use typed parameter objects for components via `Props` interfaces (examples in `src/components/*.tsx`).
- Use explicit scalar params for utility/handler functions where clarity is higher (examples: `handlePageChange(page: number)` in `src/components/SetGrid.tsx`).

**Return Values:**
- Hooks return object-shaped APIs for consumer ergonomics (examples: `useCollection` in `src/lib/collection.ts`, `useToast` in `src/hooks/use-toast.ts`).
- Guard early with `return null` for unavailable render prerequisites (example: `if (!card) return null;` in `src/components/CardDetail.tsx`).

## Module Design

**Exports:**
- Use named exports for hooks/utils (`src/lib/api.ts`, `src/lib/collection.ts`, `src/lib/utils.ts`).
- Use default export for primary React component per file (examples: `export default SetGrid` in `src/components/SetGrid.tsx`).

**Barrel Files:** 
- Not detected in `src/components/`, `src/lib/`, or `src/hooks/`.

---

*Convention analysis: 2026-03-20*
