// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    public static void CheckBatch(string Manifest,string Output)
    {
        var Root=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Manifest));
        Check(Root.Count==2 && Convert.ToInt32(Root["schema"])==1 && Root.ContainsKey("cases"),"Invalid native batch manifest");
        var Cases=Array(Root["cases"]).Cast<Dictionary<string,object>>().ToArray();
        Check(Cases.Length>0 && Cases.Length<=3,"Native batches require one to three written cases");
        var Seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach(var Case in Cases) {
            Check(Case.Count==2 && Case.ContainsKey("configuration") && Case.ContainsKey("output"),"Invalid native batch case");
            string Destination=Path.GetFullPath(TextValue(Case,"output"));
            string ConfigurationPath=Path.GetFullPath(TextValue(Case,"configuration"));
            Check(Path.GetDirectoryName(Destination)==Path.GetFullPath(Output) && Seen.Add(Destination)
                && Path.GetDirectoryName(ConfigurationPath)==Destination && File.Exists(ConfigurationPath),"Native batch case escapes its owned directory");
            var Configured=Configuration(ConfigurationPath);
            Check(MapValue(Configured["options"]).ContainsKey("program"),"Native batching only accepts written recipe programs");
        }
    }

    public static void RunBatch(object Application,string Repository,string Output,string Manifest,string Phase)
    {
        CheckBatch(Manifest,Output);
        string Pin=Hash(Manifest);
        var Root=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Manifest));
        var Owned=Application as ISldWorks;
        Check(Owned!=null && Owned.GetDocumentCount()==0,"Native batch requires an empty owned application");
        foreach(var Case in Array(Root["cases"]).Cast<Dictionary<string,object>>()) {
            Check(Owned.GetDocumentCount()==0,"Native batch retained a previous case document");
            RunConfigured(Application,Repository,TextValue(Case,"output"),TextValue(Case,"configuration"),Phase);
            Check(Owned.GetDocumentCount()==0 && Hash(Manifest)==Pin,"Native batch changed ownership or manifest");
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
            GC.WaitForPendingFinalizers();
        }
    }
}
