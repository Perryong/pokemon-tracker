# Clean idle queue polls

Operator authority: [#27 request](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6538438622).
The queue gate previously used exit 1 for both unchanged acknowledged evidence
and unfinished work. Symphony treated both as failed attempts with error backoff.

The gate contract is now:

| Exit | Meaning | Scheduler behavior |
| --- | --- | --- |
| 0 | New evidence, durable pending snapshot saved | Start the bounded model cycle |
| 75 | Fresh evidence equals acknowledged snapshot | Clean idle; reconsider on normal polling |
| 1 | Existing pending cycle | Block; retain recovery evidence |
| 2 | API, scope, state, lock or other gate error | Fail closed |

`hooks.before_run_idle_exit_code: 75` explicitly opts the personal workflow into
the reviewed upstream patch in `patches/queue-idle.patch`. Without opt-in, exit
75 remains a hook failure. The setting applies only to before_run, never to
after_create or another hook. Idle skips Codex and after_run. Symphony releases
only its in-memory dispatch reservation, without completing the issue or
changing GitHub ownership, then reconsiders it on its existing poll schedule.
The dashboard uses its existing no-active-work waiting display. This adds no
second scheduler, expiry, automatic recovery or acknowledgement.

## Host validation and installation

Keep repository execution outside the credentialed coordinator and children.
The gateway applies the patch to a separate source copy matching the recorded
base hashes; `git apply --check` must pass before applying it. Do not patch an
unknown upstream revision by ignoring failed hunks. Preserve the original source
and image, pending gate and work volume. The patch adds no dependencies.

Use the prepared credential-free offline Elixir container with the existing
reviewed dependency cache, private PID namespace, no auth/coordinator mounts or
Docker socket, and 2 CPU/3 GiB. Serialize it with the existing Python check
container. Run the test-only patch first to establish the expected failure, then
apply the implementation and run:

```sh
MIX_ENV=test HEX_OFFLINE=1 mix test test/symphony_elixir/queue_idle_test.exs
MIX_ENV=test HEX_OFFLINE=1 mix test
mix format --check-formatted lib/symphony_elixir/config/schema.ex \
  lib/symphony_elixir/workspace.ex lib/symphony_elixir/agent_runner.ex \
  lib/symphony_elixir/orchestrator.ex test/symphony_elixir/queue_idle_test.exs
```

Do not fetch dependencies during offline checks. Record actual commands, failures,
source/patch hashes, immutable image identity and cleanup. The fixed native
`coordinator` suite checks the exact tracker commit's Python tests and claim
tests; it does not compile or test the upstream Elixir patch.

After source checks pass and the current bounded cycle returns, the gateway can
build the reviewed replacement runtime in the isolated host boundary and reload
the same registration. Install the gate and rendered workflow together with the
patched runtime. An old runtime still treats exit 75 as failure; do not claim
activation from source tests alone. Preserve all mounts, budgets, the one-primary
and three-child limit, restart policy and pending evidence. A restart cannot
clear pending or authorize recovery.

Runtime acceptance must observe unchanged acknowledged evidence returning to
waiting without a model session, warning or error retry; a later relevant change
must wake the same control issue on normal polling. Pending state, API failure,
default/unrelated hooks and cleanup remain negative checks. Verify real dashboard
and log behavior. Acknowledge only after the live timeline and all writes are
reconciled. Source or test artifacts alone do not establish runtime activation.
