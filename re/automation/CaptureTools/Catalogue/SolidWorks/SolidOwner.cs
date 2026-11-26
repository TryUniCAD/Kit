// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.ExceptionServices;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Threading;
using System.Collections.Generic;
using System.Text;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;
using SolidWorks.Interop.sldworks;

public static class SolidOwner
{
    const int MissingObject = unchecked((int)0x800401E3);
    const int CallRejected = unchecked((int)0x80010001);

    [DllImport("ole32.dll", ExactSpelling = true)]
    static extern int GetRunningObjectTable(int reserved, out IRunningObjectTable table);

    [DllImport("ole32.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    static extern int CreateItemMoniker(string separator, string item, out IMoniker moniker);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    static extern bool QueryFullProcessImageNameW(SafeProcessHandle process, uint flags,
        StringBuilder path, ref int length);

    static object FindOwned(int pid)
    {
        IRunningObjectTable table=null;
        IMoniker moniker=null;
        try {
            Marshal.ThrowExceptionForHR(GetRunningObjectTable(0,out table));
            Marshal.ThrowExceptionForHR(CreateItemMoniker(null,
                "SolidWorks_PID_"+pid.ToString(CultureInfo.InvariantCulture),out moniker));
            object found;
            Marshal.ThrowExceptionForHR(table.GetObject(moniker,out found));
            return found;
        } finally {
            if(moniker!=null) Marshal.ReleaseComObject(moniker);
            if(table!=null) Marshal.ReleaseComObject(table);
        }
    }

    static void Verify(Process process, string expected, long created, int session)
    {
        if(process.HasExited || process.StartTime.ToUniversalTime().ToFileTimeUtc()!=created
            || process.SessionId!=session)
            throw new InvalidOperationException("The held SOLIDWORKS process identity changed during passive attachment");
        var image=new StringBuilder(32768);
        int length=image.Capacity;
        if(!QueryFullProcessImageNameW(process.SafeHandle,0,image,ref length))
            throw new Win32Exception(Marshal.GetLastWin32Error(),"Could not read the held SOLIDWORKS process image");
        if(!String.Equals(Path.GetFullPath(image.ToString()),Path.GetFullPath(expected),
            StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("The held SOLIDWORKS process identity changed during passive attachment");
    }

    public static ISldWorks AttachOwned(Process process, string executable, int timeoutSeconds)
    {
        long created=process.StartTime.ToUniversalTime().ToFileTimeUtc();
        int session;
        using(var caller=Process.GetCurrentProcess()) session=caller.SessionId;
        int missingGlobal=0,missingOwned=0,rejected=0;
        var elapsed=Stopwatch.StartNew();
        while(elapsed.Elapsed.TotalSeconds<timeoutSeconds) {
            Verify(process,executable,created,session);
            object found=null;
            try {
                try { found=Marshal.GetActiveObject("SldWorks.Application"); }
                catch(COMException error) {
                    if(error.ErrorCode!=MissingObject) throw;
                    missingGlobal++;
                    try { found=FindOwned(process.Id); }
                    catch(COMException owned) {
                        if(owned.ErrorCode!=MissingObject) throw;
                        missingOwned++;
                    }
                }
                if(found!=null) {
                    var application=found as ISldWorks;
                    if(application==null || application.GetProcessID()!=process.Id)
                        throw new InvalidOperationException("Passive COM returned another SOLIDWORKS process");
                    Verify(process,executable,created,session);
                    found=null;
                    return application;
                }
            } catch(COMException error) {
                if(error.ErrorCode!=CallRejected) throw;
                rejected++;
            } finally {
                if(found!=null) Marshal.ReleaseComObject(found);
            }
            Thread.Sleep(200);
        }
        throw new InvalidOperationException("Owned SOLIDWORKS automation unavailable global_rot="+missingGlobal+
            " owned_rot="+missingOwned+" rejected_calls="+rejected+" process_exited="+process.HasExited);
    }

    public static void RunOwned(Process process, string executable, string repository,
        string output, string configuration, string phase)
    {
        RunInApartment(process,executable,repository,output,configuration,phase,false);
    }

    public static void CheckReady(Process process, string executable)
    {
        ISldWorks application=null;
        try {
            application=AttachOwned(process,executable,120);
            if(application.GetDocumentCount()!=0)
                throw new InvalidOperationException("Startup requires an empty owned application");
        } finally {
            if(application!=null) Marshal.FinalReleaseComObject(application);
        }
    }

    public static void RunBatch(Process process, string executable, string repository,
        string output, string configuration, string phase)
    {
        RunInApartment(process,executable,repository,output,configuration,phase,true);
    }

    static void RunInApartment(Process process, string executable, string repository,
        string output, string configuration, string phase, bool batch)
    {
        ExceptionDispatchInfo failure=null;
        var thread=new Thread(() => {
            try { RunOwnedCore(process,executable,repository,output,configuration,phase,batch); }
            catch(Exception error) { failure=ExceptionDispatchInfo.Capture(error); }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();
        if(failure!=null) failure.Throw();
    }

    internal static void CollectNativeReferences()
    {
        for(int pass=0;pass<2;pass++) {
            GC.Collect();
            Marshal.CleanupUnusedObjectsInCurrentContext();
        }
    }

    static long ReadFrameHandle(ISldWorks application)
    {
        var frame=application.Frame() as IFrame;
        if(frame==null) return 0;
        try { return frame.GetHWndx64(); }
        finally { Marshal.ReleaseComObject(frame); }
    }

    static void CloseLastControl(ISldWorks application, Process process, string repository,
        Dictionary<string,object> record)
    {
        string path=Path.Combine(repository,"re","solidworks","examples",".SLDPRT","example.SLDPRT");
        application.DocumentVisible(false,1);
        int errors=0,warnings=0;
        var control=application.OpenDoc6(path,1,3,"",ref errors,ref warnings);
        if(control==null) throw new InvalidOperationException("The final read-only stock control could not open");
        string title;
        try {
            if(errors!=0 || (warnings!=0 && warnings!=2) || application.GetDocumentCount()!=1
                || !control.IsOpenedReadOnly() || !String.Equals(control.GetPathName(),path,StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("The final stock control is not the sole read-only owned document");
            title=control.GetTitle();
        } finally { Marshal.ReleaseComObject(control); }
        application.UserControlBackground=false;
        if(application.UserControlBackground || application.UserControl)
            throw new InvalidOperationException("The final stock control requires program-owned background mode");
        application.QuitDoc(title);
        if(process.HasExited) return;
        try {
            int remaining=application.GetDocumentCount();
            record["documents_after_final_quit"]=remaining;
            if(remaining==0) {
                application.ExitApp();
                record["empty_session_exit_app_requested"]=true;
            }
        } catch(COMException error) { record["post_quit_transport_error"]=error.ErrorCode; }
    }

    static void RunOwnedCore(Process process, string executable, string repository,
        string output, string configuration, string phase, bool batch)
    {
        ISldWorks application=null;
        Exception failure=null;
        var record=new Dictionary<string,object> {
            {"pid",process.Id},{"phase",phase},{"normal_exit_requested",false},
            {"initial_documents",null},{"background_control",false},{"cleanup_errors",new List<string>()}
        };
        var cleanup=(List<string>)record["cleanup_errors"];
        try {
            application=AttachOwned(process,executable,120);
            record["initial_documents"]=application.GetDocumentCount();
            if((int)record["initial_documents"]!=0)
                throw new InvalidOperationException("Configured authoring requires an empty owned native session");
            application.UserControlBackground=true;
            record["background_control"]=application.UserControlBackground;
            if(!(bool)record["background_control"])
                throw new InvalidOperationException("The owned application did not retain background lifetime control");
            application.Visible=false;
            if(batch) SolidWorksCapture.RunBatch(application,repository,output,configuration,phase);
            else SolidWorksCapture.RunConfigured(application,repository,output,configuration,phase);
        } catch(Exception error) {
            failure=error;
            record["failure"]=error.ToString();
        } finally {
            if(application!=null) {
                try {
                    CollectNativeReferences();
                    if(application.GetProcessID()==process.Id && application.GetDocumentCount()==0) {
                        try { record["frame_handle"]=ReadFrameHandle(application); }
                        catch(COMException error) { record["frame_query_error"]=error.Message; }
                        if(failure==null) {
                            CloseLastControl(application,process,repository,record);
                            record["normal_exit_method"]="last_background_document";
                        } else {
                            application.ExitApp();
                            record["normal_exit_method"]="exit_app";
                        }
                        record["normal_exit_requested"]=true;
                    }
                } catch(Exception error) { cleanup.Add(error.ToString()); }
                try {
                    Marshal.FinalReleaseComObject(application);
                    CollectNativeReferences();
                }
                catch(Exception error) { cleanup.Add(error.ToString()); }
            }
            Directory.CreateDirectory(output);
            string diagnostic=Path.Combine(output,phase+"-native.json");
            using(var stream=new FileStream(diagnostic,FileMode.CreateNew,FileAccess.Write,FileShare.None)) {
                byte[] bytes=new UTF8Encoding(false).GetBytes(new JavaScriptSerializer().Serialize(record)+"\n");
                stream.Write(bytes,0,bytes.Length);
                stream.Flush(true);
            }
        }
        if(failure!=null) throw new InvalidOperationException("Configured native phase failed "+failure.Message,failure);
        if(cleanup.Count!=0 || !(bool)record["normal_exit_requested"])
            throw new InvalidOperationException("Configured native phase cleanup did not complete normally");
    }
}
