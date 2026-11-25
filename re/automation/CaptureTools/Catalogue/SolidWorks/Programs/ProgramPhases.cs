// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
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
    IModelDoc2 BuildCase(Dictionary<string,object> Program,Dictionary<string,object> Options)
    {
        var Document=BuildProgram(Program,TextValue(Options,"basis"),Convert.ToInt32(Options["direction"])==-1);
        try { Units(Document,TextValue(Options,"variant")=="units-inch"?3:5); return Document; }
        catch { Close(Document); throw; }
    }

    void ProgramFirst()
    {
        string Recipe=TextValue(configuredCase,"recipe"), DirectoryName=Path.Combine(output,Recipe);
        Directory.CreateDirectory(DirectoryName);
        var Observed=Row("healthy_control_before",Control("before"));
        var Program=ProgramData();
        var Document=BuildCase(Program,configuredOptions);
        try {
            Observed["baseline"]=ProgramMeasure(Document,"as built",Program);
            var Saved=Save(Document,Path.Combine(DirectoryName,Filename(Recipe,"baseline-a")),false);
            Write(Path.Combine(DirectoryName,"first.json"),Row("observations",Observed,"first_save",Saved,"authoring_process_id",app.GetProcessID()));
        } finally { Close(Document); }
        Check(app.GetDocumentCount()==0,"Recipe first phase retained a document");
    }

    void ProgramSecond()
    {
        string Recipe=TextValue(configuredCase,"recipe"), DirectoryName=Path.Combine(output,Recipe);
        var First=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(DirectoryName,"first.json")));
        Check(RoutineReadback || Convert.ToInt32(First["authoring_process_id"])!=app.GetProcessID(),"Recipe reopen requires a fresh process");
        var Observed=MapValue(First["observations"]);
        var Saves=new List<Dictionary<string,object>> { MapValue(First["first_save"]) };
        var Programs=new Dictionary<string,Dictionary<string,object>>();
        var Program=ProgramData();
        Programs[Filename(Recipe,"baseline-a")]=Program;
        Programs[Filename(Recipe,"baseline-b")]=Program;
        string Baseline=Path.Combine(DirectoryName,Filename(Recipe,"baseline-a"));
        Check(Hash(Baseline)==TextValue(Saves[0],"sha256"),"Recipe baseline bytes changed");
        var Edits=new List<object>();
        var Variants=new List<object>();
        object Status;
        var Document=Open(Baseline,out Status);
        try {
            Observed["fresh_reopen"]=Row("open_status",Status,"measurements",ProgramMeasure(Document,"as opened",Program));
            Rebuild(Document);
            Observed["unchanged_rebuild"]=ProgramMeasure(Document,"unchanged rebuild",Program);
            Saves.Add(Save(Document,Path.Combine(DirectoryName,Filename(Recipe,"baseline-b")),true));
            foreach(var Edit in Array(Program["edits"]).Cast<Dictionary<string,object>>()) {
                string Parameter=TextValue(Edit,"parameter");
                double Value=NumberValue(Edit,"value");
                string Suffix="edit-"+Parameter+"-"+Value.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                string FileName=Filename(Recipe,Suffix);
                var EditedProgram=MapValue(Edit["program"]);
                ProgramEdit(Document,Program,Parameter,Value);
                var Changed=ProgramMeasure(Document,Suffix,EditedProgram);
                Saves.Add(Save(Document,Path.Combine(DirectoryName,FileName),true));
                Programs[FileName]=EditedProgram;
                ProgramEdit(Document,Program,Parameter,NumberValue(configuredParams,Parameter));
                Edits.Add(Row("parameter",Parameter,"value",Value,"edited",Changed,"restored",ProgramMeasure(Document,"restored "+Parameter,Program),"saved_file",FileName));
            }
        } finally { Close(Document); }
        foreach(var Variant in Array(Program["variants"]).Cast<Dictionary<string,object>>()) {
            string Name=TextValue(Variant,"name"), FileName=Filename(Recipe,Name);
            var VariantProgram=MapValue(Variant["program"]);
            Document=BuildCase(VariantProgram,MapValue(Variant["options"]));
            try {
                Variants.Add(Row("variant",Name,"reading",ProgramMeasure(Document,Name,VariantProgram)));
                Saves.Add(Save(Document,Path.Combine(DirectoryName,FileName),false));
                Programs[FileName]=VariantProgram;
            } finally { Close(Document); }
        }
        Observed["edits"]=Edits;
        Observed["variants"]=Variants;
        var Reopened=new Dictionary<string,object>();
        foreach(var Saved in Saves) {
            string FileName=TextValue(Saved,"file"), SavedPath=Path.Combine(DirectoryName,FileName);
            Document=Open(SavedPath,out Status);
            try {
                Rebuild(Document);
                var Reading=ProgramMeasure(Document,"reopened and rebuilt",Programs[FileName]);
                Reading["open_status"]=Status;
                Reopened[FileName]=Reading;
            } finally { Close(Document); }
            Check(Hash(SavedPath)==TextValue(Saved,"sha256"),"Recipe saved bytes changed on reopen");
        }
        Observed["reopened_files"]=Reopened;
        Observed["healthy_control_after"]=Control("after");
        string Measurements=Path.Combine(DirectoryName,"measurements.json");
        var Binary=System.Diagnostics.Process.GetProcessById(app.GetProcessID()).MainModule.FileVersionInfo.FileVersion;
        Write(Measurements,Row("recipe_id",Recipe,"application","SOLIDWORKS 2026","exact_application_build",app.RevisionNumber(),
            "executable_file_version",Binary,"specifications_sha256",Hash(Path.Combine(repo,"re","automation","FeatureRecipeSpecs.json")),
            "written_recipe_sha256",Program["recipe_sha256"],"authoring_origin","Independently authored from a source pinned written recipe through typed native operations",
            "world_basis",configuredOptions["basis"],"authoring_process_id",First["authoring_process_id"],"reopen_process_id",app.GetProcessID(),
            "observations",Observed,"saves",Saves,"errors",new object[0]));
        Write(Path.Combine(DirectoryName,"receipt.json"),Row("recipe_id",Recipe,"measurements","measurements.json",
            "measurement_receipt_sha256",Hash(Measurements),"native_files",Saves,"errors",0));
        Check(app.GetDocumentCount()==0,"Recipe second phase retained a document");
    }
}
