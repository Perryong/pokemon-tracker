> Current execution path: [ISOLATED-TOOL.md](ISOLATED-TOOL.md). Operator extension in #27 permits one 2 CPU/3 GiB test container alongside the 2 CPU/3 GiB coordinator, within 4 CPU/6 GiB aggregate. Earlier same-slot manual-pilot instructions below are historical and superseded; no test execution in coordinator/children.

# Offline isolation pilot — prepared, not executed

These artifacts have had source review only. No host pilot, container start,
red/green test run, or isolation pass is claimed. Keep the credentialed coordinator
restricted to source inspection until an operator completes and reviews this pilot.
This is one ephemeral use of the existing `symphony-choubokyann` slot, with four
CPUs and six GiB. It adds no service, scheduler, or parallel coordinator.

## Trusted host prerequisites

Use PowerShell 7, a reviewed host Python 3.12+, trusted Git, and a Linux Docker
daemon reporting builtin seccomp. Review this wrapper and probe independently,
then copy them to a trusted directory outside any PR checkout. Never execute a
wrapper or probe taken directly from an unreviewed PR. Source preparation uses
`git archive` of the exact supplied commit; it neither checks it out nor imports
its modules on the host. The trusted parser rejects traversal, links, devices,
metadata/auth/workpad paths, duplicate names and oversized archives. All links
are rejected, including otherwise legitimate repository symlinks.

Supply an already local, independently audited immutable image ID. The wrapper
never pulls, builds or installs. A normal Python base image will be rejected:
its default command and additional environment entries do not meet this pilot's
strict configuration contract. Before this pilot, an operator must prepare a
separate credential-free image containing Python 3.12+, `/bin/sh`, `/usr/bin/env`,
and all offline dependencies. Audit its filesystem/layers and provenance, not
just `docker image inspect`: config inspection cannot prove the layers contain
no credentials. Do not derive it from the authenticated coordinator image.

One concrete preparation route is a reviewed credential-free root filesystem
archive imported with `docker image import reviewed-rootfs.tar pilot-offline` on
the uncredentialed host. Import resets image metadata; inspect it and require
empty `Config.Env`, `Config.Cmd`, `Config.Entrypoint`, `Config.Volumes` and
`Config.OnBuild`. Save its resulting `sha256:...` ID and audit record. The wrapper
also permits precisely the standard PATH and `LANG=C.UTF-8` environment entries,
and no others. This host preparation is a separate manual prerequisite, never an
automatic fallback. Missing offline dependencies fail the check; resolve them in
a separately reviewed image before repeating with a new recorded image ID.

Alternatively, an operator can review this tiny Dockerfile outside the checkout,
replace the digest with an independently reviewed Python base digest, explicitly
prepare it once on the uncredentialed host, and audit the resulting image ID:

```dockerfile
FROM python:3.13-slim@sha256:REPLACE_WITH_REVIEWED_BASE_DIGEST AS runtime
FROM scratch
COPY --from=runtime / /
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8
```

The scratch stage inherits no command/entrypoint/volume metadata, and copies no
repository data. Any base acquisition/build is an explicit host preparation step,
not part of this pilot wrapper. The ID and filesystem/provenance still need audit.

## Sentinel-only first run

Stop the credential-bearing runtime deliberately and verify it is removed by its
existing stop/reconciliation procedure. The pilot refuses any existing fixed-name
container, including a stopped one, and never removes it. Use an uncredentialed
host session and a synthetic source repository containing no real credentials.
Do not pass actual tokens as sentinels. The wrapper creates only a synthetic parent
environment marker and a synthetic file outside the sole source mount.

```powershell
# Run only after independent source/image review and deliberate runtime shutdown.
$trusted = 'C:\TrustedTools\isolated-checks'
$repo = 'C:\Scratch\synthetic-source'
$sha = 'REPLACE_WITH_EXACT_40_LOWERCASE_HEX_COMMIT'
$image = 'sha256:REPLACE_WITH_REVIEWED_64_LOWERCASE_HEX_IMAGE_ID'
$evidence = 'C:\IsolationEvidence\sentinel-first-unique-run'
$argv = @('python3', '-c', 'print("SYNTHETIC_PAYLOAD_OK")')
& "$trusted\Invoke-IsolatedChecks.ps1" -Repository $repo -Commit $sha `
    -ReviewedImageId $image -EvidenceDirectory $evidence -CommandArgv $argv
