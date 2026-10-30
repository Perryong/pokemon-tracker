#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $HOME '.symphony/choubokyann'),
    [string]$PythonCommand = 'python'
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Process.ps1')
# Install ordinary files in the current user's profile; never copy credentials,
# repository worktrees or runtime state. Existing installation needs reconciliation.
if (Test-Path -LiteralPath $InstallRoot) { throw 'Installation already exists; preserve its registry/state and reconcile before replacing runtime files.' }
$null = Invoke-BoundedProcess $PythonCommand @((Join-Path $PSScriptRoot 'registry.py'), 'validate', '--registry', (Join-Path $PSScriptRoot 'projects.json'))
$runtime = Join-Path $InstallRoot 'runtime'
$files = @('projects.json', 'coordinator.toml', 'worker.toml', 'registry.py', 'machine.py', 'queue_gate.py',
    'WORKFLOW.template.md', 'entrypoint.sh', 'Process.ps1', 'Start-Coordinator.ps1',
    'Stop-Coordinator.ps1', 'Show-Logs.ps1', 'Install-Coordinator.ps1', 'Test-Installation.ps1',
    'test_registry.py', 'test_configuration.py', 'test_multi_project.py', 'test_queue_gate.py',
    'README.md', 'MACHINE.md', 'VERIFICATION.md')
foreach ($file in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $file) -PathType Leaf)) { throw "Missing runtime file $file" }
}
$null = New-Item -ItemType Directory -Path $runtime
foreach ($file in $files) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination $runtime }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'projects.json') -Destination (Join-Path $InstallRoot 'projects.json')
Write-Output "Installed runtime at $runtime. Only Pokemon registered. No service started."
