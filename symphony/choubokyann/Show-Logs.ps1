#requires -Version 7.0
[CmdletBinding()]
param([switch]$Follow, [ValidateRange(1, 1000)][int]$Tail = 100)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Process.ps1')
$name = 'symphony-choubokyann'
$owner = Invoke-BoundedProcess docker @('inspect', '--format', '{{index .Config.Labels "symphony.owner"}}', $name)
if ($owner -ne 'ChouBokYann') { throw 'Container ownership label mismatch.' }
if ($Follow) {
    # Deliberately interactive; Ctrl-C detaches the log viewer, not Symphony.
    & docker logs --follow --tail $Tail $name
    if ($LASTEXITCODE -ne 0) { throw 'Docker log stream ended with an error.' }
} else {
    Write-Output (Invoke-BoundedProcess docker @('logs', '--tail', "$Tail", $name) -IncludeStandardError)
}
