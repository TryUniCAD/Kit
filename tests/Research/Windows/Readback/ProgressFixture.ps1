# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

param([string]$Source, [string]$OwnerPath, [string]$JournalPath, [string]$MarkerPath)
$ErrorActionPreference = 'Stop'
$Web = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
$Program = @'
public static class ProgressFixture
{
    private const string Control = "control.SLDPRT";

    private static void HideControl(ReadbackProgress progress, string markerPath)
    {
        progress.Invoke("final_control_hidden", Control,
            () => System.IO.File.WriteAllText(markerPath, "real filesystem fixture action"),
            new System.Collections.Generic.Dictionary<string, object> { { "visible", false } });
    }

    private static void RecordVisibility(ReadbackProgress progress, string markerPath)
    {
        var visibility = new System.Collections.Generic.Dictionary<string, object>();
        progress.Invoke("close_visibility", Control, () => {
            visibility["visible"] = !System.IO.File.Exists(markerPath);
        }, visibility);
    }

    private static void RecordState(ReadbackProgress progress)
    {
        var state = new System.Collections.Generic.Dictionary<string, object>();
        progress.Invoke("close_state", Control, () => {
            state["save_flag"] = true;
            state["read_only"] = true;
            state["document_count"] = 1;
        }, state);
    }

    private static void ObserveControl(ReadbackProgress progress, string markerPath)
    {
        progress.Invoke("open_document", Control, () => System.IO.File.Exists(markerPath));
        RecordVisibility(progress, markerPath);
        RecordState(progress);
        progress.Invoke("quit_document", Control,
            () => System.IO.File.WriteAllText(markerPath, "real filesystem fixture action"),
            new System.Collections.Generic.Dictionary<string, object> { { "operand", Control } });
    }

    public static string Run(string ownerPath, string journalPath, string markerPath)
    {
        var json = new System.Web.Script.Serialization.JavaScriptSerializer();
        var owner = json.Deserialize<System.Collections.Generic.Dictionary<string, object>>(System.IO.File.ReadAllText(ownerPath));
        var progress = new ReadbackProgress(journalPath, owner);
        HideControl(progress, markerPath);
        progress.Invoke("control_after", Control, () => ObserveControl(progress, markerPath));
        return json.Serialize(progress.Finish("observed"));
    }
}
'@
Add-Type -TypeDefinition ((Get-Content -LiteralPath $Source -Raw) + "`n" + $Program) -ReferencedAssemblies @('System.Core.dll', $Web)
[ProgressFixture]::Run($OwnerPath, $JournalPath, $MarkerPath)
