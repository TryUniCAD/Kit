# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$CasePath,
    [Parameter(Mandatory)] [string]$OutputDirectory,
    [Parameter(Mandatory)] [string]$InteropAssembly,
    [Parameter(Mandatory)] [string]$ExecutablePath,
    [Parameter(Mandatory)] [ValidateSet('first', 'second')] [string]$Phase,
    [switch]$CompileOnly,
    [switch]$Batch,
    [string]$QueueDirectory,
    [string]$SourceRevision
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -ne 'Desktop' -or -not [Environment]::Is64BitProcess -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA') {
    throw 'Use 64 bit Windows PowerShell 5.1 in STA mode.'
}
$Repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../../..')).Path
$Executable = Get-Item -LiteralPath $ExecutablePath
$Interop = Get-Item -LiteralPath $InteropAssembly
if ($Executable.Name -ine 'SLDWORKS.exe' -or $Interop.Name -ine 'SolidWorks.Interop.sldworks.dll') {
    throw 'Select the registered SOLIDWORKS executable and its matching interop assembly.'
}
$Registration = (Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\SldWorks.Application\CLSID').GetValue('')
$Registered = (Get-Item -LiteralPath "Registry::HKEY_CLASSES_ROOT\CLSID\$Registration\LocalServer32").GetValue('')
if ($Executable.FullName -ine (Get-Item -LiteralPath $Registered).FullName -or
    $Executable.VersionInfo.FileVersion -cne $Interop.VersionInfo.FileVersion) {
    throw 'The executable and interop must match the registered installation and exact build.'
}
$CaseFile = (Get-Item -LiteralPath $CasePath).FullName
$Destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
if ($Destination.StartsWith($Repository + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
    $Destination -ieq $Repository) {
    throw 'Native captures require an output directory outside the source checkout.'
}
$WebExtensions = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
Add-Type -Path $Interop.FullName
$ProgramSources = @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'Programs') -Filter '*.cs' -File -Recurse | Sort-Object FullName | ForEach-Object FullName)
Add-Type -Path (@((Join-Path $PSScriptRoot '../../SolidWorksAuthoring/SolidWorksCapture.cs'),
    (Join-Path $PSScriptRoot 'ConfiguredCapture.cs'),
    (Join-Path $PSScriptRoot 'SolidOwner.cs')) + $ProgramSources) -ReferencedAssemblies @($Interop.FullName, 'System.Core.dll', $WebExtensions)
