# Market operations inspection Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans in this existing isolated worktree. The operator authorized continuing #40 under the selected fixture software design.

**Goal:** Let the operator inspect the configured Market scope, actual execution state, evidence and authority without inferring live readiness.
**Architecture:** Extend the existing private state response and React panel. Derive read-only scope from the persisted policy, current identity from listing snapshots, and schedule timing from the same Singapore slots/last-slot cursor as the worker. Record a successful fixture dispatch in the existing run-result JSON; historical runs without that field remain unverified.
**Tech Stack:** Existing Python/PostgreSQL and React/Zod; no new dependencies or schema migration.
**Spec:** Task C/D of `2026-10-31-market-v1-software.md`, the operator-selected `../specs/2026-10-31-market-shared-contract-proposal.md`, and issue #40's existing inspection requirements. This fills the approved UI's missing fields, not a new live-policy editor.

## Global constraints
- Existing single-operator authentication, Origin checks and public/private boundary stay intact.
- Display persisted synthetic policy as read-only. Do not invent live watchlists, geography, policy values or readiness.
- Connector configuration is not current health. Show last recorded fixture dispatch success/failure/time; absent history is unverified. No network probes on state reads.
- Preserve exact identity, opaque policy versions, separate integer state versions, decimal strings and explicit unavailable values.
- Publishing this feature branch is already authorized; merge and production activation are separate.

## Review focus
- Paused/no-schedule/midnight/exact-slot/catch-up timing must match worker semantics.
- Old run results must not be upgraded to verified peer exchanges.
- Evidence observed in the future or outside policy age must not display fresh; freshness labels refer to the displayed snapshot time.
- Missing/graded identities and very long IDs must render safely on narrow screens.
- Malformed private metadata must fail closed; authentication expiry must clear new fields too.

## Task 1: Complete private inspection fields

**Files:** `market_agent/src/pokemon_market/workflow.py`, `market_agent/tests/test_workflow.py`, `src/components/MarketOperations.tsx`, `src/components/__tests__/MarketOperations.test.tsx`, minimal existing styles if browser checks require them; verification docs.

**Interfaces:** Existing GET `/api/operations/state` gains `captured_at`, `scope` (policy version, allowed_cards, allowed_conditions, max_evidence_age_seconds), `next_scheduled_at`, and `sales_connection` (configured plus nullable last_dispatch containing status/time). Existing listings gain card/version/condition/condition_reviewed. Existing assessment and mandate fields become visible instead of being stripped by the client schema. New metadata is optional for older state responses; malformed supplied metadata rejects.

- [x] Write failing backend tests for scope/current identity, Singapore future/catch-up/exact-slot/pause/no-schedule behavior, and recorded vs unverified peer dispatch.
- [x] Run targeted tests and observe expected missing-field failures.
- [x] Implement state derivation and record `peer_dispatched: true` only after the configured peer callback returns successfully. Preserve errors/transactions and immutable seed.
- [x] Write failing UI tests for scope/current identity, snapshot evidence freshness, separate versions, unavailable metadata, connection history, paused/due schedule and hostile/malformed metadata.
- [x] Extend the existing layout with inspection cards and disclosure details; retain existing controls and timestamp/expiry behavior.
- [x] Run full backend suite with disposable DB and full frontend suite; build, focused lint and whitespace. Expected: all affected tests/build pass; report known full-lint baseline separately.
- [x] Playwright on real private service: authenticated inspection, current state after a controlled run, paused state, 390px layout, credential/private-state boundary. Expected: persisted facts visible, no overflow or invented activity.
- [x] Fresh focused review of this task's diff, address important findings with regressions, commit/push and update #40/#41/PR #42 evidence.


## Completion evidence

273 Python/PostgreSQL tests and 221 frontend tests passed; build, focused lint/Ruff and whitespace passed. Full lint has the unchanged 9-error/5-warning baseline. Headed Playwright verified a fresh persisted assessment and fixture dispatch, read-only scope/evidence/version details, paused state and 390px layout. See `../../market-v1-software-verification.md` for evidence and remaining issue gates.

Review corrections: shared timestamp validation now rejects non-finite parsed dates; failed dispatch history is retained through retries and subsequent pre-dispatch failure using the existing run JSON. Both had observed failing regressions before fixes. The implementation was reviewed against base `1f37d62`; historical branch review is recorded separately. Existing authorization covers feature-branch publication; main merge and production activation remain separate.
