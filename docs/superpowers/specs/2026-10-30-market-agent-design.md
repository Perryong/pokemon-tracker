# Inventory / Market Agent: first runnable slice

Date: 30 October 2026 (Asia/Singapore)

Repository: `Perryong/pokemon-tracker`

Branch: `feature/market-agent`

Status: Proposed design, awaiting operator approval. No implementation claim established.

## Intent and selected approach

Help the operator identify Pokémon-card acquisition opportunities, explain their economics, and provide bounded negotiation authority to the Sales workflow. Research must distinguish evidence from assumptions and physical stock from collection counts.

The operator selected **a runnable Market slice first** after reviewing two approaches:

1. **Runnable slice, then integration (selected):** establish a real Deep Agents harness and deterministic domain behavior using synthetic evidence, listings and stock. Deliver a credential-free demonstration before adding the shared platform. Temporary fixture contracts require later peer agreement.
2. **Integrated platform first:** build shared persistence, scheduling and authenticated A2A first. This reduces temporary adapters but blocks the first useful demonstration on shared-contract, storage and deployment decisions.

The original HTML remains the full V1 direction. This document defines the first independently testable delivery, not completion of every V1 milestone. Implementation details explicitly marked as builder choices do not require additional product decisions.

## 1. V1 outcome and scope

First-slice outcome: one local command runs an actual Market Deep Agents graph, exercises scoped tools, and emits a validated assessment plus a simulated mandate or review/rejection result. A controlled model transport makes normal tests and demos reproducible without credentials. An optional live model exercises the same tools against synthetic data only; it does not enable marketplace access.

Included: exact identity checks, evidence freshness and provenance, conservative economics, questions-only versus price authority, duplicate handling within a run, material-fact reassessment, and summaries of synthetic owned units and reconciled outcomes.

Excluded from this delivery: live searches/messages, seller commitments, payments, production inventory mutations, persistent scheduling, deployed A2A, remote tracing, private web UI, data migration and tracker synchronization. These remain named integration milestones, not silently satisfied by fixtures.

## 2. Full business flow

Full V1: scheduled discovery → exact-card/evidence review → valuation → mandate → Sales negotiation → reassessment when facts change → exact operator approval → controlled commitment → payment/receipt/inspection → resale → settlement and outcome analysis.

This slice implements discovery from fixture listings through assessment and mandate, accepts synthetic reassessment requests, and reads synthetic stock/outcomes. It produces structured Sales handoff artifacts but does not call a Sales endpoint. Its mandate is marked `simulation` and cannot authorize a live message.

Unresolved identity yields `review` with no outreach authority. Correct identity with missing condition or insufficient resale evidence can yield a questions-only mandate if the fixture policy permits enquiries. A known disallowed condition, negative economics or exhausted exposure yields rejection. Missing or invalid policy values never receive permissive defaults.

## 3. Stack and deployment

Use an isolated Python package under `market_agent/`, alongside the existing React/TypeScript tracker. Use Deep Agents and its LangGraph graph, Pydantic validation, Python decimal arithmetic, and pytest. Pin mutually compatible released dependencies and a supported Python version during implementation after checking official SDK documentation; the design does not assume unverified version numbers or API signatures.

The package has no runtime import from the open Sales PR and does not modify its files. An implementation builder may choose the package runner and small internal file layout. A README must provide environment creation, locked installation, tests, and a deterministic demo command such as `python -m pokemon_market demo --scenario qualified`.

Only in-memory, per-run state is required. Export results to stdout as JSON, with diagnostics on stderr. Persistent recovery is a later acceptance gate. There is no new server, database, Docker service or deployment in this slice.

## 4. Inventory / Market Agent

Inputs are validated, bounded synthetic records: listing/seller IDs, listing snapshot version, exact-card facts, evidence references and observation times, operator policy, exposure snapshot, owned-unit records and actual-outcome entries. An injected timezone-aware clock makes expiry and ageing reproducible.

Exact identity includes set, card number, language, printing/finish and raw/graded status; graded records include grading company and grade. Support single-card listings only initially. Bundles, missing critical identity and conflicting identity require review. Compare explicit identity fields deterministically; model confidence cannot override a mismatch. Fixture text must never establish trusted verification flags by itself.

