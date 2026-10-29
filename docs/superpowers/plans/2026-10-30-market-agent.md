# Inventory / Market Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a runnable simulated Market Deep Agent that assesses exact-card opportunities, issues bounded simulated mandates, handles reassessment and reports owned-stock outcomes.

**Architecture:** An isolated Python package owns validated fixture contracts and deterministic services. A real Deep Agents graph calls session-scoped tools, while a controlled model provides credential-free execution. All authority stays in the session service; output artifacts are simulated business payloads, not authenticated A2A traffic.

**Tech Stack:** Python, Pydantic, decimal, Deep Agents/LangGraph, pytest; isolated virtual environment with a committed dependency lock.

**Spec:** [Approved first-slice design](../specs/2026-10-30-market-agent-design.md).

## Global Constraints

- “Support single-card listings only initially.”
- “This slice accepts SGD evidence only; foreign-currency observations require review until an explicit dated FX contract is agreed.”
- “Quantity is exactly one in this slice.” Bundles must be representable as invalid candidates and routed to review, not silently coerced to one.
- “Only in-memory, per-run state is required.”
- “The package has no runtime import from the open Sales PR and does not modify its files.”
- “No tool grants operator approval, changes real inventory, dispatches a message or moves funds.”
- “Missing or invalid policy values never receive permissive defaults.”
- “No concurrency or cross-process guarantees are claimed.” Serialize session mutations within one graph invocation.
- No production connector, credentials, database, MCP server, external traces or private web UI in this delivery. Use only synthetic fixtures.
- Money enters as decimal strings, never JSON numeric values; finite, nonnegative, at most two fractional digits, explicit currency. Calculated profit may be negative. Use a separate signed output type for profit/loss.
- The first-slice valuation rule is uncalibrated for live trading. Preserve evidence basis, freshness, condition, identity and assumption labels.
- Pin a compatible released SDK set during Task 1; never guess installed capabilities or treat an empty subagent list as proof that delegation is disabled.

## Review Focus

1. Future-dated or repeated evidence must not satisfy minimum sales count or inflate value — Task 2.
2. Naive timestamps, bool-as-int inputs and malformed money must fail at the boundary — Task 1.
3. Replaying a request after revocation must not resurrect authority or double-release exposure — Task 3.
4. A full refund with unrecovered costs must remain a loss; returned stock must require reinspection — Task 4.
5. Parallel model tool calls, forged final outputs or forbidden default tools must not bypass limits — Task 5.

## Execution gate and current evidence

Design and Native execution approved on 30 October 2026. All six implementation tasks are complete locally, with 117 passing tests, six installed-wheel demos, and the independent review findings fixed. See [verification](../../../market_agent/VERIFICATION.md). The user explicitly approved a one-time local build/test exception to the Project/claim gate; the operator subsequently extended it to branch publication and a draft PR only. Merging and deployment remain unauthorized.

The planning check found no open Market implementation issue in the two repositories, and tracker Sales PR #23 remains open. This is a point-in-time scope check, not ownership. The Project read failed with missing `read:project` scope. No claim or Ready status has been established. No product scaffolding or dependency installation belongs in this planning step.

- [x] Before coding, invoke the chosen execution skill and the worktree skill; reuse the user-selected `feature/market-agent` branch in a suitable isolated checkout without resetting existing work.
- [ ] Restore authorized Project access, read Active/Blocked, refresh relevant issues/comments, native dependencies and linked PRs in both repos. A failed read remains a blocker.
- [ ] Create or reuse one issue for this isolated slice, using the issue draft below. Obtain maintainer Ready and the signed successful claim required by this checkout's `AGENTS.md`; record the exact actor/session/run and accepted event. A different contributor's manual exception is not transferable.
- [x] Record the explicit user exception before coding and retain the unresolved Project/claim gates for later integration. Issue #24 exists; no signed claim is asserted.

## File map and common test vocabulary

All new code lives under `market_agent/`. Use a `src/` layout, package name `pokemon_market`, a local `.gitignore` for `.venv/`, caches and build output, `pyproject.toml`, and `requirements.lock`. No root npm/deployment changes.

