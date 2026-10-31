# Market V1 software implementation plan

> **For agentic workers:** Use Superpowers execution, test-driven development and fresh review. The operator authorized continuous execution and selected the documented Market contract with a fixture Sales peer.

**Goal:** Deliver a durable, testable Market workflow and private operator interface using the existing Market contracts, Supabase-compatible PostgreSQL and a fixture Sales peer.

**Architecture:** Keep the current deterministic MarketSession as the business core. Persist its validated state transactionally in a private PostgreSQL schema, separate from graph checkpoints. Add bounded evidence/scenario tools, durable scheduled fixture discovery, authenticated fixture-peer exchange, and a loopback private API/UI. Existing public reference prices and collection behavior remain intact.

**Tech stack:** Existing Python 3.12/Deep Agents/Pydantic, PostgreSQL 17, psycopg, LangGraph PostgreSQL checkpointer; existing React/Vite UI. Use the standard-library HTTP server for a loopback operator service with explicit request limits and authentication. Do not add a second web framework.

**Spec:** Existing V1 HTML plan and `../specs/2026-10-31-market-shared-contract-proposal.md`. The operator selected that Market proposal as the temporary target; Sales #11 remains a real-peer interoperability dependency, not a reason to stop fixture-based development.

## Global constraints

- Single operator; a stable workspace/session ID owns all its fixture opportunity/exposure state across scheduled runs. Different run IDs must not reset capital/exposure.
- Exactly two application roles. The Sales peer is explicitly a fixture; it never contacts sellers or grants approval.
- All financial authority remains simulation-only until approved connector, shared real services and actual operator policy are supplied. Reference quotes are not completed sales.
- PostgreSQL business state, LangGraph checkpoints and traces are distinct. No production database connection or migration is implied.
- Existing money strings, exact identity and separate policy/assessment/conversation versions remain canonical for this development target. No lossy Sales-prototype conversion.
- New nontrivial behavior starts with a failing test. Each task records real test results. No merge or production deployment.
- Private API credentials remain server-side; session cookies are HttpOnly/SameSite=Strict; mutating browser requests require matching Origin. Serve only loopback. No private records in static build artifacts.

## Review focus

1. Replayed or concurrent requests must not duplicate mandates, exposure or scheduled work.
2. Persistence errors must rollback memory/DB together; stored failures that revoke stale authority must survive restart.
3. A reference quote, missing condition or hostile listing must never acquire price authority.
4. Anonymous/cross-origin/oversized/malformed private requests and forged peer tasks must fail without exposing secrets or records.
5. Restart, stale versions, pause and cancellation must leave real/fixture outcomes truthful; a completed peer task is not approval.

## Task A: Durable Market state (#32/#33/#37)

**Files:** `market_agent/src/pokemon_market/storage.py`, minimal session/harness hooks, explicit private-schema setup, `tests/test_storage.py`; dependency files managed by the coordinator.

**Interfaces:** `PostgresMarketStore(dsn).setup()` explicitly creates private schema; `.create(bundle, inventory=None)` persists an immutable seed and empty mutable state, conflicting seeds reject; `.session(session_id, clock=...)` returns a MarketSession-compatible durable facade. Existing handle/read/ingest/current_mandate/reserved_exposure/inventory methods preserve validation and fresh DB state. `build_agent(..., checkpointer=None)` and `run_agent(..., checkpointer=None, thread_id=None)` preserve current defaults.

- [x] Write DB integration tests: fresh instance recovery, same/conflicting request, concurrent issuance, expiry/revocation, failure rollback, immutable seed/scope, no anonymous SQL grants, graph checkpoints separate.
- [x] Observe failures, implement the smallest transactional state serialization/row-lock approach, rerun the tests and existing Python suite.
- [x] Record the simulation/one-workspace exposure boundary and backup/restore verification. No silent production migrations.

## Task B: Evidence and scenario calculations (#34/#35)

**Files:** `market_agent/src/pokemon_market/evidence.py`, `tests/test_evidence.py`; keep existing fixture contracts/valuation decisions unchanged unless a regression proves a fix is required.

