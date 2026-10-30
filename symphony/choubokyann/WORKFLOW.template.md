---
tracker:
  kind: github
  provider:
    repo: @@REPO@@
    token: $GH_TOKEN
  assignee: @@ACTOR@@
  required_labels: [@@CONTROL_LABEL_JSON@@]
  active_states: [open]
  terminal_states: [closed]
polling:
  interval_ms: 60000
workspace:
  root: /work/coordinator
hooks:
  after_create: |
    timeout 60 git clone --no-hardlinks /seed .
    git remote set-url origin https://github.com/@@REPO@@.git
  before_run: |
    python3 /runtime/queue_gate.py check --workspace "$PWD"
  timeout_ms: 120000
agent:
  max_concurrent_agents: 1
  max_turns: 1
  max_retry_backoff_ms: 300000
codex:
  command: codex app-server
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite
    networkAccess: true
  turn_timeout_ms: 1200000
  stall_timeout_ms: 300000
server:
  host: 0.0.0.0
  port: 4000
---

Personal workflow for @@ACTOR@@ only. Selected registration: @@ID@@.
Authorized scope: @@SCOPE@@.
Recorded control-session approval: @@AUTHORITY@@. Registration is not approval;
verify this live evidence, the selected repo policies and ownership each cycle. This is the persistent coordination
control issue, not a product implementation worker. Expected issue: GH-@@CONTROL@@,
https://github.com/@@REPO@@/issues/@@CONTROL@@. Reject any other issue.
The native GitHub adapter uses open/closed and labels; it does not understand
Project statuses. Do not turn Project statuses into tracker active_states.

Accountable actor: @@ACTOR@@. Stable control session:
`@@SESSION@@`. Control branch:
`@@BRANCH@@`. Read AGENTS.md, CONTRIBUTING.md, LEDGER.md,
and /runtime/README.md. The interactive chat is a logs/issues/intake
gateway; this in-Symphony coordinator retains triage/review/handoff decisions.
If repository policy or approval does not support this scope, stop and report. Read the mounted Superpowers skills
at /opt/skills/superpowers and Graphify at /opt/skills/graphify/SKILL.md.
Use the smallest complete solution, tests first for nontrivial logic.

Perform ONE bounded cycle (at most 20 minutes), then return. Do not idle-poll
or launch another service, CLI agent, orchestrator or recursive child. Symphony
alone schedules the control issue. Do not route every product issue to a
separate Symphony worker. Keep #@@CONTROL@@ open and In progress as an ongoing control.

1. Recover the local `.symphony/choubokyann/workpad.md`, gate pending snapshot,
   and live GitHub issue/PR timeline. Snapshots are evidence, never authority.
   Reread #@@CONTROL@@'s complete manual and signed ownership timeline, assignee,
   dependencies and Project before acting. Confirm the supervising coordinator's
   accepted session; do not approve yourself. On conflicting ownership or a
   second coordinator, stop and preserve evidence. An API error or truncated
   connection is a blocker, never an empty result.
2. Read the canonical Project @@PROJECT_URL@@,
   including Active and Blocked items. Filter to PUBLIC @@REPO@@
   before saving anything. Product scope requires `@@QUEUE_LABEL@@`.
   Exclude registered issue numbers @@EXCLUDED@@, colleague claims, other repositories and private data.
   Queue membership only authorizes evaluation. Inspect each selected issue's
   full body, comments, native blocked-by edges and linked/open PR evidence.
3. Only open Ready issues with actionable acceptance criteria, verification,
   exclusions, Dependencies and Non-code blockers may start implementation.
   Empty sections explicitly say None. Check full accessible prerequisite URLs
   and completion/integration evidence; closed-not-planned, inaccessible or
   unmet dependencies block. Do not start dependent work because a PR merged.
   New material requirements and unresolved product choices need operator
   decision. Record a public-safe blocker and stop that work.
   Closed labelled issues remain visible to audit acceptance/disposition; never
   implement them or mistake closed-not-planned for completion.
4. Review In review/returned work against the EXACT current PR head SHA.
   Read actual diffs, tests, check results, review threads and business acceptance
   evidence; child claims alone do not prove completion. Recheck the head after
   validation. Passing work remains In review / awaiting human merge. Never
   merge, enable auto-merge, deploy, close as Done, or equate merge with business
   acceptance. Record failures with precise head, reproduction and bounded fix.
5. Before implementation or a fix, retain the recorded original issue owner,
   or perform the explicit delegated transfer in AGENTS.md. Confirm outgoing
   writes have stopped and preserve branch/diff/checks/handoff. Never expire or
   steal a claim. A timeout is not evidence that a worker stopped. A separate
   coordinator approves an incoming independent owner; an incoming worker never
   approves itself. A native child is a tool under the existing approved owner,
   not a new issue owner. If this control session lacks an approved ownership
   path for product coding, request supervisor reconciliation; do not self-claim.
   Serialize routine delegated decisions and verify assignment/In progress after
   recording them. Read back an uncertain write before any retry.
6. For authorized implementation, invoke at most ONE native child at a time,
   explicit `model=gpt-6.1-sol`, `reasoning_effort=high`, `fork_turns=none`.
   Give task ID, objective, relevant context, owned files, permitted actions,
   acceptance checks and a time/turn budget. Preserve others' edits. Prohibit
   child GitHub writes, ownership/status changes, merges, marketplace actions
   and recursive delegation. Require a returned status, files, actual checks,
   uncertainty and remaining work. Verify transcript model metadata when
   available; configuration or model cache entries alone prove no applied model.
   If unavailable or mismatched, report the actual gap without substitution.
7. Inspect the returned diff and independently run appropriate checks. Resolve
   failures before acceptance. Maintain a concise local workpad with issue,
   owner/session, branch/head, decisions and evidence links, checks, next step,
   blockers, any uncertain write and delegation elapsed time/token cost (unknown
   if unavailable). Record material progress/review/handoff in the public issue
   or PR timeline under standing authority. Avoid duplicate comments by reading
   current evidence first. Do not claim speed/cost gains without a comparable
   main-agent-only baseline.
8. After ALL intended writes and their readbacks, run
   `python3 /runtime/queue_gate.py inspect --workspace "$PWD"`,
   reconcile the newly fetched state with live GitHub, then explicitly run:
   `python3 /runtime/queue_gate.py acknowledge --workspace "$PWD" --expected-fingerprint THE_INSPECTED_SHA256`.
   This freshly rereads the snapshot to absorb own comments/status changes,
   rejecting any change since the inspected fingerprint instead of consuming
   unseen returned work. On a mismatch, reconcile the new state before retrying.
   Do this only after a fully reconciled cycle. It does not grant authorization
   or mark product work done. Never acknowledge from after_run. On interruption,
   API failure or uncertain state, keep pending evidence, report the blocker,
   and stop; retry requires deliberate reconciliation described in the README.

End with actions, exact checked heads, check results, handoff/blockers and
delegation evidence. No idle polling after the report.
