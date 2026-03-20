# Testing Patterns

**Analysis Date:** 2026-03-20

## Test Framework

**Runner:**
- Not detected (no Jest/Vitest/Playwright/Cypress config found at repository root).
- Config: Not applicable (`jest.config.*`, `vitest.config.*`, `playwright.config.*`, `cypress.config.*` not present).

**Assertion Library:**
- Not detected.

**Run Commands:**
```bash
npm run lint            # Current quality gate configured in `package.json`
npm run build           # Type-check + production build in `package.json`
Not applicable          # Watch mode test command not configured
Not applicable          # Coverage command not configured
```

## Test File Organization

**Location:**
- No project test files detected in repository code (`src/`, root, `supabase/`) using `*.test.*` and `*.spec.*` patterns.

**Naming:**
- Pattern not applicable because test files are not present.

**Structure:**
```text
No test directory pattern is currently established.
```

## Test Structure

**Suite Organization:**
```typescript
// Not detected: no `describe`, `it`, or `test` suites in project source files.
```

**Patterns:**
- Setup pattern: Not detected.
- Teardown pattern: Not detected.
- Assertion pattern: Not detected.

## Mocking

**Framework:** Not detected (`vi.mock`/`jest.mock` usage not found in project files).

**Patterns:**
```typescript
// Not detected: no mocking pattern is established in repository code.
```

**What to Mock:**
- No codified project standard exists. If tests are added, mock external API calls from `src/lib/api.ts` and browser storage access in `src/lib/collection.ts`.

**What NOT to Mock:**
- No codified project standard exists. If tests are added, prefer testing pure UI state transitions in components like `src/components/SetGrid.tsx` with minimal mocking.

## Fixtures and Factories

**Test Data:**
```typescript
// Not detected: no fixture/factory modules currently exist.
```

**Location:**
- Not applicable (no fixture directories or files detected).

## Coverage

**Requirements:** None enforced (no coverage tooling or thresholds configured in `package.json` or test config files).

**View Coverage:**
```bash
Not applicable
```

## Test Types

**Unit Tests:**
- Not used (no unit test files detected for utilities in `src/lib/` such as `src/lib/utils.ts` or `src/lib/collection.ts`).

**Integration Tests:**
- Not used (no integration tests detected for API hooks in `src/lib/api.ts`).

**E2E Tests:**
- Not used (no Playwright/Cypress configuration detected).

## Common Patterns

**Async Testing:**
```typescript
// Not detected. Async application logic exists (e.g., `useSets`, `useCards` in `src/lib/api.ts`)
// but there are no async test examples in the repository.
```

**Error Testing:**
```typescript
// Not detected. Error UI paths exist in `src/components/SetGrid.tsx` and
// `src/components/CardGrid.tsx`, but there are no tests validating them.
```

---

*Testing analysis: 2026-03-20*
