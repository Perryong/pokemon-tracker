> **Current status: source-only, live startup disabled.** The PowerShell launcher,
> container entrypoint, and generated/root workflow refuse live execution before
> starting a model. Offline installation, registration and dry-run remain available.
> The restricted broker is not yet connected to the runtime; see
> [SECURITY-BROKER.md](SECURITY-BROKER.md). Earlier live-pilot instructions below
> are historical and must not be used to reactivate the old credential-bearing path.

# Host activation verification — 2026-10-30

Gateway execution of the in-Symphony coordinator's handoff for #27; this is not product approval or a claim transfer.

- Installed the runtime under `$HOME/.symphony/choubokyann`; only Pokemon registered.
- Portable Microsoft-signed PowerShell 7.6.9 is at `$LOCALAPPDATA/Symphony/tools/PowerShell-7.6.9/pwsh.exe`. Invoke that executable when `pwsh` is not on PATH. The gateway prepends its directory to the launch process PATH so the visible log window can open; no system PATH change.
- Windows `Test-Installation.ps1`: passed both synthetic registrations, separate volumes, shared cap and unknown-ID rejection. Registry validation passed.
- Linux worker-image coordinator suite: 32 passed. Attempting the Linux suite on Windows failed because the POSIX queue lock uses fcntl; the documented Linux execution passed. No cross-platform queue implementation added.
- Live container started, startup configuration validated, dashboard responded on localhost:4000 and the visible PowerShell log process launched.
- Docker inspect confirmed 4 CPUs, 6442450944 bytes memory and equal memory-swap (no extra swap); port 4000 bound only to 127.0.0.1.
- Duplicate start was rejected. Stop removed the named credential-bearing container and preserved `symphony-choubokyann-pokemon-work`.
- Astra/high parent and Sol/high child were verified from the completed bootstrap transcripts. An idle service does not itself prove another model invocation.

The bootstrap volume/archive remains preserved. The completed setup has no unresolved product writes or ownership transfers; the same recorded coordinator session continues in the installed runtime. Only its configuration is packaged by this gateway.

Application tests were not rerun for this configuration-only change. Other real projects, private repositories, organization-owned Projects, automatic restart, simultaneous project execution and merges were not enabled or live-tested. The supported initial mode runs one selected public project at a time.


## Isolated-check tool pilot

The actual Symphony coordinator implemented the source changes; the gateway reviewed and installed the trusted host files, then returned host evidence. No repository tests run in the credential-bearing coordinator or native children.

- Built a clean test image from the pinned official Python 3.13 slim base in a context containing no repository files or credentials. Test execution is offline, nonroot, read-only, capability-free, with private PID/IPC, builtin seccomp, one read-only staged-source mount and bounded writable tmpfs. No credentials, auth mounts, host state or Docker socket enter tests.
- Coordinator and one non-agent test container each have 2 CPUs / 3 GiB / no extra swap. The one-Astra-plus-one-Sol cap remains unchanged. The host transport remains available between requests; it serializes jobs, fetches missing exact commits from the registered public origin and retains a private idempotency ledger.
- Windows registration checks passed for two synthetic projects. The host ledger ACL is restricted to the operator and Windows administration accounts. Request/result mounts are separate, with results read-only in the coordinator.
- A disposable negative-control snapshot with suite guards removed failed exactly two security tests; restoring them passed all 36 isolated tests in that snapshot.
- Live Docker initially refused local logging with max-file=1 and implicit compression. The coordinator added explicit compress=false and a regression check; the original blocked result remains preserved.
- MCP startup required explicit forwarding of the non-secret project variable. Native calls then revealed that the global never-approval policy requires scoped authorization. Only run_checks and check_status are enabled/preapproved; other tool and shell policies are unchanged.
- Native Astra job coordinator-27-9dd4f39f-acceptance-1 at source 9dd4f39fe3a1a1c3db14eb2c758b6d0b7d0da8b9 passed the boundary probe, 77 coordinator tests and 13 claim tests, with exit 0 and cleanup=true. Repeating the same ID returned the same correlated result. The runner automatically obtained that published commit.
- Synthetic nonzero job returned status=failed, exit 1 and cleanup=true. Synthetic timeout job returned status=timeout, null exit and cleanup=true at the fixed deadline; the coordinator stayed running. Earlier malformed host fixtures were rejected before execution and are not counted as these acceptance results.
- The scoped-authorization regression test is included in the final source candidate. Final exact-head result and gate reconciliation are recorded on issue #27 after publication; earlier-head results must not be represented as later-head verification.

The initial approved suite is coordinator/claim checks. Application-specific suites and dependencies must be explicitly installed before they can use this boundary. No auto-merge, deployment, boot startup, unrestricted host-shell tool or automatic replay of uncertain jobs was enabled. Isolation probes are finite checks, not proof against Docker/host compromise or malicious agent instructions. Test output is untrusted data, not an instruction or proof of application correctness by itself.
