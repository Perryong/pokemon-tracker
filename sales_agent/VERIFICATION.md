# Issue #9 trial report — 2026-10-29

## Identity and ownership

- Issue: https://github.com/Perryong/pokemon-tracker/issues/9
- Accountable contributor: ChouBokYann
- Session: `symphony-sales-9-20261029-a1`
- Base / unchanged HEAD: `1141231bbf74f8ce6384ac50a57acafec5cdd976`
- Branch: `sales-agent/issue-9-symphony`
- Coordinator release/acceptance independently verified:
  https://github.com/Perryong/pokemon-tracker/issues/9#issuecomment-6501036508
- Read all 16 timeline events; no competing ownership or linked implementation PR.
  Assignment is ChouBokYann; Project Active filter is In progress and #9 matches.
  Project Blocked view and both repositories' open issues were checked for overlap.
  Native blocked-by endpoint returned HTTP 200 with an empty list, including the
  final recheck; timeline still had 16 events at final recheck.
- `gh` has no configured CLI login in this container. The supported Symphony
  `github_api` tool successfully supplied REST evidence and Project GraphQL data.
  No credentials were inspected/exported. No remote writes were made.

## Changed files

New package:

- `sales_agent/pyproject.toml`, `requirements.lock`, `.gitignore`
- `sales_agent/src/pokemon_sales/__init__.py`, `contracts.py`, `session.py`,
  `harness.py`, `controlled.py`, `__main__.py`
- `sales_agent/src/pokemon_sales/fixtures/qualified_lead.json`
- `sales_agent/tests/conftest.py`, `test_policy.py`, `test_harness.py`
- `sales_agent/README.md`, `VERIFICATION.md`

New design and plan:
`docs/superpowers/specs/2026-10-29-sales-slice-design.md` and
`docs/superpowers/plans/2026-10-29-sales-slice.md`.

The pre-existing uncommitted `AGENTS.md` change was preserved without edits.
No frontend, shared workflow or colleague implementation files changed. No commit,
push, PR, merge, ownership release or Project/issue mutation was performed.

## Acceptance evidence

| Requirement | Evidence |
| --- | --- |
| Actual Deep Agents harness | `create_deep_agent` graph executes real registered sales tools; controlled model only returns AIMessage requests |
| Validated lead and mandate | Frozen Pydantic schemas; matching lead/thread/currency, exact printing, condition/evidence, aware expiry, strict money/limits and versions |
| Allowlisted capability | Three sales tools visible; dispatch guard rejects forged execute/read/write/task/accept calls and extra message arguments |
| Deterministic authorization | Price, questions-only, scope, current versions, expiry, contact rounds, opt-out and reassessment enforced in session service |
| No commitment or ceiling leak | Template-only outbound enquiries/conditional prices; no accept/payment/meetup tool; model prose discarded |
| Operator proposal | Exact local structured terms, IDs/evidence/versions/expiry; `awaiting_operator_approval`, `dispatchable: false`; unresolved logistics explicit |
| Material facts | Structured fixture-labelled reassessment and pricing pause; unclassified text fails closed; no Market implementation |
| Hostile input and isolation | Real-graph tests exercise injection, forged generic tools, extra arguments, serial batch opt-out, separate session graphs and late expiry |
| Honest simulation | CLI JSON reports scripted transport, simulated marketplace and fixed demo clock; no live-model claim |

## Actual commands and results

The test interpreter is `/tmp/issue9-venv/bin/python` (Python 3.13.5).

1. Setup: `/opt/agent-tools/bin/python -m venv /tmp/issue9-venv`, followed by
   `/tmp/issue9-venv/bin/pip install deepagents==0.7.32 pytest==8.4.2`: **PASS**.
   Official customization docs and PyPI release metadata were checked first.
   Resolved dependencies are pinned in `requirements.lock`; `pip check`: **PASS**,
   `No broken requirements found`.
2. Policy tests were written before implementation. Initial run: **RED**, 31
   missing-module setup errors. After policy implementation: **31 passed**.
3. Harness tests were written before implementation. Initial missing-module
   error was followed by an empty adapter to verify behavioral failures:
   **RED, 9 failed** (no tool effects/proposal). Real harness implementation:
   **40 passed** across both suites.
4. Review found unclassified replies and text-only opt-out gaps. Added tests
   failed behaviorally: **2 failed, 32 passed** in policy suite; fixes brought
   combined suite to **43 passed**.
5. Added late-expiry, extra-argument and opt-out reassessment checks. Opt-out
   reassessment test failed behaviorally: **1 failed, 45 passed**. Fixed it.
6. Final focused command, from `sales_agent/`:
   `/tmp/issue9-venv/bin/python -m pytest -q`: **46 passed**.
