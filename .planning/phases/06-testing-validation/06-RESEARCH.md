# Phase 6: Testing & Validation - Research

**Researched:** 2026-03-22  
**Domain:** Vitest/Testing Library validation hardening for quantity-tracking regression gate  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
## Implementation Decisions

### Regression Gate Strictness
- Phase 6 uses a strict gate: all automated tests must pass before completion.
- Current baseline failures are in-scope and must be fixed during Phase 6 (not deferred).
- Phase completion requires both `npm run test` and `npm run build` to pass.
- Do not ship with known failing tests.

### Required Test Coverage Boundaries
- `TESTQ-02` coverage must be comprehensive:
  - increment, decrement, fast toggle, and zero-floor behavior
  - boundary checks at `0` and `999`
  - persistence assertions for quantity updates
- `TESTQ-03` must include automated regression coverage for:
  - set browsing
  - filters
  - localStorage persistence
  - album ownership interactions
- Cross-view consistency assertions are required after quantity updates:
  - `CardGrid`, `SetGrid`, `CollectionView`, and `CollectionStats` must agree on unique-vs-total semantics.
- Migration validation must include realistic large-payload automation (thousands of cards).

### Release Evidence Policy
- Automated evidence (`npm run test` + `npm run build`) is sufficient for Phase 6 sign-off.
- No additional manual smoke checklist is required for phase completion.
- If optional manual checks are run, they are informational and do not replace automated gates.

### Error/Failure Handling in Phase 6
- Fix root causes in tests or implementation; avoid relaxing assertions just to pass.
- Keep behavior contracts from Phases 4/5 intact while correcting regressions.
- Prefer explicit assertion correctness over brittle timing assumptions in UI tests.

### Scope Guardrails
- No new user-facing features in Phase 6.
- Focus is validation, regression hardening, and correctness only.
- Deferred feature ideas remain out of scope.

### Claude's Discretion
No explicit `## Claude's Discretion` section exists in `06-CONTEXT.md`.

### Deferred Ideas (OUT OF SCOPE)
## Deferred Ideas

- Manual numeric quantity input, keyboard shortcuts, and advanced duplicate workflows remain outside Phase 6.
- Any new feature request discovered during testing should be logged for future milestone planning, not implemented in this phase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TESTQ-01 | Quantity migration logic is covered by automated tests for normal and edge-case payloads | Existing `migration.test.ts` is already strong; add larger deterministic payload and mount-level integration to satisfy “realistic thousands” validation confidently |
| TESTQ-02 | Quantity controls are covered by automated tests (increment, decrement, 0-floor, fast toggle behavior) | Baseline fix first (`jest-dom` matcher setup + stable mocks), then expand `CardGrid.test.tsx` and `collection.test.ts` for 0/999 boundaries + persistence assertions |
| TESTQ-03 | Existing v1.0 core behaviors (set browsing, filters, persistence) remain verified after quantity changes | Add targeted regression suites for `SetGrid` filtering/browsing, app-level persistence remount behavior, and cross-view unique-vs-total consistency |
</phase_requirements>

## Summary

Current failure signal is precise and reproducible: `npm run test` fails with 6 failures in `src/components/__tests__/CardGrid.test.tsx`, all rooted in matcher/runtime setup (`Invalid Chai property: toBeInTheDocument`) before business assertions can execute. This is a test harness issue first, not a quantity-feature behavior failure. A secondary risk was also observed: `vi.mock("@/hooks/use-toast")` is declared inside `beforeEach`, and Vitest warns this hoist behavior will become an error in future versions.

Minimal-risk strategy: fix the harness first (add `@testing-library/jest-dom` and a Vitest setup file, move module mocks to top-level), then only tighten/extend tests with deterministic, behavior-focused assertions. Keep implementation changes minimal unless a verified contract mismatch appears. This approach honors the locked “fix root causes, don’t relax assertions” decision while unblocking all downstream coverage work.

For coverage completion, reuse existing test surfaces (`CardGrid.test.tsx`, `collection.test.ts`, `migration.test.ts`) and add a small number of high-value regression suites for `SetGrid` and app-level persistence/remount behavior. Enforce release evidence by requiring both `npm run test` and `npm run build` at phase gate, with explicit artifacts in PR/phase summary.

