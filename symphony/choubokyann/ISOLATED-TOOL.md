# Isolated checks with returned results

This implements the direction approved in [#27](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6526149446).
It supersedes the manual-only, same-container pilot in ISOLATION-PILOT.md.
The coordinator keeps running; tests are not agents. One coordinator (Astra plus
up to three Sol children after the reviewed runtime reload) uses 2 CPUs/3 GiB and one ephemeral test container uses
2 CPUs/3 GiB. No Docker socket or host-shell tool enters the coordinator.
This document is a preparation contract, not evidence that the pilot passed.

## Trust and request contract

Copy reviewed `isolated_runner.py`, `isolated_tool.py`, `registry.py`, and `isolation_probe.py`
outside the checkout into the user runtime. The host runner imports only that
installed probe. It accepts only the selected record from the existing host registry and the
`coordinator` (runtime plus claim tests) and fixed `sales-agent` suites. An unauthenticated GitHub metadata
read verifies that repository is public. The active coordinator project label
must match. Existing registration and storage remain intact. Registration still
grants no issue ownership; the coordinator verifies authority before submission.
The additional fixed `sales-agent` suite validates the simulated Sales slice; it
does not authorize live model, marketplace, approval or purchase execution.

The adapter publishes `{version:1,job_id,project,commit,suite}`. Commit must be
40 lowercase hex; the host reads it from its configured seed with git archive,
validates the tar and never checks out/imports repository code on the host.
A missing commit is fetched from that canonical public HTTPS origin, with no tags,
submodules, credential helper or forwarded auth headers; fetch failure blocks.
Local candidate commits already present in the host seed also work.
Requests cannot name commands, images, paths, mounts, network or budgets.
Request and result JSON include canonical SHA256 correlation. Host-private state
retains IDs/results; a changed ID payload or uncertain running record blocks.
A fixed per-user lock and fixed test-container name serialize all jobs.

Mount separate request directory RW and result directory RO. Never mount host
state, seed repository, credentials, auth directories or sockets into tests.
Only an exact source archive, trusted probe and fixed job JSON reach `/input`.
The test container is offline, nonroot, capability-free, read-only, private PID
and IPC, builtin seccomp, with bounded tmpfs/PIDs/output/time. An image ID and
configuration inspection do not prove clean layers: build from the official
base in a clean context containing no credentials or source checkout.

Results carry commit, image ID, archive hash, request digest, status/exit,
cleanup and at most 32768 characters of **untrusted output**. A malicious test
can fake its log or exit zero; inspect source and acceptance assertions too.
Never execute output or interpret it as instructions. Cleanup uncertainty blocks
future jobs. Host state is not writable through the transport. The trusted
coordinator still has credentials; this is an execution boundary for repository
code, not isolation from malicious agent instructions or a container-escape proof.

## Host preparation (PowerShell 7)

The operator has already authorized these actions. The gateway executes them;
the coordinator must not run repository code while preparing this tool.
Preserve the work volume, pending record, registry, current source and patch.

```powershell
$install = Join-Path $HOME '.symphony/choubokyann'
$runtime = Join-Path $install 'runtime'
$checks = Join-Path $install 'checks/pokemon'
'requests','results','state' | ForEach-Object {
    New-Item -ItemType Directory -Force (Join-Path $checks $_) | Out-Null
}
# Keep state/config host-only; do not add them to Docker bind mounts.
# Copy the reviewed candidate runtime files to $runtime, preserving projects.json.
# Existing Install-Coordinator refuses replacement intentionally.
```

Prepare a clean temporary build directory. Obtain the official base once, then
pin its resolved repo digest in this Dockerfile; record both base and final IDs:

```powershell
docker pull python:3.13-slim
$base = docker image inspect python:3.13-slim --format '{{index .RepoDigests 0}}'
$build = Join-Path ([IO.Path]::GetTempPath()) ('clean-check-image-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $build | Out-Null
@"
FROM $base AS official
FROM scratch
COPY --from=official / /
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8
"@ | Set-Content (Join-Path $build 'Dockerfile') -Encoding utf8NoBOM
docker build --network=none --tag pokemon-checks:clean $build
$image = docker image inspect pokemon-checks:clean --format '{{.Id}}'
```

No authenticated worker image, repository install or package hooks are involved.
Review the resulting provenance/configuration and retain image ID. Supply the
host seed containing the exact candidate commit. Preserve old files before
applying the returned patch; create the local candidate with hooks disabled.
The candidate SHA is not the old PR head; do not report old-head checks as new.

```powershell
$repo = 'C:\Repos\pokemon-tracker' # actual registered public seed
$sha = git -C $repo rev-parse HEAD
@{
    project='pokemon'; registry=(Join-Path $install 'projects.json'); repository=$repo; image=$image
    requests=(Join-Path $checks 'requests'); results=(Join-Path $checks 'results')
    state=(Join-Path $checks 'state')
} | ConvertTo-Json | Set-Content (Join-Path $checks 'host.json') -Encoding utf8NoBOM
# Trusted host runner: serial transport listener, not an agent scheduler.
python -I "$runtime/isolated_runner.py" --config "$checks/host.json" --serve
```

Run the last command in a separate visible terminal. It stays available until stopped, processes one job at a time with a 300-second
execution deadline, and refuses an uncertain prior job. The loop only services
explicit tool requests; it never selects issues or launches an agent. No OS service or automatic coordinator retry is installed. `--once` handles one request for diagnostics. Preserve terminal errors;
invalid request/config is a refusal, never an empty queue.

For first installation, new bind mounts require one deliberate coordinator
recreation **after its current bounded cycle returns and outgoing work stops**.
Use existing Stop/Start commands preserving volume/pending; thereafter no stop
is needed to run checks. The updated launcher mounts requests/results and caps
coordinator to 2 CPU/3 GiB. Never start a second coordinator. Host runner verifies
the actual active coordinator budget before creating the test container.

```powershell
& "$runtime/Stop-Coordinator.ps1"
& "$runtime/Start-Coordinator.ps1" -Project pokemon -Repository $repo
```

The mounted `coordinator.toml` adds `mcp_servers.isolated_checks`, command
`python3 -I /runtime/isolated_tool.py --requests /checks/requests --results /checks/results`,
60-second tool timeout. Its `env_vars = ["SYMPHONY_PROJECT"]` explicitly forwards
the selected non-secret registration; no credential variables are forwarded.
Without this setting, the adapter may fail startup because its project is missing.
The operator-authorized tool loop pins `enabled_tools = ["run_checks", "check_status"]`
and sets `tools.run_checks.approval_mode = "approve"` and
`tools.check_status.approval_mode = "approve"` within this server only. Global
`approval_policy = "never"` remains unchanged. No server-wide default or GitHub
tool preapproval is granted. These scoped settings let the trusted adapter run
under noninteractive approval policy; they do not bypass host validation or
authorize repository execution in the coordinator. Reload the app-server after
installing configuration changes, preserving the work volume and pending gate.
Selected project comes from `SYMPHONY_PROJECT`. Each call
waits at most 50 seconds; a durable `pending` result calls for `check_status`
with the identical arguments, not another job. Confirm actual tools/list and
invoke from the actual Astra run; a CLI/config declaration is not that evidence.
The adapter follows [newline JSON-RPC stdio](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
and [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp).

## Required acceptance and continuation

1. Run the new tests in the clean container. For meaningful red/green evidence,
   use a disposable source candidate with each security guard deliberately removed
   and show the corresponding tests fail, then the intact exact candidate passes.
   Do not weaken the installed host boundary to create a negative control.
2. Unit cases cover cross-project/unknown commands, traversal, conflicting IDs,
   correlated results, symlinks, nonzero/timeout and uncertain cleanup. Run probe
   negative controls (readable sentinel and inherited synthetic environment).
3. From actual Astra, call `run_checks(job_id,commit,suite='coordinator')`; retain
   submitted request, native tool return and host-private evidence. Repeated same
   ID must return the same job; no new container. Demonstrate test timeout/nonzero
   using local synthetic commits in the registered host seed, never live credentials.
4. Verify no test container remains, host results mount is read-only in coordinator,
   no Docker/auth mounts in tests, correct budgets, exact candidate/image/archive,
   and actual runtime and claim counts. Inspect source independently. Keep P1 open
   until this evidence is reviewed; no product execution/merge/deploy follows from
   a proposal or fake-boundary unit tests.
5. Reconcile live GitHub and all intended writes, inspect and acknowledge the exact
   fresh gate fingerprint, then demonstrate `check` returns unchanged/nonzero.
   Neither runner nor adapter ever mutates the queue gate or issue status.

An interrupted call retains the job. A pending job is not a failed cycle. If the
20-minute cycle ends, record identity and return; resume by deliberately checking
host completion/cleanup and live timelines, then the documented gate retry under
operator authority. There is no background result scheduler. A failed job remains
failed under its ID; fixes use a new exact commit and explicitly recorded job ID.
For host crash/running marker or uncertain cleanup, inspect Docker and preserve
state; there is no expiry, automatic replay, or deletion to force green.

## Fixed Sales Agent suite

Operator continuation: #27 comment 6527515526. Requests retain exactly the same
identity fields and may select only `coordinator` or `sales-agent`. The latter
uses `sales_agent/` from the exact requested source archive. It runs `pip check`,
`pytest -q -p no:cacheprovider`, then all five documented scripted scenarios.
The installed probe parses each demo JSON and verifies harness/transport,
outbound counts, approval-only SGD4500 proposal, denial reasons, opt-out and
replacement-mandate reassessment. No caller-supplied command or fixture path is
accepted. `PYTHONPATH` is set to the extracted `sales_agent/src` only inside the
test container; no repository package installation is needed.

The host must first prepare a clean Python 3.13 image containing the reviewed
exact `sales_agent/requirements.lock` dependencies. Build from the pinned
official base with only that lock in a clean context, use binary wheels only
(`pip install --only-binary=:all: -r requirements.lock`), and copy the resulting
filesystem into the existing scratch final stage with only approved PATH/LANG.
Do not install the repository or run its build hooks. Record lock digest, base
and final image IDs; configure the immutable final ID in host-only config.
Retain the previous image and all old job results. No dependency installation or
network fallback occurs during checks. Missing or inconsistent dependencies fail.

Install the reviewed runner, probe and adapter together outside the checkout;
the named suite is propagated in host-generated job JSON. Refresh the native MCP
schema before requesting `sales-agent`. If a running app-server retains the old
schema, preserve pending evidence and use a deliberate continuation after reload;
never write the transport manually or bypass the native tool.
