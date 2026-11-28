# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

param([string]$Source, [string]$OwnerPath, [string]$JournalPath, [string]$MarkerPath, [switch]$CompileOnly, [string]$CacheRoot)
$ErrorActionPreference = 'Stop'
[Console]::Error.WriteLine((@{ fixture = 'readback'; phase = 'started'; utc = [DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Compress))
$Web = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
$Program = @'
public static class ProgressFixture
{
    public static string Run(string ownerPath, string journalPath, string markerPath)
    {
        var json = new System.Web.Script.Serialization.JavaScriptSerializer();
        var owner = json.Deserialize<System.Collections.Generic.Dictionary<string, object>>(System.IO.File.ReadAllText(ownerPath));
        var progress = new ReadbackProgress(journalPath, owner);
        progress.Invoke("final_control_hidden", "control.SLDPRT",
            () => System.IO.File.WriteAllText(markerPath, "real filesystem fixture action"),
            new System.Collections.Generic.Dictionary<string, object> { { "visible", false } });
        progress.Invoke("control_after", "control.SLDPRT", () => {
        progress.Invoke("open_document", "control.SLDPRT", () => System.IO.File.Exists(markerPath));
        var visibility = new System.Collections.Generic.Dictionary<string, object>();
        progress.Invoke("close_visibility", "control.SLDPRT", () => {
            visibility["visible"] = !System.IO.File.Exists(markerPath);
        }, visibility);
        var state = new System.Collections.Generic.Dictionary<string, object>();
        progress.Invoke("close_state", "control.SLDPRT", () => {
            state["save_flag"] = true;
            state["read_only"] = true;
            state["document_count"] = 1;
        }, state);
        progress.Invoke("quit_document", "control.SLDPRT",
            () => System.IO.File.WriteAllText(markerPath, "real filesystem fixture action"),
            new System.Collections.Generic.Dictionary<string, object> { { "operand", "control.SLDPRT" } });
        });
        return json.Serialize(progress.Finish("observed"));
    }
}
'@
$Started = [Diagnostics.Stopwatch]::StartNew()
$Definition = (Get-Content -LiteralPath $Source -Raw) + "`n" + $Program
$Identity = $Definition + [Environment]::Version.ToString() + [IntPtr]::Size + $PSVersionTable.PSVersion.ToString()
$Hasher = [Security.Cryptography.SHA256]::Create()
try {
    $Digest = [BitConverter]::ToString($Hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($Identity))).Replace('-', '').ToLowerInvariant()
} finally { $Hasher.Dispose() }
if (-not $CacheRoot) {
    $TempRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }
    $CacheRoot = Join-Path $TempRoot 'KitReadbackFixture'
}
$CacheRoot = [IO.Path]::GetFullPath($CacheRoot)
$null = [IO.Directory]::CreateDirectory($CacheRoot)
$AssemblyPath = Join-Path $CacheRoot ($Digest + '.dll')
$Hasher = [Security.Cryptography.SHA256]::Create()
try {
    $MutexKey = [BitConverter]::ToString($Hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($CacheRoot))).Replace('-', '')
} finally { $Hasher.Dispose() }
$Mutex = New-Object Threading.Mutex($false, ('Local\KitReadback-' + $Digest + '-' + $MutexKey))
$HasLock = $false
$Compiled = $false
$CompileSeconds = 0.0
try {
    try { $HasLock = $Mutex.WaitOne(360000) }
    catch [Threading.AbandonedMutexException] { $HasLock = $true }
    if (-not $HasLock) { throw 'Timed out waiting for the readback fixture assembly' }
    if (-not [IO.File]::Exists($AssemblyPath)) {
        $PendingPath = Join-Path $CacheRoot ([Guid]::NewGuid().ToString('N') + '.dll')
        $CompileClock = [Diagnostics.Stopwatch]::StartNew()
        [Console]::Error.WriteLine((@{ fixture = 'readback'; phase = 'compile'; utc = [DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Compress))
        try {
            Add-Type -TypeDefinition $Definition -ReferencedAssemblies @('System.Core.dll', $Web) -OutputAssembly $PendingPath
            [IO.File]::Move($PendingPath, $AssemblyPath)
            $Compiled = $true
        } finally {
            if ([IO.File]::Exists($PendingPath)) { [IO.File]::Delete($PendingPath) }
        }
        $CompileSeconds = $CompileClock.Elapsed.TotalSeconds
    }
} finally {
    if ($HasLock) { $Mutex.ReleaseMutex() }
    $Mutex.Dispose()
}
Add-Type -Path $AssemblyPath
[Console]::Error.WriteLine((@{
    fixture = 'readback'; phase = 'loaded'; compiled = $Compiled; assembly = $AssemblyPath
    compile_seconds = $CompileSeconds; elapsed_seconds = $Started.Elapsed.TotalSeconds
} | ConvertTo-Json -Compress))
if ($CompileOnly) { exit 0 }
[ProgressFixture]::Run($OwnerPath, $JournalPath, $MarkerPath)
