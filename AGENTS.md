# Agent contribution rules

This repository participates in [Pokemon Reseller Agent](https://github.com/users/ChouBokYann/projects/1).
Read [CONTRIBUTING.md](CONTRIBUTING.md) for live work and checks, and [LEDGER.md](LEDGER.md) for ownership/history. These rules apply to humans and all development agents.

## ChouBokYann's development sessions

The following contributor-specific process was explicitly approved on 2026-10-29. It applies only to ChouBokYann and agents working on that contributor's behalf. Identify the accountable contributor and a unique stable non-secret session before using it; the current CLI account alone does not establish whose behalf an agent acts on. Other contributors, including Perryong and their agents, continue to use the existing workflow below.

- Use this repository as the sole development repository and the existing [Pokemon Reseller Agent project](https://github.com/users/ChouBokYann/projects/1) for issues. Historical work elsewhere is context, not an implementation contract.
- This workstream owns the Sales Agent and its operator UI. Prioritize a working Sales Agent; keep UI changes focused on operating and validating it. Do not take ownership of the Market Agent implicitly.
- Use Superpowers for development, Graphify for code memory, and Symphony for development orchestration. Symphony governs development work; the application's LangGraph workflow engine remains a separate responsibility.
- Use Symphony to schedule one persistent coordination control issue (#27) through the personal root WORKFLOW.md and its unique `symphony-choubokyann-coordinator` label. Native GitHub polling understands open/closed plus labels, so the coordinator must read the Project and full product timelines itself. Product issues opt in with `symphony-choubokyann-queue`; they are not independently dispatched by Symphony. Within the coordinator, the bounded subagent tool calls described below are permitted; they do not create separate issue owners or another scheduler. This replaces the Ruflo orchestration convention for these sessions. Do not substitute another orchestrator silently. If Symphony is unavailable or unconfigured, report that limitation before dispatching workers; read-only investigation and directly authorized single-agent work may continue. Never describe orchestration as running without actual evidence.

### Development experiment: subagents as tools

This policy applies to ChouBokYann's development sessions only, not the application's Sales/Market runtime architecture. It takes precedence over skill instructions that automatically dispatch specialists or transfer control.

- Keep one main agent responsible for the issue, plan, conversation, integration, verification and final response. Use skills and ordinary tools within its context by default.
- When a separate context has a concrete benefit, invoke a subagent through the worker's supported subagent tool interface for one bounded task. A task may use a spawn/wait/result tool sequence; it must return its result to the calling main agent. Do not hand the user conversation or issue ownership to the subagent.
- Supply a task ID, objective, minimal relevant context, allowed tools/actions, explicit file ownership (read-only by default), acceptance checks and a time/turn budget. Tell the subagent it shares the codebase and must preserve other edits. Under the 2026-10-31 operator extension in #27 comment 6537493940, allow at most three Sol/high native children alongside one Astra coordinator (four development agents total) after the reviewed runtime reload. Use fewer when work is not independent, give concurrent children disjoint file ownership, and serialize shared integration, GitHub decisions and isolated-check submissions through the main agent. Prohibit recursive delegation and persistent specialist teams.
- Require a result containing task ID, status (completed/blocked/failed), findings or artifact/file references, actual checks and results, uncertainties and remaining work. On timeout or tool failure, surface the failure to the main agent; do not assume completion or silently relaunch work with an uncertain outcome.
- The main agent inspects relevant artifacts and checks before accepting the result, resolves conflicts and decides the next action. Subagents cannot independently merge, change issue ownership/status, contact users or perform live marketplace actions.
- Record each delegation's purpose, elapsed time, available token/cost usage (unknown if unavailable), check outcomes, whether the result was accepted and any main-agent rework. Compare representative tasks with a main-agent-only baseline using the same acceptance checks; count coordination and rework in total cost/time. Report observations without claiming improvement before comparative evidence exists.
- These instructions define the experiment's policy, not a security boundary. Verify the active harness exposes a subagent tool and returns results to the parent before the first trial. If it cannot enforce a required tool/permission limit, report the gap and keep that trial in the main agent; do not invent a working tool or launch an independent background agent as a substitute.

### Bounded readiness and acceptance reviewers

- Under the operator extension in [#27 comment 6539152475](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6539152475), use a bounded native Astra/high reviewer for selected readiness and exact-head acceptance reviews. The model clarification in [#27 comment 6539174541](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6539174541) requires `model=gpt-6-astra`, `reasoning_effort=high`, `fork_turns=none` for reviewers. It returns to the coordinator and consumes one of the existing three child slots; it is neither a persistent specialist nor another coordinator. The reviewer must be independent of the implementation task it reviews. Keep four agents total: one Astra coordinator, at most one Astra reviewer, and at most two Sol/high implementation workers while that reviewer is active; without a reviewer, up to three Sol workers remain allowed. This reviewer exception supersedes Sol-only child wording below; default implementation model/cap settings stay unchanged.
- Supply one explicit task: readiness (requirements, verification, exclusions, ownership, full dependencies and non-code decisions) or acceptance (exact current PR head, actual diff/tests/checks, requirements and unresolved findings). Give public evidence and immutable source, read-only file scope, permitted tools and a time/turn budget. No repository execution, GitHub/status/ownership writes, merges, marketplace actions or recursive delegation. The parent submits isolated checks and independently verifies findings and current heads.
- Require task ID, completed/blocked/failed status, ready/blocked or pass/changes-needed verdict, evidence references, exact head for acceptance, each blocker’s responsible owner and next action, actual checks and uncertainties. Failed, timed-out, incomplete or inaccessible reviews cannot promote or pass work. A moved head invalidates acceptance and needs a fresh scoped review.
- Reuse the queue gate and local workpad: record the reviewed issue/dependency/ownership evidence digest or PR head plus check/review evidence digest, verdict and rationale. Do not spawn another reviewer for unchanged inputs, including when only another issue changed. Review records are evidence, not authorization. Astra owns promotion, dispatch and retained-owner rework decisions; only resolved prerequisites and non-code blockers permit Ready. Passing work stays In review awaiting human merge.
- Initial Pokemon intake is limited to already selected public Sales/UI issues #8, #9 and #11–#21 after full ownership/scope checks. Add the existing `symphony-choubokyann-queue` label only as evaluation opt-in. Exclude colleague Market #24, #26 and #31–#41, unrelated issues and private/other repositories. Never blanket-rewrite statuses or duplicate blocker comments. Record genuine blockers and the responsible decision; queue membership never grants implementation ownership. Later intake needs recorded selection authority.

### Personal coordinator activation and review

- The in-Symphony Astra coordinator owns triage, dispatch, review and routine handoffs; interactive chat is the operator status/log/issue-intake gateway. [MACHINE.md](symphony/choubokyann/MACHINE.md) defines one shared runtime slot (one Astra plus up to three Sol children) and explicit per-project registration. Only Pokemon is seeded. Install the runtime under the current user profile with `Install-Coordinator.ps1`; add reviewed records with `registry.py register` and select with `Start-Coordinator.ps1 -Project`. Another public repository/user-owned Project requires its own recorded authority and scope, not Python/PowerShell edits or copied Pokemon issue IDs. Registration grants no ownership and does not extend this repository's standing delegation to another repo. One fixed global coordinator slot, one Astra plus up to three Sol children (four development agents total), and separate per-registration volumes remain mandatory. The operator extension in #27 comment 6526149446 permits one ephemeral non-agent test container alongside it: coordinator and tests each 2 CPUs/3 GiB, aggregate at most 4 CPUs/6 GiB. Tests use the restricted host tool and never receive coordinator credentials or sockets. The launcher opens a visible Elixir/Symphony log terminal; the gateway relays results and operator decisions without becoming the approving coordinator.
- The versioned setup is [symphony/choubokyann/README.md](symphony/choubokyann/README.md). Review and explicitly activate it on the operator host; merely committing WORKFLOW.md does not start a service or authorize claims. The operator-authorized launcher restart policy is `unless-stopped`; a restart preserves the pending gate and never authorizes automatic retry or ownership recovery. Keep #27 open as a control issue, not a product deliverable to close.
- Mount `coordinator.toml` as `/root/.codex/config.toml` and use `codex app-server`; this CLI does not support app-server `--profile`/`-p`. The coordinator is `gpt-6-astra` at high effort. Set `agents.max_concurrent_threads_per_session=3` (excludes the primary), `agents.default_subagent_model="gpt-6.1-sol"` and high default subagent effort. Invoke a native child explicitly with Sol/high and a clean context. Depth one and child action limits are policy; shared credentials are not isolation. Do not claim a worker TOML was applied to a native child without evidence. Check runtime transcript model metadata, not just declarations or cache availability.
- Only Ready, actionable opted-in issues may begin implementation after full ownership/dependency checks. Recheck prerequisites before review. In review work is reviewed against the exact current PR head, actual diffs, tests and review threads. Blocking findings return to a bounded worker only after ownership checks; preserve the original recorded owner or obtain an explicit delegated transfer before coding. The coordinator cannot approve itself as an incoming independent owner. Tool children operate under an already approved ownership scope.
- Passing review remains In review / awaiting human merge. No automatic merge, deployment or Done transition is authorized. A merged PR alone does not establish business acceptance. Material new requirements need operator decision. Exclude Market #24/#26 and private old-repository work.
- Persist concise local workpads and material issue/PR timeline evidence; reread live state each cycle. The queue gate suppresses unchanged work and retains pending evidence on failure. Explicitly acknowledge a freshly inspected snapshot only after reconciled end-of-cycle writes; never acknowledge from `after_run`. An interrupted/uncertain cycle requires deliberate retry after checking whether writes completed and workers stopped. Never clear pending state just to restart.

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
