# Codebase Structure

**Analysis Date:** 2026-03-20

## Directory Layout

```text
pokemon-tracker - Copy/
├── src/                    # Frontend application source (React + TypeScript)
│   ├── components/         # Feature screens and reusable UI building blocks
│   │   └── ui/             # shadcn/Radix primitive components
│   ├── hooks/              # Reusable React hooks shared across features
│   └── lib/                # Domain/data hooks and utility functions
├── supabase/
│   └── migrations/         # SQL migrations for Supabase/Postgres schema
├── .planning/
│   └── codebase/           # Generated architecture/planning documentation
├── index.html              # Vite HTML host page
├── package.json            # Node scripts and dependency manifest
├── vite.config.ts          # Vite config and alias wiring
├── tsconfig.json           # Root TypeScript references and path aliases
└── eslint.config.js        # ESLint flat config
```

## Directory Purposes

**`src/`:**
- Purpose: Houses all runtime frontend code.
- Contains: Entrypoint files, feature components, UI primitives, hooks, data/client logic.
- Key files: `src/main.tsx`, `src/App.tsx`, `src/lib/api.ts`, `src/lib/collection.ts`.

**`src/components/`:**
- Purpose: Implements feature-level UI modules.
- Contains: Screen components (`SetGrid`, `CardGrid`, `CollectionView`), shared nav/modal/stat components.
- Key files: `src/components/SetGrid.tsx`, `src/components/CardGrid.tsx`, `src/components/CardDetail.tsx`, `src/components/CollectionView.tsx`, `src/components/Navbar.tsx`.

**`src/components/ui/`:**
- Purpose: Central UI primitive library used across features.
- Contains: Button, dialog, tabs, form controls, toast, pagination, and other base components.
- Key files: `src/components/ui/button.tsx`, `src/components/ui/dialog.tsx`, `src/components/ui/select.tsx`, `src/components/ui/toaster.tsx`.

**`src/hooks/`:**
- Purpose: Shared hooks not tied to one feature screen.
- Contains: Toast state management hook.
- Key files: `src/hooks/use-toast.ts`.

**`src/lib/`:**
- Purpose: Domain/data access and utility helpers.
- Contains: API models/hooks, collection storage hook, className util.
- Key files: `src/lib/api.ts`, `src/lib/collection.ts`, `src/lib/utils.ts`.

**`supabase/migrations/`:**
- Purpose: SQL migrations for backend schema and policies.
- Contains: Timestamped migration SQL files.
- Key files: `supabase/migrations/20250518150840_sunny_scene.sql`, `supabase/migrations/20250518150930_empty_silence.sql`.

## Key File Locations

**Entry Points:**
- `src/main.tsx`: React/Vite bootstrap that mounts `<App />`.
- `src/App.tsx`: App shell controlling active view and modal state.
- `index.html`: Browser host document for Vite bundle injection.

**Configuration:**
- `package.json`: Script commands (`dev`, `build`, `lint`, `preview`) and dependencies.
- `vite.config.ts`: React plugin registration and `@` alias to `src`.
- `tsconfig.json`: Root references and alias mapping for `@/*`.
- `tsconfig.app.json`: Frontend TypeScript compiler options (strict mode, JSX, bundler resolution).
- `eslint.config.js`: TypeScript + React hooks linting rules.
- `components.json`: shadcn UI config and alias declarations.

**Core Logic:**
- `src/lib/api.ts`: Pokémon TCG API contracts + fetch/retry hooks.
- `src/lib/collection.ts`: Local collection state/persistence and valuation logic.
- `src/components/CardGrid.tsx`: Card browsing flow with filters and collection actions.
- `src/components/CollectionView.tsx`: Collection search/filter/sort UI and detail modal trigger.

**Testing:**
- Not detected (`*.test.*` / `*.spec.*` files and test config files are not present in repository root or `src/`).

## Naming Conventions

**Files:**
- Feature components use PascalCase filenames: `src/components/CardGrid.tsx`, `src/components/CollectionStats.tsx`.
- Utility and hook files use kebab/lowercase style: `src/hooks/use-toast.ts`, `src/lib/utils.ts`.
- UI primitive files use lowercase kebab-case: `src/components/ui/alert-dialog.tsx`, `src/components/ui/navigation-menu.tsx`.

**Directories:**
- Source directories are lowercase and role-based: `src/components`, `src/hooks`, `src/lib`.
- Generated/planning directories are dot-prefixed for tooling metadata: `.planning/codebase`.

## Where to Add New Code

**New Feature:**
- Primary code: add new screen/container component in `src/components/` and wire visibility/state in `src/App.tsx`.
- Tests: Not applicable in current structure (no established automated test directory or runner config).

**New Component/Module:**
- Implementation: place reusable design-system primitives in `src/components/ui/`; place feature-specific presentational components in `src/components/`.

**Utilities:**
- Shared helpers: add pure utilities to `src/lib/utils.ts` or new modules in `src/lib/`.
- Shared hooks: add cross-feature hooks in `src/hooks/`.
- Remote data hooks/types: extend `src/lib/api.ts` (or split into additional files under `src/lib/` if introducing new data domains).

## Special Directories

**`src/components/ui/`:**
- Purpose: Generated and curated shadcn UI component set.
- Generated: Yes (scaffolded pattern indicated by `components.json`).
- Committed: Yes.

**`supabase/migrations/`:**
- Purpose: Database schema, policy, trigger migrations.
- Generated: Yes (timestamped migration workflow).
- Committed: Yes.

**`dist/`:**
- Purpose: Build artifacts produced by Vite.
- Generated: Yes.
- Committed: No (excluded from lint scope and treated as output).

**`.planning/codebase/`:**
- Purpose: Architecture/planning reference docs for automation workflows.
- Generated: Yes.
- Committed: Yes (intended as project documentation artifacts).

---

*Structure analysis: 2026-03-20*
