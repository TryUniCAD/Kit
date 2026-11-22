param(
    [Parameter(Mandatory = $true)][string]$SharedBundle,
    [Parameter(Mandatory = $true)][string]$TrialHash
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$candidateHash = "502544a82aa60b83ac6ee8e032a209022b3382734e6e68f9bb6c737287fec149"
$controlHash = "92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa"
$observerHash = "382982443dc01df361aa9dda537706c1581303cb6ed71a2f64020afdbc33f595"
$knownRoot = "C:\KitAttachedRadiusChild01"
$working = Join-Path $knownRoot "Working"
$controlRoot = Join-Path $knownRoot "Control02"
$candidate = Join-Path $working "DisclosedRadialSceneProbe.SLDPRT"
$control = Join-Path $controlRoot "ConcentricD01Child.SLDPRT"
$observer = Join-Path $SharedBundle "Tools\ObserveAttachedRadiusStandalone.py"
$plan = Join-Path $SharedBundle "AttachedRadiusStandalonePlan01.json"
$trial = Join-Path $SharedBundle "Trial.json"

foreach ($folder in @($knownRoot, $working)) {
    $item = Get-Item -LiteralPath $folder
    if (-not $item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw "Unexpected task directory: $folder"
    }
}
if (Get-Process -Name "SLDWORKS" -ErrorAction SilentlyContinue) { throw "The fresh oracle slot is occupied" }
if (Test-Path -LiteralPath $controlRoot) { throw "The new control directory already exists" }
if ((Get-Item -LiteralPath $candidate).Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw "The candidate is a reparse point" }
if ((Get-FileHash -LiteralPath $observer -Algorithm SHA256).Hash.ToLowerInvariant() -ne $observerHash) { throw "The observer changed" }
if ((Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -ne $candidateHash) { throw "The working candidate changed" }
if ((Get-FileHash -LiteralPath $trial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $TrialHash) { throw "The trial changed" }
$source = Join-Path $SharedBundle "ConcentricD01Child.SLDPRT"
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $controlHash) { throw "The disclosed control changed" }
New-Item -Path $controlRoot -ItemType Directory | Out-Null
Copy-Item -LiteralPath $source -Destination $control
if ((Get-FileHash -LiteralPath $control -Algorithm SHA256).Hash.ToLowerInvariant() -ne $controlHash) { throw "The new control copy changed" }

& py.exe -3.12 -E -B $observer $trial $TrialHash $plan
if ($LASTEXITCODE -ne 0) { throw "The radial trial did not qualify" }