```

The optional argv is serialized as JSON into the input mount and passed directly
to `subprocess.run`, never interpolated into shell code. The static entrypoint
uses `env -i` with PATH/HOME/LANG/PYTHONDONTWRITEBYTECODE only. With no explicit
argv, the default runs both coordinator unittest discovery and signed-claim
unittest discovery. An explicit argv replaces those defaults; for product work,
use the issue's concrete acceptance command and an image with its offline tools.
There is no dependency download/install fallback.

The probe checks parent marker absence, the host sentinel via direct and proc-root
paths, known auth/config paths, host-process environment visibility, Docker sockets,
and external/host-bridge connections. It prints labels only, never sentinel values.
Docker private PID/network namespaces and the inspected configuration supply the
primary boundary evidence. A Windows host PID can coincidentally match a Linux
container PID, causing a conservative false failure; a Windows file path is also
not a Linux VM host-path identity. Treat these as probe limitations requiring
operator analysis, never weaken the boundary or reinterpret failure as a pass.
These probes are finite checks and do not prove resistance to container escape.
The readable-sentinel unit test is a negative control for the probe's failure
branch. Run it inside the approved boundary; it needs no unsafe-container switch.
Docker Desktop may translate the effective bind source path. The wrapper checks
the original `HostConfig.Mounts` request source against the staging directory,
plus effective destination/type/readonly state. If the request source itself is
normalized, it conservatively refuses; reconcile that mapping through review.

## Functional checks and evidence

After the sentinel run succeeds and its manifest is reviewed, use a fresh evidence
directory and the exact review-head commit for the coordinator/claim checks:

```powershell
& "$trusted\Invoke-IsolatedChecks.ps1" -Repository 'C:\Repos\pokemon-tracker' `
    -Commit $sha -ReviewedImageId $image -EvidenceDirectory 'C:\IsolationEvidence\runtime-unique-run'
```

The new archive boundary tests are included by default discovery only when present
in that exact commit. Their first red/green execution remains outstanding. Required
commands are `python3 -m unittest discover -s symphony/choubokyann -p 'test_*.py'`
and `python3 -m unittest discover -s .github/scripts -p test_issue_claim.py`.

The current handoff is an uncommitted patch based on PR #28 head
`b3c375fe68190d0b7c447081e9371c722fcb0067`. Preserve the existing checkout and
review/apply the handoff in the approved control branch. Create a local candidate
commit with hooks disabled after source review, before selecting `$sha`; no push,
merge or passing-test assertion is implied. The old PR SHA does not include these
new tests. Copy the reviewed wrapper/probe into `$trusted` separately and record
their SHA-256 hashes as part of the tool audit. Do not install the runtime update
or overwrite the registration/work volume yet.

Run these failure cases using the synthetic repository and a fresh evidence path
for each invocation. Catch the expected error at the host and inspect the result;
an error alone is insufficient evidence of successful cleanup:

```powershell
# Nonzero payload must log CHECK_FAIL with exit=7, record container exit 1, and fail.
& "$trusted\Invoke-IsolatedChecks.ps1" -Repository $repo -Commit $sha `
    -ReviewedImageId $image -EvidenceDirectory 'C:\IsolationEvidence\exit-seven' `
    -CommandArgv @('python3', '-c', 'raise SystemExit(7)')
# Timeout must fail, leave exit_code null, and remove only its own container.
& "$trusted\Invoke-IsolatedChecks.ps1" -Repository $repo -Commit $sha `
    -ReviewedImageId $image -EvidenceDirectory 'C:\IsolationEvidence\timeout' `
    -TimeoutSeconds 10 -CommandArgv @('python3', '-c', 'import time; time.sleep(120)')
docker container ls -a --filter 'name=^/symphony-choubokyann$' --format '{{.ID}}'
```

The default suites include negative controls that deliberately make a synthetic
sentinel readable and inherit the synthetic parent marker, expecting the actual
boundary function to reject each before repository execution. For occupied-slot
refusal, use only a stopped synthetic container in this same slot, capture its ID,
invoke the wrapper, and verify that the same container remains untouched; remove
that captured synthetic ID deliberately. Never use the active coordinator as a
disposable test fixture. Also verify the project work volume still exists after
the pilot; it must never be mounted into or removed by this wrapper.

Record exact commit, image ID/audit, `source_tar_sha256`, JSON argv, timeout,
container exit, actual test counts/failures and operator interpretation. The host
writes safe `boundary.json`, `result.json` and bounded `untrusted-output.log` files.
The log combines stdout and stderr without preserving stream ordering. Treat all
test output and a zero exit as untrusted claims: a malicious PR can forge its own
test output. Never paste logs into an agent instruction channel or execute their
contents; review inert files outside the credentialed runtime. No source artifacts
or generated files are copied back. A host timeout triggers cleanup of only this
run's verified container ID. Cleanup failure or uncertain create outcome requires
manual slot reconciliation before any restart; no automatic coordinator restart.

The container has no forwarded environment/auth, host socket, shared PID namespace,
ports or network; no extra volumes; readonly root/input; bounded `/tmp` and `/work`
tmpfs; nonroot UID; dropped capabilities; no-new-privileges; builtin seccomp;
disabled healthcheck; 128 PID limit; fixed 4 CPU/6 GiB limits. Effective state is
checked before start. Image-layer trust and Docker/host trust remain prerequisites.
Flag semantics reference: [Docker run documentation](https://docs.docker.com/engine/containers/run/).
Documentation is not evidence that this host actually enforces the boundary.

Remaining host work: independently review artifacts and image, run sentinel pilot,
run failing-then-passing archive tests inside that boundary, run exact-head required
suites, inspect effective manifests and cleanup, and record actual evidence. Do not
restore repository execution to the coordinator merely because these files exist.
