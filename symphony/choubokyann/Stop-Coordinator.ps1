#requires -Version 7.0
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Process.ps1')
$name = 'symphony-choubokyann'
$owner = Invoke-BoundedProcess docker @('inspect', '--format', '{{index .Config.Labels "symphony.owner"}}', $name)
if ($owner -ne 'ChouBokYann') { throw 'Container ownership label mismatch; refusing removal.' }
$null = Invoke-BoundedProcess docker @('stop', '--time', '30', $name) 45
$null = Invoke-BoundedProcess docker @('rm', $name) 30
Write-Output 'Stopped and removed credential-bearing container. Work volume, branches and pending evidence preserved.'
