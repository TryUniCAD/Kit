// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    public static void ServeRoutineOwned(Process process, string executable, string repository, string queue, string revision)
    {
        ISldWorks app=null;
        Exception failure=null;
        try {
            app=SolidOwner.AttachOwned(process,executable,120);
            ServeRoutine(app,process,repository,queue,revision);
        } catch(Exception error) { failure=error; }
        finally {
            if(app!=null) {
                try {
                    if(app.GetProcessID()==process.Id && app.GetDocumentCount()==0) app.ExitApp();
                } catch(Exception error) { if(failure==null) failure=error; }
                System.Runtime.InteropServices.Marshal.FinalReleaseComObject(app);
            }
        }
        if(failure!=null) {
            PublishRoutine(Path.Combine(queue,"failure.json"),Row("error",failure.ToString()));
            throw new InvalidOperationException("Routine owner failed",failure);
        }
    }

    static void PublishRoutine(string path, object value)
    {
        byte[] bytes=new UTF8Encoding(false).GetBytes(Json.Serialize(value)+"\n");
        string temporary=path+".tmp";
        using(var stream=new FileStream(temporary,FileMode.CreateNew,FileAccess.Write,FileShare.None)) {
            stream.Write(bytes,0,bytes.Length); stream.Flush(true);
        }
        File.Move(temporary,path);
    }

    public static void ServeRoutine(ISldWorks app, Process process, string repository, string queue, string revision)
    {
        string attempts=Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(queue)),"NativeAttempts")+Path.DirectorySeparatorChar;
        string completed=Path.Combine(queue,"completed");
        Directory.CreateDirectory(completed);
        long created=process.StartTime.ToUniversalTime().ToFileTimeUtc();
        Check(app.GetProcessID()==process.Id && app.GetDocumentCount()==0,"Routine owner requires an empty owned application");
        app.UserControlBackground=true;
        Check(app.UserControlBackground,"Routine owner could not retain its application lifetime");
        app.Visible=false;
        var listener=Process.GetCurrentProcess();
        PublishRoutine(Path.Combine(queue,"ready.json"),Row("pid",process.Id,"created",created,"revision",revision,
            "listener",listener.Id,"listener_created","windows:"+listener.StartTime.ToUniversalTime().ToFileTimeUtc()));
        RoutineReadback=true;
        try {
            while(!File.Exists(Path.Combine(queue,"stop"))) {
                Check(!process.HasExited && app.GetProcessID()==process.Id,"Routine owner lost its native process");
                foreach(string request in Directory.GetFiles(queue,"*.request.json").OrderBy(path=>path)) {
                    string response=Path.Combine(completed,Path.GetFileName(request).Replace(".request.json",".response.json"));
                    if(File.Exists(response)) continue;
                    var packet=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(request));
                    string manifest=Path.GetFullPath((string)packet["manifest"]);
                    Check(packet.Count==4 && (string)packet["revision"]==revision
                        && Convert.ToDouble(packet["deadline"])>DateTimeOffset.UtcNow.ToUnixTimeSeconds(),"Routine request revision or deadline is invalid");
                    Check(manifest.StartsWith(attempts,StringComparison.OrdinalIgnoreCase)
                        && Path.GetFileName(manifest)=="BatchManifest.json" && Hash(manifest)==(string)packet["sha256"],"Routine manifest escapes its run or changed");
                    string output=Path.GetDirectoryName(manifest);
                    CheckBatch(manifest,output);
                    var root=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(manifest));
                    foreach(var item in Array(root["cases"]).Cast<Dictionary<string,object>>()) {
                        Check(!File.Exists(Path.Combine(queue,"stop")) && Convert.ToDouble(packet["deadline"])>DateTimeOffset.UtcNow.ToUnixTimeSeconds(),"Routine request cancelled or expired");
                        string destination=TextValue(item,"output"), configuration=TextValue(item,"configuration");
                        Check(app.GetDocumentCount()==0,"Routine capture retained an earlier document");
                        RunConfigured(app,repository,destination,configuration,"first");
                        Check(app.GetDocumentCount()==0,"Routine first phase retained an open document");
                        var first=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(destination,(string)Configuration(configuration)["recipe"],"first.json")));
                        var save=MapValue(first["first_save"]);
                        string baseline=Path.Combine(destination,(string)Configuration(configuration)["recipe"],(string)save["file"]);
                        Check(app.GetOpenDocumentByName(baseline)==null && Hash(baseline)==(string)save["sha256"],"Routine baseline is still loaded or changed before reopen");
                        RunConfigured(app,repository,destination,configuration,"second");
                        Check(app.GetDocumentCount()==0 && Hash(baseline)==(string)save["sha256"],"Routine verification retained a document or changed baseline bytes");
                        PublishRoutine(Path.Combine(destination,"Routine.json"),Row("schema",1,"mode","document_reopen",
                            "pid",process.Id,"created",created,"revision",revision,"manifest_sha256",packet["sha256"],
                            "configuration_sha256",Hash(configuration),"documents_before_reopen",0,"documents_after",0,
                            "baseline_unloaded",true,"baseline_sha256",Hash(baseline),"build",app.RevisionNumber()));
                    }
                    Check(Hash(manifest)==(string)packet["sha256"],"Routine manifest changed during capture");
                    File.Move(request,Path.Combine(completed,Path.GetFileName(request)));
                    PublishRoutine(response,Row("status","completed","revision",revision,"sha256",packet["sha256"],"pid",process.Id,"created",created));
                }
                Thread.Sleep(50);
            }
        } finally { RoutineReadback=false; }
    }
}
