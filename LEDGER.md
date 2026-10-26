# Work ledger

The authoritative work ledger is each GitHub issue's timeline and linked PR evidence. Start at [Active work](https://github.com/users/ChouBokYann/projects/1/views/3) or [Completed work](https://github.com/users/ChouBokYann/projects/1/views/6), then open the issue. This file defines the record; it does not duplicate live statuses.

## Ownership events

The trusted `issue-claim.yml` workflow writes comments prefixed with `<!-- pokemon-coordination/v1 -->`. Ownership controls require both verified workflow provenance and an HMAC signature from the protected environment's ledger key. The signed JSON binds the repository, issue, UTC time, accountable actor, session, claim ID, executing actor, operation, workflow run/attempt, and result. A bot name or copied run ID alone is insufficient.

- `reserved`: exclusive acquisition started; it blocks competing sessions even if a later write fails.
- `accepted`: assignment and ledger ownership are recorded. Work starts only after this event AND its workflow run succeed.
- `releasing`: release started; ownership remains reserved until removal is verified.
- `released`: ownership ended, with handoff and optional override reason.

Rejections are recorded in the failed workflow run's safe error output, not as changes to the issue's control history. Link that run from a human progress comment when context is needed. Human-authored lookalike control comments cannot release a claim. Invalid bot signatures stop processing for maintainer investigation; a confirmed unauthenticated comment may be removed after preserving incident evidence. This is an operational ledger, not a tamper-proof audit system; maintainers must reconcile unexpected manual changes.

## Progress entries

Append a brief comment when starting, reaching a useful checkpoint, becoming blocked, resuming, requesting review, handing off, or completing. Include:

```text
Event: progress | blocked | resumed | handoff | completed
Worker: GitHub user / session
Branch or PR: link
Completed: concrete result
Checks: command and actual result / evidence link
Remaining: next actionable step
Blockers: full accessible issue references, or a public-safe restricted-dependency notice
```

Corrections append new entries; do not rewrite history to imply a test passed or work completed. Use the GitHub timestamp as the event time. Keep secrets and private material out of public issues and workflow inputs.

## Recovery

GitHub concurrency does not promise FIFO order. A pending request may be cancelled when another request arrives. Cancelled, skipped, queued, or failed runs never grant permission to start.

After an unknown API outcome, inspect the issue and run before retrying. A reserved claim stays with its recorded user/session. That session may retry the claim; competing sessions must wait. A half-finished release remains reserved and can be retried. Maintainers may explicitly release abandoned work with a reason and handoff using the workflow. Never automatically expire ownership.

Completed workflow request IDs cannot be reused to acquire or release a later claim. Start a new dispatch for a new ownership lifecycle. Fresh resume requests append a matching signed acknowledgement while keeping the original claim ID; repeated acknowledgements in the same run attempt are idempotent. Copied signed events are ignored as duplicates, not applied again.

If a failed request never recorded an event, a re-run is rejected because it has no recorded target claim. Inspect current ownership and submit a fresh dispatch instead. This prevents an old failed release from releasing a newer claim by the same session.

A recorded accepted/released event may exist after a later run failure. It still affects exclusivity, but a worker must reconcile and obtain a successful acknowledgement before starting. Project-sync warnings do not erase ownership: repair the Project view using AGENTS.md. A repeated release after an already completed release may be rejected because there is no active claim; inspect the released event and repair status rather than creating a new claim.

Set Done only after acceptance evidence and the required merge/integration work are complete. A cancelled issue or abandoned PR is not completed work. Record the disposition and release the claim explicitly.
