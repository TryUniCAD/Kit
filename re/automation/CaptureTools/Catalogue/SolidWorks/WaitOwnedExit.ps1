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
    $CloseRequests = 0
    $CloseError = $null
    $CloseWait = [Diagnostics.Stopwatch]::StartNew()
    if (-not $Observed -and $AllowClose) {
        for ($Request = 0; $Request -lt 2; $Request++) {
            try {
                $Process.Refresh()
                if ($Process.HasExited -or $Process.StartTime.ToUniversalTime().ToFileTimeUtc() -ne $Created -or
                    -not [OwnedFrameClose]::Request($FrameHandle, $Process.Id)) { break }
                $CloseRequests++
            } catch {
                $CloseError = $_.Exception.Message
                break
            }
            if ($Request -eq 1) { break }
            $RetryWait = [int]([Math]::Floor($CloseWaitMilliseconds / 2) - $CloseWait.ElapsedMilliseconds)
            if ($RetryWait -le 0) { break }
            $Observed = $Process.WaitForExit($RetryWait)
            if ($Observed -or $CloseWait.ElapsedMilliseconds -ge $CloseWaitMilliseconds) { break }
        }
    }
    if (-not $Observed) {
        $Remaining = [int][Math]::Max(0, $CloseWaitMilliseconds - $CloseWait.ElapsedMilliseconds)
        $Observed = $Process.WaitForExit($Remaining)
    }
    [pscustomobject]@{
        Observed = $Observed; CloseRequested = $CloseRequests -gt 0; CloseRequests = $CloseRequests; CloseError = $CloseError
    }
}