| File within `market_agent/` | Responsibility |
| --- | --- |
| `src/pokemon_market/contracts.py` | Strict immutable request, evidence, policy and result models; safe error codes |
| `src/pokemon_market/valuation.py` | Pure identity/evidence qualification and decimal economics |
| `src/pokemon_market/session.py` | Scoped records, idempotency, versions, simulated mandates and exposure |
| `src/pokemon_market/inventory.py` | Read-only stock eligibility, ageing and reconciled profit |
| `src/pokemon_market/harness.py` | Real graph, tool authorization, bounded execution and output verification |
| `src/pokemon_market/controlled.py` | Deterministic tool-calling model transport for tests/demo |
| `src/pokemon_market/demo.py`, `__main__.py`, `__init__.py` | Packaged fixture loader, scenario runner and CLI |
| `src/pokemon_market/fixtures/qualified.json`, `inventory.json` | One synthetic acquisition and one stock/outcome dataset |
| `tests/conftest.py`, `test_contracts.py`, `test_valuation.py`, `test_session.py`, `test_inventory.py`, `test_harness.py`, `test_cli.py` | Focused offline checks |
| `README.md`, `VERIFICATION.md` | Commands, temporary peer mapping and actual acceptance evidence |

Tests share `now` (2026-10-30T04:00:00Z), `bundle` (validated acquisition fixture) and `qualified_request` (current assessment request). `session` is a fresh `MarketSession` with an injectable clock for each test. All fixture modifications must be revalidated through model parsing, not trusted `model_copy(update=...)` bypasses. Use existing pytest fixtures rather than introducing a custom test framework.

Canonical fixture: exact English raw single card, reviewed allowed condition; two distinct completed comparable SGD resale observations at `120.00` and `130.00` one day old; minimum count 2; maximum age 7 days; selling costs `10.00` fees + `5.00` delivery; acquisition costs `2.00` fees + `3.00` delivery; other costs `0.00`; required profit `20.00`; per-item limit `100.00`; available capital `200.00`; existing soft exposure `0.00`; soft cap `150.00`; mandate lifetime 900 seconds; maximum 3 reassessments. Questions-only and reviewed assumptions are explicitly allowed in this synthetic policy. These are test values, not operating advice.

## Task 1: Validated contracts and installable fixture package

**Files:** Create package metadata, lock, local ignores, `__init__.py`, `contracts.py`, `fixtures/qualified.json`, `tests/conftest.py`, `tests/test_contracts.py`.

**Interfaces:** `FixtureBundle.model_validate_json(text) -> FixtureBundle`; `Request.model_validate(data) -> Request`; `MarketError.code: str`. Define the following frozen models with unknown fields forbidden:

- `CardIdentity`: set, number, language, printing, finish, category (`raw`/`graded`), grading company and grade when graded. Missing listing identity is representable; trusted target identity must be complete.
- `Listing`: listing/seller IDs, snapshot version, card facts, quantity, nullable condition, reviewed-condition flag from fixture configuration, description, asking-price/currency and acquisition-cost fields. Foreign currency is representable but not authorized for valuation.
- `Evidence`: ID, source transaction ID, source, basis, identity/condition, observation time, currency, gross amount and completion flag. `ReviewedAssumption`: review ID, policy version, identity/condition, amount/currency, review time/expiry, loaded only from trusted fixture configuration.
- `Policy`: ID/version, allowed identities/categories/conditions, evidence age/count, assumption/enquiry permissions, required profit, per-item limit, selling costs, capital/exposure limits, mandate lifetime and reassessment limit. No omitted default financial limits.
- `FixtureBundle`: session ID, listings, evidence, assumptions, policy and existing soft exposure. Reject duplicate record IDs and inconsistent policy baselines.
- `Request`: schema version `"1"`, operation, request/correlation IDs, expected policy/assessment/conversation versions, expiry, evidence IDs, optional mandate ID and typed changes. Operations are `assess_opportunity`, `issue_mandate`, `reassess_opportunity`, `assess_owned_unit`, `prepare_resale`, `negotiate_acquisition`. Reject irrelevant or missing operation-specific fields. Changes allow only identity, condition, price, quantity, delivery and fees.
- `Assessment`: ID/version, listing reference, decision (`qualified`, `questions_only`, `review`, `rejected`), reason codes, exact facts, evidence/scenarios, valuation components, nullable item ceiling, expiry and pending questions. Model explanations are non-authoritative.
- `Mandate`: simulation mode, ID, assessment/listing/policy/conversation versions, status, expiry, nullable ceiling and total exposure. `Artifact`: request/operation/correlation metadata and stored result references, always simulation mode.

