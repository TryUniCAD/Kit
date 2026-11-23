# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

[CmdletBinding(DefaultParameterSetName = 'Capture')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Compile')][string]$Source,
    [Parameter(Mandatory = $true)][string]$AssemblyPath,
    [Parameter(Mandatory = $true, ParameterSetName = 'Capture')][string]$OwnerPath,
    [Parameter(Mandatory = $true, ParameterSetName = 'Capture')][string]$JournalPath,
    [Parameter(Mandatory = $true, ParameterSetName = 'Capture')][string]$MarkerPath
)
$ErrorActionPreference = 'Stop'
if ($PSCmdlet.ParameterSetName -eq 'Capture') {
    Add-Type -LiteralPath $AssemblyPath
    [ProgressFixture]::Run($OwnerPath, $JournalPath, $MarkerPath)
    return
}

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
Add-Type -TypeDefinition ((Get-Content -LiteralPath $Source -Raw) + "`n" + $Program) -ReferencedAssemblies @('System.Core.dll', $Web) -OutputAssembly $AssemblyPath
