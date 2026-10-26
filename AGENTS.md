# Agent contribution rules

This repository participates in [Pokemon Reseller Agent](https://github.com/users/ChouBokYann/projects/1).
Read [CONTRIBUTING.md](CONTRIBUTING.md) for live work and checks, and [LEDGER.md](LEDGER.md) for ownership/history. These rules apply to humans and all development agents.

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
