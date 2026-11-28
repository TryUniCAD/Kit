param(
    [Parameter(Mandatory = $true)][string]$SharedBundle,
    [Parameter(Mandatory = $true)][string]$GuestTools,
    [Parameter(Mandatory = $true)][string]$GuestCapture,
    [Parameter(Mandatory = $true)][string]$Control
)

$ErrorActionPreference = "Stop"
$pins = @{
    "AuthorOpenShell.py" = "0d1692d27fbe31b4cd63e910ed8cdc14c79ec31b307032fbe883d7e6213881b9"
    "Swapp.py" = "2e07f638053243b639e4fc9722de08698b8c3bdbbc1a9b008ea64de968ab4aba"
    "OracleIdentity.py" = "65e2b89250f8c4aaf74d522dac90abce8a9ef10fa8e04dfd56115be50f47386e"
    "InspectFresh.py" = "aa9d95792b7484b41e12e2ed2b097158ddfeef618bce98803efd372b0a2037de"
}

if (Test-Path -LiteralPath $GuestTools) { throw "Guest tools path already exists" }
if (Test-Path -LiteralPath $GuestCapture) { throw "Guest capture path already exists" }
$export = Join-Path $SharedBundle "Disclosure"
if (Test-Path -LiteralPath $export) { throw "Disclosure path already exists" }
New-Item -Path $GuestTools -ItemType Directory | Out-Null
foreach ($name in $pins.Keys) {
    $source = Join-Path $SharedBundle $name
    $destination = Join-Path $GuestTools $name
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pins[$name]) {
        throw "Shared tool changed: $name"
    }
    Copy-Item -LiteralPath $source -Destination $destination
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pins[$name]) {
        throw "Guest tool changed: $name"
    }
}

& py.exe -3.12 -E -B (Join-Path $GuestTools "AuthorOpenShell.py") --root $GuestCapture --control $Control
if ($LASTEXITCODE -ne 0) { throw "Open shell source batch exited $LASTEXITCODE" }
$receipt = Join-Path $GuestCapture "Receipt.json"
$report = Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
$original = Join-Path $GuestCapture "disclosed\OpenShell.SLDPRT"
$edited = Join-Path $GuestCapture "disclosed\OpenShellEdited.SLDPRT"
$files = @{
    "OpenShell.SLDPRT" = @{Source = $original; Hash = $report.cases.disclosed.original_sha256}
    "OpenShellEdited.SLDPRT" = @{Source = $edited; Hash = $report.cases.disclosed.edited_sha256}
    "Receipt.json" = @{Source = $receipt; Hash = (Get-FileHash -LiteralPath $receipt -Algorithm SHA256).Hash.ToLowerInvariant()}
}
foreach ($name in @("Author.json", "Request.json", "ReopenOriginal.json", "ReopenEdited.json")) {
    $source = Join-Path $GuestCapture ("disclosed\" + $name)
    $files[$name] = @{Source = $source; Hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()}
}
foreach ($name in @("ControlBefore.json", "ControlAfter.json")) {
    $source = Join-Path $GuestCapture $name
    $files[$name] = @{Source = $source; Hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()}
}
New-Item -Path $export -ItemType Directory | Out-Null
foreach ($name in $files.Keys) {
    $item = $files[$name]
    $destination = Join-Path $export $name
    Copy-Item -LiteralPath $item.Source -Destination $destination
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Hash) {
        throw "Disclosed artifact changed: $name"
    }
}
$files.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name) $($_.Value.Hash)" }
