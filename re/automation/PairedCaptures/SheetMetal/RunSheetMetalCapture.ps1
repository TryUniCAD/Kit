[CmdletBinding(DefaultParameterSetName = 'Capture')]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$SourceRevision,
    [Parameter(Mandatory, ParameterSetName = 'Compile')]
    [switch]$CompileOnly,
    [Parameter(Mandatory, ParameterSetName = 'Capture')]
    [string]$OutputDirectory,
    [Parameter(Mandatory, ParameterSetName = 'Capture')]
    [string]$StockControl,
    [Parameter(Mandatory, ParameterSetName = 'Capture')]
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$StockControlSha256,
    [Parameter(Mandatory, ParameterSetName = 'Capture')]
    [ValidateRange(1, 100)]
    [int]$StockSolidCount,
    [Parameter(Mandatory, ParameterSetName = 'Capture')]
    [ValidateRange(1e-12, 1.0)]
    [double]$StockVolumeM3
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -ne 'Desktop' -or
    [Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA' -or -not [Environment]::Is64BitProcess) {
    throw 'Use 64-bit Windows PowerShell 5.1 in STA mode.'
}

function Get-Hash([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-PlainFile([string]$Path) {
    $file = Get-Item -LiteralPath $Path
    if ($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Expected a plain file at $Path."
    }
    $file
}

function Get-Pin([string]$RelativePath) {
    $file = Get-PlainFile (Join-Path $repository $RelativePath)
    $blob = git -C $repository rev-parse --verify ("$SourceRevision" + ':' + $RelativePath)
    if ($LASTEXITCODE -ne 0 -or (git -C $repository hash-object --no-filters -- $file.FullName) -cne $blob -or
        $LASTEXITCODE -ne 0) {
        throw "Source bytes differ from Git at $RelativePath."
    }
    [ordered]@{ path = $RelativePath; git_blob = $blob; sha256 = Get-Hash $file.FullName; size_bytes = $file.Length }
}

function Write-NewJson([string]$Path, $Value) {
    $stage = "$Path.$([Guid]::NewGuid().ToString('N'))"
    try {
        $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 55) + [Environment]::NewLine)
        $file = [IO.File]::Open($stage, [IO.FileMode]::CreateNew)
        try {
            $file.Write($bytes, 0, $bytes.Length)
            $file.Flush($true)
        } finally { $file.Dispose() }
        [IO.File]::Move($stage, $Path)
    } finally { [IO.File]::Delete($stage) }
}

function Assert-EquivalentObservation($Authored, $Reopened) {
    if ($Authored.configuration -cne $Reopened.configuration) { throw 'Configuration changed on native reopen.' }
    $expected = @($Authored.bodies | Sort-Object -Property name)
    $actual = @($Reopened.bodies | Sort-Object -Property name)
    if ($expected.Count -ne $actual.Count) { throw 'Native solid body count changed on reopen.' }
    for ($idx = 0; $idx -lt $expected.Count; ++$idx) {
        $a = $expected[$idx]
        $b = $actual[$idx]
        if ($a.name -cne $b.name -or [Math]::Abs($a.volume_m3 - $b.volume_m3) -gt 1e-12 -or
            [Math]::Abs($a.surface_area_m2 - $b.surface_area_m2) -gt 1e-9) {
            throw "Native body name, volume or area changed on reopen at sorted body index $idx."
        }
        for ($axis = 0; $axis -lt 3; ++$axis) {
            if ([Math]::Abs($a.centroid_m[$axis] - $b.centroid_m[$axis]) -gt 2e-7 -or
                [Math]::Abs($a.bounds_m[0][$axis] - $b.bounds_m[0][$axis]) -gt 2e-7 -or
                [Math]::Abs($a.bounds_m[1][$axis] - $b.bounds_m[1][$axis]) -gt 2e-7) {
                throw "Native body centroid or bounds changed on reopen at sorted body index $idx."
            }
        }
    }
    if ($Authored.configuration_id -ne $Reopened.configuration_id) { throw 'Native configuration ID changed on reopen.' }
    if ($Authored.features.Count -ne $Reopened.features.Count) { throw 'Native feature count changed on reopen.' }
    for ($index = 0; $index -lt $Authored.features.Count; ++$index) {
        $left = $Authored.features[$index]
        $right = $Reopened.features[$index]
        if ($left.name -cne $right.name -or $left.type -cne $right.type -or $left.feature_id -ne $right.feature_id -or
            $left.error -ne $right.error -or $left.warning -ne $right.warning -or
            ($left.body_members.name -join ',') -cne ($right.body_members.name -join ',') -or
            ($left.parents.feature_id -join ',') -cne ($right.parents.feature_id -join ',')) {
            throw "Native feature identity, order, diagnostics, parents or cut-list membership changed at index $index."
        }
        if ($left.suppressed -ne $right.suppressed) {
            throw "Native feature suppression changed at index $index for $($left.name): authored $($left.suppressed), reopened $($right.suppressed)."
        }
    }
}

