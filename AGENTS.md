# Agent contribution rules

This repository participates in [Pokemon Reseller Agent](https://github.com/users/ChouBokYann/projects/1).
Read [CONTRIBUTING.md](CONTRIBUTING.md) for live work and checks, and [LEDGER.md](LEDGER.md) for ownership/history. These rules apply to humans and all development agents.

## ChouBokYann's development sessions

The following contributor-specific process was explicitly approved on 2026-10-29. It applies only to ChouBokYann and agents working on that contributor's behalf. Identify the accountable contributor and a unique stable non-secret session before using it; the current CLI account alone does not establish whose behalf an agent acts on. Other contributors, including Perryong and their agents, continue to use the existing workflow below.

- Use this repository as the sole development repository and the existing [Pokemon Reseller Agent project](https://github.com/users/ChouBokYann/projects/1) for issues. Historical work elsewhere is context, not an implementation contract.
- This workstream owns the Sales Agent and its operator UI. Prioritize a working Sales Agent; keep UI changes focused on operating and validating it. Do not take ownership of the Market Agent implicitly.
- Use Superpowers for development, Graphify for code memory, and Symphony for development orchestration. Symphony governs development work; the application's LangGraph workflow engine remains a separate responsibility.
- Use Symphony for top-level issue-worker dispatch, task scheduling and orchestration recovery. Within a Symphony-managed worker, the bounded subagent tool calls described below are permitted; they do not create separate issue owners or another scheduler. This replaces the Ruflo orchestration convention for these sessions. Do not substitute another orchestrator silently. If Symphony is unavailable or unconfigured, report that limitation before dispatching workers; read-only investigation and directly authorized single-agent work may continue. Never describe orchestration as running without actual evidence.

### Development experiment: subagents as tools

This policy applies to ChouBokYann's development sessions only, not the application's Sales/Market runtime architecture. It takes precedence over skill instructions that automatically dispatch specialists or transfer control.

- Keep one main agent responsible for the issue, plan, conversation, integration, verification and final response. Use skills and ordinary tools within its context by default.
- When a separate context has a concrete benefit, invoke a subagent through the worker's supported subagent tool interface for one bounded task. A task may use a spawn/wait/result tool sequence; it must return its result to the calling main agent. Do not hand the user conversation or issue ownership to the subagent.
- Supply a task ID, objective, minimal relevant context, allowed tools/actions, explicit file ownership (read-only by default), acceptance checks and a time/turn budget. Tell the subagent it shares the codebase and must preserve other edits. Allow at most one subagent at a time during this experiment; prohibit recursive delegation and persistent specialist teams.
- Require a result containing task ID, status (completed/blocked/failed), findings or artifact/file references, actual checks and results, uncertainties and remaining work. On timeout or tool failure, surface the failure to the main agent; do not assume completion or silently relaunch work with an uncertain outcome.
- The main agent inspects relevant artifacts and checks before accepting the result, resolves conflicts and decides the next action. Subagents cannot independently merge, change issue ownership/status, contact users or perform live marketplace actions.
- Record each delegation's purpose, elapsed time, available token/cost usage (unknown if unavailable), check outcomes, whether the result was accepted and any main-agent rework. Compare representative tasks with a main-agent-only baseline using the same acceptance checks; count coordination and rework in total cost/time. Report observations without claiming improvement before comparative evidence exists.
- These instructions define the experiment's policy, not a security boundary. Verify the active harness exposes a subagent tool and returns results to the parent before the first trial. If it cannot enforce a required tool/permission limit, report the gap and keep that trial in the main agent; do not invent a working tool or launch an independent background agent as a substitute.

### Delegated ownership approval for these sessions

This section takes precedence over the signed `issue-claim.yml` claim/release requirements in this file, CONTRIBUTING.md and LEDGER.md **only for the sessions scoped above**. Existing workflow examples and signed-event rules continue to govern other contributors. Symphony scheduling, a branch, assignment and Project status do not grant ownership.

1. Keep the issue-first, acceptance-criteria, dependency, privacy, verification and review requirements below. Check the full issue timeline, including both manual and signed ownership records, and the Project's Active/Blocked views before claiming or resuming work. Any unreleased competing owner blocks implementation, regardless of which process recorded it.
2. On 2026-10-29 ChouBokYann explicitly delegated routine development claim/release/handoff approval to the Symphony coordinator or supervising agent, instead of requiring a fresh human approval each time. This standing authority applies only to ChouBokYann's selected Sales Agent/UI work in this repository. Issue selection authorizes evaluation, not unconditional acceptance. It grants no merge, deployment, live marketplace, spending or product financial approval authority.
3. The coordinator must be separate from the incoming implementation worker. It checks the complete live timeline (manual and signed records), dependencies, Project state, actionable acceptance criteria and unresolved non-code blockers. For a transfer, verify the outgoing worker has stopped implementation and preserve its branch/diff, checks and handoff. Never seize a colleague's claim, auto-expire a worker, or assume a timeout means its writes stopped. Conflicts, inaccessible evidence, ambiguous scope or missing prerequisites require operator input.
4. Record an explicit delegated decision naming coordinator/session, authority, evidence, issue, outgoing release (if any), incoming actor/session, branch and scope. Identify it as agent approval under standing operator authority, not a human-authored or signed workflow event. Recheck the latest timeline immediately before recording, serialize decisions through one coordinator, and verify assignment/status after the write. An uncertain write must be read back before retrying. This is procedural coordination, not an atomic multi-controller lock; multiple active coordinators must stop and reconcile. The incoming worker cannot approve itself.
5. Once the decision is recorded and assignment/In progress match, the worker may implement without another human confirmation. Preserve progress, blockers, PR/check evidence and handoffs. The coordinator can release a stopped worker after preserving its handoff and set Ready or Blocked; completion still needs required review/integration evidence. Keep the existing claim until a verified release/transfer decision is recorded. Routine transitions do not authorize merging or marking unfinished work Done.
6. Never use this exception to overwrite another contributor's claim, change their process, modify signed control records, or disable the shared claim workflow. Resolve cross-process conflicts with the maintainer before either worker proceeds. Symphony does not supply this approval policy automatically: the configured supervising coordinator enforces and records it before dispatch.

## Before touching implementation

1. Read the issue, all comments, native blocked-by relationships, linked PRs, and the project's Active and Blocked views. Search both repos for overlapping work. Historical plans are context; the live issue is the work contract.
2. Use an existing issue or create one for a concrete feature/update/bug. Include acceptance criteria, verification, exclusions, `### Dependencies` and `### Non-code blockers`. Each of those sections must explicitly say `None` when empty. Resolve non-code blockers before setting Ready. Use full dependency URLs and native blocked-by relationships; an inaccessible dependency is a blocker.
3. Add the issue to the Project. A maintainer sets `Ready` only after confirming actionable requirements and evidence that prerequisites are met. Closed-as-not-planned is not completion. Split cross-repo implementations into separate linked issues.
4. Request an exclusive claim. Do not code until the matching workflow run succeeds AND the issue contains its accepted ledger event for your user/session. Assignee or project status alone does not establish a claim.

Examples use PowerShell; substitute actual issue numbers, paths and a unique non-secret session ID. Keep the session stable when resuming this work. Do not use the example issue number to claim somebody else's setup work.

```powershell
$Repo = 'Perryong/pokemon-tracker'
$Issue = 12
$Session = 'codex-my-task-20261001'
gh issue list --repo $Repo --state open
gh issue view $Issue --repo $Repo --comments
gh issue view $Issue --repo $Repo --json blockedBy,blocking,assignees,state
# Write the complete issue body to a local UTF-8 file first.
gh issue create --repo $Repo --title 'Describe the outcome' --body-file issue-body.md --label update
gh project item-add 1 --owner ChouBokYann --url "https://github.com/$Repo/issues/$Issue"
# If applicable, add each prerequisite; also explain it in the issue body.
gh issue edit $Issue --repo $Repo --add-blocked-by 'https://github.com/OWNER/REPO/issues/NUMBER'
gh workflow run issue-claim.yml --repo $Repo --ref main -f issue=$Issue -f operation=claim -f session=$Session
gh run list --repo $Repo --workflow issue-claim.yml --event workflow_dispatch --limit 20
```

Record the matching run ID and inspect `gh run view RUN_ID --repo $Repo --log`. Match the actor/session/issue ledger event and that run's successful conclusion. A failed, queued, cancelled, skipped, or unacknowledged run grants no ownership. If no event appears, inspect the run before retrying; never guess from the latest run alone. A second agent sharing your GitHub account must use its own session and cannot take your claim.

## Implement, verify, and open a PR

- Use a dedicated branch such as `issue-12-short-description`; preserve other contributors' changes.
- Recheck dependencies before starting/resuming and before review. Never turn a failed API read into “no blockers.” If requirements or dependencies change, post a progress/blocker entry and set Blocked. Retain the claim or explicitly release it with a handoff; do not abandon it silently.
- Keep changes within the issue's acceptance criteria. Run the relevant checks in CONTRIBUTING.md and report actual results, including pre-existing failures.
- Open a PR against this repo's `main`. Use a body file to preserve Markdown. Include the issue URL, outcome, checks and remaining blockers. Use `Closes OWNER/REPO#N` only when the PR fully satisfies that issue; otherwise use `Refs`.

```powershell
git switch -c "issue-$Issue-short-description"
# Implement, test, and commit only the intended files.
git push -u origin HEAD
gh pr create --repo $Repo --base main --title 'Describe resulting behavior' --body-file pr-body.md
```

Link the PR and test evidence in the issue and set `In review`. Do not merge without the maintainer's authorization. An open or merged PR is not sufficient for Done when the issue also requires deployment/integration evidence. Update the issue with that evidence before closing it as completed.

## Release, hand off, or recover

```powershell
gh workflow run issue-claim.yml --repo $Repo --ref main -f issue=$Issue -f operation=release -f session=$Session -f handoff='Branch/PR: ...; checks: ...; remaining: ...; blockers: ...'
```

Use real handoff details instead of the ellipses. For fully completed, closed-as-completed work, begin the handoff with `Completed:` and include the merged PR and acceptance evidence. This is an explicit contributor attestation; the workflow does not judge application correctness. Otherwise open work returns to Ready or Blocked after dependency checks. Verify the released event and successful run.

Only a maintainer/admin may override an abandoned claim, using `-f override=true -f reason='Owner confirmed abandonment'` and a complete handoff. No automatic expiry or theft. A partial reservation or release remains exclusive until the owning session retries or a maintainer reconciles it. Do not delete or edit control events to “unlock” work. Unknown write outcomes must be inspected before retrying.

## Project status and repair

The issue ledger is authoritative. After review, blocking, or completion, update the Project explicitly. If the workflow reports `project_sync: pending`, the recorded ownership still stands; repair the status before handing work to another agent.

```powershell
gh project item-list 1 --owner ChouBokYann --format json --limit 1000
gh project field-list 1 --owner ChouBokYann --format json
gh project item-edit --project-id PVT_kwHOBwH5gM4BlVDy --id ITEM_ID --field-id PVTSSF_lAHOBwH5gM4BlVDyzhkCW-I --single-select-option-id OPTION_ID
```

Match the item to its full issue URL and read the option ID from `field-list`; never use another issue's item ID. Paginate via the API if the CLI limit omits the target.

## Information boundaries

The tracker repo is public. Never copy private issue titles, bodies, secrets, or internal evidence into it or its logs. Public blocker messages should be generic; detailed evidence belongs in the private issue/project. Workflow dispatch inputs and release text appear publicly in public repos. Tokens belong in GitHub secrets, not issue bodies, scripts, command literals or agent memory.

## Existing agent conventions

- For multi-file/complex work, discover Ruflo tools (memory/search/routing/swarm tools) when available. If unavailable, state that and use the repository workflow; do not fabricate calls.
- `/graphify` explicitly invokes the installed graphify skill before analysis.
- When active together: superpowers chooses the process, ponytail bounds scope, and unlazy proves acceptance. Gates cover requested work, not speculative additions. Preserve TDD where required; one runnable acceptance ledger can serve verification.
- Do not install the Stop hook unless explicitly requested.
