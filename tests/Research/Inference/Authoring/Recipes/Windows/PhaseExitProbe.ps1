# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so constitutes a material breach of the license and immediately and permanently voids your rights under it.

param([Parameter(Mandatory)] [string]$HelperPath)

$ErrorActionPreference = 'Stop'
. $HelperPath
$WindowScript = @'
Add-Type -AssemblyName System.Windows.Forms
$Window = [System.Windows.Forms.Form]::new()
$Window.Text = 'Kit owned exit integration'
$Window.Opacity = 0
[System.Windows.Forms.Application]::Run($Window)
'@
$Command = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($WindowScript))
$Start = [Diagnostics.ProcessStartInfo]::new((Join-Path $PSHOME 'powershell.exe'))
$Start.Arguments = '-NoProfile -NonInteractive -STA -EncodedCommand ' + $Command
$Start.UseShellExecute = $false
$Start.CreateNoWindow = $true
$Child = [Diagnostics.Process]::Start($Start)
try {
    $Created = $Child.StartTime.ToUniversalTime().ToFileTimeUtc()
    $Deadline = [DateTime]::UtcNow.AddSeconds(15)
    do {
        $Child.Refresh()
        if ($Child.HasExited -or [DateTime]::UtcNow -ge $Deadline) { throw 'The test window did not start' }
        if ($Child.MainWindowHandle -ne [IntPtr]::Zero) { break }
        Start-Sleep -Milliseconds 50
    } while ($true)

    $Wrong = Wait-OwnedExit -Process $Child -Created ($Created + 1) -AllowClose $true -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 0
    $Failed = Wait-OwnedExit -Process $Child -Created $Created -AllowClose $false -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 0
    $Closed = Wait-OwnedExit -Process $Child -Created $Created -AllowClose $true -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 8000
    [ordered]@{
        identity_refused = -not ($Wrong.Observed -or $Wrong.CloseRequested)
        failed_phase_refused = -not ($Failed.Observed -or $Failed.CloseRequested)
        close_requested = $Closed.CloseRequested
        exit_observed = $Closed.Observed
        exit_code = if ($Closed.Observed) { $Child.ExitCode }
    } | ConvertTo-Json -Compress
} finally {
    if (-not $Child.HasExited) { $Child.Kill(); $Child.WaitForExit() }
    $Child.Dispose()
}
