param(
    [Parameter(Mandatory = $true)][string]$SharedBundle,
    [Parameter(Mandatory = $true)][string]$Control
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$owner = "C:\KitOpenShellGenerated01"
$toolDir = Join-Path $owner "Tools"
$working = Join-Path $owner "Working"
$edited = Join-Path $owner "Edited"
$name = "OpenShellCalibration.SLDPRT"
$result = Join-Path $SharedBundle "NativeResult.json"
$pins = @{
    "InspectGeneratedOpenShell.py" = "2cbcc0098dd4d60b202d0adf68b023bf7cba9237cff86f8ac6c06aafed391a90"
    "AuthorOpenShell.py" = "0d1692d27fbe31b4cd63e910ed8cdc14c79ec31b307032fbe883d7e6213881b9"
    "Swapp.py" = "2e07f638053243b639e4fc9722de08698b8c3bdbbc1a9b008ea64de968ab4aba"
    "OracleIdentity.py" = "65e2b89250f8c4aaf74d522dac90abce8a9ef10fa8e04dfd56115be50f47386e"
    "InspectFresh.py" = "aa9d95792b7484b41e12e2ed2b097158ddfeef618bce98803efd372b0a2037de"
}
$archiveHash = "84cc9032447eefd717f9fb4bc3a6c62ecf941af80aa45da861ca7bd1d456f4a1"

if (Test-Path -LiteralPath $owner) { throw "The exact shell trial locator already exists" }
if (Test-Path -LiteralPath $result) { throw "The shell trial result already exists" }
if (Get-Process -Name "SLDWORKS" -ErrorAction SilentlyContinue) { throw "The native oracle slot is occupied" }
New-Item -Path $owner -ItemType Directory | Out-Null
foreach ($directory in @($toolDir, $working, $edited)) {
    New-Item -Path $directory -ItemType Directory | Out-Null
}
foreach ($key in $pins.Keys) {
    $source = Join-Path $SharedBundle $key
    $target = Join-Path $toolDir $key
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pins[$key]) { throw "A frozen oracle tool changed" }
    Copy-Item -LiteralPath $source -Destination $target
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pins[$key]) { throw "The guest oracle tool changed" }
}
$candidate = Join-Path $working $name
$saved = Join-Path $edited $name
$archive = Join-Path $SharedBundle $name
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $archiveHash) { throw "The generated candidate changed" }
Copy-Item -LiteralPath $archive -Destination $candidate
if ((Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -ne $archiveHash) { throw "The staged candidate changed" }
& py.exe -3.12 -E -B (Join-Path $toolDir "InspectGeneratedOpenShell.py") --candidate $candidate --edited $saved --control $Control --result $result
if ($LASTEXITCODE -ne 0) { throw "The shell trial did not qualify" }
