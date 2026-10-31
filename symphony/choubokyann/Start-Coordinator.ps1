#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Project,
    [string]$Repository,
    [string]$Registry = (Join-Path $PSScriptRoot '../projects.json'),
    [string]$PythonCommand = 'python',
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
# No credential lookup or subprocess may precede this gate.
if (-not $DryRun) {
    throw 'Live coordinator startup disabled until the credential-isolated broker is integrated and verified. See SECURITY-BROKER.md.'
}
. (Join-Path $PSScriptRoot 'Process.ps1')
Invoke-BoundedProcess $PythonCommand @((Join-Path $PSScriptRoot 'machine.py'), '--registry', $Registry, '--project', $Project)
