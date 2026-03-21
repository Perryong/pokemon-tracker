# Phase 4: Data Model & Migration - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert v1 boolean ownership storage to quantity-based storage safely, preserving existing collection behavior while establishing migration, backup, and compatibility foundations for v1.1 quantity tracking.

</domain>

<decisions>
## Implementation Decisions

### Migration Trigger and Timing
- Run migration automatically on first collection load (no manual trigger required).
- Keep migration UX silent when successful and fast.
- Show a non-blocking warning toast only when fallback/error paths are used.
- If already on migrated schema version, detect and no-op safely.

### Backup and Recovery Policy
- Create one deterministic backup key during migration.
- Keep backup until the next successful app start, then allow cleanup.
- On migration failure, attempt one automatic restore from backup.
- If restore still fails, keep app usable in memory and provide manual recovery hint.

### Error Handling and Data Safety
- If migration or save fails, do not drop user data.
- Keep in-memory state usable and surface a clear warning toast.
- Log detailed error context to console for debugging/support.
- On storage quota issues, keep state in memory and warn; do not auto-trim owned data.

### Quantity Semantics and Constraints
- Quantity is the single source of truth; owned-state is strictly derived from `quantity > 0`.
- Enforce per-card range `0..999`.
- Coerce invalid/non-integer inputs to safe integer values and clamp to range.
- Use sparse storage: when quantity reaches `0`, remove the card key from persisted map.

### Compatibility and Migration Contract
- Preserve existing consumer APIs (`isOwned`, `isInCollection`, `toggleOwnership`, add/remove methods) as quantity-backed wrappers during v1.1 transition.
- Keep existing localStorage key name and migrate payload in place.
- Bump persisted schema version and cover migration behavior explicitly in tests.

### Claude's Discretion
- Internal naming of versioned schema interfaces and migration helpers.
- Exact backup key suffix string, as long as deterministic and documented.
- Migration telemetry granularity in console logs.

</decisions>

<specifics>
## Specific Ideas

- Prioritize "no data loss" and "no user interruption" as primary migration outcomes.
- Treat migration as idempotent infrastructure work before any quantity UI expansion.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and phase contract
- `.planning/ROADMAP.md` §"Phase 4: Data Model & Migration" — fixed scope, requirements, and success criteria.
- `.planning/REQUIREMENTS.md` §"Data Model & Migration" (`QTY-01..QTY-04`) — migration requirements contract.
- `.planning/REQUIREMENTS.md` §"Validation & Regression" (`TESTQ-01`) — migration test expectation.

### Prior behavior contracts to preserve
- `.planning/phases/01-data-foundation-persistence/01-CONTEXT.md` — original boolean ownership and localStorage decisions.
- `.planning/phases/03-cards-album-ownership-tracking/03-CONTEXT.md` — ownership toggle and stats behavior expectations.
- `.planning/phases/02.1-build-a-pokemon-tcg-collection-tracker-application-using-react-js-shadcn-ui-components-and-the-tcgdex-javascript-sdk-tcgdex-sdk/02.1-CONTEXT.md` — release hardening severity and reliability standards.

### Existing implementation baseline
- `src/lib/collection.ts` — current storage schema, persistence effect, and compatibility APIs.
- `src/lib/__tests__/collection.test.ts` — current persistence test patterns to evolve for migration coverage.
- `src/components/CardGrid.tsx` — current ownership consumers (`isInCollection`, add/remove) that must remain compatible.
- `src/App.tsx` — app bootstrap path where collection initialization behavior is exercised.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useCollection` in `src/lib/collection.ts` already centralizes collection state, localStorage hydration, and persistence writes.
- Existing wrapper-style ownership methods (`isInCollection`, add/remove/toggle) provide a stable API surface for backward compatibility.
- Existing test harness in `src/lib/__tests__/collection.test.ts` already validates persistence and quota error handling patterns.

### Established Patterns
- LocalStorage state is versioned (`version` field) and persisted under key `pokemon-collection-v2`.
- Persistence is write-on-change via `useEffect`, with explicit quota/error logging.
- Card-grid and stats behavior currently rely on boolean ownership semantics from collection hook outputs.

### Integration Points
- `CardGrid` ownership filters and stats calculations call collection APIs directly and must remain behaviorally consistent during migration.
- `CollectionView`/`CollectionStats` read owned-card counts from collection outputs and depend on derived ownership continuity.
- Migration/hydration timing is effectively application-start critical because collection hook initializes at first consumer mount.

</code_context>

<deferred>
## Deferred Ideas

- Manual quantity input UX and keyboard shortcuts (`QUX-01`, `QUX-02`) — Phase 5+.
- Duplicates-only filtering and batch reset workflows (`QUX-03`, `QUX-04`) — later phase.
- Trade inventory / condition / value tracking (`ADVQ-*`) — future milestone scope.

</deferred>

---

*Phase: 04-data-model-migration*
*Context gathered: 2026-03-21*