$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
if ((git -C $repository rev-parse --verify HEAD) -cne $SourceRevision -or $LASTEXITCODE -ne 0) {
    throw 'The checkout is not at the selected source revision.'
}
$relative = 're/automation/PairedCaptures/SheetMetal'
$sources = @(
    (Get-Pin "$relative/RunSheetMetalCapture.ps1")
    (Get-Pin "$relative/SheetMetalCapture.cs")
    (Get-Pin "$relative/SheetMetalCaptureSpec.json")
    (Get-Pin 're/automation/PairedCaptures/ScopeControl/SolidWorksScopeControl.cs')
)
$specificationText = Get-Content -Encoding UTF8 -LiteralPath (Join-Path $repository $sources[2].path) -Raw
$specification = $specificationText | ConvertFrom-Json
$build = $specification.build
if ($specification.schema -ne 1 -or $build -cne '34.4.1.1011' -or
    ($specification.cases.id -join ',') -cne 'A-only,A-only-repeat,A-then-B,B-then-A,A-edge,held-out' -or
    $specification.cases[-1].holdout -ne $true) {
    throw 'Unexpected sheet-metal capture recipe.'
}
$registration = (Get-Item -LiteralPath 'Registry::HKEY_CLASSES_ROOT\SldWorks.Application\CLSID').GetValue('')
$server = (Get-Item -LiteralPath "Registry::HKEY_CLASSES_ROOT\CLSID\$registration\LocalServer32").GetValue('')
$binary = Get-PlainFile $server
$interop = Get-PlainFile (Join-Path $binary.DirectoryName 'api/redist/SolidWorks.Interop.sldworks.dll')
$constants = Get-PlainFile (Join-Path $binary.DirectoryName 'api/redist/SolidWorks.Interop.swconst.dll')
if (@($binary, $interop, $constants).Where({ $_.VersionInfo.FileVersion -cne $build }).Count) {
    throw "The registered installation and installed interop must all match $build."
}
$files = @($binary, $interop, $constants)
foreach ($pin in $specification.modules.PSObject.Properties) {
    $module = Get-PlainFile (Join-Path $binary.DirectoryName $pin.Name)
    if ((Get-Hash $module.FullName) -cne $pin.Value) { throw "Installed module $($pin.Name) differs from the pinned cohort." }
    $files += $module
}
$binaries = [ordered]@{}
foreach ($file in $files) {
    $binaries[$file.Name] = [ordered]@{ sha256 = Get-Hash $file.FullName; size_bytes = $file.Length; build = $file.VersionInfo.FileVersion }
}
$web = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
Add-Type -Path $constants.FullName
Add-Type -Path $interop.FullName
$paths = @((Join-Path $repository $sources[3].path), (Join-Path $repository $sources[1].path))
Add-Type -Path $paths -ReferencedAssemblies @($interop.FullName, $constants.FullName, 'System.Core.dll', $web)
if ($CompileOnly) {
    [ordered]@{ status = 'compiled'; source_revision = $SourceRevision; build = $build; sources = $sources; binaries = $binaries } |
        ConvertTo-Json -Depth 10
    return
}