- [x] Write boundary tests, including these assertions (the bad-money cases include numeric `1`, `True`, `"NaN"`, `"Infinity"`, `"1e2"`, `"1.001"`):
  ```python
  def test_fixture_round_trip(bundle):
      assert FixtureBundle.model_validate_json(bundle.model_dump_json()) == bundle
  # test_rejects_bad_money: each bad value raises ValidationError.
  # test_rejects_naive_time_boolean_versions_unknown_fields_and_schema: each fails validation.
  # test_preserves_bundle_or_incomplete_listing_for_review: parsing succeeds without inventing identity.
  ```
- [x] Select a supported locally available Python version and released Pydantic/pytest/Deep Agents stack using official documentation and package metadata; record exact pins. In an isolated environment, run the tests and confirm failure comes from missing contract behavior, not missing pytest or an invalid runner.
- [x] Implement the models and canonical fixture; validate before freezing. Reject future policy/review timestamps, invalid expiry ordering and oversized inputs. Use 300-character IDs, 4,000-character descriptions, maximum 100 listings and 1,000 evidence records per fixture; never truncate silently.
- [x] Run `market_agent/.venv/bin/python -m pytest market_agent/tests/test_contracts.py -q`; expect all boundary cases passing. Freeze the clean compatible runtime/test dependency set into `requirements.lock`, verify `pip check`, and install the package editable with `--no-deps`. Document the exact chosen Python minor version in metadata/verification.
- [x] Commit only Task 1 files: `feat: define validated market fixture contracts`.

## Task 2: Exact identity and conservative valuation

**Files:** Create `valuation.py`, `tests/test_valuation.py`; extend `test_contracts.py` only for any newly exposed boundary.

**Interfaces:** `assess(listing: Listing, evidence: tuple[Evidence, ...], assumptions: tuple[ReviewedAssumption, ...], policy: Policy, now: datetime) -> Assessment`. This is pure; session exposure caps and authority issuance belong to Task 3. Results include full cost components and evidence provenance.

- [x] Write tests against the canonical fixture with these exact expectations:
  ```python
  def test_exact_ceiling(bundle, now):
      result = assess(bundle.listings[0], bundle.evidence, bundle.assumptions, bundle.policy, now)
      assert result.decision == 'qualified'
      assert result.item_ceiling == Decimal('80.00')
  # test_exact_ceiling: decision == 'qualified'; gross == Decimal('120.00');
  # net_resale == Decimal('105.00'); economic_ceiling == Decimal('80.00').
  # test_lowest_eligible_sale_wins: adding an eligible '110.00' sale yields ceiling '70.00'.
  # test_repeated_or_future_evidence_does_not_meet_count: decision != 'qualified'.
  # test_missing_condition: decision == 'questions_only'; item_ceiling is None.
  # test_unknown_condition_without_enquiry_permission: decision == 'review'.
  # test_identity_mismatch_or_bundle: decision == 'review'; item_ceiling is None.
  # test_known_disallowed_condition_or_nonpositive_economics: decision == 'rejected'.
  ```
