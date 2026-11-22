$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$work = 'C:\KitThinSdkFileProof01'
$worker = Join-Path $work 're\tooling\sw2026\revolve\CheckThinSuiteCase.py'
$cases = @(
 @{Id='front';Root='C:\KitThinGenerated01';File='ThinUnequal.SLDPRT';Job='f00ddbfe7e7a9e6ba0f63c86129946f2bf7d58811d760bb5b1812520864648ea';Hash='871b920ad7f1ce34a25aaffb21d5fbf4cb8c79b1e67a1c486a235fb29f2c4207'},
 @{Id='principal';Root='C:\KitThinPlaneGenerated01';File='ThinRightCenterControl.SLDPRT';Job='f3e4cc5b5f38ff677c13e52e996e59c92afdd35128e921360c24d17db0b76aa4';Hash='c5d8880148f4ff4cd40298020e9d6cf54904cec23c12f45ea87ffa6c325710aa'}
)
function Snapshot($path) {
 $entries = @(Get-ChildItem -LiteralPath $path -Recurse -Force | Sort-Object FullName)
 if (@($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count -gt 0) { throw 'original tree contains reparse points' }
 return (ConvertTo-Json -Compress -InputObject @($entries | ForEach-Object {
  $name = $_.FullName.Substring($path.Length+1)
  if ($_.PSIsContainer) { [ordered]@{ name=$name;directory=$true } }
  else { [ordered]@{name=$name;bytes=$_.Length;date=$_.LastWriteTimeUtc.Ticks;sha=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} }
 }))
}
if (@(Get-Process -Name SLDWORKS -ErrorAction SilentlyContinue).Count -ne 0) { throw 'native application is active' }
if ((Get-FileHash -LiteralPath $worker -Algorithm SHA256).Hash -ne 'a864edaba199e329da310a22eb97b15aaed3bc2bc1ef17a1211e9930c89643db') { throw 'worker source changed in guest' }
foreach ($case in $cases) {
 $original = $case.Root
 $held = Join-Path $work ('Held-' + $case.Id)
 $residue = Join-Path $work ('Interrupted-' + $case.Id)
 $native = Join-Path (Join-Path $original 'Candidates') $case.File
 if ((Test-Path -LiteralPath $held) -or (Test-Path -LiteralPath $residue)) { throw 'proof custody paths already occupied' }
 if ((Get-Item -LiteralPath $original).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'old root is a reparse point' }
 if ((Get-FileHash -LiteralPath (Join-Path $original 'NativeJob.json') -Algorithm SHA256).Hash -ne $case.Job) { throw 'original native job changed' }
 if ((Get-FileHash -LiteralPath $native -Algorithm SHA256).Hash -ne $case.Hash) { throw 'original candidate changed' }
 $baseline = Snapshot $original
 Move-Item -LiteralPath $original -Destination $held
 $status = 1
 try {
  & py.exe -3.12 -I -B $worker --case $case.Id
  $status = $LASTEXITCODE
 } finally {
  if (Test-Path -LiteralPath $original) { Move-Item -LiteralPath $original -Destination $residue }
  Move-Item -LiteralPath $held -Destination $original
  if ((Snapshot $original) -cne $baseline) { throw 'restored original tree changed' }
  [ordered]@{scope=$case.Id;original_restored=$true;original_file_sha256=$case.Hash;original_members=@(ConvertFrom-Json $baseline).Count;file_worker_exit=$status} | ConvertTo-Json -Compress
 }
 if ($status -ne 0) { exit $status }
}
exit 0
