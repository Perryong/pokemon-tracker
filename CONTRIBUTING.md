# Contributing

Start with the [Pokemon Reseller Agent project](https://github.com/users/ChouBokYann/projects/1).

| What you need | Live view |
| --- | --- |
| Available work | [Ready](https://github.com/users/ChouBokYann/projects/1/views/2) |
| Who is doing what now | [Active](https://github.com/users/ChouBokYann/projects/1/views/3) |
| Dependencies/access decisions | [Blocked](https://github.com/users/ChouBokYann/projects/1/views/4) |
| PRs needing review | [Review](https://github.com/users/ChouBokYann/projects/1/views/5) |
| Completed work | [Done](https://github.com/users/ChouBokYann/projects/1/views/6) |

Open an issue to see its latest accepted claim: the GitHub account identifies the responsible person, and the session identifies their human/agent worker. Project membership does not grant access to either repository. The project owner manages colleague invitations separately.

Follow [AGENTS.md](AGENTS.md) for issue creation, dependency checks, claiming, branches and PRs. Humans use the same claim workflow. Follow [LEDGER.md](LEDGER.md) for progress, handoff and recovery. Do not maintain a second manually copied active-work table here.

## Local checks

Application setup and deployment context remain in [README.md](README.md). Run the checks affected by your change:

```powershell
# Claim workflow (standard library; no credentials/network)
python -m unittest discover -s .github/scripts -p test_issue_claim.py
# Application checks
npm test -- --run
npm run build
npm run lint
```

Install application dependencies and configure local development as described in README first. If Node's experimental Web Storage conflicts with the tests, set `$env:NODE_OPTIONS='--no-experimental-webstorage'` for that test invocation. Report existing lint failures separately; do not describe them as passing. Documentation-only changes require link/content review and `git diff --check`, not application deployment.

## Maintainer activation

1. Review and merge the setup PR. Claim dispatch requires the workflow on the default branch; bootstrap ownership applies only to the setup issue until then.
2. In each repo's Actions secrets, configure `COORDINATION_READ_TOKEN` for read-only Issues access to both repos and `COORDINATION_PROJECT_TOKEN` for the shared user-owned Project, including access to read its issue-backed items. The built-in token handles local issue writes and Actions-run provenance. Use credentials authorized for both owners; do not assume one fine-grained token covers both accounts. Never reuse/export a contributor's CLI token without their explicit authorization.
3. Verify the intended callers have repository write access and Project write access for manual status updates. Maintainer overrides require maintain/admin access.
4. Ensure labels `feature`, `update`, and `bug` exist. Use native project auto-add if available; explicit addition in AGENTS.md works for both repos regardless of plan limits.
5. Exercise a clearly marked test issue through claim, conflicting claim, dependency block, release and completion. Record evidence in its ledger. Until these checks pass, the workflow is **installed, not verified operational**.

The shared Python scripts, focused tests, and claim workflow should remain identical in both repos. Change them through paired PRs and rerun the focused checks in each. There is no shared package to publish or server to maintain.
