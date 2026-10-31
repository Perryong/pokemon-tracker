#requires -Version 7.0
[CmdletBinding()]
param([string]$PythonCommand = 'python')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Process.ps1')
# Fully offline. Synthetic registrations exist only in this temporary directory.
# No gh, credentials, Docker, repository clone or model dispatch is invoked.
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
$null = New-Item -ItemType Directory -Path $temporary
try {
    $registry = Join-Path $temporary 'projects.json'
    '{"version":1,"projects":{}}' | Set-Content -LiteralPath $registry -Encoding utf8
    $plans = @()
    foreach ($id in @('synthetic-one', 'synthetic-two')) {
        $number = if ($id -eq 'synthetic-one') { 71 } else { 91 }
        $projectNumber = if ($id -eq 'synthetic-one') { 8 } else { 9 }
        $record = @{
            repo = "Example/$id"; actor = 'ChouBokYann'; project_owner = 'ChouBokYann'
            project_number = $projectNumber; control_issue = $number
            control_label = "$id-control"; queue_label = "$id-queue"
            session = "$id-session"; branch = "$id/coordinator"; excluded_issues = @()
            scope = 'Synthetic setup only'
            authority_url = "https://github.com/Example/$id/issues/$number#issuecomment-123"
        }
        $recordPath = Join-Path $temporary "$id.json"
        $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $recordPath -Encoding utf8
        $null = Invoke-BoundedProcess $PythonCommand @((Join-Path $PSScriptRoot 'registry.py'), 'register', '--registry', $registry, '--project', $id, '--record', $recordPath)
        $json = & (Join-Path $PSScriptRoot 'Start-Coordinator.ps1') -Project $id -Registry $registry -PythonCommand $PythonCommand -DryRun
        $plan = $json | ConvertFrom-Json
        if ($plan.selected.repo -ne "Example/$id" -or $plan.selected.control_issue -ne $number) { throw 'Project selection failed.' }
        if ($plan.workflow -notmatch "Example/$id" -or $plan.workflow -match 'Perryong/pokemon-tracker|#27|@@') { throw 'Workflow scope leaked.' }
        if ($plan.selected.container -ne 'symphony-choubokyann' -or $plan.selected.cpus -ne 2 -or $plan.selected.memory -ne '3g' -or $plan.selected.primary_slots -ne 1 -or $plan.selected.child_slots -ne 3) { throw 'Global cap changed.' }
        $plans += $plan
    }
    if ($plans[0].selected.volume -eq $plans[1].selected.volume) { throw 'Project storage is not isolated.' }
    $rejected = $false
    try { $null = & (Join-Path $PSScriptRoot 'Start-Coordinator.ps1') -Project missing -Registry $registry -PythonCommand $PythonCommand -DryRun }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'Unknown registration was accepted.' }
    Write-Output 'PASS: two synthetic projects selected/rendered; separate volumes; fixed shared cap; unknown project rejected. No runtime or network used.'
} finally {
    Remove-Item -LiteralPath $temporary -Recurse -Force
}