- [x] Run `market_agent/.venv/bin/python -m pytest market_agent/tests/test_valuation.py -q`; expect missing-function/behavior failures.
- [x] Implement `assess`. Check identity before eligibility/economics. Deduplicate observations by source transaction; conflicting duplicates force review. Compare exact identity/condition and require completed, fresh, non-future SGD sales. With sufficient observations select the minimum; otherwise allow exactly one matching current reviewed assumption. An unsupported-currency listing is review-only; exclude foreign-currency evidence and report its limitation. Missing evidence with enquiries enabled yields questions-only; conflicting trusted assumptions yield review. No model score may override these outcomes.
- [x] Add tests for wrong language/finish/grade, missing grading identity, time exactly at the maximum-age boundary, asking-only/reference-only evidence, expired/wrong-policy/unreviewed/conflicting assumptions and an assumption that cannot raise a valid observed ceiling. Run `market_agent/.venv/bin/python -m pytest market_agent/tests/test_contracts.py market_agent/tests/test_valuation.py -q`; expect PASS.
- [x] Commit: `feat: evaluate exact-card evidence and acquisition economics`.

## Task 3: Scoped mandates, exposure, idempotency and reassessment

**Files:** Create `session.py`, `tests/test_session.py`; update contract result fields only where required by the approved design.

**Interfaces:** `MarketSession(bundle: FixtureBundle, *, clock: Callable[[], datetime])`; `read_listing(listing_id: str) -> Listing`; `read_evidence(evidence_ids: tuple[str, ...]) -> tuple[Evidence, ...]`; `handle(request: Request) -> Artifact`; `current_mandate(mandate_id: str) -> Mandate`; read-only `reserved_exposure: Decimal`. Store records by correlation ID; bind all tool access to this session. Task 4 adds owned-unit loading to the constructor.

- [x] Write tests for these service results:
  ```python
  def test_request_replay(session, qualified_request):
      first = session.handle(qualified_request)
      exposure = session.reserved_exposure
      assert session.handle(qualified_request) == first
      assert session.reserved_exposure == exposure
  # test_price_authority: ceiling == Decimal('80.00'); reserved_exposure == Decimal('85.00').
  # test_questions_only: ceiling is None; reserved_exposure == Decimal('0.00').
  # test_duplicate_request_and_listing: same stored IDs; reserved_exposure stays '85.00'.
  # test_changed_payload_same_request_id: raises MarketError with code 'request_conflict'.
  # test_reassessment_releases_once: old status == 'revoked'; no double release on replay.
  # test_replay_cannot_reactivate_revoked_mandate: current_mandate(old_id).status == 'revoked'.
  ```
- [x] Run `market_agent/.venv/bin/python -m pytest market_agent/tests/test_session.py -q`; expect missing-service/behavior failures.
- [x] Implement serialized request handling, exact validation before mutations, canonical payload comparison and stored request outcomes. Identical replays return historical artifacts with current authority checked separately. Bind `negotiate_acquisition` artifacts to an active simulated mandate. Reject unknown or mismatched listing/evidence/policy/mandate references and stale state. Apply economic/per-item/capital/soft caps; include acquisition costs in exposure. Expire/release simulated reservations before calculating headroom, once only. An assessment alone never reserves funds.
- [x] Implement reassessment: reject stale/malformed requests before applying facts; for accepted new material facts revoke the prior mandate before recalculation, even if the new facts yield review or failure. Increment assessment/conversation versions, reject the fourth distinct reassessment for a limit of 3, and do not increment limits for replay. Material snapshot changes to an existing seller/listing cannot create a second active opportunity. Expiry cannot be undone by replay.
- [x] Add cap tests: available capital `84.00` caps item authority at `79.00` with total `84.00`; available capital equal to acquisition costs gives no price authority. Test baseline exposure subtraction once, expiry exactly at `now`, expired requests, policy/version changes, evidence ownership, bounded reassessment, two opportunities competing for remaining exposure, and failed reassessment retaining revocation. Run all current package tests; expect PASS.
- [x] Commit: `feat: enforce simulated mandate lifecycle and exposure`.

## Task 4: Read-only stock, ageing and outcome summaries

**Files:** Create `inventory.py`, `fixtures/inventory.json`, `tests/test_inventory.py`; extend `contracts.py`, `session.py`, and shared test fixtures.

