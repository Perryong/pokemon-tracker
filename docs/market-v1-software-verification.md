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
| #38 Peer | Authenticated A2A HTTP+JSON 1.0 fixture roles, SDK message/task round trip, durable receipts | Real Sales interoperability; full protocol cancellation/typed-error coverage is not claimed |
| #39 Inventory | Read-only fixture inspection/ageing/cost/outcome summaries, including unresolved settlement | Authoritative shared inventory/outcome ledger #16 |
| #40 UI | Cookie-authenticated loopback operations, schedules, pause, assessments, mandates, scenarios, fixture inventory and blocked reasons | Private production hosting/authentication; this local host is single operator |
| #41 Acceptance | Durable sanitized run metadata, offline/database/browser/recovery tests and fresh review | Langfuse sink/export, model budget/credentials and bounded real-model/live acceptance |

Business state and checkpoints use distinct private PostgreSQL schemas. Every run uses the same operator workspace; run IDs never reset exposure. The public tracker does not receive operator credentials, private records or fixture fallback. A plain Vite deployment reports the private backend unavailable.

A2A structured parts carry canonical business JSON in `requestJson`/`resultJson`, preserving strict integer counters through actual SDK protobuf serialization. Successful tasks remain fixture proposals with `approval: false`. No seller messages, commitments or stock/cash mutation occur.

## Fresh checks

| Check | Actual result |
| --- | --- |
| Full Python suite with `MARKET_TEST_DSN` and worktree `PYTHONPATH` | **263 passed**, no database skips |
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

No production Supabase migration, live marketplace discovery/contact, real Sales exchange, shared-ledger integration, paid model call or Langfuse export was performed. The standard-library server is loopback development hosting. Cancellation routing and SDK typed error envelopes are not full-protocol acceptance. No roadmap task requiring those real integrations is closed based on fixture tests, and nothing is merged into main or automatically queued in Symphony.


The existing GitHub/Vercel integration automatically built a public preview after the branch push; its checks succeeded. That preview has no private operations backend. No production or private-service deployment was performed. Ruflo tools were unavailable; execution used the repository workflow and Superpowers review.


## Live reference research update

The operator selected real card-price research as the next data source. Market now automatically loads the existing default card from the real TCGdex feed on entry, with dated SGD conversion, separate provider/fetch timestamps, cache limits and explicit opt-in synthetic controls. Search, manual refresh and failure behavior remain supported. Reference quotes do not become completed sales or mandate authority.

Fresh frontend checks: **215 tests passed across 23 files**, build/focused ESLint/whitespace passed. Playwright verified automatic Alakazam display, refresh, Pikachu selection, real FX provenance and 390px layout. Cancellation, initial-response races, strict effect remount and collection persistence have regressions. The current browser tab shows the new research view; the fixture scheduler is paused. This frontend change did not require repeating the unchanged Python/database suite.

Fresh independent review found no Important/Critical or actionable minor findings and independently passed 42 relevant frontend tests.

## Merge-readiness review and recovery correction

A fresh whole-branch review found that a successful mandate-linked reassessment revoked its previous mandate, then rejected an identical transport retry with `authority_inactive`. The same problem prevented recovery after a business commit followed by a lost peer receipt. Both failures were reproduced before changing the implementation.

Exact successful reassessment replay now uses the durable request fingerprint and current assessment/conversation versions without requiring the old mandate to become active again. Material listing updates invalidate replay even before another assessment is calculated. New requests still reject revoked mandates. Regression tests cover receipt replay, interrupted receipt recovery, later unassessed changes and attempted reuse of revoked authority; the original mandate remains revoked after recovery.

After this correction, the full Python suite passed **263 tests**, including **33 peer tests**, with real disposable PostgreSQL and no skips. Ruff symbol checks and whole-branch whitespace checks passed. Fresh checks immediately before this backend-only correction passed **215 frontend tests**, build, changed-TypeScript lint, dependency compatibility, wheel packaging and all six controlled CLI scenarios from the installed wheel outside the checkout. Full lint was rerun and retains **9 errors / 5 warnings**, all in unchanged files.

One Minor review finding is deferred: the private reference proxy drops `X-Market-Priority: background`, so proxied batch research can consume the Node backend's reserved foreground request slots. The backend still enforces its overall rate limit, but manual selection can temporarily receive a rate-limit response during a batch. Forwarding this validated priority header and testing the foreground reserve remains a UI/proxy follow-up under #40. No production Supabase, real Sales or live marketplace acceptance is asserted by this review.
