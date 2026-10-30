#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Project,
    [string]$Repository,
    [string]$Registry = (Join-Path $PSScriptRoot '../projects.json'),
    [string]$PythonCommand = 'python',
    [switch]$DryRun,
    [switch]$NoLogWindow,
    [string]$CodexAuth = (Join-Path $HOME '.codex/auth.json'),
    [string]$SuperpowersSkills = (Join-Path $HOME '.agents/skills/superpowers'),
    [string]$GraphifySkills = (Join-Path $HOME '.agents/skills/graphify'),
    [ValidateRange(1024, 65535)][int]$DashboardPort = 4000
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Process.ps1')
# One fixed machine slot on this Docker daemon, never a name per project.
$name = 'symphony-choubokyann'
$image = 'pokemon-symphony:worker'
$planJson = Invoke-BoundedProcess $PythonCommand @((Join-Path $PSScriptRoot 'machine.py'), '--registry', $Registry, '--project', $Project)
$plan = $planJson | ConvertFrom-Json
$selected = $plan.selected
if ($DryRun) { Write-Output $planJson; return }
if (-not $Repository) { throw '-Repository is required for live start.' }
$registryPath = (Resolve-Path -LiteralPath $Registry).Path
$runtimePath = (Resolve-Path -LiteralPath $PSScriptRoot).Path
if ($registryPath.Contains(',') -or $runtimePath.Contains(',')) { throw 'Docker mount paths cannot contain commas.' }
$paths = @($Repository, $CodexAuth, $SuperpowersSkills, $GraphifySkills) | ForEach-Object {
    $resolved = (Resolve-Path -LiteralPath $_).Path
    if ($resolved.Contains(',')) { throw 'Docker bind mount paths cannot contain commas.' }
    $resolved
}
$repoPath, $authPath, $superpowersPath, $graphifyPath = $paths
if (-not (Test-Path -LiteralPath (Join-Path $repoPath '.git') -PathType Container)) {
    throw 'Use a normal clone as the seed; external worktree gitdirs are unsupported.'
}
$origin = Invoke-BoundedProcess git @('-C', $repoPath, 'remote', 'get-url', 'origin')
$canonicalRepo = $selected.repo
if ($origin -notin @("https://github.com/$canonicalRepo.git", "https://github.com/$canonicalRepo", "git@github.com:$canonicalRepo.git")) {
    throw 'Unregistered repository origin for the selected project.'
}
$seedBranch = Invoke-BoundedProcess git @('-C', $repoPath, 'branch', '--show-current')
if ($seedBranch -cne $selected.branch) { throw 'Seed branch does not match the registered control branch; preserve work and reconcile.' }
foreach ($file in @('coordinator.toml', 'worker.toml', 'queue_gate.py', 'registry.py', 'WORKFLOW.template.md', 'machine.py', 'entrypoint.sh')) {
    if (-not (Test-Path -LiteralPath (Join-Path $runtimePath $file) -PathType Leaf)) { throw "Missing runtime file $file" }
}
$existing = Invoke-BoundedProcess docker @('container', 'ls', '-a', '--filter', "name=^/$name`$", '--format', '{{.Names}}')
if ($existing) { throw "$name already exists. Inspect it and use Stop-Coordinator.ps1 deliberately; start never replaces it." }
$null = Invoke-BoundedProcess docker @('image', 'inspect', $image, '--format', '{{.Id}}')
$oldToken = $env:GH_TOKEN
$oldQueueToken = $env:SYMPHONY_QUEUE_TOKEN
$oldProject = $env:SYMPHONY_PROJECT
$oldRegistry = $env:SYMPHONY_REGISTRY
try {
    # Existing CLI credential, environment only. Never persist or print this value.
    if (-not $env:GH_TOKEN) { $env:GH_TOKEN = Invoke-BoundedProcess gh @('auth', 'token', '--hostname', 'github.com') }
    if (-not $env:GH_TOKEN) { throw 'An existing GitHub CLI token is required.' }
    # Symphony strips tracker token names from app-server. This intentional copy
    # enables gh read APIs for explicit acknowledgement; it is NOT isolation.
    $env:SYMPHONY_QUEUE_TOKEN = $env:GH_TOKEN
    $env:SYMPHONY_PROJECT = $Project
    $env:SYMPHONY_REGISTRY = '/config/projects.json'
    $argsList = @(
        'create', '--name', $name, '--label', 'symphony.owner=ChouBokYann',
        '--label', "symphony.project=$Project", '--restart', 'no', '--init', '--security-opt', 'seccomp=unconfined',
        '--cpus', '4', '--memory', '6g', '--memory-swap', '6g',
        '--env', 'GH_TOKEN', '--env', 'SYMPHONY_QUEUE_TOKEN',
        '--env', 'SYMPHONY_PROJECT', '--env', 'SYMPHONY_REGISTRY',
        '--publish', "127.0.0.1:${DashboardPort}:4000",
        '--mount', "type=volume,source=$($selected.volume),target=/work",
        '--mount', "type=bind,source=$repoPath,target=/seed,readonly",
        '--mount', "type=bind,source=$runtimePath,target=/runtime,readonly",
        '--mount', "type=bind,source=$registryPath,target=/config/projects.json,readonly",
        '--mount', "type=bind,source=$runtimePath/coordinator.toml,target=/root/.codex/config.toml,readonly",
        '--mount', "type=bind,source=$authPath,target=/root/.codex/auth.json,readonly",
        '--mount', "type=bind,source=$superpowersPath,target=/opt/skills/superpowers,readonly",
        '--mount', "type=bind,source=$graphifyPath,target=/opt/skills/graphify,readonly",
        '--entrypoint', '/bin/sh', $image, '/runtime/entrypoint.sh'
    )
    $null = Invoke-BoundedProcess docker $argsList 60
    $null = Invoke-BoundedProcess docker @('start', $name) 30
    Write-Output "Started $name; inspect startup validation and model metadata before authorizing work. Dashboard: http://localhost:$DashboardPort"
} finally {
    $env:GH_TOKEN = $oldToken
    $env:SYMPHONY_QUEUE_TOKEN = $oldQueueToken
    $env:SYMPHONY_PROJECT = $oldProject
    $env:SYMPHONY_REGISTRY = $oldRegistry
}

# Log viewers must not inherit the temporary credential copies created above.
if (-not $NoLogWindow) {
    # A visible host terminal streams the foreground Elixir/Symphony logs.
    # Closing it only detaches logs; Stop-Coordinator.ps1 stops the service.
    try {
        $null = Start-Process pwsh -ArgumentList @('-NoExit', '-File', "`"$PSScriptRoot/Show-Logs.ps1`"", '-Follow') -PassThru
    } catch { Write-Warning 'Runtime started, but log terminal failed. Run Show-Logs.ps1 -Follow in a visible terminal.' }
}
