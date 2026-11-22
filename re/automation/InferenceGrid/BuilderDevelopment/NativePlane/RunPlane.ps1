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
    [Parameter(Mandatory)] [ValidatePattern('^[0-9a-f]{64}$')] [string]$CandidateSha256,
    [Parameter(Mandatory)] [ValidateSet('first', 'second', 'third')] [string]$Phase,
    [switch]$CompileOnly
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
    throw 'Select the registered SOLIDWORKS executable and matching interop assembly.'
}
$Registration = (Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\SldWorks.Application\CLSID').GetValue('')
$Registered = (Get-Item -LiteralPath "Registry::HKEY_CLASSES_ROOT\CLSID\$Registration\LocalServer32").GetValue('')
if ($Executable.FullName -ine (Get-Item -LiteralPath $Registered).FullName -or
    $Executable.VersionInfo.FileVersion -cne $Interop.VersionInfo.FileVersion) {
    throw 'The native executable and interop must match the exact registered build.'
}
$CaseFile = (Get-Item -LiteralPath $CasePath).FullName
$Destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
if ($Destination -ieq $Repository -or
    $Destination.StartsWith($Repository + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Candidate outputs must be outside the source checkout.'
}
$Catalogue = Join-Path $Repository 're/automation/CaptureTools/Catalogue/SolidWorks'
$WebExtensions = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
Add-Type -Path $Interop.FullName
$Programs = @(Get-ChildItem -LiteralPath (Join-Path $Catalogue 'Programs') -Filter '*.cs' -File -Recurse | Sort-Object FullName | ForEach-Object FullName)
$Collectors = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.cs' -File | Sort-Object FullName | ForEach-Object FullName)
$Candidate = Get-Item -LiteralPath (Join-Path $Destination 'CandidateProgram.cs')
if ($Candidate.PSIsContainer -or ($Candidate.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
    (Get-FileHash -LiteralPath $Candidate.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $CandidateSha256) {
    throw 'Candidate source differs from the frozen generated source.'
}
Add-Type -Path (@((Join-Path $Repository 're/automation/CaptureTools/SolidWorksAuthoring/SolidWorksCapture.cs'),
    (Join-Path $Catalogue 'ConfiguredCapture.cs'), (Join-Path $Catalogue 'SolidOwner.cs')) + $Programs + $Collectors + @($Candidate.FullName)) -ReferencedAssemblies @($Interop.FullName, 'System.Core.dll', $WebExtensions)
if ((Get-FileHash -LiteralPath $Candidate.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $CandidateSha256) {
    throw 'Candidate source changed while being compiled.'
}
[SolidWorksCapture]::CheckPlaneManifest($CaseFile)
if ($CompileOnly) { Write-Output 'Compiled trusted plane collector without starting a CAD application'; return }
$Mutex = [Threading.Mutex]::new($false, 'Local\KitResearchControllerOracle')
$Acquired = $false
$Native = $null
$ExitObserved = $false
$ForcedCleanup = $false
$Failure = $null
try {
    try { $Acquired = $Mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $Acquired = $true }
    if (-not $Acquired) { throw 'The shared SOLIDWORKS oracle is owned by another operation.' }
    if (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) { throw 'Preserve the existing native session and use an idle host.' }
    $Native = Start-Process -FilePath $Executable.FullName -WorkingDirectory $Executable.DirectoryName -WindowStyle Hidden -PassThru
    $Created = $Native.StartTime.ToUniversalTime().ToFileTimeUtc()
    if (@(Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue).Count -ne 1 -or
        $Native.StartTime.ToUniversalTime().ToFileTimeUtc() -ne $Created) { throw 'The native process identity changed before entry.' }
    [PlaneOwner]::Run($Native, $Executable.FullName, $Repository, $Destination, $CaseFile, $Phase)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
} catch { $Failure = $_ } finally {
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
        $OwnerBytes = [Text.UTF8Encoding]::new($false).GetBytes(($Owner | ConvertTo-Json -Compress) + [Environment]::NewLine)
        $Stream = [IO.File]::Open($OwnerPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
        try { $Stream.Write($OwnerBytes, 0, $OwnerBytes.Length); $Stream.Flush($true) } finally { $Stream.Dispose() }
    }
    if ($Acquired) { $Mutex.ReleaseMutex() }
    $Mutex.Dispose()
}
if ($null -ne $Failure) { throw $Failure }
if (-not $ExitObserved) { throw 'The owned candidate application did not exit normally.' }
