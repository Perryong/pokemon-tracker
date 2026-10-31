# Market V1 fixture software verification

31 October 2026, Asia/Singapore. Branch `feature/market-agent-ui-v1`; ready-for-review [PR #42](https://github.com/Perryong/pokemon-tracker/pull/42), roadmap [#31](https://github.com/Perryong/pokemon-tracker/issues/31).

The operator selected Supabase PostgreSQL and the documented Market contract with a fixture Sales peer. This delivery implements that **simulation software target**. Existing native dependencies and real integration acceptance remain open. The operator's existing personal Project/claim exception applies; no signed claim, Project state, merge or live approval is asserted.

## Implemented boundary

| Roadmap task | Delivered software | Remaining integration gate |
| --- | --- | --- |
| #32 Contracts/policy | Canonical strict Market requests, complete card identity, decimal strings, separate versions, fixture target recorded | Agreement with real Sales/shared services; actual live policy |
| #33 Persistence | Transactional PostgreSQL business state, private graph checkpoints, lease recovery, immutable workspace seed, backup/restore | Production Supabase access, deployment and operational backups |
| #34 Evidence | Bounded TCGdex reference adapter, provenance/currency/time checks and exact identity qualification | Approved marketplace/completed-sale sources; reference quotes never qualify as completed sales |
| #35 Scenarios | Deterministic conservative/base/upside calculations and private UI comparison; current mandate ceiling retained | Live evidence/policy inputs |
| #36 Discovery | Durable Singapore schedules, latest-slot catch-up, stable listing/workspace IDs, pause and bounded retries | Authorized marketplace discovery connector; current worker uses seeded fixtures |
| #37 Authority | Durable idempotency, exposure serialization, stale-version rejection, expiry/revocation and exact-request recovery | Real shared budget/approval authority and live limits |
| #38 Peer | Authenticated A2A HTTP+JSON 1.0 fixture roles, SDK message/task round trip, durable receipts | Real Sales interoperability; asynchronous running-task cancellation/streaming remain outside the synchronous fixture host |
| #39 Inventory | Read-only fixture inspection/ageing/cost/outcome summaries, including unresolved settlement | Authoritative shared inventory/outcome ledger #16 |
| #40 UI | Cookie-authenticated loopback operations, read-only scope/watchlist, dispatch history, Singapore run timing, listing identity, evidence freshness, versions, scenarios and fixture inventory | Private production hosting/authentication; this local host is single operator |
| #41 Acceptance | Durable sanitized run metadata, offline/database/browser/recovery tests and fresh review | Langfuse sink/export, model budget/credentials and bounded real-model/live acceptance |

Business state and checkpoints use distinct private PostgreSQL schemas. Every run uses the same operator workspace; run IDs never reset exposure. The public tracker does not receive operator credentials, private records or fixture fallback. A plain Vite deployment reports the private backend unavailable.

A2A structured parts carry canonical business JSON in `requestJson`/`resultJson`, preserving strict integer counters through actual SDK protobuf serialization. Successful tasks remain fixture proposals with `approval: false`. No seller messages, commitments or stock/cash mutation occur.

## Fresh checks

| Check | Actual result |
| --- | --- |
| Full Python suite with `MARKET_TEST_DSN` and worktree `PYTHONPATH` | **267 passed**, no database skips |
| Six controlled CLI scenarios | **6/6**, valid JSON stdout and empty stderr |
| `uv pip check --python market_agent/.venv/bin/python` | All 81 installed packages compatible |
| Frontend `NODE_OPTIONS=--no-experimental-webstorage npm test -- --run` | **215 passed**, 23 files |
| `npm run build` | Passed |
| ESLint for MarketOperations, its tests and modified MarketView | Passed |
| Ruff undefined/unused-symbol checks across Python source/tests | Passed |
| `git diff --check` | Passed |
| Full `npm run lint` | Existing **9 errors / 5 warnings** in unrelated unchanged files |

Use the commands in [the package README](../market_agent/README.md). Database tests skip without the disposable test DSN; a skipped run is not persistence evidence. Worker-only evidence checks also passed 75 tests; an actual bounded `base1-1` lookup returned a current TCGdex/Cardmarket EUR reference quote. A transport timing bug discovered by that real lookup was reproduced and corrected using request-completion time without accepting genuine future data.

## Recovery, protocol and browser proof

- PostgreSQL tests cover concurrent/replayed mandate issuance, exact-request replay after a lost execution receipt, failure rollback, expiry, immutable seeds, schema privacy and graph recovery.
- Restarted the actual private service against the same database/workspace; assessments, mandate IDs, schedule and runs survived. Cookies required login again as designed.
- `pg_dump` of `market_private` and `market_checkpoints` was restored into a separate disposable database. The business snapshot and counts for run receipts, peer tasks and graph checkpoints matched. The restore database was then removed; the local demo database remains temporary.
- Actual `RestTransport.send_message()` and `get_task()` ran over authenticated loopback HTTP. Canonical JSON preserves money, opaque policy versions and strict counters; malformed/duplicate JSON, forged identities, stale versions, replay conflicts and unauthorized skills reject.
- Playwright against the built private service verified anonymous operator/A2A denial, login, persisted state, assessment, schedule save, due work, pause/resume, one active mandate, scenario comparison, fixture inventory, logout and 390px width without document overflow.
- Saved local browser proof: `/tmp/market-v1-private-desktop.png` and `/tmp/market-v1-private-mobile.png`. These contain synthetic data only. The service is left **paused** after the checks.
- Earlier reference UI browser checks remain recorded in [baseline verification](market-v1-baseline.md).

Fresh review found five Important issues in the initial implementation: actual SDK numeric serialization, expired manual result reuse, terminal transient peer failure, unscheduled recovery and scenario provenance under concurrent updates. Each was reproduced before its correction and now has regression coverage. A second review found pause-after-graph recovery; this now queues the same request for resume. UI review corrected full-length IDs, pause controls, expiry updates, sanitized run errors and bounded inactive mandate history. Final focused review found no remaining Important issues in those corrections.

## Limits

No production Supabase migration, live marketplace discovery/contact, real Sales exchange, shared-ledger integration, paid model call or Langfuse export was performed. The standard-library server is loopback development hosting. Terminal-task cancellation routing and SDK typed errors are verified for the synchronous fixture host; asynchronous cancellation and streaming are not full-protocol acceptance. No roadmap task requiring those real integrations is closed based on fixture tests, and nothing is merged into main or automatically queued in Symphony.


The existing GitHub/Vercel integration automatically built a public preview after the branch push; its checks succeeded. That preview has no private operations backend. No production or private-service deployment was performed. Ruflo tools were unavailable; execution used the repository workflow and Superpowers review.


## Live reference research update

The operator selected real card-price research as the next data source. Market now automatically loads the existing default card from the real TCGdex feed on entry, with dated SGD conversion, separate provider/fetch timestamps, cache limits and explicit opt-in synthetic controls. Search, manual refresh and failure behavior remain supported. Reference quotes do not become completed sales or mandate authority.

Fresh frontend checks: **215 tests passed across 23 files**, build/focused ESLint/whitespace passed. Playwright verified automatic Alakazam display, refresh, Pikachu selection, real FX provenance and 390px layout. Cancellation, initial-response races, strict effect remount and collection persistence have regressions. The current browser tab shows the new research view; the fixture scheduler is paused. This frontend change did not require repeating the unchanged Python/database suite.

Fresh independent review found no Important/Critical or actionable minor findings and independently passed 42 relevant frontend tests.

## Merge-readiness review and recovery correction

A fresh whole-branch review found that a successful mandate-linked reassessment revoked its previous mandate, then rejected an identical transport retry with `authority_inactive`. The same problem prevented recovery after a business commit followed by a lost peer receipt. Both failures were reproduced before changing the implementation.

Exact successful reassessment replay now uses the durable request fingerprint and current assessment/conversation versions without requiring the old mandate to become active again. Material listing updates invalidate replay even before another assessment is calculated. New requests still reject revoked mandates. Regression tests cover receipt replay, interrupted receipt recovery, later unassessed changes and attempted reuse of revoked authority; the original mandate remains revoked after recovery.

After this correction, the full Python suite passed **263 tests**, including **33 peer tests**, with real disposable PostgreSQL and no skips. Ruff symbol checks and whole-branch whitespace checks passed. Fresh checks immediately before this backend-only correction passed **215 frontend tests**, build, changed-TypeScript lint, dependency compatibility, wheel packaging and all six controlled CLI scenarios from the installed wheel outside the checkout. Full lint was rerun and retains **9 errors / 5 warnings**, all in unchanged files.

The Minor reference-proxy priority finding from this review was subsequently corrected under #40; see the agent-inspection update below. No production Supabase, real Sales or live marketplace acceptance is asserted by this review.

## Agent inspection and proxy priority correction

The operator asked to proceed with the next task and inspect the agents. The task check found hosted reference integration #43 already delivered separately in draft PR #44, so this work continued the independent #40 proxy correction in PR #42.

The private proxy now forwards only the exact supported `X-Market-Priority: background` value on Market routes. This preserves the existing Node backend's 25-background/30-total request limits. Unknown priority values and Cardmarket routes receive no priority override; operator cookies and authorization headers remain excluded. A real HTTP regression reproduced the dropped header before the fix. All four proxy cases now pass, along with **267 Python tests with disposable PostgreSQL**, **42 Node middleware tests** (including foreground reserve), Ruff symbol checks and whitespace checks. Focused independent review found no actionable issues. No frontend source or bundle change was required.

At **17:27 Singapore time on 31 October 2026**, headed Playwright opened the private operations panel, authenticated using the protected local key, resumed the existing workspace, assessed `listing-1`, and paused scheduling again. New run `manual-1b9acbdf73a43b811d148dd5423af488` completed with a qualified assessment and **S$80.00 simulated item ceiling**. The stored authenticated fixture Sales task `c61f4ca3bc525ed6b7b2a317cd3523b3` completed with `proposed_terms` and `approval: false`. Existing history was retained. Screenshots: `/tmp/market-agent-inspection.png` and `/tmp/market-agent-assessment.png`.

This uses the real Deep Agents graph with a controlled model and synthetic business data. It does not verify paid-model behavior or a real Sales deployment. The inspection browser is authenticated locally; no credential was placed in Git or the screenshots. #40/#41 retain their production/integration acceptance gates.


## Operations inspection fields — 31 October 2026

The private panel now shows the persisted read-only synthetic scope/watchlist, exact current card identity and condition, listing/assessment/conversation/policy versions, evidence source/basis/original amount/currency/observation time, snapshot-relative freshness, reviewed-assumption details when present, and recorded mandate exposure. Scope, geography and fixture/live readiness remain explicit; this does not add a live policy editor.

Run timing uses the same Singapore slot calculation as the worker, including latest missed-slot catch-up, exact slots and midnight. Paused/no-schedule states have no next execution claim. Fixture transport configuration and the latest recorded dispatch outcome are shown separately from current connectivity. Historical graph completions without dispatch evidence remain unverified. A retry retains the prior failed dispatch in existing run JSON even if it subsequently fails before transport.

Fresh verification on the final implementation:

- **273 Python tests passed**, no skips, with `MARKET_TEST_DSN` pointing to disposable PostgreSQL and `PYTHONPATH=market_agent/src`; includes 24 workflow tests and CLI subprocess checks. An earlier invocation omitted the source path and failed seven CLI imports; the corrected full invocation passed.
- **221 frontend tests passed across 23 files**, including 27 private operations tests. Production build, focused ESLint, Ruff symbol checks and whitespace passed. Full lint retains **9 errors / 5 warnings** in unchanged files.
- Independent focused review found two Important issues: invalid timezone offsets could crash rendering, and retrying a failed dispatch could erase its displayed outcome. Both were reproduced by failing regressions before correction; the full suites above passed afterward.
- Headed Playwright at **18:52 Singapore time** authenticated to the existing workspace, inspected scope, resumed, ran a fresh assessment and paused scheduling again. Persisted run `manual-58e062b4dd14715a2df95de547a9d059` completed with a qualified assessment and **S$80.00 simulated item ceiling**; the fixture dispatch recorded success. Existing history remained intact.
- Desktop and 390px rendering were inspected visually; no horizontal document overflow. Local screenshots: `/tmp/market-operations-details-desktop.png`, `/tmp/market-operations-details-assessment.png`, `/tmp/market-operations-details-mobile.png`. The browser remains open and scheduling paused.

The inspection-field slice of #40 is delivered for the selected fixture target. #40/#41 remain open for shared UI/service agreements, private production hosting, real Sales/ledger acceptance, model-budget evaluation and Langfuse decisions. No production migration, main merge or live marketplace action was performed.


## Fixture peer cancellation and typed HTTP errors — 31 October 2026

The next actionable #38/#41 slice completes `POST /a2a/{role}/tasks/{id}:cancel` using the existing synchronous peer lifecycle. A completed task rejects cancellation with the SDK-recognized `TaskNotCancelableError`; unknown/other-role tasks return `TaskNotFoundError`. Cancellation does not reverse results, alter exposure or grant approval. Paused operation still permits task inspection and truthful cancellation responses. Body identity must match the path; tenant overrides, unknown fields and non-object metadata reject.

A2A responses now use the documented nested HTTP error envelope and pinned SDK error mappings; peer requests accept both `application/a2a+json` and legacy `application/json`. Authentication runs before body/task inspection. Malformed requests, unsupported skills, oversized bodies, paused service and runtime failures return bounded status information without echoing request metadata or exception text. Existing operator endpoints retain their response format.

Verification: **281 Python/PostgreSQL tests passed, no skips**, including **41 peer tests** and actual SDK HTTP transport. Seven new raw-HTTP cases failed before implementation; after correcting a test URL typo, the SDK cancellation regression was also rerun against the old server and failed for the expected missing route. All eight new cases pass in the final suite. Fresh scoped review found no Critical or Important findings. Ruff symbol checks and whitespace passed. No frontend source changed, so the preceding 221-test/build/Playwright UI results remain historical and were not repeated.

Protocol reference: [A2A 1.0.1 HTTP error handling](https://a2a-protocol.org/v1.0.1/specification/#116-error-handling). This finishes the synchronous fixture route/error gap, not asynchronous cancellation, streaming, real Sales interoperability, shared approvals/stock, Langfuse or paid-model acceptance. #38/#41 retain those applicable gates; no main merge or live action is included.


## Hosted reference integration — 31 October 2026

Integrated the already reviewed PR #44 commit `970ad32` into this branch, preserving automatic initial card lookup, selection/cancellation/race handling, private operations and collection behavior. Public Market health/search/native-card/FX calls now use the hosted pokemon-price-api. Private operations remain same-origin; the Python read-only evidence adapter and its optional trusted loopback backend are unchanged.

Hosted FX uses one shared request for EUR/USD, validates observation and server expiry, caps freshness, and converts native values once. Card Detail regression fixtures were updated to the same hosted contract; existing sleep/focus rate recovery tests remain.

Fresh checks: **226 frontend tests across 24 files**, build, focused ESLint and whitespace passed. Full lint still reports **9 existing errors/5 warnings**. The new hosted-public/local-private integration regression was observed failing before integration. Fresh scoped review found no actionable issues.

Headed Playwright against plain static `dist/` at port 8792 verified automatic live prices despite local `/api/market/health` returning 404. Native EUR 48.30 × dated rate 1.4282 displayed **SGD 68.98**; these are recorded observations, not fixed expected prices. Pikachu search/selection, desktop and 390px layout passed with no page errors/overflow. All eight observed Market requests used the hosted API without credentials or request bodies. Private operations reported unavailable on that static origin; separate authentication to the existing port8791 private host still showed scope and paused scheduling. Screenshots: `/tmp/market-hosted-integrated-desktop.png`, `/tmp/market-hosted-integrated-mobile.png`.

The unchanged backend's **281-test** result is from the preceding protocol task and was not repeated. Hosted API availability and physical-phone access remain external acceptance limits. PR #44's source commit is now incorporated, but neither PR is merged into main and no PR is closed automatically.
