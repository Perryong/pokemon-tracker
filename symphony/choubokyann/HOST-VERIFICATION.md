# Host activation verification — 2026-10-30

Gateway execution of the in-Symphony coordinator's handoff for #27; this is not product approval or a claim transfer.

- Installed the runtime under `C:/Users/maker/.symphony/choubokyann`; only Pokemon registered.
- Portable Microsoft-signed PowerShell 7.6.9 is at `C:/Users/maker/AppData/Local/Symphony/tools/PowerShell-7.6.9/pwsh.exe`. Invoke that executable when `pwsh` is not on PATH. The gateway prepends its directory to the launch process PATH so the visible log window can open; no system PATH change.
- Windows `Test-Installation.ps1`: passed both synthetic registrations, separate volumes, shared cap and unknown-ID rejection. Registry validation passed.
- Linux worker-image coordinator suite: 32 passed. Attempting the Linux suite on Windows failed because the POSIX queue lock uses fcntl; the documented Linux execution passed. No cross-platform queue implementation added.
- Live container started, startup configuration validated, dashboard responded on localhost:4000 and the visible PowerShell log process launched.
- Docker inspect confirmed 4 CPUs, 6442450944 bytes memory and equal memory-swap (no extra swap); port 4000 bound only to 127.0.0.1.
- Duplicate start was rejected. Stop removed the named credential-bearing container and preserved `symphony-choubokyann-pokemon-work`.
- Astra/high parent and Sol/high child were verified from the completed bootstrap transcripts. An idle service does not itself prove another model invocation.

The bootstrap volume/archive remains preserved. The completed setup has no unresolved product writes or ownership transfers; the same recorded coordinator session continues in the installed runtime. Only its configuration is packaged by this gateway.

Application tests were not rerun for this configuration-only change. Other real projects, private repositories, organization-owned Projects, automatic restart, simultaneous project execution and merges were not enabled or live-tested. The supported initial mode runs one selected public project at a time.