$stock = Get-PlainFile $StockControl
if ($stock.Extension -ine '.sldprt' -or (Get-Hash $stock.FullName) -cne $StockControlSha256) {
    throw 'The stock part differs from its independently supplied SHA-256.'
}
$output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
if ((Test-Path -LiteralPath $output) -or
    $output.StartsWith($repository.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Choose an unused private output directory outside the checkout.'
}
$parent = Get-Item -LiteralPath (Split-Path -Parent $output)
if (-not $parent.PSIsContainer -or ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Use an existing plain output parent directory.'
}

function Measure-Stock([string]$Phase) {
    $control = [SheetMetalCapture]::Measure($binary.FullName, $stock.FullName, $StockControlSha256,
        $StockSolidCount, $Phase, $null, $null, 0, 0, 0) | ConvertFrom-Json
    Write-NewJson (Join-Path $output "$Phase.json") $control
    $volume = ($control.observation.bodies | Measure-Object -Property volume_m3 -Sum).Sum
    if ([Math]::Abs($volume - $StockVolumeM3) -gt [Math]::Max(1e-12, $StockVolumeM3 * 1e-7)) {
        throw "Stock control $Phase disagreed with the independently measured volume."
    }
    $control
}

$guard = [Threading.Mutex]::new($false, 'Local\KitResearchControllerOracle')
$locked = $false
$ownedOutput = $false
$stockStarted = $false
$stockFinished = $false
$phase = 'acquire_oracle'
try {
    try { $locked = $guard.WaitOne(0) }
    catch [Threading.AbandonedMutexException] { $locked = $true }
    if (!$locked -or (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue)) {
        throw 'The shared oracle is occupied.'
    }
    $output = (New-Item -ItemType Directory -Path $output).FullName
    $ownedOutput = $true
    $holdout = (New-Item -ItemType Directory -Path (Join-Path $output 'sealed-holdout')).FullName
    Write-NewJson (Join-Path $output 'run.json') ([ordered]@{
        schema = 1; build = $build; source_revision = $SourceRevision; sources = $sources; binaries = $binaries
        stock = [ordered]@{ sha256 = $StockControlSha256; expected_solids = $StockSolidCount; expected_volume_m3 = $StockVolumeM3 }
    })

    $phase = 'stock-before'
    $before = Measure-Stock $phase
    $stockStarted = $true
    $discovery = @()
    $sealed = $null
    $processes = @($before.native_process)
    foreach ($case in $specification.cases) {
        $caseOutput = if ($case.holdout) { $holdout } else { $output }
        $phase = "$($case.id)-author"
        $authored = [SheetMetalCapture]::Author($binary.FullName, $specificationText, $case.id, $caseOutput) | ConvertFrom-Json
        $authorReceipt = "$($case.id).authored.json"
        Write-NewJson (Join-Path $caseOutput $authorReceipt) $authored
        $processes += $authored.native_process
        $results = @()
        foreach ($save in $authored.saves) {
            $phase = "$($save.archive.file)-reopen"
            $receipt = "$($save.archive.file).reopened.json"
            $flange = $save.flange
            $reopen = [SheetMetalCapture]::Measure($binary.FullName, (Join-Path $caseOutput $save.archive.file),
                $save.archive.sha256, $case.bodies.Count, $save.archive.file, $authored.edge_authoring.profile_dimension,
                $authored.edge_authoring.source_edge, $flange.profile_length_m, $flange.angle_rad, $flange.radius_m) | ConvertFrom-Json
            Write-NewJson (Join-Path $caseOutput $receipt) $reopen
            Assert-EquivalentObservation $save $reopen.observation
            $processes += $reopen.native_process
            $results += [ordered]@{ archive = $save.archive; reopened_receipt = $receipt; reopened_sha256 = Get-Hash (Join-Path $caseOutput $receipt) }
        }
        $projection = [ordered]@{
            case = $case.id; authored_receipt = $authorReceipt; authored_sha256 = Get-Hash (Join-Path $caseOutput $authorReceipt)
            archives = $results
        }
        if ($case.holdout) {
            $sealPath = Join-Path $holdout 'seal.json'
            Write-NewJson $sealPath $projection
            $sealed = [ordered]@{ path = 'sealed-holdout/seal.json'; sha256 = Get-Hash $sealPath }
        } else { $discovery += $projection }
    }

    $phase = 'stock-after'
    $stockFinished = $true
    $after = Measure-Stock $phase
    Assert-EquivalentObservation $before.observation $after.observation
    $processes += $after.native_process
    $phase = 'finalize'
    if ($processes.Count -ne 16 -or @($processes | Where-Object { $_.exited_observed -ne $true }).Count -ne 0 -or
        @($processes | ForEach-Object { "$($_.pid)/$($_.started_utc)" } | Select-Object -Unique).Count -ne 16) {
        throw 'Expected 16 distinct owned and exited authoring, reopen and stock processes.'
    }
    foreach ($pin in $sources) {
        if ((Get-Pin $pin.path).sha256 -cne $pin.sha256) { throw "Pinned source changed during capture at $($pin.path)." }
    }
    foreach ($file in $files) {
        if ((Get-Hash $file.FullName) -cne $binaries[$file.Name].sha256) { throw "Installation changed during capture at $($file.Name)." }
    }
    $report = Join-Path $output 'report.json'
    Write-NewJson $report ([ordered]@{
        schema = 1; status = 'complete_native_capture'; provenance_sha256 = Get-Hash (Join-Path $output 'run.json')
        stock_before_sha256 = Get-Hash (Join-Path $output 'stock-before.json')
        stock_after_sha256 = Get-Hash (Join-Path $output 'stock-after.json')
        native_processes = $processes; discovery = $discovery; held_out_seal = $sealed
    })
    Get-Hash $report
} catch {
    if ($ownedOutput) {
        $failure = $_.Exception.GetBaseException()
        $failureRecord = [ordered]@{
            schema = 1; status = 'failed'; phase = $phase; source_revision = $SourceRevision
            type = $failure.GetType().Name; hresult = $failure.HResult
            message = $failure.Message.Substring(0, [Math]::Min($failure.Message.Length, 2048))
        }
        if ($failure.Data.Contains('scope_cleanup')) { $failureRecord.cleanup = $failure.Data['scope_cleanup'] | ConvertFrom-Json }
        if ($failure.Data.Contains('sheet_metal_base_evidence')) {
            $failureRecord.base_authoring = $failure.Data['sheet_metal_base_evidence'] | ConvertFrom-Json
        }
        if ($failure.Data.Contains('sheet_metal_close_hresult')) {
            $failureRecord.document_close_hresult = $failure.Data['sheet_metal_close_hresult']
        }
        if ($stockStarted -and !$stockFinished) {
            if (Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue) {
                $failureRecord.stock_after = 'oracle_not_empty_after_failure'
            } else {
                try {
                    $after = Measure-Stock 'stock-after'
                    Assert-EquivalentObservation $before.observation $after.observation
                    $failureRecord.stock_after = 'passed'
                } catch {
                    $postFailure = $_.Exception.GetBaseException()
                    $failureRecord.stock_after = 'failed'
                    $failureRecord.stock_after_hresult = $postFailure.HResult
                    $failureRecord.stock_after_message = $postFailure.Message.Substring(0, [Math]::Min($postFailure.Message.Length, 2048))
                }
            }
        }
        Write-NewJson (Join-Path $output 'failure.json') $failureRecord
    }
    throw
} finally {
    if ($locked) { $guard.ReleaseMutex() }
    $guard.Dispose()
}
