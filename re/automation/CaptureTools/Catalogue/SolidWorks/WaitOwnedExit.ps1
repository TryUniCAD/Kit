# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the PolyForm Strict License 1.0.0.

Add-Type -Path (Join-Path $PSScriptRoot 'OwnedFrameClose.cs')

function Wait-OwnedExit {
    param(
        [Parameter(Mandatory)] [Diagnostics.Process]$Process,
        [Parameter(Mandatory)] [long]$Created,
        [Parameter(Mandatory)] [bool]$AllowClose,
        [long]$FrameHandle = 0,
        [int]$ExitWaitMilliseconds = 10000,
        [int]$CloseWaitMilliseconds = 20000
    )

    $Observed = $Process.WaitForExit($ExitWaitMilliseconds)
    $CloseRequested = $false
    $CloseError = $null
    if (-not $Observed -and $AllowClose) {
        try {
            $Process.Refresh()
            if (-not $Process.HasExited -and $Process.StartTime.ToUniversalTime().ToFileTimeUtc() -eq $Created) {
                $CloseRequested = [OwnedFrameClose]::Request($FrameHandle, $Process.Id)
            }
        } catch { $CloseError = $_.Exception.Message }
    }
    if (-not $Observed) { $Observed = $Process.WaitForExit($CloseWaitMilliseconds) }
    [pscustomobject]@{ Observed = $Observed; CloseRequested = $CloseRequested; CloseError = $CloseError }
}
