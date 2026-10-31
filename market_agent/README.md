# Simulated Inventory / Market Agent

A real Deep Agents graph assesses synthetic Pokémon listings, invokes deterministic pricing tools and requests **simulated** negotiation mandates. The default model transport is controlled and credential-free. It is a runnable software slice, not a live Carousell integration.

## Run locally

Verified with Python **3.12.13**. Run from the repository root:

```sh
uv venv --python 3.12 market_agent/.venv
uv pip install --python market_agent/.venv/bin/python -r market_agent/requirements.lock
uv pip install --python market_agent/.venv/bin/python --no-deps --no-build-isolation -e ./market_agent
uv pip check --python market_agent/.venv/bin/python
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

## Durable private fixture workflow

The operator selected the documented Market contract as the temporary development target, with a fixture Sales peer and Supabase-compatible PostgreSQL. Business state lives in `market_private`; LangGraph checkpoints live separately in `market_checkpoints`. Graph checkpoints do not grant authority. A stable workspace owns exposure across runs and restarts.

Build the frontend (`npm run build`) and start its existing reference backend (`npm run preview -- --host 127.0.0.1 --port 5193`). Configure the private service process with these environment variables through your local secret manager or an untracked protected file:

- `MARKET_DATABASE_URL`: trusted direct/session PostgreSQL connection, using a dedicated server role. For Supabase use the connection details from that project's dashboard and its required TLS settings. Transaction pooling is not verified.
- `MARKET_OPERATOR_TOKEN`: a random secret of at least 32 characters, used only at the private login form.
- `MARKET_PEER_TOKEN`: a different random secret of at least 32 characters for fixture peer HTTP requests.

For a **disposable simulation database only**, explicitly initialize synthetic data and serve the private UI:

```sh
market_agent/.venv/bin/python -m pokemon_market serve \
  --workspace market-operator-fixture --initialize-demo \
  --port 8791 --dist dist --reference-url http://127.0.0.1:5193
```

`--initialize-demo` creates the private schemas and seeds this workspace once, rebasing synthetic fixture dates to initialization time. A restart never refreshes its evidence, policy or expiry. Later starts may omit this flag. An unknown workspace fails rather than inventing data. Stop with Ctrl-C; restart with the same workspace and database. Operator cookies expire after eight hours and reset on server restart; business state persists.

Open the loopback URL, select **Market → Open private operations**, and enter the operator key. The private panel supports bounded Singapore schedules, pause/resume, assessment, conservative/base/upside comparisons, current simulated mandates, sanitized run status and fixture inventory/outcomes. The worker checks durable jobs every five seconds, catches up only the latest scheduled slot after downtime, and recovers expired leases even without a recurring schedule. Transient fixture peer failures replay the same request at most three attempts; other failures remain visible for review. Pausing prevents new job claims and peer dispatch; an already executing deterministic tool can finish.

The server binds only `127.0.0.1`, validates Host and mutation Origin, bounds JSON requests and read time, and separates HttpOnly/SameSite operator cookies from peer bearer authentication. It proxies only the configured loopback reference/cardmarket paths. A plain Vite/public deployment has no private operator backend and must show unavailable. This local standard-library host is not an internet deployment or multi-user authentication system.

### Fixture A2A boundary

The A2A SDK validates Agent Cards, SendMessage requests, task responses and artifacts for the HTTP+JSON 1.0 binding. Both fixture role endpoints require the peer bearer key:

- `/a2a/market/.well-known/agent-card.json`, `/a2a/market/message:send`, `/a2a/market/tasks/{id}`
- Equivalent `/a2a/sales/...` routes for the fixture Sales role.

Structured A2A parts contain `data.requestJson`, the canonical strict Request JSON string; response parts contain `data.resultJson`, the canonical Artifact JSON string plus explicit fixture/mode/outcome/approval metadata. This avoids protobuf Struct converting integer counters to floating point during real SDK transport. Nested JSON must be canonical (sorted keys, compact separators, no duplicate keys). The business envelope preserves full card identity, strict decimal money and separate policy/assessment/conversation versions. Completed tasks describe simulated proposed terms or resale drafts; they never grant purchase approval or imply seller contact. The fixture does not import or alter Sales PR #23. Real Sales agreement/interoperability remains [#11](https://github.com/Perryong/pokemon-tracker/issues/11)/[#12](https://github.com/Perryong/pokemon-tracker/issues/12).

### Verification and recovery

Database integration tests require `MARKET_TEST_DSN` pointing to a **disposable** PostgreSQL database. They create isolated synthetic workspaces. Without that variable, database tests skip; an offline pass alone does not verify persistence.

```sh
market_agent/.venv/bin/python -m pytest market_agent/tests -q
uv pip check --python market_agent/.venv/bin/python
NODE_OPTIONS=--no-experimental-webstorage npm test -- --run
npm run build
```

Back up both private schemas with `pg_dump`, store dumps as private data, restore to a separate disposable database and compare the business snapshot, job receipts, peer tasks and checkpoints before relying on a backup. This was exercised locally; no production Supabase migration or restore has been performed. Run status exposes only whitelisted IDs/status/timestamps/error codes; prompts, credentials, raw listing content and peer bodies are not exported as traces. Langfuse export and paid model evaluation remain unconfigured.

## Boundaries before live operation

The live reference adapter preserves original currencies, provenance and timestamps. Reference quotes are not completed sales and do not qualify acquisition authority. No approved marketplace discovery connector, real Sales peer, authoritative shared stock/budget/approval service or live operator policy is configured. Scheduling currently discovers the explicitly seeded synthetic listings only. The read-only inventory is a fixture view, not the shared production ledger under #16.

There are no live seller messages, commitments, payments, stock mutations or tracker synchronization. Repeated physical resale/return cycles still require the authoritative ledger. New workspaces must not be used to evade exposure limits. Hosting, shared-service integration, live policy, marketplace authorization, model/trace budgets and real operational acceptance remain external gates. See [software verification](../docs/market-v1-software-verification.md).

[Issue #24](https://github.com/Perryong/pokemon-tracker/issues/24) tracks this slice. The operator explicitly authorized a **one-time local build/test exception** to the repository's Project/signed-claim gate on 30 October 2026. The operator subsequently extended the exception to pushing this branch and opening a draft PR. This is not a signed claim, Project completion, merge or deployment approval. See [verification](VERIFICATION.md) for actual evidence.
