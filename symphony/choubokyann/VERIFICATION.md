# Multi-project continuation verification — 2026-10-30

This section supersedes the archived cycle's single-project limitation and
interactive-supervisor wording below. The earlier work is preserved in full.
Accountable contributor/session: ChouBokYann /
`symphony-coordinator-27-20261030`; branch `choubokyann/symphony-coordinator`.
Continuation began 13:09 UTC and completed within the requested 25-minute bound.

## Outcome

Implemented generic explicit registration using the existing runtime/gate/profiles.
Only Pokemon is seeded. `registry.py register` adds reviewed public repo/user
Project records; `Start-Coordinator.ps1 -Project ID` selects the same record for
origin/branch checks, per-project volume, workflow generation and gate queries.
No Python/PowerShell source edit or Pokemon issue ID copy is needed for another
registration. One global named container remains capped at 4 CPUs/6 GiB, one
Astra/high plus one Sol/high child, one selected project at a time.

`Install-Coordinator.ps1` installs runtime files and a separate registry under
`$HOME/.symphony/choubokyann`. `Test-Installation.ps1` exercises the same launcher
in offline dry-run mode using two temporary synthetic registrations. Start opens
a visible PowerShell terminal streaming the foreground Elixir/Symphony logs;
Show-Logs also supplies bounded recent stdout/stderr. The gateway executes host
commands and relays results; the in-Symphony coordinator retains decisions.
Exact commands and recovery/switching limits are in [MACHINE.md](MACHINE.md).

**Implemented locally, not installed or activated on the operator host.** This
container has no PowerShell or Docker socket. No live script/window/resource/
credential-removal test is claimed. The gateway must run the concrete host checks.

## Live evidence rechecked

- Complete #27 REST timeline: 11 events, including accepted distinct session
  comment 6523188095 and operator extension comment 6523350813. No competing or
  released ownership appeared. Issue open, sole assignee ChouBokYann, Project
  In progress, no native blocked-by prerequisites. Read the Project's complete
  item page, filtering private/other-repository items before reporting/persisting.
- Parameterized production inventory/issue/PR GraphQL queries each returned HTTP
  200 without GraphQL errors. #27 timeline/dependencies were complete. Canonical
  Project page was complete; the persistent coordinator and product queue labels
  select no issues. Therefore the prepared workflow has not been activated.
- #9 remains In review. PR #23 head observed:
  `dde45fa5b84850e05473007629858d858abb156f`. This is schema/readiness evidence,
  not a product code review or approval. No product claim/status was changed.
- Root `OPERATOR-INBOX.md` was read and preserved; there is no second inbox under
  symphony/choubokyann. Market #24/#26 and private old-repo work remain excluded.

## Native child result and applied model proof

Exactly one child in this continuation: `/root/project_registry`, task
`GH27-registry-extension`, explicitly `gpt-6.1-sol`, high, `fork_turns=none`.
Owned only registry.py, test_registry.py and projects.json; budget 8 minutes /
35 tool calls; no GitHub writes, ownership/status changes, commits/merge, services,
recursive delegation or shell-launched agents. It returned completed with eight
passing registry tests after six observed missing-feature failures.

Actual local transcript `turn_context` metadata:

| Role | Session UUID | Applied model | Effort |
| --- | --- | --- | --- |
| Parent | 01a18ced-c986-7522-b5d4-71f0dd6b6c1d | gpt-6-astra | high |
| Child | 01a18cee-db55-7971-8e58-f7dc203a9df1 | gpt-6.1-sol | high |

Child transcript: 13:10:26.413Z–13:13:19.094Z, 172.681 seconds. Cumulative usage:
590,798 input tokens (562,944 cached), 7,596 output, 598,394 total processed tokens;
monetary cost unknown. Main-agent integration/review time is included in the
continuation wall time but not isolated. No comparable main-only baseline was
performed; no cost/speed improvement is claimed.

The parent inspected all three artifacts and independently ran the tests before
accepting them. Main rework: made the symlink test portable on hosts without that
privilege; integrated data selection across all callers; bound gate state to its
registration; added CLI isolation tests and rejected an explicitly empty scope
instead of falling back to Pokemon. Worker TOML was not loaded into the native
child. File/action/depth limits remain policy, not credential security isolation.

## Actual checks

