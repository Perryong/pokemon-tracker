# Simulated Inventory / Market Agent

A real Deep Agents graph assesses synthetic Pokémon listings, invokes deterministic pricing tools and requests **simulated** negotiation mandates. The default model transport is controlled and credential-free. It is a runnable software slice, not a live Carousell integration.

## Run locally

Verified with Python **3.12.13**. Run from the repository root:

```sh
uv venv --python 3.12 market_agent/.venv
uv pip install --python market_agent/.venv/bin/python -r market_agent/requirements.lock
uv pip install --python market_agent/.venv/bin/python --no-deps --no-build-isolation -e ./market_agent
market_agent/.venv/bin/python -m pip check
market_agent/.venv/bin/python -m pytest market_agent/tests -q
market_agent/.venv/bin/python -m pokemon_market demo --scenario qualified
```

With Python 3.12 and pip already installed, a standard `python3.12 -m venv` and the equivalent `.venv/bin/python -m pip install` commands also work. No frontend development server is needed.

| Scenario | Expected outcome |
| --- | --- |
| `qualified` | S$80.00 maximum item price; S$85.00 total simulated acquisition exposure |
| `questions-only` | Missing verified condition; enquiries only, no price authority |
| `identity-review` | Wrong language; review, no mandate |
| `stale-evidence` | Stale observations; questions only |
| `reassessment` | First qualify, then receive damaged-condition facts; revoke previous mandate and reject |
| `inventory` | Inspected availability, ageing, S$5.00 aggregate realized profit and one pending outcome |

Every scenario uses **30 October 2026, 04:00 UTC** as its injected clock. The historical fixture dates and expiry are intentional. The command emits one JSON document to stdout. Diagnostics go to stderr. Review/rejection is a successfully processed result (exit 0); invalid configuration is exit 2 and runtime failure is exit 1.

All records and numeric policy limits are synthetic. The qualified fixture uses S$120 gross resale, S$15 selling costs, S$20 required profit and S$5 acquisition costs. These are test assumptions, not advice or live settings.

## What the services enforce

- Exact set/number/language/printing/finish/raw-or-graded identity; bundles and ambiguous matches enter review.
- Fresh comparable completed sales, distinct source transactions and explicit currencies. Asking/reference prices alone do not qualify. Choose the lowest qualifying observation once the configured sample count is met; otherwise use a permitted, current operator-reviewed assumption.
- Strict decimal money, required limits, evidence expiry, maximum exposure and per-item ceilings. Assessment alone does not reserve exposure.
- Session-scoped request IDs, payload conflicts, version checks, duplicate discovery, one active simulated mandate per listing, revocation on new material facts, and once-only expiration/release. A current material change beyond the reassessment limit still revokes authority and records the facts; that listing is then blocked for the rest of the session. A new operator-reviewed fixture/session is required to resume.
- Read-only inventory: receipt and inspection before availability; physical returns require reinspection. Reserved inspected units retain their valuation but cannot prepare resale. Pending costs/settlement do not become fabricated zero-cost profits. Returned stock retains its cost basis; `cash_result` reports actual net cash separately from realized profit so held stock is not expensed twice.
- A real graph with scoped tools and a terminal `FinalReference` tool. The model names a result already stored by a service; it cannot supply authoritative prices, IDs, policy or approval. Acquisition completion must reference the mandate-stage result, including exposure-based rejections. Internal price ceilings are for the operator, and no counterparty message is generated.

Graph entry operations are `assess_opportunity`, `reassess_opportunity`, `assess_owned_unit` and `prepare_resale`. Standalone `issue_mandate` and `negotiate_acquisition` are session APIs; acquisition graphs issue their mandate internally.

The graph is bounded to 12 model calls, 24 tool calls, a 60-second response deadline and one final-output retry. The selected live provider has a 30-second request timeout and zero transport retries. On the response deadline, a daemon worker may finish an already-running model request, but cancelled/deadline checks deny later tools. This is not a sandbox for executing arbitrary Python supplied by callers.

Deep Agents 0.7.32 requires an internal `read_file` tool. It has only ephemeral StateBackend storage, no host backend, no writes or content offloading; its schema is hidden and dispatch is denied. No delegation, shell, database, payment, marketplace or approval tool is available. Live tracing is disabled. Provider profiles are configured process-wide for the chosen model within this dedicated application.

## Optional live model, synthetic tools

An explicit model option can make paid model API calls. Configure `OPENAI_API_KEY` in the process environment, then choose your accessible model:

```sh
market_agent/.venv/bin/python -m pokemon_market demo --scenario qualified --model openai:YOUR_MODEL
```

Only the OpenAI adapter is configured in this slice. Do not put keys in fixtures, arguments, prompts or Git. This mode still uses synthetic listings and in-memory authority. Live model quality, account access and costs have **not** been verified by the offline suite.

## Temporary peer contract

The package does not import or alter Sales PR #23. These are application artifacts, **not authenticated A2A messages**.

| Market slice | Sales proposal / integration decision |
| --- | --- |
| `schema_version: "1"`, simulation mode | Agree a shared versioned envelope and authenticated sender before integration |
| SGD decimal strings (`"80.00"`) | Proposal uses integer `ceiling_minor`; agree lossless currency/precision conversion |
| String policy version and integer assessment/conversation versions | Proposal uses numeric policy/state versions; agree authority and mapping rather than casting blindly |
| `negotiate_acquisition`, `prepare_resale` artifacts | No Sales dispatch; later use real authenticated A2A tasks/artifacts |
| `reassess_opportunity`, `assess_owned_unit` | Local validated request handling only; no transport authentication |
| Historical replay result | Check `current_mandate` separately; replay never renews authority |

See [shared-contract issue #11](https://github.com/Perryong/pokemon-tracker/issues/11) and [Sales PR #23](https://github.com/Perryong/pokemon-tracker/pull/23). Owned-unit valuation reuses the evidence/economics calculation with zero proposed acquisition fees; its ceiling is an analytical output, not permission to buy, reserve or sell that unit.

## Boundaries and next integration work

The session stores records in memory; a new process starts fresh. There are no durable schedules, restart recovery, persistent global exposure, real budget/stock holds, operational tracing, authentication server or private web UI. Session locks serialize concurrent graph tool calls only within that process. Inventory fixtures support one lifecycle outcome per physical unit; repeated resale/return cycles require the later authoritative ledger.

No live searches, messages, commitments, payments, stock mutation, data migration or tracker synchronization occur. The existing React tracker, browser collection and Sales workstream remain separate. Full V1 still requires shared contracts/ledger, persistent workflows, authenticated A2A, exact approvals, authorized marketplace capabilities and live acceptance.

[Issue #24](https://github.com/Perryong/pokemon-tracker/issues/24) tracks this slice. The operator explicitly authorized a **one-time local build/test exception** to the repository's Project/signed-claim gate on 30 October 2026. This is not a signed claim, Project completion, merge or deployment approval. See [verification](VERIFICATION.md) for actual evidence.