if ($QueueDirectory) {
    if ($SourceRevision -cnotmatch '^[0-9a-f]{40}$' -or
        (Resolve-Path -LiteralPath $QueueDirectory).Path -cne $Destination) { throw 'Invalid routine queue identity.' }
}
elseif ($Batch) { [SolidWorksCapture]::CheckBatch($CaseFile, $Destination) }
else { [SolidWorksCapture]::CheckConfigured($CaseFile) }
. (Join-Path $PSScriptRoot 'WaitOwnedExit.ps1')
if ($CompileOnly) {
    Write-Output 'Compiled configured SOLIDWORKS authoring without starting an application'
    return
}
$Mutex = [Threading.Mutex]::new($false, 'Local\KitResearchControllerOracle')
$Acquired = $false
$Native = $null
$ExitObserved = $false
$ForcedCleanup = $false
$Failure = $null
$RpcLost = $false
. (Join-Path $PSScriptRoot 'StartOwnedSolid.ps1')
$FrameHandle = 0
try {
    try { $Acquired = $Mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $Acquired = $true }
    if (-not $Acquired) { throw 'The shared SOLIDWORKS oracle is owned by another operation.' }
    if (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) {
        throw 'Preserve the existing SOLIDWORKS session and use an idle native host.'
    }
    $Native = Start-OwnedSolid -Executable $Executable -Destination $Destination -Phase $Phase
    $Created = $Native.StartTime.ToUniversalTime().ToFileTimeUtc()
    if (@(Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue).Count -ne 1 -or
        $Native.StartTime.ToUniversalTime().ToFileTimeUtc() -ne $Created) {
        throw 'The application identity changed before authoring.'
    }
    if ($QueueDirectory) {
        # the routine owner requests its own exit and publishes no per-phase native receipt
        [SolidWorksCapture]::ServeRoutineOwned($Native, $Executable.FullName, $Repository, $Destination, $SourceRevision)
    }
    else {
        if ($Batch) {
            [SolidOwner]::RunBatch($Native, $Executable.FullName, $Repository, $Destination, $CaseFile, $Phase)
        }
        else { [SolidOwner]::RunOwned($Native, $Executable.FullName, $Repository, $Destination, $CaseFile, $Phase) }
        $Receipt = Get-Content -LiteralPath (Join-Path $Destination ($Phase + '-native.json')) -Raw | ConvertFrom-Json
        if ($Receipt.pid -ne $Native.Id -or $Receipt.normal_exit_requested -ne $true) {
            throw 'The native exit request receipt does not identify the owned application.'
        }
        $FrameHandle = [long]$Receipt.frame_handle
    }
} catch {
    $Failure = $_
    for ($Cause = $_.Exception; $null -ne $Cause; $Cause = $Cause.InnerException) {
        # RPC server unavailable, call failed, call failed before execution, disconnected, server died with or without execution.
        if ($Cause.HResult -in @(-2147023174, -2147023170, -2147023169, -2147417848, -2147418105, -2147418094)) {
            $RpcLost = $true
            break
        }
    }
} finally {
    if ($null -ne $Native) {
        $NativeExit = Wait-OwnedExit -Process $Native -Created $Created -AllowClose ($null -eq $Failure) -FrameHandle $FrameHandle
        $ExitObserved = $NativeExit.Observed
        if (-not $ExitObserved -and $Native.StartTime.ToUniversalTime().ToFileTimeUtc() -eq $Created) {
            try {
                $Native.Kill()
                $ForcedCleanup = $Native.WaitForExit(10000)
            } catch {
                if (-not $Native.WaitForExit(0)) { throw }
                $ExitObserved = $true
            }
        }
        $ProcessId = $Native.Id
        $Native.Dispose()
        if (-not (Test-Path -LiteralPath $Destination)) { [IO.Directory]::CreateDirectory($Destination) | Out-Null }
        $OwnerPath = Join-Path $Destination ($Phase + '-owner.json')
        $Owner = [ordered]@{ phase = $Phase; pid = $ProcessId; created = $Created; owned_process_exit_observed = $ExitObserved; forced_owned_cleanup = $ForcedCleanup }
        $Owner.window_close_requested = $NativeExit.CloseRequested
        if ($null -ne $NativeExit.CloseError) { $Owner.window_close_error = $NativeExit.CloseError }
        $OwnerJson = ($Owner | ConvertTo-Json -Compress) + [Environment]::NewLine
        $OwnerBytes = [Text.UTF8Encoding]::new($false).GetBytes($OwnerJson)
        $OwnerStream = [IO.File]::Open($OwnerPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
        try { $OwnerStream.Write($OwnerBytes, 0, $OwnerBytes.Length); $OwnerStream.Flush($true) } finally { $OwnerStream.Dispose() }
    }
    if ($Acquired) { $Mutex.ReleaseMutex() }
    $Mutex.Dispose()
}
if ($RpcLost -and ($ExitObserved -or $ForcedCleanup) -and -not $QueueDirectory) {
    [Console]::Error.WriteLine("SOLIDWORKS COM/RPC session lost: " + $Failure.Exception.ToString())
    exit 71
}
if ($null -ne $Failure) { throw $Failure }
if (-not $ExitObserved) {
    if ($ForcedCleanup -and -not $QueueDirectory) {
        [Console]::Error.WriteLine('SOLIDWORKS shutdown grace expired; terminated owned application.')
        exit 72
    }
    throw 'The owned SOLIDWORKS process did not exit normally.'
}
