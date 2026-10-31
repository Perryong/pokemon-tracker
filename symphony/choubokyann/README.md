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

Start refuses an existing named container and never discards pending evidence.
The selected seed's origin and branch must match its registration. A new workspace
clones the seed's committed branch; uncommitted product files are not copied.
Existing workspaces remain intact. Stop checks the owner and removes the credential
container while preserving the selected volume. All projects share one fixed
container slot and resource/model cap, with isolated volumes. The launcher uses
`unless-stopped`: Docker may restart the existing container after an unexpected
exit or daemon restart, while a deliberate stop remains stopped. Docker and the
trusted host check runner must themselves be available; this launcher installs no
login task. Restart never clears pending gate evidence or retries interrupted work.
See [Docker restart policy semantics](https://docs.docker.com/engine/containers/start-containers-automatically/).

## Model settings and actual evidence

`coordinator.toml` is mounted as `/root/.codex/config.toml`. The command is
`codex app-server`; installed CLI 0.165.0 rejects `--profile`/`-p` for this
subcommand. The entrypoint runs `codex app-server --strict-config
--print-startup-config` with a 30-second timeout before Symphony dispatch.
Startup validation verifies supported configuration, **not applied model usage**.

The base selects Astra/high and at most three Sol/high children (four development
agents total; the primary is excluded from
`agents.max_concurrent_threads_per_session`). Native spawn explicitly selects
Sol/high with `fork_turns=none`. `worker.toml` versions the standalone worker base
and disables delegation when loaded independently. It is not automatically
loaded by this harness's native child. Depth one, allowed files/actions, no
recursive delegation and child no-write-to-GitHub rules are instruction policy;
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

The token is read from existing `GH_TOKEN` or `gh auth token` into process memory,
passed to Docker with `--env NAME` (no value in argv), and restored in the host
shell afterward. No token file/config/log is written. Docker necessarily retains
container environment until removal; avoid environment dumps. Codex auth is
mounted read-only. Symphony removes tracker secret environment names before
app-server launch. `SYMPHONY_QUEUE_TOKEN` intentionally carries the same approved
credential to the gate's gh subprocess for end-of-cycle reads. The gate maps it
to GH_TOKEN only in that subprocess. Parent and child share filesystem and
credential access: these are policy boundaries, not a security sandbox between
agents. Use the least access the operator approves; never log API stderr/payloads.

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
operator decision. Passing review can remain In review / awaiting human merge.
No automatic merging, Done, deployment or marketplace action is authorized. A
merged PR alone is insufficient business acceptance. #27 remains ongoing.

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
