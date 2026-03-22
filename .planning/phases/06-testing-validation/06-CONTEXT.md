# Phase 6: Testing & Validation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate v1.1 quantity tracking end-to-end by fixing current baseline test failures, expanding automated coverage for quantity behaviors and v1.0 regressions, and enforcing strict release gates before milestone completion.

</domain>

<decisions>
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

</decisions>

<specifics>
## Specific Ideas

- The current failing test signature indicates assertion environment mismatch (`toBeInTheDocument`) and likely related timing/selector fragility in quantity tests; address this early as baseline unblock.
- Build a concise test matrix mapping requirement IDs (`TESTQ-02`, `TESTQ-03`) to concrete suites and assertions so checker/verifier can audit quickly.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` §"Phase 6: Testing & Validation"
- `.planning/REQUIREMENTS.md` §"Validation & Regression" (`TESTQ-01..TESTQ-03`)
- `.planning/STATE.md` current phase status and open TODOs

### Upstream behavior contracts
- `.planning/phases/04-data-model-migration/04-CONTEXT.md` (quantity semantics, migration safety)
- `.planning/phases/05-quantity-ui-statistics/05-CONTEXT.md` (toggle/control/stat semantics)

### Existing code/test surfaces
- `src/components/__tests__/CardGrid.test.tsx`
- `src/lib/__tests__/collection.test.ts`
- `src/components/SetGrid.tsx`
- `src/components/CollectionView.tsx`
- `src/components/CollectionStats.tsx`
- `src/lib/collection.ts`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing Vitest + Testing Library setup already covers core app surfaces.
- Migration tests from Phase 4 provide patterns for payload and edge-case validation.
- Quantity UI tests from Phase 5 can be extended rather than replaced.

### Current Baseline Signal
- Latest baseline run failed with 6 failing tests in `CardGrid` quantity test group.
- Error sample indicates matcher/runtime setup issue (`Invalid Chai property: toBeInTheDocument`) and follow-on assertion instability.
- Baseline repair is explicitly required before adding final validation coverage.

### Integration Points
- Quantity behavior assertions must align with `useCollection` semantics (`quantity > 0` implies owned).
- Stats assertions must verify consistency across all UI surfaces after state changes.
- Regression suites must continue validating pre-v1.1 user workflows.

</code_context>

<deferred>
## Deferred Ideas

- Manual numeric quantity input, keyboard shortcuts, and advanced duplicate workflows remain outside Phase 6.
- Any new feature request discovered during testing should be logged for future milestone planning, not implemented in this phase.

</deferred>

---

*Phase: 06-testing-validation*
*Context gathered: 2026-03-22*