**Interfaces:** Define `OwnedUnit`, `Outcome`, `InventoryBundle`, `InventorySummary` in `contracts.py`. `InventorySummary` exposes `unsold_cost_basis: Decimal` plus per-unit and per-outcome results. `summarize_inventory(units: tuple[OwnedUnit, ...], outcomes: tuple[Outcome, ...], now: datetime) -> InventorySummary`; extend `MarketSession(..., inventory: InventoryBundle | None = None)` and add `read_owned_unit(unit_id: str) -> OwnedUnit`. `handle(assess_owned_unit)` returns stock facts and an evidence-linked Task 2 assessment using the unit's inspected identity/condition as trusted target facts; `handle(prepare_resale)` emits only a draft-task artifact for inspected available stock, with no reservation or sale authority.

- [x] Write tests for these inventory fixtures:
  ```python
  def test_empty_inventory(now):
      assert summarize_inventory((), (), now).unsold_cost_basis == Decimal('0.00')
  # test_available_requires_receipt_and_inspection: unreceived/quarantined units not eligible.
  # test_age_and_unsold_basis: acquired 10 days ago => age_days == 10; unsold_basis == '85.00'.
  # test_reconciled_sale: proceeds '120.00' - acquisition '85.00' - seller_costs '15.00' => profit '20.00'.
  # test_pending_costs: realized_profit is None, not an invented zero-cost profit.
  # test_full_refund: sale '120.00', refund '120.00', acquisition '85.00', recovery '85.00',
  # unrecovered seller_costs '15.00' => realized_profit == Decimal('-15.00').
  # test_physical_return_requires_new_inspection: returned unit cannot prepare_resale.
  ```
- [x] Run `market_agent/.venv/bin/python -m pytest market_agent/tests/test_inventory.py -q`; expect missing-function/behavior failures.
- [x] Implement read-only calculations and session scope checks. Units carry receipt/inspection/return events with timestamps, stock status and acquisition cost basis; outcomes carry independently confirmed fulfillment/settlement, actual receipts/refunds/recoveries/costs and reconciliation completeness. Deduplicate by outcome ID; reject inconsistent chronology, duplicate/conflicting outcomes and future acquisition dates. Keep outstanding cash, returned stock and unsold basis visible; do not double-count a returned unit's cost basis as both a completed disposal and unsold expense. No stock mutation tool is added.
- [x] Add tests for reserved units, fulfillment without settlement, exact UTC day ageing, unknown/cross-session unit IDs, conflicting outcome IDs and insufficient valuation evidence on otherwise eligible stock. Run all current package tests; expect PASS.
- [x] Commit: `feat: report inspected inventory and reconciled outcomes`.

## Task 5: Real Deep Agents graph with enforced tool boundaries

**Files:** Create `harness.py`, `controlled.py`, `tests/test_harness.py`; extend `tests/conftest.py` with controlled tool transcripts.

**Interfaces:** `build_agent(session: MarketSession, model: BaseChatModel) -> CompiledStateGraph`; `run_agent(session: MarketSession, model: BaseChatModel, request: Request) -> Artifact`; `ControlledModel` is an SDK-compatible tool-calling model used by tests and the demo. Tool names: `read_listing`, `read_evidence`, `assess_opportunity`, `issue_mandate`, `reassess_opportunity`, `assess_owned_unit`, `prepare_resale`, `summarize_inventory`. All tools call the same session/services from Tasks 2–4. Final model output contains result references, not authoritative economics.

- [x] Write real-graph tests with these assertions:
  ```python
  def test_real_graph_returns_simulated_artifact(session, qualified_request):
      result = run_agent(session, ControlledModel(), qualified_request)
      assert isinstance(result, Artifact)
      assert result.mode == 'simulation'
  # test_graph_calls_tools: captured calls contain assess_opportunity and issue_mandate;
  # resulting artifact is simulation mode and resolves to stored ceiling '80.00'.
  # test_forged_result: unknown ID or changed ceiling rejected with 'invalid_output'.
  # test_forbidden_tools: task/execute/network/approval/payment invocations denied.
  # test_cross_session_read: foreign record ID yields 'record_not_found' without contents.
  # test_parallel_mandates: total exposure <= configured headroom, even in one model turn.
  # test_malicious_listing: injected limit/credential instructions do not alter policy or output secrets.
  ```