**Primary recommendation:** Execute Phase 6 in two plans: (1) baseline stabilization + TESTQ-02 completion, then (2) TESTQ-03 regression expansion + strict release evidence gate.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vitest | 4.1.0 | Test runner/assertions/mocking | Already project standard; fast unit + component testing in Vite ecosystem |
| @testing-library/react | 16.3.2 | React component rendering and DOM querying | Existing test style already built around RTL |
| @testing-library/jest-dom | 6.9.1 | DOM matchers (`toBeInTheDocument`, `toBeDisabled`, etc.) | Direct fix for current matcher failure; canonical matcher extension for RTL ergonomics |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @testing-library/user-event | 14.6.1 | User-like interaction simulation | Use for toggle/filter interaction regressions where fidelity matters |
| happy-dom | 20.8.4 | DOM environment for Vitest | Keep current environment for test speed and compatibility |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@testing-library/jest-dom` | Plain Chai/`expect(...).toBeTruthy()` | Lower setup cost, but weaker intent/readability and less semantic UI assertions |
| `fireEvent` everywhere | More `user-event` | More realistic interactions but slower; use selectively for critical workflow tests |

**Installation:**
```bash
npm install -D @testing-library/jest-dom
```

**Version verification (npm registry):**
- `vitest@4.1.0` — published 2026-03-12
- `@testing-library/react@16.3.2` — published 2026-01-19
- `@testing-library/user-event@14.6.1` — published 2025-01-21
- `happy-dom@20.8.4` — published 2026-03-12
- `@testing-library/jest-dom@6.9.1` — published 2025-10-01

## Architecture Patterns

### Recommended Project Structure
```text
src/
├── components/
│   └── __tests__/
│       ├── CardGrid.test.tsx                 # Quantity control behavior (TESTQ-02)
│       ├── SetGrid.regression.test.tsx       # Browsing + filter regressions (TESTQ-03)
│       └── App.persistence-regression.test.tsx # Remount/localStorage behavior (TESTQ-03)
├── lib/
│   └── __tests__/
│       ├── collection.test.ts                # Quantity API + persistence contract
│       └── migration.test.ts                 # Large-payload migration safety
└── test/
    └── setup.ts                              # jest-dom + global test setup/mocks
```

### Pattern 1: Harness-first stabilization
**What:** Fix test runtime/matcher setup and hoisted-mock hygiene before changing feature assertions.  
**When to use:** Whenever failures indicate assertion/runtime errors rather than product behavior mismatches.  
**Example:**
```ts
// vitest.config.ts
test: {
  environment: 'happy-dom',
  globals: true,
  setupFiles: ['src/test/setup.ts'],
}
```

```ts
// src/test/setup.ts
import '@testing-library/jest-dom/vitest';
```

### Pattern 2: Contract-focused UI assertions (not index-based)
**What:** Assert by accessible labels/text/roles tied to user-visible contracts; avoid brittle array index assumptions.  
**When to use:** Quantity controls and filters where UI order may shift with sorting/filtering.  
**Example:**
```ts
const card = screen.getByText('Blastoise').closest('[data-testid="card-tile"]');
const minus = within(card!).getByLabelText('Decrease quantity');
expect(minus).toBeDisabled();
```

### Anti-Patterns to Avoid
- **Assertion downgrades to bypass setup issues:** Do not replace semantic matchers with weaker checks just to pass.
- **Mock definitions inside hooks (`beforeEach`) for module mocks:** Vitest warns this will hard-fail in future.
- **Index-coupled selectors (`buttons[1]`) for behavior-critical tests:** Breaks with harmless UI reorder.

## Don’t Hand-Roll

| Problem | Don’t Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DOM presence/disabled assertions | Custom helper utilities around `element !== null` | `@testing-library/jest-dom` matchers | Better failure output, semantic intent, standard ecosystem pattern |
| Interaction timing loops | Manual `setTimeout` polling wrappers | `waitFor` + RTL queries | Less flake, aligned with Testing Library async model |
| Complex in-memory fixture generators in each test | Repeated ad-hoc card map builders | Shared deterministic fixture factory functions | Easier large-payload validation and reproducibility |

**Key insight:** The highest risk in this phase is flaky/fragile test infrastructure, not missing business logic; use mature testing utilities to reduce incidental complexity.

## Common Pitfalls

### Pitfall 1: Matcher runtime mismatch (`toBeInTheDocument`)
**What goes wrong:** Chai cannot resolve jest-dom matcher; tests fail before behavior assertions.  
**Why it happens:** No `@testing-library/jest-dom` import in Vitest setup (`setupFiles` currently empty).  
**How to avoid:** Add setup file and import `@testing-library/jest-dom/vitest`; keep this in shared config.  
**Warning signs:** Error text `Invalid Chai property: toBeInTheDocument` in multiple tests.

### Pitfall 2: Hoisted module mocks declared inside test lifecycle blocks
**What goes wrong:** Mock behavior becomes confusing and future Vitest versions may error.  
**Why it happens:** `vi.mock()` inside `beforeEach` in `CardGrid.test.tsx`.  
**How to avoid:** Move all `vi.mock()` calls to top-level and mutate return values in `beforeEach` only.  
**Warning signs:** Vitest warning about hoisted nested mock calls.

### Pitfall 3: Fragile selectors tied to render order
**What goes wrong:** Tests pass/fail based on card order or filtering side-effects, not requirement behavior.  
**Why it happens:** Assertions using array indexes from `getAllBy*`.  
**How to avoid:** Scope queries to named card containers or roles/labels with `within()`.  
**Warning signs:** Non-deterministic failures after unrelated UI sorting/filter updates.

## Code Examples

Verified in-repo patterns and required adjustments:

### Fix matcher setup for Vitest + RTL
```ts
// Source: src/test/setup.ts (new)
import '@testing-library/jest-dom/vitest';
```

### Stable quantity persistence assertion
```ts
// Source pattern: src/lib/__tests__/collection.test.ts
act(() => result.current.setQuantity('card-1', 2));
const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
expect(stored.cardQuantities['card-1']).toBe(2);
```

### Large-payload migration validation (deterministic)
```ts
// Source pattern: src/lib/__tests__/migration.test.ts
const ownedCards: Record<string, boolean> = {};
for (let i = 0; i < 10000; i++) ownedCards[`card-${i}`] = i % 3 === 0;
const migrated = migrateV1ToV3({ version: 1, ownedCards });
expect(Object.keys(migrated.cardQuantities).length).toBeGreaterThan(3000);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Boolean ownership only | Quantity-backed ownership (`quantity > 0`) | Phase 4/5 | Tests must validate unique-vs-total semantics across views |
| Ad-hoc component assertions | Contract + semantic matcher assertions | Phase 6 target | Lower flake, clearer regression intent |
| Single-surface checks | Cross-view consistency assertions | Phase 5+6 | Prevents semantic drift across `CardGrid`, `SetGrid`, `CollectionView`, `CollectionStats` |