| Check | Result |
| --- | --- |
| Coordinator suite, `python3 -m unittest discover -s symphony/choubokyann -p 'test_*.py'` | **32 passed** (registry, gate, multi-project CLI/rendering/isolation, configuration contracts) |
| Signed-claim suite, `python3 -m unittest discover -s .github/scripts -p test_issue_claim.py` | **13 passed** |
| Tests-first evidence | Registry absent: six failures; integration missing scope/rendering APIs: three errors; empty explicit scope: observed assertion failure, then fixed/green |
| Two synthetic projects | Actual machine CLI plans and gate CLI selection produce different workflows/volumes/scope-bound pending fingerprints; cross-registration check/inspect/acknowledge/retry preserve original state and fail closed |
| Elixir Workflow.load + Config.Schema.parse | Pokemon and both synthetic rendered workflows passed; selected repos/labels and one runner/one turn checked; YAML boolean-shaped label remains a string |
| Codex 0.165.0 `app-server --strict-config --print-startup-config` | Both TOMLs validated as base configs in temporary Codex homes; exit 0; expected helper-alias warning only |
| Production GraphQL variable wiring | Inventory, #27 issue and PR #23 queries returned HTTP 200, no GraphQL errors |
| `sh -n symphony/choubokyann/entrypoint.sh`; `git diff --check` | Passed |
| AGENTS outside ChouBokYann section | Exact comparison against HEAD passed; global/colleague rules unchanged |
| PowerShell installer/start/stop/log/dry-run | Static review only; executable host acceptance path supplied, not run here |
| Application tests/build/lint | Not run: npm unavailable; no product application files changed |

