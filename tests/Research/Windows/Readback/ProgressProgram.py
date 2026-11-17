# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# managed journal bytes must cross the real python queue boundary without serializer assumptions
KProgressScript = """param([string]$Source, [string]$OwnerPath, [string]$JournalPath, [string]$MarkerPath)
$ErrorActionPreference = 'Stop'
$Web = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'System.Web.Extensions.dll'
$Program = @'
public static class ProgressFixture
{
    public static string Run(string ownerPath, string journalPath, string markerPath)
    {
        var json = new System.Web.Script.Serialization.JavaScriptSerializer();
        var owner = json.Deserialize<System.Collections.Generic.Dictionary<string, object>>(System.IO.File.ReadAllText(ownerPath));
        var progress = new ReadbackProgress(journalPath, owner);
        progress.Invoke("control_before", null, () => System.IO.File.WriteAllText(markerPath, "real filesystem fixture action"));
        return json.Serialize(progress.Finish("observed"));
    }
}
'@
Add-Type -TypeDefinition ((Get-Content -LiteralPath $Source -Raw) + "`n" + $Program) -ReferencedAssemblies @('System.Core.dll', $Web)
[ProgressFixture]::Run($OwnerPath, $JournalPath, $MarkerPath)
"""
