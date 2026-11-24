# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so constitutes a material breach of the license and immediately and permanently voids your rights under it.

param(
    [Parameter(Mandatory)] [string]$HelperPath,
    [Parameter(Mandatory)] [string]$ProbeDirectory
)

$ErrorActionPreference = 'Stop'
. $HelperPath
$WindowScript = @'
Add-Type -AssemblyName System.Windows.Forms
$Window = [System.Windows.Forms.Form]::new()
$Window.Text = 'Kit owned exit integration'
$Window.Opacity = 0
if ($env:KIT_PHASE_EXIT_ACK) {
    $Window.add_FormClosing({
        param($Sender, $EventArgs)
        $EventArgs.Cancel = $true
        [IO.File]::AppendAllText($env:KIT_PHASE_EXIT_ACK, "close received`n")
    })
}
[System.Windows.Forms.Application]::Run($Window)
'@

function Get-ProbeFrame([Diagnostics.Process]$Process, [DateTime]$Deadline) {
    do {
        $Process.Refresh()
        if ($Process.HasExited -or [DateTime]::UtcNow -ge $Deadline) { throw 'The test window did not start' }
        if ($Process.MainWindowHandle -ne [IntPtr]::Zero) { return $Process.MainWindowHandle.ToInt64() }
        Start-Sleep -Milliseconds 50
    } while ($true)
}

$Command = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($WindowScript))
$Start = [Diagnostics.ProcessStartInfo]::new((Join-Path $PSHOME 'powershell.exe'))
$Start.Arguments = '-NoProfile -NonInteractive -STA -EncodedCommand ' + $Command
$Start.UseShellExecute = $false
$Start.CreateNoWindow = $true
$Start.EnvironmentVariables.Remove('KIT_PHASE_EXIT_ACK')
$Child = [Diagnostics.Process]::Start($Start)
$Peer = $null
try {
    $Ack = Join-Path $ProbeDirectory 'CloseReceived.txt'
    $Start.EnvironmentVariables['KIT_PHASE_EXIT_ACK'] = $Ack
    $Peer = [Diagnostics.Process]::Start($Start)
    $Created = $Child.StartTime.ToUniversalTime().ToFileTimeUtc()
    $PeerCreated = $Peer.StartTime.ToUniversalTime().ToFileTimeUtc()
    $FrameDeadline = [DateTime]::UtcNow.AddSeconds(15)
    $Frame = Get-ProbeFrame $Child $FrameDeadline
    $PeerFrame = Get-ProbeFrame $Peer $FrameDeadline
    $Wrong = Wait-OwnedExit -Process $Child -Created ($Created + 1) -AllowClose $true -FrameHandle $Frame -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 0
    $Failed = Wait-OwnedExit -Process $Child -Created $Created -AllowClose $false -FrameHandle $Frame -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 0
    $Missing = Wait-OwnedExit -Process $Child -Created $Created -AllowClose $true -FrameHandle 0 -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 0
    $Foreign = Wait-OwnedExit -Process $Child -Created $Created -AllowClose $true -FrameHandle $PeerFrame -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 0
    $Kept = Wait-OwnedExit -Process $Peer -Created $PeerCreated -AllowClose $true -FrameHandle $PeerFrame -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 2000
    $Closed = Wait-OwnedExit -Process $Child -Created $Created -AllowClose $true -FrameHandle $Frame -ExitWaitMilliseconds 0 -CloseWaitMilliseconds 8000
    [ordered]@{
        identity_refused = -not ($Wrong.Observed -or $Wrong.CloseRequested)
        failed_phase_refused = -not ($Failed.Observed -or $Failed.CloseRequested)
        missing_frame_refused = -not ($Missing.Observed -or $Missing.CloseRequested)
        foreign_frame_refused = -not ($Foreign.Observed -or $Foreign.CloseRequested)
        posted_without_exit = $Kept.CloseRequested -and -not $Kept.Observed -and
            (Test-Path -LiteralPath $Ack) -and [IO.File]::ReadAllLines($Ack).Length -eq 1
        close_requested = $Closed.CloseRequested
        exit_observed = $Closed.Observed
        exit_code = if ($Closed.Observed) { $Child.ExitCode }
    } | ConvertTo-Json -Compress
} finally {
    foreach ($Process in @($Peer, $Child)) {
        if ($null -eq $Process) { continue }
        try {
            if (-not $Process.HasExited) { $Process.Kill(); $null = $Process.WaitForExit(3000) }
        } finally { $Process.Dispose() }
    }
}