**Interfaces:** Strict `ReferenceSnapshot` contract preserving provider/card ID, original currencies, observed/fetched time and source classification; `load_reference(card_id, *, base_url, now)` only accepts bounded IDs and a trusted loopback reference backend. `valuation_scenarios(listing, evidence, assumptions, policy, now)` returns deterministic conservative/base/upside evidence-derived gross/net/ceiling strings and method/assumption metadata, or explicit unavailable/review reasons. Conservative authority stays with existing assess().

- [x] Failing tests for identity/freshness/FX/source failures, reference-as-sale rejection, exact amount/rounding and min/median/max observed-sale scenarios; no invented multipliers.
- [x] Implement and verify against recorded data; a bounded real backend lookup is separate read-only evidence.

## Task C: Private Market UI (#40)

**Files:** `src/components/MarketOperations.tsx`, its component tests, and minimal MarketView mounting/styles. No server/agent/dependency edits.

**API contract:** Same-origin `/api/operations`: POST `/login` body `{token}` creates cookie; POST `/logout`; GET `/state`; POST `/assess` body `{listing_id}`; POST `/schedule` body `{times:["HH:MM"],timezone:"Asia/Singapore"}`; POST `/pause` body `{paused:boolean}`; POST `/run` (run due work). Other mutations require matching Origin. All responses identify `mode:"simulation"`, `peer:"fixture"`, `live_ready:false`. `/state` returns `paused`, `schedule`, `runs`, `assessments`, `mandates`, `inventory`, `blocked_reasons`; decimal money remains strings. Unconfigured public preview returns unavailable, never fixtures.

- [x] Failing UI tests for login, unauthorized/unavailable states, bounded schedule controls, pause/resume, explicit simulated authority, expiry/questions-only, stale response and mobile/keyboard behavior.
- [x] Implement using existing components and render current API state. Never show raw tokens in logs/status or store tokens in localStorage. Re-run frontend tests/build/focused lint.

## Task D: Durable workflow, fixture peer and private API (#36/#38/#39)

**Files:** new `workflow.py`, `peer.py`, `server.py`, CLI entry; tests for each and operational docs. Coordinator owns these files.

- [x] Persist schedule/timezone, lease/run identity and pause state in the private business schema. Single catch-up after downtime; recurring same snapshot must not create duplicate active authority. Use one stable workspace. Simulated connector fixtures are clearly identified; live connector unsupported.
- [x] Expose bounded authenticated fixture peer tasks using the adopted Market envelope and explicit request/skill/expiry/version checks. Use actual supported A2A protocol/SDK for transport when available; otherwise report the protocol gate pending rather than call custom JSON authenticated A2A.
- [x] Provide read-only fixture inventory/actual-outcome summaries through existing service logic; do not invent #16 production stock or settlement.
- [x] Implement loopback API with bounded JSON parsing, exact-origin checks and separate operator/peer authentication; no credential/DSN disclosure or arbitrary upstream path/URL.
- [x] Serve the built UI and existing public reference API through fixed loopback proxy configuration. Authenticated private endpoints must be unavailable on plain public Vite deployment.
- [x] Add durable worker polling/start/stop commands and verify restart, concurrency, pause, replay and malformed requests. No broad filesystem/network tool exposed to the model.

## Task E: Acceptance and handoff (#41)

- [x] Run all Python/frontend/database tests, build, dependency check, focused lint and whitespace checks; distinguish old lint findings.
- [x] Playwright: login, schedule, simulated run, assessments/mandates/questions-only, pause, inventory, logout, phone-width rendering and public/private boundary.
- [x] Run backup/restore and restart without duplicated authority. Verify whitelisted durable run metadata and sanitized failure codes. A Langfuse exporter and real-model evaluation stay pending until a sink, credentials and budgets are selected; do not add an unused exporter.
- [x] Fresh whole-branch review, fix Important findings with regression tests, publish updated draft PR and exact issue evidence. Do not mark real-peer/live-production gates complete from fixture tests.


## Completion evidence and external gates

Software checks and fresh review are recorded in `../../market-v1-software-verification.md`. The checkboxes above cover the operator-selected **fixture software target**, not closure of every parent roadmap issue. No production Supabase connection, approved marketplace connector, real Sales contract, shared stock/budget/approval authority, live policy or paid-model/Langfuse acceptance is supplied. These remain explicit external gates; no merge, live activation or deployment occurred.
