# Restricted GitHub broker foundation

The operator authorized remediation of both security findings in
[#27](https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6539577837).
Source tests and a validation library do not constitute a deployed broker or
resolve either finding. Keep PR28 blocked until exact-source checks, independent
review and actual host/runtime verification are complete.

The broker core accepts fixed structured operations, a trusted selected-project
policy and a transport supplied by the trusted host. It does not accept URLs,
REST paths, GraphQL, shell commands, credentials or arbitrary output fields.
Scope comes from host-owned policy, not caller overrides. Mutations require an
exact request/current-evidence receipt from the trusted runtime. Receipt issuance
must preserve the automatic coordinator/reviewer workflow under standing authority;
a permanent manual approval per routine operation is not the intended system.
The core does not yet implement that issuer, authenticated parent/reviewer channel,
live transport or complete evidence-reading API. Shared native-child role strings
are not an authentication boundary.

Merge remains disabled by default. An enabled host integration guard must hold
the coordinator's integration serialization while rereading live authority,
ownership, dependencies, review, checks, target branch and exact head/base.
Ordinary GitHub protections and expected-head merge guard remain mandatory.
GitHub has no atomic expected-base merge parameter: local serialization cannot
freeze other remote actors. A detected move requires revalidation, and resulting
integration must be read back. No main/colleague merge, auto-merge, protection
bypass, deployment, ownership release or Done transition follows from a receipt.

Private durable intent precedes remote writes. Completed requests replay without
another write; changed identity conflicts. Unknown/interrupted writes block new
submissions until deliberate trusted readback, including attempts with a new ID.
Corrupt or symlinked ledger state fails closed. Raw remote errors and arbitrary
response fields must not enter model-facing responses.

Remaining runtime integration must remove GitHub credentials from the model
container and its accessible parent processes/mounts, remove the broad Symphony
GitHub dynamic tool dispatch, and move polling/gate/source acquisition into the
trusted boundary. Preserve one Symphony scheduler, the four-development-agent
cap and the 4 CPU/6 GiB aggregate budget. Separate process/mount/PID boundaries
must be verified with synthetic sentinels; environment-variable renaming alone
does not establish isolation. Complete scoped status/ownership/gate operations,
bounded readable timelines and no-PR issue handling are still required for a
usable coordinator replacement.

Test code runs only through the installed isolated-check tool. Its structured
result source and migration contract are documented in [ISOLATED-TOOL.md](ISOLATED-TOOL.md).
Do not install this foundation as an active security boundary without the remaining
implementation, adversarial host pilot, rollback/readback and independent acceptance.
