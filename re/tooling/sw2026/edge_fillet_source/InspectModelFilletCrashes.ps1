param(
    [Parameter(Mandatory = $true)]
    [string] $ResultPath
)

$ErrorActionPreference = 'Stop'
$result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
if ($result.schema -ne 'kit.sw2026.edge-fillet-model-native.v1' -or $result.oracle.build -ne '34.5.2.0604') {
    throw 'Expected the exact SOLIDWORKS 2026 model fillet native result'
}

$owners = @{}
$starts = @()
foreach ($case in $result.cases.PSObject.Properties) {
    foreach ($phase in $case.Value.phases.PSObject.Properties) {
        $process = @($phase.Value.process)
        if ($process.Count -eq 2 -and $process[0] -gt 0 -and $process[1] -gt 0) {
            $owners["$($process[0]):$($process[1])"] = $case.Name
            $starts += [DateTime]::FromFileTimeUtc([long]$process[1])
        }
    }
}
if ($starts.Count -eq 0) {
    throw 'No exact candidate lifetime is present'
}

$after = ($starts | Sort-Object | Select-Object -First 1).ToLocalTime()
$events = @(Get-WinEvent -FilterHashtable @{
    LogName = 'Application'
    Id = 1000
    StartTime = $after
} -ErrorAction SilentlyContinue | ForEach-Object {
    $values = @($_.Properties | ForEach-Object Value)
    if ($values.Count -ge 10 -and $values[0] -eq 'SLDWORKS.exe' -and $values[1] -eq '34.5.2.604') {
        $key = "$($values[8]):$($values[9])"
        if ($owners.ContainsKey($key)) {
            [ordered]@{
                case = $owners[$key]
                event = $_.Id
                record = $_.RecordId
                time_utc = $_.TimeCreated.ToUniversalTime().ToString('o')
                application_build = $values[1]
                module = $values[3]
                exception_code = $values[6]
                faulting_offset = $values[7]
                process = @([long]$values[8], [long]$values[9])
            }
        }
    }
} | Sort-Object { $_.record })

[ordered]@{
    schema = 'kit.sw2026.edge-fillet-model-events.v1'
    native_result_sha256 = (Get-FileHash -LiteralPath $ResultPath -Algorithm SHA256).Hash.ToLowerInvariant()
    events = $events
} | ConvertTo-Json -Depth 5
