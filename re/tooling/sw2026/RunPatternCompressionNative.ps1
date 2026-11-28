$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$shared = '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\PatternCompressionTrial01'
$packet = Join-Path $shared 'Packet'
$packetPin = '9e8456c5f266646e7a96ffa711c5a4e3be957ffa807eaddc4e9aa8e0dae8bf8c'
$observerPin = '4586919bb798d1e49ef2d6d14f927af0f014901246797a15b1bd241df9033cf8'
$observer = Join-Path $packet 'Tools\ObserveGeneratedLinearPattern.py'
$locator = 'C:\KitGeneratedLocalPattern'
$held = 'C:\KitPatternCompressionTrial01\ClassicLocatorHeld'
$retained = 'C:\KitPatternCompressionTrial01\AlternateNativeFiles'
$known = [ordered]@{
 'ColdRaisedPatternA.SLDPRT'='f7e5290dfda2cd2aedfc281ea8ee6275fd1214fc011bcda51f88d43d8cc4356f';
 'ColdRaisedPatternAEdited.SLDPRT'='d8b83bdf73f97c41581be425353cf8fa9595bf0a9cd6387cf67448b4b5af1d86';
 'ColdRaisedPatternB.SLDPRT'='032c9c5696a4b97a9a5c5178147cb8443b90a6350588154dec693ff56d372754';
 'ColdRaisedPatternBEdited.SLDPRT'='36e1d0f88d4169b256ca5e39f6c2009f03529490ec4fe882803666f6aa2b50e8'
}
function Check-Digest($file, $expected) {
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $expected) { throw "unexpected hash for $file" }
}
function Check-ClassicLocator {
    $root = Get-Item -LiteralPath $locator
    if ($root.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'classic root is a link' }
    $members = @(Get-ChildItem -LiteralPath $locator -Force)
    if ($members.Count -ne $known.Count) { throw 'classic locator contains unexpected members' }
    foreach ($file in $known.GetEnumerator()) { Check-Digest (Join-Path $locator $file.Key) $file.Value }
}
if ((Test-Path -LiteralPath $held) -or (Test-Path -LiteralPath $retained) -or
    (Test-Path -LiteralPath (Join-Path $shared 'NativeResult')) -or
    @(Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue).Count -ne 0) { throw 'native trial paths or application are occupied' }
Check-Digest (Join-Path $packet 'Packet.json') $packetPin
Check-Digest $observer $observerPin
Check-ClassicLocator
Move-Item -LiteralPath $locator -Destination $held
$status = 1
try {
    & py.exe -3.12 -E -B $observer $packet --pin $packetPin
    $status = $LASTEXITCODE
} finally {
    if (Test-Path -LiteralPath $locator) { Move-Item -LiteralPath $locator -Destination $retained }
    Move-Item -LiteralPath $held -Destination $locator
    Check-ClassicLocator
    [ordered]@{ original_restored = $true; packet_sha256 = $packetPin; observer_exit_code = $status; alternate_files = $retained } |
        ConvertTo-Json -Compress | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $shared 'NativeTransport.json')
}
exit $status