- [x] Run `market_agent/.venv/bin/python -m pytest market_agent/tests/test_harness.py -q`; expect missing-harness/behavior failures.
- [x] Implement the graph using the pinned SDK's supported configuration/middleware. Bind only session-scoped business tools; disable default delegation and execution, and deny tools outside the explicit allowlist at dispatch even if the model invents them. Remove unused file tools where supported; any remaining scratch storage must be ephemeral, bounded to 64 KiB and contain no host files. Do not mount repository memory, secrets or general-purpose skills. Inspect the actual bound tool list in tests rather than relying only on documentation.
- [x] Implement `run_agent` with at most 12 model calls, 24 business-tool calls, 60 seconds wall time, one structured-output retry and no automatic business-action retries. For acquisition runs, bind tool requests to the run's correlation/version scope and derive stable distinct assessment/mandate request IDs from the input request ID; retries reuse these IDs. The model cannot supply arbitrary record scope or mint fresh IDs to evade replay controls. Disable automatic remote trace export for this slice. Ensure one session serializes mutations; cached idempotent results never reacquire exposure. Resolve returned references against stored state and reject altered data; sanitize unexpected errors to safe codes. A timeout after a successful mutation must not make a retry issue new authority.
- [x] Test endless tool calls, malformed structured output, unexpected exception sanitization, raw listing text impersonating trusted evidence, unknown tool calls, and missing credentials for an optional model. Controlled tests block outbound network. Run all current package tests; expect PASS with actual tool-call evidence.
- [x] Commit: `feat: run market assessment through a constrained Deep Agents harness`.

## Task 6: Runnable scenarios, verification and peer handoff

**Files:** Create `demo.py`, `__main__.py`, `tests/test_cli.py`, `README.md`, `VERIFICATION.md`; amend package data metadata if needed to include JSON fixtures.

**Interfaces:** `load_bundle() -> FixtureBundle`; `run_scenario(name: str, *, model: BaseChatModel | None = None) -> Artifact`; `main(argv: list[str] | None = None) -> int`. CLI: `python -m pokemon_market demo --scenario NAME`. Names: `qualified`, `questions-only`, `identity-review`, `stale-evidence`, `reassessment`, `inventory`. Use revalidated variants of packaged data rather than six almost-identical files. Default controlled transport uses no credentials. Optional `--model PROVIDER:NAME` explicitly enables one documented supported provider against synthetic tools only; choose/install its compatible adapter when dependencies are locked, and require its server-side environment credential.

- [x] Write subprocess tests:
  ```python
  def test_demo_json():
      result = subprocess.run([sys.executable, '-m', 'pokemon_market', 'demo',
                               '--scenario', 'qualified'], capture_output=True, text=True)
      assert result.returncode == 0
      assert json.loads(result.stdout)['mode'] == 'simulation'
  # test_demo_json: exit == 0; stdout parses as one JSON document; mode == 'simulation'.
  # test_qualified_demo: item ceiling == '80.00'; total exposure == '85.00'.
  # test_expected_review_is_success: identity-review exits 0 with decision 'review'.
  # test_invalid_scenario: nonzero exit and concise stderr, no traceback or secret.
  # test_packaged_fixtures: demo works outside the repository working directory.
  ```