Evidence records distinguish asking prices, reference-market observations, observed resale outcomes and explicitly operator-reviewed assumptions. Every valuation preserves source, currency, observation time, condition coverage and assumption status. This slice accepts SGD evidence only; foreign-currency observations require review until an explicit dated FX contract is agreed. Reference/asking prices alone cannot qualify a resale estimate.

Proposed first-slice valuation policy: require an explicit positive `minimum_observed_sales` in the fixture policy. Eligible observations must be distinct completed resale records for the exact identity and reviewed condition, in SGD, timestamped no later than the injected clock and no older than the policy maximum age. If the minimum count is met, use the lowest eligible observed gross resale amount; retain the other eligible amounts as explanatory scenarios only. Otherwise use a single current operator-reviewed gross resale assumption bound to that identity, condition and policy version, only if policy expressly permits it. Assumption approval comes from trusted session configuration, never listing/model input. Missing or conflicting approved assumptions require review. An assumption cannot raise a ceiling established by sufficient observations. This deliberately simple fixture rule is not a calibrated live valuation policy; changing it for production requires operator agreement and evaluation.

Policy specifies allowed identities/categories/conditions, evidence maximum age, mandate duration, required profit, per-item and total acquisition limits, available capital, soft-exposure cap and permission for questions-only enquiries. Numeric limits are required fixture inputs, not production recommendations. Enquiries consume no price exposure and confer no price authority.

Deterministic economics use finite, nonnegative decimal strings with at most two fractional digits and explicit `SGD`; reject floats, exponents, NaN/infinity and excess precision at input boundaries. Quantity is exactly one in this slice. Conservative net resale is gross resale minus selling fees, delivery and other selling costs. Maximum item price is net resale minus required profit minus acquisition delivery, fees and other acquisition costs. Cap it by the per-item ceiling and remaining total capital/soft exposure after acquisition costs. No qualifying positive ceiling means no price mandate. Demonstrate exact amounts and equality boundaries in tests; do not introduce percentage fee estimates or rounding assumptions.

Example fixture: eligible gross resale `120.00`, selling fees `10.00`, selling delivery `5.00`, required profit `20.00`, acquisition delivery `3.00`, acquisition fees `2.00`, and zero other costs produce an economic item ceiling of `80.00` and total acquisition exposure of `85.00`, before tighter policy caps. The session receives available capital already net of existing hard obligations and a separate existing soft-exposure amount; subtract existing soft exposure and new session reservations once when calculating remaining capital. Soft-cap headroom subtracts those same soft reservations once. Never treat negotiation exposure as payment or deduct already-accounted hard obligations again.

The domain service, not the model, stores assessments and issues simulated mandates. Price mandates reserve their maximum total acquisition exposure in the in-memory session. Duplicate `(seller_id, listing_id)` discoveries reuse the active record and exposure; changed snapshots force reassessment. New material facts revoke the old mandate before any replacement is considered, including when reassessment fails. The service rejects stale versions/expired authority and releases or replaces simulated exposure exactly once. No concurrency or cross-process guarantees are claimed.

Inventory is read-only to this agent. Fixture unit records preserve purchase, receipt, inspection, availability, reservation, fulfillment and settlement facts. Available stock requires receipt plus passed inspection; a collection quantity is not sufficient. Summaries show unit age from acquisition time, unsold cost basis and unsettled records. Realized profit uses only complete reconciled outcome entries, actual proceeds/refunds and actual acquisition/selling costs. Incomplete outcomes are labelled pending, not assigned zero costs; returned physical stock requires reinspection. No autonomous policy changes follow these summaries.

## 5. Sales Agent boundary

Reuse the responsibilities documented by the Sales workstream: enquiries, conditional negotiation, seller fact extraction, approval preparation and assisted resale. Do not implement those capabilities in the Market package.

The current Sales proposal uses integer minor units and numeric policy/state versions; the HTML describes decimal money strings and a broader business envelope. This slice owns a temporary Market schema with `schema_version: "1"`, explicit evidence/assessment/policy/conversation versions and simulated authority. It does not claim drop-in Sales compatibility or copy the Sales models. The README includes a mapping table and outstanding peer decisions; a production adapter and shared schema are follow-up work under the shared-contract agreement.

