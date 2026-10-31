# Market V1 integration baseline

Date: 31 October 2026 (Asia/Singapore). Workstream: [#31](https://github.com/Perryong/pokemon-tracker/issues/31).

The operator authorized starting the first task and continuing in dependency order,
including browser verification. The existing personal Project/claim exception
applies; this is not a signed claim or permission to merge or activate live trading.

## Selected revision and integration

The dedicated `feature/market-agent-ui-v1` branch was fast-forwarded locally from
`1141231bbf74f8ce6384ac50a57acafec5cdd976` to
`5720d200a8b449ed97c22f4772ed5cf7cf2b9e18`. That pinned snapshot contains the simulated
Market package from #24 / draft PR #25 and the Market view under #26, including the
SGD, discovery and latest selection/rate-recovery fixes. The original UI checkout
was left on its existing branch. No changes were made to Sales modules or main.

An isolated worktree reused the existing installed frontend dependencies and Python
3.12.13 environment. Python imports were explicitly directed at this worktree's
source. No dependency installation or paid model call was needed for baseline QA.

## Fresh verification

| Check | Actual result |
| --- | --- |
| Python `pytest market_agent/tests -q -p no:cacheprovider` | 117 passed |
| Python `pip check` | No broken requirements |
| Six controlled CLI scenarios | 6/6 passed; valid JSON stdout; empty stderr |
| `NODE_OPTIONS=--no-experimental-webstorage npm test -- --run` | 190 passed across 22 files |
| `npm run build` | Passed |
| ESLint for changed TS/TSX files since `bb034ce` | Passed |
| Full `npm run lint` | Existing 9 errors and 5 warnings, in files unchanged since `bb034ce` |

The controlled scenarios cover a qualified S$80 ceiling/S$85 exposure, questions-only
authority, wrong-identity review, stale evidence, damaged-condition reassessment,
and inspected inventory with S$5 realized profit and one pending outcome. These
are fixed-clock synthetic fixtures, not live operator policy or financial results.

Active simulation mandates can be questions-only (`ceiling: null`, zero exposure).
Consumers must check actual authority, expiry and current mandate state rather than
infer price permission from an active status or a cached historical result.

## Playwright checks against the built preview

The built frontend and its backend were served on a separate loopback port. Checks:

- Market navigation and backend health rendered successfully.
- An invalid card ID displayed the validation message without a lookup.
- `base1-1` returned Alakazam, with real TCGdex provider/fetch timestamps and dated
  estimated SGD conversion. The initial browser assertion mistakenly expected
  Charizard; inspecting the actual response corrected that test expectation.
- Partial search `pika` returned 243 matches; the initial batch contained 12 cards.
- High-to-low sorting was checked numerically, with unavailable prices last.
- Selecting `cel25-5` displayed Pikachu's details and average charts.
- A 390×844 viewport had no horizontal document overflow.

Observed FX: EUR→SGD 1.4282 and USD→SGD 1.2784, dated 30 October 2026. Quotes remain
reference evidence and must not be promoted to completed Singapore sales. Browser
proof was saved locally as `mobile-market.png`; it is not a phone/network access test.

## Decision and next dependency

The operator explicitly selected **Supabase PostgreSQL with a disposable local
database for tests**. No production database connection, migration or data import
was performed. Docker, Supabase CLI and a local PostgreSQL 17 image are available.

The next task, #32, depends on shared contract #11, which remains open without a
recorded peer agreement. Sales PR #23 still contains temporary fixture contracts.
The [Market-side compatibility proposal](superpowers/specs/2026-10-31-market-shared-contract-proposal.md)
records the exact missing decisions. It does not silently choose a Sales policy
version mapping, discard identity facts or fabricate evidence.

All later Market implementation tasks depend directly or transitively on #32.
This baseline is verified; shared-contract completion and downstream implementation
must not be reported as complete merely because this branch builds.

## Independent handoff review

A fresh reviewer inspected the baseline report, compatibility proposal and focused
Market contract/session/harness/UI paths against #31/#32 and the Sales proposal.
No Critical or Important handoff blockers were found. One documentation ambiguity
was corrected: missing identity requires review; only missing condition or resale
evidence can yield questions-only authority. The reviewer did not repeat the tests
or browser checks and did not claim production readiness.

## Limits

No live model evaluation, Carousell search/contact, authenticated peer exchange,
durable ledger operation, private operations UI, migration, merge or deployment was
tested. Those remain the separately tracked tasks and acceptance gates. Existing
full-repository lint findings remain unresolved.


## Subsequent operator decision

The operator selected the documented Market contract with a fixture Sales peer.
That decision unblocked downstream simulation software work; the baseline's earlier
blocked state above is historical. See [the software verification](market-v1-software-verification.md)
for the resulting implementation, checks and remaining real integration gates.
