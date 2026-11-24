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
    [ValidatePattern('^[0-9a-f]{32}$')] [string]$ParallelGroup,
    [ValidateRange(2, 5)] [int]$ParallelWorkerLimit = 5,
    [ValidateRange(1, 1200)] [int]$ParallelWaitSeconds = 300
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
if ($Batch) { [SolidWorksCapture]::CheckBatch($CaseFile, $Destination) }
else { [SolidWorksCapture]::CheckConfigured($CaseFile) }
if ($CompileOnly) {
    Write-Output 'Compiled configured SOLIDWORKS authoring without starting an application'
    return
}
$Parallel = [bool]$ParallelGroup
[SolidOwner]::ParallelCapture = $Parallel
$Shared = $false
. (Join-Path $PSScriptRoot 'ParallelSolidSession.ps1')
$Lease = $null
$Peers = @()
$Mutex = [Threading.Mutex]::new($false, 'Local\KitResearchControllerOracle')
$Acquired = $false
$Native = $null
$ExitObserved = $false
$ForcedCleanup = $false
$Failure = $null
try {
    $WaitMs = if ($Parallel) { $ParallelWaitSeconds * 1000 } else { 0 }
    try { $Acquired = $Mutex.WaitOne($WaitMs) } catch [Threading.AbandonedMutexException] { $Acquired = $true }
    if (-not $Acquired) { throw 'The shared SOLIDWORKS oracle is owned by another operation.' }
    if ($Parallel) {
        $Peers = @(Get-ParallelSolidPeers $ParallelGroup)
        if ($Peers.Count -ge $ParallelWorkerLimit) {
            throw "The catalogue already owns $ParallelWorkerLimit SOLIDWORKS processes."
        }
    } elseif (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) {
        throw 'Preserve the existing SOLIDWORKS session and use an idle native host.'
    }
    $Native = Start-Process -FilePath $Executable.FullName -WorkingDirectory $Executable.DirectoryName -WindowStyle Hidden -PassThru
    $Created = $Native.StartTime.ToUniversalTime().ToFileTimeUtc()
    if ($Native.HasExited -or $Native.StartTime.ToUniversalTime().ToFileTimeUtc() -ne $Created) {
        throw 'The application identity changed before authoring.'
    }
    $Shared = $Parallel -and [SolidOwner]::CanShareSession($Native, $Executable.FullName)
    if ($Parallel -and -not $Shared) {
        if (@(Get-ParallelSolidPeers $ParallelGroup $Native.Id).Count -gt 0) {
            throw 'The SOLIDWORKS dimension prompt is enabled while a catalogue peer is active.'
        }
        Write-Output 'The dimension prompt requires an exclusive SOLIDWORKS phase.'
    }
    [SolidOwner]::KeepDimensionPreference = $Shared
    if ($Shared) {
        $NewLease = $false
        $LeaseName = Get-ParallelSolidLeaseName $ParallelGroup $Native.Id $Created
        $LeaseHandle = [Threading.Mutex]::new($true, $LeaseName, [ref]$NewLease)
        if (-not $NewLease) {
            $LeaseHandle.Dispose()
            throw 'A catalogue lease already exists for the new SOLIDWORKS process.'
        }
        $Lease = $LeaseHandle
        $Peers = @(Get-ParallelSolidPeers $ParallelGroup $Native.Id)
        $Mutex.ReleaseMutex()
        $Acquired = $false
    } elseif (@(Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue).Count -ne 1) {
        throw 'The application identity changed before authoring.'
    }
    if ($Batch) {
        [SolidOwner]::RunBatch($Native, $Executable.FullName, $Repository, $Destination, $CaseFile, $Phase)
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
    }
    else { [SolidOwner]::RunOwned($Native, $Executable.FullName, $Repository, $Destination, $CaseFile, $Phase) }
} catch { $Failure = $_ } finally {
    try {
        if ($null -ne $Native) {
            $ExitObserved = $Native.WaitForExit(30000)
            if (-not $ExitObserved -and $Native.StartTime.ToUniversalTime().ToFileTimeUtc() -eq $Created) {
                $Native.Kill()
                $ForcedCleanup = $Native.WaitForExit(10000)
            }
            $ProcessId = $Native.Id
            $Native.Dispose()
            if (-not (Test-Path -LiteralPath $Destination)) { [IO.Directory]::CreateDirectory($Destination) | Out-Null }
            $OwnerPath = Join-Path $Destination ($Phase + '-owner.json')
            $Owner = [ordered]@{ phase = $Phase; pid = $ProcessId; created = $Created; owned_process_exit_observed = $ExitObserved; forced_owned_cleanup = $ForcedCleanup }
            if ($Parallel) {
                $Owner.parallel_eligible = $Shared
                $Owner.parallel_peer_pids = $Peers
            }
            $OwnerJson = ($Owner | ConvertTo-Json -Compress) + [Environment]::NewLine
            $OwnerBytes = [Text.UTF8Encoding]::new($false).GetBytes($OwnerJson)
            $OwnerStream = [IO.File]::Open($OwnerPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
            try { $OwnerStream.Write($OwnerBytes, 0, $OwnerBytes.Length); $OwnerStream.Flush($true) } finally { $OwnerStream.Dispose() }
        }
    } finally {
        if ($null -ne $Lease) {
            $Lease.ReleaseMutex()
            $Lease.Dispose()
        }
        if ($Acquired) { $Mutex.ReleaseMutex() }
        $Mutex.Dispose()
    }
}
if ($null -ne $Failure) { throw $Failure }
if (-not $ExitObserved) { throw 'The owned SOLIDWORKS process did not exit normally.' }