## 6. Deep Agents harness

The real graph receives controlled instructions and only these business capabilities: read fixture listings/evidence, request deterministic assessment, request simulated mandate, reassess a candidate, read scoped owned-unit status and summarize reconciled outcomes. The builder may consolidate tools where that simplifies authorization.

Tools are bound to a single session and its record allowlist. Unknown IDs, mismatched ownership, invalid schemas and cross-session references fail closed. All numeric/state decisions are recomputed or loaded by services, never accepted from model text. Validate final structured output against the stored service result and references; unsupported or fabricated assertions cannot become an authoritative assessment.

Inspect and constrain the selected Deep Agents defaults. No delegation/spawn, shell, host filesystem, unrestricted network, database credentials, messaging or approval tools may be reachable. If scratch-file tools are necessary, use bounded ephemeral task storage containing no secrets; they confer no business authority. Cap tool/model steps and retries with deterministic failure output. Live-model credentials remain in the runtime environment and out of prompts, fixtures, artifacts and logs.

Tests must invoke the real graph with a controlled model that calls its tools; testing plain helper functions alone does not establish a runnable harness. Isolation and tool-surface tests assert forbidden capabilities are absent or denied.

## 7. A2A interaction contract

Represent four future operations: Market sends `negotiate_acquisition` and `prepare_resale`; Market receives `reassess_opportunity` and `assess_owned_unit`. First-slice artifacts are business payloads, explicitly **not authenticated A2A traffic**. There is no server endpoint or transport identity field trusted as authentication.

Each request carries schema version, request ID, correlation ID, applicable policy/assessment/conversation versions, expiry and evidence references. Mandate references are required only for operations acting on an existing mandate. Reassessment contains an explicit allowlist of changed identity, condition, price, quantity, delivery or fee facts. Unknown fields fail validation.

Within the session, an identical request ID and payload returns the recorded result; a reused ID with changed payload conflicts. Different business operations use distinct request IDs. Bound reassessment attempts per opportunity and reject stale conversation/assessment versions. Idempotent replay exposes the original result without reissuing or revalidating authority as current; consumers must separately check current mandate status. Revoke/expire outcomes remain visible.

Later integration adds actual protocol Agent Cards, authenticated tasks/messages/artifacts, peer/skill authorization, persistent idempotency, cancellation and recovery tests. A negotiation result is proposed terms, never proof of purchase or approval.

## 8. Tools and MCP

Use ordinary typed Python domain calls and fixture adapters. No MCP server is needed for this delivery. The source adapters are bounded reads from packaged synthetic data; no hidden Carousell endpoints, browser automation or new collector.

Later, consume approved market evidence through the agreed service boundary and enable Carousell capabilities only after authorization and outcome-reconciliation evidence. MCP is optional tool interoperability, not marketplace permission. Retain evidence provenance and missingness through every adapter.

## 9. Approvals and guardrails

No tool grants operator approval, changes real inventory, dispatches a message or moves funds. Simulated policy/mandate operations never produce executable approval. Model proposals cannot increase operator limits, change evidence trust, mutate policy, disclose private ceilings to a seller or broaden record access.

Include malicious fixture listing text that asks the agent to change policy or reveal secrets. Business services enforce identity, evidence, money, expiry, state and record scope independently of prompt instructions. Logs expose only synthetic inputs and bounded diagnostic codes; controlled failures must not dump credentials or model configuration.

Full V1 still requires exact operator approval, atomic real budget/stock holds, durable outbox/reconciliation, global stop, receipt/inspection and returns handling. The simulated session cannot substitute for those services or their concurrency tests.

## 10. Operator interface

First-slice interface: CLI JSON results and a short README scenario guide. Each result states simulation mode, decision/reason codes, exact identity, evidence age/limitations, valuation components, authority status/expiry and pending questions. Internal ceilings are operator-facing data only; no counterparty-facing text is generated.

