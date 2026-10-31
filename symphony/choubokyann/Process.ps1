# Requires PowerShell 7: ArgumentList avoids shell interpolation and quoting.
function Invoke-BoundedProcess {
    param([string]$File, [string[]]$Arguments, [int]$Seconds = 30, [switch]$IncludeStandardError)
    $info = [System.Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $File
    $info.UseShellExecute = $false
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $info
    try {
        if (-not $process.Start()) { throw 'Process did not start.' }
        $out = $process.StandardOutput.ReadToEndAsync()
        $err = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($Seconds * 1000)) {
            $process.Kill($true)
            throw "Timed out running $File; inspect state before retrying."
        }
        # Do not echo arguments or stderr: a credential command may contain secrets.
        $output = $out.GetAwaiter().GetResult()
        $errorOutput = $err.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) { throw "$File failed (exit $($process.ExitCode)); inspect state before retrying." }
        if ($IncludeStandardError) { return ($output + $errorOutput).Trim() }
        return $output.Trim()
    } finally { $process.Dispose() }
}
