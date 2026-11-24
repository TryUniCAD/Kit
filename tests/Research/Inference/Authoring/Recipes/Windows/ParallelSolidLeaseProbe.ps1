# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

param(
    [Parameter(Mandatory)] [string]$Helper,
    [Parameter(Mandatory)] [string]$Workspace,
    [ValidateSet('check', 'hold')] [string]$Mode = 'check',
    [string]$LeaseName
)

$ErrorActionPreference = 'Stop'
. $Helper
$Ready = Join-Path $Workspace 'ready.txt'
$Release = Join-Path $Workspace 'release.txt'
if ($Mode -eq 'hold') {
    $Created = $false
    $Lease = [Threading.Mutex]::new($true, $LeaseName, [ref]$Created)
    if (-not $Created) { throw 'Expected a fresh peer mutex' }
    try {
        [IO.File]::WriteAllText($Ready, 'ready')
        $Deadline = [DateTime]::UtcNow.AddSeconds(25)
        while (-not [IO.File]::Exists($Release)) {
            if ([DateTime]::UtcNow -gt $Deadline) { throw 'Timed out awaiting release' }
            Start-Sleep -Milliseconds 50
        }
    } finally {
        $Lease.ReleaseMutex()
        $Lease.Dispose()
    }
    return
}

function Assert-Refused([string]$Group, [Diagnostics.Process]$Peer) {
    try { [void](Confirm-ParallelSolidPeer $Group $Peer) }
    catch {
        if ($_.Exception.Message -like 'Preserve the existing SOLIDWORKS session*' -or
            $_.Exception.Message -like 'The existing SOLIDWORKS process lost its catalogue lease*') { return }
        throw
    }
    throw 'The catalogue accepted a process without its live group lease'
}

$Peer = [Diagnostics.Process]::GetCurrentProcess()
$Group = [Guid]::NewGuid().ToString('N')
$ForeignGroup = [Guid]::NewGuid().ToString('N')
$Name = Get-ParallelSolidLeaseName $Group $Peer.Id ($Peer.StartTime.ToUniversalTime().ToFileTimeUtc())
$Arguments = '-NoProfile -NonInteractive -File "{0}" -Helper "{1}" -Workspace "{2}" -Mode hold -LeaseName "{3}"' -f $PSCommandPath, $Helper, $Workspace, $Name
$Owner = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $Arguments -WindowStyle Hidden -PassThru
try {
    $Deadline = [DateTime]::UtcNow.AddSeconds(15)
    while (-not [IO.File]::Exists($Ready)) {
        if ($Owner.HasExited -or [DateTime]::UtcNow -gt $Deadline) { throw 'The lease holder did not start' }
        Start-Sleep -Milliseconds 50
    }
    $OpenLease = [Threading.Mutex]::OpenExisting($Name)
    try {
        if (-not (Confirm-ParallelSolidPeer $Group $Peer)) { throw 'The same-run holder did not pass' }
        Assert-Refused $ForeignGroup $Peer
        [IO.File]::WriteAllText($Release, 'release')
        if (-not $Owner.WaitForExit(10000) -or $Owner.ExitCode -ne 0) { throw 'The lease holder did not exit normally' }
        Assert-Refused $Group $Peer
    } finally { $OpenLease.Dispose() }
    Assert-Refused $Group $Peer
    Write-Output 'same run accepted, foreign and expired owners refused'
} finally {
    if (-not $Owner.HasExited) { $Owner.Kill(); $Owner.WaitForExit() }
    $Owner.Dispose()
    $Peer.Dispose()
}
