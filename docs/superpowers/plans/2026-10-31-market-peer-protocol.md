# Market fixture peer protocol completion

> **For agentic workers:** Use superpowers:executing-plans inline in the existing isolated worktree; continuous execution of the fixture target is already authorized.

**Goal:** Complete the existing synchronous fixture peer's cancellation route and structured HTTP errors under #38/#41.
**Architecture:** Reuse `FixturePeerService.cancel_task`, the current HTTP server and pinned A2A SDK error mappings. The fixture completes synchronously: cancellation of a completed task rejects truthfully, and unknown/other-role tasks remain inaccessible. No asynchronous task engine or new business state.
**Tech Stack:** Existing Python, PostgreSQL, a2a-sdk 1.3.0 and HTTP+JSON 1.0 binding.
**Spec:** Existing approved `2026-10-31-market-v1-software.md` Task D/E, shared-contract proposal, issue #38 cancellation/recovery criteria, and [A2A 1.0.1 HTTP error/cancel specification](https://a2a-protocol.org/v1.0.1/specification/#116-error-handling).

## Constraints and decisions
- Keep role/workspace authorization and body limits. Operator endpoints retain their existing response format.
- POST `/a2a/{role}/tasks/{id}:cancel` calls the existing terminal-state method; path identity is authoritative. Accept empty body or matching id plus optional object metadata; reject conflicting id, tenant override, unknown fields and malformed data.
- A2A errors use the documented nested status envelope and installed SDK mappings for TaskNotFound, TaskNotCancelable, UnsupportedOperation and InvalidParams. Generic auth/conflict/size/unavailable errors retain their HTTP status and sanitized code, with no raw exception/request data.
- Support A2A JSON media type on peer requests/responses while retaining application/json compatibility. No credential, message, seller or database content in errors.
- Real Sales, running-task cancellation, production access, Langfuse and paid models remain separate gates. No merge or deployment action.

## Review focus
- Cancellation cannot reverse completed business state or grant approval.
- Unknown and other-role task IDs have the same response before and after restart.
- Auth precedes request/body/task inspection; pause does not hide completed task inspection/cancellation outcomes.
- Path/body identity mismatch and hostile metadata cannot select another record.
- Protocol error formatting must not change operator/UI behavior or disclose runtime exceptions.

## Task 1: Finish synchronous fixture HTTP protocol behavior

**Files:** `market_agent/src/pokemon_market/server.py`, `market_agent/tests/test_peer.py`, `market_agent/README.md`, verification document.

- [x] Add failing real-HTTP/SDK tests for terminal cancellation, unknown/other-role tasks, auth, body validation, pause, media types and sanitized structured errors.
- [x] Observe missing-route/error-envelope failures.
- [x] Add the bounded cancel route and use installed SDK error mappings in peer responses; keep domain semantics unchanged.
- [x] Run focused peer tests then full Python/PostgreSQL suite and Ruff/whitespace checks. No UI change; prior UI/Playwright checks are historical.
- [x] Request one fresh scoped review, fix Important findings with regression evidence, document exact results/limits and publish to existing PR42 with issue progress updates.

## Completion evidence

281 Python/PostgreSQL tests passed, including 41 peer tests; Ruff/whitespace passed. Fresh scoped review found no Critical/Important findings. Existing fixture execution and feature-branch publication authorization applies; no merge. Full evidence is in `../../market-v1-software-verification.md`.
