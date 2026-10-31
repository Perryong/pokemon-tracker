> Current execution path: [ISOLATED-TOOL.md](ISOLATED-TOOL.md). Operator extension in #27 permits one 2 CPU/3 GiB test container alongside the 2 CPU/3 GiB coordinator, within 4 CPU/6 GiB aggregate. Earlier same-slot manual-pilot instructions below are historical and superseded; no test execution in coordinator/children.

# Personal machine runtime

The Astra coordinator **inside Symphony** owns triage, dispatch, review and routine
handoffs. Interactive chat is the logs/issues/intake gateway: it executes these
host commands, reports results and relays operator decisions. It does not become
the approving coordinator. Registration is not claim approval, product readiness,
or permission to merge. Other repositories need their own applicable approval
policy; Pokemon's standing delegation does not extend to them.

Repository installs, tests, hooks, demos and builds are prohibited in the
credential-bearing coordinator and its children. The staged
[offline pilot](ISOLATION-PILOT.md) uses the same fixed container slot only after
the coordinator has returned its handoff and the gateway has stopped/removed it.
The check lifetime has no agents, credentials, persistent coordinator volume or
network. The gateway returns inert evidence; it does not acquire issue ownership.
The pilot remains unverified until actual host results are recorded. Do not run
these new artifacts or PR code in the active coordinator to validate them.

## Install once under the current user's profile

Required host tools: PowerShell 7, Python 3.11+, git, gh and Docker, with the
existing `pokemon-symphony:worker` image and Codex login. The image supplies
Elixir/Symphony and worker tools. No new framework, scheduler, image build,
credential file or boot service is installed. In a visible PowerShell 7 terminal,
from the reviewed checkout containing this setup:

```powershell
$source = (Get-Location).Path
$install = Join-Path $HOME '.symphony/choubokyann'
pwsh -File "$source/symphony/choubokyann/Install-Coordinator.ps1"
$runtime = Join-Path $install 'runtime'
python "$runtime/registry.py" validate --registry "$install/projects.json"
pwsh -File "$runtime/Test-Installation.ps1"
pwsh -File "$runtime/Start-Coordinator.ps1" -Project pokemon -DryRun
```

`Install-Coordinator.ps1` copies only listed runtime/config/test/docs files into
`$HOME/.symphony/choubokyann/runtime` and seeds the editable registration file at
`$HOME/.symphony/choubokyann/projects.json`. The runtime's copy of projects.json is
only a seed/test fixture; the launcher uses the installation-root registry.
Installation does not depend on a temporary/ignored worktree afterward. It refuses
an existing installation rather than overwriting registrations or an active runtime.
For an update, stop/reconcile first, preserve the installation-root registry and all
volumes, review the file diff and replace only runtime files deliberately. Do not
run the installer over an existing installation or delete it to bypass a failure.
A partial failed installation needs inspection, not automatic replacement.

Only Pokemon is seeded: `Perryong/pokemon-tracker`, user Project `ChouBokYann/1`,
control #27, its accepted session/branch, exclusions #24/#26 and Sales/UI scope.
The default volume is `symphony-choubokyann-pokemon-work`. This is a new name relative
to the earlier supervised prototype's `pokemon-symphony-choubokyann-work`; no data
is automatically migrated or deleted. Preserve the archived bootstrap workspace,
branches and pending evidence separately. Do not switch a real pending project to
a fresh volume to escape recovery; reconcile the old run and record the handoff
before the first launch under this installation.

## Explicit registration without source changes

The standard JSON file contains `version: 1` and a `projects` object keyed by a
stable lowercase ID. `registry.py register` adds exactly one validated new record;
it refuses unknown fields, duplicate repositories/IDs, unsafe names, wrong actor,
and malformed authority URLs. It writes atomically under an exclusive local lock.
It does not call GitHub, create issues/labels, enroll other projects automatically,
or start a runtime. Stop/reconcile the selected runtime before editing registration
records. Never rename/reuse an existing ID to obtain a different volume or discard
pending state. A stale `.lock` requires checking whether its writer stopped and
whether the write completed before deliberate recovery.