**Deprecated/outdated for this phase:**
- “Fix by loosening assertions” — explicitly disallowed by locked decisions.
- “Manual-only smoke signoff” — insufficient; gate is automated (`npm run test` + `npm run build`).

## TESTQ Coverage Map (Implementable Target)

### TESTQ-02 (Quantity controls)
| Behavior | Suite/File | Concrete Assertions |
|----------|------------|---------------------|
| Increment/decrement buttons | `src/components/__tests__/CardGrid.test.tsx` | `incrementQuantity`/`decrementQuantity` called for selected card; UI qty badge updates |
| Zero-floor | `CardGrid.test.tsx` + `src/lib/__tests__/collection.test.ts` | decrement at `0` remains `0`; minus button disabled; storage omits zero key |
| Fast toggle `0 ↔ 1` / `>1 -> 0` | `CardGrid.test.tsx` | Add button sets owned to qty=1; remove from qty>1 clears ownership |
| 0 and 999 boundaries | `collection.test.ts` (+ optionally CardGrid integration) | increment at 999 no-op; setQuantity clamps negative/overflow |
| Persistence after updates | `collection.test.ts` | localStorage reflects quantity changes and sparse removals |

### TESTQ-03 (v1.0 regressions after quantity changes)
| Behavior | Suite/File | Concrete Assertions |
|----------|------------|---------------------|
| Set browsing (render/pagination basics) | `src/components/__tests__/SetGrid.regression.test.tsx` (new) | set cards render from `useSets`; selecting set calls callback |
| Filters (search/legality/date/series) | `SetGrid.regression.test.tsx` (new) | filtered set list updates correctly; clear filters resets |
| localStorage persistence across sessions | `src/components/__tests__/App.persistence-regression.test.tsx` (new) + `collection.test.ts` | state survives remount via storage hydration |
| Album ownership interactions | `CardGrid.test.tsx` | Add/Remove still works with quantity controls enabled |
| Cross-view semantic consistency | `src/components/__tests__/CrossViewStats.test.tsx` (new, light integration) | unique-owned vs total quantity agree across SetGrid/CollectionView/CollectionStats for same fixture |

## Migration Large-Payload Validation Strategy

1. **Keep existing 5000-card migration test** in `migration.test.ts` (already present).  
2. **Add deterministic 10k-card variant** (non-random, patterned ownership) to reduce false positives.  
3. **Add mount-level hydration test** in `collection.test.ts` using large pre-seeded v1 payload to validate hook initialization + sparse v3 output.  
4. **Guard runtime cost** by making one large test “smoke-level” (single scenario), not many permutations.  
5. **Evidence artifact:** report card count migrated and assert exact expected owned count.

## Release Evidence Plan (Strict Gate)

1. **During implementation (per commit):**
   - Run targeted suites:
   ```bash
   npm run test -- src/components/__tests__/CardGrid.test.tsx
   npm run test -- src/lib/__tests__/collection.test.ts
   ```