The full private UI remains a follow-up: automation controls, leads, evidence, inventory summaries and operations views integrated with the Sales-owned approval console. Do not add private records to the public tracker, public RPC or GitHub Pages artifacts.

## 11. Delivery and acceptance

Implementation reaches only the new Python package, its fixtures/tests/lock file, package README and verification record, plus this workstream's design/implementation-plan documents. Existing React callers, collection migrations, pricing endpoint, Sales package and deployment remain unchanged. Root documentation links are optional if needed for discovery; do not reorganize unrelated docs.

Before implementation: approve this design, invoke Superpowers writing-plans, refresh both repositories' issues/PRs and Project Active/Blocked status, create or reuse a non-overlapping issue with acceptance/dependency sections, and complete the repository's maintainer Ready and signed claim gates. Design documentation alone establishes no ownership. The last Project read failed for missing `read:project` scope; this remains unresolved rather than evidence of no blockers.

The first-slice issue can be independent of Sales merge and live marketplace access because it has no Sales runtime dependency and only simulated adapters. Shared contracts, production storage and approved access are dependencies of later integration. Maintainers must confirm this boundary before Ready.

Acceptance evidence:

- Real graph demo calls scoped tools and emits a validated qualified result with an exact expected ceiling.
- Wrong language/printing/grade, bundles and unresolved identity cannot produce outreach authority; missing condition produces at most questions-only authority.
- Stale or unsupported evidence, unreviewed assumptions and missing limits cannot produce price authority. A recorded operator-reviewed assumption remains visibly labelled.
- Cost/profit, capital and exposure boundary fixtures return exact decimal results; duplicate discovery/request replay cannot duplicate simulated exposure.
- Material changes revoke old authority; stale/expired versions, conflicting request IDs and reassessment limits fail closed.
- Separate sessions cannot read each other's records; forged result references and malicious listing instructions cannot bypass service rules.
- Inventory fixtures demonstrate inspected availability, pending settlement, unsold cost basis, a reconciled profitable sale and a refunded sale with unrecovered costs.
- Tests run offline with controlled model transport. Report live-model verification separately; absence of credentials is not a reason to fake such a test.
- Run focused Python tests, locked dependency consistency checks, all documented deterministic scenarios and whitespace/content checks. Frontend checks are required only if frontend behavior changes.

Following milestones: agree shared contracts/ledger; add persistent services and scheduling; add authenticated A2A and recovery; integrate sanitized Langfuse tracing/private UI; prove authorized connector capabilities; then perform bounded live acceptance. These require their own accepted issues and verification evidence. No software-only test establishes live readiness or profitability.

## 12. Decisions and sources

Selected by the operator: runnable Market slice first, on `feature/market-agent`, using the supplied V1 direction and Superpowers.

Builder proposals in this design: isolated package; synthetic single-card SGD inputs; credential-free controlled model demo; per-run in-memory state; lowest qualifying observed resale with a configured minimum sample count, or an explicitly permitted reviewed assumption; CLI output; no first-slice Sales adapter. These constrain the initial delivery while preserving explicit integration work.

Outstanding production decisions: shared ledger/storage, agreed peer schema and identity mapping, authorized connector, actual trading limits/categories, schedule and quiet hours, model/host/trace retention and private operator access. They do not receive invented production values in fixture configuration.

Sources:

- [V1 system and agent plan](../../../output/plans/pokemon-reselling-v1.html), all twelve sections.
- [Repository rules](../../../AGENTS.md), [contributing](../../../CONTRIBUTING.md), [ledger](../../../LEDGER.md), and [current application](../../../README.md).
- [Sales runnable-slice issue #9](https://github.com/Perryong/pokemon-tracker/issues/9) and [proposed implementation PR #23](https://github.com/Perryong/pokemon-tracker/pull/23), inspected during scope discovery; neither is assumed merged.
- [Shared contracts issue #11](https://github.com/Perryong/pokemon-tracker/issues/11), including peer-agreement and storage blockers.
- Official SDK/protocol references linked by the HTML must be rechecked when selecting dependencies. This design does not assert that historical SDK examples remain current.

Only public repository context and synthetic requirements belong in these committed documents. Do not copy restricted project evidence into this public repository.