For an approved **new public repo and user-owned Project**, prepare its own control
issue, full timeline, applicable ownership policy, accepted distinct session,
branch and scoped labels. Verify prerequisites and preserve any outgoing handoff.
Write a UTF-8 JSON record with these exact fields (replace every example value
with that project's reviewed values; this example is not enrolled):

```json
{
  "repo": "Example/approved-project",
  "actor": "ChouBokYann",
  "project_owner": "ChouBokYann",
  "project_number": 8,
  "control_issue": 71,
  "control_label": "approved-project-control",
  "queue_label": "approved-project-queue",
  "session": "approved-project-coordinator-20261030",
  "branch": "coordination/setup",
  "excluded_issues": [],
  "scope": "The explicitly approved development workstream",
  "authority_url": "https://github.com/Example/approved-project/issues/71#issuecomment-123"
}
```

Keep public metadata only, no token/private issue text. Actor is fixed to
ChouBokYann for this personal installation; private repositories and organization
Projects are unsupported and must not be registered. The approval URL must refer
to that repository's control issue comment. Its syntax is validated locally; the
coordinator must read it and the complete live timeline to establish actual authority.

```powershell
# After actual project approval, with its completed record at this path:
python "$runtime/registry.py" register --registry "$install/projects.json" `
  --project approved-project --record "$HOME/approved-project-registration.json"
pwsh -File "$runtime/Start-Coordinator.ps1" -Project approved-project -DryRun
```

The same launcher, workflow template and gate select repository, Project, control
issue, labels, session, branch, scope and exclusions from that record. No source
edit or Pokemon issue-ID copy is necessary. The seed checkout must be a normal
clone of the selected repo on the registered branch; origin and branch are checked.
Before live activation, its committed tree must contain the reviewed repository
ownership policy, including the scoped AGENTS rules for Pokemon. Installation
does not copy uncommitted seed edits into new workspaces. This bootstrap creates
no commit; relay that prerequisite instead of implicitly committing for the operator.
Existing workspaces are never reset/recloned. Each ID has its own persistent
`symphony-choubokyann-ID-work` volume, containing `/work/coordinator`, workpads,
branches, gate evidence and logs. A scope fingerprint rejects state reuse under
another registration, including `retry`. Changing an established registration
requires explicit reconciliation; the gate deliberately does not migrate state.

## One global slot, visible terminal, start/stop/logs

One selected project runs at a time. All starts share Docker name
`symphony-choubokyann`, **2 CPUs / 3 GiB / no extra swap**, one Symphony runner,
Astra/high plus at most three Sol/high children excluding the parent (four
development agents total). One separate non-agent test container is limited to
2 CPUs / 3 GiB; the aggregate remains 4 CPUs / 6 GiB. No per-project
container override is exposed. Docker's name reservation rejects concurrent
starts even across different registry files; an existing stopped container also
blocks start. Stop deliberately before switching projects. These controls cover
supported entrypoints on one Docker daemon, not manually renamed containers,
other machines, or shared-credential agent isolation. Depth one and allowed child
actions are policy; no recursive or shell-launched agent is allowed.

After the preserved setup/handoff is reviewed, the existing bootstrap has stopped,
and the control issue's label, assignment, Project In progress and accepted session
are verified, run in the visible host terminal (set actual local paths):

```powershell
$seed = 'C:/path/to/reviewed/pokemon-tracker'
pwsh -File "$runtime/Start-Coordinator.ps1" -Project pokemon -Repository $seed `
  -SuperpowersSkills 'C:/tools/superpowers' -GraphifySkills 'C:/tools/graphify'
# Start opens a separate visible PowerShell terminal streaming Elixir/Symphony.
# To open/reopen it manually in a visible terminal:
pwsh -NoExit -File "$runtime/Show-Logs.ps1" -Follow
# Bounded recent stdout/stderr for the gateway:
pwsh -File "$runtime/Show-Logs.ps1" -Tail 100
# Stop/remove credentials, preserve the project volume and all pending evidence:
pwsh -File "$runtime/Stop-Coordinator.ps1"
```

`-NoLogWindow` suppresses the automatic new window only when the gateway already
has the requested visible terminal running `Show-Logs.ps1 -Follow`. Ctrl-C in the
log viewer detaches it; it does not stop Symphony. Elixir remains the container's
foreground process after configuration validation, with logs at `/work/logs` and
Docker stdout/stderr. The dashboard is `http://localhost:4000` (host binding
127.0.0.1); a different localhost port can be selected. Do not dump container env.

Start obtains the approved existing gh token into memory and passes environment
**names**, never credential arguments. Codex auth is read-only. Runtime/config,
skills and seed mounts are read-only; the project volume is writable. Container
`seccomp=unconfined` supports the inner Codex workspace sandbox; no privileged or
full-access mode is used. A failed/timed-out start is uncertain: inspect that named
container and its logs before retrying. Start never removes it or clears pending
runs. The operator-authorized launcher uses Docker `unless-stopped`, so an
unexpected exit or daemon restart can resume the existing container; a deliberate
stop remains stopped. Stop-Coordinator removes it while preserving the volume.
The launcher installs no OS login task. Docker and the trusted isolated-check
runner must be available before checks can complete. Any separately installed
operator login task must preserve deliberate stop, one coordinator and one runner.
A restart does not clear pending work or authorize retry: reconcile an interrupted
cycle and use the documented deliberate recovery. No merge, deployment or Done
transition is authorized by restart support.

## Host acceptance to relay to the coordinator

1. Run the install/validation/dry-run commands above. `Test-Installation.ps1`
   invokes **the same launcher** with two temporary synthetic registrations and
   verifies different repos/control IDs/volumes/workflows, one unchanged global
   cap, and rejection of an unknown ID. It needs no auth, Docker, network or real
   unrelated repo and deletes only its own temporary fixture directory.
2. After live prerequisites, inspect startup config and the visible terminal;
   verify only the selected public queue wakes the coordinator. An empty queue
   deliberately blocks paid dispatch. No product work starts merely from registration.
3. Inspect the safe resource/port fields (not the container environment):
   `docker inspect --format '{{.HostConfig.NanoCpus}} {{.HostConfig.Memory}} {{json .HostConfig.PortBindings}}' symphony-choubokyann`.
   Expect 2000000000 NanoCPUs, 3221225472 bytes and localhost publication. Attempt
   another supported start and confirm the existing-container rejection.
4. Inspect `{{.HostConfig.RestartPolicy.Name}}` for `unless-stopped`. After a
   deliberate idle reload, verify loaded child cap 3, Astra/high parent and
   Sol/high child transcript metadata. A declared limit is not proof of four
   agents running; use concurrent children only for independent disjoint work.
   Keep GitHub decisions, integration and check submissions serialized.
   Relay actual parent/child transcript model metadata, exact reviewed heads,
   unchanged/changed queue and interrupted/pending recovery results. Follow
   README's inspect/acknowledge/retry protocol; no after_run acknowledgment.
5. Stop, confirm container removal, and verify the selected volume remains with
   `docker volume inspect symphony-choubokyann-pokemon-work`. Report limitations
   to the in-Symphony coordinator; the gateway does not approve ownership itself.

The container used to develop this extension has neither PowerShell nor a Docker
socket. These host checks are executable handoff instructions, not claimed live
results. CPU/RAM choices preserve headroom against operator-reported resources;
there is no throughput/cost improvement claim or automatic resource scaling.
