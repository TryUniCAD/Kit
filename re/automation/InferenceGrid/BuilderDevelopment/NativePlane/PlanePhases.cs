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
    public static void CheckPlaneManifest(string Manifest)
    {
        var Root=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Manifest));
        Check(Root.Count==3 && Convert.ToInt32(Root["schema_version"])==1,"Invalid plane manifest");
        var Program=MapValue(Root["program"]);
        Check(Program.Count==5 && Convert.ToInt32(Program["schema"])==1,"Invalid candidate program fields");
        Check(new[]{"offset_plane","coincident_plane"}.Contains(TextValue(Program,"operation")),"Invalid candidate plane operation");
        Check(new[]{"XY","YZ","XZ"}.Contains(TextValue(Program,"support")),"Invalid candidate support");
        double ScaleValue=NumberValue(Program,"scale");
        Check(ScaleValue>=-2 && ScaleValue<=2 && Program["reverse"] is bool,"Invalid bounded candidate controls");
        var Cases=Array(Root["cases"]).Cast<Dictionary<string,object>>().ToArray();
        Check(Cases.Length>=1 && Cases.Length<=3,"Native plane batch requires one to three cases");
        var Seen=new HashSet<string>();
        foreach(var Case in Cases) {
            string Id=TextValue(Case,"id");
            Check(Case.Count==3 && Id.Length>0 && Id.Length<=40 && Id.All(Symbol=>char.IsLetterOrDigit(Symbol)||Symbol=='-'||Symbol=='_') && Seen.Add(Id),"Invalid native plane case identity");
            Check(NumberValue(Case,"offset_mm")>0 && NumberValue(Case,"edit_mm")>0,"Native plane case controls must be positive");
        }
    }

    IModelDoc2 BuildPlane(Dictionary<string,object> Program,double Requested)
    {
        var Document=(IModelDoc2)app.INewDocument2(template,0,0,0);
        Check(Document!=null,"Create candidate research part");
        try {
            Units(Document,5);
            ProgramSeed(Document,Row("kind","block","width_mm",40.0,"depth_mm",20.0,"height_mm",10.0),"XY");
            var Feature=GeneratedPlaneBuilder.BuildCandidate(Document,Requested);
            Check(Feature!=null,"Candidate native plane creation failed");
            Feature.Name="RecipeFeature";
            if(TextValue(Program,"operation")=="offset_plane") {
                var NativeDimensions=Dimensions(Feature).ToArray();
                Check(NativeDimensions.Length==1,"Candidate offset feature has no unique native dimension");
                NativeDimensions[0].Name="offset_mm";
            }
            Document.ClearSelection2(true);
            Rebuild(Document);
            return Document;
        } catch { Close(Document); throw; }
    }

    void PlaneFirst(Dictionary<string,object> Program,Dictionary<string,object> Case)
    {
        string DirectoryName=Path.Combine(output,"C"+TextValue(Case,"id"));
        Directory.CreateDirectory(DirectoryName);
        var Document=BuildPlane(Program,NumberValue(Case,"offset_mm"));
        try {
            var Observations=Row("baseline",MeasurePlane(Document,"as built"));
            var Saved=Save(Document,Path.Combine(DirectoryName,"A.SLDPRT"),false);
            Saved["role"]="baseline-a"; Saved["offset_mm"]=Case["offset_mm"]; Saved["writer_process_id"]=app.GetProcessID();
            Write(Path.Combine(DirectoryName,"first.json"),Row("observations",Observations,"first_save",Saved,"authoring_process_id",app.GetProcessID()));
        } finally { Close(Document); }
    }

    void PlaneSecond(Dictionary<string,object> Case)
    {
        string DirectoryName=Path.Combine(output,"C"+TextValue(Case,"id"));
        var First=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(DirectoryName,"first.json")));
        Check(Convert.ToInt32(First["authoring_process_id"])!=app.GetProcessID(),"Candidate reopen did not use a fresh process");
        var Observed=MapValue(First["observations"]);
        var Saves=new List<Dictionary<string,object>> { MapValue(First["first_save"]) };
        string Baseline=Path.Combine(DirectoryName,"A.SLDPRT");
        Check(Hash(Baseline)==TextValue(Saves[0],"sha256"),"Candidate baseline bytes changed");
        object Status;
        var Document=Open(Baseline,out Status);
        try {
            Observed["fresh_reopen"]=Row("open_status",Status,"measurements",MeasurePlane(Document,"fresh reopen"));
            Rebuild(Document); Observed["unchanged_rebuild"]=MeasurePlane(Document,"unchanged rebuild");
            var Feature=Features(Document).Single(Found=>Found.Name=="RecipeFeature");
            var NativeDimensions=Dimensions(Feature).Where(Dimension=>Dimension.Name=="offset_mm").ToArray();
            Observed["edited"]=null; Observed["restored"]=null;
            if(NativeDimensions.Length==1 && NativeDimensions[0].DrivenState==2) {
                var Dimension=NativeDimensions[0]; double Initial=Dimension.SystemValue;
                int EditStatus=Dimension.SetSystemValue3(NumberValue(Case,"edit_mm")*.001,1,null);
                Check(EditStatus==0,"Native dimension edit failed"); Rebuild(Document);
                Observed["edited"]=MeasurePlane(Document,"edited");
                var Edited=Save(Document,Path.Combine(DirectoryName,"E.SLDPRT"),true);
                Edited["role"]="edited"; Edited["offset_mm"]=Case["edit_mm"]; Edited["writer_process_id"]=app.GetProcessID(); Saves.Add(Edited);
                Check(Dimension.SetSystemValue3(Initial,1,null)==0,"Native dimension restore failed"); Rebuild(Document);
                Observed["restored"]=MeasurePlane(Document,"restored");
                var Restored=Save(Document,Path.Combine(DirectoryName,"B.SLDPRT"),true);
                Restored["role"]="baseline-b"; Restored["offset_mm"]=Case["offset_mm"]; Restored["writer_process_id"]=app.GetProcessID(); Saves.Add(Restored);
            } else Observed["edit_error"]="Candidate has no unique native driving offset dimension";
        } finally { Close(Document); }
        Write(Path.Combine(DirectoryName,"measurements.json"),Row("id",Case["id"],"requested",Row("offset_mm",Case["offset_mm"],"edit_mm",Case["edit_mm"]),
            "observations",Observed,"saves",Saves,"authoring_process_id",First["authoring_process_id"],"reopen_process_id",app.GetProcessID(),
            "application_build",app.RevisionNumber(),"executable_file_version",System.Diagnostics.Process.GetProcessById(app.GetProcessID()).MainModule.FileVersionInfo.FileVersion));
    }

    void PlaneThird(Dictionary<string,object> Case)
    {
        string DirectoryName=Path.Combine(output,"C"+TextValue(Case,"id"));
        string Measurements=Path.Combine(DirectoryName,"measurements.json");
        var Report=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Measurements));
        Check(Convert.ToInt32(Report["authoring_process_id"])!=app.GetProcessID()
            && Convert.ToInt32(Report["reopen_process_id"])!=app.GetProcessID(),"Archive reopen requires a third fresh process");
        var Reopened=new Dictionary<string,object>();
        foreach(var Saved in Array(Report["saves"]).Cast<Dictionary<string,object>>()) {
            Check(Convert.ToInt32(Saved["writer_process_id"])!=app.GetProcessID(),"Saved archive writer cannot verify its own reopen");
            string FileName=TextValue(Saved,"file"), SavedPath=Path.Combine(DirectoryName,FileName);
            Check(Hash(SavedPath)==TextValue(Saved,"sha256"),"Saved archive changed before independent reopen");
            object Status;
            var Document=Open(SavedPath,out Status);
            try {
                Rebuild(Document);
                var Reading=MeasurePlane(Document,"reopened and rebuilt");
                Reading["open_status"]=Status; Reading["role"]=Saved["role"]; Reading["requested_offset_mm"]=Saved["offset_mm"];
                Reading["process_id"]=app.GetProcessID(); Reading["writer_process_id"]=Saved["writer_process_id"];
                Reopened[FileName]=Reading;
            } finally { Close(Document); }
            Check(Hash(SavedPath)==TextValue(Saved,"sha256"),"Candidate saved bytes changed after reopen");
        }
        MapValue(Report["observations"])["reopened_files"]=Reopened;
        Report["archive_reopen_process_id"]=app.GetProcessID();
        Write(Measurements,Report);
    }

    public static void RunPlane(object Application,string Repository,string Output,string Manifest,string Phase)
    {
        CheckPlaneManifest(Manifest); string Pin=Hash(Manifest);
        var Root=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Manifest));
        var Capture=new SolidWorksCapture((ISldWorks)Application,Repository,Output);
        Check(Capture.app.GetDocumentCount()==0,"Candidate plane phase requires an empty owned application");
        var Before=Capture.Control("before");
        foreach(var Case in Array(Root["cases"]).Cast<Dictionary<string,object>>()) {
            if(Phase=="first") Capture.PlaneFirst(MapValue(Root["program"]),Case);
            else if(Phase=="second") Capture.PlaneSecond(Case);
            else { Check(Phase=="third","Invalid candidate phase"); Capture.PlaneThird(Case); }
            Check(Capture.app.GetDocumentCount()==0 && Hash(Manifest)==Pin,"Candidate phase changed ownership or input");
            GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect(); GC.WaitForPendingFinalizers();
        }
        var After=Capture.Control("after");
        Write(Path.Combine(Output,Phase+"-controls.json"),Row("before",Before,"after",After,"application_build",Capture.app.RevisionNumber(),"pid",Capture.app.GetProcessID()));
    }
}
