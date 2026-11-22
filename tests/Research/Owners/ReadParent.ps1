param([int]$ProcessNumber)
$ErrorActionPreference = 'Stop'
$Value = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $ProcessNumber" -Property ParentProcessId
if ($null -eq $Value) { exit 3 }
[Console]::Write($Value.ParentProcessId)