- [x] Run `market_agent/.venv/bin/python -m pytest market_agent/tests/test_cli.py -q`; expect missing-entrypoint/behavior failures.
- [x] Implement fixture loading via package resources and argparse entrypoint. Domain review/rejection is a successfully processed result (exit 0); invalid input/configuration is exit 2; runtime failure is exit 1. Output all money as fixed two-decimal strings, diagnostics only to stderr, and no partial artifact on failure. Demo outputs show scope, evidence/assumptions, current authority and expiry; inventory scenario includes pending and loss cases.
- [x] Write README install/test/demo commands with the actual chosen Python version and pins. Map temporary Market decimal/string-version contracts to the Sales proposal's integer-minor-unit/numeric versions; label conversion as unresolved peer work, with links to #11 and #23. Document no authenticated A2A, persistence, live marketplace or production inventory authority. Record the model configuration path without example credentials.
- [x] Verify from a fresh environment: locked installation and editable package install with no dependency re-resolution, `python -m pip check`, `python -m pytest tests -q` (working directory `market_agent/`), all six CLI scenarios, and `git diff --check`. Build/install the local wheel into a clean environment and run at least the qualified demo outside the checkout to prove package data inclusion. Record exact commands, counts, versions and failures in `VERIFICATION.md`; live-model checks are explicitly not run unless actually exercised with authorized configuration. Run frontend tests only if frontend behavior changed.
- [x] Request independent whole-branch review under Superpowers, fix actionable findings, rerun affected checks and commit intended files locally under the recorded exception.
- [ ] Before publishing: resolve Project/claim and dependency gates, obtain publication authorization, and hand off a reviewable PR. Do not merge or mark full V1 complete. Attach any created PR to this chat.

## Public-safe implementation issue draft

**Title:** Market Agent: runnable Deep Agents assessment slice with simulated tools

**Outcome:** Implement this approved first slice in `market_agent/` on `feature/market-agent`, preserving the Sales and React workstreams. The design and plan are local commits until published; link their actual published revisions when available, never invent URLs.

### Acceptance criteria

- Real Deep Agents graph and credential-free demo exercise scoped business tools.
- Exact identity/evidence rules, decimal ceilings, policy limits and simulated mandates pass offline tests.
- Duplicate/replayed/stale requests, reassessment/revocation and exposure remain consistent within one session.
- Scoped inventory summaries distinguish inspection, pending settlement, unsold basis, returns and actual losses.
- Forbidden tools, cross-session references, hostile listings and fabricated final output fail closed.
- Install/test/demo commands and temporary Sales boundary are documented; simulated and unverified live capabilities are explicit.

### Verification

Tasks 1–6 checks, recorded red/green evidence, fresh locked install, all scenarios, package-data check and independent review. No network/model credentials required for normal tests.

### Dependencies

None for this isolated simulated slice. No Sales runtime import, production data migration or live connector dependency. Shared integration follows the separate peer-contract decision.

### Non-code blockers

Project access verification, maintainer Ready review and the required accepted actor/session claim remain unresolved. The original draft required these before implementation. The user subsequently authorized a one-time exception for local build/test, selected Native execution and approved the plan. The Project/claim gates remain unresolved for integration.

### Exclusions

No live search/contact, commitment/payment, production stock changes, deployed A2A, persistent scheduling, database migration, Langfuse export, web UI or tracker synchronization.

## Source checks and coverage self-review

Official [Deep Agents customization](https://docs.langchain.com/oss/python/deepagents/customization) and [overview](https://docs.langchain.com/oss/python/deepagents/overview) were consulted during planning. They document graph construction, structured output and configurable built-ins; the pinned release and actual tool exposure must still be verified during implementation. Do not install the examples' default agents unchanged.

Coverage: design sections 1–4 map to Tasks 1–3 and 6; section 5 to the isolated package and Task 6 peer mapping; section 6 to Task 5; section 7 to Task 3 artifacts/replay and Task 4 stock artifacts; sections 8–9 to Tasks 1, 3 and 5; section 10 to Task 6; section 11 to the execution gate and Task 6; section 12 to this plan's constraints and explicit later milestones. Read-only inventory/outcomes map to Task 4. Deferred full-V1 work is not an implementation gap in this first-slice plan.

Self-review completed: all six tasks have defined producers/consumers and red/green checks; the five Review Focus cases are assigned; no root frontend or Sales edits are needed; plan generation is not evidence that product tests passed. Execution boxes now reflect the completed local tasks. Project/claim and publication gates remain open; see verification for the explicit exception and evidence.
