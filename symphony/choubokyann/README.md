> **Current status: source-only, live startup disabled.** The PowerShell launcher,
> container entrypoint, and generated/root workflow refuse live execution before
> starting a model. Offline installation, registration and dry-run remain available.
> The restricted broker is not yet connected to the runtime; see
> [SECURITY-BROKER.md](SECURITY-BROKER.md). Earlier live-pilot instructions below
> are historical and must not be used to reactivate the old credential-bearing path.

> Current execution path: [ISOLATED-TOOL.md](ISOLATED-TOOL.md). Operator extension in #27 permits one 2 CPU/3 GiB test container alongside the 2 CPU/3 GiB coordinator, within 4 CPU/6 GiB aggregate. Earlier same-slot manual-pilot instructions below are historical and superseded; no test execution in coordinator/children.

# ChouBokYann's personal Symphony coordinator

For machine installation, registration and the shared agent cap, see [MACHINE.md](MACHINE.md).

This setup schedules only the ongoing [control issue #27](https://github.com/Perryong/pokemon-tracker/issues/27).
Symphony owns dispatch/retry timing; the model performs one bounded coordination
cycle and returns. No additional scheduler or dependency is introduced. Product
work opts in with `symphony-choubokyann-queue` in public
`Perryong/pokemon-tracker` and the existing
[Project](https://github.com/users/ChouBokYann/projects/1). Labels are evaluation
scope, never ownership or readiness authority. Market #24/#26 are excluded.

## Repository execution boundary — pilot pending

Never execute repository-controlled code in the coordinator or native children.
The coordinator remains a credential-bearing trusted control plane. It may inspect
source and use reviewed installed GitHub/gate tools; a repository test, installer,
hook, build or demo must run only in the separate offline check lifetime described
in [ISOLATION-PILOT.md](ISOLATION-PILOT.md). The host gateway stops the coordinator
and reuses the one fixed container slot, with no auth mounts or credentials, then
returns exact-head evidence. No Docker socket is exposed to agents or tests.

The pilot artifacts are source-reviewed candidates, **not verified isolation**.
Do not resolve the P1 or resume product execution until the actual sentinel,
negative-control and required offline workflow checks pass. Keep pending evidence
and use deliberate recovery after the host handoff. The agent/test separation is
not achieved by removing an environment variable; the host must verify the entire
container boundary and its image. This does not remove credentials from the
trusted agent itself or establish resistance to malicious agent instructions.

## Activation on the operator host

Use [MACHINE.md](MACHINE.md) for the exact persistent installation, registration,
offline two-project validation, start, visible Elixir terminal, logs and stop
commands. Only Pokemon is seeded; a different explicitly registered public repo
and user-owned Project use the same runtime without source changes. The runtime
is installed under `$HOME/.symphony/choubokyann/runtime`, separately from each
project seed/workspace. This bootstrap makes no GitHub writes or live activation.

The gateway executes host commands and relays results; the in-Symphony coordinator
retains coordination decisions. Confirm the existing #27 session/branch and full
ownership timeline before activation. Keep #27 open and In progress; apply the
unique coordinator label to it only. Product opt-in is deliberate and does not
establish readiness. Preserve/stop the bootstrap before starting another instance.

Live start now refuses before credential lookup, Docker access, mounts or model
startup. `-DryRun` still validates and renders a registration without starting any
service. Stop and log commands remain available for reconciling older installations.
A source update does not stop or upgrade an already-running host container.

## Model settings and actual evidence

The TOML files retain the intended model configuration for future broker integration.
No model is launched by the current entrypoints. Historical startup evidence below
is not evidence that this source-only revision is operational.

The base selects Astra/high and at most three Sol/high children (four development
agents total; the primary is excluded from
`agents.max_concurrent_threads_per_session`). Native spawn explicitly selects
Sol/high with `fork_turns=none`. `worker.toml` versions the standalone worker base
and disables delegation when loaded independently. It is not automatically
loaded by this harness's native child. Depth one, allowed files/actions, no
recursive delegation and scoped child GitHub-action rules are instruction policy;
do not invent a supported depth config key or claim separate credential isolation.
See the official [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
for current keys and [subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents).

Check actual `turn_context` model/effort metadata for both parent and child.
The bootstrap verified Astra/high and Sol/high in separate session transcripts;
see VERIFICATION.md. Cache availability and a TOML declaration alone are not
proof. After a cap/configuration reload, verify actual loaded limits and parent/child
model metadata before claiming activation. Use fewer children when tasks are not
independent; require disjoint file ownership and parent-serialized integration,
GitHub decisions and isolated checks. If the model/tool is unavailable, report it
without silent substitution.

The credential-bearing launcher has been removed. The new launcher never looks up
or copies a GitHub credential. Do not restore the former shared-token startup:
the trusted broker must keep credentials outside all model-accessible processes,
mounts and tools before a reviewed live path can be enabled.

## Queue gate and recovery

The standard-library gate runs in `before_run`, before any paid model turn.
`SYMPHONY_REGISTRY=/config/projects.json` and `SYMPHONY_PROJECT` select the same
validated record used to render the workflow. Manual gate commands inherit these
environment names in the container, or require explicit `--registry`/`--project`.
The scope fingerprint binds persisted state to the registration. A different
registration, or legacy unbound state, fails closed even on retry: preserve the
file and reconcile deliberately, never delete pending evidence to obtain dispatch.
It checks the authenticated actor, canonical public repo, unique control label,
the selected control assignment and Project status, product opt-in, exclusions and Project
membership. It fingerprints canonical queued issues, dependencies and linked PR
heads/checks/reviews/threads plus relevant open PRs and statuses. It filters
private/other-repo Project data before persistence. It stores only safe IDs,
digests and recovery reasons. It does not decide claim validity, resolve business
requirements, interpret readiness, or authorize implementation.
Closed labelled product issues remain visible for acceptance/disposition review;
they are not implementation candidates. Only open Ready work may start. Remove
the queue label deliberately after reconciled disposition to keep the bounded
inventory small; this bootstrap performs no such writes.

Connections are explicitly bounded to 100 entries and fail closed on truncation
instead of silently using partial evidence. Read calls have a 20-second timeout
and each snapshot has a 100-second budget. The head commit connection deliberately
selects the latest commit only. Larger queues/timelines require a reviewed paging
change, not raising limits blindly. Errors, missing data and empty scope block
dispatch. Symphony may log/retry a genuinely failed hook with backoff; no paid
model runs occur while unchanged evidence or pending work blocks dispatch.

`check` returns 0 only for new evidence and atomically saves a pending record
under `<workspace>/.symphony/choubokyann/queue-gate.json`. A freshly read snapshot
matching the acknowledged fingerprint returns 75 without changing state. The
personal workflow opts into `hooks.before_run_idle_exit_code: 75` through the
reviewed [Symphony runtime patch](QUEUE-IDLE.md). That outcome starts no model,
runs no after_run hook, and returns to ordinary polling without a failure retry
or completion record. Changed evidence on a later poll starts a new cycle.
Pending work returns 1 and blocks all automatic redispatch, including after new
evidence; it has no expiry. Read, scope, lock and state errors return 2. These
remain failures, as do nonzero results from other hooks or workflows that have
not opted in. A local file lock serializes gate state writes. There is deliberately
**no after_run acknowledgement**; only the coordinator may reconcile fresh evidence.

At successful cycle end, finish and read back all GitHub writes. Use `inspect`
to obtain a fresh safe snapshot, reconcile its state with live GitHub, then
acknowledge the exact fingerprint. A change between inspection and acknowledgement
fails closed and leaves pending evidence. The fresh end snapshot absorbs the
coordinator's own comments/status updates so they do not cause endless self-churn.

```sh
python3 /runtime/queue_gate.py inspect --workspace "$PWD"
python3 /runtime/queue_gate.py acknowledge --workspace "$PWD" \
  --expected-fingerprint THE_INSPECTED_SHA256
```

Snapshots and the local workpad are evidence, never authority. Reread full live
ownership and dependencies before every mutation. Keep concise decisions,
branches/heads, check results, ownership/session, issue/PR links, uncertain writes,
next action and blockers in `workpad.md`; append material public-safe progress to
issue/PR timelines. Do not persist private source payloads or credentials.

After interruption or uncertain writes, stop the worker first, preserve its diff,
branch and workpad, and inspect the live timeline/checks. Never blindly repeat a
claim/comment. Once the coordinator has reconciled outcomes and confirmed no
outgoing writes remain, deliberately run the following in the preserved workspace
using the image's Python (for example an explicit `docker exec` on the stopped-work
coordinator container after it has been safely restarted). Do not remove state:

```sh
python3 /runtime/queue_gate.py retry --workspace "$PWD" \
  --reason 'Coordinator reconciled timeline and stopped outgoing work; evidence: public URL'
```

Retry archives pending evidence and the reason; the next `check` still rereads
scope and state. It grants no ownership. Starting a new container never retries
implicitly. If a state file is corrupt, preserve it and have the coordinator
reconcile; do not delete it to obtain a green gate.

## Review, ownership and completion

Only Ready issues with complete requirements and satisfied native/body
dependencies can begin. In review work is reviewed at the exact PR SHA, with
actual diff/test/check/review evidence. Recheck that SHA before recording results.
Failing reviews receive a bounded worker task only under an already valid claim
or an explicit delegated transfer. Preserve the original owner when using a tool
child; a child is not an independently scheduled issue owner. If this coordinator
would become a new owner, its supervisor must approve that incoming session;
it cannot approve itself. This intentionally blocks unattended self-claims.

Never take a colleague claim, infer abandonment from timeout, or implement
dependent work before prerequisite acceptance. New material requirements require
operator decision. Passing review remains In review pending a separate integration
decision. The operator's [scoped authority](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6539304288)
permits the Astra coordinator to accept and merge eligible Sales/UI and personal
orchestration PRs only in public `Perryong/pokemon-tracker`, only into
`feature/sales-agent`. New issue branches start from that integration branch;
preserve existing work; the seeded control registration now uses `feature/sales-agent`
so the merged PR branch can be deleted. This does not extend to another registration, `main` or colleague
branches. Outside that exact authority, human merge remains required.

Immediately before merging, verify live authority, repository/base/head, ownership,
full prerequisites, actual diff, isolated checks and independent findings. Blocking
findings prevent merge; a moved head/base requires scoped revalidation. Use an
exact-head merge guard and ordinary protections, never force push, bypass checks
or enable auto-merge. Read back uncertain writes before retrying. Verify the
resulting integration revision and required checks, then record business acceptance
and any claim release separately. A merge is not a Done transition or permission
for dependent work, deployment or marketplace action. Same-account reviewer
returns are independent evidence, not fabricated GitHub approvals. #27 remains
open/In progress. An explicit no-merge instruction in the active turn still blocks
merging until reconciled; installing this prose does not override that turn.

## Bounded reviewer and selected backlog intake

The operator extension in [#27](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6539152475)
adds two explicit tool tasks: readiness review of selected Sales/UI backlog, and
acceptance review of In review/returned work at the exact current PR head. Invoke
an independent native `gpt-6-astra`/high child with a clean context, read-only
public evidence and immutable source, task ID, file/tool scope and time/turn
budget, under the [model clarification](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6539174541). At most one Astra reviewer replaces one Sol worker slot: one Astra coordinator plus reviewer plus at most two Sol workers, four agents total. Without a reviewer, up to three Sol workers remain allowed. The implementation default stays Sol/high. This exception supersedes the earlier Sol-only child description. It consumes one existing child slot; Astra retains issue ownership and
all decisions. No persistent reviewer, recursive delegation or additional scheduler.

Reviewers cannot execute repository code, submit checks, change status/ownership,
merge or take live actions. Under the scoped authority above, an Astra reviewer
may create/update a scoped PR only when explicitly assigned that operation, then
return its URL/base/exact head and evidence. All other GitHub access remains
read-only; Sol children cannot write GitHub. Astra serializes PR writes and isolated checks and
independently verifies the returned verdict, source and live head. Require status,
ready/blocked or pass/changes-needed verdict, evidence/head, blocker owner/action,
checks and uncertainty. Inaccessible, failed or incomplete reviews fail closed;
a changed head or base invalidates acceptance. Preserve the original product owner
for any fix. Passing work remains In review until separately authorized integration,
with business acceptance still separate.

Use existing gate/workpad evidence digests to avoid another reviewer when its
issue/dependency/ownership inputs or head/base/check/review evidence are unchanged.
Record the prior verdict and rationale; another issue's change alone is no reason
to repeat it. The cache grants neither readiness nor ownership.

For Pokemon, the recorded initial intake is #8, #9 and #11–#21 only. Audit full
ownership/scope before adding the existing queue label. Leave colleague Market
#24/#26/#31–#41, unrelated issues and private repositories outside intake. Labels
permit evaluation, not coding. Record actual blockers and responsible next
decisions; promote only after verified prerequisite and non-code resolution.
Avoid duplicate comments and same-status writes. Other registrations require
their own recorded scope and selected list; do not copy these issue numbers.

Validation uses the existing isolated coordinator suite for rendering/scope
regressions plus actual returned readiness/acceptance trials, model metadata and
parent decisions. Prose declarations alone do not prove reviewer activation.
Install the reviewed template/docs through the existing gateway path and reload
only after the bounded cycle returns, preserving pending evidence and budgets.

## Local checks

Run these only in the isolated host check boundary (Python 3.13), never in
the coordinator. The gate uses the standard-library POSIX file lock. Review
PowerShell harness source before the host pilot; record actual host results.

```sh
python3 -m unittest discover -s symphony/choubokyann -p 'test_*.py'
python3 -m unittest discover -s .github/scripts -p test_issue_claim.py
sh -n symphony/choubokyann/entrypoint.sh
git diff --check
```

Use a temporary Codex home to validate each TOML as a **base config**, never as a
named profile. No live model call is needed for startup validation. Local fixture
tests and contract checks do not prove Docker/PowerShell launch behavior. The
operator pilot must test startup, localhost publication, unchanged/changed queue,
pending failure/retry and stop/removal with the preserved volume before unattended
activation. See VERIFICATION.md for actual results and remaining limitations.
