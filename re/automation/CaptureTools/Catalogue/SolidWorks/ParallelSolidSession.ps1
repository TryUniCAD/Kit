# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

function Get-ParallelSolidLeaseName([string]$Group, [int]$ProcessId, [long]$Created) {
    return "Local\KitResearchSolidWorks-$Group-$ProcessId-$Created"
}

function Confirm-ParallelSolidPeer([string]$Group, [Diagnostics.Process]$Process) {
    if ($Process.HasExited) { return $false }
    try {
        $Created = $Process.StartTime.ToUniversalTime().ToFileTimeUtc()
        $Name = Get-ParallelSolidLeaseName $Group $Process.Id $Created
        $Lease = [Threading.Mutex]::OpenExisting($Name)
    } catch [Threading.WaitHandleCannotBeOpenedException] {
        if ($Process.HasExited) { return $false }
        throw 'Preserve the existing SOLIDWORKS session outside this catalogue run.'
    } catch {
        if ($Process.HasExited) { return $false }
        throw
    }
    try {
        try { $Available = $Lease.WaitOne(0) } catch [Threading.AbandonedMutexException] { $Available = $true }
        if ($Available) {
            $Lease.ReleaseMutex()
            if ($Process.HasExited) { return $false }
            throw 'The existing SOLIDWORKS process lost its catalogue lease.'
        }
        return $true
    } finally { $Lease.Dispose() }
}

function Get-ParallelSolidPeers([string]$Group, [int]$SkipId = 0) {
    foreach ($Peer in Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) {
        try {
            if ($Peer.Id -ne $SkipId -and (Confirm-ParallelSolidPeer $Group $Peer)) {
                $Peer.Id
            }
        } finally { $Peer.Dispose() }
    }
}
