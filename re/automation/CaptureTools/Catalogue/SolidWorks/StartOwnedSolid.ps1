# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
function Start-OwnedSolid {
    param($Executable, [string]$Destination, [string]$Phase)
    $Attempts = [Collections.Generic.List[object]]::new()
    $Total = [Diagnostics.Stopwatch]::StartNew()
    try {
        for ($Attempt = 1; $Attempt -le 3; $Attempt++) {
            if (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) {
                throw 'Preserve the existing SOLIDWORKS session and use an idle native host.'
            }
            $Native = $null
            $Created = $null
            $Record = [ordered]@{ attempt = $Attempt; ready = $false }
            $Elapsed = [Diagnostics.Stopwatch]::StartNew()
            try {
                $Native = Start-Process -FilePath $Executable.FullName -WorkingDirectory $Executable.DirectoryName -WindowStyle Hidden -PassThru
                $Created = $Native.StartTime.ToUniversalTime().ToFileTimeUtc()
                $Record.pid = $Native.Id
                $Record.created = $Created
                [IO.Directory]::CreateDirectory($Destination) | Out-Null
                [IO.File]::AppendAllText((Join-Path $Destination ($Phase + '-startup.jsonl')),
                    (($Record | ConvertTo-Json -Compress) + [Environment]::NewLine), [Text.UTF8Encoding]::new($false))
                if (@(Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue).Count -ne 1) {
                    throw 'The application identity changed before authoring.'
                }
                [SolidOwner]::CheckReady($Native, $Executable.FullName)
                $Record.ready = $true
                return $Native
            } catch {
                $Record.error = $_.Exception.ToString()
                if ($null -ne $Native) {
                    try {
                        if (-not $Native.HasExited) {
                            if ($null -eq $Created -or $Native.StartTime.ToUniversalTime().ToFileTimeUtc() -ne $Created) {
                                throw 'Cannot prove ownership of the failed startup process.'
                            }
                            $Native.Kill()
                            $Record.forced_owned_cleanup = $true
                        }
                        $Record.owned_process_exit_observed = $Native.WaitForExit(10000)
                        if (-not $Record.owned_process_exit_observed) { throw 'Failed startup process did not exit.' }
                    } finally { $Native.Dispose() }
                }
                if ($Attempt -eq 3) { throw }
                Write-Host "SOLIDWORKS startup attempt $Attempt failed; retrying"
                Start-Sleep -Milliseconds 1000
            } finally {
                $Record.seconds = $Elapsed.Elapsed.TotalSeconds
                $Attempts.Add($Record)
            }
        }
    } finally {
        [IO.Directory]::CreateDirectory($Destination) | Out-Null
        $Report = [ordered]@{ max_attempts = 3; seconds = $Total.Elapsed.TotalSeconds; attempts = @($Attempts.ToArray()) }
        $Bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Report | ConvertTo-Json -Depth 8 -Compress) + [Environment]::NewLine)
        $Stream = [IO.File]::Open((Join-Path $Destination ($Phase + '-startup.json')), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
        try { $Stream.Write($Bytes, 0, $Bytes.Length); $Stream.Flush($true) } finally { $Stream.Dispose() }
    }
}