Superpowers tests-first and verification guidance applied. Graphify's existing
partial graph was queried; current source findings were saved to ignored local
Graphify memory. New modules were verified by source inspection/tests, not assumed
present in the old graph. Official [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
was checked alongside installed CLI help: the concurrency key excludes the
primary thread, and explicit child model/effort override defaults. This agrees
with the observed model transcripts; declarations alone were not treated as proof.

## Files changed in this continuation

- New: Install-Coordinator.ps1, Show-Logs.ps1, Test-Installation.ps1,
  WORKFLOW.template.md, machine.py, registry.py, projects.json,
  test_registry.py and test_multi_project.py under symphony/choubokyann/.
- Updated: root WORKFLOW.md, ChouBokYann-only AGENTS.md; Start-Coordinator.ps1,
  Process.ps1, entrypoint.sh, queue_gate.py, test_configuration.py, README.md,
  MACHINE.md and this VERIFICATION.md.
- Preserved prior setup: both TOMLs, Stop-Coordinator.ps1, test_queue_gate.py,
  .gitignore and the supplied root OPERATOR-INBOX.md. No product files changed.

## Limits and host handoff

The host must execute MACHINE.md's install, offline synthetic validation and live
pilot, with the reviewed ownership policy present in the seed's committed tree; missing PowerShell/Docker here prevents claiming those completed. Registry
records validate local syntax, not real authority or readiness. The coordinator
must reread each selected repository's policy, full ownership timeline, Project
and prerequisites; Pokemon delegation never automatically extends to another repo.
Public repositories and user-owned Projects only. The gate retains the existing
100-entry fail-closed connection bound. Native tool policy does not isolate shared
credentials; the fixed container cap covers supported starts on one Docker daemon.

Existing installation/container/pending state is never discarded by start/install.
Legacy unbound gate state fails closed and needs deliberate reconciliation. The
new per-registration volume names do not migrate/delete the old prototype volume;
preserve its evidence and recorded handoff before first activation. Neither a
registration nor a merged PR establishes business acceptance. Human merge remains
mandatory; #27 remains an open ongoing control issue.

No commit, push, PR, GitHub mutation, service launch, unrelated registration,
product implementation or marketplace action was performed in this continuation.

---

# Archived prior-cycle report (superseded where noted above)

# Bootstrap verification — 2026-10-30

Accountable contributor/session: ChouBokYann /
`symphony-coordinator-27-20261030`. Branch:
`choubokyann/symphony-coordinator`. Local changes only; no commit, push, PR,
GitHub mutation, service start, product implementation or market action.

## Live readiness and ownership

- Read #27's complete timeline (9 events at final audit), issue body, assignee
  and native blocked-by endpoint. The
  [delegated acceptance](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6523188095)
  names this distinct session and branch; no competing/released ownership event
  appeared. Issue is open, assigned to ChouBokYann; native dependencies are empty.
- Read Project 1 with GraphQL, checked complete pageInfo, and filtered canonical
  public tracker items before recording results. #27 is In progress; #9 remains
  In review. There are no Ready canonical tracker items. Public #10 has no Status.
  This audit does not grant permission to change colleague items or declare
  closed work complete.
- Read the canonical repo's open issues/PRs/labels. PRs #23 and #25 are existing
  product work; no overlapping coordination PR was found. PR #23's observed head
  is `dde45fa5b84850e05473007629858d858abb156f`. It was queried for gate schema
  validation, not reviewed/approved as a product deliverable.
- Neither `symphony-choubokyann-coordinator` nor
  `symphony-choubokyann-queue` exists at audit time. #27 still has its bootstrap
  label. The new workflow is therefore **prepared, not activated**. No live
  labels/statuses were changed. Market #24/#26 and private old-repo work were
  excluded from implementation and persisted evidence.
- A scope update arrived in the preserved, externally supplied
  `OPERATOR-INBOX.md` and was verified in the
  [live timeline](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6523350813).
  MACHINE.md documents reusable installation, explicit manual registration,
  visible logs and one shared agent slot. Only Pokemon is executable initially;
  another project needs a reviewed registration/adapter change. No generic
  scheduler or automatic discovery was introduced.

## Applied models and child trial

Exactly one native child was spawned: `/root/queue_gate`, task `GH27-gate`,
`model=gpt-6.1-sol`, `reasoning_effort=high`, `fork_turns=none`. Allowed writes
were only queue_gate.py and test_queue_gate.py, with a 10-minute/35-tool-turn
budget, no GitHub writes, ownership changes, merges, service starts, recursive
delegation or shell-launched agents. It returned to this coordinator.

Observed local `turn_context` metadata, not merely declarations:

| Role | Harness session UUID | Model | Effort |
| --- | --- | --- | --- |
| Primary | 01a18cdc-886b-78d1-ab8f-21e0dd14b95b | gpt-6-astra | high |
| Child | 01a18cdd-e10b-76a3-9ef3-cdfc704ab452 | gpt-6.1-sol | high |

Installed CLI: 0.165.0. Model cache also lists both requested models, but that is
availability evidence only. The native child ran from 12:51:53.763Z to
12:57:09.194Z, about 5m15s. Its recorded cumulative usage is 817,957 input tokens
(790,400 cached), 14,338 output tokens, 832,295 total processed tokens. Monetary
cost is unknown. Primary coordination/rework was not separately timed; overall
bootstrap time includes it. No comparable main-agent-only baseline was run, so
no speed/cost improvement is claimed.

The child reported tests-first development and 12 passing gate tests. Primary
review inspected actual code/tests, validated live GraphQL selections, requested
race-safe acknowledgement and review-thread coverage, then independently tested
the result. Primary rework added closed queued issue coverage (observed failing
test, then green), fixed string-key PR deduplication, and integrated profiles,
workflow/scripts/docs. Child result accepted with that rework.

The native tool's file/action limits and depth one are policy, not enforced
credential separation. The worker TOML is versioned but was not automatically
loaded into the native child; the explicit spawn and transcript prove its model.

## Actual checks

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s symphony/choubokyann -p 'test_*.py'` | 17 passed (13 gate, 4 configuration contracts) |
| `python3 -m unittest discover -s .github/scripts -p test_issue_claim.py` | 13 passed |
| Gate failure paths | Wrong actor/repo/label, competing assignee, Project status, API failure/timeout/truncation, pending retention, deliberate retry, changed/unchanged state, PR checks/reviews/threads, private Project filtering, no self-churn, acknowledgement race covered |
| `codex app-server --strict-config --print-startup-config` | Both profile files validated as base config in temporary Codex homes; exit 0. Only expected temporary-home helper-alias warnings |
| Installed Symphony `Workflow.load` and `Config.Schema.parse` via Elixir | Passed; GitHub adapter, unique control label, one turn and `codex app-server` confirmed; no service started |
| Live GraphQL inventory, issue #27, PR #23 | All returned HTTP 200 with no GraphQL errors, including stateReason and reviewThreads selections |
| `sh -n symphony/choubokyann/entrypoint.sh` | Passed |
| `git diff --check` | Passed |
| AGENTS boundary comparison against bootstrap input | Global/colleague sections unchanged; only ChouBokYann section edited |
| `npm test -- --run` | Could not run: npm not installed (exit 127). No application files changed; application build/lint not run |

Superpowers TDD and verification guidance were used. Graphify's installed
`/opt/agent-tools/bin/graphify` performed local AST extraction/query/save-result
without LLM calls; its graph/memory remain ignored. Extraction reported missing
SQL grammar and symbol-less files; the graph is partial context, not acceptance
authority. A truncated exploratory query was rerun with a sufficient budget.

## Remaining host verification and limits

- No Docker socket or PowerShell is available in this worker. PowerShell has
  static contract review only; no claim of launch/stop, localhost publication,
  CPU/RAM enforcement or credential-container removal being live-tested.
- Shell gh has no token in this bootstrap; live reads used Symphony's existing
  authenticated GitHub API tool. The gate's gh subprocess transport is tested
  with fixtures. End-to-end gh/environment forwarding needs the host pilot.
- The supervisor must review and exercise start/stop and queue-change/failure
  recovery with approved labels before unattended activation. Do not clear
  pending evidence to make a pilot pass. Startup validation alone does not prove
  applied runtime models; inspect new transcript metadata too.
- The gate fails closed above 100 entries per selected connection and after its
  read deadline; this bounds the initial installation. Extending pagination or
  registering another project is explicit reviewed work.
- The global cap covers supported starts on one Docker daemon, not manual
  bypasses or other machines. Token access is shared policy, not child isolation.
- New product ownership still follows the standing separate-approver rule;
  this setup claim grants no ownership of other product issues. Human merge and
  business acceptance remain required. #27 remains an ongoing control issue.

## Changed files

Root WORKFLOW.md; the ChouBokYann-only AGENTS.md section; .gitignore; and these
files under symphony/choubokyann/: coordinator.toml, worker.toml, queue_gate.py,
test_queue_gate.py, test_configuration.py, Process.ps1, Start-Coordinator.ps1,
Stop-Coordinator.ps1, entrypoint.sh, README.md, MACHINE.md and VERIFICATION.md.
OPERATOR-INBOX.md was supplied externally and preserved unchanged. Personal
workpad and Graphify output are ignored; no credentials were written to files.

## 2026-10-31 — owner-authorized source-only merge remediation

Perry authorized fixing the launcher and branch references, then merging PR28 into
its existing `feature/sales-agent` base and deleting the PR head. The current Sales
base was merged while retaining the newer coordinator policy. The exposed-token
startup implementation is removed. PowerShell live start refuses before any tool
or credential lookup; direct shell entrypoint, workflow before-run hook and model
command also refuse. Offline install/render/dry-run remain available. The seed
registration now uses `feature/sales-agent`; historical branch names above remain
as evidence, not active registration instructions.

Verification on the final source candidate:
- Five new launcher/security tests failed against the old source, then passed.
  Synthetic token sentinels and tool-call markers verified no tool/model execution
  or secret output. PowerShell 7.6.9 was actually executed on macOS.
- macOS coordinator suite: 203 tests, 188 passed and 15 Linux-only tests skipped.
  Canonical TMPDIR avoids macOS `/var` symlink rejection by the broker's intended
  path defense; no production validation was weakened.
- Credential-free, network-disabled, read-only-source Linux Python 3.13 container:
  203 tests, 201 passed and two PowerShell tests skipped (both passed on macOS).
  All 15 real kernel privilege-boundary tests passed. No live model was started.
- Shared claim suite: 13 passed. PowerShell synthetic two-project validation and
  a fresh temporary install plus installed-runtime validation passed.
- Shell syntax and `git diff --check` passed. Existing Sales files are unchanged
  from merged PR23, whose 46 tests passed in the preceding merge verification.

This is a source-only safety fix, not a working broker deployment. Live operation
remains blocked pending broker integration and host acceptance. Existing host
installations/containers were not updated or stopped; preserve their registries,
volumes and pending evidence for deliberate operator reconciliation. Issue27 stays
open, and historical security reports are not proof of live remediation.
