#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Repository,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{40}$')][string]$Commit,
    [Parameter(Mandatory)][ValidatePattern('^sha256:[0-9a-f]{64}$')][string]$ReviewedImageId,
    [Parameter(Mandatory)][string]$EvidenceDirectory,
    [string[]]$CommandArgv = @(),
    [ValidateRange(10, 1800)][int]$TimeoutSeconds = 300,
    [string]$PythonCommand = 'python3'
)
$ErrorActionPreference = 'Stop'
# This trusted host script must be reviewed and copied outside the PR checkout.
# No dot-sourcing, hooks, builds, package install, checkout, or repository imports.
function Invoke-HostProcess {
    param([string]$File, [string[]]$Arguments, [int]$Seconds = 30, [switch]$IncludeStandardError)
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $File
    $info.UseShellExecute = $false
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    try {
        if (-not $process.Start()) { throw 'Host tool did not start.' }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($Seconds * 1000)) {
            $process.Kill($true)
            throw 'Host operation timed out; cleanup and reconcile before retrying.'
        }
        $text = $stdout.GetAwaiter().GetResult()
        $errorText = $stderr.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) { throw 'Host operation failed; no execution authorized.' }
        if ($IncludeStandardError) { return ($text + $errorText).Trim() }
        return $text.Trim()
    } finally { $process.Dispose() }
}
$name = 'symphony-choubokyann'
$runId = [Guid]::NewGuid().ToString('N')
$containerId = $null
$createdAttempted = $false
$stage = Join-Path ([IO.Path]::GetTempPath()) "isolated-check-$runId"
$evidence = [IO.Path]::GetFullPath($EvidenceDirectory)
if (Test-Path -LiteralPath $evidence) { throw 'EvidenceDirectory must be new.' }
$repo = (Resolve-Path -LiteralPath $Repository).Path
if ($repo.Contains(',') -or $stage.Contains(',')) { throw 'Unsupported mount path.' }
$existing = Invoke-HostProcess docker @('container', 'ls', '-a', '--filter', "name=^/$name`$", '--format', '{{.ID}}')
if ($existing) { throw 'Fixed runtime slot is occupied. Stop/reconcile it deliberately before this pilot.' }
$daemonSecurity = (Invoke-HostProcess docker @('info', '--format', '{{json .SecurityOptions}}')) | ConvertFrom-Json
if (@($daemonSecurity) -cnotcontains 'name=seccomp,profile=builtin') {
    throw 'Docker daemon must report the builtin seccomp profile before this pilot.'
}
$image = (Invoke-HostProcess docker @('image', 'inspect', $ReviewedImageId)) | ConvertFrom-Json
if (@($image).Count -ne 1 -or $image.Id -cne $ReviewedImageId) { throw 'Image identity mismatch.' }
if ($image.Config.Volumes -or $image.Config.Entrypoint -or $image.Config.Cmd -or $image.Config.OnBuild) {
    throw 'Reviewed image must have no volumes, entrypoint, command or on-build hooks.'
}
$allowedImageEnv = @('PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin', 'LANG=C.UTF-8')
foreach ($entry in @($image.Config.Env)) {
    if ($entry -and $entry -cnotin $allowedImageEnv) { throw 'Image environment is outside the reviewed allowlist.' }
}
$resolved = Invoke-HostProcess git @('--no-replace-objects', '-C', $repo, 'rev-parse', '--verify', "$Commit^{commit}")
if ($resolved -cne $Commit) { throw 'Exact commit is unavailable.' }
$null = New-Item -ItemType Directory -Path $stage
$null = New-Item -ItemType Directory -Path $evidence
$sentinel = Join-Path ([IO.Path]::GetTempPath()) "outside-source-$runId"
$oldSentinel = $env:ISOLATION_PARENT_SENTINEL
$exitCode = $null
$archiveSha = $null
try {
    [IO.File]::WriteAllText($sentinel, 'SYNTHETIC-NOT-A-CREDENTIAL')
    $env:ISOLATION_PARENT_SENTINEL = 'SYNTHETIC-NOT-A-CREDENTIAL'
    $archive = Join-Path $stage 'source.tar'
    $null = Invoke-HostProcess git @('--no-replace-objects', '-C', $repo, '-c', 'core.hooksPath=/dev/null', 'archive', '--format=tar', "--output=$archive", $Commit)
    # Trusted parser reads headers only; never extracts untrusted source on host.
    $probe = Join-Path $PSScriptRoot 'isolation_probe.py'
    $null = Invoke-HostProcess $PythonCommand @('-I', $probe, '--validate', $archive)
    $archiveSha = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    Copy-Item -LiteralPath $probe -Destination (Join-Path $stage 'probe.py')
    @{ sentinel_path = $sentinel.Replace('\', '/'); host_pid = $PID; argv = @($CommandArgv) } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stage 'job.json') -Encoding utf8NoBOM
    $createArgs = @(
        'create', '--name', $name, '--label', "isolation.run=$runId", '--restart', 'no', '--no-healthcheck',
        '--cpus', '4', '--memory', '6g', '--memory-swap', '6g', '--pids-limit', '128',
        # Omitted --pid selects Docker's private PID namespace; 'private' is not a valid CLI value.
        '--network', 'none', '--ipc', 'private', '--user', '65534:65534',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges=true', '--read-only',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m,mode=1777',
        '--tmpfs', '/work:rw,nosuid,nodev,size=1g,mode=1777',
        '--log-driver', 'local', '--log-opt', 'max-size=8m', '--log-opt', 'max-file=1',
        '--mount', "type=bind,source=$stage,target=/input,readonly",
        '--entrypoint', '/bin/sh', $ReviewedImageId, '-c',
        'exec /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp LANG=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 python3 -I /input/probe.py --run /input/job.json'
    )
    $createdAttempted = $true
    $containerId = Invoke-HostProcess docker $createArgs
    if ($containerId -notmatch '^[0-9a-f]{64}$') { throw 'Uncertain container create outcome.' }
    # Docker inspect is trusted daemon state; do not save full process environment.
    $state = (Invoke-HostProcess docker @('container', 'inspect', $containerId)) | ConvertFrom-Json
    $h = $state.HostConfig
    $requestedMount = @($h.Mounts | Where-Object { $_.Target -ceq '/input' })
    if ($h.NetworkMode -cne 'none' -or $h.PidMode -cne '' -or $h.IpcMode -cne 'private' -or
        -not $h.ReadonlyRootfs -or $h.Privileged -or $state.Config.User -cne '65534:65534' -or
        $h.NanoCpus -ne 4000000000 -or $h.Memory -ne 6442450944 -or $h.MemorySwap -ne 6442450944 -or $h.PidsLimit -ne 128 -or
        $h.CapAdd -or $h.Devices -or $h.DeviceRequests -or
        @($state.Config.Healthcheck.Test).Count -ne 1 -or $state.Config.Healthcheck.Test[0] -cne 'NONE' -or
        $h.Tmpfs.'/tmp' -cne 'rw,nosuid,nodev,size=128m,mode=1777' -or
        $h.Tmpfs.'/work' -cne 'rw,nosuid,nodev,size=1g,mode=1777' -or
        @($h.Tmpfs.PSObject.Properties).Count -ne 2 -or
        $requestedMount.Count -ne 1 -or $requestedMount[0].Source -cne $stage -or
        @($h.Mounts).Count -ne 1 -or
        @($state.Mounts | Where-Object { $_.Type -eq 'bind' -and ($_.RW -or $_.Destination -cne '/input') }).Count -ne 0 -or
        @($state.Mounts | Where-Object { $_.Type -eq 'bind' }).Count -ne 1 -or
        @($state.Mounts | Where-Object { $_.Type -notin @('bind', 'tmpfs') }).Count -ne 0 -or
        @($state.Mounts | Where-Object { $_.Type -eq 'tmpfs' -and $_.Destination -notin @('/tmp', '/work') }).Count -ne 0 -or
        ($h.PortBindings -and @($h.PortBindings.PSObject.Properties).Count -ne 0) -or
        @($h.CapDrop) -cnotcontains 'ALL' -or @($h.SecurityOpt) -cnotcontains 'no-new-privileges=true' -or
        @($h.SecurityOpt | Where-Object { $_ -like '*unconfined*' }).Count -ne 0) {
        throw 'Docker boundary configuration mismatch; container will not start.'
    }
    @{ container_id = $containerId; network = $h.NetworkMode; pid = $h.PidMode;
       readonly_root = $h.ReadonlyRootfs; user = $state.Config.User; cpus = 4; memory_bytes = $h.Memory;
       memory_swap_bytes = $h.MemorySwap; ipc = $h.IpcMode;
       pids_limit = $h.PidsLimit; cap_drop = $h.CapDrop; security = $h.SecurityOpt;
       seccomp_daemon = $daemonSecurity; mount_destinations = @($state.Mounts.Destination);
       tmpfs = $h.Tmpfs; healthcheck = $state.Config.Healthcheck.Test } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidence 'boundary.json') -Encoding utf8NoBOM
    $null = Invoke-HostProcess docker @('start', $containerId)
    $waitResult = Invoke-HostProcess docker @('wait', $containerId) $TimeoutSeconds
    if ($waitResult -notmatch '^\d+$') { throw 'Invalid container exit result.' }
    $exitCode = [int]$waitResult
} finally {
    # Recover uncertain create only by exact per-run ownership label, never name alone.
    if ($createdAttempted -and -not $containerId) {
        try {
            $owned = (Invoke-HostProcess docker @('container', 'inspect', $name)) | ConvertFrom-Json
            if ($owned.Config.Labels.'isolation.run' -ceq $runId) { $containerId = $owned.Id }
        } catch { Write-Warning 'Create outcome uncertain; inspect fixed slot before retrying.' }
    }
    try {
      try {
       if ($containerId -match '^[0-9a-f]{64}$') {
        try {
            # Captured text is untrusted data. Never print or execute it in the agent runtime.
            $logs = Invoke-HostProcess docker @('logs', $containerId) -IncludeStandardError
            [IO.File]::WriteAllText((Join-Path $evidence 'untrusted-output.log'), $logs)
        } finally { $null = Invoke-HostProcess docker @('rm', '--force', $containerId) }
       }
      } finally {
      @{ commit = $Commit; source_tar_sha256 = $archiveSha; image_id = $ReviewedImageId;
       argv = @($CommandArgv); run_id = $runId; exit_code = $exitCode;
       result = $(if ($exitCode -ceq 0) { 'container-exit-zero-untrusted' } else { 'failed-or-incomplete' }) } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidence 'result.json') -Encoding utf8NoBOM
      }
    } finally {
    $env:ISOLATION_PARENT_SENTINEL = $oldSentinel
    Remove-Item -LiteralPath $sentinel -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    }
}
if ($exitCode -cne 0) { throw 'Isolated checks failed or incomplete; inspect inert evidence manually.' }
Write-Output 'Container exited zero. Evidence remains untrusted; operator review is required.'