7. `/tmp/issue9-venv/bin/pip install --no-deps -e sales_agent`: **PASS**.
8. `/tmp/issue9-venv/bin/pip wheel --no-deps ./sales_agent --wheel-dir /tmp/issue9-wheels`:
   **PASS**. Inspected wheel: six Python modules plus packaged JSON fixture;
   no graph, test/cache data or credentials. An earlier command omitted `./`
   and downloaded the unrelated `sales_agent` PyPI wheel into `/tmp`; it was
   never installed or used. The corrected local build above is the evidence.
9. `git diff --check` and per-new-file `git diff --no-index --check /dev/null FILE`:
   **PASS**. Frontend checks were not run because frontend files did not change.

Each demo command below ran from `sales_agent/` with
`/tmp/issue9-venv/bin/python -m pokemon_sales --scenario SCENARIO` and exited **0**:

| SCENARIO | Outbound | Root proposal | Tool results |
| --- | ---: | --- | --- |
| eligible | 2 | SGD 4500 cents awaiting approval | sent, sent, awaiting_operator_approval |
| out-of-policy | 1 | None | sent, price_out_of_mandate, price_out_of_mandate |
| expired | 0 | None | expired_mandate × 3 |
| opt-out | 1 | None | sent, seller_opt_out, seller_opt_out; no reassessment |
| material-facts | 1 | None | sent, reassessment_required × 2; structured reassessment |

The worker wrote synthetic demo JSON and red/green logs under `/tmp` during
execution. The temporary worker container was subsequently removed; those `/tmp`
files are not retained artifacts. The coordinator preserved the source checkout
and local session transcript, and independently regenerated all five demo results.
`tool_results` are historical tool responses; only the root `proposal` is the
final revalidated artifact, and no artifact authorizes dispatch.

## Skills, review, rulings and usage

Used mounted Superpowers instructions for design, planning, TDD, inline execution
and verification. The operator explicitly authorized module/test choices and
single-worker execution, so no additional approval, automatic specialist dispatch
or commit/publish workflow was introduced. The supervising interactive agent
performs independent review after collecting this local diff; author self-review
is not represented as independent review.

Worker choices: integer SGD cents and Python 3.13; three template-only tools;
model-call allowlist plus dispatch denial rather than removing required Deep Agents
scaffolding; conservative reassessment of unclassified text; local non-dispatchable
proposal with unresolved delivery/logistics. These choices limit this slice and
require revisiting the fixture contract during integration. No deferred minor
code findings were identified in the self-review.

Graphify ran only on bounded source paths, never dependencies or credentials:
`/opt/agent-tools/bin/graphify update src --no-cluster` produced 438 nodes/1074
edges; its output was moved to `/tmp/issue9-frontend-graph` to keep frontend clean.
A broad query found no matching nodes. Focused sales extraction:
`graphify update sales_agent/src/pokemon_sales --no-cluster` produced 62 nodes/100
edges; `graphify query SalesSession --graph .../graph.json --budget 500` succeeded.
The local ignored graph lives under `sales_agent/src/pokemon_sales/graphify-out`.
Graphify reported a pre-#1504 node-ID compatibility note; this graph is supporting
code memory, not acceptance evidence. No comparative performance claim is made.

No subagent was invoked. Delegation count/time/cost: 0; total model token/cost
usage is unavailable. No other orchestrator or independent worker was launched.

## Simulation, limits and remaining work

Real: Deep Agents/LangChain/LangGraph tool execution, validation and policy service.
Simulated: model responses, seller exchange, qualified-lead/reassessment boundary
and fixed demo clock. Live model, marketplace and authenticated A2A: **not run**.

No implementation blocker remains for the isolated software slice. Supervisor
review is outstanding; the issue remains open and owned by this session. All
state is ephemeral. Durable suppression/counters/recovery, authenticated contracts,
Market integration, complete exact approvals/budget holds, live connector access
and operational evidence remain follow-ups under #8. Fixture annotations are
trusted test inputs, not real seller classification. No production-readiness,
live-access or full-V1 completion claim is made.


## Independent coordinator verification

After the worker stopped, the coordinator preserved its Git checkout and reviewed
the schemas, session policy, real harness adapter, controlled model, tests and
documentation. No blocking code finding or product-code rework was identified.

A fresh Python 3.13 virtual environment in a separate container installed
`requirements.lock` and the local editable package. `pip check` passed;
`python -m pytest -q -p no:cacheprovider` passed **46 tests**. All five CLI
scenarios exited zero. The coordinator parsed the regenerated JSON and checked
outbound counts (2/1/0/1/1), the eligible 4500-cent non-dispatchable proposal,
absence of proposals in the four denial/reassessment cases, opt-out without
reassessment, and replacement-mandate requirement for material facts.

The worker completed naturally in **881.281 seconds** (about 14m41s), with no
subagent delegation. Symphony reported 3,353,709 cumulative tokens (3,327,902 input,
25,807 output); these are reported counters, not billed usage or dollar cost, and
cached-token accounting was not established. There is no controlled baseline and
no efficacy claim. The routing label and credential-bearing runtime container
were removed. Review and merge are still required; issue #9 is not Done.