2. **Before plan merge:**
   ```bash
   npm run test
   ```
3. **Phase sign-off gate (mandatory):**
   ```bash
   npm run test && npm run build
   ```
4. **Capture in summary/PR:**
   - test pass count
   - build success
   - note baseline moved from 6 failures → 0 failures

## Sequencing Recommendation (2 Executable Plans)

### Plan A — Baseline Stabilization + TESTQ-02 Completion
- Add test setup (`jest-dom`) and top-level mock hygiene.
- Repair existing `CardGrid.test.tsx` failures.
- Fill TESTQ-02 gaps: boundaries (0/999), persistence, robust selectors.
- Exit criteria: all quantity-control tests green; no Vitest mock-hoist warnings.

### Plan B — TESTQ-03 Regression Expansion + Gate Evidence
- Add SetGrid regression suite (browsing/filters).
- Add persistence/remount regression suite.
- Add cross-view consistency suite for unique-vs-total semantics.
- Execute strict gate (`npm run test && npm run build`) and record evidence.

## Open Questions

1. **Should cross-view consistency be one integrated suite or two focused suites?**
   - What we know: Contracts require consistency across 4 surfaces.
   - What’s unclear: Best balance of speed vs diagnostic clarity.
   - Recommendation: Start with one focused fixture-driven suite; split only if flakiness appears.

2. **Do we need to add data-testid attributes for stable scoping?**
   - What we know: Current tests rely partly on index-based queries.
   - What’s unclear: Whether role/label queries alone remain stable for all cards.
   - Recommendation: Prefer accessible queries first; add minimal `data-testid` only where ambiguity remains.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 + Testing Library React 16.3.2 |
| Config file | `vitest.config.ts` |
| Quick run command | `npm run test -- src/components/__tests__/CardGrid.test.tsx` |
| Full suite command | `npm run test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TESTQ-01 | Migration normal/edge + large payload | unit/integration | `npm run test -- src/lib/__tests__/migration.test.ts` | ✅ |
| TESTQ-02 | Quantity controls, boundaries, persistence | component + hook | `npm run test -- src/components/__tests__/CardGrid.test.tsx && npm run test -- src/lib/__tests__/collection.test.ts` | ✅ (needs fixes/expansion) |
| TESTQ-03 | Set browsing, filters, persistence, ownership regressions | component/integration | `npm run test -- src/components/__tests__/SetGrid.regression.test.tsx && npm run test -- src/components/__tests__/App.persistence-regression.test.tsx` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** targeted suites for touched area (`CardGrid` / `collection` / new regression files)
- **Per wave merge:** `npm run test`
- **Phase gate:** `npm run test && npm run build` before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `src/test/setup.ts` — shared matcher setup for Vitest (`@testing-library/jest-dom/vitest`)
- [ ] Update `vitest.config.ts` `setupFiles` to include setup
- [ ] `src/components/__tests__/SetGrid.regression.test.tsx` — covers TESTQ-03 set browsing + filters
- [ ] `src/components/__tests__/App.persistence-regression.test.tsx` — covers TESTQ-03 localStorage persistence/remount
- [ ] `src/components/__tests__/CrossViewStats.test.tsx` — covers cross-view semantics requirement in 06-CONTEXT
- [ ] Move `vi.mock('@/hooks/use-toast')` to top-level in `CardGrid.test.tsx`

## Sources

### Primary (HIGH confidence)
- Local repo execution evidence: `npm run test` output (2026-03-22) — confirmed 6 failing `CardGrid` tests with `Invalid Chai property: toBeInTheDocument`
- `vitest.config.ts` — confirmed `setupFiles: []` and `happy-dom` test environment
- `src/components/__tests__/CardGrid.test.tsx` — confirmed failing matcher usage and nested `vi.mock`
- `src/lib/__tests__/migration.test.ts` — confirmed existing 5000-card migration coverage
- `src/lib/collection.ts`, `src/lib/stats.ts`, `src/components/{CardGrid,SetGrid,CollectionView,CollectionStats}.tsx` — confirmed quantity semantics and cross-view stat surfaces
- npm registry metadata via `npm view` — verified current package versions and publish dates

### Secondary (MEDIUM confidence)
- Vitest warning link surfaced in test output: https://vitest.dev/guide/mocking/modules#how-it-works (module mock hoisting behavior)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — package versions verified from npm registry and already used in repo
- Architecture: **HIGH** — directly derived from current code/test layout and failing output
- Pitfalls: **HIGH** — reproduced via baseline run and file inspection

**Research date:** 2026-03-22  
**Valid until:** 2026-04-21 (30 days; stack is stable but test tooling can evolve quickly)
